# Qualys MCP — Module Build Guide (contract for builder agents)

Every feature module follows this exact contract so the parallel build stays
consistent and auto-discovery works. **Read this fully before writing a module.**
Use the two reference modules as your templates:

- Read-only: `qualys_mcp/modules/knowledgebase.py`
- Read + write + destructive: `qualys_mcp/modules/vm_scans.py`

## 1. File & class conventions
- One file per module in `qualys_mcp/modules/<snake_name>.py`.
- One class named `<CamelName>Module(BaseModule)`. The registry name is the
  class name lowercased minus `Module` (e.g. `HostAssetsModule` -> `hostassets`).
  Keep the CamelName a single token where possible so the registry name has no
  surprises (e.g. `VmScansModule` -> `vmscans`).
- Set `module_label` to a short human string (used in "not entitled" errors).
- Import only: `from typing import Any`, `from mcp.server import FastMCP`,
  `from qualys_mcp.modules.base import BaseModule`. Do **not** import other
  modules or touch shared files.

## 2. Registration
```python
def register_tools(self, server: FastMCP) -> None:
    self._add_tool(server, self.list_x, "list_x", tier="read")
    self._add_tool(server, self.create_x, "create_x", tier="write")
    self._add_tool(server, self.delete_x, "delete_x", tier="destructive")
```
- Tool names are auto-prefixed with `qualys_`. Do **not** add the prefix yourself.
- Name tools `<verb>_<noun>`; keep them unique across the whole server
  (prefix with your domain if collision is likely, e.g. `list_was_scans`).

## 3. Safety tiers (pick correctly — the audit checks this)
| Tier | Use for | Annotation |
|---|---|---|
| `read` | list/get/search/fetch/status/count/export-read | read-only |
| `write` | create/update/add/launch/pause/resume/import/assign | write |
| `destructive` | delete/purge/remove/deactivate/cancel-permanent | destructive |

Every `destructive` tool MUST:
1. Take a `confirm: str | None = None` parameter (last positional).
2. Call the guard first and return early:
   ```python
   guard = self._confirm_or_error(confirm, expected=<target_id>)
   if guard:
       return guard
   ```
`_add_tool` hides destructive tools entirely unless the console runs with
`QUALYS_ENABLE_DESTRUCTIVE=true`, so never rely on them always being present.

## 4. Calling the API — use the client regime wrappers
- Classic FO (`/api/2.0/fo/...`, `/msp/...`): `self._fo(path, method=..., params=..., data=...)`
  - GET reads use `params=`; POST actions use `data=` and include `"action": "..."`.
  - Booleans auto-convert to `1`/`0`; lists auto-join to CSV; `None` is dropped.
  - Returns a parsed dict (XML normalized). Pass `parse=False` for CSV/binary.
  - **Raw request body**: for import/create endpoints that need a verbatim XML
    or JSON payload (not form fields), pass `content=<str|bytes>` and
    `content_type=` (e.g. `"text/xml"` or `"application/json"`); `data` is then
    ignored. Use this for option-profile / compliance-policy imports and any
    JSON-body FO action.
- QPS REST (`/qps/rest/...`): `self._qps(path, method=..., body_xml=..., params=..., accept="xml"|"json")`
  - Build the `<ServiceRequest>` XML body as a string when filtering/creating.
- Gateway/JWT (`/...` on the gateway host): `self._gateway(path, method=..., params=..., json=...)`
  - JWT is fetched/refreshed automatically. Bodies are JSON.

Return the wrapper's result directly. Do not catch and swallow errors — the
client already normalizes failures to `{"error": ...}`.

## 5. Tool method style
- Full type hints on every parameter and `-> dict[str, Any]` return.
- Google-style docstring: one-line summary, then `Args:` (document EVERY param,
  including valid enum values and formats) and `Returns:` (name the Qualys
  output envelope). The docstring is what the model sees — be precise about
  filters, date formats (`YYYY-MM-DD[THH:MM:SSZ]`), and id formats.
- Prefer flat scalar params over nested dicts so the tool schema is model-friendly.
- Do not add pagination loops that fetch everything; expose Qualys's own
  paging params (`id_min`, `truncation_limit`, `lastId`, etc.) and return one page.

## 6. Validate before you hand off
From the repo root:
```
.\.venv\Scripts\python.exe -m qualys_mcp --check
```
Your module must appear with the expected tool count and cause **no** errors.
Then run destructive-enabled to confirm your destructive tools appear:
```
$env:QUALYS_ENABLE_DESTRUCTIVE='true'; .\.venv\Scripts\python.exe -m qualys_mcp --check
```

## 7. Source of truth for endpoints
- Classic VM/PC: `qualys-api-vmpc-user-guide.pdf` (repo root, 1911 pp).
  Extract the section for your cluster with:
  ```
  pdftotext -f <startpage> -l <endpage> qualys-api-vmpc-user-guide.pdf - | less
  ```
- Everything else (QPS/Gateway families): the online docs index
  https://docs.qualys.com/en/vm/api/index.htm and the per-product API guides.
- If an endpoint's exact params are uncertain, encode what the docs specify and
  add a `# TODO(verify): <what>` comment rather than guessing silently.

## 8. Do NOT touch (owned by the orchestrator)
`base.py`, `registry.py`, `client.py`, `server.py`, `config.py`, everything in
`common/`, `pyproject.toml`. If you need a new shared helper, note it in your
final report instead of editing shared files.
