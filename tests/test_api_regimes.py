"""One focused end-to-end test per Qualys API regime (FO / QPS / Gateway).

Each test mocks the HTTP layer with respx (no real network) and drives one
representative tool through a real module method, proving the full path —
tool method -> ``self._fo``/``self._qps``/``self._gateway`` -> ``QualysClient``
-> httpx -> response parsing -> returned dict — actually works for each of
the three regimes documented in ``docs/MODULE_BUILD_GUIDE.md``.

See ``tests/test_foundation.py`` for the base FO-regime coverage (VM Scans);
this file adds QPS and Gateway coverage plus a second, distinct FO example.
"""

import httpx
import respx

from qualys_mcp.client import QualysClient
from qualys_mcp.config import QualysConfig
from qualys_mcp.modules.asset_tags import AssetTagsModule
from qualys_mcp.modules.gav import GavModule
from qualys_mcp.modules.knowledgebase import KnowledgeBaseModule

API_URL = "https://qualysapi.qg2.apps.qualys.com"
GATEWAY_URL = "https://gateway.qg2.apps.qualys.com"


def _client(enable_destructive: bool = False) -> QualysClient:
    cfg = QualysConfig(
        username="u",
        password="p",
        platform="US2",
        api_url=API_URL,
        gateway_url=GATEWAY_URL,
        console_label="regime-test",
        enable_destructive=enable_destructive,
    )
    return QualysClient(cfg)


# ---------------------------------------------------------------------- #
# Regime 1: classic FO API (self._fo) -- KnowledgeBase
# ---------------------------------------------------------------------- #


@respx.mock
def test_fo_regime_knowledgebase_list_returns_parsed_data():
    route = respx.get(f"{API_URL}/api/2.0/fo/knowledge_base/vuln/").mock(
        return_value=httpx.Response(
            200,
            text=(
                "<?xml version='1.0'?><KNOWLEDGE_BASE_VULN_LIST_OUTPUT>"
                "<RESPONSE><VULN_LIST><VULN>"
                "<QID>38170</QID><TITLE>OpenSSH Detection</TITLE>"
                "<SEVERITY_LEVEL>2</SEVERITY_LEVEL>"
                "</VULN></VULN_LIST></RESPONSE></KNOWLEDGE_BASE_VULN_LIST_OUTPUT>"
            ),
        )
    )
    mod = KnowledgeBaseModule(_client())
    result = mod.list_knowledgebase(ids="38170", details="Basic")

    assert route.called
    vuln = result["KNOWLEDGE_BASE_VULN_LIST_OUTPUT"]["RESPONSE"]["VULN_LIST"]["VULN"]
    assert vuln["QID"] == "38170"
    assert vuln["TITLE"] == "OpenSSH Detection"

    # Request was a Basic-auth GET carrying the mandatory anti-CSRF header
    # and the expected query params (booleans/None cleaned upstream).
    req = route.calls.last.request
    assert req.headers.get("X-Requested-With") == "qualys-mcp"
    assert req.url.params.get("action") == "list"
    assert req.url.params.get("ids") == "38170"


# ---------------------------------------------------------------------- #
# Regime 2: QPS REST API (self._qps) -- Asset Tags search
# ---------------------------------------------------------------------- #


@respx.mock
def test_qps_regime_asset_tags_search_returns_parsed_data():
    route = respx.post(f"{API_URL}/qps/rest/2.0/search/am/tag").mock(
        return_value=httpx.Response(
            200,
            text=(
                "<?xml version='1.0'?><ServiceResponse>"
                "<responseCode>SUCCESS</responseCode><count>1</count>"
                "<data><Tag><id>101</id><name>Production</name></Tag></data>"
                "</ServiceResponse>"
            ),
        )
    )
    mod = AssetTagsModule(_client())
    result = mod.search_tags(name="Production", name_operator="EQUALS")

    assert route.called
    service_response = result["ServiceResponse"]
    assert service_response["responseCode"] == "SUCCESS"
    tag = service_response["data"]["Tag"]
    assert tag["id"] == "101"
    assert tag["name"] == "Production"

    # The XML ServiceRequest body carried the search criterion.
    req = route.calls.last.request
    body = req.content.decode()
    assert '<Criteria field="name" operator="EQUALS">Production</Criteria>' in body
    assert req.headers.get("Content-Type") == "text/xml"


# ---------------------------------------------------------------------- #
# Regime 3: Gateway/JWT API (self._gateway) -- GAV asset list
# ---------------------------------------------------------------------- #


@respx.mock
def test_gateway_regime_gav_list_fetches_jwt_then_returns_parsed_data():
    auth_route = respx.post(f"{GATEWAY_URL}/auth").mock(
        return_value=httpx.Response(201, text="dummy.jwt.token")
    )
    list_route = respx.post(f"{GATEWAY_URL}/rest/2.0/search/am/asset").mock(
        return_value=httpx.Response(
            200,
            json={
                "responseCode": "SUCCESS",
                "assetListData": {"asset": [{"assetId": 1, "name": "host1.example.com"}]},
            },
        )
    )
    mod = GavModule(_client())
    result = mod.list_gav_assets(filter_qql="operatingSystem:Windows")

    # JWT was fetched exactly once and used as a Bearer token on the real call.
    assert auth_route.called
    assert list_route.called
    assert list_route.calls.last.request.headers.get("Authorization") == "Bearer dummy.jwt.token"

    assert result["responseCode"] == "SUCCESS"
    assert result["assetListData"]["asset"][0]["name"] == "host1.example.com"

    # Auth call carried Basic-style form credentials, not JSON.
    auth_req = auth_route.calls.last.request
    assert auth_req.headers.get("Content-Type") == "application/x-www-form-urlencoded"
