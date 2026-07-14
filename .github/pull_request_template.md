## Summary

<!-- What does this change and why? -->

## Type of change
- [ ] New module (`qualys_mcp/modules/<name>.py`)
- [ ] New tool(s) on an existing module
- [ ] Bug fix
- [ ] Docs / tests / CI

## Checklist
- [ ] `python -m qualys_mcp --check` passes and lists the module with its tool count
- [ ] `ruff check .` is clean
- [ ] `pytest -q` passes
- [ ] Every new tool is classified into the correct safety tier (read / write / destructive)
- [ ] Destructive tools take a `confirm` arg and use `_confirm_or_error`
- [ ] No credentials, tokens, real hostnames/IPs, or scan output in the diff
- [ ] API calls go through `self._fo` / `self._qps` / `self._gateway` (no ad‑hoc httpx)
