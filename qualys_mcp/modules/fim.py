"""FIM module (Gateway/JWT API) — File Integrity Monitoring.

Search FIM change events and incidents, inspect monitoring profiles/rules and
ignored events, and create/approve incidents.

Gateway host + Bearer-JWT auth (fetched automatically by the client). FIM
paths mix ``/fim/v2/`` (events, ignored events, incident counts) and
``/fim/v3/`` (incident search/approve). The confirmed paths below come from
the FIM API guide; less-documented ones (get single event, create manual
incident, list profiles/rules) are flagged ``# TODO(verify)``.

Docs: https://docs.qualys.com/en/fim/api/get_started/get_started.htm
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class FimModule(BaseModule):
    """List FIM events/incidents/profiles and create/approve incidents."""

    module_label = "fim"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_fim_events, "list_fim_events", tier="read")
        self._add_tool(server, self.get_fim_event, "get_fim_event", tier="read")
        self._add_tool(server, self.list_fim_incidents, "list_fim_incidents", tier="read")
        self._add_tool(server, self.list_fim_profiles, "list_fim_profiles", tier="read")
        self._add_tool(server, self.list_fim_rules, "list_fim_rules", tier="read")
        self._add_tool(server, self.list_fim_ignored_events, "list_fim_ignored_events", tier="read")
        # Writes
        self._add_tool(server, self.create_fim_incident, "create_fim_incident", tier="write")
        self._add_tool(server, self.approve_fim_incident, "approve_fim_incident", tier="write")

    # ------------------------------ reads ------------------------------ #
    def list_fim_events(
        self,
        filter_query: str | None = None,
        page_number: int = 0,
        page_size: int = 50,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """Search FIM change events.

        Note: FIM retains events/incidents for 15 months; older data is purged.

        Args:
            filter_query: FIM QQL filter string, e.g.
                ``"action:'Content changes'"`` or
                ``"dateTime: [2024-01-01 ... 2024-01-31]"``.
                # TODO(verify): confirm the request-body field name (assumed
                # ``filter``) and QQL token syntax.
            page_number: Zero-based page index (body ``pageNumber``).
            page_size: Records per page (body ``pageSize``).
            sort: Sort expression, e.g. ``"[{\"dateTime\":\"desc\"}]"``.
                # TODO(verify) sort body shape.

        Returns:
            Parsed gateway JSON with matching FIM event records.
        """
        body: dict[str, Any] = {"pageNumber": page_number, "pageSize": page_size}
        if filter_query is not None:
            body["filter"] = filter_query  # TODO(verify) field name
        if sort is not None:
            body["sort"] = sort  # TODO(verify) field name/shape
        return self._gateway("/fim/v2/events/search", method="POST", json=body)

    def get_fim_event(self, event_id: str) -> dict[str, Any]:
        """Fetch full detail for a single FIM event by ID.

        Args:
            event_id: The FIM event ID to fetch.

        Returns:
            Parsed gateway JSON with the event record.
        """
        # TODO(verify): the FIM guide does not clearly document a get-by-id
        # endpoint; assumed ``GET /fim/v2/events/{id}``. Otherwise use
        # list_fim_events with an id filter.
        return self._gateway(f"/fim/v2/events/{event_id}", method="GET")

    def list_fim_incidents(
        self,
        filter_query: str | None = None,
        page_number: int = 0,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Search FIM incidents.

        Args:
            filter_query: FIM QQL filter string for incidents (e.g. by name,
                status, or reviewer). # TODO(verify) field name/syntax.
            page_number: Zero-based page index.
            page_size: Records per page.

        Returns:
            Parsed gateway JSON with matching FIM incident records.
        """
        body: dict[str, Any] = {"pageNumber": page_number, "pageSize": page_size}
        if filter_query is not None:
            body["filter"] = filter_query  # TODO(verify) field name
        # Confirmed: incident search moved to v3.
        return self._gateway("/fim/v3/incidents/search", method="POST", json=body)

    def list_fim_profiles(
        self,
        filter_query: str | None = None,
        page_number: int = 0,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """List FIM monitoring profiles.

        Args:
            filter_query: Optional QQL filter for profiles (e.g. by name).
            page_number: Zero-based page index.
            page_size: Records per page.

        Returns:
            Parsed gateway JSON with monitoring profile records.
        """
        body: dict[str, Any] = {"pageNumber": page_number, "pageSize": page_size}
        if filter_query is not None:
            body["filter"] = filter_query  # TODO(verify) field name
        # TODO(verify): confirm profiles search path/version (assumed
        # ``/fim/v3/profiles/search``; may be ``/fim/v2/``).
        return self._gateway("/fim/v3/profiles/search", method="POST", json=body)

    def list_fim_rules(
        self,
        profile_id: str,
        page_number: int = 0,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """List monitoring rules within a FIM profile.

        Args:
            profile_id: The monitoring profile ID whose rules to list.
            page_number: Zero-based page index.
            page_size: Records per page.

        Returns:
            Parsed gateway JSON with the profile's monitoring rule records.
        """
        # TODO(verify): FIM rules are embedded in a profile's definition; there
        # may be no standalone rules-search endpoint. This assumes a profile
        # sub-resource ``GET /fim/v3/profiles/{id}/rules``. Otherwise fetch the
        # profile via list_fim_profiles and read its ``rules`` array.
        params = {"pageNumber": page_number, "pageSize": page_size}
        return self._gateway(
            f"/fim/v3/profiles/{profile_id}/rules", method="GET", params=params
        )

    def list_fim_ignored_events(
        self,
        filter_query: str | None = None,
        page_number: int = 0,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Search ignored FIM events (events suppressed by ignore rules).

        Args:
            filter_query: Optional QQL filter string. # TODO(verify) field name.
            page_number: Zero-based page index.
            page_size: Records per page.

        Returns:
            Parsed gateway JSON with ignored event records.
        """
        body: dict[str, Any] = {"pageNumber": page_number, "pageSize": page_size}
        if filter_query is not None:
            body["filter"] = filter_query  # TODO(verify) field name
        # Confirmed prefix: ignored events live under /fim/v2/events/ignore/.
        return self._gateway("/fim/v2/events/ignore/search", method="POST", json=body)

    # ------------------------------ writes ----------------------------- #
    def create_fim_incident(
        self,
        name: str,
        filter_query: str | None = None,
        comment: str | None = None,
        approval_status: str | None = None,
    ) -> dict[str, Any]:
        """Create a manual FIM incident from a set of events.

        Args:
            name: Incident name/title.
            filter_query: QQL selecting the events to attach to the incident
                (e.g. a time window + asset/profile filter).
                # TODO(verify) body field name and whether an explicit event-id
                # list is required instead of a filter.
            comment: Optional reviewer comment.
            approval_status: Optional initial approval status, e.g.
                "PENDING", "APPROVED". # TODO(verify) enum.

        Returns:
            Parsed gateway JSON with the created incident (including its ID).
        """
        # TODO(verify): confirm create-incident path/body. Assumed
        # ``POST /fim/v2/incidents`` with a JSON incident object.
        body: dict[str, Any] = {"name": name}
        if filter_query is not None:
            body["filter"] = filter_query
        if comment is not None:
            body["comment"] = comment
        if approval_status is not None:
            body["approvalStatus"] = approval_status
        return self._gateway("/fim/v2/incidents", method="POST", json=body)

    def approve_fim_incident(
        self,
        incident_id: str,
        comment: str | None = None,
        approval_status: str = "APPROVED",
    ) -> dict[str, Any]:
        """Approve (or set the approval status of) a FIM incident.

        Args:
            incident_id: The incident ID to approve.
            comment: Optional reviewer comment recorded with the approval.
            approval_status: Approval status to set — "APPROVED" (default),
                "REJECTED", etc. # TODO(verify) accepted enum values.

        Returns:
            Parsed gateway JSON confirming the approval.
        """
        # Confirmed: approve is a v3 incident sub-resource.
        body: dict[str, Any] = {"approvalStatus": approval_status}  # TODO(verify) body shape
        if comment is not None:
            body["comment"] = comment
        return self._gateway(
            f"/fim/v3/incidents/{incident_id}/approve", method="POST", json=body
        )
