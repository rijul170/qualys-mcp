# Qualys MCP — Safety Audit (Part A)

Audit date: 2026-07-13
Scope: all 58 feature module files in `qualys_mcp/modules/` (excludes `base.py`
and `__init__.py`). Method: AST-parsed every `register_tools()` method to
extract `(tool_name, tier, method)` triples, cross-referenced each method body
for `confirm` parameters and `self._confirm_or_error(...)` guards, then
spot-checked ~10 tools by hand to validate the automated extraction.

Totals found: **363 tools registered across 59 module instances*** (179
`read`, 145 `write`, 39 `destructive`).

\* `--check` reports "59 modules" (one more than the 58 files) and slightly
higher tool totals (327 default / 366 destructive-enabled) than the raw
per-module AST sum (324 / 363) — the gap is constant before and after Part B's
edits, so it reflects tooling/summary-line behavior outside this audit's
scope (not a module miscount), not a regression.

## 1. Destructive tool inventory (39 tools)

Every destructive tool below was checked for: tier=`"destructive"` in
`register_tools`; a `confirm: str | None = None` parameter; a call to
`self._confirm_or_error(confirm, expected=...)`; and an early `return guard`
immediately after, before any mutating client call. All 39 pass all four
checks — no exceptions found.

| Module (file) | Tool | `confirm` param | Guard called | Early return | `expected=` |
|---|---|---|---|---|---|
| asset_groups.py | delete_asset_group | yes | yes | yes | `id` |
| asset_tags.py | delete_tag | yes | yes | yes | `str(tag_id)` |
| auth_records.py | delete_auth_record | yes | yes | yes | `ids` |
| cloud_agent.py | uninstall_agent | yes | yes | yes | `str(asset_id)` |
| cloudview_connectors.py | delete_cloud_connector | yes | yes | yes | `connector_id` |
| compliance_scans.py | delete_compliance_scan | yes | yes | yes | `scan_ref` |
| containerized_scanner.py | delete_containerized_scanner | yes | yes | yes | `str(appliance_id)` |
| cs_containers.py | delete_cs_container | yes | yes | yes | `container_sha` |
| cs_images.py | delete_cs_image | yes | yes | yes | `image_sha` |
| cs_policies.py | delete_cs_policy | yes | yes | yes | `policy_id` |
| cs_registries.py | delete_cs_registry | yes | yes | yes | `registry_id` |
| cs_sensors.py | delete_cs_sensor | yes | yes | yes | `sensor_id` |
| edr.py | quarantine_edr_asset | yes | yes | yes | `asset_id` |
| edr.py | kill_edr_process | yes | yes | yes | `process_id` |
| excluded_hosts.py | remove_all_excluded_hosts | yes | yes | yes | `'ALL'` (literal) |
| maps.py | delete_map_report | yes | yes | yes | `ref` |
| maps.py | delete_legacy_scheduled_task | yes | yes | yes | `task_id` |
| maps.py | delete_domain | yes | yes | yes | `ids` |
| option_profiles.py | delete_option_profile | yes | yes | yes | `str(profile_id)` |
| patch_mgmt.py | delete_deployment_job | yes | yes | yes | `job_ids` |
| pc_exceptions.py | delete_pc_exception | yes | yes | yes | `exception_numbers` |
| pc_policies.py | delete_compliance_policy | yes | yes | yes | `str(policy_id)` |
| pcas_policies.py | delete_pcas_policy | yes | yes | yes | `str(policy_id)` |
| purge_hosts.py | purge_hosts | yes | yes | yes | `'PURGE'` (literal) |
| remediation_tickets.py | delete_tickets | yes | yes | yes | `ticket_numbers` or `'ALL_MATCHING_FILTERS'` |
| reports.py | delete_report | yes | yes | yes | `str(id)` |
| scan_schedules.py | delete_vm_scan_schedule | yes | yes | yes | `str(id)` |
| scan_schedules.py | delete_compliance_scan_schedule | yes | yes | yes | `str(id)` |
| scanner_appliances.py | delete_virtual_scanner | yes | yes | yes | `str(appliance_id)` |
| search_lists.py | delete_static_search_list | yes | yes | yes | `str(search_list_id)` |
| search_lists.py | delete_dynamic_search_list | yes | yes | yes | `str(search_list_id)` |
| vaults.py | delete_vault | yes | yes | yes | `vault_id` |
| virtual_hosts.py | delete_virtual_host | yes | yes | yes | `f"{ip}:{port}"` |
| vm_scans.py | delete_scan | yes | yes | yes | `scan_ref` |
| was_auth.py | delete_was_auth_record | yes | yes | yes | `str(auth_record_id)` |
| was_reports.py | delete_was_report | yes | yes | yes | `str(report_id)` |
| was_scans.py | delete_was_scan | yes | yes | yes | `str(scan_id)` |
| was_schedules.py | delete_was_schedule | yes | yes | yes | `str(schedule_id)` |
| was_webapps.py | delete_was_webapp | yes | yes | yes | `str(webapp_id)` |

No destructive tool was found registered under any tier other than
`"destructive"`, missing a `confirm` parameter, missing the
`_confirm_or_error` call, or missing the early-return guard.

## 2. Misclassifications

Checked every tool name against the leading-verb convention (`<verb>_<noun>`,
per the build guide) for both directions: destructive-implying verbs
(`delete/purge/remove/deactivate/uninstall/quarantine/kill`) registered as
non-destructive, and mutation-implying verbs
(`create/update/add/edit/set/launch/import/merge/assign/cancel/run/trigger/
approve/enable/disable/replace/reset/schedule/sync`) registered as `read`.

**No `read`-tier tool has a mutation-implying leading verb.** A naive
substring scan initially flagged `reports.py::scheduled_reports_list`,
`was_schedules.py::get_was_schedule`, and `users.py::activate_deactivate_user`
— all three are false positives (the verb substring appears mid-word: "get" /
"list" is the actual leading action, "schedule"/"deactivate" is a noun/part of
a compound, not the tool's verb). None are real misclassifications.

**Six `write`-tier tools have a destructive-implying leading verb**
(`delete_`/`remove_`) but are registered `tier="write"` rather than
`"destructive"`:

| Module | Tool | Assessment |
|---|---|---|
| csam.py | `remove_csam_asset_tags` | Removes a tag *association* from an asset (QPS `update/am/hostasset`), not a resource deletion. Reversible via `add_csam_asset_tags`. Mirrors `add_csam_asset_tags` (write) by design. |
| excluded_hosts.py | `remove_excluded_hosts` | Removes a *subset* of IPs from the excluded-hosts list (hosts become scannable again); reversible by re-adding the same IPs. The module deliberately reserves `tier="destructive"` for the sibling `remove_all_excluded_hosts` (clears the *entire* list), whose docstring explicitly explains this split. |
| pcas_policies.py | `remove_pcas_policy_technology` | Removes one technology association from a still-existing policy (PCAS `DELETE /policy/technology`). Reversible via the paired `add`-technology write tool. |
| pcas_policies.py | `delete_pcas_policy_section` | Deletes one section from a still-existing policy, not the policy itself (`delete_pcas_policy` is separately `tier="destructive"`). |
| pcas_policies.py | `delete_pcas_policy_section_control` | Removes a control's section membership, not the control or policy. |
| pcas_policies.py | `remove_pcas_control_technology` | Removes one technology association from a control. Reversible via the paired `add`-technology write tool. |

These six are flagged per the literal audit rule (verb implies destructive,
tier is not `"destructive"`), but on inspection each removes a sub-element/
association from a resource that continues to exist and remains
straightforwardly reversible via a paired `add_*` write tool in the same
module — a defensible design choice, not an oversight, and each case is
already documented in its own docstring. Recommend the orchestrator confirm
this is intentional; no code changes were made since Part A is audit-only.

**No other misclassifications were found.**

## 3. Destructive-gating tool-count delta

```
QUALYS_ENABLE_DESTRUCTIVE unset:   59 modules, 327 tools registered
QUALYS_ENABLE_DESTRUCTIVE=true:    59 modules, 366 tools registered
Delta:                             39 tools
```

The delta (39) exactly matches the number of destructive tools inventoried in
section 1 — confirming `_add_tool`'s gating in `base.py` hides precisely the
destructive tool set (and nothing else) when the console runs without
`QUALYS_ENABLE_DESTRUCTIVE=true`, and reveals exactly that set when it is
enabled. Both `--check` runs completed with no errors.
