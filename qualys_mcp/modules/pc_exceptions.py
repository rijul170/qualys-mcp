"""Policy Compliance — Exceptions module (classic FO API).

Covers listing, requesting, updating, and deleting compliance exceptions.
An exception temporarily changes a control's status on a host from Failed to
PassedE (passed with an exception) once approved.

Docs: Qualys VM/PC API User Guide — "Exceptions" (list/request/update/delete).
Endpoint: ``/api/2.0/fo/compliance/exception/``.
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class PcExceptionsModule(BaseModule):
    """List, request, update, and delete Policy Compliance (PC) exceptions."""

    module_label = "pc_exceptions"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_pc_exceptions, "list_pc_exceptions", tier="read")
        self._add_tool(server, self.request_pc_exception, "request_pc_exception", tier="write")
        self._add_tool(server, self.update_pc_exception, "update_pc_exception", tier="write")
        self._add_tool(server, self.delete_pc_exception, "delete_pc_exception", tier="destructive")

    def list_pc_exceptions(
        self,
        exception_number: int | None = None,
        exception_numbers: str | None = None,
        exception_number_min: int | None = None,
        exception_number_max: int | None = None,
        ip: str | None = None,
        network_name: str | None = None,
        status: str | None = None,
        control_id: int | None = None,
        control_statement: str | None = None,
        policy_id: int | None = None,
        technology_name: str | None = None,
        assignee_id: int | None = None,
        created_by: int | None = None,
        modified_by: int | None = None,
        details: str = "Basic",
        is_active: bool | None = None,
        created_after_date: str | None = None,
        updated_after_date: str | None = None,
        expired_before_date: str | None = None,
        expired_after_date: str | None = None,
        truncation_limit: int | None = None,
    ) -> dict[str, Any]:
        """List compliance exceptions in the account.

        By default all exceptions are listed; optional parameters filter the
        output.

        Args:
            exception_number: Show a single exception by number.
            exception_numbers: Comma-separated exception numbers and/or
                ranges (e.g. "289-292").
            exception_number_min: Only exceptions with number >= this value.
            exception_number_max: Only exceptions with number <= this value.
            ip: Restrict to exceptions on a specific host IP address.
            network_name: Restrict to exceptions on a specific network.
            status: "pending", "approved", "rejected", or "expired".
            control_id: Restrict to a control ID (prefix match — e.g. 23
                matches 23, 234, 2343, 233).
            control_statement: Restrict by control statement (partial text
                match allowed) for controls in a given policy.
            policy_id: Restrict to exceptions for controls in this policy.
            technology_name: Restrict to a control technology name.
            assignee_id: Restrict to exceptions assigned to this user ID.
            created_by: Restrict to exceptions created by this user ID.
            modified_by: Restrict to exceptions last modified by this user ID.
            details: "None" (numbers only), "Basic" (default; all details
                except comment history), or "All" (adds comment history).
            is_active: True for active exceptions only, False for inactive
                only. Both shown when unset.
            created_after_date: Only exceptions requested after this date
                (mm/dd/yyyy).
            updated_after_date: Only exceptions updated after this date
                (mm/dd/yyyy).
            expired_before_date: Only exceptions expiring before this date
                (mm/dd/yyyy).
            expired_after_date: Only exceptions expiring after this date
                (mm/dd/yyyy).
            truncation_limit: Max exceptions per page (default 1000).

        Returns:
            Parsed EXCEPTION_LIST_OUTPUT.
        """
        params = {
            "action": "list",
            "exception_number": exception_number,
            "exception_numbers": exception_numbers,
            "exception_number_min": exception_number_min,
            "exception_number_max": exception_number_max,
            "ip": ip,
            "network_name": network_name,
            "status": status,
            "control_id": control_id,
            "control_statement": control_statement,
            "policy_id": policy_id,
            "technology_name": technology_name,
            "assignee_id": assignee_id,
            "created_by": created_by,
            "modified_by": modified_by,
            "details": details,
            "is_active": is_active,
            "created_after_date": created_after_date,
            "updated_after_date": updated_after_date,
            "expired_before_date": expired_before_date,
            "expired_after_date": expired_after_date,
            "truncation_limit": truncation_limit,
        }
        return self._fo("/api/2.0/fo/compliance/exception/", method="GET", params=params)

    def request_pc_exception(
        self,
        control_id: int,
        policy_id: int,
        technology_id: int,
        assignee_id: int,
        comments: str,
        host_id: int | None = None,
        instance_string: str | None = None,
        reopen_on_evidence_change: bool | None = None,
        tag_set_by: str | None = None,
        tag_include_selector: str | None = None,
        tag_exclude_selector: str | None = None,
        tag_set_include: str | None = None,
        tag_set_exclude: str | None = None,
    ) -> dict[str, Any]:
        """Request a new compliance exception (created Pending, expiry = creation date).

        Either ``host_id`` or a tag set (``tag_set_include``/``tag_set_by``/
        selectors) must be provided to target one or more hosts.

        Args:
            control_id: Control ID to request an exception for.
            policy_id: Policy ID that contains the control.
            technology_id: Technology ID associated with the target host(s).
            assignee_id: User ID to assign the exception to (must have access
                to the affected hosts).
            comments: User-defined comments (required, saved in history).
            host_id: Host ID to request the exception for (required unless a
                tag set is provided instead).
            instance_string: Single instance on the host, e.g. "os" or
                "oracle10:1:1521:ora10204u". Required when the control is
                associated with an application-based instance technology
                (e.g. "MSSQL 2022:1:1433:MSSQLSERVER:master"). Must be
                combined with ``host_id``.
            reopen_on_evidence_change: For approved exceptions only — reopen
                the exception if a future scan shows a different failing
                value.
            tag_set_by: "id" (default) or "name" — how ``tag_set_include``/
                ``tag_set_exclude`` identify tags. Alternative to ``host_id``
                for targeting multiple hosts by tag.
            tag_include_selector: "any" (default) or "all".
            tag_exclude_selector: "any" (default) or "all".
            tag_set_include: Comma-separated tag IDs/names to include.
            tag_set_exclude: Comma-separated tag IDs/names to exclude.

        Returns:
            SIMPLE_RETURN with the new EXCEPTION_NUMBER(s), or an error dict.
        """
        data = {
            "action": "request",
            "control_id": control_id,
            "policy_id": policy_id,
            "technology_id": technology_id,
            "assignee_id": assignee_id,
            "comments": comments,
            "host_id": host_id,
            "instance_string": instance_string,
            "reopen_on_evidence_change": reopen_on_evidence_change,
            "tag_set_by": tag_set_by,
            "tag_include_selector": tag_include_selector,
            "tag_exclude_selector": tag_exclude_selector,
            "tag_set_include": tag_set_include,
            "tag_set_exclude": tag_set_exclude,
        }
        return self._fo("/api/2.0/fo/compliance/exception/", method="POST", data=data)

    def update_pc_exception(
        self,
        exception_numbers: str,
        comments: str,
        reassign_to: int | None = None,
        reopen_on_evidence_change: bool | None = None,
        status: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Update one or more compliance exceptions.

        All actions taken are logged in each exception's history with the
        caller's name and a timestamp.

        Args:
            exception_numbers: Comma-separated exception numbers and/or
                ranges (e.g. "50-55").
            comments: User-defined comments (required, saved in history).
            reassign_to: User ID to reassign the exception(s) to.
            reopen_on_evidence_change: For approved exceptions only — reopen
                if a future scan shows a different failing value.
            status: "Pending", "Approved", or "Rejected".
            end_date: New expiry date, format mm/dd/yyyy (only relevant to
                Approved exceptions). Use "0" for a never-ending exception.

        Returns:
            Parsed BATCH_RETURN, or an error dict.
        """
        data = {
            "action": "update",
            "exception_numbers": exception_numbers,
            "comments": comments,
            "reassign_to": reassign_to,
            "reopen_on_evidence_change": reopen_on_evidence_change,
            "status": status,
            "end_date": end_date,
        }
        return self._fo("/api/2.0/fo/compliance/exception/", method="POST", data=data)

    def delete_pc_exception(self, exception_numbers: str, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete one or more compliance exceptions. IRREVERSIBLE.

        Args:
            exception_numbers: Comma-separated exception numbers and/or
                ranges (e.g. "40-41").
            confirm: Must equal ``exception_numbers`` to proceed.

        Returns:
            Parsed BATCH_RETURN, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=exception_numbers)
        if guard:
            return guard
        data = {"action": "delete", "exception_numbers": exception_numbers}
        return self._fo("/api/2.0/fo/compliance/exception/", method="POST", data=data)
