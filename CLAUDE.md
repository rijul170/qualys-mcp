# CLAUDE.md — Qualys MCP

Guidance for AI agents working in this repo.

## What this is
An MCP server exposing the full Qualys portal, one process per console
(`qualys-consulting` :8781, `qualys-cloud` :8782). Python + FastMCP. Patterned
on the Falcon MCP (two-instance streamable-http, DPAPI creds, PS launcher) and
the AlertLogic MCP (raw HTTP client, module-per-file).

## Golden rules
1. **Never edit shared files casually.** `client.py`, `server.py`, `registry.py`,
   `config.py`, `modules/base.py`, and `common/*` are the framework. Modules only
   add files under `modules/`.
2. **Auth is lazy.** No network at import/construction. `--check` must always work
   with no creds. Don't add eager `login()` calls.
3. **Three regimes, one client.** Use `self._fo` / `self._qps` / `self._gateway`.
   Don't build ad-hoc `httpx` calls in modules.
4. **Safety tiers are load-bearing.** Classify every tool read/write/destructive.
   Destructive tools need a `confirm` arg + `_confirm_or_error` guard and are
   hidden unless `QUALYS_ENABLE_DESTRUCTIVE=true`.
5. **Secrets never touch chat or plaintext.** Credentials live only in
   DPAPI blobs under `.secrets/`, created by `encrypt-qualys-creds.ps1`.

## Validate
```
.\.venv\Scripts\python.exe -m qualys_mcp --check
```
Expect no errors and your module listed with its tool count.

## Reference material
- `docs/MODULE_BUILD_GUIDE.md` — the module contract.
- Qualys VM/PC API User Guide (official PDF from your Qualys console under
  Help > Resources, or docs.qualys.com) — the classic VM/PC API reference.
- Reference modules: `modules/knowledgebase.py` (read), `modules/vm_scans.py` (all tiers).

## Platform (POD) map
`config.PLATFORMS` maps `US1..KSA1` to API + Gateway URLs. Unknown PODs: set
`QUALYS_API_URL` / `QUALYS_GATEWAY_URL` explicitly.
