"""Live READ-ONLY audit for one Qualys console.

Builds a QualysClient from the QUALYS_* environment (set by run-live-audit.ps1,
which decrypts the DPAPI credential blob), then exercises a curated set of
**read-only** tools spanning every API family (FO / QPS / Gateway) to verify:

* credentials + base URLs are correct (connectivity),
* Gateway JWT auth works,
* which modules the console is entitled to (vs "not subscribed" errors).

This script NEVER calls a write or destructive tool. Each probe is a list/get/
count/search read. Results are written as JSON + Markdown to reports/.

Usage (normally via run-live-audit.ps1):
    python scripts/live_readonly_audit.py --console cloud --out reports/cloud
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qualys_mcp.client import QualysClient
from qualys_mcp.config import QualysConfig
from qualys_mcp.registry import get_available_modules

# Curated, bounded, READ-ONLY probes: (module_registry_name, method, kwargs, family).
# One representative low-cost read per major product so the audit is fast and
# never pulls a whole subscription. Missing methods are reported, not fatal.
PROBES: list[tuple[str, str, dict[str, Any], str]] = [
    # --- Classic FO ---
    ("knowledgebase", "list_knowledgebase", {"ids": "90001"}, "FO"),
    ("vmscans", "list_scans", {"state": "Finished"}, "FO"),
    ("hostassets", "list_hosts", {"truncation_limit": 2}, "FO"),
    ("assetgroups", "list_asset_groups", {}, "FO"),
    ("optionprofiles", "list_option_profiles", {}, "FO"),
    ("scannerappliances", "list_scanner_appliances", {}, "FO"),
    ("reports", "list_reports", {}, "FO"),
    ("reporttemplates", "list_report_templates", {}, "FO"),
    ("remediationtickets", "view_ticket_list", {}, "FO"),
    ("pcpolicies", "list_compliance_policies", {}, "FO"),
    ("pccontrols", "list_compliance_controls", {}, "FO"),
    ("authrecords", "list_auth_records", {}, "FO"),
    ("users", "list_users", {}, "FO"),
    ("networks", "list_networks", {}, "FO"),
    ("maps", "list_map_reports", {}, "FO"),
    # --- QPS REST ---
    ("assettags", "search_tags", {}, "QPS"),
    ("hostassetam", "count_host_assets", {}, "QPS"),
    ("cloudagent", "list_agents", {}, "QPS"),
    ("waswebapps", "count_was_webapps", {}, "QPS"),
    ("wasscans", "search_was_scans", {}, "QPS"),
    # --- Gateway (JWT) ---
    ("gav", "count_gav_assets", {}, "Gateway"),
    ("csam", "count_csam_assets", {}, "Gateway"),
    ("csimages", "list_cs_images", {}, "Gateway"),
    ("cscontainers", "list_cs_containers", {}, "Gateway"),
    ("cloudviewconnectors", "list_cloud_connectors", {}, "Gateway"),
    ("patchmgmt", "list_patch_catalog", {}, "Gateway"),
    ("certview", "count_certificates", {}, "Gateway"),
    ("easm", "list_external_assets", {}, "Gateway"),
    ("fim", "list_fim_events", {}, "Gateway"),
    ("edr", "search_edr_events", {}, "Gateway"),
]


def _classify(result: Any) -> tuple[str, str]:
    """Return (status, detail) for a probe result."""
    if isinstance(result, dict) and "error" in result:
        code = str(result.get("qualys_code", ""))
        sc = result.get("status_code")
        detail = f"{result['error']}"[:200]
        if code == "NOT_ENTITLED" or sc in (401, 403):
            return "not_entitled_or_forbidden", detail
        if sc in (400, 409):
            return "api_error", detail
        return "error", detail
    return "ok", "response received"


def main() -> int:
    parser = argparse.ArgumentParser(description="Qualys live read-only audit")
    parser.add_argument("--console", required=True, help="console label (consulting/cloud)")
    parser.add_argument("--out", default=None, help="output path prefix (no extension)")
    args = parser.parse_args()

    config = QualysConfig.from_env(console_label=args.console)
    try:
        config.require_credentials()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    client = QualysClient(config)
    available = get_available_modules()

    # 1) Connectivity / auth (FO Basic).
    conn = client.verify_connectivity()
    connected = bool(isinstance(conn, dict) and conn.get("connected"))

    results = []
    for module_name, method_name, kwargs, family in PROBES:
        entry: dict[str, Any] = {
            "module": module_name,
            "tool": method_name,
            "family": family,
        }
        module_class = available.get(module_name)
        if module_class is None:
            entry.update(status="module_missing", detail="not discovered")
            results.append(entry)
            continue
        method = getattr(module_class(client), method_name, None)
        if method is None:
            entry.update(status="method_missing", detail="probe name mismatch")
            results.append(entry)
            continue
        try:
            res = method(**kwargs)
            status, detail = _classify(res)
        except Exception as exc:  # noqa: BLE001 - report, never crash the audit
            status, detail = "exception", f"{type(exc).__name__}: {exc}"[:200]
        entry.update(status=status, detail=detail)
        results.append(entry)

    ok = sum(1 for r in results if r["status"] == "ok")
    summary = {
        "console": args.console,
        "platform": config.platform,
        "api_url": config.api_url,
        "gateway_url": config.gateway_url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "connectivity": conn,
        "connected": connected,
        "probes_total": len(results),
        "probes_ok": ok,
        "results": results,
    }

    out = Path(args.out) if args.out else Path("reports") / f"{args.console}-readonly-audit"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        f"# Qualys live read-only audit — console: {args.console}",
        "",
        f"- Platform: {config.platform}  |  API: {config.api_url}",
        f"- Gateway: {config.gateway_url}",
        f"- Connected (FO auth): **{connected}**",
        f"- Probes OK: **{ok}/{len(results)}**",
        f"- Generated: {summary['timestamp']}",
        "",
        "| Module | Probe tool | Family | Status | Detail |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['module']} | {r['tool']} | {r['family']} | {r['status']} | "
            f"{str(r.get('detail','')).replace('|', '/')[:120]} |"
        )
    out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[{args.console}] connected={connected} probes_ok={ok}/{len(results)} -> {out}.md")
    return 0 if connected else 1


if __name__ == "__main__":
    sys.exit(main())
