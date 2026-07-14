"""Qualys MCP Server — main entry point.

One process serves one Qualys console. Modules are auto-discovered and each
registers its tools. Authentication is lazy, so ``--check`` can enumerate every
module and tool with no credentials configured (used by the offline audit).
"""

import argparse
import os
import sys
from typing import Literal

import uvicorn
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from qualys_mcp import __version__, registry
from qualys_mcp.client import QualysClient
from qualys_mcp.common.auth import (
    ASGIApp,
    auth_middleware,
    normalize_content_type_middleware,
    strip_trailing_slash_middleware,
)
from qualys_mcp.common.logging import configure_logging, get_logger
from qualys_mcp.config import QualysConfig
from qualys_mcp.modules.base import READ_ONLY_ANNOTATIONS

logger = get_logger(__name__)

TransportType = Literal["stdio", "sse", "streamable-http"]


class QualysMCPServer:
    """MCP server for a single Qualys console."""

    def __init__(
        self,
        config: QualysConfig,
        enabled_modules: set[str] | None = None,
        stateless_http: bool = False,
        api_key: str | None = None,
        host: str = "127.0.0.1",
        port: int = 8781,
    ):
        self.config = config
        self.api_key = api_key
        self.host = host
        self.port = port
        self.stateless_http = stateless_http

        configure_logging(debug=config.debug)
        self.enabled_modules = enabled_modules or set(registry.get_module_names())

        self.client = QualysClient(config)

        self.server = FastMCP(
            name=f"Qualys MCP ({config.console_label})",
            instructions=(
                "This server provides access to a Qualys console: VMDR, Policy "
                "Compliance, WAS, Cloud Agent, Container Security, TotalCloud, "
                "Patch Management, CSAM/GAV, EASM and administration."
            ),
            debug=config.debug,
            log_level="DEBUG" if config.debug else "INFO",
            stateless_http=stateless_http,
            host=host,
            port=port,
        )
        self.server._mcp_server.version = __version__

        # Instantiate enabled + available modules.
        self.modules: dict[str, object] = {}
        available = registry.get_available_modules()
        for name in self.enabled_modules:
            module_class = available.get(name)
            if module_class is None:
                logger.warning("Requested module '%s' not found; skipping.", name)
                continue
            self.modules[name] = module_class(self.client)

        tool_count = self._register_tools()
        logger.info(
            "Qualys MCP v%s (%s) - %d modules, %d tools%s",
            __version__,
            config.console_label,
            len(self.modules),
            tool_count,
            "" if config.enable_destructive else " [destructive disabled]",
        )

    # ------------------------------------------------------------------ #
    def _register_tools(self) -> int:
        """Register core tools + all module tools. Returns total tool count."""
        self.server.add_tool(
            self.qualys_check_connectivity,
            name="qualys_check_connectivity",
            annotations=READ_ONLY_ANNOTATIONS,
        )
        self.server.add_tool(
            self.qualys_list_enabled_modules,
            name="qualys_list_enabled_modules",
            annotations=READ_ONLY_ANNOTATIONS,
        )
        self.server.add_tool(
            self.qualys_list_modules,
            name="qualys_list_modules",
            annotations=READ_ONLY_ANNOTATIONS,
        )
        core = 3

        for module in self.modules.values():
            module.register_tools(self.server)  # type: ignore[attr-defined]
            if hasattr(module, "register_resources"):
                module.register_resources(self.server)  # type: ignore[attr-defined]

        return core + sum(len(getattr(m, "tools", [])) for m in self.modules.values())

    # ------------------------------------------------------------------ #
    # Core tools
    # ------------------------------------------------------------------ #
    def qualys_check_connectivity(self) -> dict[str, object]:
        """Verify credentials and connectivity to this Qualys console."""
        return self.client.verify_connectivity()

    def qualys_list_enabled_modules(self) -> dict[str, list[str]]:
        """List the modules enabled on this console instance."""
        return {"modules": sorted(self.modules.keys())}

    def qualys_list_modules(self) -> dict[str, list[str]]:
        """List every module available in the qualys-mcp build."""
        return {"modules": registry.get_module_names()}

    # ------------------------------------------------------------------ #
    def _run_http_transport(self, app: ASGIApp) -> None:
        app = strip_trailing_slash_middleware(app)
        app = normalize_content_type_middleware(app)
        if self.api_key:
            app = auth_middleware(app, self.api_key)
            logger.info("API key authentication enabled")
        uvicorn.run(
            app,
            host=self.host,
            port=self.port,
            log_level="debug" if self.config.debug else "info",
        )

    def run(self, transport: TransportType = "stdio") -> None:
        """Run the server under the chosen transport."""
        if transport in ("streamable-http", "sse"):
            logger.info("Starting %s on %s:%d", transport, self.host, self.port)
            app_method = (
                self.server.streamable_http_app
                if transport == "streamable-http"
                else self.server.sse_app
            )
            self._run_http_transport(app_method())
        else:
            self.server.run(transport)


# ---------------------------------------------------------------------- #
# CLI
# ---------------------------------------------------------------------- #
def parse_modules_list(modules_string: str) -> list[str]:
    """Validate a comma-separated module list against discovered modules."""
    available = registry.get_module_names()
    if not modules_string:
        return available
    requested = [m.strip() for m in modules_string.split(",") if m.strip()]
    invalid = [m for m in requested if m not in available]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"Invalid modules: {', '.join(invalid)}. Available: {', '.join(available)}"
        )
    return requested


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qualys MCP Server")
    parser.add_argument("--version", "-V", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--transport",
        "-t",
        choices=["stdio", "sse", "streamable-http"],
        default=os.environ.get("QUALYS_MCP_TRANSPORT", "stdio"),
    )
    parser.add_argument(
        "--modules",
        "-m",
        type=parse_modules_list,
        default=parse_modules_list(os.environ.get("QUALYS_MCP_MODULES", "")),
        metavar="MODULE1,MODULE2,...",
        help="Comma-separated modules to enable (default: all).",
    )
    parser.add_argument("--platform", default=os.environ.get("QUALYS_PLATFORM"))
    parser.add_argument("--console-label", default=os.environ.get("QUALYS_CONSOLE_LABEL", "qualys"))
    parser.add_argument("--host", default=os.environ.get("QUALYS_MCP_HOST", "127.0.0.1"))
    parser.add_argument("--port", "-p", type=int, default=int(os.environ.get("QUALYS_MCP_PORT", "8781")))
    parser.add_argument("--api-key", default=os.environ.get("QUALYS_MCP_API_KEY"))
    parser.add_argument(
        "--stateless-http",
        action="store_true",
        default=os.environ.get("QUALYS_MCP_STATELESS_HTTP", "").lower() == "true",
    )
    parser.add_argument(
        "--enable-destructive",
        action="store_true",
        default=os.environ.get("QUALYS_ENABLE_DESTRUCTIVE", "").lower() == "true",
        help="Register destructive (delete/purge) tools. Off by default.",
    )
    parser.add_argument("--debug", "-d", action="store_true", default=os.environ.get("QUALYS_DEBUG", "").lower() == "true")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Offline validation: instantiate all modules, print module/tool counts, exit. "
        "No credentials or network required.",
    )
    return parser.parse_args()


def _run_check(args: argparse.Namespace) -> int:
    """Offline build validation used by the audit wave."""
    configure_logging(debug=args.debug)
    config = QualysConfig.from_env(
        platform=args.platform,
        console_label=args.console_label,
        enable_destructive=args.enable_destructive,
        debug=args.debug,
        # Dummy creds so require_credentials() never trips during --check.
        username=os.environ.get("QUALYS_USERNAME", "check"),
        password=os.environ.get("QUALYS_PASSWORD", "check"),
        api_url=os.environ.get("QUALYS_API_URL", "https://qualysapi.example.com"),
    )
    server = QualysMCPServer(
        config=config,
        enabled_modules=set(args.modules),
        port=args.port,
    )
    module_names = sorted(server.modules.keys())
    total_tools = 3 + sum(len(getattr(m, "tools", [])) for m in server.modules.values())
    print(f"qualys-mcp v{__version__}")
    print(f"discovered modules : {len(registry.get_module_names())}")
    print(f"enabled modules    : {len(module_names)}")
    print(f"registered tools   : {total_tools}")
    print(f"destructive tools  : {'ENABLED' if config.enable_destructive else 'gated (hidden)'}")
    print("modules:")
    for name in module_names:
        count = len(getattr(server.modules[name], "tools", []))
        print(f"  - {name}: {count} tools")
    return 0


def main() -> None:
    load_dotenv()
    args = parse_args()

    if args.check:
        sys.exit(_run_check(args))

    try:
        config = QualysConfig.from_env(
            platform=args.platform,
            console_label=args.console_label,
            enable_destructive=args.enable_destructive,
            debug=args.debug,
        )
        server = QualysMCPServer(
            config=config,
            enabled_modules=set(args.modules),
            stateless_http=args.stateless_http,
            api_key=args.api_key,
            host=args.host,
            port=args.port,
        )
        logger.info("Starting server with %s transport", args.transport)
        server.run(args.transport)
    except (RuntimeError, ValueError) as exc:
        logger.error("Startup error: %s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
