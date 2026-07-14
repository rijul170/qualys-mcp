"""Users module (classic FO API) — Users and Activity Log.

Covers subscription user management: list users, add/edit user accounts,
activate/deactivate accounts, self-service login password change, and
exporting the user activity log.

Endpoints:
* ``/msp/user_list.php`` — list users.
* ``/msp/user.php`` — add/edit user; activate/deactivate user.
* ``/api/2.0/fo/user/change_password/`` — change the calling user's login password.
* ``/api/2.0/fo/activity_log/`` — export the user activity log (CSV).

Docs: Qualys VM/PC API User Guide — "Users and Activity Log" (pp. 1863-1887).
"""

import json
from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class UsersModule(BaseModule):
    """Manage subscription users and review user activity."""

    module_label = "users"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_users, "list_users", tier="read")
        self._add_tool(
            server, self.export_user_activity_log, "export_user_activity_log", tier="read"
        )
        # Writes
        self._add_tool(server, self.add_or_edit_user, "add_or_edit_user", tier="write")
        self._add_tool(
            server, self.activate_deactivate_user, "activate_deactivate_user", tier="write"
        )
        self._add_tool(server, self.change_login_password, "change_login_password", tier="write")
        self._add_tool(server, self.accept_eula, "accept_eula", tier="write")
        self._add_tool(
            server, self.admin_change_user_password, "admin_change_user_password", tier="write"
        )

    # ------------------------------ reads ------------------------------ #
    def list_users(
        self,
        external_id_contains: str | None = None,
        external_id_assigned: bool | None = None,
        show_access_permissions: bool | None = None,
    ) -> dict[str, Any]:
        """List users visible to the calling account in the subscription.

        Args:
            external_id_contains: Only show users whose external ID contains
                this substring (max 256 chars, case-sensitive). Mutually
                exclusive with ``external_id_assigned``.
            external_id_assigned: True to show only users with an external ID
                assigned; False to show only users without one. Mutually
                exclusive with ``external_id_contains``.
            show_access_permissions: Include access permission info (GUI, API, SAML).

        Returns:
            Parsed USER_LIST_OUTPUT (users with login, general info, asset
            groups, and permissions; last login date is included for
            Manager/Unit Manager callers).
        """
        params = {
            "external_id_contains": external_id_contains,
            "external_id_assigned": external_id_assigned,
            "show_access_permissions": show_access_permissions,
        }
        return self._fo("/msp/user_list.php", method="GET", params=params)

    def export_user_activity_log(
        self,
        user_action: str | None = None,
        action_details: str | None = None,
        username: str | None = None,
        since_datetime: str | None = None,
        until_datetime: str | None = None,
        user_role: str | None = None,
        truncation_limit: int | None = None,
    ) -> dict[str, Any]:
        """Export the subscription's user activity log (CSV output only).

        Args:
            user_action: Filter by action, e.g. "login", "launch", "finished",
                "add", "edit", "delete", "request" (see Qualys's "User actions"
                reference table for the full list of ~50 action keywords).
            action_details: Filter on further detail about the action (e.g. an
                error-message substring for the "error" action).
            username: Restrict to actions performed by this user login.
                Populated in the output only when the caller is a Manager or
                Unit Manager (a Unit Manager sees only users in their hierarchy).
            since_datetime: Include activity from this point on. Format
                ``YYYY-MM-DD[THH:MM:SSZ]`` (UTC), e.g. "2024-01-01" or
                "2024-01-01T00:00:00Z". Must be <= today.
            until_datetime: Include activity up to this point. Same format as
                ``since_datetime``; must be >= ``since_datetime`` and <= today.
            user_role: Comma-separated user roles to restrict the export to —
                Manager, Unit Manager, Auditor, Scanner, Reader,
                "KnowledgeBase Only", "Remediation User", Contact. Defaults to
                all roles visible to the caller.
            truncation_limit: Maximum number of log records to include.

        Returns:
            ``{"raw": <csv text>}`` — the activity log endpoint only supports
            CSV output.
        """
        params = {
            "action": "list",
            "user_action": user_action,
            "action_details": action_details,
            "username": username,
            "since_datetime": since_datetime,
            "until_datetime": until_datetime,
            "user_role": user_role,
            "output_format": "csv",
            "truncation_limit": truncation_limit,
        }
        return self._fo("/api/2.0/fo/activity_log/", method="GET", params=params, parse=False)

    # ------------------------------ writes ----------------------------- #
    def add_or_edit_user(
        self,
        action: str,
        login: str | None = None,
        user_role: str | None = None,
        business_unit: str | None = None,
        asset_groups: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        title: str | None = None,
        phone: str | None = None,
        fax: str | None = None,
        email: str | None = None,
        address1: str | None = None,
        address2: str | None = None,
        city: str | None = None,
        country: str | None = None,
        state: str | None = None,
        zip_code: str | None = None,
        external_id: str | None = None,
        send_email: bool | None = None,
        time_zone_code: str | None = None,
    ) -> dict[str, Any]:
        """Add a new user account, or edit an existing one.

        For ``action="add"``: ``user_role``, ``business_unit``, ``first_name``,
        ``last_name``, ``title``, ``email``, ``address1``, ``city``, and
        ``country`` are required (``state`` is additionally required when
        ``country`` is "United States of America", "Australia", "Canada", or
        "India"). ``login`` must be omitted — Qualys generates it.

        For ``action="edit"``: ``login`` is required. ``user_role`` and
        ``business_unit`` cannot be changed via this API (omit them). Any
        other field supplied replaces the existing value; pass ``""`` on a
        clearable field (e.g. ``external_id``, ``time_zone_code``) to clear it.

        Args:
            action: "add" or "edit".
            login: Qualys user login to edit. Required for edit; invalid for add.
            user_role: One of "manager", "unit_manager", "scanner", "reader",
                "contact", "administrator". Required for add; invalid for edit.
            business_unit: "Unassigned" or an existing custom business unit
                title. Required for add; invalid for edit.
            asset_groups: Comma-separated asset group titles assigned to the
                user. Only valid when the user role is Scanner, Reader, or
                Contact (invalid for Manager/Unit Manager).
            first_name: User's first name (required for add).
            last_name: User's last name (required for add).
            title: User's job title (required for add).
            phone: User's phone number.
            fax: User's fax number.
            email: User's email address (required for add).
            address1: Address line 1 (required for add).
            address2: Address line 2.
            city: City (required for add).
            country: Country name, e.g. "United States of America" (required for add).
            state: State/province code. Required for add when ``country`` is
                United States of America, Australia, Canada, or India.
            zip_code: Zip/postal code (defaults to the API user's zip code if omitted on add).
            external_id: Custom external ID (max 256 chars, case sensitive).
                Pass ``""`` to delete an existing external ID on edit.
            send_email: Add only. True (default) emails the new user a secure
                link to their credentials; False causes the response to
                include the generated login/password as XML value pairs instead.
            time_zone_code: Timezone code (see the ``time_zone_code_list``
                function for valid codes); pass ``""`` to reset to the
                browser's timezone.

        Returns:
            Parsed USER_OUTPUT with a SUCCESS/FAILED status and message.
        """
        action = action.lower().strip()
        if action not in ("add", "edit"):
            return {"error": "action must be one of: add, edit"}
        data = {
            "action": action,
            "login": login,
            "user_role": user_role,
            "business_unit": business_unit,
            "asset_groups": asset_groups,
            "first_name": first_name,
            "last_name": last_name,
            "title": title,
            "phone": phone,
            "fax": fax,
            "email": email,
            "address1": address1,
            "address2": address2,
            "city": city,
            "country": country,
            "state": state,
            "zip_code": zip_code,
            "external_id": external_id,
            "send_email": send_email,
            "time_zone_code": time_zone_code,
        }
        return self._fo("/msp/user.php", method="POST", data=data)

    def activate_deactivate_user(self, login: str, action: str) -> dict[str, Any]:
        """Activate an inactive user account, or deactivate an active one.

        Cannot be used on accounts with "Pending Activation" status.
        Deactivating a user does not delete their account settings — they can
        be reactivated later.

        Args:
            login: Qualys user login to activate/deactivate.
            action: "activate" (Inactive -> Active) or "deactivate"
                (Active -> Inactive).

        Returns:
            Parsed USER_OUTPUT with a SUCCESS/FAILED status and message.
        """
        action = action.lower().strip()
        if action not in ("activate", "deactivate"):
            return {"error": "action must be one of: activate, deactivate"}
        data = {"action": action, "login": login}
        return self._fo("/msp/user.php", method="POST", data=data)

    def change_login_password(self, new_password: str) -> dict[str, Any]:
        """Change the login password for the account making this API call.

        Per the VM/PC API Guide "Change Login Password" section, this endpoint
        takes a **raw JSON body** ``{"newPassword": "..."}`` with
        ``Content-Type: application/json`` (POST), not form fields. The
        documented curl sample is::

            curl --location '<base>/api/2.0/fo/user/change_password/index.php' \\
              --header 'X-Requested-With: ...' \\
              --header 'Content-Type: application/json' \\
              --data '{"newPassword": "abcd123#"}'

        It is restricted to HTTP Basic authentication — a request made with a
        JWT bearer token is rejected with "Please use basic authentication, as
        this endpoint doesn't support JWT authentication." The self._fo()
        regime already uses Basic auth. The password can be changed at most 3
        times per hour; exceeding this returns a rate-limit error (code 1905).

        Args:
            new_password: The new login password for the calling user.

        Returns:
            Parsed SIMPLE_RETURN with "Password changed successfully", or a
            rate-limit/error message from Qualys.
        """
        body = json.dumps({"newPassword": new_password})
        return self._fo(
            "/api/2.0/fo/user/change_password/",
            method="POST",
            content=body,
            content_type="application/json",
        )

    def accept_eula(self) -> dict[str, Any]:
        """Accept the Qualys End User License Agreement for the calling account.

        Completes account registration (first-login) programmatically instead
        of via the Qualys UI. Any user with permission to log in to Qualys may
        accept the EULA. Must be called with HTTP Basic authentication (the
        self._fo() regime already uses Basic auth); once accepted, msp and
        VM/PC v2.0+ APIs also work with JWT.

        The endpoint takes no input parameters — it acts on the account whose
        credentials make the request.

        Returns:
            Parsed GENERIC_RETURN with a SUCCESS status (e.g. "TNC accepted
            within MSP"), or an error dict.
        """
        return self._fo("/msp/acceptEULA.php", method="POST")

    def admin_change_user_password(
        self,
        user_logins: str,
        email: bool | None = None,
    ) -> dict[str, Any]:
        """Reset the login password of one or more *other* users (admin batch reset).

        Distinct from :meth:`change_login_password` (which changes the calling
        user's own password to a chosen value): here the service
        **auto-generates** new strong passwords for the target accounts — no
        plaintext password is supplied or accepted by this tool. Passwords can
        be reset for accounts in "active", "inactive", or "pending activation"
        status (not deleted accounts, and not Contact users who have no login).

        Permissions: Managers can reset all users except themselves; Unit
        Managers all users in their business unit except themselves;
        Administrators all except Managers/Administrators/themselves. When a
        sub-user's password is reset, it can be reset at most 3 times per hour.
        Must be called with HTTP Basic authentication.

        Args:
            user_logins: One or more Qualys user login IDs (comma-separated),
                or the literal "all" to reset every user in the subscription
                except the requesting user.
            email: Whether affected users receive an email notification. True
                (default when omitted) emails each user a secure link to their
                new password; False suppresses the email and instead returns
                each user's login ID and new password as value pairs in the
                XML report (accounts in "pending activation" are auto-activated
                in that case).

        Returns:
            Parsed PASSWORD_CHANGE_OUTPUT listing the affected accounts and
            whether each password was changed, or an error dict.
        """
        data = {"user_logins": user_logins, "email": email}
        return self._fo("/msp/password_change.php", method="POST", data=data)
