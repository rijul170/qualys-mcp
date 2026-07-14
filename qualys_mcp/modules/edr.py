"""EDR module (Gateway/JWT API) — Endpoint Detection & Response.

Search EDR events, inspect event/asset detail, and drive response actions
(quarantine host/file, kill process). EDR shares the Qualys IOC service, so
its API paths use the ``/ioc/`` prefix.

Gateway host + Bearer-JWT auth (fetched automatically by the client). The
remediation-action paths (``/ioc/remediation-actions/...``) and asset paths
(``/ioc/asset/...``) are documented; event-search paths and action request
bodies are less firmly pinned down and are flagged ``# TODO(verify)``.

Response actions (quarantine, kill process) are treated as **destructive**:
they change endpoint state in ways that disrupt the host/process, so they
require the destructive enable flag + an explicit ``confirm`` token.

Docs: https://docs.qualys.com/en/edr/latest/ and the EDR/IOC API reference.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class EdrModule(BaseModule):
    """Search EDR events/assets and perform response actions on endpoints."""

    module_label = "edr"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.search_edr_events, "search_edr_events", tier="read")
        self._add_tool(server, self.get_edr_event, "get_edr_event", tier="read")
        self._add_tool(server, self.list_edr_assets, "list_edr_assets", tier="read")
        # Destructive response actions (gated + confirm)
        self._add_tool(server, self.quarantine_edr_asset, "quarantine_edr_asset", tier="destructive")
        self._add_tool(server, self.kill_edr_process, "kill_edr_process", tier="destructive")

    # ------------------------------ reads ------------------------------ #
    def search_edr_events(
        self,
        filter_query: str | None = None,
        page_number: int = 0,
        page_size: int = 50,
        search_after_values: str | None = None,
    ) -> dict[str, Any]:
        """Search EDR detection events.

        Path/params confirmed via the EDR API guide's "Fetch Events Using
        SearchAfter"
        (https://docs.qualys.com/en/edr/latest/mergedProjects/edr_api/events-api/fetch_events_using_searchafter_api.htm):
        ``GET /ioc/events/searchAfter`` (a GET with query params, not the
        POST-with-JSON-body ``/ioc/events/search`` previously assumed here —
        that resource does not exist and 404s). There is no plain
        non-cursor events list; ``search_after_values`` from a prior
        response's ``searchAfterValues`` is required to page past the first
        page.

        Args:
            filter_query: EDR QQL filter string, e.g. "type:file" or a
                time-range/asset expression, sent as the ``filter`` query
                param.
            page_number: Zero-based page index (default 0).
            page_size: Records per page (default 50; API default is 10).
            search_after_values: Pagination cursor value(s) returned by the
                previous response's ``searchAfterValues`` field. Omit for the
                first page.

        Returns:
            Parsed gateway JSON with matching EDR event records.
        """
        params: dict[str, Any] = {"pageNumber": page_number, "pageSize": page_size}
        if filter_query is not None:
            params["filter"] = filter_query
        if search_after_values is not None:
            params["searchAfterValues"] = search_after_values
        return self._gateway("/ioc/events/searchAfter", method="GET", params=params)

    def get_edr_event(self, agent_id: str, event_id: str) -> dict[str, Any]:
        """Fetch full detail for a single EDR event by ID.

        Path confirmed via
        https://docs.qualys.com/en/edr/latest/mergedProjects/edr_api/events-api/fetch_event_details.htm:
        event detail is keyed by ``{agentId}/{eventId}`` (not a bare event ID
        as previously assumed here).

        Args:
            agent_id: The Cloud Agent ID that reported the event.
            event_id: The EDR event ID to fetch.

        Returns:
            Parsed gateway JSON with the event detail (process tree,
            indicators, MITRE mapping, verdict).
        """
        return self._gateway(f"/ioc/events/{agent_id}/{event_id}", method="GET")

    def list_edr_assets(
        self,
        filter_query: str | None = None,
        page_number: int = 0,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """List assets monitored by EDR.

        Args:
            filter_query: Optional QQL filter (e.g. by hostname, agent status).
                # TODO(verify) whether asset listing takes a filter body or
                # only query params.
            page_number: Zero-based page index.
            page_size: Records per page.

        Returns:
            Parsed gateway JSON with EDR asset records.
        """
        # Documented IOC asset endpoints: /ioc/asset/all, /ioc/asset/count,
        # /ioc/asset/{assetId}, /ioc/asset/searchAfter. This uses the
        # list-all resource with GET + pageNumber/pageSize query params,
        # which matches the documented usage (confirmed via multiple EDR API
        # guide pages referencing GET .../ioc/asset/all?pageNumber=&pageSize=).
        # TODO(verify): the live audit observed HTTP 500 here even though the
        # path/method/params match documentation — this looks like a
        # subscription/console-side issue (e.g. empty EDR asset inventory)
        # rather than a client request bug. Re-test against a console with
        # EDR-monitored assets before assuming this code is still wrong.
        params: dict[str, Any] = {"pageNumber": page_number, "pageSize": page_size}
        if filter_query is not None:
            params["filter"] = filter_query  # TODO(verify) param name
        return self._gateway("/ioc/asset/all", method="GET", params=params)

    # --------------------------- destructive --------------------------- #
    def quarantine_edr_asset(
        self,
        asset_id: str,
        confirm: str | None = None,
    ) -> dict[str, Any]:
        """Quarantine (network-isolate) an EDR asset. DISRUPTIVE / gated.

        Restricts the infected host from network communication (Windows agent
        4.9.0+ / Linux agent 6.0.0+). Requires the destructive enable flag and
        an explicit ``confirm`` token.

        Args:
            asset_id: The EDR asset ID to quarantine.
            confirm: Must equal ``asset_id`` to proceed.

        Returns:
            Parsed gateway JSON with the remediation action result, or a
            confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=asset_id)
        if guard:
            return guard
        # Documented: /ioc/remediation-actions/performQuarantineHostAction.
        # TODO(verify): confirm exact request body field names for the target
        # asset (assumed ``assetId``) and any required action metadata.
        body = {"assetId": asset_id}
        return self._gateway(
            "/ioc/remediation-actions/performQuarantineHostAction",
            method="POST",
            json=body,
        )

    def kill_edr_process(
        self,
        asset_id: str,
        process_id: str,
        confirm: str | None = None,
    ) -> dict[str, Any]:
        """Kill a running process on an EDR-monitored asset. DISRUPTIVE / gated.

        Uses the generic remediation-action endpoint with a KILL_PROCESS
        action. Requires the destructive enable flag and an explicit
        ``confirm`` token.

        Args:
            asset_id: The EDR asset ID hosting the process.
            process_id: Identifier of the process to kill (OS PID or the EDR
                process identifier from the event detail).
                # TODO(verify): confirm whether the API expects the OS PID or an
                # EDR-internal process/event reference.
            confirm: Must equal ``process_id`` to proceed.

        Returns:
            Parsed gateway JSON with the remediation action result, or a
            confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=process_id)
        if guard:
            return guard
        # Documented: /ioc/remediation-actions/performAction (kill/quarantine/
        # delete file or process).
        # TODO(verify): confirm the request body — assumed an actionType
        # discriminator plus asset/process identifiers.
        body = {
            "actionType": "KILL_PROCESS",  # TODO(verify) enum value
            "assetId": asset_id,
            "processId": process_id,
        }
        return self._gateway(
            "/ioc/remediation-actions/performAction", method="POST", json=body
        )
