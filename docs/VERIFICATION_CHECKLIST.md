# Qualys MCP — Go-Live Verification Checklist (Audit C1)

Audit date: 2026-07-13.

This is the single punch list of every place a builder agent flagged its own
uncertainty in-code, plus the modules that most need a live-console check
before this server is trusted for production use. Source: `grep -rn
"# TODO(verify)" qualys_mcp/` — **256 markers across 37 module files** (zero
hits outside `qualys_mcp/modules/`, i.e. `server.py`/`client.py`/`registry.py`/
`config.py`/`common/*` carry no unresolved uncertainty markers).

How to use this list: for each item, hit the endpoint against a real console
(sandbox subscription recommended — several of these are `write`/`destructive`
tier) and either delete the `# TODO(verify)` comment once confirmed correct,
or fix the field name/path/enum and re-verify.

## 1. Full punch list, grouped by module (file:line — comment text)

### `qualys_mcp/modules/asset_tags.py` (13)
- L12: Management API"). Uncertain specifics are flagged ``# TODO(verify)``.
- L22: confirm this is the complete/current ruleType enum for the tag rule type.
- L59: confirm default AND-combination semantics for the search criteria.
- L63: confirm the exact ``preferences`` element name for offset paging.
- L123: `"CLOUD_ASSET".` — confirm full enum for the asset-type filter.
- L125: confirm QPS field name for the parent reference.
- L129: confirm QPS preferences element name for offset paging.
- L142: `criteria.append(("parentTagId", "EQUALS", str(parent_tag_id)))` — field name unconfirmed.
- L174: static tag with no rule — confirm full enum.
- L178: `rule_type` is set — confirm syntax per ruleType.
- L181: confirm the exact XML element Qualys expects for the tag rule body.
- L198: `fields.append(f"<parentTagId>{int(parent_tag_id)}</parentTagId>")` — element name unconfirmed.
- L240: confirm child-tag cascade behavior (whether child tags are deleted with the parent).

### `qualys_mcp/modules/auth_records.py` (6)
- L327: VMware `ssl_verify` uses "all"/"skip"/"none" — confirm exact accepted values per record_type.
- L402: `update_auth_record`'s `ssl_verify` semantics per record_type — same caveat as create.
- L460: Kerberos/GSSAPI fields (use_kerberos, realm_discovery, user_realm, krb5_password, ...) abbreviated — not exposed as named params.
- L752: Oracle OS-dependent compliance-check parameters (win_ora_home_*, unix_ora_home_*, perform_windows_os_checks, TCPS wallet params) abbreviated.
- L1196: PostgreSQL vault-backed client_key/passphrase variants (client_key_type=vault, passphrase_type=vault + *_vault_type/*_vault_id) not exposed.
- L1547: `add_ips`/`remove_ips`/`network_id` were not explicitly confirmed for this record type's update action.

### `qualys_mcp/modules/certview.py` (6)
- L11: flagged ``# TODO(verify)`` (module-level caveat statement).
- L113: CertView v2 documents only the unified POST-search endpoint — GET-based search assumed.
- L136: confirm the instances endpoint path/body.
- L146: filter field name unconfirmed for certificate instances.
- L163: confirm the CA (certificate authority) endpoint path/method entirely — assumed.
- L185: confirm a dedicated count endpoint exists — assumed.

### `qualys_mcp/modules/cloud_agent.py` (18) — highest marker count, tied with `fim`
- L17: Every uncertain path/param is flagged (module-level caveat).
- L51: confirm preferences element name for offset paging.
- L106: confirm the exact search path/version for agent search.
- L117: `e.g. "VM", "PC", "FIM"` — field name/enum for module filter unconfirmed.
- L120: field name unconfirmed.
- L131: `criteria.append(("tagName", "EQUALS", tag_name))` — field name unconfirmed.
- L133: `criteria.append(("tagId", "EQUALS", str(tag_id)))` — field name unconfirmed.
- L135: `criteria.append(("activatedModule", "EQUALS", activated_module))` — field name unconfirmed.
- L137: `criteria.append(("lastCheckedIn", "GREATER", last_checked_in_after))` — field/operator unconfirmed.
- L139: confirm path — assumed dedicated Cloud Agent search resource.
- L145: confirm path/version — assumed to mirror the search resource.
- L167: confirm exact resource path/version — `ca/activationkey` assumed.
- L185: `criteria.append(("isEnabled", "EQUALS", "1" if is_enabled else "0"))` — field name unconfirmed.
- L199: confirm exact resource path/version — `ca/configurationprofile` assumed.
- L227: confirm exact path and request body shape for agent activation.
- L241: `<ActivationKey>` element name unconfirmed.
- L243: `<profileId>` element name unconfirmed.
- L253: confirm exact path — some Cloud Agent API versions may differ.

### `qualys_mcp/modules/cloudview_connectors.py` (6)
- L143: exact AWS connector create body field names unconfirmed.
- L197: Azure connector create body field names unconfirmed.
- L246: GCP connector create body shape unconfirmed.
- L297: update body typically must echo required fields — unconfirmed which.
- L331: the run (sync) endpoint path (`POST ...`) unconfirmed.
- L362: some releases expose delete as a bulk operation — unconfirmed for single delete.

### `qualys_mcp/modules/cloudview_posture.py` (3)
- L77: a dedicated single-control endpoint may not exist — assumed.
- L223: resource inventory path unconfirmed.
- L265: a dedicated policy/mandate list endpoint is not confirmed.

### `qualys_mcp/modules/cloudview_remediation.py` (5)
- L16: the public CloudView/TotalCloud API docs do not clearly document this endpoint (module-level caveat).
- L65: path guessed.
- L84: path guessed.
- L122: path and body are best-effort; path guessed.
- L159: path and method are best-effort; guessed.

### `qualys_mcp/modules/compliance_framework_reports.py` (1)
- L180: this endpoint returns a binary zip file — download handling unconfirmed end-to-end.

### `qualys_mcp/modules/cs_containers.py` (4)
- L7: Uncertain paths/params/bodies flagged (module-level caveat).
- L88: sub-resource path for container vulnerabilities — assumed.
- L102: sub-resource path for container software — assumed.
- L126: delete-by-id path/method — assumed.

### `qualys_mcp/modules/cs_images.py` (4)
- L8: paths/params/bodies flagged (module-level caveat).
- L63: `/csapi/v1.3/images` assumed as the standard list endpoint.
- L88: sub-resource path for image vulnerabilities — assumed.
- L127: delete-by-id path/method — assumed.

### `qualys_mcp/modules/cs_policies.py` (12)
- L7: Uncertain paths/params/bodies flagged (module-level caveat).
- L29: `_BASE = "/csapi/v1.3/centralizedPolicy"` — base path unconfirmed.
- L69: list path/method — assumed GET on centralizedPolicy.
- L82: get-by-id path — assumed GET `{base}/{policyId}`.
- L101: exact `policyType`/`type` field name and enum unconfirmed.
- L105: `"AUDIT"` — field name and enum values unconfirmed.
- L114: nested `rules`/`authorizationRules`/... shape unconfirmed.
- L120: `"policyType": policy_type` — field name unconfirmed.
- L126: `body["action"] = action` — field name unconfirmed.
- L145: new enforcement action enum unconfirmed.
- L158: `body["action"] = action` — field name unconfirmed (update path).
- L181: delete path/method — assumed.

### `qualys_mcp/modules/cs_registries.py` (9)
- L7: Uncertain paths/params/bodies flagged (module-level caveat).
- L97: exact accepted `registryType` enum values unconfirmed.
- L100: exact `credentialType` enum values unconfirmed and which fields apply.
- L108: exact JSON body shape — CS docs show a flat body with uncertain nesting.
- L119: `body["credential"] = {...}` — wrapper key name ("credential") unconfirmed.
- L147: `body["credential"] = {"userName": username, "password": password}` — shape unconfirmed.
- L148: update method/path — assumed PUT `/csapi/v1.3/registry/{registryId}`.
- L169: the confirmed registry-scan endpoint is uncertain.
- L202: delete path/method — assumed.

### `qualys_mcp/modules/cs_sensors.py` (3)
- L7: Uncertain paths/params/bodies flagged (module-level caveat).
- L76: get-by-id path — assumed GET `/csapi/v1.3/sensors/{sensorId}`.
- L99: delete-by-id path/method — assumed.

### `qualys_mcp/modules/csam.py` (8)
- L21: CSAM and GAV share the `/rest/2.0/.../am/asset` backend — cross-module assumption.
- L24: the GAV/CSAM v2 API documents search/count filters in an XML/JSON body — shape unconfirmed.
- L84: confirm the field-selection param name.
- L89: confirm JSON filter body key vs XML `<FilterRequest>` body.
- L143: confirm `/rest/2.0/am/asset/component[/{assetId}]` path.
- L162: CSAM surfaces assigned tags inline on the asset record — unconfirmed.
- L209: confirm QPS endpoint (`am/hostasset` vs `am/asset`) for tag add.
- L228: confirm QPS endpoint and that `<tags><remove><TagSimple>` shape is correct.

### `qualys_mcp/modules/easm.py` (14)
- L16: uncertain path/param/body flagged (module-level caveat).
- L58: confirm the request-body field name for the query.
- L63: confirm max page size.
- L66: confirm the source filter value/field used to scope EASM.
- L77: `body["filter"] = filter_ql` — body field name unconfirmed.
- L79: correct field/value to scope results to EASM source unconfirmed.
- L81: confirm CSAM gateway asset-search path and method.
- L93: confirm get-by-id path — assumed `/rest/2.0/get/am/asset/{id}`.
- L106: severity/risk-type/asset field name unconfirmed.
- L115: `body["filter"] = filter_ql` — field name unconfirmed.
- L116: confirm the EASM findings/risks endpoint path entirely.
- L131: confirm the discovery-trigger path/method/body — assumed.
- L150: confirm the accepted seed-type enum values.
- L155: confirm path and body field names for adding seeds.

### `qualys_mcp/modules/edr.py` (14)
- L10: bodies less firmly pinned down (module-level caveat).
- L53: confirm the request-body field name (assumed).
- L57: sort expression shape unconfirmed.
- L64: `body["filter"] = filter_query` — field name unconfirmed.
- L66: `body["sort"] = sort` — shape unconfirmed.
- L67: confirm EDR event-search path — assumed `/ioc/events/search`.
- L81: confirm get-by-id path — assumed `/ioc/events/{id}`.
- L94: whether asset listing takes a filter body or query params — unconfirmed.
- L104: confirm method (GET vs POST) and how filters/paging are passed.
- L108: `params["filter"] = filter_query` — param name unconfirmed.
- L135: confirm exact request body field names for the quarantine target.
- L160: confirm whether the API expects the OS PID or an internal process ID.
- L173: confirm the request body — assumed an `actionType` field.
- L176: `"actionType": "KILL_PROCESS"` — enum value unconfirmed.

### `qualys_mcp/modules/fim.py` (18) — highest marker count, tied with `cloud_agent`
- L10: (incident, list profiles/rules) flagged (module-level caveat).
- L55: confirm the request-body field name (assumed).
- L60: sort body shape unconfirmed.
- L67: `body["filter"] = filter_query` — field name unconfirmed.
- L69: `body["sort"] = sort` — field name/shape unconfirmed.
- L81: the FIM guide does not clearly document a get-by-id endpoint.
- L96: status/reviewer filter field name/syntax unconfirmed.
- L105: `body["filter"] = filter_query` — field name unconfirmed.
- L127: `body["filter"] = filter_query` — field name unconfirmed.
- L128: confirm profiles search path/version (assumed).
- L148: FIM rules are embedded in a profile's definition — no clear standalone endpoint.
- L166: QQL filter string field name unconfirmed.
- L175: `body["filter"] = filter_query` — field name unconfirmed.
- L193: body field name and whether an explicit event-id is required — unconfirmed.
- L197: `"PENDING", "APPROVED"` — enum unconfirmed.
- L202: confirm create-incident path/body — assumed.
- L225: `"REJECTED", etc.` — accepted enum values unconfirmed.
- L231: `body: dict[str, Any] = {"approvalStatus": approval_status}` — body shape unconfirmed.

### `qualys_mcp/modules/gav.py` (4)
- L19: GAV and CSAM share the same `/rest/2.0/.../am/asset` backend — cross-module assumption.
- L23: the GAV/CSAM v2 API documents its search/count filters in an XML/JSON body — shape unconfirmed.
- L59: confirm the JSON key for the QQL filter ("filter" vs alternatives).
- L127: confirm `/am/v2/sn/assets/host/{assetId}` path and response shape.

### `qualys_mcp/modules/host_asset_am.py` (15)
- L15: Uncertain specifics flagged (module-level caveat).
- L45: confirm default AND-combination semantics.
- L48: confirm the exact `preferences` element name for offset paging.
- L104: `criteria.append(("dnsHostName", "CONTAINS", dns_hostname))` — field name unconfirmed.
- L106: `criteria.append(("netbiosName", "CONTAINS", netbios_name))` — field name unconfirmed.
- L108: `criteria.append(("operatingSystem", "CONTAINS", os_pattern))` — field name unconfirmed.
- L110: `criteria.append(("tagName", "EQUALS", tag_name))` — field name unconfirmed (vs "tags.name").
- L112: `criteria.append(("tagId", "EQUALS", str(tag_id)))` — field name unconfirmed (vs "tags.id").
- L134: confirm AND semantics and exact QPS field names for asset search.
- L149: confirm preferences element name for offset paging.
- L213: confirm which asset types/modules populate `am/asset`.
- L219: field name/enum values unconfirmed.
- L232: `criteria.append(("type", "EQUALS", asset_type))` — field name unconfirmed.
- L234: `criteria.append(("tagName", "EQUALS", tag_name))` — field name unconfirmed.
- L236: `criteria.append(("tagId", "EQUALS", str(tag_id)))` — field name unconfirmed.

### `qualys_mcp/modules/option_profiles.py` (3)
- L7: See markers for gaps (module-level caveat).
- L188: option profiles support hundreds of additional fields not all exposed as named params on `create_option_profile`.
- L319: `update_option_profile` shares the same field-coverage caveat.

### `qualys_mcp/modules/patch_mgmt.py` (17)
- L24: flagged where uncertain (module-level caveat).
- L79: confirm sort syntax.
- L84: confirm `/pm/v3/patches` path (vs GET `/pm/v1/patches`) and body field names.
- L104: confirm single-patch GET path (`/pm/v3/patches/{uuid}` vs `/pm/v1/...`).
- L119: confirm `/pm/v3/patches/count` (vs GET `/pm/v1/patches/count`) and body fields.
- L185: confirm the catalog filter param/mechanism.
- L192: confirm `/pm/v1/patchcatalog/patches` path and whether GET+params or POST+body.
- L213: confirm the job filter param name.
- L218: confirm sort syntax.
- L265: `"Uninstall"` — confirm enum values.
- L273: `"WEEKLY", "MONTHLY"` — confirm enum + required companion fields.
- L280: confirm exact nested schema for deployment window.
- L285: confirm `/pm/v1/deploymentjob` create body field names.
- L338: confirm PATCH `/pm/v1/deploymentjob/update/{id}` body field names.
- L367: confirm status change is via PATCH update with `{"status": "Enabled"}`.
- L381: confirm status change is via PATCH update with `{"status": "Disabled"}`.
- L403: confirm DELETE `/pm/v1/deploymentjobs` body shape (list vs `{"jobIds": [...]}`).

### `qualys_mcp/modules/patches.py` (1)
- L55: confirm exact FO path/param names against a live console.

### `qualys_mcp/modules/pc_controls.py` (2)
- L91: the VM/PC User Guide's "Control Criticality" section doesn't document a direct FO get action — bridges to Gateway PCAS; confirm.
- L120: no subscription-wide/global control-criticality reset action confirmed.

### `qualys_mcp/modules/pc_policies.py` (2)
- L182: the API also accepts raw policy XML in place of the structured import — confirm equivalence.
- L325: this module reaches PCAS (`/pcas/v3/...`) via the Gateway for update/delete since FO has no such action — confirm PCAS behavior end-to-end.

### `qualys_mcp/modules/pc_posture.py` (1)
- L62: this module reaches PCRS (`/pcrs/...`) via the Gateway for streaming posture — confirm behavior end-to-end.

### `qualys_mcp/modules/pcas_policies.py` (1)
- L17: this module reaches PCAS via `self._gateway()` (JWT) — confirm base path/version against a live console.

### `qualys_mcp/modules/pcrs.py` (13)
- L19: flagged (module-level caveat vs the FO Compliance API).
- L55: confirm the exact query-param name (assumed).
- L65: `params["lastEvaluationDate"] = last_evaluation_date` — param name unconfirmed.
- L81: PCRS documents a policy list endpoint but not clearly enough — confirm.
- L86: `params = {"policyId": policy_id}` — param name/support unconfirmed.
- L101: param name/units for time window unconfirmed.
- L106: `params: dict[str, Any] = {"policyId": policy_id}` — param name unconfirmed.
- L108: `params["lastEvaluationDate"] = last_evaluation_date` — param name unconfirmed.
- L126: param name/units unconfirmed.
- L133: confirm request-body field names — the PCRS blog post shows a different shape.
- L140: `body["evaluationDate"] = evaluation_date` — field name unconfirmed.
- L159: PCRS is posture-focused; a dedicated controls-listing endpoint is unconfirmed.
- L176: confirm a per-control PCRS endpoint exists — assumed.

### `qualys_mcp/modules/remediation_tickets.py` (1)
- L419: the API guide only shows this endpoint invoked via a specific method/shape — confirm generalization.

### `qualys_mcp/modules/search_lists.py` (3)
- L7: See markers for gaps (module-level caveat).
- L246: the API supports many more criteria fields not all exposed as named params.
- L368: same field-coverage caveat applies to the dynamic-list update tool.

### `qualys_mcp/modules/users.py` (1) — HIGH PRIORITY, likely live bug
- L254: `change_login_password` posts form-encoded `data=` via `self._fo()`, but the Qualys VM/PC API Guide's "Change Login Password" (`/api/2.0/fo/user/change_password/`) shows the endpoint expects a **raw JSON body** (`Content-Type: application/json`, `{"newPassword": "..."}`). `self._fo()` only sends form-encoded `data=` for the FO regime — if Qualys rejects form-encoded data here, `client.py` needs an optional JSON-body path added (out of this module's scope; flagged for the orchestrator). **Test this against a live console before relying on it.**

### `qualys_mcp/modules/vaults.py` (1)
- L178: vault-type-specific fields not promoted to a named parameter (e.g. CA Access Control's `ca_url`/`ca_api_username`/`ca_ssl_verify`/`ca_web_username`/`ca_web_password`, Azure Key's `app_id`/`ak_secret_name`, ARCON PAM's `vault_service_type`/`ssl_verify`) — must be passed via `extra_params`.

### `qualys_mcp/modules/was_auth.py` (6)
- L7: uncertain nested fields flagged (module-level caveat).
- L63: preference element names follow the common QPS 3.0 convention — assumed, not confirmed for WAS auth records specifically.
- L153: confirm this is the literal value expected by the API.
- L163: exact element name/wrapper for the Selenium script unconfirmed.
- L171: the form-record sub-object nesting (formRecord/type/...) unconfirmed.
- L207: confirm `username`/`password` live directly on the record vs. nested.

### `qualys_mcp/modules/was_findings.py` (3)
- L7: flagged (module-level caveat).
- L61: preference element names follow the common QPS 3.0 convention — assumed.
- L218: the update-finding endpoint path and body shape are not confirmed.

### `qualys_mcp/modules/was_reports.py` (8)
- L7: flagged (module-level caveat).
- L62: preference element names follow the common QPS 3.0 convention — assumed.
- L97: exact enum values (e.g. "SUBMITTED", "RUNNING", ...) unconfirmed.
- L111: `self._criteria("status", "EQUALS", status)` — status enum unconfirmed.
- L125: this wrapper requests `accept="xml"` (the only text format assumed to be supported) — confirm.
- L173: confirmed body shape assumption for report creation.
- L178: nested shape assumed.
- L194: `WAS_SCAN_REPORT`/`WAS_COMPARISON_REPORT` config shape unconfirmed.

### `qualys_mcp/modules/was_scans.py` (5)
- L7: flagged (module-level caveat).
- L64: preference element names follow the common QPS 3.0 convention — assumed.
- L125: `self._criteria("launchedDate", "LESSER", launched_before)` — operator name unconfirmed.
- L153: the WAS API v3 has no separate lightweight "status" endpoint — best-effort via `get_was_scan`.
- L244: exact request body wrapper for scan launch assumed.

### `qualys_mcp/modules/was_schedules.py` (15) — 2nd-highest marker count
- L9: confirm against the live WAS API guide/XSD (module-level caveat).
- L67: preference element names follow the common QPS 3.0 convention — assumed.
- L95: resource path (`was/wasscanschedule`) and Criteria field names unconfirmed.
- L122: `/qps/rest/3.0/search/was/wasscanschedule` — resource path unconfirmed.
- L131: resource path (`was/wasscanschedule`) not directly confirmed for get-by-id.
- L141: `/qps/rest/3.0/get/was/wasscanschedule/{schedule_id}` — path unconfirmed.
- L161: this entire body shape is a best-effort inference.
- L195: `<wasScan>{scan_fields}</wasScan>` — wrapper element name unconfirmed.
- L196: `startDate` field name unconfirmed.
- L197: `occurrenceType` field name unconfirmed.
- L201: `/qps/rest/3.0/create/was/wasscanschedule` — resource path unconfirmed.
- L216: resource path and field names — see create_was_schedule caveat.
- L237: `/qps/rest/3.0/update/was/wasscanschedule/{schedule_id}` — path unconfirmed.
- L252: resource path not directly confirmed for the delete action.
- L266: `/qps/rest/3.0/delete/was/wasscanschedule/{schedule_id}` — path unconfirmed.

### `qualys_mcp/modules/was_webapps.py` (10)
- L7: flagged (module-level caveat).
- L65: preference element names (`limitResults`/`startFromOffset`) — assumed.
- L233: exact nested XML likely differs from assumption.
- L237: field name/nesting for attaching an auth record unconfirmed.
- L240: element name (`uris`) and list wrapper shape unconfirmed.
- L242: nested shape (`scannerAppliance.type` vs a scanner-id reference) unconfirmed.
- L253: `tags` field shape unconfirmed.
- L254: `authRecord` field shape unconfirmed.
- L255: `uris` field shape unconfirmed.
- L256: `scannerAppliance` field shape unconfirmed.

## 2. QPS/Gateway modules built from docs research, not the PDF (higher verification priority)

The classic FO modules were built directly against the bundled 1911-page
`qualys-api-vmpc-user-guide.pdf`. The 27 modules below talk to the QPS REST
API or the JWT Gateway host — **neither family is documented in that PDF**,
so every one of them was built from Qualys's online docs / third-party
references rather than an authoritative bundled spec. All 27 carry at least
one `# TODO(verify)` marker (see Section 1); none has zero. Ordered by marker
count (proxy for how much of the module is "best effort"):

| Module | Family | `# TODO(verify)` count | Risk characterization |
|---|---|---|---|
| `fim` | Gateway | 18 | Base search path, get-by-id, profiles/rules listing, and incident create/approve body shapes all unconfirmed. Verify every write tool before use. |
| `cloud_agent` | QPS | 18 | Search path/version, most filter field names, and the activation/config-profile resource paths are all assumed. |
| `patch_mgmt` | Gateway | 17 | `/pm/v1` vs `/pm/v3` path version ambiguous across almost every tool; deployment-job body fields and enable/disable semantics unconfirmed. |
| `was_schedules` | QPS | 15 | Resource path itself (`was/wasscanschedule`) is not directly confirmed for any of search/get/create/update/delete. |
| `host_asset_am` | QPS | 15 | Most search-criteria field names (dnsHostName, tagName, tagId, type, ...) unconfirmed; AND-combination semantics unconfirmed. |
| `easm` | Gateway | 14 | Findings/risks endpoint path "entirely" unconfirmed per the module's own note; discovery-trigger and seed-add bodies assumed. |
| `edr` | Gateway | 14 | Event-search/get-by-id paths assumed; quarantine/kill-process body field names and enum values unconfirmed. |
| `cs_policies` | Gateway | 12 | Base path, list/get/update/delete methods, and policyType/action field names all unconfirmed. |
| `pcrs` | Gateway | 13 | Policy-list endpoint, per-control endpoint, and most param names (policyId, lastEvaluationDate, evaluationDate) unconfirmed. |
| `asset_tags` | QPS | 13 | ruleType enum, parentTagId field name, and child-tag cascade-on-delete behavior unconfirmed. |
| `was_webapps` | QPS | 10 | Nested XML for auth-record attachment, URIs, tags, and scanner-appliance assignment all unconfirmed. |
| `cs_registries` | Gateway | 9 | registryType/credentialType enums, credential body wrapper key, and update/delete paths unconfirmed. |
| `was_reports` | QPS | 8 | Status enum, report-creation body shape, and WAS_SCAN_REPORT/WAS_COMPARISON_REPORT config shape unconfirmed. |
| `csam` | QPS + Gateway | 8 | Shares unresolved GAV backend ambiguity (filter body format, tag-add endpoint). |
| `was_auth` | QPS | 6 | Selenium-script wrapper element and form-record nesting unconfirmed. |
| `cloudview_connectors` | Gateway | 6 | AWS/Azure/GCP connector create body field names all unconfirmed; delete-as-bulk-operation uncertainty. |
| `certview` | Gateway | 6 | Instances endpoint, CA endpoint, and count endpoint existence all unconfirmed. |
| `was_scans` | QPS | 5 | Status endpoint doesn't exist per WAS v3 (best-effort substitute); launch body wrapper assumed. |
| `cloudview_remediation` | Gateway | 5 | Module's own note: "public CloudView/TotalCloud API docs do not clearly [document this]" — every path guessed. |
| `gav` | Gateway | 4 | Shares CSAM backend ambiguity; single-asset path/response shape unconfirmed. |
| `cs_images` | Gateway | 4 | Vulnerability/software sub-resource paths and delete method assumed. |
| `cs_containers` | Gateway | 4 | Same category of assumption as `cs_images`. |
| `was_findings` | QPS | 3 | Update-finding path/body shape not confirmed. |
| `cloudview_posture` | Gateway | 3 | Single-control and policy/mandate-list endpoints may not exist as assumed. |
| `cs_sensors` | Gateway | 3 | Get-by-id and delete paths assumed. |
| `pcas_policies` | Gateway | 1 | Base path/version for the whole module reached via `self._gateway()` — one caveat, but it's foundational. |
| `compliance_framework_reports` | Gateway | 1 | Binary zip download handling for the report file unconfirmed end-to-end. |

**Recommendation**: prioritize live-console smoke tests for `fim`,
`cloud_agent`, `patch_mgmt`, `was_schedules`, and `host_asset_am` first —
they have the most markers and the least-confirmed foundational paths
(base resource path itself is in question, not just a field name).

## 3. Top items to resolve before go-live (cross-referenced with `COVERAGE_MATRIX.md`)

1. **`users.change_login_password`** (users.py:254) — probable body-encoding
   mismatch (form vs. raw JSON) that will likely fail against a live console
   until `client.py` gets an optional JSON-body path for the FO regime.
2. **Scan-schedule run-history endpoint** (`/api/2.0/fo/scan/schedules/
   runhistory/?action=list`) is not implemented in `vmscans`,
   `compliancescans`, or `scanschedules` at all — confirm whether this is
   in-scope for a future module addition.
3. **`reporttemplates`** is deliberately read-only — confirm with
   stakeholders whether create/update/delete for Scan/PCI/Patch/Map
   templates should be added before go-live or is acceptably out of scope.
4. **`knowledgebase`**: `action=reset` / `action=custom` (Editing
   Vulnerabilities) and `action=list_vendors` (Vendor IDs) are documented
   but unimplemented — low-effort additions if needed.
5. **`users`**: "Accept Qualys EULA" and the admin batch "User Password
   Change" endpoints are undocumented gaps — confirm whether they're needed
   for this deployment's user-provisioning workflow.
6. **`restricted_ips.manage_restricted_ips`**: `clear`/`delete` operations
   are tiered `write`, not `destructive`, despite being able to fully open
   the subscription's API/UI access by removing all IP restrictions —
   consider re-tiering to `destructive` with a `confirm` guard.
7. Run the 5 modules in the Section 2 priority list (`fim`, `cloud_agent`,
   `patch_mgmt`, `was_schedules`, `host_asset_am`) through at least one
   real call per tool against a sandbox console — these are the modules
   most likely to have an outright-wrong path or body shape rather than
   just a missing optional field.
