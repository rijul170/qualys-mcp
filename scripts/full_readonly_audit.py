"""Comprehensive READ-ONLY audit of one Qualys console.

Exercises EVERY read-tier tool (MCP ``readOnlyHint=True``) across all modules,
calling the ones whose parameters are all optional (bounded to tiny result
pages) and reporting per-tool status + per-module entitlement. It NEVER calls a
write or destructive tool:

* the client is built with ``enable_destructive=False`` so destructive tools are
  not even registered, and
* only tools whose annotation is read-only are ever invoked.

Read tools that require arguments (e.g. get-by-id) are listed but not called
(no valid IDs to pass safely). Output: JSON + Markdown under reports/.

Usage (via run-full-audit.ps1):
    python scripts/full_readonly_audit.py --console cloud --out reports/cloud-full
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qualys_mcp.client import QualysClient
from qualys_mcp.config import QualysConfig
from qualys_mcp.registry import get_available_modules

# Small bounding values injected when a read tool exposes a known paging/limit
# param, so we never pull a whole subscription during the audit.
BOUND_KWARGS: dict[str, Any] = {
    "truncation_limit": 2,
    "limit": 2,
    "pageSize": 2,
    "page_size": 2,
    "rows": 2,
    "batch": 1,
    "details": "Basic",
    "detail": "Basic",
    "num_records": 2,
}

# Per-method overrides for no-required-arg tools that would otherwise return a
# very large dataset (keyed by the underlying method name).
OVERRIDES: dict[str, dict[str, Any]] = {
    "list_knowledgebase": {"ids": "90001"},  # avoid pulling the entire KB
    "get_qids": {"ids": "90001"},
}


def _read_tools(client: QualysClient) -> list[tuple[str, str, Any, Any]]:
    """Return [(module, tool_name, bound_method, annotations)] for read tools only."""
    out: list[tuple[str, str, Any, Any]] = []
    for module_name, module_class in get_available_modules().items():
        module = module_class(client)

        class _Stub:
            def __init__(self) -> None:
                self.captured: list[tuple[str, Any, Any]] = []

            def add_tool(self, fn: Any, name: str | None = None, annotations: Any = None) -> None:
                self.captured.append((name, fn, annotations))

        stub = _Stub()
        try:
            module.register_tools(stub)  # type: ignore[arg-type]
        except Exception:  # noqa: BLE001
            continue
        for name, fn, ann in stub.captured:
            if getattr(ann, "readOnlyHint", False):
                out.append((module_name, name, fn, ann))
    return out


def _callable_kwargs(fn: Any) -> tuple[bool, dict[str, Any], list[str]]:
    """Decide if a read tool is safe to call with no user input.

    Returns (callable_now, kwargs_to_pass, required_param_names).
    A tool is callable_now only if every parameter has a default.
    """
    sig = inspect.signature(fn)
    required: list[str] = []
    kwargs: dict[str, Any] = {}
    for pname, p in sig.parameters.items():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        if p.default is inspect.Parameter.empty:
            required.append(pname)
        elif pname in BOUND_KWARGS:
            kwargs[pname] = BOUND_KWARGS[pname]
    kwargs.update(OVERRIDES.get(getattr(fn, "__name__", ""), {}))
    # Only keep override keys that are real params of this tool.
    valid = set(inspect.signature(fn).parameters)
    kwargs = {k: v for k, v in kwargs.items() if k in valid}
    return (len(required) == 0, kwargs, required)


def _classify(result: Any, connected: bool) -> tuple[str, str]:
    if isinstance(result, dict) and "error" in result:
        code = str(result.get("qualys_code", ""))
        sc = result.get("status_code")
        text = str(result.get("error", ""))[:180]
        low = text.lower()
        if code == "NOT_ENTITLED" or any(
            s in low for s in ("not authorized", "not subscribed", "not activated", "no permission", "not enabled", "not entitled")
        ):
            return "not_entitled", text
        if sc in (401, 403):
            return ("not_entitled" if connected else "auth_error"), text
        if sc in (409, 429):
            return "rate_limited", text
        return "error", text
    if isinstance(result, dict):
        keys = ",".join(list(result.keys())[:4])
        return "ok", f"keys: {keys}"
    return "ok", type(result).__name__


def main() -> int:
    parser = argparse.ArgumentParser(description="Qualys comprehensive read-only audit")
    parser.add_argument("--console", required=True)
    parser.add_argument("--out", default=None)
    parser.add_argument("--delay", type=float, default=0.15, help="seconds between calls")
    args = parser.parse_args()

    # Force destructive OFF regardless of environment — belt and suspenders.
    config = QualysConfig.from_env(console_label=args.console)
    config.enable_destructive = False
    try:
        config.require_credentials()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    client = QualysClient(config)
    conn = client.verify_connectivity()
    connected = bool(isinstance(conn, dict) and conn.get("connected"))

    # Canary: Qualys code 2003 ("Registration must be completed before API
    # requests will be processed") blocks every functional call. Detect it once
    # and abort early with a clear message instead of probing 100+ tools.
    canary = client.fo(
        "/api/2.0/fo/asset/group/", method="GET", params={"action": "list", "truncation_limit": "1"}
    )
    canary_err = str(canary.get("error", "")) if isinstance(canary, dict) else ""
    if "registration must be completed" in canary_err.lower():
        msg = (
            f"[{args.console}] connected={connected} but API is BLOCKED: Qualys code 2003 - "
            f"the API user must complete registration (log into the Qualys UI once and accept "
            f"the EULA / set a permanent password) before any API request will be processed."
        )
        print(msg)
        out = Path(args.out) if args.out else Path("reports") / f"{args.console}-full-readonly-audit"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.with_suffix(".md").write_text("# " + msg + "\n", encoding="utf-8")
        return 3

    tools = _read_tools(client)
    results: list[dict[str, Any]] = []
    for module_name, tool_name, fn, _ann in tools:
        entry: dict[str, Any] = {"module": module_name, "tool": tool_name}
        callable_now, kwargs, required = _callable_kwargs(fn)
        if not callable_now:
            entry.update(status="skipped_needs_args", detail=f"requires: {', '.join(required)}")
            results.append(entry)
            continue
        try:
            res = fn(**kwargs)
            status, detail = _classify(res, connected)
        except Exception as exc:  # noqa: BLE001
            status, detail = "exception", f"{type(exc).__name__}: {exc}"[:180]
        entry.update(status=status, detail=detail)
        results.append(entry)
        time.sleep(args.delay)

    # Roll up per-module entitlement: entitled if any read tool returned ok.
    modules: dict[str, dict[str, int]] = {}
    for r in results:
        m = modules.setdefault(r["module"], {"ok": 0, "not_entitled": 0, "error": 0, "skipped": 0, "other": 0})
        s = r["status"]
        if s == "ok":
            m["ok"] += 1
        elif s == "not_entitled":
            m["not_entitled"] += 1
        elif s == "skipped_needs_args":
            m["skipped"] += 1
        elif s in ("error", "exception", "auth_error", "rate_limited"):
            m["error"] += 1
        else:
            m["other"] += 1

    def module_verdict(c: dict[str, int]) -> str:
        if c["ok"] > 0:
            return "ENTITLED"
        if c["not_entitled"] > 0 and c["error"] == 0:
            return "not_subscribed"
        if c["error"] > 0:
            return "needs_review"
        return "only_arg_tools"

    counts = {
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "not_entitled": sum(1 for r in results if r["status"] == "not_entitled"),
        "error": sum(1 for r in results if r["status"] in ("error", "exception", "auth_error")),
        "rate_limited": sum(1 for r in results if r["status"] == "rate_limited"),
        "skipped_needs_args": sum(1 for r in results if r["status"] == "skipped_needs_args"),
    }

    summary = {
        "console": args.console,
        "platform": config.platform,
        "api_url": config.api_url,
        "gateway_url": config.gateway_url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "connected": connected,
        "connectivity": conn,
        "read_tools_total": len(tools),
        "counts": counts,
        "module_verdicts": {m: module_verdict(c) for m, c in sorted(modules.items())},
        "results": results,
    }

    out = Path(args.out) if args.out else Path("reports") / f"{args.console}-full-readonly-audit"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        f"# Qualys comprehensive read-only audit — {args.console}",
        "",
        f"- Platform {config.platform} | API {config.api_url}",
        f"- Connected (FO auth): **{connected}**",
        f"- Read tools: {len(tools)} — ok **{counts['ok']}**, not_entitled {counts['not_entitled']}, "
        f"error {counts['error']}, rate_limited {counts['rate_limited']}, "
        f"needs-args (not called) {counts['skipped_needs_args']}",
        f"- Generated {summary['timestamp']}",
        "",
        "## Per-module verdict",
        "",
        "| Module | Verdict | ok | not_entitled | error | needs-args |",
        "|---|---|---|---|---|---|",
    ]
    for m, c in sorted(modules.items()):
        lines.append(
            f"| {m} | {module_verdict(c)} | {c['ok']} | {c['not_entitled']} | {c['error']} | {c['skipped']} |"
        )
    lines += ["", "## Per-tool detail", "", "| Module | Tool | Status | Detail |", "|---|---|---|---|"]
    for r in results:
        lines.append(
            f"| {r['module']} | {r['tool']} | {r['status']} | "
            f"{str(r.get('detail','')).replace('|','/')[:120]} |"
        )
    out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        f"[{args.console}] connected={connected} read_tools={len(tools)} "
        f"ok={counts['ok']} not_entitled={counts['not_entitled']} error={counts['error']} "
        f"needs_args={counts['skipped_needs_args']} -> {out}.md"
    )
    return 0 if connected else 1


if __name__ == "__main__":
    sys.exit(main())
