"""Qualys API client covering all three API regimes behind one object.

Regimes
-------
* ``fo()``       — classic "FO" API (``/api/2.0/fo/`` and ``/msp/``). HTTP Basic
                   auth, mandatory ``X-Requested-With`` header, form-encoded
                   requests, XML responses (normalized to dict).
* ``qps()``      — QPS REST API (``/qps/rest/``). HTTP Basic auth. Accepts an
                   XML body, returns XML (normalized to dict) or JSON.
* ``gateway()``  — Gateway APIs (Container Security, TotalCloud, Patch, CSAM,
                   EASM, ...). Bearer-JWT auth fetched lazily from ``/auth`` and
                   cached until it 401s, then refreshed once.

All regimes share one :class:`httpx.Client`, one credential set, and a common
409 rate-limit/concurrency retry loop. Authentication is **lazy**: no network
call happens at construction time, so modules can be instantiated and tools
enumerated (``server --check``) with no credentials present.
"""

import re
import time
from typing import Any, Literal

import httpx

from qualys_mcp.common.errors import QualysAuthError, error_dict
from qualys_mcp.common.logging import get_logger
from qualys_mcp.common.rate_limit import RateLimitState
from qualys_mcp.common.utils import clean_params, truncate_for_log
from qualys_mcp.common.xml import parse_xml
from qualys_mcp.config import QualysConfig

logger = get_logger(__name__)

HttpMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]


class QualysClient:
    """Unified client for one Qualys console across all API families."""

    def __init__(self, config: QualysConfig):
        self.config = config
        self._http: httpx.Client | None = None
        self._jwt: str | None = None
        self._basic_verified = False
        self.last_rate_limit: RateLimitState | None = None

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    @property
    def http(self) -> httpx.Client:
        """Lazily create the shared httpx client."""
        if self._http is None:
            self._http = httpx.Client(
                timeout=self.config.timeout,
                verify=self.config.verify_tls,
                follow_redirects=True,
                headers={"User-Agent": self._user_agent()},
            )
        return self._http

    def close(self) -> None:
        if self._http is not None:
            self._http.close()
            self._http = None

    def _user_agent(self) -> str:
        from qualys_mcp import __version__

        return f"qualys-mcp/{__version__} ({self.config.console_label})"

    # ------------------------------------------------------------------ #
    # Connectivity / auth
    # ------------------------------------------------------------------ #
    def verify_connectivity(self) -> dict[str, Any]:
        """Live connectivity + auth check against the classic FO API.

        Uses the lightweight ``about.php`` endpoint which requires a valid
        session/credentials but touches no subscription data.
        """
        self.config.require_credentials()
        try:
            resp = self._request(
                "GET",
                f"{self.config.api_url}/msp/about.php",
                regime="fo",
            )
            connected = resp.status_code == 200
            self._basic_verified = connected
            return {
                "connected": connected,
                "status_code": resp.status_code,
                "console": self.config.console_label,
                "platform": self.config.platform,
                "api_url": self.config.api_url,
            }
        except Exception as exc:  # noqa: BLE001
            return error_dict(f"Connectivity check failed: {exc}", details={
                "console": self.config.console_label,
                "api_url": self.config.api_url,
            })

    def _ensure_jwt(self, force: bool = False) -> str:
        """Fetch (and cache) a Gateway JWT via ``POST {gateway}/auth``."""
        if self._jwt and not force:
            return self._jwt
        self.config.require_credentials()
        if not self.config.gateway_url:
            raise QualysAuthError(
                "No Gateway URL configured for this console; set QUALYS_GATEWAY_URL "
                "or a known QUALYS_PLATFORM to use Gateway modules (Container Security, "
                "TotalCloud, Patch, CSAM, EASM)."
            )
        url = f"{self.config.gateway_url}/auth"
        data = {
            "username": self.config.username,
            "password": self.config.password,
            "token": "true",
            "permissions": "true",
        }
        resp = self.http.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code != 201 and resp.status_code != 200:
            raise QualysAuthError(
                f"Gateway auth failed ({resp.status_code}): {truncate_for_log(resp.text, 200)}"
            )
        self._jwt = resp.text.strip()
        logger.debug("Obtained Gateway JWT for console %s", self.config.console_label)
        return self._jwt

    # ------------------------------------------------------------------ #
    # Public per-regime entry points
    # ------------------------------------------------------------------ #
    def fo(
        self,
        path: str,
        *,
        method: HttpMethod = "GET",
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        content: str | bytes | None = None,
        content_type: str | None = None,
        parse: bool = True,
    ) -> dict[str, Any]:
        """Call a classic FO endpoint.

        Args:
            path: Path beginning with ``/`` (e.g. ``/api/2.0/fo/scan/``).
            method: HTTP method. FO write actions use POST with an ``action`` param.
            params: Query parameters (cleaned; bools -> 1/0, lists -> csv).
            data: Form body parameters (for POST), same cleaning applied.
            content: Raw request body (str/bytes) for endpoints that require a
                verbatim XML/JSON payload rather than form fields — e.g. import
                option profiles / compliance policies, or JSON-body user actions.
                When set, ``data`` is ignored and ``content_type`` is sent.
            content_type: Content-Type header to use with ``content`` (defaults
                to ``text/xml`` when ``content`` is provided).
            parse: When True, parse the XML body to a dict; else return ``{"raw": text}``.

        Returns:
            Parsed response dict, or a standardized error dict.
        """
        self.config.require_credentials()
        url = f"{self.config.api_url}{path}"
        extra_headers: dict[str, str] = {}
        body_bytes: bytes | None = None
        if content is not None:
            body_bytes = content.encode("utf-8") if isinstance(content, str) else content
            extra_headers["Content-Type"] = content_type or "text/xml"
        resp = self._request(
            method,
            url,
            regime="fo",
            params=clean_params(params),
            data=None if body_bytes is not None else clean_params(data),
            content=body_bytes,
            extra_headers=extra_headers or None,
        )
        return self._finish_xml(resp, parse=parse)

    def qps(
        self,
        path: str,
        *,
        method: HttpMethod = "POST",
        body_xml: str | None = None,
        params: dict[str, Any] | None = None,
        accept: Literal["xml", "json"] = "xml",
    ) -> dict[str, Any]:
        """Call a QPS REST endpoint (``/qps/rest/...``).

        Args:
            path: Path beginning with ``/qps/rest/`` (e.g.
                ``/qps/rest/2.0/search/am/hostasset``).
            method: HTTP method.
            body_xml: Raw XML ``ServiceRequest`` body, if any.
            params: Query parameters.
            accept: Response format to request.

        Returns:
            Parsed response dict, or a standardized error dict.
        """
        self.config.require_credentials()
        url = f"{self.config.api_url}{path}"
        headers = {
            "Accept": "application/json" if accept == "json" else "application/xml",
        }
        if body_xml is not None:
            headers["Content-Type"] = "text/xml"
        resp = self._request(
            method,
            url,
            regime="qps",
            params=clean_params(params),
            content=body_xml.encode("utf-8") if body_xml else None,
            extra_headers=headers,
        )
        if accept == "json":
            return self._finish_json(resp)
        return self._finish_xml(resp, parse=True)

    def gateway(
        self,
        path: str,
        *,
        method: HttpMethod = "GET",
        params: dict[str, Any] | None = None,
        json: Any = None,
        content: str | bytes | None = None,
        content_type: str | None = None,
        accept: Literal["json", "xml"] = "json",
    ) -> dict[str, Any]:
        """Call a Gateway (JWT) endpoint.

        Handles a one-time transparent token refresh on 401.

        Args:
            path: Path beginning with ``/`` (e.g. ``/csapi/v1.3/images``).
            method: HTTP method.
            params: Query parameters.
            json: JSON request body, if any.
            content: Raw request body (str/bytes) for gateway endpoints that
                require XML — e.g. GAV/CSAM v2 ``<FilterRequest>`` search bodies.
                When set, ``json`` is ignored and ``content_type`` is sent.
            content_type: Content-Type for ``content`` (default ``text/xml``).
            accept: Response format to request/parse — "json" (default) or "xml"
                (parsed to dict via xmltodict, for GAV/CSAM-style XML responses).

        Returns:
            Parsed response dict, or a standardized error dict.
        """
        token = self._ensure_jwt()
        url = f"{self.config.gateway_url}{path}"
        body_bytes: bytes | None = None
        extra_headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/xml" if accept == "xml" else "application/json",
        }
        if content is not None:
            body_bytes = content.encode("utf-8") if isinstance(content, str) else content
            extra_headers["Content-Type"] = content_type or "text/xml"

        def _call(hdrs: dict[str, str]) -> httpx.Response:
            return self._request(
                method,
                url,
                regime="gateway",
                params=clean_params(params),
                json=None if body_bytes is not None else json,
                content=body_bytes,
                extra_headers=hdrs,
            )

        resp = _call(extra_headers)
        if resp.status_code == 401:
            # Token likely expired: refresh once and retry.
            logger.debug("Gateway 401; refreshing JWT and retrying once.")
            token = self._ensure_jwt(force=True)
            extra_headers["Authorization"] = f"Bearer {token}"
            resp = _call(extra_headers)

        if accept == "xml":
            return self._finish_xml(resp, parse=True)
        return self._finish_json(resp)

    # ------------------------------------------------------------------ #
    # Core request with rate-limit/concurrency retry
    # ------------------------------------------------------------------ #
    def _request(
        self,
        method: HttpMethod,
        url: str,
        *,
        regime: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        content: bytes | None = None,
        json: Any = None,
        extra_headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Issue one HTTP request, retrying HTTP 409 per Qualys backoff hints."""
        headers: dict[str, str] = {}
        auth: tuple[str, str] | None = None

        if regime in ("fo", "qps"):
            # Basic auth + mandatory anti-CSRF header for the classic/QPS APIs.
            auth = (self.config.username or "", self.config.password or "")
            headers["X-Requested-With"] = self.config.requested_with
        if extra_headers:
            headers.update(extra_headers)

        attempt = 0
        while True:
            attempt += 1
            resp = self.http.request(
                method,
                url,
                params=params or None,
                data=data or None,
                content=content,
                json=json,
                headers=headers,
                auth=auth,
            )
            self.last_rate_limit = RateLimitState.from_headers(resp.headers)

            if (
                resp.status_code == 409
                and attempt <= self.config.max_retries
                and self._is_retryable_409(resp)
            ):
                delay = self.last_rate_limit.backoff_seconds(attempt)
                logger.warning(
                    "Qualys 409 (rate/concurrency) on %s; backing off %.1fs "
                    "(attempt %d/%d).",
                    url,
                    delay,
                    attempt,
                    self.config.max_retries,
                )
                time.sleep(delay)
                continue
            return resp

    # Qualys FO 409 error codes that genuinely indicate rate/concurrency limits
    # (worth retrying with backoff). Everything else that returns 409 — most
    # importantly 2003 "Registration must be completed before API requests will
    # be processed" — is NOT retryable and must fail fast.
    _RETRYABLE_409_CODES = {"1959", "1960", "1965", "1966"}

    def _is_retryable_409(self, resp: httpx.Response) -> bool:
        """Return True only for genuine rate-limit / concurrency 409s."""
        rl = self.last_rate_limit
        # Explicit rate-limit signalling in headers -> definitely retryable.
        if rl and (rl.to_wait_sec or rl.concurrency_limit or rl.remaining is not None):
            return True
        # Otherwise inspect the SIMPLE_RETURN error code in the body.
        match = re.search(r"<CODE>(\d+)</CODE>", resp.text or "")
        if match:
            return match.group(1) in self._RETRYABLE_409_CODES
        # No rate-limit headers and no recognizable code: don't hammer.
        return False

    # ------------------------------------------------------------------ #
    # Response finishers
    # ------------------------------------------------------------------ #
    def _finish_xml(self, resp: httpx.Response, *, parse: bool) -> dict[str, Any]:
        if resp.status_code >= 400:
            parsed = parse_xml(resp.text)
            text = None
            sr = parsed.get("SIMPLE_RETURN", {})
            if sr:
                text = sr.get("RESPONSE", {}).get("TEXT")
            return error_dict(
                text or f"HTTP {resp.status_code}",
                status_code=resp.status_code,
                details=parsed or truncate_for_log(resp.text),
            )
        if not parse:
            return {"raw": resp.text}
        return parse_xml(resp.text)

    def _finish_json(self, resp: httpx.Response) -> dict[str, Any]:
        try:
            body = resp.json() if resp.content else {}
        except ValueError:
            body = {"raw": resp.text}
        if resp.status_code >= 400:
            message = None
            if isinstance(body, dict):
                message = (
                    body.get("message")
                    or (body.get("_error") or {}).get("message")
                    if isinstance(body.get("_error"), dict)
                    else body.get("message")
                )
            return error_dict(
                message or f"HTTP {resp.status_code}",
                status_code=resp.status_code,
                details=body,
            )
        return body if isinstance(body, dict) else {"data": body}
