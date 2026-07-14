# AGENTS.md

See [CLAUDE.md](CLAUDE.md) for full guidance and
[docs/MODULE_BUILD_GUIDE.md](docs/MODULE_BUILD_GUIDE.md) for the module contract.

TL;DR for building a module:
- Add one file `qualys_mcp/modules/<name>.py` with a `<Name>Module(BaseModule)`.
- Register tools via `self._add_tool(server, self.<fn>, "<tool_name>", tier=...)`.
- Call the API with `self._fo` / `self._qps` / `self._gateway`.
- Destructive tools: `confirm` arg + `_confirm_or_error` guard.
- Validate with `python -m qualys_mcp --check`. Don't touch framework files.
