"""Container Security — Sensors module (Gateway/JWT API).

Container Security is a Gateway-family product: calls go to the gateway host
(JWT auto-fetched) under ``/csapi/v1.3/...`` with JSON bodies — no ``/qps/rest``
prefix and no XML. Not in the VM/PC PDF; endpoint shapes come from the public
CS API reference (https://docs.qualys.com/en/cs/api/ and CS API release notes).
Uncertain paths/params/bodies are flagged with ``# TODO(verify)``.

Note: the deployed CS *sensors* (agents) resource ``/csapi/v1.3/sensors`` is
distinct from *sensor profiles* (``/csapi/v1.3/sensorProfile``); this module
covers the deployed sensors.

Docs: Qualys Container Security API Guide — "Sensors".
"""

from typing import Any

from mcp.server import FastMCP

from qualys_mcp.modules.base import BaseModule


class CsSensorsModule(BaseModule):
    """List, inspect, and delete deployed Container Security sensors."""

    module_label = "cs_sensors"

    def register_tools(self, server: FastMCP) -> None:
        # Reads
        self._add_tool(server, self.list_cs_sensors, "list_cs_sensors", tier="read")
        self._add_tool(server, self.get_cs_sensor, "get_cs_sensor", tier="read")
        # Destructive
        self._add_tool(server, self.delete_cs_sensor, "delete_cs_sensor", tier="destructive")

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def list_cs_sensors(
        self,
        filter: str | None = None,
        page_number: int | None = None,
        page_size: int = 50,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """List deployed container security sensors.

        Args:
            filter: Qualys QQL-style filter string, e.g. "sensorType:GENERAL" or
                "status:UNKNOWN" (``filter`` query param).
            page_number: Zero-based page index (``pageNumber`` query param).
            page_size: Results per page (``pageSize`` query param; default 50).
            sort: Sort expression (``sort`` query param).

        Returns:
            Parsed JSON with a ``data`` array of sensor records (uuid, hostname,
            sensorType, status, version).
        """
        params = {
            "filter": filter,
            "pageNumber": page_number,
            "pageSize": page_size,
            "sort": sort,
        }
        # Confirmed: GET /csapi/v1.3/sensors (supports filter=sensorType:GENERAL etc).
        return self._gateway("/csapi/v1.3/sensors", method="GET", params=params)

    def get_cs_sensor(self, sensor_id: str) -> dict[str, Any]:
        """Fetch details of a single sensor.

        Args:
            sensor_id: The sensor UUID (``sensorId``).

        Returns:
            Parsed JSON sensor record.
        """
        # TODO(verify): get-by-id path — assumed GET /csapi/v1.3/sensors/{sensorId}.
        return self._gateway(f"/csapi/v1.3/sensors/{sensor_id}", method="GET")

    # ------------------------------------------------------------------ #
    # Destructive
    # ------------------------------------------------------------------ #
    def delete_cs_sensor(self, sensor_id: str, confirm: str | None = None) -> dict[str, Any]:
        """Permanently delete a sensor. IRREVERSIBLE.

        Gated: requires the console to be started with QUALYS_ENABLE_DESTRUCTIVE
        and the caller to pass confirm=<sensor_id>. Note: Qualys only permits
        deleting sensors whose status is UNKNOWN (i.e. no longer reporting).

        Args:
            sensor_id: The sensor UUID to delete.
            confirm: Must equal ``sensor_id`` to proceed.

        Returns:
            Parsed JSON status, or a confirmation/error dict.
        """
        guard = self._confirm_or_error(confirm, expected=sensor_id)
        if guard:
            return guard
        # TODO(verify): delete-by-id path/method — assumed
        # DELETE /csapi/v1.3/sensors/{sensorId}. Bulk delete is also supported via
        # ?sensorIds=a&sensorIds=b, not exposed here.
        return self._gateway(f"/csapi/v1.3/sensors/{sensor_id}", method="DELETE")
