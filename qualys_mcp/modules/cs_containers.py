"""Container Security — Containers module (Gateway/JWT API).

Container Security is a Gateway-family product: calls go to the gateway host
(JWT auto-fetched) under ``/csapi/v1.3/...`` with JSON bodies — no ``/qps/rest``
prefix and no XML. Not in the VM/PC PDF; endpoint shapes come from the public
CS API reference (https://docs.qualys.com/en/cs/api/ and CS API release notes).
Uncertain paths/params/bodies are flagged with ``# TODO(verify)``.

Docs: Qualys Container Security API Guide — "Containers".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class CsContainersModule(BaseModule):
    """List, inspect, and manage Container Security container assets."""

    module_label = "cs_containers"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_cs_containers, "list_cs_containers", tier="read")
        self._add_tool(server, self.get_cs_container, "get_cs_container", tier="read")
        self._add_tool(
            server, self.get_cs_container_vulnerabilities, "get_cs_container_vulnerabilities", tier="read"
        )
        self._add_tool(server, self.get_cs_container_software, "get_cs_container_software", tier="read")
        # Destructive
        self._add_tool(server, self.delete_cs_container, "delete_cs_container", tier="destructive")

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def list_cs_containers(
        self,
        filter: str | None = None,
        page_number: int | None = None,
        page_size: int = 50,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List containers in the subscription.

        Args:
            filter: Qualys QQL-style filter string (e.g.
                "state:RUNNING and vulnerabilities.severity:5"). Passed as the
                ``filter`` query param.
            page_number: Zero-based page index (``pageNumber`` query param).
            page_size: Results per page (``pageSize`` query param; default 50).
            sort: Sort expression, e.g. "created:desc" (``sort`` query param).

        Returns:
            Parsed JSON with a ``data`` array of container records and paging
            metadata.
        """
        params = {
            "filter": filter,
            "pageNumber": page_number,
            "pageSize": page_size,
            "sort": sort,
        }
        # Confirmed: GET /csapi/v1.3/containers (bulk variant: /containers/list).
        return self._gateway("/csapi/v1.3/containers", method="GET", params=params)

    def get_cs_container(self, container_sha: str) -> dict[str, Any]:
        """Fetch full metadata for a single container.

        Args:
            container_sha: The container SHA identifier (a.k.a. containerId/QLP id).

        Returns:
            Parsed JSON container record (image, host, state, ports, vuln counts).
        """
        return self._gateway(f"/csapi/v1.3/containers/{container_sha}", method="GET")

    def get_cs_container_vulnerabilities(self, container_sha: str) -> dict[str, Any]:
        """Fetch the vulnerability findings for a container.

        Args:
            container_sha: The container SHA identifier.

        Returns:
            Parsed JSON with the container's detected vulnerabilities.
        """
        # TODO(verify): sub-resource path for container vulnerabilities — assumed
        # "/csapi/v1.3/containers/{containerSha}/vuln" by analogy with images.
        return self._gateway(f"/csapi/v1.3/containers/{container_sha}/vuln", method="GET")

    def get_cs_container_software(self, container_sha: str) -> dict[str, Any]:
        """Fetch the installed software packages for a container.

        Args:
            container_sha: The container SHA identifier.

        Returns:
            Parsed JSON with installed packages, versions, and per-package
            vulnerability counts.
        """
        # TODO(verify): sub-resource path for container software — assumed
        # "/csapi/v1.3/containers/{containerSha}/software" by analogy with the
        # confirmed image software endpoint.
        return self._gateway(f"/csapi/v1.3/containers/{container_sha}/software", method="GET")

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_cs_container(self, container_sha: str, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete a container from the subscription. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<container_sha>.

        Args:
            container_sha: The container SHA identifier to delete.
            confirm: Must equal ``container_sha`` to proceed.

        Returns:
            Parsed JSON status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=container_sha)
        if guard:
            return guard
        # TODO(verify): delete-by-id path/method — assumed
        # DELETE /csapi/v1.3/containers/{containerSha}.
        return self._gateway(f"/csapi/v1.3/containers/{container_sha}", method="DELETE")
