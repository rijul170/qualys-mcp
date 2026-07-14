"""Container Security — Registries module (Gateway/JWT API).

Container Security is a Gateway-family product: calls go to the gateway host
(JWT auto-fetched) under ``/csapi/v1.3/...`` with JSON bodies — no ``/qps/rest``
prefix and no XML. Not in the VM/PC PDF; endpoint shapes come from the public
CS API reference (https://docs.qualys.com/en/cs/api/ and CS API release notes).
Uncertain paths/params/bodies are flagged with ``# TODO(verify)``.

Docs: Qualys Container Security API Guide — "Registry".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class CsRegistriesModule(BaseModule):
    """List, inspect, configure, and scan Container Security registries."""

    module_label = "cs_registries"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_cs_registries, "list_cs_registries", tier="read")
        self._add_tool(server, self.get_cs_registry, "get_cs_registry", tier="read")
        # Writes
        self._add_tool(server, self.create_cs_registry, "create_cs_registry", tier="write")
        self._add_tool(server, self.update_cs_registry, "update_cs_registry", tier="write")
        self._add_tool(server, self.run_cs_registry_scan, "run_cs_registry_scan", tier="write")
        # Destructive
        self._add_tool(server, self.delete_cs_registry, "delete_cs_registry", tier="destructive")

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def list_cs_registries(
        self,
        filter: str | None = None,
        page_number: int | None = None,
        page_size: int = 50,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List configured container registries.

        Args:
            filter: Qualys QQL-style filter string (``filter`` query param).
            page_number: Zero-based page index (``pageNumber`` query param).
            page_size: Results per page (``pageSize`` query param; default 50).
            sort: Sort expression (``sort`` query param).

        Returns:
            Parsed JSON with a ``data`` array of registry records.
        """
        params = {
            "filter": filter,
            "pageNumber": page_number,
            "pageSize": page_size,
            "sort": sort,
        }
        # Confirmed: GET /csapi/v1.3/registry
        return self._gateway("/csapi/v1.3/registry", method="GET", params=params)

    def get_cs_registry(self, registry_id: str) -> dict[str, Any]:
        """Fetch details of a single registry.

        Args:
            registry_id: The registry ID (``registryId``).

        Returns:
            Parsed JSON registry record.
        """
        # Confirmed: GET /csapi/v1.3/registry/{registryId}
        return self._gateway(f"/csapi/v1.3/registry/{registry_id}", method="GET")

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def create_cs_registry(
        self,
        registry_name: str,
        registry_uri: str,
        registry_type: str,
        credential_type: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> dict[str, Any]:
        """Create (connect) a new container registry.

        Args:
            registry_name: Display name for the registry (``registryName``).
            registry_uri: Registry URL/URI, e.g. "https://registry.example.com"
                (``registryUri``).
            registry_type: Registry type — e.g. "DockerV2", "AWS", "AZURE",
                "GCR", "DOCKERHUB", "JFROG", "QUAY".
                # TODO(verify): exact accepted ``registryType`` enum values.
            credential_type: Credential mechanism — e.g. "Token", "BASIC",
                "AWS_IAM", "AZURE_AD".
                # TODO(verify): exact ``credentialType`` enum values and which
                # extra fields each type requires (e.g. AWS needs region/role ARN).
            username: Registry username (for basic/token credentials).
            password: Registry password/token (for basic/token credentials).

        Returns:
            Parsed JSON with the created registry's ID, or an error dict.
        """
        # TODO(verify): exact JSON body shape — the CS docs show a flat body with
        # registryName/registryUri/registryType/credentialType plus a nested
        # credential object; the credential sub-structure below is inferred.
        body: dict[str, Any] = {
            "registryName": registry_name,
            "registryUri": registry_uri,
            "registryType": registry_type,
        }
        if credential_type is not None:
            body["credentialType"] = credential_type
        if username is not None or password is not None:
            body["credential"] = {  # TODO(verify): wrapper key name ("credential")
                "userName": username,
                "password": password,
            }
        return self._gateway("/csapi/v1.3/registry", method="POST", json=body)

    def update_cs_registry(
        self,
        registry_id: str,
        registry_name: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing registry connection.

        Args:
            registry_id: The registry ID to update (``registryId``).
            registry_name: New display name, if changing.
            username: New registry username, if changing.
            password: New registry password/token, if changing.

        Returns:
            Parsed JSON with the updated registry record, or an error dict.
        """
        body: dict[str, Any] = {}
        if registry_name is not None:
            body["registryName"] = registry_name
        if username is not None or password is not None:
            body["credential"] = {"userName": username, "password": password}  # TODO(verify)
        # TODO(verify): update method/path — assumed PUT /csapi/v1.3/registry/{registryId}.
        return self._gateway(f"/csapi/v1.3/registry/{registry_id}", method="PUT", json=body)

    def run_cs_registry_scan(
        self,
        registry_id: str,
        repo_tags: str | None = None,
        on_demand: bool = True,
    ) -> dict[str, Any]:
        """Trigger a scan of a registry's images.

        Args:
            registry_id: The registry ID to scan (``registryId``).
            repo_tags: Optional comma-separated repo:tag patterns to limit scope
                (maps to a ``repoTags`` list in the body).
            on_demand: When True, request an immediate one-time scan rather than a
                recurring schedule.

        Returns:
            Parsed JSON with the created scan/schedule reference, or an error dict.
        """
        # TODO(verify): The confirmed registry scan endpoint is
        # POST /csapi/v1.3/registry/{registryId}/schedule (used both for recurring
        # schedules and, with onDemand=true, for immediate scans). The body field
        # names below (onDemand, filters.repoTags) are inferred and NOT confirmed;
        # a dedicated on-demand scan path may exist in newer CS versions.
        body: dict[str, Any] = {"onDemand": on_demand}
        if repo_tags:
            body["filters"] = {"repoTags": [t.strip() for t in repo_tags.split(",") if t.strip()]}
        return self._gateway(
            f"/csapi/v1.3/registry/{registry_id}/schedule",
            method="POST",
            json=body,
        )

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_cs_registry(self, registry_id: str, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete (disconnect) a registry. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<registry_id>.

        Args:
            registry_id: The registry ID to delete.
            confirm: Must equal ``registry_id`` to proceed.

        Returns:
            Parsed JSON status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=registry_id)
        if guard:
            return guard
        # TODO(verify): delete path/method — assumed
        # DELETE /csapi/v1.3/registry/{registryId}.
        return self._gateway(f"/csapi/v1.3/registry/{registry_id}", method="DELETE")
