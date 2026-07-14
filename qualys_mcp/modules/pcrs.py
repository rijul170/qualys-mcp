"""PCRS module (Gateway/JWT API) — Policy Compliance Reporting/Posture Streaming.

The Policy Compliance Reporting Service (PCRS, a.k.a. Posture Streaming API)
extracts policy posture in bulk over the Gateway with Bearer-JWT auth. It is
distinct from the classic FO Policy Compliance API (``/api/2.0/fo/compliance/``)
that another module already covers — PCRS is optimized for streaming large
posture datasets policy-by-policy.

Confirmed endpoints (Gateway host, Bearer-JWT):
* ``GET  /pcrs/1.0/posture/policy/list``  — list evaluated policies.
* ``GET  /pcrs/1.0/posture/hostids``      — resolve host IDs for a policy.
* ``POST /pcrs/1.0/posture/postureInfo``  — stream posture for a host set.
  (v2 exists: ``GET /pcrs/2.0/posture/policy/list`` adds policy tag info.)

Default rate limit: ~25 requests/subscription/60s per PCRS API.

Endpoints for a single policy's metadata and for controls are less firmly
documented in PCRS specifically (control detail traditionally comes from the
FO Compliance API), so those are flagged ``# TODO(verify)``.

Docs: https://blog.qualys.com/product-tech/2023/10/31/qualys-api-best-practices-policy-compliance-posture-streaming-pcrs-api
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class PcrsModule(BaseModule):
    """Read policy posture in bulk via the PCRS (Posture Streaming) Gateway API."""

    module_label = "pcrs"

    def register_tools(self, server: FastMCP) -> None:
        self._add_tool(server, self.list_pcrs_policies, "list_pcrs_policies", tier="read")
        self._add_tool(server, self.get_pcrs_policy, "get_pcrs_policy", tier="read")
        self._add_tool(server, self.resolve_pcrs_host_ids, "resolve_pcrs_host_ids", tier="read")
        self._add_tool(server, self.get_pcrs_posture, "get_pcrs_posture", tier="read")
        self._add_tool(server, self.list_pcrs_controls, "list_pcrs_controls", tier="read")
        self._add_tool(server, self.get_pcrs_control, "get_pcrs_control", tier="read")

    # ------------------------------ reads ------------------------------ #
    def list_pcrs_policies(
        self,
        last_evaluation_date: int | None = None,
        api_version: str = "1.0",
    ) -> dict[str, Any]:
        """List policies that have been evaluated (PCRS policy list).

        Args:
            last_evaluation_date: Epoch (seconds) lower bound — return policies
                evaluated on/after this time. Pass 0 for all evaluated policies.
                # TODO(verify): confirm the exact query-param name (assumed
                # ``lastEvaluationDate``) and whether it is epoch seconds or ms.
            api_version: "1.0" (default) or "2.0". v2.0 additionally returns
                policy tag information.

        Returns:
            Parsed gateway JSON with the evaluated-policy list.
        """
        params: dict[str, Any] = {}
        if last_evaluation_date is not None:
            params["lastEvaluationDate"] = last_evaluation_date  # TODO(verify) param name
        version = "2.0" if str(api_version).startswith("2") else "1.0"
        return self._gateway(
            f"/pcrs/{version}/posture/policy/list", method="GET", params=params
        )

    def get_pcrs_policy(self, policy_id: str, api_version: str = "1.0") -> dict[str, Any]:
        """Fetch metadata for a single policy via PCRS.

        Args:
            policy_id: The policy ID to fetch.
            api_version: "1.0" (default) or "2.0".

        Returns:
            Parsed gateway JSON with the policy metadata.
        """
        # TODO(verify): PCRS documents a policy *list* endpoint but not clearly
        # a get-single-policy endpoint. This assumes the list resource accepts
        # a ``policyId`` filter param; if unsupported, callers should use
        # list_pcrs_policies and filter client-side, or the FO Compliance API.
        version = "2.0" if str(api_version).startswith("2") else "1.0"
        params = {"policyId": policy_id}  # TODO(verify) param name/support
        return self._gateway(
            f"/pcrs/{version}/posture/policy/list", method="GET", params=params
        )

    def resolve_pcrs_host_ids(
        self,
        policy_id: str,
        last_evaluation_date: int | None = None,
    ) -> dict[str, Any]:
        """Resolve the host IDs scanned for a policy (step before posture fetch).

        Args:
            policy_id: The policy ID whose scanned host IDs to resolve.
            last_evaluation_date: Epoch (seconds) — only hosts scanned on/after
                this time. # TODO(verify) param name/units.

        Returns:
            Parsed gateway JSON with the list of host IDs for the policy.
        """
        params: dict[str, Any] = {"policyId": policy_id}  # TODO(verify) param name
        if last_evaluation_date is not None:
            params["lastEvaluationDate"] = last_evaluation_date  # TODO(verify) param name
        return self._gateway("/pcrs/1.0/posture/hostids", method="GET", params=params)

    def get_pcrs_posture(
        self,
        policy_id: str,
        host_ids: str,
        evaluation_date: int | None = None,
    ) -> dict[str, Any]:
        """Stream posture info for a policy and a set of host IDs.

        Workflow: call :meth:`list_pcrs_policies` -> :meth:`resolve_pcrs_host_ids`
        -> this method with the resolved host IDs.

        Args:
            policy_id: The policy ID to extract posture for.
            host_ids: Comma-separated host IDs (from :meth:`resolve_pcrs_host_ids`).
            evaluation_date: Optional epoch (seconds) evaluation-date bound.
                # TODO(verify) param name/units.

        Returns:
            Parsed gateway JSON with per-control/per-host posture records
            (PASSED/FAILED status, evidence).
        """
        # Confirmed path/method; body field names are the uncertain part.
        # TODO(verify): confirm request-body field names — the PCRS blog shows a
        # payload carrying the policy and host-id set; assumed ``policyId`` and
        # ``hostIds`` (list). Some versions expect ``hostIds`` as an array of
        # ints rather than a CSV string.
        host_id_list: list[Any] = [h.strip() for h in host_ids.split(",") if h.strip()]
        body: dict[str, Any] = {"policyId": policy_id, "hostIds": host_id_list}
        if evaluation_date is not None:
            body["evaluationDate"] = evaluation_date  # TODO(verify) field name
        return self._gateway("/pcrs/1.0/posture/postureInfo", method="POST", json=body)

    def list_pcrs_controls(
        self,
        policy_id: str,
        page_number: int = 0,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """List the controls defined in a policy.

        Args:
            policy_id: The policy ID whose controls to list.
            page_number: Zero-based page index.
            page_size: Records per page.

        Returns:
            Parsed gateway JSON with the policy's control records.
        """
        # TODO(verify): PCRS is posture-focused; a dedicated controls-listing
        # endpoint may not exist under /pcrs. Assumed
        # ``/pcrs/1.0/posture/controls`` with a policyId filter. If unavailable,
        # control definitions come from the FO Compliance API
        # (/api/2.0/fo/compliance/policy/ with action=list) handled elsewhere.
        params = {"policyId": policy_id, "pageNumber": page_number, "pageSize": page_size}
        return self._gateway("/pcrs/1.0/posture/controls", method="GET", params=params)

    def get_pcrs_control(self, control_id: str) -> dict[str, Any]:
        """Fetch metadata for a single compliance control by ID.

        Args:
            control_id: The control ID (CID) to fetch.

        Returns:
            Parsed gateway JSON with the control definition.
        """
        # TODO(verify): confirm a per-control PCRS endpoint exists. Assumed
        # ``/pcrs/1.0/posture/controls/{cid}``; control metadata is otherwise
        # served by the FO Compliance control APIs.
        return self._gateway(f"/pcrs/1.0/posture/controls/{control_id}", method="GET")
