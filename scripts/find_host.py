"""Find a host by name on one console and pull its vulnerabilities (read-only).

Uses QualysClient directly (no module imports), so it's unaffected by concurrent
module edits. Strategy:
  1. Resolve the host by name via Asset Management search (QPS AM), trying the
     'name', 'dnsHostName', then 'netbiosName' fields with CONTAINS.
  2. For each resolved IP, pull Host List VM Detection (classic FO) vulns.
  3. Enrich the top QIDs with titles/severity from the KnowledgeBase.
Writes reports/host-<console>-<name>.{json,md} and prints a summary.
"""

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from qualys_mcp.client import QualysClient
from qualys_mcp.common.utils import as_list
from qualys_mcp.config import QualysConfig


def am_search(client: QualysClient, field: str, name: str):
    body = (
        "<ServiceRequest><preferences><limitResults>50</limitResults></preferences>"
        f'<filters><Criteria field="{field}" operator="CONTAINS">{html.escape(name)}</Criteria></filters>'
        "</ServiceRequest>"
    )
    return client.qps("/qps/rest/2.0/search/am/hostasset", method="POST", body_xml=body, accept="xml")


def extract_hosts(resp):
    if not isinstance(resp, dict):
        return []
    data = resp.get("ServiceResponse", {}).get("data") or {}
    return as_list(data.get("HostAsset")) if data else []


def fo_detections(client: QualysClient, ips: str):
    return client.fo(
        "/api/2.0/fo/asset/host/vm/detection/",
        method="GET",
        params={"action": "list", "ips": ips, "show_igs": "1", "show_reopened_info": "1"},
    )


def kb_titles(client: QualysClient, qids: list[str]) -> dict:
    if not qids:
        return {}
    resp = client.fo(
        "/api/2.0/fo/knowledge_base/vuln/",
        method="GET",
        params={"action": "list", "ids": ",".join(qids), "details": "Basic"},
    )
    out: dict[str, dict] = {}
    try:
        vulns = as_list(resp["KNOWLEDGE_BASE_VULN_LIST_OUTPUT"]["RESPONSE"]["VULN_LIST"]["VULN"])
        for v in vulns:
            out[str(v.get("QID"))] = {"title": v.get("TITLE"), "severity": v.get("SEVERITY_LEVEL")}
    except Exception:  # noqa: BLE001
        pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--console", required=True)
    ap.add_argument("--name", required=True)
    args = ap.parse_args()

    cfg = QualysConfig.from_env(console_label=args.console)
    cfg.require_credentials()
    c = QualysClient(cfg)

    conn = c.verify_connectivity()
    connected = conn.get("connected") if isinstance(conn, dict) else False
    print(f"[{args.console}] connected={connected}")

    hosts, used_field = [], None
    for field in ("name", "dnsHostName", "netbiosName"):
        resp = am_search(c, field, args.name)
        if isinstance(resp, dict) and "error" in resp:
            print(f"  AM search ({field}) error: {str(resp['error'])[:120]}")
            continue
        hosts = extract_hosts(resp)
        if hosts:
            used_field = field
            break

    result = {
        "console": args.console,
        "name": args.name,
        "found": bool(hosts),
        "matched_field": used_field,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hosts": [],
    }

    if not hosts:
        print(f"  NOT FOUND via AM search (name/dnsHostName/netbiosName CONTAINS '{args.name}').")
    else:
        print(f"  found {len(hosts)} asset(s) via '{used_field}'")
        for h in hosts[:5]:
            ip = h.get("address")
            info = {
                "id": h.get("id"),
                "name": h.get("name"),
                "dnsHostName": h.get("dnsHostName"),
                "netbiosName": h.get("netbiosName"),
                "os": h.get("os"),
                "ip": ip,
                "trackingMethod": h.get("trackingMethod"),
                "modified": h.get("modified"),
                "vulnerabilities": {"total": 0, "severity_counts": {}, "top": []},
            }
            print(f"   - {info['name']} | IP {ip} | OS {info['os']} | track {info['trackingMethod']}")
            if ip:
                det = fo_detections(c, ip)
                if isinstance(det, dict) and "error" in det:
                    print(f"     detection error: {str(det['error'])[:120]}")
                else:
                    dets = []
                    try:
                        hlist = as_list(
                            det["HOST_LIST_VM_DETECTION_OUTPUT"]["RESPONSE"]["HOST_LIST"]["HOST"]
                        )
                    except Exception:  # noqa: BLE001
                        hlist = []
                    for host in hlist:
                        dets.extend(as_list((host.get("DETECTION_LIST") or {}).get("DETECTION")))
                    v = info["vulnerabilities"]
                    v["total"] = len(dets)
                    for d in dets:
                        sev = str(d.get("SEVERITY", "?"))
                        v["severity_counts"][sev] = v["severity_counts"].get(sev, 0) + 1
                    top = sorted(dets, key=lambda d: int(d.get("SEVERITY", 0) or 0), reverse=True)[:20]
                    titles = kb_titles(c, [str(d.get("QID")) for d in top if d.get("QID")])
                    for d in top:
                        q = str(d.get("QID"))
                        v["top"].append(
                            {
                                "qid": q,
                                "severity": d.get("SEVERITY"),
                                "type": d.get("TYPE"),
                                "status": d.get("STATUS"),
                                "last_found": d.get("LAST_FOUND_DATETIME"),
                                "title": (titles.get(q) or {}).get("title"),
                            }
                        )
                    print(f"     vulnerabilities: {v['total']} total, by severity {v['severity_counts']}")
            result["hosts"].append(info)

    out = Path("reports") / f"host-{args.console}-{args.name}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [f"# Host lookup: {args.name} on {args.console}", "",
             f"- Connected: {connected}", f"- Found: {result['found']} (matched field: {used_field})",
             f"- Generated: {result['timestamp']}", ""]
    for info in result["hosts"]:
        v = info["vulnerabilities"]
        lines += [
            f"## {info['name']}  (IP {info['ip']})",
            f"- Asset ID {info['id']} | DNS {info['dnsHostName']} | NetBIOS {info['netbiosName']}",
            f"- OS: {info['os']} | tracking: {info['trackingMethod']} | modified: {info['modified']}",
            f"- Vulnerabilities: **{v['total']}** total, by severity {v['severity_counts']}",
            "",
            "| QID | Sev | Type | Status | Last found | Title |",
            "|---|---|---|---|---|---|",
        ]
        for t in v["top"]:
            lines.append(
                f"| {t['qid']} | {t['severity']} | {t['type']} | {t['status']} | "
                f"{t['last_found']} | {str(t['title'])[:70]} |"
            )
        lines.append("")
    out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  report -> {out}.md")
    return 0 if hosts else 4


if __name__ == "__main__":
    sys.exit(main())
