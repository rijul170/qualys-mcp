"""Configuration for the Qualys MCP server.

A single server process serves exactly one Qualys console (subscription). Two
consoles => two processes on two ports, mirroring the Falcon us2/eu1 layout.
Configuration comes from environment variables (loaded from ``.env`` by the
launcher) or explicit constructor arguments.

Platform (POD) selection sets both the classic/QPS API base URL and the
Gateway base URL. Any platform not in the built-in map can be driven by setting
``QUALYS_API_URL`` and ``QUALYS_GATEWAY_URL`` explicitly.
"""

import os
from dataclasses import dataclass, field
from typing import Any

from qualys_mcp.common.logging import get_logger

logger = get_logger(__name__)

# Built-in platform map: platform code -> (api_base_url, gateway_base_url).
# Source: Qualys "Platform Identification / API server URLs" documentation.
# Anything missing can be overridden via QUALYS_API_URL / QUALYS_GATEWAY_URL.
PLATFORMS: dict[str, tuple[str, str]] = {
    "US1": ("https://qualysapi.qualys.com", "https://gateway.qg1.apps.qualys.com"),
    "US2": ("https://qualysapi.qg2.apps.qualys.com", "https://gateway.qg2.apps.qualys.com"),
    "US3": ("https://qualysapi.qg3.apps.qualys.com", "https://gateway.qg3.apps.qualys.com"),
    "US4": ("https://qualysapi.qg4.apps.qualys.com", "https://gateway.qg4.apps.qualys.com"),
    "EU1": ("https://qualysapi.qualys.eu", "https://gateway.qg1.apps.qualys.eu"),
    "EU2": ("https://qualysapi.qg2.apps.qualys.eu", "https://gateway.qg2.apps.qualys.eu"),
    "EU3": ("https://qualysapi.qg3.apps.qualys.it", "https://gateway.qg3.apps.qualys.it"),
    "IN1": ("https://qualysapi.qg1.apps.qualys.in", "https://gateway.qg1.apps.qualys.in"),
    "CA1": ("https://qualysapi.qg1.apps.qualys.ca", "https://gateway.qg1.apps.qualys.ca"),
    "AE1": ("https://qualysapi.qg1.apps.qualys.ae", "https://gateway.qg1.apps.qualys.ae"),
    "UK1": ("https://qualysapi.qg1.apps.qualys.co.uk", "https://gateway.qg1.apps.qualys.co.uk"),
    "AU1": ("https://qualysapi.qg1.apps.qualys.com.au", "https://gateway.qg1.apps.qualys.com.au"),
    "KSA1": ("https://qualysapi.qg1.apps.qualysksa.com", "https://gateway.qg1.apps.qualysksa.com"),
}


@dataclass
class QualysConfig:
    """Resolved configuration for one Qualys console."""

    username: str | None = None
    password: str | None = None
    platform: str | None = None
    api_url: str = ""
    gateway_url: str = ""
    # Any non-empty value satisfies the mandatory FO API anti-CSRF header.
    requested_with: str = "qualys-mcp"
    console_label: str = "qualys"
    enable_destructive: bool = False
    verify_tls: bool = True
    timeout: float = 300.0
    max_retries: int = 4
    debug: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls, **overrides: Any) -> "QualysConfig":
        """Build config from ``QUALYS_*`` environment variables + overrides.

        Recognized env vars:
            QUALYS_USERNAME, QUALYS_PASSWORD
            QUALYS_PLATFORM           (e.g. US2, EU1; sets api/gateway URLs)
            QUALYS_API_URL            (explicit override of the POD map)
            QUALYS_GATEWAY_URL        (explicit override of the POD map)
            QUALYS_REQUESTED_WITH     (X-Requested-With header value)
            QUALYS_CONSOLE_LABEL      (namespacing label, e.g. consulting/cloud)
            QUALYS_ENABLE_DESTRUCTIVE (true/false — gate for delete/purge tools)
            QUALYS_VERIFY_TLS         (true/false)
            QUALYS_TIMEOUT            (seconds)
            QUALYS_DEBUG              (true/false)
        """

        def _bool(name: str, default: bool) -> bool:
            raw = os.environ.get(name)
            if raw is None:
                return default
            return raw.strip().lower() in ("1", "true", "yes", "on")

        platform = overrides.get("platform") or os.environ.get("QUALYS_PLATFORM")
        api_url = overrides.get("api_url") or os.environ.get("QUALYS_API_URL", "")
        gateway_url = overrides.get("gateway_url") or os.environ.get("QUALYS_GATEWAY_URL", "")

        if platform:
            mapped = PLATFORMS.get(platform.upper())
            if mapped:
                api_url = api_url or mapped[0]
                gateway_url = gateway_url or mapped[1]
            else:
                logger.warning(
                    "Unknown platform '%s'; set QUALYS_API_URL / QUALYS_GATEWAY_URL explicitly.",
                    platform,
                )

        cfg = cls(
            username=overrides.get("username") or os.environ.get("QUALYS_USERNAME"),
            password=overrides.get("password") or os.environ.get("QUALYS_PASSWORD"),
            platform=platform,
            api_url=api_url.rstrip("/"),
            gateway_url=gateway_url.rstrip("/"),
            requested_with=overrides.get("requested_with")
            or os.environ.get("QUALYS_REQUESTED_WITH", "qualys-mcp"),
            console_label=overrides.get("console_label")
            or os.environ.get("QUALYS_CONSOLE_LABEL", "qualys"),
            enable_destructive=overrides.get("enable_destructive")
            if overrides.get("enable_destructive") is not None
            else _bool("QUALYS_ENABLE_DESTRUCTIVE", False),
            verify_tls=overrides.get("verify_tls")
            if overrides.get("verify_tls") is not None
            else _bool("QUALYS_VERIFY_TLS", True),
            timeout=float(overrides.get("timeout") or os.environ.get("QUALYS_TIMEOUT", "300")),
            max_retries=int(overrides.get("max_retries") or os.environ.get("QUALYS_MAX_RETRIES", "4")),
            debug=overrides.get("debug")
            if overrides.get("debug") is not None
            else _bool("QUALYS_DEBUG", False),
        )
        return cfg

    def require_credentials(self) -> None:
        """Raise if credentials or base URL are missing (called before login)."""
        missing = []
        if not self.username:
            missing.append("QUALYS_USERNAME")
        if not self.password:
            missing.append("QUALYS_PASSWORD")
        if not self.api_url:
            missing.append("QUALYS_API_URL or QUALYS_PLATFORM")
        if missing:
            raise ValueError(
                "Missing Qualys configuration: "
                + ", ".join(missing)
                + ". Set them via environment (see .env.example) or pass explicitly."
            )
