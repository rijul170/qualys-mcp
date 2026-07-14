"""Vault Support module (classic FO API) — third-party password vault definitions.

Covers ``/api/2.0/fo/vault/``: list, view, create, update, and delete
authentication vault configurations. A "vault" record here is the standalone
connection definition for a third-party password vault (e.g. CyberArk AIM,
HashiCorp, Thycotic Secret Server); it is separate from an *authentication
record's* ``login_type=vault``/``vault_id``/``vault_type`` fields (see the
``auth_records`` module), which reference a vault defined here by ID.

Docs: Qualys VM/PC API User Guide — "Vault Support" (pp. 885-912): Vault
Support matrix, Vault Definition, List Vaults, Manage Vaults.

Pattern
-------
* Reads: ``action=list`` / ``action=view`` via ``params=``.
* Writes: ``action=create`` / ``action=update`` via ``data=``.
* Destructive: ``action=delete`` via ``data=``, gated by ``_confirm_or_error``.

Supported ``vault_type`` values (see "Vault Support matrix" for which
technologies/capabilities each vault supports): ARCON PAM, Azure Key,
BeyondTrust PBPS, CA Access Control, CA PAM, CyberArk AIM, CyberArk PIM Suite,
HashiCorp, Hitachi ID PAM, Lieberman ERPM, Quest Vault, Thycotic Secret
Server, Wallix AdminBastion (WAB).

Each vault type has its own required/optional settings fields (see "Tell me
about vault settings" in the API guide). The most common fields across types
(url, username, password, ssl_verify, port, domain, appid, safe, cert,
private_key, private_key_pwd, api_version, auth_type, path, role_name,
role_id, secret_id, server_address, access_key, appkey, folder, file,
system_name, account_name) are exposed as named parameters on
``create_vault``/``update_vault``; anything else can be passed via
``extra_params``.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule

_VAULT_PATH = "/api/2.0/fo/vault/"


class VaultsModule(BaseModule):
    """List and manage third-party authentication vault definitions."""

    module_label = "vaults"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_vaults, "list_vaults", tier="read")
        self._add_tool(server, self.get_vault, "get_vault", tier="read")

        # Writes
        self._add_tool(server, self.create_vault, "create_vault", tier="write")
        self._add_tool(server, self.update_vault, "update_vault", tier="write")

        # Destructive
        self._add_tool(server, self.delete_vault, "delete_vault", tier="destructive")

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def list_vaults(
        self,
        title: str | None = None,
        vault_type: str | None = None,
        modified: str | None = None,
        orderby: str | None = None,
        sortorder: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        echo_request: bool | None = None,
    ) -> dict[str, Any]:
        """List authentication vault definitions configured in the subscription.

        Permissions: Managers, Unit Managers, and Scanners can view vaults.

        Args:
            title: Restrict to vaults whose title matches this string.
            vault_type: Restrict to a single vault type, e.g. "CyberArk AIM",
                "HashiCorp", "Thycotic Secret Server". See module docstring
                for the full list of supported values.
            modified: Restrict to vaults modified on/after this date/time,
                format "YYYY-MM-DD[THH:MM:SSZ]" (UTC/GMT).
            orderby: Sort field: "id", "title", "system_name",
                "last_modified", or "last_modified_by".
            sortorder: "asc" (default) or "desc". Used with orderby.
            limit: Max vault records to return, starting at offset. The API
                requires limit and offset to be specified together (or
                neither) — if only one is given here, the other is defaulted
                (limit defaults to 1000; offset defaults to 0) so the request
                always sends both or neither.
            offset: Starting vault record number (used with limit). See
                ``limit`` for the both-or-neither pairing behavior.
            echo_request: Echo the request's input parameters in the XML output.

        Returns:
            Parsed AUTH_VAULT_LIST_OUTPUT with the matching vault summaries
            (title, vault_type, last_modified, id).
        """
        # Qualys rejects requests that specify only one of limit/offset
        # ("specify both or none"). If the caller gave exactly one, default
        # the other so we always send the pair together (or neither).
        if limit is None and offset is not None:
            limit = 1000
        if offset is None and limit is not None:
            offset = 0
        params = {
            "action": "list",
            "title": title,
            "type": vault_type,
            "modified": modified,
            "orderby": orderby,
            "sortorder": sortorder,
            "limit": limit,
            "offset": offset,
            "echo_request": echo_request,
        }
        return self._fo(_VAULT_PATH, method="GET", params=params)

    def get_vault(self, vault_id: str) -> dict[str, Any]:
        """View full settings for a single authentication vault.

        Args:
            vault_id: The vault's ID.

        Returns:
            Parsed VAULT_OUTPUT with the vault's type-specific settings
            (e.g. URL, safe name, app ID) — never includes secret values
            like passwords or private keys.
        """
        params = {"action": "view", "id": vault_id}
        return self._fo(_VAULT_PATH, method="GET", params=params)

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def create_vault(
        self,
        title: str,
        vault_type: str,
        comments: str | None = None,
        url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        ssl_verify: bool | None = None,
        port: int | None = None,
        domain: str | None = None,
        appid: str | None = None,
        safe: str | None = None,
        cert: str | None = None,
        private_key: str | None = None,
        private_key_pwd: str | None = None,
        api_version: str | None = None,
        auth_type: str | None = None,
        path: str | None = None,
        role_name: str | None = None,
        role_id: str | None = None,
        secret_id: str | None = None,
        server_address: str | None = None,
        access_key: str | None = None,
        appkey: str | None = None,
        folder: str | None = None,
        file: str | None = None,
        system_name: str | None = None,
        account_name: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new third-party authentication vault definition.

        Permissions: Managers can always create vaults; Unit Managers need
        the "Create/edit authentication records/vaults" permission.

        Field applicability is vault-type-specific — see "Tell me about vault
        settings" in the API guide for the exact required/optional fields per
        ``vault_type``. Common examples:
        * CyberArk AIM: appid, safe, url, ssl_verify, cert, private_key,
          private_key_pwd.
        * HashiCorp: url, api_version, ssl_verify, auth_type ("userpass",
          "cert", or "approle") plus path/username/password (userpass),
          path/role_name/cert/private_key/passphrase (cert), or
          path/role_id/secret_id (approle).
        * Thycotic Secret Server: url, username, password, domain.
        * Quest Vault: server_address, port, username, access_key.
        * CyberArk PIM Suite: server_address, port, safe, username, password.
        * Wallix AdminBastion (WAB): url, ssl_verify, username, password or
          appkey.
        # TODO(verify): vault-type-specific fields not promoted to a named
        # parameter here (e.g. CA Access Control's ca_url/ca_api_username/
        # ca_ssl_verify/ca_web_username/ca_web_password, Azure Key's
        # app_id/ak_secret_name, ARCON PAM's vault_service_type/ssl_verify)
        # should be passed via extra_params.

        Args:
            title: The vault title (required).
            vault_type: The vault type. One of: "ARCON PAM", "Azure Key",
                "BeyondTrust PBPS", "CA Access Control", "CA PAM",
                "CyberArk AIM", "CyberArk PIM Suite", "HashiCorp",
                "Hitachi ID PAM", "Lieberman ERPM", "Quest Vault",
                "Thycotic Secret Server", "Wallix AdminBastion (WAB)".
            comments: User-defined comments.
            url: HTTP/HTTPS URL to the vault's API (most HTTP-based vaults).
            username: Username for accessing the vault.
            password: Password for accessing the vault.
            ssl_verify: Verify the vault server's SSL certificate (default
                True for most vault types).
            port: Port the vault server listens on (Quest Vault, CyberArk PIM
                Suite).
            domain: FQDN if the vault is integrated with Active Directory
                (Thycotic Secret Server, Lieberman ERPM).
            appid: Application ID for CyberArk AIM's CCP web services.
            safe: Digital password safe name (CyberArk AIM / CyberArk PIM Suite).
            cert: X.509 client certificate content (PEM, with header/footer).
            private_key: RSA private key content (PEM, with header/footer).
            private_key_pwd: Passphrase for an encrypted private_key.
            api_version: HashiCorp Vault HTTP API version (default "v1").
            auth_type: HashiCorp auth method: "userpass", "cert", or "approle".
            path: HashiCorp auth mount path (defaults vary by auth_type, e.g.
                "auth/userpass", "auth/cert", "auth/approle").
            role_name: HashiCorp cert-auth role name.
            role_id: HashiCorp approle role ID.
            secret_id: HashiCorp approle secret ID.
            server_address: Vault server IP (Quest Vault, CyberArk PIM Suite).
            access_key: API/CLI key for SSH auth to Quest Vault.
            appkey: Application key (BeyondTrust PBPS) or REST API key
                (Wallix AdminBastion).
            folder: Digital safe folder name (CyberArk AIM).
            file: Digital safe file name (CyberArk AIM).
            system_name: Managed system/asset name (BeyondTrust PBPS).
            account_name: Managed account name (BeyondTrust PBPS).
            extra_params: Additional vault-type-specific fields to pass
                through as-is. Overrides any same-named field set above.

        Returns:
            SIMPLE_RETURN with the new vault ID, or an error dict.
        """
        params: dict[str, Any] = {
            "action": "create",
            "title": title,
            "type": vault_type,
            "comments": comments,
            "url": url,
            "username": username,
            "password": password,
            "ssl_verify": ssl_verify,
            "port": port,
            "domain": domain,
            "appid": appid,
            "safe": safe,
            "cert": cert,
            "private_key": private_key,
            "private_key_pwd": private_key_pwd,
            "api_version": api_version,
            "auth_type": auth_type,
            "path": path,
            "role_name": role_name,
            "role_id": role_id,
            "secret_id": secret_id,
            "server_address": server_address,
            "access_key": access_key,
            "appkey": appkey,
            "folder": folder,
            "file": file,
            "system_name": system_name,
            "account_name": account_name,
        }
        if extra_params:
            params.update(extra_params)
        return self._fo(_VAULT_PATH, method="POST", data=params)

    def update_vault(
        self,
        vault_id: str,
        title: str | None = None,
        comments: str | None = None,
        url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        ssl_verify: bool | None = None,
        port: int | None = None,
        domain: str | None = None,
        appid: str | None = None,
        safe: str | None = None,
        cert: str | None = None,
        private_key: str | None = None,
        private_key_pwd: str | None = None,
        api_version: str | None = None,
        auth_type: str | None = None,
        path: str | None = None,
        role_name: str | None = None,
        role_id: str | None = None,
        secret_id: str | None = None,
        server_address: str | None = None,
        access_key: str | None = None,
        appkey: str | None = None,
        folder: str | None = None,
        file: str | None = None,
        system_name: str | None = None,
        account_name: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update settings for an existing authentication vault.

        Only the fields provided are changed; the vault's type cannot be
        changed after creation. See ``create_vault`` for field semantics.

        Args:
            vault_id: The vault's ID (required).
            title: New title to replace the existing one.
            comments: New user-defined comments.
            url: New vault API URL.
            username: New username for accessing the vault.
            password: New password for accessing the vault.
            ssl_verify: New SSL verification setting.
            port: New port number.
            domain: New Active Directory domain.
            appid: New CyberArk AIM application ID.
            safe: New digital password safe name.
            cert: New client certificate content.
            private_key: New private key content.
            private_key_pwd: New private key passphrase.
            api_version: New HashiCorp API version.
            auth_type: New HashiCorp auth method.
            path: New HashiCorp auth mount path.
            role_name: New HashiCorp cert-auth role name.
            role_id: New HashiCorp approle role ID.
            secret_id: New HashiCorp approle secret ID.
            server_address: New vault server IP.
            access_key: New SSH access key (Quest Vault).
            appkey: New application/API key.
            folder: New CyberArk AIM folder name.
            file: New CyberArk AIM file name.
            system_name: New managed system/asset name (BeyondTrust PBPS).
            account_name: New managed account name (BeyondTrust PBPS).
            extra_params: Additional vault-type-specific fields to pass
                through as-is. Overrides any same-named field set above.

        Returns:
            SIMPLE_RETURN with the updated vault ID, or an error dict.
        """
        params: dict[str, Any] = {
            "action": "update",
            "id": vault_id,
            "title": title,
            "comments": comments,
            "url": url,
            "username": username,
            "password": password,
            "ssl_verify": ssl_verify,
            "port": port,
            "domain": domain,
            "appid": appid,
            "safe": safe,
            "cert": cert,
            "private_key": private_key,
            "private_key_pwd": private_key_pwd,
            "api_version": api_version,
            "auth_type": auth_type,
            "path": path,
            "role_name": role_name,
            "role_id": role_id,
            "secret_id": secret_id,
            "server_address": server_address,
            "access_key": access_key,
            "appkey": appkey,
            "folder": folder,
            "file": file,
            "system_name": system_name,
            "account_name": account_name,
        }
        if extra_params:
            params.update(extra_params)
        return self._fo(_VAULT_PATH, method="POST", data=params)

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_vault(self, vault_id: str, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete an authentication vault definition. IRREVERSIBLE.

        Deleting a vault that is still referenced by authentication records
        (via ``vault_id``) will break authentication for those records.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<vault_id>.

        Args:
            vault_id: The vault's ID to delete.
            confirm: Must equal ``vault_id`` to proceed.

        Returns:
            SIMPLE_RETURN status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=vault_id)
        if guard:
            return guard
        data = {"action": "delete", "id": vault_id}
        return self._fo(_VAULT_PATH, method="POST", data=data)
