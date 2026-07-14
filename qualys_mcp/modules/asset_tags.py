"""Asset Tags module (QPS REST API) — Asset Management / Tagging.

Search, fetch, create, update, and delete asset tags, including dynamic tags
(rule-based tags Qualys evaluates against the asset inventory to
auto-assign/remove themselves).

Endpoints: ``/qps/rest/2.0/{search,get,create,update,delete}/am/tag``.

Docs: This QPS/AM API family is not covered by the classic VM/PC PDF; the
endpoint shapes below follow Qualys's documented QPS REST conventions (see
the API index at https://docs.qualys.com/en/vm/api/index.htm -> "Asset
Management API"). Uncertain specifics are flagged ``# TODO(verify)``.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule

# Known Cloud Agent / AM dynamic tag rule types.
# TODO(verify): confirm this is the complete/current ruleType enum for the
# target subscription's AM API version — Qualys has added rule types over
# time (e.g. additional CLOUD_ASSET/location-based variants).
KNOWN_RULE_TYPES = (
    "STATIC",
    "GROOVY",
    "OS_REGEX",
    "NETWORK_RANGE",
    "NAME_CONTAINS",
    "INSTALLED_SOFTWARE",
    "OPEN_PORTS",
    "VULN_EXISTS",
    "CLOUD_ASSET",
)


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
        criteria: List of ``(field, operator, value)`` tuples. Multiple
            criteria are combined with AND by QPS.
            # TODO(verify): confirm default AND-combination semantics for the
            # target API version.
        limit: Max results per page (``preferences/limitResults``).
        offset: Pagination offset.
            # TODO(verify): confirm the exact ``preferences`` element name for
            # offset-based paging (assumed ``startFromOffset``).

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


class AssetTagsModule(BaseModule):
    """Search, create, update, and delete asset tags via the QPS AM API."""

    module_label = "asset_tags"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.search_tags, "search_tags", tier="read")
        self._add_tool(server, self.get_tag, "get_tag", tier="read")
        self._add_tool(server, self.create_tag, "create_tag", tier="write")
        self._add_tool(server, self.update_tag, "update_tag", tier="write")
        self._add_tool(server, self.delete_tag, "delete_tag", tier="destructive")

    # ------------------------------ reads ------------------------------ #
    def search_tags(
        self,
        name: str | None = None,
        name_operator: str = "CONTAINS",
        tag_id: int | None = None,
        rule_type: str | None = None,
        parent_tag_id: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """Search asset tags in the subscription.

        Args:
            name: Tag name to filter on.
            name_operator: Comparison operator for ``name`` — e.g. "CONTAINS",
                "EQUALS", "NOT EQUALS". Defaults to "CONTAINS".
            tag_id: Filter to a specific tag ID (operator EQUALS).
            rule_type: Filter to tags with this dynamic rule type. See
                :data:`KNOWN_RULE_TYPES` for common values, e.g. "STATIC",
                "GROOVY", "OS_REGEX", "NETWORK_RANGE", "NAME_CONTAINS",
                "INSTALLED_SOFTWARE", "OPEN_PORTS", "VULN_EXISTS",
                "CLOUD_ASSET". # TODO(verify): confirm full enum.
            parent_tag_id: Filter to child tags of this parent tag ID.
                # TODO(verify): confirm QPS field name for the parent reference
                # (assumed ``parentTagId``).
            limit: Max tags to return per page.
            offset: Pagination offset into the result set.
                # TODO(verify): confirm QPS preferences element name for offset paging.

        Returns:
            Parsed ServiceResponse with the matching ``Tag`` records.
        """
        criteria: list[tuple[str, str, str]] = []
        if name is not None:
            criteria.append(("name", name_operator, name))
        if tag_id is not None:
            criteria.append(("id", "EQUALS", str(tag_id)))
        if rule_type is not None:
            criteria.append(("ruleType", "EQUALS", rule_type))
        if parent_tag_id is not None:
            criteria.append(("parentTagId", "EQUALS", str(parent_tag_id)))  # TODO(verify) field name
        body = _build_search_request(criteria, limit=limit, offset=offset)
        return self._qps("/qps/rest/2.0/search/am/tag", method="POST", body_xml=body)

    def get_tag(self, tag_id: int) -> dict[str, Any]:
        """Fetch full details for a single asset tag by ID.

        Args:
            tag_id: The tag ID to fetch.

        Returns:
            Parsed ServiceResponse with the ``Tag`` record.
        """
        return self._qps(f"/qps/rest/2.0/get/am/tag/{tag_id}", method="GET")

    # ------------------------------ writes ----------------------------- #
    def create_tag(
        self,
        name: str,
        rule_type: str | None = None,
        rule_text: str | None = None,
        color: str | None = None,
        parent_tag_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new asset tag, optionally as a dynamic (rule-based) tag.

        Args:
            name: Tag name (required).
            rule_type: Dynamic tag rule type — see :data:`KNOWN_RULE_TYPES`
                for common values (e.g. "STATIC", "GROOVY", "OS_REGEX",
                "NETWORK_RANGE", "NAME_CONTAINS", "INSTALLED_SOFTWARE",
                "OPEN_PORTS", "VULN_EXISTS", "CLOUD_ASSET"). Omit for a plain
                static tag with no rule. # TODO(verify): confirm full enum.
            rule_text: The rule expression Qualys evaluates against assets for
                this tag's ``rule_type`` (e.g. a Groovy expression, a CIDR
                range for NETWORK_RANGE, a regex for OS_REGEX). Required when
                ``rule_type`` is set. # TODO(verify): confirm syntax per ruleType.
            color: Tag color as a hex string, e.g. "#0000FF".
            parent_tag_id: ID of the parent tag to nest this tag under.
                # TODO(verify): confirm the exact XML element Qualys expects
                # for the parent association — seen documented as both a
                # nested ``<parentTagId>`` element and a nested
                # ``<parent><id>...</id></parent>`` reference across QPS API
                # versions; this module assumes the flat ``<parentTagId>`` form.

        Returns:
            Parsed ServiceResponse with the created ``Tag`` (including its new ID).
        """
        fields = [f"<name>{_xml_escape(name)}</name>"]
        if rule_type is not None:
            fields.append(f"<ruleType>{_xml_escape(rule_type)}</ruleType>")
        if rule_text is not None:
            fields.append(f"<ruleText>{_xml_escape(rule_text)}</ruleText>")
        if color is not None:
            fields.append(f"<color>{_xml_escape(color)}</color>")
        if parent_tag_id is not None:
            fields.append(f"<parentTagId>{int(parent_tag_id)}</parentTagId>")  # TODO(verify)
        body = "<ServiceRequest><data><Tag>" + "".join(fields) + "</Tag></data></ServiceRequest>"
        return self._qps("/qps/rest/2.0/create/am/tag", method="POST", body_xml=body)

    def update_tag(
        self,
        tag_id: int,
        name: str | None = None,
        rule_type: str | None = None,
        rule_text: str | None = None,
        color: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing asset tag's name, color, or dynamic rule.

        Args:
            tag_id: ID of the tag to update.
            name: New tag name.
            rule_type: New dynamic rule type (see :meth:`create_tag` for valid
                values). Supply together with ``rule_text`` to add/change a rule.
            rule_text: New rule expression for ``rule_type``.
            color: New tag color as a hex string, e.g. "#00FF00".

        Returns:
            Parsed ServiceResponse with the updated ``Tag``.
        """
        fields = []
        if name is not None:
            fields.append(f"<name>{_xml_escape(name)}</name>")
        if rule_type is not None:
            fields.append(f"<ruleType>{_xml_escape(rule_type)}</ruleType>")
        if rule_text is not None:
            fields.append(f"<ruleText>{_xml_escape(rule_text)}</ruleText>")
        if color is not None:
            fields.append(f"<color>{_xml_escape(color)}</color>")
        body = "<ServiceRequest><data><Tag>" + "".join(fields) + "</Tag></data></ServiceRequest>"
        return self._qps(f"/qps/rest/2.0/update/am/tag/{tag_id}", method="POST", body_xml=body)

    # --------------------------- destructive --------------------------- #
    def delete_tag(self, tag_id: int, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete an asset tag. IRREVERSIBLE.

        Any assets currently carrying this tag will have it removed.
        # TODO(verify): confirm child-tag cascade behavior (whether child tags
        # of a deleted parent are also deleted or re-parented) for the target
        # API version.

        Args:
            tag_id: ID of the tag to delete.
            confirm: Must equal ``str(tag_id)`` to proceed.

        Returns:
            Parsed ServiceResponse confirming deletion, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(tag_id))
        if guard:
            return guard
        return self._qps(f"/qps/rest/2.0/delete/am/tag/{tag_id}", method="POST")
