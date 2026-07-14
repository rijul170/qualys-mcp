"""Container Security — Images module (Gateway/JWT API).

Container Security is a Gateway-family product: calls go to the gateway host
(JWT auto-fetched) under ``/csapi/v1.3/...`` with JSON bodies — there is NO
``/qps/rest`` prefix and no XML. It is not in the VM/PC PDF; endpoint shapes
below come from the public CS API reference
(https://docs.qualys.com/en/cs/api/ and the CS API release notes). Uncertain
paths/params/bodies are flagged with ``# TODO(verify)``.

Docs: Qualys Container Security API Guide — "Images".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class CsImagesModule(BaseModule):
    """List, inspect, and manage Container Security image assets."""

    module_label = "cs_images"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_cs_images, "list_cs_images", tier="read")
        self._add_tool(server, self.get_cs_image, "get_cs_image", tier="read")
        self._add_tool(server, self.get_cs_image_vulnerabilities, "get_cs_image_vulnerabilities", tier="read")
        self._add_tool(server, self.get_cs_image_software, "get_cs_image_software", tier="read")
        # Destructive
        self._add_tool(server, self.delete_cs_image, "delete_cs_image", tier="destructive")

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def list_cs_images(
        self,
        filter: str | None = None,
        page_number: int | None = None,
        page_size: int = 50,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List container images in the subscription.

        Args:
            filter: Qualys QQL-style filter string (e.g.
                "repo:nginx and vulnerabilities.severity:5"). Passed as the
                ``filter`` query param.
            page_number: Zero-based page index (``pageNumber`` query param).
            page_size: Results per page (``pageSize`` query param; default 50).
            sort: Sort expression, e.g. "created:desc" (``sort`` query param).

        Returns:
            Parsed JSON with a ``data`` array of image records and paging metadata.
        """
        params = {
            "filter": filter,
            "pageNumber": page_number,
            "pageSize": page_size,
            "sort": sort,
        }
        # TODO(verify): "/csapi/v1.3/images" is the standard list endpoint; the
        # bulk variant "/csapi/v1.3/images/list" exists for large result sets.
        return self._gateway("/csapi/v1.3/images", method="GET", params=params)

    def get_cs_image(self, image_sha: str) -> dict[str, Any]:
        """Fetch full metadata for a single image.

        Args:
            image_sha: The image SHA/digest identifier.

        Returns:
            Parsed JSON image record (repo tags, layers, vuln counts, lifecycle).
        """
        return self._gateway(f"/csapi/v1.3/images/{image_sha}", method="GET")

    def get_cs_image_vulnerabilities(self, image_sha: str) -> dict[str, Any]:
        """Fetch the vulnerability findings for an image.

        Args:
            image_sha: The image SHA/digest identifier.

        Returns:
            Parsed JSON with the image's detected vulnerabilities (QIDs, CVEs,
            severities).
        """
        # TODO(verify): sub-resource path for image vulnerabilities — assumed
        # "/csapi/v1.3/images/{imageSha}/vuln"; some CS versions expose this as
        # "/vulns" or fold vulns into the image detail response instead.
        return self._gateway(f"/csapi/v1.3/images/{image_sha}/vuln", method="GET")

    def get_cs_image_software(self, image_sha: str) -> dict[str, Any]:
        """Fetch the installed software packages for an image.

        Args:
            image_sha: The image SHA/digest identifier.

        Returns:
            Parsed JSON with installed packages, versions, lifecycle and per-package
            vulnerability counts.
        """
        # Confirmed shape: GET /csapi/v1.3/images/{imageSha}/software
        return self._gateway(f"/csapi/v1.3/images/{image_sha}/software", method="GET")

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_cs_image(self, image_sha: str, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete an image from the subscription. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<image_sha>. Note: Qualys rejects deletion
        of images that still have active containers (CREATED/RUNNING/STOPPED/
        PAUSED) associated with them.

        Args:
            image_sha: The image SHA/digest to delete.
            confirm: Must equal ``image_sha`` to proceed.

        Returns:
            Parsed JSON status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=image_sha)
        if guard:
            return guard
        # TODO(verify): delete-by-id path/method — assumed
        # DELETE /csapi/v1.3/images/{imageSha}. CS also supports bulk delete by
        # ?filter=... or an imageIds list; not exposed here.
        return self._gateway(f"/csapi/v1.3/images/{image_sha}", method="DELETE")
