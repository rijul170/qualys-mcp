"""Cloud Agent module (QPS REST API) — agent inventory and lifecycle.

Lists and manages Qualys Cloud Agents: agent search/detail, activation keys
(bind newly installed agents to this subscription and a module set),
configuration profiles, and activate/uninstall lifecycle actions.

Endpoints (Cloud Agent API family):
* ``/qps/rest/2.0/{search,get}/am/hostasset`` — agent search/get. The Cloud
  Agent API Guide's "List Agents"/"Get Asset Information for a Single Agent"
  use cases are served by the shared Asset Management (AM) hostasset
  resource (not a dedicated ``ca/agent`` resource, which does not exist —
  confirmed via https://docs.qualys.com/en/ca/api/agents/list_agents.htm and
  https://docs.qualys.com/en/ca/api/use_cases/asset_info_single_agent.htm).
* ``/qps/rest/1.0/activate/ca/agent/{id}`` — activate modules on an agent (write).
* ``/qps/rest/1.0/uninstall/ca/agent/{id}`` — uninstall an agent (destructive).
* ``/qps/rest/1.0/search/ca/agentactkey/`` — activation key search (legacy
  Cloud Agent API; confirmed via
  https://docs.qualys.com/en/ca/api/act_key/act_key_apis.htm — a newer
  ``POST /caui/v1/activation-keys/manage`` gateway endpoint also exists but
  is not used here since this module calls the classic/QPS host).
* ``/qps/rest/1.0/search/ca/agentconfig`` — configuration profile search
  (legacy Cloud Agent API; confirmed via
  https://docs.qualys.com/en/ca/api/config/config_apis.htm).

Docs: The Cloud Agent API is not covered by the classic VM/PC PDF; this
module is built from Qualys's documented QPS REST/Cloud Agent conventions
(see the API index at https://docs.qualys.com/en/vm/api/index.htm -> "Cloud
Agent API"). Every uncertain path/param is flagged ``# TODO(verify)`` —
confirm against the current Cloud Agent API Guide for the target
subscription before relying on this in production.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


def _xml_escape(value: Any) -> str:
    """Escape a value for safe inclusion as XML text/attribute content."""
    text = str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _build_search_request(
    criteria: list[tuple[str, str, str]],
    limit: int | None = None,
    offset: int | None = None,
) -> str:
    """Build a ``<ServiceRequest>`` XML body for a QPS search call.

    Args:
        criteria: List of ``(field, operator, value)`` tuples, ANDed by QPS.
        limit: Max results per page (``preferences/limitResults``).
        offset: Pagination offset.
            # TODO(verify): confirm preferences element name for offset paging
            # (assumed ``startFromOffset``).

    Returns:
        A ``ServiceRequest`` XML string.
    """
    parts = ["<ServiceRequest>"]
    prefs = []
    if limit is not None:
        prefs.append(f"<limitResults>{int(limit)}</limitResults>")
    if offset is not None:
        prefs.append(f"<startFromOffset>{int(offset)}</startFromOffset>")
    if prefs:
        parts.append("<preferences>" + "".join(prefs) + "</preferences>")
    if criteria:
        parts.append("<filters>")
        for field, operator, value in criteria:
            parts.append(
                f'<Criteria field="{_xml_escape(field)}" operator="{_xml_escape(operator)}">'
                f"{_xml_escape(value)}</Criteria>"
            )
        parts.append("</filters>")
    parts.append("</ServiceRequest>")
    return "".join(parts)


class CloudAgentModule(BaseModule):
    """List and manage Qualys Cloud Agents, activation keys, and config profiles."""

    module_label = "cloud_agent"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_agents, "list_agents", tier="read")
        self._add_tool(server, self.get_agent, "get_agent", tier="read")
        self._add_tool(server, self.list_activation_keys, "list_activation_keys", tier="read")
        self._add_tool(server, self.list_config_profiles, "list_config_profiles", tier="read")
        # Write (reversible)
        self._add_tool(server, self.activate_agent, "activate_agent", tier="write")
        # Destructive
        self._add_tool(server, self.uninstall_agent, "uninstall_agent", tier="destructive")

    # ------------------------------ reads ------------------------------ #
    def list_agents(
        self,
        name: str | None = None,
        tag_name: str | None = None,
        tag_id: int | None = None,
        activated_module: str | None = None,
        last_checked_in_after: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """Search/list Cloud Agent-managed hosts.

        Confirmed via the Cloud Agent API Guide's "List Agents" page
        (https://docs.qualys.com/en/ca/api/agents/list_agents.htm): there is
        no dedicated ``ca/agent`` search resource — Cloud Agent hosts are
        listed through the shared AM hostasset search
        (``/qps/rest/2.0/search/am/hostasset``), typically scoped with a
        ``tagName EQUALS "Cloud Agent"`` criterion.
        # TODO(verify): the additional filter field names below
        # (tagName/tagId/activatedModule/lastCheckedIn) beyond the confirmed
        # ``tagName`` example are still best-effort guesses at AM hostasset
        # criteria field names.

        Args:
            name: Asset/host name substring match.
            tag_name: Restrict to agents on assets carrying this exact tag name.
            tag_id: Restrict to agents on assets carrying this exact tag ID.
            activated_module: Restrict to agents with this module activated,
                e.g. "VM", "PC", "FIM". # TODO(verify) field name/enum.
            last_checked_in_after: ISO datetime lower bound
                (``YYYY-MM-DDTHH:MM:SSZ``) on the agent's last check-in.
                # TODO(verify) field name.
            limit: Max results per page.
            offset: Pagination offset into the result set.

        Returns:
            Parsed ServiceResponse with matching Cloud Agent host records.
        """
        criteria: list[tuple[str, str, str]] = []
        if name is not None:
            criteria.append(("name", "CONTAINS", name))
        if tag_name is not None:
            criteria.append(("tagName", "EQUALS", tag_name))  # TODO(verify) field name
        if tag_id is not None:
            criteria.append(("tagId", "EQUALS", str(tag_id)))  # TODO(verify) field name
        if activated_module is not None:
            criteria.append(("activatedModule", "EQUALS", activated_module))  # TODO(verify) field name
        if last_checked_in_after is not None:
            criteria.append(("lastCheckedIn", "GREATER", last_checked_in_after))  # TODO(verify) field/operator
        body = _build_search_request(criteria, limit=limit, offset=offset)
        return self._qps("/qps/rest/2.0/search/am/hostasset", method="POST", body_xml=body)

    def get_agent(self, asset_id: int) -> dict[str, Any]:
        """Fetch full detail for a single Cloud Agent host by asset ID.

        Confirmed via
        https://docs.qualys.com/en/ca/api/use_cases/asset_info_single_agent.htm:
        this is the AM hostasset get-by-id resource, the same one
        :class:`~qualys_mcp.modules.host_asset_am.HostAssetAmModule` uses.

        Args:
            asset_id: The asset ID of the Cloud Agent host to fetch.

        Returns:
            Parsed ServiceResponse with the agent host record.
        """
        return self._qps(f"/qps/rest/2.0/get/am/hostasset/{asset_id}", method="GET")

    def list_activation_keys(
        self,
        title: str | None = None,
        is_enabled: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """List Cloud Agent activation keys available in the subscription.

        Activation keys bind newly installed agents to this subscription and
        a default set of modules (VM/PC/etc.).
        Path confirmed via
        https://docs.qualys.com/en/ca/api/act_key/act_key_apis.htm (legacy
        Cloud Agent "Search Activation Key" API: ``POST
        /qps/rest/1.0/search/ca/agentactkey/``).
        # TODO(verify): the ``isEnabled`` criteria field name is still a
        # best-effort guess.

        Args:
            title: Activation key title/name substring match.
            is_enabled: Restrict to enabled (True) or disabled (False) keys.
            limit: Max results per page.
            offset: Pagination offset into the result set.

        Returns:
            Parsed ServiceResponse with matching activation key records (key
            value, title, enabled modules, provisioned/limit counts).
        """
        criteria: list[tuple[str, str, str]] = []
        if title is not None:
            criteria.append(("title", "CONTAINS", title))
        if is_enabled is not None:
            criteria.append(("isEnabled", "EQUALS", "1" if is_enabled else "0"))  # TODO(verify) field name
        body = _build_search_request(criteria, limit=limit, offset=offset)
        return self._qps("/qps/rest/1.0/search/ca/agentactkey/", method="POST", body_xml=body)

    def list_config_profiles(
        self,
        name: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """List Cloud Agent configuration profiles in the subscription.

        Configuration profiles control per-agent behavior (scan interval,
        CPU/network throttling, manifest download rules, etc.).
        Path confirmed via
        https://docs.qualys.com/en/ca/api/config/config_apis.htm (legacy
        Cloud Agent config-profile search: ``POST
        /qps/rest/1.0/search/ca/agentconfig``).

        Args:
            name: Configuration profile name substring match.
            limit: Max results per page.
            offset: Pagination offset into the result set.

        Returns:
            Parsed ServiceResponse with matching configuration profile records.
        """
        criteria: list[tuple[str, str, str]] = []
        if name is not None:
            criteria.append(("name", "CONTAINS", name))
        body = _build_search_request(criteria, limit=limit, offset=offset)
        return self._qps("/qps/rest/1.0/search/ca/agentconfig", method="POST", body_xml=body)

    # ------------------------------ write ------------------------------ #
    def activate_agent(
        self,
        asset_id: int,
        activation_key: str | None = None,
        profile_id: int | None = None,
    ) -> dict[str, Any]:
        """Activate (or reactivate) Cloud Agent modules on an asset.

        Reversible: activated modules can later be deactivated/reactivated,
        unlike :meth:`uninstall_agent` which removes the agent entirely.
        # TODO(verify): confirm exact path and request body shape —
        # activation may require an ``ActivationKey`` element, a
        # ``moduleList`` element, or both depending on Cloud Agent API version.

        Args:
            asset_id: The asset ID of the Cloud Agent host to activate.
            activation_key: Activation key value to bind the agent to a module set.
            profile_id: Configuration profile ID to apply on activation.

        Returns:
            Parsed ServiceResponse confirming the activation request.
        """
        fields = []
        if activation_key is not None:
            fields.append(f"<ActivationKey>{_xml_escape(activation_key)}</ActivationKey>")  # TODO(verify)
        if profile_id is not None:
            fields.append(f"<profileId>{int(profile_id)}</profileId>")  # TODO(verify)
        body = "<ServiceRequest><data>" + "".join(fields) + "</data></ServiceRequest>"
        return self._qps(f"/qps/rest/1.0/activate/ca/agent/{asset_id}", method="POST", body_xml=body)

    # --------------------------- destructive --------------------------- #
    def uninstall_agent(self, asset_id: int, confirm: str | None = None) -> dict[str, Any]:
        """Uninstall the Cloud Agent from a host. IRREVERSIBLE.

        Removes the agent binary/service from the endpoint; the host will
        stop reporting to Qualys until the agent is manually reinstalled.
        # TODO(verify): confirm exact path — some Cloud Agent API versions
        # expose this as ``uninstall`` (schedules agent removal on next
        # check-in) versus a separate "purge"/"delete" call that only removes
        # the Qualys asset record without touching the endpoint software.
        # Confirm which behavior the target subscription's API performs
        # before calling in production.

        Args:
            asset_id: The asset ID of the Cloud Agent host to uninstall.
            confirm: Must equal ``str(asset_id)`` to proceed.

        Returns:
            Parsed ServiceResponse confirming the uninstall request, or a
            confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(asset_id))
        if guard:
            return guard
        return self._qps(f"/qps/rest/1.0/uninstall/ca/agent/{asset_id}", method="POST")
