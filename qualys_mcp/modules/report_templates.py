"""VM Report Templates module (classic FO API) — read/write/destructive.

Lists all report templates in the account and exports (read), creates, and
updates (write) the full settings of Scan, PCI Scan, Patch, and Map report
templates, plus deletes them (destructive).

Create/update send the template as a verbatim XML ``REPORTTEMPLATE`` document
(``report_format=xml``), so those tools take the raw XML body and pass it via
``fo(content=..., content_type="text/xml")``.

Endpoints (per template type ``{scan,pciscan,patch,map}``):
* ``/msp/report_template_list.php`` (list all templates, all types)
* ``/api/2.0/fo/report/template/<type>/?action=export`` [GET]
* ``/api/2.0/fo/report/template/<type>/?action=create&report_format=xml`` [POST]
* ``/api/2.0/fo/report/template/<type>/?action=update&report_format=xml`` [PUT]
* ``/api/2.0/fo/report/template/<type>/?action=delete`` [POST]

Docs: Qualys VM/PC API User Guide — "VM Report Templates".

Note: the API guide's "API Support for Report Templates" table documents only
Create (POST), Update (PUT), Delete (POST), and Export (GET) actions. It does
NOT document an ``import`` action for any template type — see the
``# TODO(verify)`` note in ``register_tools`` — so no import tools are added.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class ReportTemplatesModule(BaseModule):
    """List and export Qualys VM report templates (scan, PCI, patch, map)."""

    module_label = "report_templates"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(
            server, self.list_report_templates, "list_report_templates", tier="read"
        )
        self._add_tool(server, self.get_scan_template, "get_scan_template", tier="read")
        self._add_tool(
            server, self.get_pci_scan_template, "get_pci_scan_template", tier="read"
        )
        self._add_tool(server, self.get_patch_template, "get_patch_template", tier="read")
        self._add_tool(server, self.get_map_template, "get_map_template", tier="read")
        # Writes — create/update (raw XML template body)
        self._add_tool(server, self.create_scan_template, "create_scan_template", tier="write")
        self._add_tool(server, self.update_scan_template, "update_scan_template", tier="write")
        self._add_tool(
            server, self.create_pci_scan_template, "create_pci_scan_template", tier="write"
        )
        self._add_tool(
            server, self.update_pci_scan_template, "update_pci_scan_template", tier="write"
        )
        self._add_tool(server, self.create_patch_template, "create_patch_template", tier="write")
        self._add_tool(server, self.update_patch_template, "update_patch_template", tier="write")
        self._add_tool(server, self.create_map_template, "create_map_template", tier="write")
        self._add_tool(server, self.update_map_template, "update_map_template", tier="write")
        # Destructive — delete
        self._add_tool(
            server, self.delete_scan_template, "delete_scan_template", tier="destructive"
        )
        self._add_tool(
            server,
            self.delete_pci_scan_template,
            "delete_pci_scan_template",
            tier="destructive",
        )
        self._add_tool(
            server, self.delete_patch_template, "delete_patch_template", tier="destructive"
        )
        self._add_tool(
            server, self.delete_map_template, "delete_map_template", tier="destructive"
        )
        # TODO(verify): the API guide documents only create/update/delete/export
        # for report templates — no "import" action is documented for scan,
        # pciscan, patch, or map templates, so no import tools are provided.

    def list_report_templates(self) -> dict[str, Any]:
        """List all available report templates (all types) in the account.

        Returns:
            Parsed REPORT_TEMPLATE_LIST — one entry per template with ID,
            type (Auto/Manual), template_type (Scan/Map/Remediation/
            Compliance/Policy/Patch), title, owner, last_update, and the
            global flag.
        """
        return self._fo("/msp/report_template_list.php", method="GET")

    def get_scan_template(self, template_id: int | None = None) -> dict[str, Any]:
        """Export one or all Scan report templates.

        Args:
            template_id: Template ID to export. When omitted, all Scan
                templates in the account are exported.

        Returns:
            Parsed REPORTTEMPLATE/SCANTEMPLATE export (full template
            settings: title, target, display, filter, user access).
        """
        params = {"action": "export", "report_format": "xml", "template_id": template_id}
        return self._fo("/api/2.0/fo/report/template/scan/", method="GET", params=params)

    def get_pci_scan_template(self, template_id: int | None = None) -> dict[str, Any]:
        """Export one or all PCI Scan report templates.

        Args:
            template_id: Template ID to export. When omitted, all PCI Scan
                templates in the account are exported.

        Returns:
            Parsed REPORTTEMPLATE/PCISCANTEMPLATE export — same settings as
            a Scan template plus PCI risk-ranking fields.
        """
        params = {"action": "export", "report_format": "xml", "template_id": template_id}
        return self._fo("/api/2.0/fo/report/template/pciscan/", method="GET", params=params)

    def get_patch_template(self, template_id: int | None = None) -> dict[str, Any]:
        """Export one or all Patch report templates.

        Args:
            template_id: Template ID to export. When omitted, all Patch
                templates in the account are exported.

        Returns:
            Parsed REPORTTEMPLATE/PATCHTEMPLATE export (full template
            settings: title, target, display, filter, user access).
        """
        params = {"action": "export", "report_format": "xml", "template_id": template_id}
        return self._fo("/api/2.0/fo/report/template/patch/", method="GET", params=params)

    def get_map_template(self, template_id: int | None = None) -> dict[str, Any]:
        """Export one or all Map report templates.

        Args:
            template_id: Template ID to export. When omitted, all Map
                templates in the account are exported.

        Returns:
            Parsed REPORTTEMPLATE/MAPTEMPLATE export (full template
            settings).
        """
        params = {"action": "export", "report_format": "xml", "template_id": template_id}
        return self._fo("/api/2.0/fo/report/template/map/", method="GET", params=params)

    # ------------------------------ writes ----------------------------- #
    def create_scan_template(self, template_xml: str) -> dict[str, Any]:
        """Create a Scan report template from a raw XML template document.

        Args:
            template_xml: A complete ``REPORTTEMPLATE`` XML document (with a
                ``SCANTEMPLATE`` body of TITLE/TARGET/DISPLAY/FILTER/
                USERACCESS ``<INFO key=...>`` settings), matching the guide's
                scanreporttemplate DTD. Sent verbatim as the request body.

        Returns:
            SIMPLE_RETURN with the new template ID, or an error dict.
        """
        return self._template_write("scan", "create", template_xml)

    def update_scan_template(self, template_id: int, template_xml: str) -> dict[str, Any]:
        """Update an existing Scan report template with a raw XML document.

        Args:
            template_id: ID of the Scan template to update.
            template_xml: A complete ``REPORTTEMPLATE`` XML document with the
                new settings (see ``create_scan_template``). Sent verbatim as
                the request body.

        Returns:
            SIMPLE_RETURN confirming the update, or an error dict.
        """
        return self._template_write("scan", "update", template_xml, template_id=template_id)

    def create_pci_scan_template(self, template_xml: str) -> dict[str, Any]:
        """Create a PCI Scan report template from a raw XML template document.

        Args:
            template_xml: A complete ``REPORTTEMPLATE`` XML document with a
                ``PCISCANTEMPLATE`` body — the Scan template settings plus PCI
                risk-ranking fields (see the guide's pciscanreporttemplate
                DTD). Sent verbatim as the request body.

        Returns:
            SIMPLE_RETURN with the new template ID, or an error dict.
        """
        return self._template_write("pciscan", "create", template_xml)

    def update_pci_scan_template(self, template_id: int, template_xml: str) -> dict[str, Any]:
        """Update an existing PCI Scan report template with a raw XML document.

        Args:
            template_id: ID of the PCI Scan template to update.
            template_xml: A complete ``REPORTTEMPLATE`` XML document with the
                new settings (see ``create_pci_scan_template``). Sent verbatim
                as the request body.

        Returns:
            SIMPLE_RETURN confirming the update, or an error dict.
        """
        return self._template_write("pciscan", "update", template_xml, template_id=template_id)

    def create_patch_template(self, template_xml: str) -> dict[str, Any]:
        """Create a Patch report template from a raw XML template document.

        Args:
            template_xml: A complete ``REPORTTEMPLATE`` XML document with a
                ``PATCHTEMPLATE`` body of TITLE/TARGET/DISPLAY/FILTER/
                USERACCESS ``<INFO key=...>`` settings (see the guide's
                patchreporttemplate DTD). Sent verbatim as the request body.

        Returns:
            SIMPLE_RETURN with the new template ID, or an error dict.
        """
        return self._template_write("patch", "create", template_xml)

    def update_patch_template(self, template_id: int, template_xml: str) -> dict[str, Any]:
        """Update an existing Patch report template with a raw XML document.

        Args:
            template_id: ID of the Patch template to update.
            template_xml: A complete ``REPORTTEMPLATE`` XML document with the
                new settings (see ``create_patch_template``). Sent verbatim as
                the request body.

        Returns:
            SIMPLE_RETURN confirming the update (may include a NOTIFICATION),
            or an error dict.
        """
        return self._template_write("patch", "update", template_xml, template_id=template_id)

    def create_map_template(self, template_xml: str) -> dict[str, Any]:
        """Create a Map report template from a raw XML template document.

        Args:
            template_xml: A complete ``REPORTTEMPLATE`` XML document with a
                ``MAPTEMPLATE`` body of template settings. Sent verbatim as
                the request body.

        Returns:
            SIMPLE_RETURN with the new template ID, or an error dict.
        """
        return self._template_write("map", "create", template_xml)

    def update_map_template(self, template_id: int, template_xml: str) -> dict[str, Any]:
        """Update an existing Map report template with a raw XML document.

        Args:
            template_id: ID of the Map template to update.
            template_xml: A complete ``REPORTTEMPLATE`` XML document with the
                new settings (see ``create_map_template``). Sent verbatim as
                the request body.

        Returns:
            SIMPLE_RETURN confirming the update, or an error dict.
        """
        return self._template_write("map", "update", template_xml, template_id=template_id)

    # --------------------------- destructive --------------------------- #
    def delete_scan_template(
        self, template_id: int, confirm: str | None = None
    ) -> dict[str, Any]:
        """Permanently delete a Scan report template. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<template_id>.

        Args:
            template_id: ID of the Scan template to delete.
            confirm: Must equal ``str(template_id)`` to proceed.

        Returns:
            SIMPLE_RETURN status, or a confirmation/error dict.
        """
        return self._template_delete("scan", template_id, confirm)

    def delete_pci_scan_template(
        self, template_id: int, confirm: str | None = None
    ) -> dict[str, Any]:
        """Permanently delete a PCI Scan report template. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<template_id>.

        Args:
            template_id: ID of the PCI Scan template to delete.
            confirm: Must equal ``str(template_id)`` to proceed.

        Returns:
            SIMPLE_RETURN status, or a confirmation/error dict.
        """
        return self._template_delete("pciscan", template_id, confirm)

    def delete_patch_template(
        self, template_id: int, confirm: str | None = None
    ) -> dict[str, Any]:
        """Permanently delete a Patch report template. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<template_id>.

        Args:
            template_id: ID of the Patch template to delete.
            confirm: Must equal ``str(template_id)`` to proceed.

        Returns:
            SIMPLE_RETURN status, or a confirmation/error dict.
        """
        return self._template_delete("patch", template_id, confirm)

    def delete_map_template(
        self, template_id: int, confirm: str | None = None
    ) -> dict[str, Any]:
        """Permanently delete a Map report template. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<template_id>.

        Args:
            template_id: ID of the Map template to delete.
            confirm: Must equal ``str(template_id)`` to proceed.

        Returns:
            SIMPLE_RETURN status, or a confirmation/error dict.
        """
        return self._template_delete("map", template_id, confirm)

    # ------------------------------ helpers ---------------------------- #
    def _template_write(
        self,
        kind: str,
        action: str,
        template_xml: str,
        template_id: int | None = None,
    ) -> dict[str, Any]:
        """Send a create (POST) or update (PUT) with a raw XML template body.

        Args:
            kind: Template endpoint segment — "scan", "pciscan", "patch", or
                "map".
            action: "create" or "update".
            template_xml: The verbatim ``REPORTTEMPLATE`` XML document.
            template_id: Required for "update"; identifies the target template.

        Returns:
            Parsed SIMPLE_RETURN, or an error dict.
        """
        method = "POST" if action == "create" else "PUT"
        params = {"action": action, "report_format": "xml", "template_id": template_id}
        return self._fo(
            f"/api/2.0/fo/report/template/{kind}/",
            method=method,
            params=params,
            content=template_xml,
            content_type="text/xml",
        )

    def _template_delete(
        self, kind: str, template_id: int, confirm: str | None
    ) -> dict[str, Any]:
        """Guarded delete (POST action=delete) for a report template.

        Args:
            kind: Template endpoint segment — "scan", "pciscan", "patch", or
                "map".
            template_id: The template ID to delete.
            confirm: Must equal ``str(template_id)`` to proceed.

        Returns:
            Parsed SIMPLE_RETURN, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=str(template_id))
        if guard:
            return guard
        data = {"action": "delete", "template_id": template_id}
        return self._fo(
            f"/api/2.0/fo/report/template/{kind}/", method="POST", data=data
        )
