"""Live tool-availability + parity audit for both running Qualys MCP servers.

Connects to each server over the MCP streamable-HTTP protocol (the same way a
client does), pulls the authoritative tools/list, and compares:
  * each console's exposed tools vs the expected registry sets
    (destructive-off = 360, destructive-on = 403), and
  * the two consoles against each other (parity).
Also reports enabled-module count and connectivity per console.

Writes reports/tool-availability-audit.md. Run:  python scripts/audit_tools.py
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from qualys_mcp import registry
from qualys_mcp.client import QualysClient
from qualys_mcp.config import QualysConfig

CONSOLES = {"qualys-consulting": 8781, "qualys-cloud": 8782}


def expected_sets():
    """Build the expected tool-name sets from the registry (destructive off/on)."""

    def build(enable: bool) -> set[str]:
        cfg = QualysConfig(
            username="x", password="x", api_url="https://x", gateway_url="https://x",
            enable_destructive=enable,
        )
        client = QualysClient(cfg)
        names = ["qualys_check_connectivity", "qualys_list_enabled_modules", "qualys_list_modules"]
        for _n, cls in registry.get_available_modules().items():
            m = cls(client)

            class _Stub:
                def add_tool(self, fn, name=None, annotations=None):
                    names.append(name)

            m.register_tools(_Stub())
        return set(names)

    return build(False), build(True)


async def probe(port: int):
    url = f"http://127.0.0.1:{port}/mcp"
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = sorted(t.name for t in tools.tools)
            enabled = await session.call_tool("qualys_list_enabled_modules", {})
            conn = await session.call_tool("qualys_check_connectivity", {})

            def _text(res):
                try:
                    return res.content[0].text
                except Exception:  # noqa: BLE001
                    return str(res)

            return names, _text(enabled), _text(conn)


async def main() -> int:
    ro, full = expected_sets()
    destructive_only = full - ro
    lines = [
        "# Qualys MCP — live tool-availability & parity audit",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Expected tools: **{len(ro)}** (destructive off) / **{len(full)}** (destructive on); "
        f"{len(destructive_only)} destructive-gated.",
        "",
    ]
    print(lines[3])

    results = {}
    for name, port in CONSOLES.items():
        try:
            names, enabled, conn = await probe(port)
        except Exception as exc:  # noqa: BLE001
            msg = f"[{name}] ERROR connecting on :{port} -> {exc}"
            print(msg)
            lines.append(f"## {name} :{port}\n\n- **UNREACHABLE**: {exc}\n")
            continue
        got = set(names)
        results[name] = got
        match = "FULL (403, destructive on)" if got == full else (
            "READ+WRITE (360, destructive off)" if got == ro else "NON-STANDARD"
        )
        missing = sorted(ro - got)      # expected read/write tools that are absent
        unexpected = sorted(got - full)  # tools not in any known set
        has_destr = bool(got & destructive_only)
        try:
            mod_count = len(json.loads(enabled).get("modules", []))
        except Exception:  # noqa: BLE001
            mod_count = "?"
        connected = "connected" if '"connected": true' in conn.lower() or '"connected":true' in conn.lower() else conn[:80]

        print(f"[{name}] :{port}  tools={len(got)}  match={match}  enabled_modules={mod_count}  destructive={'ON' if has_destr else 'off'}")
        if missing:
            print(f"   MISSING read/write tools: {missing}")
        if unexpected:
            print(f"   UNEXPECTED tools: {unexpected}")

        lines += [
            f"## {name} :{port}",
            "",
            f"- Connectivity: {connected}",
            f"- Enabled modules: **{mod_count}** / {len(registry.get_module_names())} discovered",
            f"- Tools exposed: **{len(got)}**  → {match}",
            f"- Destructive tools registered: **{'YES' if has_destr else 'no'}**",
            f"- Missing (expected read/write) : {missing or 'none'}",
            f"- Unexpected (unknown) tools    : {unexpected or 'none'}",
            "",
        ]

    if len(results) == 2:
        c, k = results["qualys-consulting"], results["qualys-cloud"]
        only_cloud = sorted(k - c)
        only_cons = sorted(c - k)
        print(f"\nPARITY  consulting={len(c)}  cloud={len(k)}  only-in-cloud={len(only_cloud)}  only-in-consulting={len(only_cons)}")
        lines += [
            "## Parity between consoles",
            "",
            f"- consulting: {len(c)} tools | cloud: {len(k)} tools",
            f"- Only in **cloud** ({len(only_cloud)}): {only_cloud or 'none'}",
            f"- Only in **consulting** ({len(only_cons)}): {only_cons or 'none'}",
            "",
            "Note: a difference equal to the destructive-gated set is expected when the "
            "two consoles run with different QUALYS_ENABLE_DESTRUCTIVE settings — not a build gap.",
            "",
        ]

    out = Path("reports/tool-availability-audit.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nreport -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
