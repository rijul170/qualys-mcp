"""Patch List module (classic FO API).

Covers the "Patch List" endpoint under Assets in the VM/PC API guide, which
returns the superseding patches that fix a single host's vulnerability
detections. Homed as its own module during Wave-1 integration (it fell
between the Assets cluster's file assignments).

Endpoint: ``GET /api/2.0/fo/asset/patch/index.php`` (confirmed via
https://docs.qualys.com/en/vm/api/assets/patch_list/patch_list.htm — the
previously assumed ``/api/2.0/fo/asset/host/patch/`` path does not exist and
404'd in the live audit). This is a per-host lookup: the only documented
parameters are ``host_id`` (required) and ``output_format``; there is no
documented ids/qids/ips/asset-group/tag filter set for this endpoint.
Docs: Qualys VM/PC API User Guide — Assets > "Patch List".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class PatchesModule(BaseModule):
    """List superseding patches that fix a single host's detections."""

    module_label = "patches"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_patches, "list_patches", tier="read")

    def list_patches(
        self,
        host_id: int,
        output_format: str = "xml",
    ) -> dict[str, Any]:
        """List the superseding patches that fix detections on a single host.

        Args:
            host_id: The host ID to list superseding patches for (required).
            output_format: Only "xml" is documented for this endpoint.
                Qualys only accepts lowercase.

        Returns:
            Parsed patch list output (per-host superseding patch records).
        """
        params = {
            "host_id": host_id,
            "output_format": output_format.lower(),
        }
        return self._fo("/api/2.0/fo/asset/patch/index.php", method="GET", params=params)
