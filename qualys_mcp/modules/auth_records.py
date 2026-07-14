"""Scan Authentication module (classic FO API) — auth records for trusted scans.

Covers ``/api/2.0/fo/auth/...``: the aggregate list endpoint, per-type list
endpoints, and create/update/delete for authentication records used by
authenticated (trusted) VM/PC scans across ~40 technologies (Unix, Windows,
Oracle, MS SQL, MySQL, PostgreSQL, VMware, SNMP, HTTP, Docker, Kubernetes,
Cassandra, DataStax, application servers, cloud/network devices, etc).

Docs: Qualys VM/PC API User Guide — "Scan Authentication" (pp. 605-912).

Pattern
-------
* Reads: ``action=list`` (or the static permissions summary) via ``params=``.
* Writes: ``action=create|update`` via ``data=``.
* Destructive: ``action=delete`` via ``data=``, gated by ``_confirm_or_error``.

Generic vs. dedicated tools
----------------------------
``create_auth_record`` / ``update_auth_record`` / ``delete_auth_record`` work
for *any* record type supported by the FO auth API (pass ``record_type``) and
expose the common cross-type parameters plus an ``extra_params`` escape hatch
for type-specific fields not promoted to a named parameter.

Dedicated ``create_<type>_auth`` / ``update_<type>_auth`` tools are provided
for the most commonly used types (unix, windows, oracle, ms_sql, mysql,
postgresql, vmware, snmp, http, docker, kubernetes, mongodb, ibm_db2, sybase,
network_ssh, cassandra, palo_alto_firewall, nsx, tomcat, apache, ms_exchange)
with their real, type-specific parameters spelled out. There is no dedicated
delete per type — use ``delete_auth_record`` for all types.

Supported ``record_type`` values for the generic tools (FO endpoint
``/api/2.0/fo/auth/<record_type>/``): apache, azure_ms_sql, bind, cassandra,
cisco_apic, datastax, docker, greenplum, http, ibm_db2, ibm_websphere,
infoblox, informixdb, jboss, kubernetes, mariadb, marklogic,
microsoft_sharepoint, mongodb, ms_exchange, ms_iis, ms_sql, mysql, neo4j,
network_ssh, nginx, nsx, oracle, oracle_http_server, oracle_listener,
oracle_weblogic, palo_alto_firewall, postgresql, sap_hana, sapiq, snmp,
sybase, tomcat, unix, vcenter, vmware, windows.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule

_AUTH_BASE = "/api/2.0/fo/auth"


class AuthRecordsModule(BaseModule):
    """Create, list, update, and delete Qualys scan authentication records."""

    module_label = "auth_records"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_auth_records, "list_auth_records", tier="read")
        self._add_tool(
            server, self.list_auth_records_by_type, "list_auth_records_by_type", tier="read"
        )
        self._add_tool(server, self.get_auth_record, "get_auth_record", tier="read")
        self._add_tool(
            server, self.user_permissions_summary, "user_permissions_summary", tier="read"
        )

        # Generic writes (any record_type)
        self._add_tool(server, self.create_auth_record, "create_auth_record", tier="write")
        self._add_tool(server, self.update_auth_record, "update_auth_record", tier="write")

        # Dedicated writes for the most common record types
        self._add_tool(server, self.create_unix_auth, "create_unix_auth", tier="write")
        self._add_tool(server, self.update_unix_auth, "update_unix_auth", tier="write")
        self._add_tool(server, self.create_windows_auth, "create_windows_auth", tier="write")
        self._add_tool(server, self.update_windows_auth, "update_windows_auth", tier="write")
        self._add_tool(server, self.create_oracle_auth, "create_oracle_auth", tier="write")
        self._add_tool(server, self.update_oracle_auth, "update_oracle_auth", tier="write")
        self._add_tool(server, self.create_mssql_auth, "create_mssql_auth", tier="write")
        self._add_tool(server, self.update_mssql_auth, "update_mssql_auth", tier="write")
        self._add_tool(server, self.create_mysql_auth, "create_mysql_auth", tier="write")
        self._add_tool(server, self.update_mysql_auth, "update_mysql_auth", tier="write")
        self._add_tool(
            server, self.create_postgresql_auth, "create_postgresql_auth", tier="write"
        )
        self._add_tool(
            server, self.update_postgresql_auth, "update_postgresql_auth", tier="write"
        )
        self._add_tool(server, self.create_vmware_auth, "create_vmware_auth", tier="write")
        self._add_tool(server, self.update_vmware_auth, "update_vmware_auth", tier="write")
        self._add_tool(server, self.create_snmp_auth, "create_snmp_auth", tier="write")
        self._add_tool(server, self.update_snmp_auth, "update_snmp_auth", tier="write")
        self._add_tool(server, self.create_http_auth, "create_http_auth", tier="write")
        self._add_tool(server, self.update_http_auth, "update_http_auth", tier="write")
        self._add_tool(server, self.create_docker_auth, "create_docker_auth", tier="write")
        self._add_tool(server, self.update_docker_auth, "update_docker_auth", tier="write")
        self._add_tool(
            server, self.create_kubernetes_auth, "create_kubernetes_auth", tier="write"
        )
        self._add_tool(
            server, self.update_kubernetes_auth, "update_kubernetes_auth", tier="write"
        )
        self._add_tool(server, self.create_mongodb_auth, "create_mongodb_auth", tier="write")
        self._add_tool(server, self.update_mongodb_auth, "update_mongodb_auth", tier="write")
        self._add_tool(server, self.create_ibm_db2_auth, "create_ibm_db2_auth", tier="write")
        self._add_tool(server, self.update_ibm_db2_auth, "update_ibm_db2_auth", tier="write")
        self._add_tool(server, self.create_sybase_auth, "create_sybase_auth", tier="write")
        self._add_tool(server, self.update_sybase_auth, "update_sybase_auth", tier="write")
        self._add_tool(
            server, self.create_network_ssh_auth, "create_network_ssh_auth", tier="write"
        )
        self._add_tool(
            server, self.update_network_ssh_auth, "update_network_ssh_auth", tier="write"
        )
        self._add_tool(server, self.create_cassandra_auth, "create_cassandra_auth", tier="write")
        self._add_tool(server, self.update_cassandra_auth, "update_cassandra_auth", tier="write")
        self._add_tool(
            server,
            self.create_palo_alto_firewall_auth,
            "create_palo_alto_firewall_auth",
            tier="write",
        )
        self._add_tool(
            server,
            self.update_palo_alto_firewall_auth,
            "update_palo_alto_firewall_auth",
            tier="write",
        )
        self._add_tool(server, self.create_nsx_auth, "create_nsx_auth", tier="write")
        self._add_tool(server, self.update_nsx_auth, "update_nsx_auth", tier="write")
        self._add_tool(server, self.create_tomcat_auth, "create_tomcat_auth", tier="write")
        self._add_tool(server, self.update_tomcat_auth, "update_tomcat_auth", tier="write")
        self._add_tool(server, self.create_apache_auth, "create_apache_auth", tier="write")
        self._add_tool(server, self.update_apache_auth, "update_apache_auth", tier="write")
        self._add_tool(
            server, self.create_ms_exchange_auth, "create_ms_exchange_auth", tier="write"
        )
        self._add_tool(
            server, self.update_ms_exchange_auth, "update_ms_exchange_auth", tier="write"
        )

        # Destructive (generic; works for any record_type)
        self._add_tool(server, self.delete_auth_record, "delete_auth_record", tier="destructive")

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def list_auth_records(
        self,
        title: str | None = None,
        comments: str | None = None,
        ids: str | None = None,
        id_min: int | None = None,
        id_max: int | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """List all authentication records visible to the user, across all technologies.

        Aggregate endpoint — returns per-technology ID sets (e.g. AUTH_UNIX_IDS,
        AUTH_WINDOWS_IDS) rather than full record detail. Use
        ``list_auth_records_by_type`` or ``get_auth_record`` for full detail.
        Maximum 1,000 records per request; a ``WARNING`` element with a
        follow-up URL is returned if the result is truncated.

        Args:
            title: Restrict to records whose title contains this string.
            comments: Restrict to records whose comments contain this string.
            ids: Comma-separated record IDs and/or ID ranges (e.g. "30003250").
            id_min: Minimum record ID.
            id_max: Maximum record ID.
            echo_request: Echo the request's input parameters in the XML output.

        Returns:
            Parsed AUTH_LIST_OUTPUT / auth_records_output (per-type ID sets).
        """
        params = {
            "action": "list",
            "title": title,
            "comments": comments,
            "ids": ids,
            "id_min": id_min,
            "id_max": id_max,
            "echo_request": echo_request,
        }
        return self._fo(f"{_AUTH_BASE}/", method="GET", params=params)

    def list_auth_records_by_type(
        self,
        record_type: str,
        details: str = "Basic",
        ids: str | None = None,
        id_min: int | None = None,
        id_max: int | None = None,
        title: str | None = None,
        comments: str | None = None,
        template_auth_id: str | None = None,
        template_auth_name: str | None = None,
        is_template: bool | None = None,
        status: bool | None = None,
        is_system_created: bool | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """List authentication records for a specific technology, with full detail.

        Args:
            record_type: The FO auth record type, e.g. "unix", "windows",
                "oracle", "ms_sql", "mysql", "postgresql", "vmware", "snmp",
                "http", "docker", "kubernetes". See module docstring for the
                full list of ~40 supported values.
            details: "None" (ID only), "Basic" (default; ID + attributes), or
                "All" (Basic + a glossary of record owners).
            ids: Comma-separated record IDs and/or ID ranges.
            id_min: Minimum record ID.
            id_max: Maximum record ID.
            title: Restrict to records whose title contains this string.
            comments: Restrict to records whose comments contain this string.
            template_auth_id: (Oracle/MongoDB only) Restrict to records linked
                to this system record template ID.
            template_auth_name: (Oracle/MongoDB only) Restrict to records
                linked to this system record template name.
            is_template: (Oracle/MongoDB only) True to list only system record
                templates; False to list only regular records.
            status: True to list only active records; False for inactive only.
            is_system_created: True to list only system-created records; False
                for only user-created records.
            echo_request: Echo the request's input parameters in the XML output.

        Returns:
            Parsed AUTH_<TYPE>_LIST_OUTPUT for the requested record type.
        """
        params = {
            "action": "list",
            "details": details,
            "ids": ids,
            "id_min": id_min,
            "id_max": id_max,
            "title": title,
            "comments": comments,
            "template_auth_id": template_auth_id,
            "template_auth_name": template_auth_name,
            "is_template": is_template,
            "status": status,
            "is_system_created": is_system_created,
            "echo_request": echo_request,
        }
        return self._fo(f"{_AUTH_BASE}/{record_type}/", method="GET", params=params)

    def get_auth_record(self, record_type: str, ids: str) -> dict[str, Any]:
        """Fetch full detail (``details=All``) for one or more auth records of a given type.

        Convenience wrapper over ``list_auth_records_by_type``.

        Args:
            record_type: The FO auth record type, e.g. "unix", "windows",
                "oracle". See module docstring for the full list.
            ids: Comma-separated record IDs and/or ID ranges (e.g. "1359-1407").

        Returns:
            Parsed AUTH_<TYPE>_LIST_OUTPUT with full record detail.
        """
        params = {"action": "list", "details": "All", "ids": ids}
        return self._fo(f"{_AUTH_BASE}/{record_type}/", method="GET", params=params)

    def user_permissions_summary(self) -> dict[str, Any]:
        """Return the static user-role permissions summary for auth records.

        This is reference data transcribed from the API User Guide's "Scan
        Authentication — User Permissions Summary" section; it is not a live
        API call (Qualys does not expose this as an endpoint). For full
        details see "Managing Authentication Records" in Qualys online help.

        Returns:
            A dict keyed by action ("view_record_list", "create_record",
            "update_delete_record"), each mapping user role -> permission
            description.
        """
        return {
            "source": (
                "Qualys VM/PC API User Guide — Scan Authentication — "
                "User Permissions Summary"
            ),
            "max_records_per_request": 1000,
            "view_record_list": {
                "Manager": "View all authentication records in the subscription.",
                "Unit Manager": (
                    "View authentication records which contain hosts in the "
                    "user's business unit."
                ),
                "Scanner": (
                    "View authentication records which contain hosts in the "
                    "user's assigned asset groups."
                ),
                "Auditor, Reader": "No permissions.",
            },
            "create_record": {
                "Manager": "Create authentication records for hosts in the subscription.",
                "Unit Manager": (
                    "Create authentication records for hosts in the user's business "
                    "unit. The permission 'create/edit authentication records' must "
                    "be granted in the user's account."
                ),
                "Auditor, Scanner, Reader": "No permissions.",
            },
            "update_delete_record": {
                "Manager": "Update and delete authentication records.",
                "Unit Manager": (
                    "Update and delete authentication records. The permission "
                    "'create/edit authentication records/vaults' must be granted "
                    "in the user's account. To edit a record, at least one host "
                    "in the record must be in the user's business unit. To delete "
                    "a record, all hosts in the record must also be in the user's "
                    "business unit."
                ),
                "Auditor, Scanner, Reader": "No permissions.",
            },
        }

    # ------------------------------------------------------------------ #
    # Generic writes (any record_type)
    # ------------------------------------------------------------------ #
    def create_auth_record(
        self,
        record_type: str,
        title: str,
        ips: str | None = None,
        username: str | None = None,
        password: str | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        port: str | None = None,
        database: str | None = None,
        comments: str | None = None,
        ssl_verify: str | None = None,
        hosts: str | None = None,
        network_id: int | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create an authentication record for any supported technology.

        Covers the common cross-type fields. Types with additional or
        differently-named fields (e.g. Unix's ``sub_type``/``skip_password``,
        Windows' ``windows_domain``, Oracle's ``sid``/``servicename``) should
        either use the dedicated ``create_<type>_auth`` tool (for the most
        common types) or pass those fields via ``extra_params`` here.

        Args:
            record_type: The FO auth record type, e.g. "unix", "windows",
                "oracle", "ms_sql", "mysql", "postgresql", "vmware", "snmp",
                "http", "docker", "kubernetes", "sybase", "ibm_db2", etc. See
                module docstring for the full list of ~40 supported values.
            title: A unique title for the record (required, max 255 chars).
            ips: Comma-separated IPs/ranges to add to the record. Required to
                create for most types (Docker/Kubernetes/etc all require it too).
            username: Account username for authentication (most DB/OS types).
            password: Account password for authentication (basic login_type).
            login_type: "basic" (default) or "vault" (third-party vault lookup).
            vault_id: Vault ID to retrieve the password from (login_type=vault).
            vault_type: Vault type name, e.g. "CyberArk AIM", "HashiCorp" (see
                "Vault Support matrix" — use the ``vaults`` module's
                ``list_vaults`` to see configured vaults). Required to create
                when login_type=vault.
            port: Port the service/database instance is running on (most DB
                and network-device types).
            database: Database/instance name to authenticate to (DB types).
            comments: User-defined notes (max 1999 chars).
            ssl_verify: SSL verification setting. Most types use "0"/"1";
                VMware uses "all"/"skip"/"none". # TODO(verify): confirm exact
                accepted values per record_type before relying on this blindly.
            hosts: Comma-separated FQDNs for custom SSL certificate validation
                (used when ssl_verify requires host verification).
            network_id: Network ID for the record (only when Networks feature
                is enabled).
            extra_params: Additional type-specific fields to pass through
                as-is, e.g. {"sid": "ORCL"} for Oracle or {"folder": "...",
                "file": "..."} for a CyberArk AIM vault login. Overrides any
                same-named field set above.

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params: dict[str, Any] = {
            "action": "create",
            "title": title,
            "ips": ips,
            "username": username,
            "password": password,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "port": port,
            "database": database,
            "comments": comments,
            "ssl_verify": ssl_verify,
            "hosts": hosts,
            "network_id": network_id,
        }
        if extra_params:
            params.update(extra_params)
        return self._fo(f"{_AUTH_BASE}/{record_type}/", method="POST", data=params)

    def update_auth_record(
        self,
        record_type: str,
        ids: str,
        title: str | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        username: str | None = None,
        password: str | None = None,
        login_type: str | None = None,
        vault_id: str | None = None,
        vault_type: str | None = None,
        port: str | None = None,
        database: str | None = None,
        comments: str | None = None,
        ssl_verify: str | None = None,
        hosts: str | None = None,
        network_id: int | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update an existing authentication record for any supported technology.

        Args:
            record_type: The FO auth record type. See module docstring for
                the full list of ~40 supported values.
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            ips: Overwrites (replaces) the record's IP list. Mutually
                exclusive with add_ips/remove_ips.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            username: New account username.
            password: New account password.
            login_type: "basic" or "vault".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name (see "Vault Support matrix").
            port: New port number.
            database: New database/instance name.
            comments: New user-defined notes.
            ssl_verify: New SSL verification setting (type-dependent format;
                see create_auth_record). # TODO(verify) per record_type.
            hosts: New comma-separated FQDN list for SSL validation.
            network_id: New network ID (Networks feature only).
            extra_params: Additional type-specific fields to pass through
                as-is. Overrides any same-named field set above.

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params: dict[str, Any] = {
            "action": "update",
            "ids": ids,
            "title": title,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "username": username,
            "password": password,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "port": port,
            "database": database,
            "comments": comments,
            "ssl_verify": ssl_verify,
            "hosts": hosts,
            "network_id": network_id,
        }
        if extra_params:
            params.update(extra_params)
        return self._fo(f"{_AUTH_BASE}/{record_type}/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: Unix (also covers Cisco / Checkpoint Firewall sub-types)
    # ------------------------------------------------------------------ #
    def create_unix_auth(
        self,
        title: str,
        ips: str,
        username: str,
        password: str | None = None,
        sub_type: str | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        port: str | None = None,
        cleartext_password: bool | None = None,
        skip_password: bool | None = None,
        enable_password: str | None = None,
        expert_password: str | None = None,
        target_type: str | None = None,
        use_agentless_tracking: bool | None = None,
        agentless_tracking_path: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a Unix authentication record (also used for Cisco / Checkpoint Firewall).

        # TODO(verify): Kerberos/GSSAPI fields (use_kerberos, realm_discovery,
        # user_realm, krb5_password, ...) and the root-delegation-tools XML
        # file are abbreviated here; pass them via
        # create_auth_record(record_type="unix", extra_params={...}) instead.

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges to add to the record.
            username: The account username for authentication.
            password: The account password (required unless vault or
                skip_password is used).
            sub_type: "cisco" or "checkpoint_firewall" for those host types;
                omit for plain Unix.
            login_type: "basic" (default) or "vault".
            vault_id: Vault ID to retrieve the password from (login_type=vault).
            vault_type: Vault type name (see "Vault Support matrix").
            port: Custom port(s) for compliance scans only.
            cleartext_password: Allow the password to be sent in clear text
                for services that don't support strong encryption.
            skip_password: True if the login account has no password (Unix
                sub-type only; mutually exclusive with password/vault).
            enable_password: Password for the "enable" command (Cisco only).
            expert_password: Password for the "expert" command (Checkpoint
                Firewall only).
            target_type: "A10", "HP_COMWARE", "CISCO_ASA_WITH_FIREPOWE", or
                "auto" (default).
            use_agentless_tracking: Enable Agentless Tracking (Unix only).
            agentless_tracking_path: Host ID file path (required if
                use_agentless_tracking=True).
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "username": username,
            "password": password,
            "sub_type": sub_type,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "port": port,
            "cleartext_password": cleartext_password,
            "skip_password": skip_password,
            "enable_password": enable_password,
            "expert_password": expert_password,
            "target_type": target_type,
            "use_agentless_tracking": use_agentless_tracking,
            "agentless_tracking_path": agentless_tracking_path,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/unix/", method="POST", data=params)

    def update_unix_auth(
        self,
        ids: str,
        title: str | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        username: str | None = None,
        password: str | None = None,
        login_type: str | None = None,
        vault_id: str | None = None,
        vault_type: str | None = None,
        port: str | None = None,
        cleartext_password: bool | None = None,
        skip_password: bool | None = None,
        enable_password: str | None = None,
        expert_password: str | None = None,
        target_type: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing Unix (or Cisco / Checkpoint Firewall) authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            username: New account username.
            password: New account password.
            login_type: "basic" or "vault".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name.
            port: New custom port(s) (compliance only).
            cleartext_password: Allow clear-text password transmission.
            skip_password: True if the login account has no password.
            enable_password: New "enable" command password (Cisco only).
            expert_password: New "expert" command password (Checkpoint only).
            target_type: "A10", "HP_COMWARE", "CISCO_ASA_WITH_FIREPOWE", "auto".
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "username": username,
            "password": password,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "port": port,
            "cleartext_password": cleartext_password,
            "skip_password": skip_password,
            "enable_password": enable_password,
            "expert_password": expert_password,
            "target_type": target_type,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/unix/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: Windows
    # ------------------------------------------------------------------ #
    def create_windows_auth(
        self,
        title: str,
        ips: str,
        username: str,
        password: str | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        windows_ad_domain: str | None = None,
        windows_domain: str | None = None,
        ntlm: bool | None = None,
        kerberos: bool | None = None,
        ntlmv2: bool | None = None,
        require_smb_signing: bool | None = None,
        minimum_smb_version: str | None = None,
        use_agentless_tracking: bool | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a Windows authentication record.

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges to add to the record.
            username: The Windows account username for authentication.
            password: The account password (required unless login_type=vault).
            login_type: "basic" (default) or "vault".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name (see "Vault Support matrix").
            windows_ad_domain: Active Directory FQDN for domain-level auth.
                Mutually exclusive with windows_domain and with ips.
            windows_domain: NetBIOS domain name for domain-level auth.
                Mutually exclusive with windows_ad_domain.
            ntlm: Enable NTLMv1 (default: not attempted). Set True to allow it.
            kerberos: Enable Kerberos (default: enabled). Set False to disable.
            ntlmv2: Enable NTLMv2 (default: enabled). Set False to disable.
            require_smb_signing: Require SMB signing on target hosts (default
                False — recommended, since enabling can break auth to hosts
                without SMB signing configured).
            minimum_smb_version: Minimum SMB protocol version: "1", "2.0.2",
                "2.1", "3.0", "3.0.2", "3.1.1", or "" for no version set.
            use_agentless_tracking: Enable Agentless Tracking.
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "username": username,
            "password": password,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "windows_ad_domain": windows_ad_domain,
            "windows_domain": windows_domain,
            "ntlm": ntlm,
            "kerberos": kerberos,
            "ntlmv2": ntlmv2,
            "require_smb_signing": require_smb_signing,
            "minimum_smb_version": minimum_smb_version,
            "use_agentless_tracking": use_agentless_tracking,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/windows/", method="POST", data=params)

    def update_windows_auth(
        self,
        ids: str,
        title: str | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        username: str | None = None,
        password: str | None = None,
        login_type: str | None = None,
        vault_id: str | None = None,
        vault_type: str | None = None,
        windows_domain: str | None = None,
        ntlm: bool | None = None,
        kerberos: bool | None = None,
        ntlmv2: bool | None = None,
        require_smb_signing: bool | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing Windows authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            username: New account username.
            password: New account password.
            login_type: "basic" or "vault".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name.
            windows_domain: New NetBIOS domain name. Note: once saved, the
                domain type (AD vs NetBIOS) cannot be changed.
            ntlm: Enable/disable NTLMv1.
            kerberos: Enable/disable Kerberos.
            ntlmv2: Enable/disable NTLMv2.
            require_smb_signing: Require SMB signing on target hosts.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "username": username,
            "password": password,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "windows_domain": windows_domain,
            "ntlm": ntlm,
            "kerberos": kerberos,
            "ntlmv2": ntlmv2,
            "require_smb_signing": require_smb_signing,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/windows/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: Oracle
    # ------------------------------------------------------------------ #
    def create_oracle_auth(
        self,
        title: str,
        ips: str,
        username: str,
        password: str | None = None,
        sid: str | None = None,
        servicename: str | None = None,
        port: int | None = None,
        is_cdb: bool | None = None,
        pc_only: bool | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        is_template: bool | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create an Oracle authentication record (or an Oracle system record template).

        Exactly one of ``sid`` or ``servicename`` is required to create a
        record. # TODO(verify): OS-dependent compliance-check parameters
        (win_ora_home_*, unix_ora_home_*, perform_windows_os_checks, etc.) and
        TCPS wallet parameters (cwallet, ewallet, passphrase) are abbreviated
        here; pass them via create_auth_record(record_type="oracle",
        extra_params={...}) instead.

        Args:
            title: A unique title for the record (or template, if is_template).
            ips: Comma-separated IPs/ranges to add to the record.
            username: The Oracle account username for authentication.
            password: The account password (required unless login_type=vault).
            sid: The Oracle System ID (SID). Mutually exclusive with servicename.
            servicename: The Oracle service name. Mutually exclusive with sid.
            port: Port the instance is running on. When omitted, "All Ports"
                is used.
            is_cdb: Mark the database as a Container Database (compliance only).
            pc_only: Restrict this record to compliance scans only, allowing
                multiple records on the same host/port combination.
            login_type: "basic" (default) or "vault".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name (see "Vault Support matrix").
            is_template: Create an Oracle system record template instead of a
                regular record (used to seed credentials for auto-discovered
                instances on Unix).
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "username": username,
            "password": password,
            "sid": sid,
            "servicename": servicename,
            "port": port,
            "is_cdb": is_cdb,
            "pc_only": pc_only,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "is_template": is_template,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/oracle/", method="POST", data=params)

    def update_oracle_auth(
        self,
        ids: str,
        title: str | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        username: str | None = None,
        password: str | None = None,
        sid: str | None = None,
        servicename: str | None = None,
        port: int | None = None,
        status: bool | None = None,
        save_as_user_auth: bool | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing Oracle authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            username: New account username.
            password: New account password.
            sid: New Oracle SID. Mutually exclusive with servicename.
            servicename: New Oracle service name. Mutually exclusive with sid.
            port: New port number.
            status: Active (True) or inactive (False). System-created and
                user-created records only, not templates.
            save_as_user_auth: Convert a system-created record to a
                user-created record (system-created records only).
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "username": username,
            "password": password,
            "sid": sid,
            "servicename": servicename,
            "port": port,
            "status": status,
            "save_as_user_auth": save_as_user_auth,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/oracle/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: MS SQL
    # ------------------------------------------------------------------ #
    def create_mssql_auth(
        self,
        title: str,
        username: str,
        password: str | None = None,
        db_local: bool | None = None,
        windows_domain: str | None = None,
        auth_os_type: str | None = None,
        mssql_unix_insta_path: str | None = None,
        mssql_unix_conf_path: str | None = None,
        instance: str | None = None,
        auto_discover_instances: bool | None = None,
        database: str | None = None,
        auto_discover_databases: bool | None = None,
        port: int | None = None,
        auto_discover_ports: bool | None = None,
        member_domain: str | None = None,
        ips: str | None = None,
        kerberos: bool | None = None,
        ntlmv2: bool | None = None,
        ntlmv1: bool | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create an MS SQL Server authentication record (compliance scans).

        Requires either ``port`` or ``auto_discover_ports=True``, and either
        ``ips`` or ``member_domain`` (Windows only).

        Args:
            title: A unique title for the record.
            username: The account username for authentication.
            password: The account password (required unless login_type=vault).
            db_local: True (default) if credentials are for a local MS SQL
                Server database account; False if they are for a Windows OS
                account associated with the MS SQL Server database account.
            windows_domain: Domain where the login credentials are stored;
                required when db_local=False.
            auth_os_type: "unix" or "windows" (only when db_local=True).
            mssql_unix_insta_path: MS SQL instance directory on Unix hosts
                (only when auth_os_type="unix").
            mssql_unix_conf_path: MS SQL config file path on Unix hosts (only
                when auth_os_type="unix").
            instance: Database instance name (defaults to "MSSQLSERVER" on
                Windows if unspecified; required for Unix). Mutually exclusive
                with auto_discover_instances.
            auto_discover_instances: Auto-discover all instance names
                (Windows auth required). Mutually exclusive with instance.
            database: Database name (defaults to "master" if unspecified).
                Mutually exclusive with auto_discover_databases.
            auto_discover_databases: Auto-discover all database names.
            port: Port the instance is running on. Mutually exclusive with
                auto_discover_ports.
            auto_discover_ports: Auto-discover all ports MS SQL Server runs on
                (Unix/Windows auth required).
            member_domain: Windows-only; defines the domain of the MS SQL
                server. Required if ips/add_ips are not specified.
            ips: Comma-separated IPs/ranges to add to the record.
            kerberos: Enable/disable Kerberos (default: enabled).
            ntlmv2: Enable/disable NTLMv2 (default: enabled).
            ntlmv1: Enable/disable NTLMv1 (default: disabled).
            login_type: "basic" (default) or "vault".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name (see "Vault Support matrix").
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "username": username,
            "password": password,
            "db_local": db_local,
            "windows_domain": windows_domain,
            "auth_os_type": auth_os_type,
            "mssql_unix_insta_path": mssql_unix_insta_path,
            "mssql_unix_conf_path": mssql_unix_conf_path,
            "instance": instance,
            "auto_discover_instances": auto_discover_instances,
            "database": database,
            "auto_discover_databases": auto_discover_databases,
            "port": port,
            "auto_discover_ports": auto_discover_ports,
            "member_domain": member_domain,
            "ips": ips,
            "kerberos": kerberos,
            "ntlmv2": ntlmv2,
            "ntlmv1": ntlmv1,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/ms_sql/", method="POST", data=params)

    def update_mssql_auth(
        self,
        ids: str,
        title: str | None = None,
        username: str | None = None,
        password: str | None = None,
        database: str | None = None,
        auto_discover_databases: bool | None = None,
        port: int | None = None,
        auto_discover_ports: bool | None = None,
        member_domain: str | None = None,
        windows_domain: str | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing MS SQL Server authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            username: New account username.
            password: New account password.
            database: New database name.
            auto_discover_databases: Auto-discover all database names.
            port: New port number.
            auto_discover_ports: Auto-discover all ports.
            member_domain: New Windows domain for the record. To switch a
                record from a Windows account back to a local MS SQL account,
                set windows_domain="" to clear it.
            windows_domain: New domain for a Windows-account-based record.
            ips: Overwrites (replaces) the record's IP list. Mutually
                exclusive with add_ips/remove_ips/member_domain.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "username": username,
            "password": password,
            "database": database,
            "auto_discover_databases": auto_discover_databases,
            "port": port,
            "auto_discover_ports": auto_discover_ports,
            "member_domain": member_domain,
            "windows_domain": windows_domain,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/ms_sql/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: MySQL
    # ------------------------------------------------------------------ #
    def create_mysql_auth(
        self,
        title: str,
        ips: str,
        username: str,
        password: str | None = None,
        database: str | None = None,
        port: int | None = None,
        ssl_verify: bool | None = None,
        hosts: str | None = None,
        windows_config_file: str | None = None,
        unix_config_file: str | None = None,
        client_cert: str | None = None,
        client_key: str | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a MySQL authentication record.

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges to add to the record.
            username: The account username for authentication.
            password: The account password (required unless login_type=vault).
            database: Database name to authenticate to.
            port: Port the database is running on.
            ssl_verify: True for full SSL certificate validation. False
                (default) still allows SSL but skips server certificate
                verification.
            hosts: Comma-separated FQDNs for hosts with a custom trusted-CA
                SSL certificate installed.
            windows_config_file: Path to the MySQL config file on Windows
                hosts. Specify this or unix_config_file per host OS.
            unix_config_file: Path to the MySQL config file on Unix hosts.
            client_cert: PEM-encoded X.509 client certificate (if the server
                requires certificate auth for SSL).
            client_key: PEM-encoded RSA private key (if the server requires
                certificate auth for SSL).
            login_type: "basic" (default) or "vault".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name (see "Vault Support matrix").
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "username": username,
            "password": password,
            "database": database,
            "port": port,
            "ssl_verify": ssl_verify,
            "hosts": hosts,
            "windows_config_file": windows_config_file,
            "unix_config_file": unix_config_file,
            "client_cert": client_cert,
            "client_key": client_key,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/mysql/", method="POST", data=params)

    def update_mysql_auth(
        self,
        ids: str,
        title: str | None = None,
        username: str | None = None,
        password: str | None = None,
        database: str | None = None,
        port: int | None = None,
        ssl_verify: bool | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing MySQL authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            username: New account username.
            password: New account password.
            database: New database name.
            port: New port number.
            ssl_verify: New SSL verification setting.
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "username": username,
            "password": password,
            "database": database,
            "port": port,
            "ssl_verify": ssl_verify,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/mysql/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: PostgreSQL
    # ------------------------------------------------------------------ #
    def create_postgresql_auth(
        self,
        title: str,
        ips: str,
        username: str,
        password: str | None = None,
        pgsql_db_name: str | None = None,
        port: int | None = None,
        pgsql_win_conf_path: str | None = None,
        pgsql_unix_conf_path: str | None = None,
        ssl_verify: bool | None = None,
        hosts: str | None = None,
        client_cert: str | None = None,
        client_key: str | None = None,
        passphrase: str | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a PostgreSQL authentication record (compliance scans).

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges to add to the record.
            username: The account username for authentication.
            password: The account password (required unless login_type=vault).
            pgsql_db_name: The database instance to authenticate to.
            port: Port the database instance runs on (default 5432).
            pgsql_win_conf_path: Path to postgresql.conf on Windows assets.
            pgsql_unix_conf_path: Path to postgresql.conf on Unix assets.
            ssl_verify: True to verify the server's SSL certificate.
            hosts: Comma-separated FQDNs for hosts with a custom trusted-CA
                SSL certificate (required if ssl_verify=True).
            client_cert: Client certificate content (passphrase auth).
            client_key: Client key content (basic client_key_type).
            passphrase: Passphrase value (basic passphrase_type).
                # TODO(verify): vault-backed client_key/passphrase variants
                (client_key_type=vault, passphrase_type=vault, and their
                *_vault_type/*_vault_id fields) aren't exposed here — use
                create_auth_record(record_type="postgresql", extra_params={...}).
            login_type: "basic" (default) or "vault".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name (see "Vault Support matrix").
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "username": username,
            "password": password,
            "pgsql_db_name": pgsql_db_name,
            "port": port,
            "pgsql_win_conf_path": pgsql_win_conf_path,
            "pgsql_unix_conf_path": pgsql_unix_conf_path,
            "ssl_verify": ssl_verify,
            "hosts": hosts,
            "client_cert": client_cert,
            "client_key": client_key,
            "passphrase": passphrase,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/postgresql/", method="POST", data=params)

    def update_postgresql_auth(
        self,
        ids: str,
        title: str | None = None,
        username: str | None = None,
        password: str | None = None,
        pgsql_db_name: str | None = None,
        port: int | None = None,
        pgsql_win_conf_path: str | None = None,
        pgsql_unix_conf_path: str | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing PostgreSQL authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            username: New account username.
            password: New account password.
            pgsql_db_name: New database instance name.
            port: New port number.
            pgsql_win_conf_path: New postgresql.conf path on Windows assets.
            pgsql_unix_conf_path: New postgresql.conf path on Unix assets.
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "username": username,
            "password": password,
            "pgsql_db_name": pgsql_db_name,
            "port": port,
            "pgsql_win_conf_path": pgsql_win_conf_path,
            "pgsql_unix_conf_path": pgsql_unix_conf_path,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/postgresql/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: VMware
    # ------------------------------------------------------------------ #
    def create_vmware_auth(
        self,
        title: str,
        ips: str,
        username: str | None = None,
        password: str | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        port: int | None = None,
        hosts: str | None = None,
        ssl_verify: str | None = None,
        is_disconnect: bool | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a VMware (vSphere/ESXi) authentication record.

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges to add to the record. For
                login_type="vcenter", these are the ESXi host IPs.
            username: The VMware account username (max 13 chars).
            password: The account password (required unless login_type=vault).
            login_type: "basic" (default), "vault", or "vcenter" (scan ESXi
                hosts through vCenter; requires a separate vCenter record
                mapping vCenter IPs to these ESXi IPs).
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name (see "Vault Support matrix").
            port: Port for the ESXi web services connection (default 443).
            hosts: Comma-separated FQDNs for hosts with a custom trusted-CA
                SSL certificate.
            ssl_verify: "all" (full validation), "skip" (self-signed/custom
                root CA — no hostname check), or "none" (no verification).
            is_disconnect: True if the ESXi hosts are disconnected and should
                not receive scan traffic. Only valid with login_type="vcenter".
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "username": username,
            "password": password,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "port": port,
            "hosts": hosts,
            "ssl_verify": ssl_verify,
            "is_disconnect": is_disconnect,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/vmware/", method="POST", data=params)

    def update_vmware_auth(
        self,
        ids: str,
        title: str | None = None,
        username: str | None = None,
        password: str | None = None,
        port: int | None = None,
        ssl_verify: str | None = None,
        is_disconnect: bool | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing VMware (vSphere/ESXi) authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            username: New account username.
            password: New account password.
            port: New port number.
            ssl_verify: "all", "skip", or "none".
            is_disconnect: Mark ESXi hosts as disconnected (login_type=vcenter
                records only).
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "username": username,
            "password": password,
            "port": port,
            "ssl_verify": ssl_verify,
            "is_disconnect": is_disconnect,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/vmware/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: SNMP
    # ------------------------------------------------------------------ #
    def create_snmp_auth(
        self,
        title: str,
        ips: str,
        version: str = "v1",
        community_strings: str | None = None,
        username: str | None = None,
        password: str | None = None,
        auth_alg: str | None = None,
        encrypt_password: str | None = None,
        priv_alg: str | None = None,
        security_engine_id: str | None = None,
        context_engine_id: str | None = None,
        context: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create an SNMP authentication record (SNMPv1, v2c, or v3).

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges to add to the record.
            version: "v1" (default), "v2c", or "v3".
            community_strings: Comma-separated community strings (v1/v2c only).
            username: SNMPv3 account username (max 128 chars).
            password: SNMPv3 authentication password. If used, must be
                specified together with auth_alg (and username).
            auth_alg: SNMPv3 authentication algorithm: "MD5", "SHA1", "SHA224",
                "SHA256", "SHA384", or "SHA512".
            encrypt_password: SNMPv3 privacy (encryption) password. If used,
                must be specified together with priv_alg.
            priv_alg: SNMPv3 privacy algorithm: "DES" or "AES".
            security_engine_id: SNMPv3 security engine ID (max 128 chars),
                required if the target host configuration defines one.
            context_engine_id: SNMPv3 context engine ID for scoped PDUs.
            context: SNMPv3 context name for scoped PDUs.
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "version": version,
            "community_strings": community_strings,
            "username": username,
            "password": password,
            "auth_alg": auth_alg,
            "encrypt_password": encrypt_password,
            "priv_alg": priv_alg,
            "security_engine_id": security_engine_id,
            "context_engine_id": context_engine_id,
            "context": context,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/snmp/", method="POST", data=params)

    def update_snmp_auth(
        self,
        ids: str,
        title: str | None = None,
        version: str | None = None,
        community_strings: str | None = None,
        username: str | None = None,
        password: str | None = None,
        auth_alg: str | None = None,
        encrypt_password: str | None = None,
        priv_alg: str | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing SNMP authentication record.

        To remove authentication or privacy, pass empty strings for the
        associated parameter group (username/password/auth_alg, or
        encrypt_password/priv_alg).

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            version: "v1", "v2c", or "v3".
            community_strings: New comma-separated community strings.
            username: New SNMPv3 username.
            password: New SNMPv3 authentication password.
            auth_alg: New SNMPv3 authentication algorithm.
            encrypt_password: New SNMPv3 privacy password.
            priv_alg: New SNMPv3 privacy algorithm.
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "version": version,
            "community_strings": community_strings,
            "username": username,
            "password": password,
            "auth_alg": auth_alg,
            "encrypt_password": encrypt_password,
            "priv_alg": priv_alg,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/snmp/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: HTTP
    # ------------------------------------------------------------------ #
    def create_http_auth(
        self,
        title: str,
        username: str,
        password: str,
        vhost: str | None = None,
        realm: str | None = None,
        ips: str | None = None,
        ssl: bool | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        comments: str | None = None,
    ) -> dict[str, Any]:
        """Create an HTTP authentication record for HTTP-protocol-level auth.

        Exactly one of ``vhost``, ``realm``, or ``ips`` identifies the
        protected target and is required to create.
        # TODO(verify): add_ips/remove_ips/network_id were not explicitly
        # documented for this record type in the source guide excerpt — if
        # needed, pass them via create_auth_record(record_type="http",
        # extra_params={...}) and verify behavior.

        Args:
            title: A unique title for the record.
            username: The account username for HTTP authentication.
            password: The account password (max 100 chars).
            vhost: Virtual host FQDN to authenticate against (e.g.
                "bank.qualys.com"). Alternative to realm/ips.
            realm: HTTP realm name to authenticate against. Alternative to
                vhost/ips.
            ips: IP address to authenticate against. Alternative to vhost/realm.
            ssl: Restrict authentication attempts to HTTPS submissions only.
            login_type: "basic" (default) or "vault".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name (see "Vault Support matrix").
            comments: User-defined notes.

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "username": username,
            "password": password,
            "vhost": vhost,
            "realm": realm,
            "ips": ips,
            "ssl": ssl,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "comments": comments,
        }
        return self._fo(f"{_AUTH_BASE}/http/", method="POST", data=params)

    def update_http_auth(
        self,
        ids: str,
        title: str | None = None,
        username: str | None = None,
        password: str | None = None,
        vhost: str | None = None,
        realm: str | None = None,
        ssl: bool | None = None,
        comments: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing HTTP authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            username: New account username.
            password: New account password.
            vhost: New virtual host FQDN.
            realm: New HTTP realm name.
            ssl: Restrict authentication attempts to HTTPS submissions only.
            comments: New user-defined notes.

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "username": username,
            "password": password,
            "vhost": vhost,
            "realm": realm,
            "ssl": ssl,
            "comments": comments,
        }
        return self._fo(f"{_AUTH_BASE}/http/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: Docker
    # ------------------------------------------------------------------ #
    def create_docker_auth(
        self,
        title: str,
        ips: str,
        docker_deamon_conf_file: str | None = None,
        docker_command: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a Docker authentication record (compliance scans only).

        Used to authenticate to a Docker daemon (v1.9-1.12) on a Linux host.
        No username/password: authentication is via the local daemon command.

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges to add to the record.
            docker_deamon_conf_file: Path to the Docker daemon config file
                (e.g. "/etc/docker/daemon.json").
            docker_command: Path to the docker command to connect to the local
                daemon (e.g. "/usr/bin/docker").
            comments: User-defined notes.
            network_id: Network ID (Networks feature only; default 0).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "docker_deamon_conf_file": docker_deamon_conf_file,
            "docker_command": docker_command,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/docker/", method="POST", data=params)

    def update_docker_auth(
        self,
        ids: str,
        title: str | None = None,
        docker_deamon_conf_file: str | None = None,
        docker_command: str | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing Docker authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            docker_deamon_conf_file: New Docker daemon config file path.
            docker_command: New path to the docker command.
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "docker_deamon_conf_file": docker_deamon_conf_file,
            "docker_command": docker_command,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/docker/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: Kubernetes
    # ------------------------------------------------------------------ #
    def create_kubernetes_auth(
        self,
        title: str,
        ips: str,
        unix_bin_path: str | None = None,
        unix_conf_path: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a Kubernetes authentication record (compliance scans only).

        Used to authenticate to a Kubernetes application (v1.x) on a Unix host.

        Args:
            title: A unique title for the record (max 255 chars).
            ips: Comma-separated IPs/ranges to add to the record.
            unix_bin_path: Absolute path to the 'kubectl' binary.
            unix_conf_path: Absolute path to the Kubernetes config file.
            comments: User-defined notes (max 1999 chars).
            network_id: Network ID (Networks feature only; default 0).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "unix_bin_path": unix_bin_path,
            "unix_conf_path": unix_conf_path,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/kubernetes/", method="POST", data=params)

    def update_kubernetes_auth(
        self,
        ids: str,
        title: str | None = None,
        unix_bin_path: str | None = None,
        unix_conf_path: str | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing Kubernetes authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            unix_bin_path: New path to the 'kubectl' binary.
            unix_conf_path: New path to the Kubernetes config file.
            ips: Overwrites (replaces) the record's IP list. Mutually
                exclusive with add_ips/remove_ips.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "unix_bin_path": unix_bin_path,
            "unix_conf_path": unix_conf_path,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/kubernetes/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: MongoDB
    # ------------------------------------------------------------------ #
    def create_mongodb_auth(
        self,
        title: str,
        ips: str,
        username: str,
        password: str | None = None,
        unix_conf_file: str | None = None,
        database_name: str | None = None,
        port: int | None = None,
        ssl_verify: bool | None = None,
        hosts: str | None = None,
        credential_type: str | None = None,
        cleartext: bool | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        is_template: bool | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a MongoDB authentication record (MongoDB 3.x on Unix; VM & PC).

        # TODO(verify): The API guide's Input Parameters table names the config
        # path ``unix_conf_file`` while every curl sample uses
        # ``unix_conf_path`` — this tool sends ``unix_conf_file``; if the scan
        # cannot find the config, retry via
        # create_auth_record(record_type="mongodb", extra_params={"unix_conf_path": ...}).
        # Certificate (login_type="pkcert": private_key/passphrase/certificate/
        # require_cert) and LDAP-external nuances are abbreviated; pass them via
        # create_auth_record(record_type="mongodb", extra_params={...}).

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges to add to the record.
            username: The MongoDB (or vault) account username.
            password: The account password (required when login_type="basic").
            unix_conf_file: Full path to the MongoDB config file on Unix assets
                (must be identical across all hosts in the record).
            database_name: The database to authenticate to.
            port: Port the instance runs on (default 27017).
            ssl_verify: True to validate the server's SSL certificate.
            hosts: Comma-separated FQDNs with a custom trusted-CA SSL cert
                installed (required when ssl_verify=True).
            credential_type: "local" (default) or "external" (LDAP). For LDAP
                you must also set cleartext=True.
            cleartext: Send credentials in clear text (required True for LDAP
                external auth).
            login_type: "basic" (default), "vault", or "pkcert".
            vault_id: Vault ID to retrieve the password from (login_type=vault).
            vault_type: Vault type name (see "Vault Support matrix").
            is_template: True to create a MongoDB system record template (used
                to seed credentials for auto-discovered instances on Unix).
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "username": username,
            "password": password,
            "unix_conf_file": unix_conf_file,
            "database_name": database_name,
            "port": port,
            "ssl_verify": ssl_verify,
            "hosts": hosts,
            "credential_type": credential_type,
            "cleartext": cleartext,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "is_template": is_template,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/mongodb/", method="POST", data=params)

    def update_mongodb_auth(
        self,
        ids: str,
        title: str | None = None,
        username: str | None = None,
        password: str | None = None,
        unix_conf_file: str | None = None,
        database_name: str | None = None,
        port: int | None = None,
        ssl_verify: bool | None = None,
        status: bool | None = None,
        save_as_user_auth: bool | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing MongoDB authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            username: New account username.
            password: New account password.
            unix_conf_file: New MongoDB config-file path on Unix assets.
            database_name: New database name.
            port: New port number.
            ssl_verify: New SSL verification setting.
            status: Active (True) / inactive (False). Applies to system- and
                user-created records; not valid for templates.
            save_as_user_auth: Convert a system-created record to a
                user-created record (system-created records only).
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "username": username,
            "password": password,
            "unix_conf_file": unix_conf_file,
            "database_name": database_name,
            "port": port,
            "ssl_verify": ssl_verify,
            "status": status,
            "save_as_user_auth": save_as_user_auth,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/mongodb/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: IBM DB2
    # ------------------------------------------------------------------ #
    def create_ibm_db2_auth(
        self,
        title: str,
        ips: str,
        username: str,
        password: str | None = None,
        database: str | None = None,
        port: int | None = None,
        pc_only: bool | None = None,
        win_db2dir: str | None = None,
        unix_db2dir: str | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create an IBM DB2 authentication record (VM & PC).

        Authenticates to one or more DB2 instances on a single host. For a
        vulnerability scan an instance is unique by (IP, port); for a
        compliance scan by (IP, port, database) — set pc_only for the latter.

        # TODO(verify): OS-dependent archive-log paths (win_prilogfile/
        # unix_prilogfile, *_seclogfile, *_terlogfile, *_mirlogfile) are
        # abbreviated; pass them via
        # create_auth_record(record_type="ibm_db2", extra_params={...}).

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges to add to the record.
            username: DB2 account username (max 13 chars).
            password: DB2 account password (required unless login_type=vault).
            database: The DB2 database name (max 8 chars).
            port: Port the DB2 instance is running on.
            pc_only: True to restrict the record to compliance scans only
                (allows multiple records differing only by database name).
            win_db2dir: Path to the DB2 runtime library on Windows (for
                OS-dependent compliance checks).
            unix_db2dir: Path to the DB2 runtime library on Unix.
            login_type: "basic" (default) or "vault".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name (e.g. "CyberArk AIM", "HashiCorp").
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "username": username,
            "password": password,
            "database": database,
            "port": port,
            "pc_only": pc_only,
            "win_db2dir": win_db2dir,
            "unix_db2dir": unix_db2dir,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/ibm_db2/", method="POST", data=params)

    def update_ibm_db2_auth(
        self,
        ids: str,
        title: str | None = None,
        username: str | None = None,
        password: str | None = None,
        database: str | None = None,
        port: int | None = None,
        pc_only: bool | None = None,
        win_db2dir: str | None = None,
        unix_db2dir: str | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing IBM DB2 authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            username: New DB2 account username.
            password: New DB2 account password.
            database: New DB2 database name.
            port: New port number.
            pc_only: Restrict the record to compliance scans only.
            win_db2dir: New DB2 runtime library path on Windows.
            unix_db2dir: New DB2 runtime library path on Unix.
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "username": username,
            "password": password,
            "database": database,
            "port": port,
            "pc_only": pc_only,
            "win_db2dir": win_db2dir,
            "unix_db2dir": unix_db2dir,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/ibm_db2/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: Sybase
    # ------------------------------------------------------------------ #
    def create_sybase_auth(
        self,
        title: str,
        ips: str,
        username: str,
        password: str | None = None,
        port: int | None = None,
        database: str | None = None,
        auto_discover_databases: bool | None = None,
        installation_dir: str | None = None,
        password_encryption: bool | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a Sybase (SAP ASE) authentication record (VM & PC).

        Provide either ``database`` OR ``auto_discover_databases=True``.

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges to add to the record.
            username: Sybase (or vault) account username (max 255 chars).
            password: Sybase account password (required unless login_type=vault).
            port: The port the Sybase database is on (required to create).
            database: The Sybase database name to authenticate to. Mutually
                exclusive with auto_discover_databases.
            auto_discover_databases: True to auto-discover and authenticate to
                all Sybase databases on the host. Mutually exclusive with
                ``database``.
            installation_dir: The database installation directory (required to
                create when the record will scan Unix hosts).
            password_encryption: True if the Sybase instance requires an
                encrypted password for login (auth fails if required but off).
            login_type: "basic" (default) or "vault".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name (see "Vault Support matrix").
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "username": username,
            "password": password,
            "port": port,
            "database": database,
            "auto_discover_databases": auto_discover_databases,
            "installation_dir": installation_dir,
            "password_encryption": password_encryption,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/sybase/", method="POST", data=params)

    def update_sybase_auth(
        self,
        ids: str,
        title: str | None = None,
        username: str | None = None,
        password: str | None = None,
        port: int | None = None,
        database: str | None = None,
        auto_discover_databases: bool | None = None,
        installation_dir: str | None = None,
        password_encryption: bool | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing Sybase (SAP ASE) authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            username: New account username.
            password: New account password.
            port: New port number.
            database: New Sybase database name.
            auto_discover_databases: Enable/disable auto-discovery of databases.
            installation_dir: New database installation directory (Unix).
            password_encryption: Enable/disable required password encryption.
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "username": username,
            "password": password,
            "port": port,
            "database": database,
            "auto_discover_databases": auto_discover_databases,
            "installation_dir": installation_dir,
            "password_encryption": password_encryption,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/sybase/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: Network SSH (replaces Cisco / Checkpoint Firewall records)
    # ------------------------------------------------------------------ #
    def create_network_ssh_auth(
        self,
        title: str,
        ips: str,
        username: str,
        password: str | None = None,
        password2: str | None = None,
        port: str | None = None,
        target_type: str | None = None,
        cleartext_password: bool | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a Network SSH authentication record (SSH2; VM & PC).

        A modern replacement for the Cisco / Checkpoint Firewall records with
        the same functionality plus Unix-style ``target_type`` support. An IP
        placed in a Network SSH record cannot also appear in a Unix, Cisco, or
        Checkpoint record.

        # TODO(verify): private-key-certificate material is supplied via a
        # separate XML file body (network_ssh_auth_params.dtd) that this
        # form-based tool does not send. Vault-backed ``password2`` uses
        # ``p2_``-prefixed vault params; pass any of these via
        # create_auth_record(record_type="network_ssh", extra_params={...}).

        Args:
            title: A unique title for the record.
            ips: Comma-separated target IPs/ranges to authenticate to.
            username: The Network SSH (or vault) account username.
            password: The account password (max 100 chars).
            password2: Secondary password — the Cisco "enable" password or the
                Checkpoint Firewall "expert" password (1-31 chars).
            port: The port(s) SSH runs on (comma-separated).
            target_type: Device target type (e.g. "A10", "HP_COMWARE",
                "CISCO_ASA_WITH_FIREPOWE", "Auto (default)").
            cleartext_password: Allow the password to be sent in clear text for
                services without strong encryption (requires ``password`` on create).
            login_type: "basic" (default) or "vault".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name (see "Vault Support matrix").
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "username": username,
            "password": password,
            "password2": password2,
            "port": port,
            "target_type": target_type,
            "cleartext_password": cleartext_password,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/network_ssh/", method="POST", data=params)

    def update_network_ssh_auth(
        self,
        ids: str,
        title: str | None = None,
        username: str | None = None,
        password: str | None = None,
        password2: str | None = None,
        port: str | None = None,
        target_type: str | None = None,
        cleartext_password: bool | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing Network SSH authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            username: New account username.
            password: New account password.
            password2: New secondary (enable/expert) password.
            port: New SSH port(s) (comma-separated).
            target_type: New device target type.
            cleartext_password: Allow clear-text password transmission. Note:
                on update, if the record has no password set, this is silently
                ignored.
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "username": username,
            "password": password,
            "password2": password2,
            "port": port,
            "target_type": target_type,
            "cleartext_password": cleartext_password,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/network_ssh/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: Apache Cassandra
    # ------------------------------------------------------------------ #
    def create_cassandra_auth(
        self,
        title: str,
        ips: str,
        username: str | None = None,
        password: str | None = None,
        port: int | None = None,
        ssl_verify_with_host: bool | None = None,
        hosts: str | None = None,
        require_cert: bool | None = None,
        certificate: str | None = None,
        private_key: str | None = None,
        confpath: str | None = None,
        basepath: str | None = None,
        cleartext: bool | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create an Apache Cassandra authentication record (compliance/PC).

        # TODO(verify): passphrase and vault-backed passphrase params
        # (passphrase, use_vault_passphrase, pp_vault_type, pp_vault_record,
        # pp_<vault_parameters>) are abbreviated; pass them via
        # create_auth_record(record_type="cassandra", extra_params={...}).
        # add_ips/remove_ips are not documented for this type — the update
        # tool sends them anyway; if rejected, use ``ips`` (overwrite) instead.

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges to add to the record.
            username: The Cassandra (or vault) account username.
            password: The account password.
            port: Port the Cassandra instance is running on.
            ssl_verify_with_host: True to verify the server's SSL certificate
                is valid and trusted.
            hosts: Comma-separated FQDNs with a custom trusted-CA SSL cert
                installed (required when ssl_verify_with_host=True).
            require_cert: True to authenticate via ``certificate`` +
                ``private_key`` (enables "Require Certificate").
            certificate: Certificate content (required when require_cert=True).
            private_key: Private key content (required when require_cert=True).
            confpath: Full path to the Cassandra yaml/yml file.
            basepath: Base path to the Cassandra installation.
            cleartext: True to send credentials in clear text.
            login_type: "basic" (default) or "vault".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name (see "Vault Support matrix").
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "username": username,
            "password": password,
            "port": port,
            "ssl_verify_with_host": ssl_verify_with_host,
            "hosts": hosts,
            "require_cert": require_cert,
            "certificate": certificate,
            "private_key": private_key,
            "confpath": confpath,
            "basepath": basepath,
            "cleartext": cleartext,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/cassandra/", method="POST", data=params)

    def update_cassandra_auth(
        self,
        ids: str,
        title: str | None = None,
        username: str | None = None,
        password: str | None = None,
        port: int | None = None,
        ssl_verify_with_host: bool | None = None,
        hosts: str | None = None,
        require_cert: bool | None = None,
        certificate: str | None = None,
        private_key: str | None = None,
        confpath: str | None = None,
        basepath: str | None = None,
        cleartext: bool | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing Apache Cassandra authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            username: New account username.
            password: New account password.
            port: New port number.
            ssl_verify_with_host: New SSL verification setting.
            hosts: New comma-separated FQDN list for SSL validation.
            require_cert: Enable/disable certificate-based auth.
            certificate: New certificate content.
            private_key: New private key content.
            confpath: New path to the Cassandra yaml/yml file.
            basepath: New base path to the Cassandra installation.
            cleartext: Send credentials in clear text.
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add (see create TODO).
            remove_ips: Comma-separated IPs/ranges to remove (see create TODO).
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "username": username,
            "password": password,
            "port": port,
            "ssl_verify_with_host": ssl_verify_with_host,
            "hosts": hosts,
            "require_cert": require_cert,
            "certificate": certificate,
            "private_key": private_key,
            "confpath": confpath,
            "basepath": basepath,
            "cleartext": cleartext,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/cassandra/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: Palo Alto Firewall
    # ------------------------------------------------------------------ #
    def create_palo_alto_firewall_auth(
        self,
        title: str,
        ips: str,
        username: str,
        password: str | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a Palo Alto Firewall (PAN-OS) authentication record (VM & PC).

        The account must have the "Superuser (read-only)" role or a custom role
        with the XML API privileges "Configuration" and "Operational Requests".
        Qualys uses the PAN-OS XML API over port 443 (must be open).

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges the record will authenticate to.
            username: The Palo Alto (or vault) account username.
            password: The account password (required unless login_type=vault).
            login_type: "basic" (default) or "vault".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name (see "Vault Support matrix").
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "username": username,
            "password": password,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/palo_alto_firewall/", method="POST", data=params)

    def update_palo_alto_firewall_auth(
        self,
        ids: str,
        title: str | None = None,
        username: str | None = None,
        password: str | None = None,
        login_type: str | None = None,
        vault_id: str | None = None,
        vault_type: str | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing Palo Alto Firewall authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            username: New account username.
            password: New account password.
            login_type: "basic" or "vault".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name.
            ips: Overwrites (replaces) the record's IP list. Mutually exclusive
                with add_ips/remove_ips.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "username": username,
            "password": password,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/palo_alto_firewall/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: VMware NSX
    # ------------------------------------------------------------------ #
    def create_nsx_auth(
        self,
        title: str,
        ips: str,
        username: str,
        password: str | None = None,
        port: int | None = None,
        hosts: str | None = None,
        ssl_verify_with_host: bool | None = None,
        login_type: str = "basic",
        vault_id: str | None = None,
        vault_type: str | None = None,
        use_ad_hashicorp: bool | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a VMware NSX authentication record (VM & PC).

        Uses the classic v2.0 endpoint (``/api/2.0/fo/auth/nsx/``).
        # TODO(verify): Qualys also ships a v3.0 endpoint
        # (``/api/3.0/fo/auth/nsx/``) with expanded HashiCorp AD support; this
        # module's shared base path targets v2.0. Vault-based auth for NSX is
        # supported only for HashiCorp Vault. login_type also accepts "vcenter"
        # per the v3.0 docs — verify support on the v2.0 endpoint.

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges to add to the record.
            username: The NSX (or vault) account username.
            password: The account password (required unless login_type=vault).
            port: Port the NSX instance is running on.
            hosts: Comma-separated FQDNs with a custom trusted-CA SSL cert.
            ssl_verify_with_host: True to verify the server's SSL certificate.
            login_type: "basic" (default), "vault" (HashiCorp only), or
                "vcenter".
            vault_id: Vault ID to retrieve the password from (login_type=vault).
            vault_type: Vault type name (HashiCorp for NSX).
            use_ad_hashicorp: True to enable Active Directory when HashiCorp
                Vault is selected.
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "username": username,
            "password": password,
            "port": port,
            "hosts": hosts,
            "ssl_verify_with_host": ssl_verify_with_host,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "use_ad_hashicorp": use_ad_hashicorp,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/nsx/", method="POST", data=params)

    def update_nsx_auth(
        self,
        ids: str,
        title: str | None = None,
        username: str | None = None,
        password: str | None = None,
        port: int | None = None,
        hosts: str | None = None,
        ssl_verify_with_host: bool | None = None,
        login_type: str | None = None,
        vault_id: str | None = None,
        vault_type: str | None = None,
        use_ad_hashicorp: bool | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing VMware NSX authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            username: New account username.
            password: New account password.
            port: New port number.
            hosts: New comma-separated FQDN list for SSL validation.
            ssl_verify_with_host: New SSL verification setting.
            login_type: "basic", "vault" (HashiCorp only), or "vcenter".
            vault_id: Vault ID to retrieve the password from.
            vault_type: Vault type name.
            use_ad_hashicorp: Enable Active Directory with HashiCorp Vault.
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "username": username,
            "password": password,
            "port": port,
            "hosts": hosts,
            "ssl_verify_with_host": ssl_verify_with_host,
            "login_type": login_type,
            "vault_id": vault_id,
            "vault_type": vault_type,
            "use_ad_hashicorp": use_ad_hashicorp,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/nsx/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: Tomcat (application server)
    # ------------------------------------------------------------------ #
    def create_tomcat_auth(
        self,
        title: str,
        ips: str,
        installation_path: str | None = None,
        instance_path: str | None = None,
        auto_discover_instances: bool | None = None,
        installation_path_windows: str | None = None,
        instance_path_windows: str | None = None,
        service_name: str | None = None,
        status: bool | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a Tomcat application-server authentication record (VM & PC).

        Covers Apache Tomcat 6.x-9.x, VMware vFabric tc Server, and Pivotal tc
        Server. Provide the Unix (``installation_path``) OR Windows
        (``installation_path_windows``) install directory per the target OS.
        No login credentials: Tomcat records identify the server install/config
        on the host (OS-level auth comes from the associated Unix/Windows record).

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges to add to the record.
            installation_path: Unix install directory of the Tomcat server
                (e.g. "/opt/apache-tomcat-9.0.x", $CATALINA_HOME).
            instance_path: Unix directory of the Tomcat instance(s). Use with
                auto_discover_instances for multiple instances; leave unset
                when it equals the install directory.
            auto_discover_instances: True to auto-discover all instances (for
                vFabric/Pivotal with multiple instances).
            installation_path_windows: Windows install directory of the Tomcat
                server (e.g. "C:\\tomcat\\apache-tomcat-8.5.11").
            instance_path_windows: Windows directory of the Tomcat instance(s).
            service_name: The Tomcat service name identifying the server
                instance to authenticate to.
            status: Active (True) / inactive (False). Defaults to active.
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "installation_path": installation_path,
            "instance_path": instance_path,
            "auto_discover_instances": auto_discover_instances,
            "installation_path_windows": installation_path_windows,
            "instance_path_windows": instance_path_windows,
            "service_name": service_name,
            "status": status,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/tomcat/", method="POST", data=params)

    def update_tomcat_auth(
        self,
        ids: str,
        title: str | None = None,
        installation_path: str | None = None,
        instance_path: str | None = None,
        auto_discover_instances: bool | None = None,
        installation_path_windows: str | None = None,
        instance_path_windows: str | None = None,
        service_name: str | None = None,
        status: bool | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing Tomcat application-server authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            installation_path: New Unix install directory.
            instance_path: New Unix instance directory.
            auto_discover_instances: Enable/disable instance auto-discovery.
            installation_path_windows: New Windows install directory.
            instance_path_windows: New Windows instance directory.
            service_name: New Tomcat service name.
            status: Active (True) / inactive (False).
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "installation_path": installation_path,
            "instance_path": instance_path,
            "auto_discover_instances": auto_discover_instances,
            "installation_path_windows": installation_path_windows,
            "instance_path_windows": instance_path_windows,
            "service_name": service_name,
            "status": status,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/tomcat/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: Apache HTTP Server (application server)
    # ------------------------------------------------------------------ #
    def create_apache_auth(
        self,
        title: str,
        ips: str,
        unix_apache_config_file: str | None = None,
        unix_apache_control_command: str | None = None,
        windows_apache_config_file: str | None = None,
        windows_apache_control_command: str | None = None,
        status: bool | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create an Apache Web Server authentication record (VM & PC).

        Also covers IBM HTTP Server, VMware vFabric Web Server, and Pivotal
        Web Server. Provide the Unix config/control pair OR the Windows
        config/control pair per the target OS. No login credentials: OS-level
        auth comes from the associated Unix/Windows record.

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges to add to the record.
            unix_apache_config_file: Path to the Apache config file on Unix.
            unix_apache_control_command: Path to the Apache control command on
                Unix (for IBM HTTP Server, the "bin" dir or "apachectl"; for
                vFabric, the global "bin" dir or "httpdctl").
            windows_apache_config_file: Windows path to the Apache/IBM HTTP
                server config file.
            windows_apache_control_command: Windows path to the Apache/IBM HTTP
                server control command.
            status: Active (True) / inactive (False). Defaults to active.
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "unix_apache_config_file": unix_apache_config_file,
            "unix_apache_control_command": unix_apache_control_command,
            "windows_apache_config_file": windows_apache_config_file,
            "windows_apache_control_command": windows_apache_control_command,
            "status": status,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/apache/", method="POST", data=params)

    def update_apache_auth(
        self,
        ids: str,
        title: str | None = None,
        unix_apache_config_file: str | None = None,
        unix_apache_control_command: str | None = None,
        windows_apache_config_file: str | None = None,
        windows_apache_control_command: str | None = None,
        status: bool | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing Apache Web Server authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            unix_apache_config_file: New Unix config file path.
            unix_apache_control_command: New Unix control command path.
            windows_apache_config_file: New Windows config file path.
            windows_apache_control_command: New Windows control command path.
            status: Active (True) / inactive (False). Valid on update only for
                user-created records.
            ips: Overwrites (replaces) the record's IP list.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "unix_apache_config_file": unix_apache_config_file,
            "unix_apache_control_command": unix_apache_control_command,
            "windows_apache_config_file": windows_apache_config_file,
            "windows_apache_control_command": windows_apache_control_command,
            "status": status,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/apache/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Dedicated: MS Exchange Server
    # ------------------------------------------------------------------ #
    def create_ms_exchange_auth(
        self,
        title: str,
        ips: str,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Create an MS Exchange Server authentication record (compliance/PC).

        The record identifies target hosts only; login uses the Windows
        authentication record(s) that also cover these IPs (no username/
        password is set on the MS Exchange record itself).

        Args:
            title: A unique title for the record.
            ips: Comma-separated IPs/ranges the server will authenticate to.
            comments: User-defined notes.
            network_id: Network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the new record ID, or an error dict.
        """
        params = {
            "action": "create",
            "title": title,
            "ips": ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/ms_exchange/", method="POST", data=params)

    def update_ms_exchange_auth(
        self,
        ids: str,
        title: str | None = None,
        ips: str | None = None,
        add_ips: str | None = None,
        remove_ips: str | None = None,
        comments: str | None = None,
        network_id: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing MS Exchange Server authentication record.

        Args:
            ids: Comma-separated record IDs and/or ID ranges to update.
            title: New title for the record.
            ips: Overwrites (replaces) the record's IP list. Cannot be
                specified together with add_ips/remove_ips.
            add_ips: Comma-separated IPs/ranges to add to the existing list.
            remove_ips: Comma-separated IPs/ranges to remove from the list.
            comments: New user-defined notes.
            network_id: New network ID (Networks feature only).

        Returns:
            BATCH_RETURN with the updated record ID(s), or an error dict.
        """
        params = {
            "action": "update",
            "ids": ids,
            "title": title,
            "ips": ips,
            "add_ips": add_ips,
            "remove_ips": remove_ips,
            "comments": comments,
            "network_id": network_id,
        }
        return self._fo(f"{_AUTH_BASE}/ms_exchange/", method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Destructive (generic; any record_type)
    # ------------------------------------------------------------------ #
    def delete_auth_record(
        self, record_type: str, ids: str, confirm: str | None = None
    ) -> dict[str, Any]:
        """Permanently delete one or more authentication records. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<ids>.

        Args:
            record_type: The FO auth record type, e.g. "unix", "windows",
                "oracle". See module docstring for the full list of ~40
                supported values.
            ids: Comma-separated record IDs and/or ID ranges to delete. To
                delete a record, all hosts in the record must be in the
                caller's business unit (Unit Manager role).
            confirm: Must equal ``ids`` to proceed.

        Returns:
            BATCH_RETURN status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=ids)
        if guard:
            return guard
        data = {"action": "delete", "ids": ids}
        return self._fo(f"{_AUTH_BASE}/{record_type}/", method="POST", data=data)
