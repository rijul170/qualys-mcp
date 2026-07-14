# Qualys MCP

> A [Model Context Protocol](https://modelcontextprotocol.io) server for **full Qualys portal management** — expose VMDR, Policy Compliance, WAS, Cloud Agent, Container Security, TotalCloud, Patch Management, CSAM/GAV, EASM and administration to any MCP‑capable client (Claude, and other MCP hosts).

<p>
  <a href="https://github.com/rijul170/qualys-mcp/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/rijul170/qualys-mcp/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue.svg">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-green.svg">
  <img alt="MCP" src="https://img.shields.io/badge/MCP-server-black.svg">
  <img alt="Tools" src="https://img.shields.io/badge/tools-400%2B-orange.svg">
</p>

One process per Qualys console (run as many as you have subscriptions). Built on
[FastMCP](https://github.com/jlowin/fastmcp), with a single client that speaks all
three Qualys API families, a strict read / write / destructive safety model, and
credentials that never touch chat or plaintext.

---

## Highlights

- **Broad coverage** — 59 auto‑discovered feature modules spanning the whole
  portal: VMDR, PC, WAS, Cloud Agent, Container Security, TotalCloud/CloudView,
  Patch Management, CSAM/GAV, EASM, FIM, EDR, PCRS, and administration.
- **~400 tools** — `list_hosts`, `list_host_detections`, `launch_scan`,
  `search_was_findings`, `list_knowledgebase`, `get_cs_image_vulnerabilities`,
  and hundreds more, each mapped 1:1 to a documented Qualys API operation.
- **Three API regimes, one client** — the classic "FO" XML API, the QPS REST
  API, and the JWT‑authenticated Gateway are all handled behind `self._fo` /
  `self._qps` / `self._gateway`.
- **Safety tiers are load‑bearing** — every tool is annotated read‑only, write,
  or destructive. Destructive tools (delete / purge / deactivate) are **not even
  registered** unless you opt in per console, and still require a per‑call
  confirmation token.
- **Lazy auth** — no network calls at import or construction; `--check` runs
  fully offline with no credentials.
- **Secrets stay secret** — on Windows, credentials live only in DPAPI‑encrypted
  blobs; on any OS you can supply them via environment variables. Nothing is ever
  written to the repo.

## The three API regimes

| Regime | Base path | Auth | Payload |
|---|---|---|---|
| Classic "FO" | `/api/2.0/fo/`, `/msp/` | Basic + `X-Requested-With` header | form → XML |
| QPS REST | `/qps/rest/` | Basic | XML `<ServiceRequest>` / JSON |
| Gateway | `gateway.<pod>.apps.qualys.com` | Bearer JWT (from `/auth`) | JSON |

## Architecture

```
qualys_mcp/
  server.py     FastMCP server; lazy auth; --check offline validation
  registry.py   auto-discovers modules/*.py
  client.py     one client, three API regimes (FO / QPS / Gateway-JWT)
  config.py     per-console config + platform (POD) -> URL map
  common/       auth (HTTP mw), errors, logging, rate_limit, utils, xml
  modules/      base.py + one file per feature module (the bulk of the surface)
```

Adding a capability is just dropping a file in `qualys_mcp/modules/` — see
[docs/MODULE_BUILD_GUIDE.md](docs/MODULE_BUILD_GUIDE.md).

## Quick start

### 1. Install

```bash
python -m venv .venv
# Windows:      .\.venv\Scripts\pip install -e .
# macOS/Linux:  ./.venv/bin/pip install -e .
```

### 2. Offline sanity check (no credentials required)

```bash
python -m qualys_mcp --check
```

Lists every discovered module with its tool count and exits — a good first
smoke test.

### 3. Provide credentials

You need a Qualys **API user** and your platform/POD code (e.g. `US1`, `US2`,
`EU1`; find it under your console URL or **Help → About**).

**Any OS — environment variables:**

```bash
export QUALYS_USERNAME='api-user'
export QUALYS_PASSWORD='api-pass'
export QUALYS_PLATFORM='US2'          # or set QUALYS_API_URL / QUALYS_GATEWAY_URL
python -m qualys_mcp --transport streamable-http --host 127.0.0.1 --port 8781 --console-label consulting
```

**Windows — DPAPI‑encrypted blobs (recommended for a persistent deployment):**

```powershell
# Encrypt once per console; the blob is user-scoped and stored under .secrets/
.\encrypt-qualys-creds.ps1 -Console consulting -Platform US2
.\encrypt-qualys-creds.ps1 -Console cloud      -Platform US2

# Launch one instance per console (:8781, :8782)
.\start-qualys-mcp.ps1
#   ...opt into destructive tools for a console only when you mean it:
.\start-qualys-mcp.ps1 -EnableDestructive cloud

# Optional: keep both alive across reboots via a Scheduled Task watchdog
.\register-qualys-mcp-task.ps1
```

See [.env.example](.env.example) for every `QUALYS_*` setting.

### 4. Point your MCP client at it

A ready‑to‑use [`.mcp.json`](.mcp.json) is included for Claude Code:

```json
{
  "mcpServers": {
    "qualys-consulting": { "type": "http", "url": "http://localhost:8781/mcp" },
    "qualys-cloud":      { "type": "http", "url": "http://localhost:8782/mcp" }
  }
}
```

`scripts/register_mcp_clients.py` shows how to register the same local‑HTTP
servers into several MCP clients at once.

## Safety model

- Tools are annotated **read‑only**, **write**, or **destructive**.
- Destructive tools (delete, purge, deactivate, uninstall) are **not registered**
  unless the console runs with `QUALYS_ENABLE_DESTRUCTIVE=true`.
- Even when enabled, each destructive tool requires a matching `confirm=<id>`
  argument before it will act — so a destructive call can never happen by
  accident from a single prompt.

Read [docs/SAFETY_AUDIT.md](docs/SAFETY_AUDIT.md) for the full tiering.

## Module & tool inventory

- **59 modules** auto‑discovered from `qualys_mcp/modules/`.
- **~360 tools** registered by default; **~400** with
  `QUALYS_ENABLE_DESTRUCTIVE=true` (the extra ~40 are the guarded destructive
  tools that otherwise stay hidden).
- Spread across the three API regimes, with a handful of modules spanning two.

The full per‑module table (registry name, API family, tool counts, one‑line
description) is in [docs/MODULE_INDEX.md](docs/MODULE_INDEX.md), and a complete
endpoint → tool → action breakdown is in
[docs/ENDPOINTS_TOOLS_ACTIONS.md](docs/ENDPOINTS_TOOLS_ACTIONS.md).

## Configuration reference

| Variable | Purpose |
|---|---|
| `QUALYS_USERNAME` / `QUALYS_PASSWORD` | API user credentials |
| `QUALYS_PLATFORM` | POD code (`US1`…`KSA1`) — auto‑fills API + Gateway URLs |
| `QUALYS_API_URL` / `QUALYS_GATEWAY_URL` | Explicit overrides for unlisted PODs |
| `QUALYS_CONSOLE_LABEL` | Names the console in logs and the server name |
| `QUALYS_ENABLE_DESTRUCTIVE` | `true` to register the destructive tier |
| `QUALYS_MCP_MODULES` | Comma‑separated allowlist to scope a console to its licensed modules |
| `QUALYS_MCP_API_KEY` | Optional shared secret for the HTTP transport |

## Development

```bash
pip install -e ".[dev]"
python -m qualys_mcp --check   # offline validation
pytest                          # unit tests (no network)
ruff check .                    # lint
```

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Disclaimer

This is an independent, community project. It is **not affiliated with,
endorsed by, or supported by Qualys, Inc.** "Qualys" and product names are
trademarks of their respective owners. Use against your own subscriptions in
accordance with your Qualys license and API terms. The software is provided
"as is" (see [LICENSE](LICENSE)); you are responsible for what you run against
your environment — especially the destructive tier.

## Star history

<a href="https://star-history.com/#rijul170/qualys-mcp&Date">
  <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=rijul170/qualys-mcp&type=Date">
</a>

## License

[MIT](LICENSE) © 2026 Rijul Sharma
