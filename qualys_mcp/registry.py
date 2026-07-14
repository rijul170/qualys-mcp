"""Module registry for the Qualys MCP server.

Modules are auto-discovered by scanning ``qualys_mcp/modules`` for classes whose
name ends in ``Module`` (excluding ``BaseModule``). The registry name is the
class name lowercased with the ``Module`` suffix removed — e.g. ``VmScansModule``
=> ``vmscans``. This mirrors the Falcon MCP discovery pattern so a new module is
added simply by dropping a file into ``modules/``.
"""

from __future__ import annotations

import importlib
import os
import pkgutil
from typing import TYPE_CHECKING

from qualys_mcp.common.logging import get_logger

if TYPE_CHECKING:
    from qualys_mcp.modules.base import BaseModule

logger = get_logger(__name__)

AVAILABLE_MODULES: dict[str, type["BaseModule"]] = {}


def discover_modules() -> None:
    """Populate ``AVAILABLE_MODULES`` by importing every module file."""
    current_dir = os.path.dirname(__file__)
    modules_path = os.path.join(current_dir, "modules")

    for _, name, is_pkg in pkgutil.iter_modules([modules_path]):
        if is_pkg or name == "base":
            continue
        module = importlib.import_module(f"qualys_mcp.modules.{name}")
        for attr_name in dir(module):
            if attr_name.endswith("Module") and attr_name != "BaseModule":
                module_class = getattr(module, attr_name)
                registry_name = attr_name.lower().replace("module", "")
                AVAILABLE_MODULES[registry_name] = module_class
                logger.debug("Discovered module: %s (%s)", registry_name, attr_name)


def get_available_modules() -> dict[str, type["BaseModule"]]:
    """Return the discovered module map, discovering lazily on first call."""
    if not AVAILABLE_MODULES:
        discover_modules()
    return AVAILABLE_MODULES


def get_module_names() -> list[str]:
    """Return the sorted list of discovered module names."""
    return sorted(get_available_modules().keys())
