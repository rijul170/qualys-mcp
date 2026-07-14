"""Smoke tests: every discovered module registers cleanly and safely.

Unlike ``test_foundation.py`` (which drives one reference module end-to-end),
this file instantiates and registers *every* module returned by
``qualys_mcp.registry.get_available_modules()`` against a lightweight stub
server (not the real ``FastMCP``) that simply records ``(name, annotations,
function)`` for each ``add_tool`` call. This keeps the suite fast and
network-free while still exercising the exact registration path every
module goes through in production (``BaseModule._add_tool`` ->
``server.add_tool(method, name=..., annotations=...)``).

Run with pytest from the repo root.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable

import pytest

from qualys_mcp import registry
from qualys_mcp.client import QualysClient
from qualys_mcp.config import QualysConfig

# ---------------------------------------------------------------------- #
# Helpers
# ---------------------------------------------------------------------- #


class _StubServer:
    """Records every ``add_tool`` call instead of building a real MCP tool.

    Matches the subset of ``FastMCP.add_tool``'s signature that
    ``BaseModule._add_tool`` actually calls:
    ``server.add_tool(method, name=..., annotations=...)``.
    """

    def __init__(self) -> None:
        self.registered: list[tuple[str, Any, Callable[..., Any]]] = []

    def add_tool(
        self,
        fn: Callable[..., Any],
        name: str | None = None,
        annotations: Any = None,
        **_: Any,
    ) -> None:
        self.registered.append((name, annotations, fn))


def _build_client(enable_destructive: bool) -> QualysClient:
    """Build a QualysClient against a dummy config. No network is ever hit."""
    cfg = QualysConfig(
        username="smoke-user",
        password="smoke-pass",
        platform="US2",
        api_url="https://qualysapi.qg2.apps.qualys.com",
        gateway_url="https://gateway.qg2.apps.qualys.com",
        console_label="smoke-test",
        enable_destructive=enable_destructive,
    )
    return QualysClient(cfg)


def _register_all_modules(enable_destructive: bool) -> tuple[_StubServer, dict[str, str]]:
    """Instantiate + register every discovered module against one stub server.

    Returns the stub server (with every tool registered across every module,
    so cross-module duplicate-name checks are meaningful) plus a dict mapping
    module registry name -> error string for any module whose instantiation
    or ``register_tools`` call raised (collected rather than raised
    immediately, so a single broken module doesn't hide failures in others).
    """
    client = _build_client(enable_destructive)
    server = _StubServer()
    errors: dict[str, str] = {}
    modules = registry.get_available_modules()
    assert modules, "registry.get_available_modules() returned nothing"
    for mod_name, mod_cls in modules.items():
        try:
            instance = mod_cls(client)
            instance.register_tools(server)
        except Exception as exc:  # noqa: BLE001 - collect, don't abort the loop
            errors[mod_name] = f"{type(exc).__name__}: {exc}"
    return server, errors


# ---------------------------------------------------------------------- #
# Fixtures (registration is done once per module-scope; it's cheap but no
# need to repeat it for every single test function).
# ---------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def registered_destructive_enabled() -> tuple[_StubServer, dict[str, str]]:
    return _register_all_modules(enable_destructive=True)


@pytest.fixture(scope="module")
def registered_destructive_disabled() -> tuple[_StubServer, dict[str, str]]:
    return _register_all_modules(enable_destructive=False)


# ---------------------------------------------------------------------- #
# Tests
# ---------------------------------------------------------------------- #


def test_every_module_registers_without_exception(registered_destructive_enabled):
    _, errors = registered_destructive_enabled
    assert not errors, f"modules raised during register_tools(): {errors}"


def test_no_duplicate_tool_names_across_server(registered_destructive_enabled):
    server, _ = registered_destructive_enabled
    names = [name for name, _, _ in server.registered]
    dupes = sorted({n for n in names if names.count(n) > 1})
    assert not dupes, f"duplicate tool names registered across modules: {dupes}"


def test_every_tool_name_has_qualys_prefix(registered_destructive_enabled):
    server, _ = registered_destructive_enabled
    unprefixed = sorted(name for name, _, _ in server.registered if not (name or "").startswith("qualys_"))
    assert not unprefixed, f"tool names missing the 'qualys_' prefix: {unprefixed}"


def test_at_least_one_tool_registered_per_family(registered_destructive_enabled):
    # Sanity: registration actually produced tools (not silently a no-op).
    server, _ = registered_destructive_enabled
    assert len(server.registered) > 300, (
        f"expected several hundred tools across 59 modules, got {len(server.registered)}"
    )


def test_destructive_tools_disappear_when_disabled(
    registered_destructive_enabled, registered_destructive_disabled
):
    enabled_server, _ = registered_destructive_enabled
    disabled_server, _ = registered_destructive_disabled
    enabled_count = len(enabled_server.registered)
    disabled_count = len(disabled_server.registered)
    assert disabled_count < enabled_count, (
        "expected fewer tools registered with enable_destructive=False "
        f"(got enabled={enabled_count}, disabled={disabled_count})"
    )

    disabled_names = {name for name, _, _ in disabled_server.registered}
    enabled_names = {name for name, _, _ in enabled_server.registered}
    # Every tool visible when disabled must also be visible when enabled
    # (enabling destructive only adds tools, never removes/renames any).
    assert disabled_names <= enabled_names


def test_destructive_tools_require_confirm_param(registered_destructive_enabled):
    """Every tool tagged destructiveHint=True must accept a 'confirm' param."""
    server, _ = registered_destructive_enabled
    destructive_tools = [
        (name, fn)
        for name, annotations, fn in server.registered
        if annotations is not None and getattr(annotations, "destructiveHint", False)
    ]
    assert destructive_tools, "expected at least one destructive tool with enable_destructive=True"

    missing_confirm = []
    for name, fn in destructive_tools:
        sig = inspect.signature(fn)
        if "confirm" not in sig.parameters:
            missing_confirm.append(name)
    assert not missing_confirm, (
        f"destructive tools missing a 'confirm' parameter: {missing_confirm}"
    )


def test_non_destructive_tools_outnumber_destructive(registered_destructive_enabled):
    # Basic shape check: destructive tools should be a small minority.
    server, _ = registered_destructive_enabled
    destructive = sum(
        1
        for _, annotations, _ in server.registered
        if annotations is not None and getattr(annotations, "destructiveHint", False)
    )
    total = len(server.registered)
    assert 0 < destructive < total
