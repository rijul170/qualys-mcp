# Contributing to Qualys MCP

Thanks for your interest in improving Qualys MCP! Contributions of all
sizes are welcome — new modules, bug fixes, docs, and tests.

## Ground rules

The framework files are load‑bearing and change rarely:

- `client.py`, `server.py`, `registry.py`, `config.py`,
  `modules/base.py`, and everything under `common/` are the framework.
- **New capabilities are added as new files under `qualys_mcp/modules/`** —
  you should almost never need to edit the framework to add a tool.

See [docs/MODULE_BUILD_GUIDE.md](docs/MODULE_BUILD_GUIDE.md) for the module
contract, and [CLAUDE.md](CLAUDE.md) for the design golden rules.

## Adding a module

1. Create `qualys_mcp/modules/<name>.py` with a `class <Name>Module(BaseModule)`.
2. Register each tool: `self._add_tool(server, self.<fn>, "<tool_name>", tier="read|write|destructive")`.
3. Call the Qualys API only through `self._fo` / `self._qps` / `self._gateway`.
4. Destructive tools **must** take a `confirm` argument and guard with
   `self._confirm_or_error(...)`.
5. Keep auth lazy — no network calls at import or construction.

## Before you open a PR

```bash
python -m qualys_mcp --check   # module must appear with its tool count
pytest                          # unit tests, no network required
ruff check .                    # lint
```

- Classify every new tool into the correct safety tier. When in doubt, choose
  the more conservative tier.
- Never commit credentials, tokens, real hostnames/IPs, or scan output. The
  `.gitignore` already excludes `.secrets/`, `.env*`, `logs/`, and `reports/` —
  double‑check your diff regardless.
- Match the surrounding code style (type hints, docstrings that describe the
  Qualys parameters, no ad‑hoc `httpx` calls).

## Reporting bugs / requesting features

Open an issue with what you expected, what happened, the Qualys module/tool
involved, and (for bugs) a minimal repro. **Never paste credentials, JWTs, or
raw scan data** into an issue.

## License

By contributing, you agree that your contributions are licensed under the
project's [MIT License](LICENSE).
