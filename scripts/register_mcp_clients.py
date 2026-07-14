"""Register the Qualys MCP (local HTTP) into every MCP client on this machine.

Adds two servers — qualys-consulting (:8781) and qualys-cloud (:8782) — to each
client using a local-HTTP pattern. MCP is registered over local HTTP only (no
remote transport): every entry points at 127.0.0.1/localhost. Idempotent:
re-running updates the entries in place. Each
edited file is backed up once to "<file>.bak-qualys" before the first change.

Run:  python scripts/register_mcp_clients.py            (apply)
      python scripts/register_mcp_clients.py --dry-run  (preview only)
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
APPDATA = Path(os.environ.get("APPDATA", HOME / "AppData/Roaming"))

CONSOLES = {"qualys-consulting": 8781, "qualys-cloud": 8782}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _save(path: Path, data, dry: bool) -> None:
    if dry:
        return
    backup = path.with_suffix(path.suffix + ".bak-qualys")
    if not backup.exists():
        shutil.copy2(path, backup)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def register(path: Path, container_key: str, entry_fn, dry: bool) -> str:
    """Add the console entries into path[container_key] using entry_fn(port)."""
    if not path.exists():
        return f"skip  (not found)   {path}"
    try:
        data = _load(path)
    except Exception as exc:  # noqa: BLE001
        return f"ERROR (bad json {exc}) {path}"
    container = data.setdefault(container_key, {})
    changed = []
    for name, port in CONSOLES.items():
        desired = entry_fn(port)
        if container.get(name) != desired:
            container[name] = desired
            changed.append(name)
    _save(path, data, dry)
    verb = "would add/update" if dry else "added/updated"
    return f"ok    {verb} {changed or 'nothing (already current)'}  ->  {path}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = args.dry_run

    targets = [
        # Claude Desktop — stdio bridge to local HTTP via mcp-remote (Falcon pattern)
        (
            APPDATA / "Claude/claude_desktop_config.json",
            "mcpServers",
            lambda port: {"command": "npx", "args": ["-y", "mcp-remote", f"http://127.0.0.1:{port}/mcp"]},
        ),
        # OpenCode — "remote" (url-based) local server
        (
            HOME / ".config/opencode/opencode.json",
            "mcp",
            lambda port: {"type": "remote", "url": f"http://127.0.0.1:{port}/mcp", "enabled": True},
        ),
        # Antigravity (serverUrl format)
        (
            HOME / ".antigravity/mcp_config.json",
            "mcpServers",
            lambda port: {"serverUrl": f"http://localhost:{port}/mcp"},
        ),
        # Antigravity (gemini type/url format) — two active copies
        (
            HOME / ".gemini/config/mcp_config.json",
            "mcpServers",
            lambda port: {"type": "http", "url": f"http://127.0.0.1:{port}/mcp"},
        ),
        (
            HOME / ".gemini/antigravity-ide/mcp_config.json",
            "mcpServers",
            lambda port: {"type": "http", "url": f"http://127.0.0.1:{port}/mcp"},
        ),
    ]

    print(f"{'DRY-RUN: ' if dry else ''}Registering {list(CONSOLES)} into MCP clients\n")
    for path, key, fn in targets:
        print(" ", register(path, key, fn, dry))
    print(
        "\nNote: Claude Code uses the project's .mcp.json (already provided in this "
        "repo) when the project folder is opened."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
