# Qualys MCP — Coverage Matrix & Gap Analysis (Audit C1)

Audit date: 2026-07-13.
Scope: all 59 registered modules / 366 tools (363 module tools + 3 core
server tools: `qualys_check_connectivity`, `qualys_list_enabled_modules`,
`qualys_list_modules`).

## Method

1. **Enumerated the built surface** by instantiating every discovered module
   class (`qualys_mcp.registry.get_available_modules()`) against a stub
   `FastMCP` server that records every `_add_tool()` call, with
   `QUALYS_ENABLE_DESTRUCTIVE=true` so destructive tools are included. This is
   the authoritative source for the table below (not a hand transcription).
   Cross-checked against:
   ```
   QUALYS_ENABLE_DESTRUCTIVE=true .venv/Scripts/python.exe -m qualys_mcp --check
   ```
   which reports **59 modules, 366 tools** — matches (363 module tools + 3
   core tools registered directly in `server.py::_register_tools`).
2. **API family** per module was derived by counting `self._fo(` /
   `self._qps(` / `self._gateway(` call sites in each module's source file.
   A module is "mixed" when it calls more than one regime (e.g. `pc_policies`
   uses FO for policy CRUD but bridges to the Gateway PCAS API for
   update/delete, since FO has no such action — see notes).
3. **Classic FO / VM-PC cross-reference**: extracted the PDF's table of
   contents and the section text for every FO-backed module's documented
   page range from `qualys-api-vmpc-user-guide.pdf` (1911 pp, `pdftotext -f
   <a> -l <b>`), and diffed the documented `action=`/endpoint list against
   the tool's actual implementation. QPS/Gateway-only modules were **not**
   cross-referenced against this PDF (they aren't documented in it — see
   `VERIFICATION_CHECKLIST.md` for those instead).

## Coverage matrix

| Module (registry name) | API family | # tools | Tools | Coverage notes |
|---|---|---|---|---|
| `assetgroups` | FO | 4 | `qualys_list_asset_groups`, `qualys_add_asset_group`, `qualys_edit_asset_group`, `qualys_delete_asset_group` | Full match to "Asset Group List" / "Manage Asset Groups" (pp.1194-1201). |
| `assettags` | QPS | 5 | `qualys_search_tags`, `qualys_get_tag`, `qualys_create_tag`, `qualys_update_tag`, `qualys_delete_tag` | QPS Asset Management API — docs-research, not in the FO PDF. Heavy `# TODO(verify)` count (13). |
| `authrecords` | FO | 29 | `qualys_list_auth_records`, `qualys_list_auth_records_by_type`, `qualys_get_auth_record`, `qualys_user_permissions_summary`, `qualys_create_auth_record`, `qualys_update_auth_record`, `qualys_create_unix_auth`, `qualys_update_unix_auth`, `qualys_create_windows_auth`, `qualys_update_windows_auth`, `qualys_create_oracle_auth`, `qualys_update_oracle_auth`, `qualys_create_mssql_auth`, `qualys_update_mssql_auth`, `qualys_create_mysql_auth`, `qualys_update_mysql_auth`, `qualys_create_postgresql_auth`, `qualys_update_postgresql_auth`, `qualys_create_vmware_auth`, `qualys_update_vmware_auth`, `qualys_create_snmp_auth`, `qualys_update_snmp_auth`, `qualys_create_http_auth`, `qualys_update_http_auth`, `qualys_create_docker_auth`, `qualys_update_docker_auth`, `qualys_create_kubernetes_auth`, `qualys_update_kubernetes_auth`, `qualys_delete_auth_record` | **GAP.** Only 11 of ~38 documented record types (pp.605-879) get dedicated, fully-typed `create_<type>_auth`/`update_<type>_auth` tools; the other ~27 (Cassandra, DataStax, App Server, Azure MS SQL, Cisco APIC, DNS BIND, IBM DB2, InformixDB, Infoblox, JBoss, MariaDB, MarkLogic, MS SharePoint, MongoDB, MS Exchange, Neo4j, Nginx, Oracle Listener, Oracle WebLogic, Palo Alto Firewall, Pivotal Greenplum, SAP Hana, SAP IQ, Sybase, Network SSH, VMware NSX, Oracle HTTP Server, vCenter-ESXi Mapping) are reachable only through the generic `create_auth_record`/`update_auth_record` + `extra_params` escape hatch — technically complete but the model has to know each type's exact field names from the docs. |
| `certview` | Gateway | 5 | `qualys_search_certificates`, `qualys_get_certificate`, `qualys_list_certificate_instances`, `qualys_list_certificate_authorities`, `qualys_count_certificates` | CertView Gateway API — docs-research. |
| `cloudagent` | QPS | 6 | `qualys_list_agents`, `qualys_get_agent`, `qualys_list_activation_keys`, `qualys_list_config_profiles`, `qualys_activate_agent`, `qualys_uninstall_agent` | Cloud Agent QPS API — docs-research. |
| `cloudinternalscans` | FO | 3 | `qualys_list_cloud_internal_scans`, `qualys_create_cloud_internal_scan`, `qualys_update_cloud_internal_scan` | Matches "Create/Update Azure Internal Scan" + "…Azure and GCP Internal Scan" (pp.79-84); GCP is reached via the generic `cloud_provider` passthrough. |
| `cloudperimeterscans` | FO | 5 | `qualys_list_cloud_perimeter_scans`, `qualys_create_cloud_perimeter_scan`, `qualys_update_cloud_perimeter_scan`, `qualys_reset_cloud_perimeter_scan`, `qualys_launch_cloud_perimeter_scan` | Matches "Create/Update/Reset Cloud Perimeter Scan" (pp.72-78). `list`/`launch` are convenience wrappers over the VM Scan Schedule list/create endpoints — by design, not a gap. |
| `cloudviewconnectors` | Gateway | 8 | `qualys_list_cloud_connectors`, `qualys_get_cloud_connector`, `qualys_create_aws_connector`, `qualys_create_azure_connector`, `qualys_create_gcp_connector`, `qualys_update_cloud_connector`, `qualys_run_connector_sync`, `qualys_delete_cloud_connector` | TotalCloud/CloudView Gateway — docs-research. |
| `cloudviewposture` | Gateway | 7 | `qualys_list_cloudview_controls`, `qualys_get_cloudview_control`, `qualys_list_cloudview_evaluations`, `qualys_list_control_evaluation_resources`, `qualys_get_cloudview_evaluation_stats`, `qualys_list_cloudview_resources`, `qualys_list_cloudview_policies` | TotalCloud/CloudView Gateway — docs-research. |
| `cloudviewremediation` | Gateway | 4 | `qualys_list_remediation_activities`, `qualys_get_remediation_activity`, `qualys_trigger_remediation`, `qualys_set_remediation_rule` | TotalCloud/CloudView Gateway — docs-research; module docstring itself flags the public docs as unclear on this endpoint. |
| `complianceframeworkreports` | Gateway | 8 | `qualys_list_preferred_frameworks`, `qualys_list_framework_policies`, `qualys_list_framework_asset_groups`, `qualys_list_framework_asset_tags`, `qualys_list_framework_report_sources`, `qualys_create_framework_report`, `qualys_get_framework_report_status`, `qualys_download_framework_report` | Full 1:1 match to the 8 documented "Compliance Framework Reports" APIs (pp.1556-1563) even though the family is Gateway (`/pcrs/...` host) — PDF documents this endpoint explicitly. |
| `compliancescans` | FO | 7 | `qualys_list_compliance_scans`, `qualys_list_scap_scans`, `qualys_fetch_compliance_scan_results`, `qualys_launch_compliance_scan`, `qualys_launch_compliance_scan_on_ec2`, `qualys_manage_compliance_scan`, `qualys_delete_compliance_scan` | Matches List/SCAP List/Launch/Launch-EC2/Manage (pp.59-71). **Shares the run-history GAP** below with `vmscans`/`scanschedules`. |
| `containerizedscanner` | FO | 4 | `qualys_list_containerized_scanners`, `qualys_create_containerized_scanner`, `qualys_update_containerized_scanner`, `qualys_delete_containerized_scanner` | Full 1:1 match to Create/List/Update/Delete Containerized Scanner Appliance (pp.594-604). |
| `csam` | QPS + Gateway | 7 | `qualys_search_csam_assets`, `qualys_get_csam_asset`, `qualys_count_csam_assets`, `qualys_list_csam_software`, `qualys_list_csam_asset_tags`, `qualys_add_csam_asset_tags`, `qualys_remove_csam_asset_tags` | CSAM shares the GAV `/rest/2.0/.../am/asset` backend — docs-research, module explicitly flags the XML-vs-JSON filter-body ambiguity. |
| `cscontainers` | Gateway | 5 | `qualys_list_cs_containers`, `qualys_get_cs_container`, `qualys_get_cs_container_vulnerabilities`, `qualys_get_cs_container_software`, `qualys_delete_cs_container` | Container Security Gateway — docs-research; several sub-resource paths are `# TODO(verify)` guesses. |
| `csimages` | Gateway | 5 | `qualys_list_cs_images`, `qualys_get_cs_image`, `qualys_get_cs_image_vulnerabilities`, `qualys_get_cs_image_software`, `qualys_delete_cs_image` | Container Security Gateway — docs-research. |
| `cspolicies` | Gateway | 5 | `qualys_list_cs_policies`, `qualys_get_cs_policy`, `qualys_create_cs_policy`, `qualys_update_cs_policy`, `qualys_delete_cs_policy` | Container Security Gateway — docs-research; base path itself is `# TODO(verify)`. |
| `csregistries` | Gateway | 6 | `qualys_list_cs_registries`, `qualys_get_cs_registry`, `qualys_create_cs_registry`, `qualys_update_cs_registry`, `qualys_run_cs_registry_scan`, `qualys_delete_cs_registry` | Container Security Gateway — docs-research. |
| `cssensors` | Gateway | 3 | `qualys_list_cs_sensors`, `qualys_get_cs_sensor`, `qualys_delete_cs_sensor` | Container Security Gateway — docs-research. |
| `easm` | Gateway | 5 | `qualys_list_external_assets`, `qualys_get_external_asset`, `qualys_list_attack_surface_findings`, `qualys_trigger_easm_discovery`, `qualys_add_easm_seed` | EASM Gateway — docs-research, 14 `# TODO(verify)` markers (heaviest uncertainty alongside `fim`/`cloud_agent`). |
| `edr` | Gateway | 5 | `qualys_search_edr_events`, `qualys_get_edr_event`, `qualys_list_edr_assets`, `qualys_quarantine_edr_asset`, `qualys_kill_edr_process` | EDR Gateway — docs-research, 14 `# TODO(verify)` markers. |
| `excludedhosts` | FO | 5 | `qualys_list_excluded_hosts`, `qualys_list_excluded_hosts_history`, `qualys_add_excluded_hosts`, `qualys_remove_excluded_hosts`, `qualys_remove_all_excluded_hosts` | Full 1:1 match to Excluded Host List / Change History / Manage (pp.1175-1184). |
| `fim` | Gateway | 8 | `qualys_list_fim_events`, `qualys_get_fim_event`, `qualys_list_fim_incidents`, `qualys_list_fim_profiles`, `qualys_list_fim_rules`, `qualys_list_fim_ignored_events`, `qualys_create_fim_incident`, `qualys_approve_fim_incident` | FIM Gateway — docs-research, 18 `# TODO(verify)` markers (highest of any module, tied with `cloud_agent`). |
| `gav` | Gateway | 4 | `qualys_list_gav_assets`, `qualys_get_gav_asset`, `qualys_count_gav_assets`, `qualys_list_gav_host_instances` | GAV Gateway — docs-research, shares backend ambiguity with `csam`. |
| `hostassetam` | QPS | 5 | `qualys_search_host_assets`, `qualys_get_host_asset`, `qualys_count_host_assets`, `qualys_search_assets`, `qualys_get_asset` | Asset Management (AM) QPS API — docs-research, 15 `# TODO(verify)` markers. |
| `hostassets` | FO | 3 | `qualys_list_hosts`, `qualys_list_host_detections`, `qualys_update_hosts` | Full match to Host List / Host Update / Host List Detection (pp.925-1174). |
| `ipmanagement` | FO | 3 | `qualys_list_ips`, `qualys_add_ips`, `qualys_update_ips` | Full 1:1 match to IP List / Add IPs / Update IPs (pp.914-924). |
| `ipv6assets` | FO | 2 | `qualys_list_ipv6_mapping_records`, `qualys_add_ipv6_mapping_records` | Full match — the PDF documents only list + add for IPv6 mapping records (pp.1211-1218); no update/delete action exists. |
| `knowledgebase` | FO | 5 | `qualys_list_knowledgebase`, `qualys_get_qids`, `qualys_download_qvs_json`, `qualys_list_vendor_references`, `qualys_edit_vulnerability` | **GAP.** "Editing Vulnerabilities" (p.556) documents 3 actions — `action=edit`, `action=reset`, `action=custom` (list customized vulns) — only `edit` is implemented; the module's own docstring says "Use the classic FO `action=reset` (not exposed here)". "Vendor IDs and References" (p.591) documents `action=list_vendors` **and** `action=list_vendor_references`; only the latter is implemented. |
| `maps` | FO | 13 | `qualys_list_map_reports`, `qualys_list_running_maps`, `qualys_fetch_map_report`, `qualys_list_legacy_scheduled_tasks`, `qualys_list_domains`, `qualys_launch_map`, `qualys_cancel_map`, `qualys_create_legacy_scheduled_task`, `qualys_create_domain`, `qualys_update_domain`, `qualys_delete_map_report`, `qualys_delete_legacy_scheduled_task`, `qualys_delete_domain` | Full match to "Discovery Scans (maps)" (pp.173-197). |
| `networks` | FO | 4 | `qualys_list_networks`, `qualys_create_network`, `qualys_update_network`, `qualys_assign_scanner_appliance_to_network` | Full 1:1 match to Network List/Create/Update/Assign Scanner Appliance (pp.1219-1224). |
| `optionprofiles` | FO | 6 | `qualys_list_option_profiles`, `qualys_export_option_profiles`, `qualys_import_option_profiles`, `qualys_create_option_profile`, `qualys_update_option_profile`, `qualys_delete_option_profile` | Correctly bridges the generic export/import XML endpoint (`/subscription/option_profile/`) with the simpler typed VM/PCI/PC create/update/delete/list endpoints (`/subscription/option_profile/{vm,pci,pc}/`, pp.219-476). Hundreds of granular scan-option fields are intentionally not all promoted to named params (self-flagged `# TODO(verify)`; full control still available via export/import XML) — a documented design tradeoff, not an oversight. |
| `patches` | FO | 1 | `qualys_list_patches` | Full match — "Patch List" (p.1209) documents only a single read (`/api/2.0/fo/asset/patch/index.php`), no write/delete action exists. |
| `patchmgmt` | Gateway | 12 | `qualys_search_pm_patches`, `qualys_get_pm_patch`, `qualys_count_pm_patches`, `qualys_list_pm_assets`, `qualys_list_patch_catalog`, `qualys_list_deployment_jobs`, `qualys_get_deployment_job`, `qualys_create_deployment_job`, `qualys_update_deployment_job`, `qualys_enable_deployment_job`, `qualys_disable_deployment_job`, `qualys_delete_deployment_job` | Patch Management Gateway — docs-research, 17 `# TODO(verify)` markers (near-highest). |
| `pcaspolicies` | Gateway | 25 | `qualys_get_pcas_policy`, `qualys_update_pcas_policy`, `qualys_lock_pcas_policy`, `qualys_delete_pcas_policy`, `qualys_list_pcas_policy_technologies`, `qualys_add_pcas_policy_technologies`, `qualys_remove_pcas_policy_technology`, `qualys_get_pcas_policy_section`, `qualys_add_pcas_policy_section`, `qualys_update_pcas_policy_section`, `qualys_delete_pcas_policy_section`, `qualys_get_pcas_policy_section_control`, `qualys_add_pcas_policy_section_control`, `qualys_update_pcas_policy_section_control`, `qualys_delete_pcas_policy_section_control`, `qualys_list_pcas_control_technologies`, `qualys_add_pcas_control_technologies`, `qualys_remove_pcas_control_technology`, `qualys_get_pcas_control_technology_evaluation`, `qualys_update_pcas_control_technology_evaluation`, `qualys_list_pcas_library_labels`, `qualys_list_pcas_library_label_technologies`, `qualys_list_pcas_library_policies`, `qualys_get_pcas_library_policy`, `qualys_import_pcas_library_policy` | Gateway, but the PDF **does** document "PCAS Policies" as a PC sub-chapter (pp.1820-1862): Policy, Lock Policy, Policy Technology, Policy Section, Policy Section Control, …Control Technology, …Control Technology Evaluate, Library Label, Library Label Technology, Library Policy, Library Policy Details, Import Library Policy — this module maps 1:1 onto every one of those 12 documented sub-sections. No "Create Policy" action is documented (policies are created via the classic `pc_policies.import_compliance_policy`, not here), consistent with there being no `create_pcas_policy` tool. |
| `pccontrols` | FO + Gateway | 3 | `qualys_list_compliance_controls`, `qualys_get_control_criticality`, `qualys_set_control_criticality` | Matches Compliance Control List (p.1441) + Control Criticality (p.1792). Control Criticality is reached via the Gateway PCAS API since the classic FO API has no such action (module explicitly documents this bridge). |
| `pcexceptions` | FO | 4 | `qualys_list_pc_exceptions`, `qualys_request_pc_exception`, `qualys_update_pc_exception`, `qualys_delete_pc_exception` | Full 1:1 match to List/Request/Update/Delete exceptions (pp.1793-1811). |
| `pcpolicies` | FO + Gateway | 8 | `qualys_list_compliance_policies`, `qualys_export_compliance_policy`, `qualys_import_compliance_policy`, `qualys_merge_compliance_policy`, `qualys_manage_policy_asset_tags`, `qualys_manage_policy_asset_groups`, `qualys_update_compliance_policy`, `qualys_delete_compliance_policy` | Matches List/Export/Import/Merge/Manage-Tags/Manage-Groups (pp.1493-1554) — the FO "Compliance Policy" chapter documents **no** top-level update/delete action; this module correctly bridges `update_compliance_policy`/`delete_compliance_policy` to the Gateway PCAS Policy API instead of guessing an FO action that doesn't exist (self-documented in-code). Good design, not a gap — flagged in the verification checklist as higher-priority to test live since it crosses API families. |
| `pcposture` | FO + Gateway | 4 | `qualys_list_posture_policies`, `qualys_resolve_posture_host_ids`, `qualys_list_posture_info`, `qualys_stream_posture_info` | Matches Get Policy List / Resolve Host IDs / Get Posture Info / Streaming (pp.1564-1791). |
| `pcrs` | Gateway | 6 | `qualys_list_pcrs_policies`, `qualys_get_pcrs_policy`, `qualys_resolve_pcrs_host_ids`, `qualys_get_pcrs_posture`, `qualys_list_pcrs_controls`, `qualys_get_pcrs_control` | PCRS Gateway — docs-research, 13 `# TODO(verify)` markers; module notes the PCRS docs don't clearly confirm a policy-list or per-control endpoint. |
| `purgehosts` | FO | 1 | `qualys_purge_hosts` | Full match — "Purge Hosts" (p.1202) documents a single `action=purge` endpoint. |
| `remediationtickets` | FO | 6 | `qualys_view_ticket_list`, `qualys_get_ticket_info`, `qualys_view_deleted_tickets`, `qualys_edit_tickets`, `qualys_set_ignore_vulns`, `qualys_delete_tickets` | Full 1:1 match to all 6 documented ticket APIs (pp.1421-1439). |
| `reports` | FO | 9 | `qualys_list_reports`, `qualys_download_report`, `qualys_scheduled_reports_list`, `qualys_launch_report`, `qualys_launch_scorecard`, `qualys_cancel_report`, `qualys_launch_scheduled_report`, `qualys_asset_search_report`, `qualys_delete_report` | Full 1:1 match to Report List/Launch/Scorecard/Cancel/Download/Delete/Scheduled-List/Launch-Scheduled/Asset-Search (pp.1225-1306). |
| `reporttemplates` | FO | 5 | `qualys_list_report_templates`, `qualys_get_scan_template`, `qualys_get_pci_scan_template`, `qualys_get_patch_template`, `qualys_get_map_template` | **GAP — largest write/destructive gap in the classic API.** Read-only by explicit design (module docstring: "Creating/updating/deleting templates is out of scope … not requested"). The PDF documents full `action=create`/`update`/`delete`/`export` for **each** of Scan Template (p.1308), PCI Scan Template (p.1393), Patch Template (p.1395), and Map Template (p.1403) — up to 16 write/destructive endpoints with zero tool coverage. |
| `restrictedips` | FO | 2 | `qualys_list_restricted_ips`, `qualys_manage_restricted_ips` | Full match to List + Manage (activate/add/delete/replace/clear, pp.1189-1193). **Safety-tier note**: `manage_restricted_ips` is tiered `write`, but its `clear`/`delete` operations can fully disable the account's IP allow-list (a security-relevant, arguably-destructive change); it is available even when `QUALYS_ENABLE_DESTRUCTIVE=false` and needs no `confirm`. |
| `scannerappliances` | FO | 9 | `qualys_list_scanner_appliances`, `qualys_get_scanner_vlans_routes`, `qualys_create_virtual_scanner`, `qualys_update_virtual_scanner`, `qualys_update_physical_scanner`, `qualys_replace_scanner_appliance`, `qualys_set_scanner_vlans`, `qualys_set_scanner_routes`, `qualys_delete_virtual_scanner` | Full 1:1 match to List/Manage-Virtual/Update-Physical/Replace/VLANs&Routes (pp.199-218). No "delete physical appliance" action exists in the PDF either (hardware deactivation is out-of-band) — consistent with no such tool. |
| `scanschedules` | FO | 8 | `qualys_list_vm_scan_schedules`, `qualys_list_compliance_scan_schedules`, `qualys_create_vm_scan_schedule`, `qualys_update_vm_scan_schedule`, `qualys_create_compliance_scan_schedule`, `qualys_update_compliance_scan_schedule`, `qualys_delete_vm_scan_schedule`, `qualys_delete_compliance_scan_schedule` | Full match to VM/PC Scan Schedule List/Create/Update/Delete (pp.85-123). **Shares the run-history GAP** below. |
| `scap` | FO | 3 | `qualys_list_scap_policies`, `qualys_get_cyberscope_report`, `qualys_get_scap_arf_report` | Matches SCAP Policy List / Cyberscope Report / ARF Report (pp.1812-1819); the Cyberscope section documents 3 URL variants (scan/policy/global results) consolidated behind `get_cyberscope_report` — worth a live-console check that all 3 report types are reachable (see verification checklist). |
| `searchlists` | FO | 8 | `qualys_list_static_search_lists`, `qualys_list_dynamic_search_lists`, `qualys_create_static_search_list`, `qualys_update_static_search_list`, `qualys_create_dynamic_search_list`, `qualys_update_dynamic_search_list`, `qualys_delete_static_search_list`, `qualys_delete_dynamic_search_list` | Full 1:1 match to Static/Dynamic Search List CRUD (pp.559-590). |
| `users` | FO | 5 | `qualys_list_users`, `qualys_export_user_activity_log`, `qualys_add_or_edit_user`, `qualys_activate_deactivate_user`, `qualys_change_login_password` | **GAP.** "Accept Qualys EULA" (`/msp/acceptEULA.php`, p.1877 — programmatic first-login/registration completion) and admin-triggered batch "User Password Change" (`/msp/password_change.php`, p.1880 — resets passwords for *other* users, distinct from the self-service `change_login_password`) are both fully undocumented in the module and unimplemented. **Also a likely live bug**: `change_login_password` posts form-encoded `data=` to `/api/2.0/fo/user/change_password/`, but the PDF sample shows this endpoint requires a raw JSON body (`Content-Type: application/json`, `{"newPassword": "..."}`) — flagged by the module's own `# TODO(verify)` as needing a `client.py` change (raw JSON POST support for the FO regime) that's out of this module's scope. |
| `vaults` | FO | 5 | `qualys_list_vaults`, `qualys_get_vault`, `qualys_create_vault`, `qualys_update_vault`, `qualys_delete_vault` | Full 1:1 match to List/View/Create/Update/Delete Vaults (pp.899-911). |
| `virtualhosts` | FO | 3 | `qualys_list_virtual_hosts`, `qualys_manage_virtual_host`, `qualys_delete_virtual_host` | Full match — "Manage Virtual Hosts" documents 5 actions (create/update/delete/add_fqdn/delete_fqdn, pp.1185-1188), all reachable (4 via `manage_virtual_host`'s `operation` param + dedicated `delete_virtual_host`). |
| `vmscans` | FO | 12 | `qualys_list_scans`, `qualys_fetch_scan_results`, `qualys_vm_scan_statistics`, `qualys_vm_scan_summary`, `qualys_scan_summary`, `qualys_scanner_details`, `qualys_get_pci_share_status`, `qualys_launch_scan`, `qualys_launch_scan_on_ec2`, `qualys_manage_scan`, `qualys_share_pci_scan`, `qualys_delete_scan` | Matches List/Launch/Launch-EC2/Manage/Statistics/Summary/Scanner-Details/Share-PCI (pp.38-172). **GAP**: see "Scan schedule run-history" below. |
| `wasauth` | QPS | 5 | `qualys_search_was_auth_records`, `qualys_get_was_auth_record`, `qualys_create_was_auth_record`, `qualys_update_was_auth_record`, `qualys_delete_was_auth_record` | WAS QPS API — docs-research (not in this PDF; WAS has its own API guide). |
| `wasfindings` | QPS | 4 | `qualys_search_was_findings`, `qualys_get_was_finding`, `qualys_count_was_findings`, `qualys_update_was_finding` | WAS QPS API — docs-research; update-finding body shape flagged `# TODO(verify)`. |
| `wasreports` | QPS | 4 | `qualys_search_was_reports`, `qualys_download_was_report`, `qualys_create_was_report`, `qualys_delete_was_report` | WAS QPS API — docs-research, 8 `# TODO(verify)` markers on report-config body shape. |
| `wasscans` | QPS | 6 | `qualys_search_was_scans`, `qualys_get_was_scan`, `qualys_get_was_scan_status`, `qualys_launch_was_scan`, `qualys_cancel_was_scan`, `qualys_delete_was_scan` | WAS QPS API — docs-research; module notes there's no separate lightweight "status" endpoint in WAS v3 (best-effort). |
| `wasschedules` | QPS | 5 | `qualys_search_was_schedules`, `qualys_get_was_schedule`, `qualys_create_was_schedule`, `qualys_update_was_schedule`, `qualys_delete_was_schedule` | WAS QPS API — docs-research, 15 `# TODO(verify)` markers (2nd-highest of any module) — resource path itself (`was/wasscanschedule`) is unconfirmed. |
| `waswebapps` | QPS | 6 | `qualys_search_was_webapps`, `qualys_get_was_webapp`, `qualys_count_was_webapps`, `qualys_create_was_webapp`, `qualys_update_was_webapp`, `qualys_delete_was_webapp` | WAS QPS API — docs-research, 10 `# TODO(verify)` markers on nested XML shapes. |

## Concrete documented gaps (classic FO / VM-PC API)

Ranked roughly by materiality:

1. **Report Templates are read-only** (`reporttemplates` module). The PDF
   documents full `action=create` / `action=update` / `action=delete` /
   `action=export` for **Scan Template** (p.1308), **PCI Scan Template**
   (p.1393), **Patch Template** (p.1395), and **Map Template** (p.1403) — up
   to 16 endpoints. Only the read/export side (`get_scan_template`,
   `get_pci_scan_template`, `get_patch_template`, `get_map_template`,
   `list_report_templates`) is implemented; the module's own docstring
   states this was a deliberate scope cut, not an oversight.
2. **Scan-schedule run-history endpoint is completely missing.**
   `/api/2.0/fo/scan/schedules/runhistory/?action=list` ("List Last 'N' Scan
   References for a Schedule", documented identically for VM scans on p.48
   and for Compliance scans on p.61) is not implemented anywhere in
   `vmscans`, `compliancescans`, or `scanschedules` — grep for
   `runhistory`/`schedule_scan_ids`/`schedule_executions_count` across the
   whole codebase returns zero hits. This is the one explicitly called out
   as an example in the audit brief, and it is confirmed real.
3. **Auth records: only 11/~38 technology types have dedicated, fully-typed
   tools** (`authrecords` module) — see table row above. Not a hard gap
   (the generic `create_auth_record`/`update_auth_record` + `extra_params`
   cover every type per the FO API), but a real usability/verification gap
   since the model has to supply exact field names by hand for the other 27
   types.
4. **KnowledgeBase "Editing Vulnerabilities" is 1/3 complete**
   (`knowledgebase` module): `action=edit` is implemented; `action=reset`
   (revert a customized QID) and `action=custom` (list customized/edited
   vulnerabilities) are not, despite being documented on the same page
   (p.556) and explicitly acknowledged as missing in the module's own
   docstring.
5. **Vendor list action missing** (`knowledgebase` module): the "Vendor IDs
   and References" section (p.591) documents both `action=list_vendors`
   (list vendor IDs/names) and `action=list_vendor_references`; only the
   latter is exposed as `list_vendor_references`, with no way to call
   `list_vendors`.
6. **Users: two documented endpoints are entirely unimplemented**
   (`users` module) — "Accept Qualys EULA" (`/msp/acceptEULA.php`, p.1877)
   and the admin-triggered batch "User Password Change"
   (`/msp/password_change.php`, p.1880, resets *other* users' passwords —
   distinct from the self-service `change_login_password`).
7. **Likely live-breaking body-encoding bug**: `users.change_login_password`
   sends a form-encoded body to `/api/2.0/fo/user/change_password/`, but the
   documented endpoint (p.1874) requires a raw JSON body. Flagged by the
   module author as needing a `client.py`-level fix (raw JSON POST support
   for the FO regime), which is out of a single module's scope — see
   `VERIFICATION_CHECKLIST.md`.
8. **Restricted IPs safety-tier gap**: `manage_restricted_ips`'s
   `clear`/`delete` operations (which can fully open up API/UI access by
   disabling the subscription's IP allow-list) are tiered `write`, not
   `destructive` — no `confirm` needed and available even with
   `QUALYS_ENABLE_DESTRUCTIVE=false`.

No other classic FO/VM-PC section examined (Scans, Scan Schedules, Scan
Configuration/Option Profiles, Vault Support, Assets/IP/Host/Excluded/
Virtual/Restricted/Asset-Groups/Purge/Patch, IPv6, Networks, Remediation
Tickets, Compliance Control/Policy/Framework-Reports/Posture/Exceptions/SCAP/
PCAS) showed a missing documented action — those modules match their PDF
sections 1:1 (see per-row notes above for the specific page ranges checked).

## Coverage summary by API family

| Family | Modules | Tools | Notes |
|---|---|---|---|
| **FO** (classic `/api/2.0/fo/`, `/msp/`) | 25 pure + 4 mixed (`pccontrols`, `pcpolicies`, `pcposture`, `pcaspolicies` bridge to Gateway) | ~205 | Built directly against the 1911-page PDF. Coverage is very high (~1:1 on almost every section) with the concrete gaps enumerated above concentrated in `reporttemplates`, `authrecords`, `knowledgebase`, and `users`. |
| **QPS** (`/qps/rest/`) | 12 (`assettags`, `cloudagent`, `hostassetam`, `wasauth`, `wasfindings`, `wasreports`, `wasscans`, `wasschedules`, `waswebapps`, plus the QPS half of `csam`/`gav` where applicable) | ~57 | Built from online docs research, not the PDF (WAS/AM have their own API guides not included in this repo). Not independently verified against a live console or official WAS/AM XSD — see verification checklist; `wasschedules`/`hostassetam`/`assettags` carry the heaviest uncertainty. |
| **Gateway** (JWT `gateway.<pod>...`) | 18 pure (`certview`, `cloudviewconnectors`, `cloudviewposture`, `cloudviewremediation`, `complianceframeworkreports`, `cscontainers`, `csimages`, `cspolicies`, `csregistries`, `cssensors`, `easm`, `edr`, `fim`, `gav`, `patchmgmt`, `pcaspolicies`, `pcrs`, plus the Gateway half of `csam`) | ~104 | Highest-uncertainty family: `fim` and `cloud_agent` (QPS) each carry 18 `# TODO(verify)` markers, `patch_mgmt` 17, `was_schedules` 15, `host_asset_am` 15, `edr`/`easm` 14 each. Container Security (`cs_*`), EDR, FIM, EASM, PCRS, and Patch Management modules all have unconfirmed base paths, body shapes, or field names — treat as "best effort against public docs" until checked against a live console (see `VERIFICATION_CHECKLIST.md`). |
| **Core** (server-level) | — | 3 | `qualys_check_connectivity`, `qualys_list_enabled_modules`, `qualys_list_modules` — registered directly in `server.py`, outside any module. |

**Overall**: the classic FO/VM-PC surface (the only family checkable against
an authoritative 1911-page spec) is comprehensively covered — 8 concrete,
specific gaps found across 32 FO-touching modules, all documented above with
PDF page citations. The QPS and Gateway surface (27 modules, ~161 tools,
44% of the total tool count) was necessarily built from online documentation
rather than a bundled spec and should be treated as the higher-risk area for
go-live verification; see `VERIFICATION_CHECKLIST.md` for the itemized
punch list.
