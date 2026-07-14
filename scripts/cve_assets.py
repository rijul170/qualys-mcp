"""Assets affected by one or more CVEs, with hostname / IP / tags (read-only).

Qualys detects by QID, not CVE, so:
  1. Resolve CVE -> QID via the KnowledgeBase (paginated scan of QIDs modified
     since --kb-since; CVE data is included with details=Basic, no show_cve).
  2. Pull Host List VM Detection for those QIDs with show_tags=1 (paginated).
  3. Emit a table: hostname (DNS/NetBIOS), IP, tags, and which CVEs/QIDs hit.

Uses QualysClient directly. Writes reports/cve-assets-<console>.{json,md}.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from qualys_mcp.client import QualysClient
from qualys_mcp.common.utils import as_list
from qualys_mcp.config import QualysConfig


def kb_cve_to_qids(client, cves: set[str], since: str, max_batches: int = 60) -> dict[str, set[str]]:
    """Scan the KB (paginated by id_min) building CVE->{QIDs} for the target CVEs."""
    hits: dict[str, set[str]] = {}
    id_min = None
    for _ in range(max_batches):
        params = {"action": "list", "last_modified_after": since, "details": "Basic"}
        if id_min is not None:
            params["id_min"] = id_min
        resp = client.fo("/api/2.0/fo/knowledge_base/vuln/", method="GET", params=params)
        if isinstance(resp, dict) and "error" in resp:
            print("  KB error:", str(resp["error"])[:160])
            break
        root = resp.get("KNOWLEDGE_BASE_VULN_LIST_OUTPUT", {}).get("RESPONSE", {})
        vulns = as_list((root.get("VULN_LIST") or {}).get("VULN"))
        if not vulns:
            break
        max_qid = 0
        for v in vulns:
            q = str(v.get("QID"))
            if q.isdigit():
                max_qid = max(max_qid, int(q))
            for cve in as_list((v.get("CVE_LIST") or {}).get("CVE")):
                cid = cve.get("ID") if isinstance(cve, dict) else cve
                if cid in cves:
                    hits.setdefault(cid, set()).add(q)
        if len(hits) >= len(cves):  # all target CVEs resolved — stop early
            break
        warning = root.get("WARNING")
        if warning and max_qid:
            id_min = max_qid + 1  # next page
            continue
        break
    return hits


def detections_for_qids(client, qids: list[str], max_batches: int = 40) -> list[dict]:
    """Pull Host List VM Detection for the given QIDs (with tags), paginated."""
    hosts: list[dict] = []
    id_min = None
    for _ in range(max_batches):
        params = {
            "action": "list",
            "qids": ",".join(qids),
            "show_tags": "1",
            "show_igs": "0",
            "truncation_limit": "1000",
        }
        if id_min is not None:
            params["id_min"] = id_min
        resp = client.fo("/api/2.0/fo/asset/host/vm/detection/", method="GET", params=params)
        if isinstance(resp, dict) and "error" in resp:
            print("  detection error:", str(resp["error"])[:160])
            break
        root = resp.get("HOST_LIST_VM_DETECTION_OUTPUT", {}).get("RESPONSE", {})
        hlist = as_list((root.get("HOST_LIST") or {}).get("HOST"))
        if not hlist:
            break
        hosts.extend(hlist)
        max_id = max((int(h["ID"]) for h in hlist if str(h.get("ID", "")).isdigit()), default=0)
        warning = root.get("WARNING")
        if warning and max_id:
            id_min = max_id + 1
            continue
        break
    return hosts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--console", required=True)
    ap.add_argument("--cves", required=True, help="comma-separated CVE IDs")
    ap.add_argument("--kb-since", default="2026-01-01")
    args = ap.parse_args()

    cves = {c.strip() for c in args.cves.split(",") if c.strip()}
    cfg = QualysConfig.from_env(console_label=args.console)
    cfg.require_credentials()
    c = QualysClient(cfg)

    print(f"[{args.console}] resolving {len(cves)} CVE(s) -> QIDs via KB (since {args.kb_since}) ...")
    cve_qids = kb_cve_to_qids(c, cves, args.kb_since)
    qid_cve: dict[str, list[str]] = {}
    for cve, qids in cve_qids.items():
        for q in qids:
            qid_cve.setdefault(q, []).append(cve)
    all_qids = sorted(qid_cve.keys(), key=lambda x: int(x))
    for cve in sorted(cves):
        print(f"   {cve} -> {sorted(cve_qids.get(cve, [])) or 'no QID in KB window'}")

    result = {
        "console": args.console,
        "cves": sorted(cves),
        "cve_to_qids": {k: sorted(v) for k, v in cve_qids.items()},
        "kb_since": args.kb_since,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "assets": [],
    }

    if all_qids:
        print(f"[{args.console}] pulling detections for QIDs {all_qids} ...")
        hosts = detections_for_qids(c, all_qids)
        for h in hosts:
            tags = as_list((h.get("TAGS") or {}).get("TAG"))
            tag_names = [t.get("NAME") for t in tags if isinstance(t, dict) and t.get("NAME")]
            det_qids = [str(d.get("QID")) for d in as_list((h.get("DETECTION_LIST") or {}).get("DETECTION"))]
            matched_qids = sorted(set(det_qids) & set(all_qids), key=lambda x: int(x))
            matched_cves = sorted({cve for q in matched_qids for cve in qid_cve.get(q, [])})
            result["assets"].append({
                "hostname": h.get("DNS") or h.get("NETBIOS") or h.get("IP"),
                "dns": h.get("DNS"),
                "netbios": h.get("NETBIOS"),
                "ip": h.get("IP"),
                "os": h.get("OS"),
                "tags": tag_names,
                "matched_qids": matched_qids,
                "matched_cves": matched_cves,
            })
        print(f"[{args.console}] affected assets: {len(result['assets'])}")

    out = Path("reports") / f"cve-assets-{args.console}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [
        f"# Assets affected by CVEs — {args.console}",
        "",
        f"- CVEs: {', '.join(sorted(cves))}",
        "- CVE→QID: " + "; ".join(f"{k}={sorted(v)}" for k, v in result["cve_to_qids"].items()) or "- CVE→QID: none",
        f"- Affected assets: **{len(result['assets'])}**",
        f"- Generated: {result['timestamp']}",
        "",
        "| Hostname | IP | OS | Tags | Matched CVEs |",
        "|---|---|---|---|---|",
    ]
    for a in result["assets"]:
        lines.append(
            f"| {a['hostname']} | {a['ip']} | {str(a['os'])[:40]} | "
            f"{', '.join(a['tags'])} | {', '.join(a['matched_cves'])} |"
        )
    out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[{args.console}] report -> {out}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
