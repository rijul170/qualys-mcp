"""Foundation tests: registry discovery, param cleaning, client regimes, gating.

These establish the test pattern for module tests (mock HTTP with respx; never
hit the real Qualys API). Run with pytest from the repo root.
"""

import httpx
import respx

from qualys_mcp import registry
from qualys_mcp.client import QualysClient
from qualys_mcp.common.utils import as_list, clean_params
from qualys_mcp.config import QualysConfig
from qualys_mcp.modules.vm_scans import VmScansModule


def _client(enable_destructive: bool = False) -> QualysClient:
    cfg = QualysConfig(
        username="u",
        password="p",
        platform="US2",
        api_url="https://qualysapi.qg2.apps.qualys.com",
        gateway_url="https://gateway.qg2.apps.qualys.com",
        console_label="test",
        enable_destructive=enable_destructive,
    )
    return QualysClient(cfg)


def test_registry_discovers_reference_modules():
    names = registry.get_module_names()
    assert "vmscans" in names
    assert "knowledgebase" in names


def test_clean_params_bools_lists_none():
    out = clean_params({"a": True, "b": False, "c": None, "d": [1, 2, 3], "e": "x"})
    assert out == {"a": "1", "b": "0", "d": "1,2,3", "e": "x"}


def test_as_list_normalizes_scalar_and_list():
    assert as_list(None) == []
    assert as_list("x") == ["x"]
    assert as_list([1, 2]) == [1, 2]


@respx.mock
def test_fo_get_parses_xml_and_sends_required_header():
    route = respx.get("https://qualysapi.qg2.apps.qualys.com/api/2.0/fo/scan/").mock(
        return_value=httpx.Response(
            200,
            text="<?xml version='1.0'?><SCAN_LIST_OUTPUT><RESPONSE><SCAN_LIST>"
            "<SCAN><REF>scan/1.1</REF></SCAN></SCAN_LIST></RESPONSE></SCAN_LIST_OUTPUT>",
        )
    )
    mod = VmScansModule(_client())
    result = mod.list_scans()
    assert "SCAN_LIST_OUTPUT" in result
    # Mandatory anti-CSRF header must be present on FO calls.
    assert route.calls.last.request.headers.get("X-Requested-With") == "qualys-mcp"


@respx.mock
def test_409_registration_incomplete_fails_fast():
    # Qualys code 2003 (registration not completed) is a 409 that must NOT be
    # retried — one call, immediate error, no 30s backoff storm.
    body = (
        "<?xml version='1.0'?><SIMPLE_RETURN><RESPONSE><CODE>2003</CODE>"
        "<TEXT>Registration must be completed before API requests will be processed.</TEXT>"
        "</RESPONSE></SIMPLE_RETURN>"
    )
    route = respx.get("https://qualysapi.qg2.apps.qualys.com/api/2.0/fo/asset/group/").mock(
        return_value=httpx.Response(409, text=body)
    )
    mod = VmScansModule(_client())  # any FO module; reuse client
    res = mod.client.fo("/api/2.0/fo/asset/group/", method="GET", params={"action": "list"})
    assert res["error"] and res["status_code"] == 409
    assert route.call_count == 1  # failed fast, no retries


def test_is_retryable_409_distinguishes_codes():
    c = _client()
    assert c._is_retryable_409(httpx.Response(409, text="<CODE>1965</CODE>")) is True
    assert c._is_retryable_409(httpx.Response(409, text="<CODE>2003</CODE>")) is False
    assert c._is_retryable_409(httpx.Response(409, text="no code here")) is False


def test_destructive_hidden_without_enable_flag():
    mod = VmScansModule(_client(enable_destructive=False))
    # Guard blocks even a direct call.
    res = mod.delete_scan("scan/1.1", confirm="scan/1.1")
    assert res["error"] and res["qualys_code"] == "DESTRUCTIVE_DISABLED"


def test_destructive_requires_matching_confirm():
    mod = VmScansModule(_client(enable_destructive=True))
    # Wrong/absent confirm -> refused.
    assert mod.delete_scan("scan/1.1", confirm=None)["qualys_code"] == "CONFIRMATION_REQUIRED"
    assert mod.delete_scan("scan/1.1", confirm="nope")["qualys_code"] == "CONFIRMATION_REQUIRED"


@respx.mock
def test_fo_raw_content_body_sets_content_type_and_skips_form():
    route = respx.post("https://qualysapi.qg2.apps.qualys.com/api/2.0/fo/subscription/option_profile/vm/").mock(
        return_value=httpx.Response(
            200,
            text="<?xml version='1.0'?><SIMPLE_RETURN><RESPONSE><CODE>0</CODE>"
            "<TEXT>imported</TEXT></RESPONSE></SIMPLE_RETURN>",
        )
    )
    client = _client()
    xml = "<OPTION_PROFILES><OPTION_PROFILE><BASIC_INFO/></OPTION_PROFILE></OPTION_PROFILES>"
    result = client.fo(
        "/api/2.0/fo/subscription/option_profile/vm/",
        method="POST",
        params={"action": "import"},
        content=xml,
        content_type="text/xml",
    )
    assert result["SIMPLE_RETURN"]["RESPONSE"]["TEXT"] == "imported"
    req = route.calls.last.request
    assert req.headers.get("Content-Type") == "text/xml"
    assert req.content.decode() == xml  # raw body, not form-encoded


@respx.mock
def test_destructive_proceeds_with_valid_confirm():
    respx.post("https://qualysapi.qg2.apps.qualys.com/api/2.0/fo/scan/").mock(
        return_value=httpx.Response(
            200,
            text="<?xml version='1.0'?><SIMPLE_RETURN><RESPONSE><CODE>0</CODE>"
            "<TEXT>scan deleted</TEXT></RESPONSE></SIMPLE_RETURN>",
        )
    )
    mod = VmScansModule(_client(enable_destructive=True))
    res = mod.delete_scan("scan/1.1", confirm="scan/1.1")
    assert res["SIMPLE_RETURN"]["RESPONSE"]["TEXT"] == "scan deleted"
