"""Option Profiles module (classic FO API).

Covers listing, exporting, importing, and create/update/delete for VM, PCI,
and PC (Policy Compliance) option profiles. Option profiles have hundreds of
possible fields (scan/map/additional sections); this module implements the
core CRUD operations with the most commonly used fields rather than
enumerating every field. See ``# TODO(verify)`` markers for gaps.

Endpoints:
* ``/api/2.0/fo/subscription/option_profile/`` (export / import, any type)
* ``/api/2.0/fo/subscription/option_profile/vm/`` (VM option profiles)
* ``/api/2.0/fo/subscription/option_profile/pci/`` (PCI option profiles)
* ``/api/2.0/fo/subscription/option_profile/pc/`` (PC / Compliance option profiles)

Docs: Qualys VM/PC API User Guide — "Option Profile Export", "Option Profile
Import", "Option Profiles for VM", "Option Profiles for PCI", "Option
Profiles for Compliance".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule

#: Maps a short profile_type key to its classic FO path suffix.
_PROFILE_PATHS: dict[str, str] = {
    "vm": "/api/2.0/fo/subscription/option_profile/vm/",
    "pci": "/api/2.0/fo/subscription/option_profile/pci/",
    "pc": "/api/2.0/fo/subscription/option_profile/pc/",
}


class OptionProfilesModule(BaseModule):
    """List, export/import, and manage VM/PCI/PC option profiles."""

    module_label = "option_profiles"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_option_profiles, "list_option_profiles", tier="read")
        self._add_tool(server, self.export_option_profiles, "export_option_profiles", tier="read")
        # Writes
        self._add_tool(server, self.import_option_profiles, "import_option_profiles", tier="write")
        self._add_tool(server, self.create_option_profile, "create_option_profile", tier="write")
        self._add_tool(server, self.update_option_profile, "update_option_profile", tier="write")
        # Destructive
        self._add_tool(server, self.delete_option_profile, "delete_option_profile", tier="destructive")

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def list_option_profiles(
        self,
        profile_type: str = "vm",
        profile_id: int | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        """List option profiles of a given type (VM, PCI, or PC/Compliance).

        Args:
            profile_type: "vm", "pci", or "pc" (PC = Policy Compliance; note
                PC listing requires a PC/SCA/VMDR subscription with the API
                add-on).
            profile_id: Restrict to the option profile with this ID.
            title: Restrict to the option profile with this exact title.

        Returns:
            Parsed OPTION_PROFILES list for the given type.
        """
        profile_type = profile_type.lower().strip()
        if profile_type not in _PROFILE_PATHS:
            return {"error": f"profile_type must be one of: {', '.join(_PROFILE_PATHS)}"}
        params = {"action": "list", "id": profile_id, "title": title}
        return self._fo(_PROFILE_PATHS[profile_type], method="GET", params=params)

    def export_option_profiles(
        self,
        option_profile_id: int | None = None,
        option_profile_title: str | None = None,
        option_profile_type: str | None = None,
        include_system_option_profiles: bool | None = None,
        scan_disconnected_esxi: bool | None = None,
    ) -> dict[str, Any]:
        """Export one or all option profiles (any type) to XML.

        Requires the Manager role. Exported XML can be edited and fed back
        into ``import_option_profiles``.

        Args:
            option_profile_id: Export only the option profile with this ID.
                When omitted (with option_profile_title also omitted), all
                option profiles are exported.
            option_profile_title: Export only the option profile with this
                exact title.
            option_profile_type: Restrict to a group/type: "user" (user
                defined), "compliance", or "pci".
            include_system_option_profiles: Include Qualys system option
                profiles in the output (default False/excluded).
            scan_disconnected_esxi: Include the "Disconnected ESXi" scan
                setting in the export (v3.0+ behavior).

        Returns:
            Parsed OPTION_PROFILES XML document.
        """
        params = {
            "action": "export",
            "option_profile_id": option_profile_id,
            "option_profile_title": option_profile_title,
            "option_profile_type": option_profile_type,
            "include_system_option_profiles": include_system_option_profiles,
            "scan_disconnected_esxi": scan_disconnected_esxi,
        }
        return self._fo(
            "/api/2.0/fo/subscription/option_profile/", method="GET", params=params
        )

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def import_option_profiles(
        self, xml_body: str, echo_request: bool | None = None
    ) -> dict[str, Any]:
        """Import option profiles from an OPTION_PROFILES XML document.

        Requires the Manager role. Any search lists referenced for
        Vulnerability Detection / Custom / Excluded lists must already exist
        in the subscription (matched by title) — otherwise "Complete"
        vulnerability detection is assigned instead. Password Brute Force
        lists and PC Scan Restriction policies are never imported (always
        empty).

        Args:
            xml_body: The full ``<?xml ...?><OPTION_PROFILES>...</OPTION_PROFILES>``
                document (as exported by ``export_option_profiles``, optionally
                edited).
            echo_request: Echo input parameters back in the XML output.

        Returns:
            SIMPLE_RETURN status (with the new option profile ID/title), or
            an error dict.
        """
        # Qualys expects the entire POST body to be the raw OPTION_PROFILES
        # XML document (Content-Type: text/xml) — "action"/"echo_request" are
        # query parameters, not form fields. Use self._fo()'s raw-body
        # passthrough (content=/content_type=) instead of form-encoded data=.
        params = {"action": "import", "echo_request": echo_request}
        return self._fo(
            "/api/2.0/fo/subscription/option_profile/",
            method="POST",
            params=params,
            content=xml_body,
            content_type="text/xml",
        )

    def create_option_profile(
        self,
        profile_type: str,
        title: str,
        owner: str | None = None,
        global_profile: bool | None = None,
        offline_scanner: bool | None = None,
        default_profile: bool | None = None,
        enable_partial_ssl_tls_auditing: bool | None = None,
        scan_tcp_ports: str | None = None,
        scan_udp_ports: str | None = None,
        vulnerability_detection: str | None = None,
        basic_information_gathering: str | None = None,
        authentication: str | None = None,
        scan_overall_performance: str | None = None,
        scan_external_scanners: int | None = None,
        scan_scanner_appliances: int | None = None,
        scan_total_process: int | None = None,
        scan_http_process: int | None = None,
        scan_packet_delay: str | None = None,
        scan_intensity: str | None = None,
        scan_parallel_scaling: bool | None = None,
        scan_dead_hosts: bool | None = None,
        purge_host_data: bool | None = None,
        custom_search_list_ids: str | None = None,
        custom_search_list_title: str | None = None,
        exclude_search_list_ids: str | None = None,
        additional_tcp_ports_additional: str | None = None,
        scan_disconnected_esxi: bool | None = None,
    ) -> dict[str, Any]:
        """Create a VM, PCI, or PC (Compliance) option profile.

        # TODO(verify): option profiles support hundreds of additional fields
        # (Map section, Additional/host-discovery section, password brute
        # forcing, system authentication duplicate handling, custom HTTP
        # headers, max scan duration, etc — see the API guide's "Option
        # Profiles for VM/PCI/PC" sections). Only the most common fields are
        # exposed here; pass a curated XML via export/import for full control.

        Args:
            profile_type: "vm", "pci", or "pc" (PC = Policy Compliance).
            title: Title for the new option profile.
            owner: Owner of the option profile (defaults to the caller).
            global_profile: Share this profile with all users (Manager) or
                all business-unit users (Unit Manager).
            offline_scanner: Download this profile to offline scanners on
                next sync.
            default_profile: Make this the subscription's default profile for
                scans/maps (only one default profile allowed).
            enable_partial_ssl_tls_auditing: Enable partial SSL/TLS auditing
                during scan execution.
            scan_tcp_ports: "none", "full", "standard", or "light" (VM/PC;
                required by the API for VM/PC types).
            scan_udp_ports: "none", "full", "standard", or "light" (VM/PC;
                required by the API for VM/PC types).
            vulnerability_detection: "complete", "custom", or "runtime" (VM
                only; "runtime"/Select-at-Runtime is not supported via API
                for launching scans).
            basic_information_gathering: Map info-gathering scope: "all",
                "register", "netblockonly", or "none" (VM Map section).
            authentication: Comma-separated authentication technologies to
                enable, e.g. "Windows,Unix,Oracle,SNMP,VMware,DB2,HTTP,MySQL".
            scan_overall_performance: "high", "normal", "low", or "custom".
            scan_external_scanners: Number of external scanners to use
                (subscriptions with multiple external scanners).
            scan_scanner_appliances: Number of scanner appliances to scan
                concurrently per scan task.
            scan_total_process: Max processes to run concurrently per host
                (includes HTTP processes).
            scan_http_process: Max HTTP processes to run concurrently.
            scan_packet_delay: "minimum", "short", "medium", "long", or
                "maximum".
            scan_intensity: "normal", "medium", "low", or "minimum"
                (aggressiveness of port scanning / host discovery).
            scan_parallel_scaling: Dynamically scale hosts-in-parallel based
                on each appliance's compute resources.
            scan_dead_hosts: Scan hosts that don't respond to pings.
            purge_host_data: Purge host data when the host's OS vendor
                changes at scan time (e.g. Linux -> Windows).
            custom_search_list_ids: Comma-separated search list IDs to use
                for a "custom" vulnerability_detection scan.
            custom_search_list_title: Comma-separated search list titles to
                use for a "custom" vulnerability_detection scan.
            exclude_search_list_ids: Comma-separated search list IDs to
                exclude from the scan.
            additional_tcp_ports_additional: Comma-separated additional TCP
                ports to scan (PCI: up to 7 beyond the 13 standard ports).
            scan_disconnected_esxi: Launch authenticated ESXi scans without
                creating VMware auth records / vCenter mapping.

        Returns:
            SIMPLE_RETURN status with the new option profile ID, or an error
            dict.
        """
        profile_type = profile_type.lower().strip()
        if profile_type not in _PROFILE_PATHS:
            return {"error": f"profile_type must be one of: {', '.join(_PROFILE_PATHS)}"}
        data = {
            "action": "create",
            "title": title,
            "owner": owner,
            "global": global_profile,
            "offline_scanner": offline_scanner,
            "default": default_profile,
            "enable_partial_ssl_tls_auditing": enable_partial_ssl_tls_auditing,
            "scan_tcp_ports": scan_tcp_ports,
            "scan_udp_ports": scan_udp_ports,
            "vulnerability_detection": vulnerability_detection,
            "basic_information_gathering": basic_information_gathering,
            "authentication": authentication,
            "scan_overall_performance": scan_overall_performance,
            "scan_external_scanners": scan_external_scanners,
            "scan_scanner_appliances": scan_scanner_appliances,
            "scan_total_process": scan_total_process,
            "scan_http_process": scan_http_process,
            "scan_packet_delay": scan_packet_delay,
            "scan_intensity": scan_intensity,
            "scan_parallel_scaling": scan_parallel_scaling,
            "scan_dead_hosts": scan_dead_hosts,
            "purge_host_data": purge_host_data,
            "custom_search_list_ids": custom_search_list_ids,
            "custom_search_list_title": custom_search_list_title,
            "exclude_search_list_ids": exclude_search_list_ids,
            "additional_tcp_ports_additional": additional_tcp_ports_additional,
            "scan_disconnected_esxi": scan_disconnected_esxi,
        }
        return self._fo(_PROFILE_PATHS[profile_type], method="POST", data=data)

    def update_option_profile(
        self,
        profile_type: str,
        profile_id: int,
        title: str | None = None,
        owner: str | None = None,
        global_profile: bool | None = None,
        offline_scanner: bool | None = None,
        enable_partial_ssl_tls_auditing: bool | None = None,
        scan_tcp_ports: str | None = None,
        scan_udp_ports: str | None = None,
        vulnerability_detection: str | None = None,
        basic_information_gathering: str | None = None,
        authentication: str | None = None,
        scan_overall_performance: str | None = None,
        scan_external_scanners: int | None = None,
        scan_scanner_appliances: int | None = None,
        scan_total_process: int | None = None,
        scan_http_process: int | None = None,
        scan_packet_delay: str | None = None,
        scan_intensity: str | None = None,
        scan_parallel_scaling: bool | None = None,
        scan_dead_hosts: bool | None = None,
        purge_host_data: bool | None = None,
        custom_search_list_ids: str | None = None,
        custom_search_list_title: str | None = None,
        exclude_search_list_ids: str | None = None,
        additional_tcp_ports_additional: str | None = None,
        scan_disconnected_esxi: bool | None = None,
    ) -> dict[str, Any]:
        """Update a VM, PCI, or PC (Compliance) option profile.

        Only the fields you pass are changed; omitted fields keep their
        current value. See ``create_option_profile`` for field semantics.

        # TODO(verify): see ``create_option_profile`` — same field-coverage
        # caveat applies (hundreds of possible fields, common ones exposed).

        Args:
            profile_type: "vm", "pci", or "pc".
            profile_id: ID of the option profile to update.
            title: New title.
            owner: New owner.
            global_profile: Make/unmake this profile global.
            offline_scanner: Download to offline scanners on next sync.
            enable_partial_ssl_tls_auditing: Enable/disable partial SSL/TLS
                auditing.
            scan_tcp_ports: "none", "full", "standard", or "light".
            scan_udp_ports: "none", "full", "standard", or "light".
            vulnerability_detection: "complete", "custom", or "runtime" (VM
                only).
            basic_information_gathering: "all", "register", "netblockonly",
                or "none" (VM Map section).
            authentication: Comma-separated authentication technologies.
            scan_overall_performance: "high", "normal", "low", or "custom".
            scan_external_scanners: Number of external scanners to use.
            scan_scanner_appliances: Number of scanner appliances to use
                concurrently.
            scan_total_process: Max concurrent processes per host.
            scan_http_process: Max concurrent HTTP processes.
            scan_packet_delay: "minimum", "short", "medium", "long", or
                "maximum".
            scan_intensity: "normal", "medium", "low", or "minimum".
            scan_parallel_scaling: Enable dynamic parallel scaling.
            scan_dead_hosts: Scan hosts that don't respond to pings.
            purge_host_data: Purge host data on OS vendor change.
            custom_search_list_ids: Comma-separated search list IDs (custom
                vulnerability detection).
            custom_search_list_title: Comma-separated search list titles
                (custom vulnerability detection).
            exclude_search_list_ids: Comma-separated search list IDs to
                exclude.
            additional_tcp_ports_additional: Comma-separated additional TCP
                ports (PCI).
            scan_disconnected_esxi: Enable/disable disconnected-ESXi scanning.

        Returns:
            SIMPLE_RETURN status ("Option profile successfully updated."), or
            an error dict.
        """
        profile_type = profile_type.lower().strip()
        if profile_type not in _PROFILE_PATHS:
            return {"error": f"profile_type must be one of: {', '.join(_PROFILE_PATHS)}"}
        data = {
            "action": "update",
            "id": profile_id,
            "title": title,
            "owner": owner,
            "global": global_profile,
            "offline_scanner": offline_scanner,
            "enable_partial_ssl_tls_auditing": enable_partial_ssl_tls_auditing,
            "scan_tcp_ports": scan_tcp_ports,
            "scan_udp_ports": scan_udp_ports,
            "vulnerability_detection": vulnerability_detection,
            "basic_information_gathering": basic_information_gathering,
            "authentication": authentication,
            "scan_overall_performance": scan_overall_performance,
            "scan_external_scanners": scan_external_scanners,
            "scan_scanner_appliances": scan_scanner_appliances,
            "scan_total_process": scan_total_process,
            "scan_http_process": scan_http_process,
            "scan_packet_delay": scan_packet_delay,
            "scan_intensity": scan_intensity,
            "scan_parallel_scaling": scan_parallel_scaling,
            "scan_dead_hosts": scan_dead_hosts,
            "purge_host_data": purge_host_data,
            "custom_search_list_ids": custom_search_list_ids,
            "custom_search_list_title": custom_search_list_title,
            "exclude_search_list_ids": exclude_search_list_ids,
            "additional_tcp_ports_additional": additional_tcp_ports_additional,
            "scan_disconnected_esxi": scan_disconnected_esxi,
        }
        return self._fo(_PROFILE_PATHS[profile_type], method="POST", data=data)

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_option_profile(
        self, profile_type: str, profile_id: int, confirm: str | None = None
    ) -> dict[str, Any]:
        """Permanently delete a VM, PCI, or PC option profile. IRREVERSIBLE.

        Args:
            profile_type: "vm", "pci", or "pc".
            profile_id: ID of the option profile to delete.
            confirm: Must equal ``str(profile_id)`` to proceed.

        Returns:
            SIMPLE_RETURN status ("Option Profile Deleted Successfully"), or
            a confirmation/error dict.
        """
        profile_type = profile_type.lower().strip()
        if profile_type not in _PROFILE_PATHS:
            return {"error": f"profile_type must be one of: {', '.join(_PROFILE_PATHS)}"}
        guard = self._confirm_or_error(confirm, expected=str(profile_id))
        if guard:
            return guard
        data = {"action": "delete", "id": profile_id}
        return self._fo(_PROFILE_PATHS[profile_type], method="POST", data=data)
