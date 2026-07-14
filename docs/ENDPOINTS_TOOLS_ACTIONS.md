# Qualys MCP — Endpoints, Tools & Actions Reference

Authoritative, generated reference mapping every MCP tool exposed by this
server to its underlying Qualys API endpoint, HTTP method, action/verb, and
safety tier. Builds on `MODULE_BUILD_GUIDE.md` (the module contract),
`MODULE_INDEX.md` (the module inventory), and `COVERAGE_MATRIX.md` (the
gap analysis against the vendor API docs) — see those for narrative detail
this file doesn't repeat.

**Method**: Section C was produced by (1) instantiating every module from
`qualys_mcp.registry.get_available_modules()` against a stub server that
records every `_add_tool()` call (tool name, tier, bound method) with
`QUALYS_ENABLE_DESTRUCTIVE=true`, matching the `--check` output used
elsewhere in this repo; then (2) statically parsing (Python `ast`, no
imports executed, no network) every tool method's source to recover the
`self._fo()` / `self._qps()` / `self._gateway()` call site(s) — HTTP method,
endpoint path/template, and the literal or dispatched `action` value(s).
Endpoints built from an f-string or a small dict/ternary of alternatives are
rendered as `{a|b|c}` templates. No live API calls were made in producing
this document.

## Deployment model & safety gating (read this first)

- **Two-console deployment.** One `qualys_mcp` process serves exactly one
  Qualys console/subscription (`QualysConfig` in `config.py`); a second
  console runs as a second process on a second port, mirroring the
  Falcon us2/eu1 pattern. Each console independently decides whether
  destructive tools are exposed.
- **Destructive gating is two-layered.** (1) `BaseModule._add_tool()`
  (`qualys_mcp/modules/base.py`) skips registering any `tier="destructive"`
  tool entirely unless the process was started with
  `QUALYS_ENABLE_DESTRUCTIVE=true` — the tool simply does not exist on the
  MCP tool list otherwise. (2) Even when enabled, every destructive tool's
  body calls `self._confirm_or_error(confirm, expected=<target_id>)` first,
  which refuses to proceed unless the caller echoes back the exact target
  id/name in a `confirm=` argument — a second explicit-intent check beyond
  the tool merely being callable. This reference was generated **with
  destructive tools enabled** so it documents the full 366-tool surface;
  a console running with the default `QUALYS_ENABLE_DESTRUCTIVE=false`
  exposes only the 327 read/write tools (see `MODULE_INDEX.md`).

## A. Capabilities overview

The server wraps three distinct Qualys API regimes (classic FO, QPS REST,
and JWT-authenticated Gateway APIs — see the Legend for auth differences)
behind one consistent tool contract, spanning essentially every major
Qualys module. Counts below are **tool counts** (read / write / destructive)
with destructive tools enabled, grouped by functional domain rather than by
API family; a domain's modules may span more than one API family.

**Vulnerability scanning & VMDR** (15 modules — `vmscans`, `scanschedules`,
`hostassets`, `ipmanagement`, `ipv6assets`, `knowledgebase`, `assetgroups`,
`excludedhosts`, `virtualhosts`, `networks`, `purgehosts`, `maps`,
`cloudinternalscans`, `cloudperimeterscans`, `searchlists` — read 31 / write
36 / destructive 12, 79 tools). The core VMDR surface: launch/monitor/manage
on-demand and EC2 vulnerability scans, create recurring VM scan schedules,
manage the host/IP/asset-group/network inventory (including IPv6 mapping
and excluded/virtual hosts), run network discovery maps, query the QID
KnowledgeBase, build QID search lists to target scans and reports, and
purge stale host assessment data. Cloud-provider-triggered internal/
perimeter scan jobs (Azure/GCP/AWS-adjacent) are included here as VMDR
scan-launch variants.

**Policy Compliance** (9 modules — `compliancescans`, `scap`, `pcpolicies`,
`pcexceptions`, `pccontrols`, `pcposture`, `pcrs`, `pcaspolicies`,
`complianceframeworkreports` — read 38 / write 26 / destructive 4, 68
tools). Launch and manage PC/SCAP compliance scans; author, import/export,
merge, lock, and delete compliance policies and their sections/controls
(via both the classic FO policy API and the newer Gateway PCAS policy-authoring
API — the two bridge together since FO has no update/delete action for
policies); manage compliance exceptions and per-control criticality; pull
posture/evaluation results in bulk via PCRS/streaming; and generate
mandate/framework-based compliance reports (CIS, PCI, NIST, etc.).

**Web App Scanning (WAS)** (6 modules — `wasauth`, `wasfindings`,
`wasreports`, `wasscans`, `wasschedules`, `waswebapps` — read 15 / write 10
/ destructive 5, 30 tools). Full lifecycle for web application security
testing over the QPS WAS API: register/search/update/delete Web Application
assets, manage their authentication records and recurring scan schedules,
launch/monitor/cancel scans, and search/update WAS findings (vulns,
sensitive content, information gathered) plus generate and download reports.

**Cloud Agent & Asset Management/Tagging** (3 modules — `cloudagent`,
`assettags`, `hostassetam` — read 11 / write 3 / destructive 2, 16 tools).
List and manage Qualys Cloud Agents (activation keys, configuration
profiles, agent activation/uninstall), and search/tag the QPS Asset
Management (AM) inventory — host assets, generic assets, and the tags
assigned to them.

**Container Security** (5 modules — `cscontainers`, `csimages`,
`cspolicies`, `csregistries`, `cssensors` — read 14 / write 5 / destructive
5, 24 tools). Inventory and inspect running containers and container
images (including their vulnerabilities and installed software), configure
and scan container registries, manage centralized container security
policies, and list/remove deployed sensors.

**Cloud Security / TotalCloud (CloudView)** (3 modules —
`cloudviewconnectors`, `cloudviewposture`, `cloudviewremediation` — read 11
/ write 7 / destructive 1, 19 tools). Configure AWS/Azure/GCP cloud
connectors and trigger their inventory sync; query cloud security posture
(controls, policy evaluations, evaluated resources, per-account/per-control
stats); and list, trigger, and configure remediation for posture findings.

**Patch Management** (2 modules — `patchmgmt`, `patches` — read 8 / write 4
/ destructive 1, 13 tools). Search the Gateway Patch Management catalog and
patch inventory by QQL, inspect PM-managed assets, and create/update/
enable/disable/delete patch deployment jobs; plus the classic FO read-only
"patches applicable to a host" list.

**CSAM / GAV (asset inventory)** (2 modules — `csam`, `gav` — read 9 /
write 2 / destructive 0, 11 tools). Read-only Global AssetView (GAV) asset
inventory search/count/detail, plus CSAM's richer asset search/software
inventory and the ability to add/remove user-defined tags on a CSAM asset
(the tag-write path bridges through the QPS AM `hostasset` update endpoint,
since CSAM/GAV itself is read-only).

**EASM (External Attack Surface Management)** (1 module — `easm` — read 3 /
write 2 / destructive 0, 5 tools). Search external (internet-facing)
assets and attack-surface findings, and drive discovery by triggering a
profile scan or adding a new discovery seed.

**CertView** (1 module — `certview` — read 5 / write 0 / destructive 0, 5
tools). Fully read-only: search/count the certificate inventory and list
certificate instances (deployments) and certificate authorities.

**FIM (File Integrity Monitoring)** (1 module — `fim` — read 6 / write 2 /
destructive 0, 8 tools). Search FIM events and incidents, list monitoring
profiles/rules/ignored events, and create or approve a FIM incident.

**EDR (Endpoint Detection & Response)** (1 module — `edr` — read 3 / write
0 / destructive 2, 5 tools). Search EDR events and list monitored assets;
quarantine an asset or kill a malicious process are the two response
actions, both tiered destructive since they take an irreversible action on
a live endpoint.

**Users & administration** (2 modules — `users`, `restrictedips` — read 3 /
write 4 / destructive 0, 7 tools). Manage subscription user accounts
(add/edit, activate/deactivate, export activity log, self-service password
change) and the subscription's restricted (allow-listed) source-IP list for
API/UI access.

**Scanner appliances & option profiles** (3 modules — `scannerappliances`,
`optionprofiles`, `containerizedscanner` — read 5 / write 11 / destructive
3, 19 tools). List and manage virtual and physical scanner appliances
(VLANs, routes, replacement), containerized (QCS) scanner appliances, and
VM/PCI/PC option profiles (list/export/import/create/update/delete).

**Reporting & remediation** (3 modules — `reports`, `reporttemplates`,
`remediationtickets` — read 11 / write 7 / destructive 2, 20 tools). Launch,
monitor, download, cancel, and delete VM/PCI/scorecard/scheduled reports;
list and export report templates (read-only by design — see
`COVERAGE_MATRIX.md` gap #1); and view/edit/delete VM remediation tickets
plus ignore/restore vulnerabilities on hosts.

**Auth records & vaults** (2 modules — `authrecords`, `vaults` — read 6 /
write 26 / destructive 2, 34 tools). Create/update scan authentication
records for ~11 dedicated technology types (Unix, Windows, Oracle, MS SQL,
MySQL, PostgreSQL, VMware, SNMP, HTTP, Docker, Kubernetes) plus a generic
create/update/list/delete path covering every other documented type via
`extra_params`; and list/create/update/delete third-party credential vault
definitions referenced by those auth records.

## B. Summary matrix — API family × safety tier

Counts are **per-tool**, keyed by the actual API regime each tool's own
`self._fo()` / `self._qps()` / `self._gateway()` call uses (not the
module's dominant-family label in `MODULE_INDEX.md` — a handful of modules
bridge two regimes internally, e.g. `pcpolicies.update_compliance_policy`
is an FO-dominant module but that one tool calls the Gateway PCAS API; see
the per-module `API family` line in Section C for the exact split).

| API family | Read | Write | Destructive | Total |
|---|---:|---:|---:|---:|
| **FO** — classic `/api/2.0/fo/`, `/msp/` | 68 | 93 | 21 | 182 |
| **QPS** — `/qps/rest/` | 26 | 15 | 7 | 48 |
| **Gateway** — JWT `gateway.<pod>...` | 84 | 37 | 11 | 132 |
| **N/A** — static reference data, no live call (`qualys_user_permissions_summary`) | 1 | 0 | 0 | 1 |
| **Module tools subtotal** | **179** | **145** | **39** | **363** |
| Core server tools (`qualys_check_connectivity`, `qualys_list_enabled_modules`, `qualys_list_modules`) | 3 | 0 | 0 | 3 |
| **Grand total** | **182** | **145** | **39** | **366** |

This reconciles exactly to the 363 module tools + 3 core tools = 366 total
reported by `python -m qualys_mcp --check` with
`QUALYS_ENABLE_DESTRUCTIVE=true` (see `MODULE_INDEX.md`). For reference,
the module-level dominant-family grouping used elsewhere in this repo is
31 FO / 9 QPS / 19 Gateway modules (59 total).

## C. Master table — every tool, grouped by module

Modules are grouped by their dominant API family (matching
`MODULE_INDEX.md`'s section order: Classic FO, then QPS, then Gateway),
alphabetical by registry name within each section. Each module subsection
gives its tool count by tier and its `# self._fo/_qps/_gateway` call-site
family split, then every tool with: HTTP method, endpoint (as called;
`{placeholder}` segments are supplied by the tool's own parameters),
action/verb(s) actually sent to Qualys, and a one-line capability summary
(the tool's own docstring first line).

### Classic FO API (`/api/2.0/fo/`, `/msp/`)

#### `assetgroups` — List, create, edit, and delete asset groups.
*4 tools (read 1 / write 2 / destructive 1), API family: FO:4*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_asset_groups` | read | GET | `/api/2.0/fo/asset/group/` | list | List asset groups in the user account. |
| `qualys_add_asset_group` | write | POST | `/api/2.0/fo/asset/group/` | add | Create a new asset group. |
| `qualys_edit_asset_group` | write | POST | `/api/2.0/fo/asset/group/` | edit | Edit an existing asset group. |
| `qualys_delete_asset_group` | destructive | POST | `/api/2.0/fo/asset/group/` | delete | Permanently delete an asset group. IRREVERSIBLE. |

#### `authrecords` — Create, list, update, and delete Qualys scan authentication records.
*29 tools (read 4 / write 24 / destructive 1), API family: FO:28*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_auth_records` | read | GET | `/api/2.0/fo/auth/` | list | List all authentication records visible to the user, across all technologies. |
| `qualys_list_auth_records_by_type` | read | GET | `/api/2.0/fo/auth/{record_type}/` | list | List authentication records for a specific technology, with full detail. |
| `qualys_get_auth_record` | read | GET | `/api/2.0/fo/auth/{record_type}/` | list | Fetch full detail (``details=All``) for one or more auth records of a given type. |
| `qualys_user_permissions_summary` | read | N/A | `N/A` | N/A (static reference data — no live API call) | Return the static user-role permissions summary for auth records. |
| `qualys_create_auth_record` | write | POST | `/api/2.0/fo/auth/{record_type}/` | create | Create an authentication record for any supported technology. |
| `qualys_update_auth_record` | write | POST | `/api/2.0/fo/auth/{record_type}/` | update | Update an existing authentication record for any supported technology. |
| `qualys_create_unix_auth` | write | POST | `/api/2.0/fo/auth/unix/` | create | Create a Unix authentication record (also used for Cisco / Checkpoint Firewall). |
| `qualys_update_unix_auth` | write | POST | `/api/2.0/fo/auth/unix/` | update | Update an existing Unix (or Cisco / Checkpoint Firewall) authentication record. |
| `qualys_create_windows_auth` | write | POST | `/api/2.0/fo/auth/windows/` | create | Create a Windows authentication record. |
| `qualys_update_windows_auth` | write | POST | `/api/2.0/fo/auth/windows/` | update | Update an existing Windows authentication record. |
| `qualys_create_oracle_auth` | write | POST | `/api/2.0/fo/auth/oracle/` | create | Create an Oracle authentication record (or an Oracle system record template). |
| `qualys_update_oracle_auth` | write | POST | `/api/2.0/fo/auth/oracle/` | update | Update an existing Oracle authentication record. |
| `qualys_create_mssql_auth` | write | POST | `/api/2.0/fo/auth/ms_sql/` | create | Create an MS SQL Server authentication record (compliance scans). |
| `qualys_update_mssql_auth` | write | POST | `/api/2.0/fo/auth/ms_sql/` | update | Update an existing MS SQL Server authentication record. |
| `qualys_create_mysql_auth` | write | POST | `/api/2.0/fo/auth/mysql/` | create | Create a MySQL authentication record. |
| `qualys_update_mysql_auth` | write | POST | `/api/2.0/fo/auth/mysql/` | update | Update an existing MySQL authentication record. |
| `qualys_create_postgresql_auth` | write | POST | `/api/2.0/fo/auth/postgresql/` | create | Create a PostgreSQL authentication record (compliance scans). |
| `qualys_update_postgresql_auth` | write | POST | `/api/2.0/fo/auth/postgresql/` | update | Update an existing PostgreSQL authentication record. |
| `qualys_create_vmware_auth` | write | POST | `/api/2.0/fo/auth/vmware/` | create | Create a VMware (vSphere/ESXi) authentication record. |
| `qualys_update_vmware_auth` | write | POST | `/api/2.0/fo/auth/vmware/` | update | Update an existing VMware (vSphere/ESXi) authentication record. |
| `qualys_create_snmp_auth` | write | POST | `/api/2.0/fo/auth/snmp/` | create | Create an SNMP authentication record (SNMPv1, v2c, or v3). |
| `qualys_update_snmp_auth` | write | POST | `/api/2.0/fo/auth/snmp/` | update | Update an existing SNMP authentication record. |
| `qualys_create_http_auth` | write | POST | `/api/2.0/fo/auth/http/` | create | Create an HTTP authentication record for HTTP-protocol-level auth. |
| `qualys_update_http_auth` | write | POST | `/api/2.0/fo/auth/http/` | update | Update an existing HTTP authentication record. |
| `qualys_create_docker_auth` | write | POST | `/api/2.0/fo/auth/docker/` | create | Create a Docker authentication record (compliance scans only). |
| `qualys_update_docker_auth` | write | POST | `/api/2.0/fo/auth/docker/` | update | Update an existing Docker authentication record. |
| `qualys_create_kubernetes_auth` | write | POST | `/api/2.0/fo/auth/kubernetes/` | create | Create a Kubernetes authentication record (compliance scans only). |
| `qualys_update_kubernetes_auth` | write | POST | `/api/2.0/fo/auth/kubernetes/` | update | Update an existing Kubernetes authentication record. |
| `qualys_delete_auth_record` | destructive | POST | `/api/2.0/fo/auth/{record_type}/` | delete | Permanently delete one or more authentication records. IRREVERSIBLE. |

#### `cloudinternalscans` — Create, update, and list Azure/GCP cloud internal scan jobs (VM only).
*3 tools (read 1 / write 2 / destructive 0), API family: FO:3*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_cloud_internal_scans` | read | GET | `/api/3.0/fo/schedule/scan/` | list | List cloud internal scan jobs (Azure/GCP) via the VM scan schedule list. |
| `qualys_create_cloud_internal_scan` | write | POST | `/api/3.0/fo/scan/cloud/internal/job/` | create | Create an Azure or GCP cloud internal scan job. |
| `qualys_update_cloud_internal_scan` | write | POST | `/api/3.0/fo/scan/cloud/internal/job/` | update | Update an existing Azure or GCP cloud internal scan job. |

#### `cloudperimeterscans` — Create, update, and launch cloud perimeter scan jobs (VM/PC).
*5 tools (read 1 / write 4 / destructive 0), API family: FO:5*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_cloud_perimeter_scans` | read | GET | `/api/2.0/fo/schedule/scan/` | list | List cloud perimeter scan jobs via the VM scan schedule list. |
| `qualys_create_cloud_perimeter_scan` | write | POST | `/api/4.0/fo/scan/cloud/perimeter/job/` | create | Create a cloud perimeter scan job (VM or PC). |
| `qualys_update_cloud_perimeter_scan` | write | POST | `/api/4.0/fo/scan/cloud/perimeter/job/` | update | Update an existing cloud perimeter scan job. |
| `qualys_reset_cloud_perimeter_scan` | write | POST | `/api/4.0/fo/scan/cloud/perimeter/job/` | update | Reset a cloud perimeter scan job's pause/cancel duration and recurrence. |
| `qualys_launch_cloud_perimeter_scan` | write | POST | `/api/4.0/fo/scan/cloud/perimeter/job/` | create | Launch a one-time (immediate) cloud perimeter scan job. |

#### `compliancescans` — Launch, monitor, and manage Policy Compliance (PC) and SCAP scans.
*7 tools (read 3 / write 3 / destructive 1), API family: FO:7*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_compliance_scans` | read | GET | `/api/2.0/fo/scan/compliance/` | list | List Policy Compliance scans in the subscription. |
| `qualys_list_scap_scans` | read | GET | `/api/2.0/fo/scan/scap/` | list | List SCAP scans in the subscription. |
| `qualys_fetch_compliance_scan_results` | read | GET | `/api/2.0/fo/scan/compliance/` | fetch | Fetch results for a compliance scan with status Finished/Canceled/Paused/Error. |
| `qualys_launch_compliance_scan` | write | POST | `/api/2.0/fo/scan/compliance/` | launch | Launch a new Policy Compliance scan. |
| `qualys_launch_compliance_scan_on_ec2` | write | POST | `/api/2.0/fo/scan/compliance/` | launch | Launch a compliance scan against Amazon EC2 hosts, selected by tag. |
| `qualys_manage_compliance_scan` | write | POST | `/api/2.0/fo/scan/compliance/` | cancel \| pause \| resume | Pause, resume, or cancel a running compliance scan (reversible). |
| `qualys_delete_compliance_scan` | destructive | POST | `/api/2.0/fo/scan/compliance/` | delete | Permanently delete a compliance scan and its results. IRREVERSIBLE. |

#### `containerizedscanner` — Create, list, update, and delete containerized scanner appliances.
*4 tools (read 1 / write 2 / destructive 1), API family: FO:4*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_containerized_scanners` | read | POST | `/api/2.0/fo/appliance/qcss/` | list | List containerized scanner appliances. |
| `qualys_create_containerized_scanner` | write | POST | `/api/2.0/fo/appliance/qcss/` | create | Create a new containerized scanner appliance. |
| `qualys_update_containerized_scanner` | write | POST | `/api/2.0/fo/appliance/qcss/` | update | Update a containerized scanner appliance's settings and/or tags. |
| `qualys_delete_containerized_scanner` | destructive | POST | `/api/2.0/fo/appliance/qcss/` | delete | Permanently delete a containerized scanner appliance. IRREVERSIBLE. |

#### `excludedhosts` — List, audit, and manage the subscription excluded-host list.
*5 tools (read 2 / write 2 / destructive 1), API family: FO:5*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_excluded_hosts` | read | GET | `/api/2.0/fo/asset/excluded_ip/` | list | List hosts on the excluded-hosts list (hosts that will not be scanned). |
| `qualys_list_excluded_hosts_history` | read | GET | `/api/2.0/fo/asset/excluded_ip/history/` | list | View the change history (add/remove events) for excluded hosts. |
| `qualys_add_excluded_hosts` | write | POST | `/api/2.0/fo/asset/excluded_ip/` | add | Add hosts (IPs) to the excluded-hosts list. Excluded hosts are not scanned. |
| `qualys_remove_excluded_hosts` | write | POST | `/api/2.0/fo/asset/excluded_ip/` | remove | Remove specific hosts from the excluded-hosts list (they become scannable again). |
| `qualys_remove_all_excluded_hosts` | destructive | POST | `/api/2.0/fo/asset/excluded_ip/` | remove_all | Remove ALL hosts from the excluded-hosts list in one call. IRREVERSIBLE. |

#### `hostassets` — List, update, and pull vulnerability detections for scanned hosts.
*3 tools (read 2 / write 1 / destructive 0), API family: FO:3*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_hosts` | read | GET | `/api/2.0/fo/asset/host/` | list | List scanned hosts in the subscription (host inventory, not detections). |
| `qualys_list_host_detections` | read | GET | `/api/2.0/fo/asset/host/vm/detection/` | list | List hosts with their latest vulnerability detections (the VMDR feed). |
| `qualys_update_hosts` | write | POST | `/api/2.0/fo/asset/host/` | update | Bulk-update host attributes (tracking method, owner, UD fields, comments). |

#### `ipmanagement` — List, add, and update IP addresses in the Qualys subscription.
*3 tools (read 1 / write 2 / destructive 0), API family: FO:3*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_ips` | read | GET | `/api/2.0/fo/asset/ip/` | list | List IP addresses/ranges in the user account. |
| `qualys_add_ips` | write | POST | `/api/2.0/fo/asset/ip/` | add | Add IP addresses/ranges to the subscription for scanning and reporting. |
| `qualys_update_ips` | write | POST | `/api/2.0/fo/asset/ip/` | update | Update attributes of existing IP addresses in the subscription. |

#### `ipv6assets` — List and add IPv4/IPv6 mapping records for IPv6 asset management.
*2 tools (read 1 / write 1 / destructive 0), API family: FO:2*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_ipv6_mapping_records` | read | GET | `/api/2.0/fo/asset/ip/v4_v6` | list | List IPv6 mapping records in the subscription. |
| `qualys_add_ipv6_mapping_records` | write | POST | `/api/2.0/fo/asset/ip/v4_v6` | add | Add IPv6 mapping records to the subscription. |

#### `knowledgebase` — Query the Qualys vulnerability KnowledgeBase (QIDs).
*5 tools (read 4 / write 1 / destructive 0), API family: FO:6*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_knowledgebase` | read | GET | `/api/2.0/fo/knowledge_base/vuln/` | list | List vulnerabilities (QIDs) from the Qualys KnowledgeBase. |
| `qualys_get_qids` | read | GET | `/api/2.0/fo/knowledge_base/vuln/` | list | Fetch full detail for specific QIDs. |
| `qualys_download_qvs_json` | read | GET | `/api/2.0/fo/knowledge_base/qvs/` | list | Download Qualys Vulnerability Score (QVS) data from the KnowledgeBase. |
| `qualys_list_vendor_references` | read | GET | `/api/2.0/fo/vendor/` | list_vendor_references | List vendor references (patches/advisories) for QIDs in the KnowledgeBase. |
| `qualys_edit_vulnerability` | write | POST | `/api/2.0/fo/knowledge_base/vuln/` | edit | Edit a vulnerability's severity, disabled state, or comments. |

#### `maps` — Launch and manage discovery scans (maps), scheduled tasks, and domains.
*13 tools (read 5 / write 5 / destructive 3), API family: FO:13*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_map_reports` | read | GET | `/msp/map_report_list.php` | list (implicit — dedicated endpoint, no action param) | List saved network map reports in the user's account. |
| `qualys_list_running_maps` | read | GET | `/msp/scan_running_list.php` | list (implicit — dedicated endpoint, no action param) | List maps and scans currently running in the user's account. |
| `qualys_fetch_map_report` | read | GET | `/msp/map_report.php` | fetch (implicit — dedicated endpoint, no action param) | Download a saved map report (status must be "Finished"). |
| `qualys_list_legacy_scheduled_tasks` | read | GET | `/msp/scheduled_scans.php` | list (via `type` param, no action param) | List scheduled scan and/or map tasks (legacy Scheduled Scans API). |
| `qualys_list_domains` | read | GET | `/api/2.0/fo/asset/domain/` | list | List asset domains defined in the subscription (map targets). |
| `qualys_launch_map` | write | GET | `/msp/map-2.php` | launch (implicit — dedicated endpoint, no action param) | Launch a network discovery map (asynchronous, one domain at a time). |
| `qualys_cancel_map` | write | GET | `/msp/scan_cancel.php` | cancel (implicit — dedicated endpoint, no action param) | Cancel a running map (or scan). Not possible while status is "Loading". |
| `qualys_create_legacy_scheduled_task` | write | POST | `/msp/scheduled_scans.php` | add_task=yes | Add a scheduled scan or map task (legacy Scheduled Scans API). |
| `qualys_create_domain` | write | POST | `/api/2.0/fo/asset/domain/` | create | Add an asset domain (and optional netblocks) for use as a map target. |
| `qualys_update_domain` | write | POST | `/api/2.0/fo/asset/domain/` | update | Update an existing asset domain's netblocks. |
| `qualys_delete_map_report` | destructive | GET | `/msp/scan_report_delete.php` | delete (implicit — dedicated endpoint, no action param) | Permanently delete a saved network map report. IRREVERSIBLE. |
| `qualys_delete_legacy_scheduled_task` | destructive | POST | `/msp/scheduled_scans.php` | drop_task=yes | Permanently remove a scheduled scan or map task. IRREVERSIBLE. |
| `qualys_delete_domain` | destructive | POST | `/api/2.0/fo/asset/domain/` | delete | Permanently delete one or more asset domains. IRREVERSIBLE. |

#### `networks` — List, create, and update custom networks; assign scanner appliances to them.
*4 tools (read 1 / write 3 / destructive 0), API family: FO:4*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_networks` | read | GET | `/api/2.0/fo/network/` | list | List custom networks in the subscription. |
| `qualys_create_network` | write | POST | `/api/2.0/fo/network/` | create | Create a new custom network. |
| `qualys_update_network` | write | POST | `/api/2.0/fo/network/` | update | Rename an existing custom network. The network ID itself cannot change. |
| `qualys_assign_scanner_appliance_to_network` | write | POST | `/api/2.0/fo/appliance/` | assign_network_id | Assign a scanner appliance to a custom network. |

#### `optionprofiles` — List, export/import, and manage VM/PCI/PC option profiles.
*6 tools (read 2 / write 3 / destructive 1), API family: FO:7*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_option_profiles` | read | GET | `/api/2.0/fo/subscription/option_profile/{vm\|pci\|pc}/` | list | List option profiles of a given type (VM, PCI, or PC/Compliance). |
| `qualys_export_option_profiles` | read | GET | `/api/2.0/fo/subscription/option_profile/` | export | Export one or all option profiles (any type) to XML. |
| `qualys_import_option_profiles` | write | POST | `/api/2.0/fo/subscription/option_profile/` | import | Import option profiles from an OPTION_PROFILES XML document. |
| `qualys_create_option_profile` | write | POST | `/api/2.0/fo/subscription/option_profile/{vm\|pci\|pc}/` | create | Create a VM, PCI, or PC (Compliance) option profile. |
| `qualys_update_option_profile` | write | POST | `/api/2.0/fo/subscription/option_profile/{vm\|pci\|pc}/` | update | Update a VM, PCI, or PC (Compliance) option profile. |
| `qualys_delete_option_profile` | destructive | POST | `/api/2.0/fo/subscription/option_profile/{vm\|pci\|pc}/` | delete | Permanently delete a VM, PCI, or PC option profile. IRREVERSIBLE. |

#### `patches` — List patches applicable to host assets.
*1 tools (read 1 / write 0 / destructive 0), API family: FO:1*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_patches` | read | GET | `/api/2.0/fo/asset/host/patch/` | list | List patches applicable to hosts in the subscription. |

#### `pccontrols` — Query Policy Compliance (PC) controls and their criticality.
*3 tools (read 2 / write 1 / destructive 0), API family: FO:2+Gateway:1*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_compliance_controls` | read | GET | `/api/2.0/fo/compliance/control/` | list | List compliance controls (System Defined Controls and UDCs) visible to the user. |
| `qualys_get_control_criticality` | read | GET | `/api/2.0/fo/compliance/control/` | list | Get the criticality rating(s) for specific compliance controls. |
| `qualys_set_control_criticality` | write | PUT | `/pcas/v3/policy/section/control` | update | Override a control's criticality within one policy section. |

#### `pcexceptions` — List, request, update, and delete Policy Compliance (PC) exceptions.
*4 tools (read 1 / write 2 / destructive 1), API family: FO:4*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_pc_exceptions` | read | GET | `/api/2.0/fo/compliance/exception/` | list | List compliance exceptions in the account. |
| `qualys_request_pc_exception` | write | POST | `/api/2.0/fo/compliance/exception/` | request | Request a new compliance exception (created Pending, expiry = creation date). |
| `qualys_update_pc_exception` | write | POST | `/api/2.0/fo/compliance/exception/` | update | Update one or more compliance exceptions. |
| `qualys_delete_pc_exception` | destructive | POST | `/api/2.0/fo/compliance/exception/` | delete | Permanently delete one or more compliance exceptions. IRREVERSIBLE. |

#### `pcpolicies` — Manage Policy Compliance (PC) compliance policies.
*8 tools (read 2 / write 5 / destructive 1), API family: FO:8+Gateway:3*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_compliance_policies` | read | GET | `/api/2.0/fo/compliance/policy/` | list | List compliance policies visible to the user. |
| `qualys_export_compliance_policy` | read | GET | `/api/2.0/fo/compliance/policy/` | export | Export a compliance policy to XML (service-provided controls, optionally UDCs). |
| `qualys_import_compliance_policy` | write | POST | `/api/2.0/fo/compliance/policy/` | import | Import a compliance policy defined in XML into the account. |
| `qualys_merge_compliance_policy` | write | POST | `/api/2.0/fo/compliance/policy/` | merge | Merge one compliance policy's content into another. |
| `qualys_manage_policy_asset_tags` | write | POST | `/api/2.0/fo/compliance/policy/` | add_asset_tags \| remove_asset_tags \| set_asset_tags | Add, remove, or set the asset tags assigned to a compliance policy. |
| `qualys_manage_policy_asset_groups` | write | POST | `/api/2.0/fo/compliance/policy/` | add_asset_group_ids \| remove_asset_group_ids \| set_asset_group_ids | Add, remove, or set the asset groups assigned to a compliance policy. |
| `qualys_update_compliance_policy` | write | PUT | `/pcas/v3/policy` | update | Update a compliance policy's title, cover page, and/or active status. |
| `qualys_delete_compliance_policy` | destructive | DELETE | `/pcas/v3/policy` | delete | Permanently delete a compliance policy, its exceptions, and posture data. IRREVERSIBLE. |

#### `purgehosts` — Purge vulnerability and/or compliance assessment data from hosts.
*1 tools (read 0 / write 0 / destructive 1), API family: FO:1*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_purge_hosts` | destructive | POST | `/api/2.0/fo/asset/host/` | purge | Purge assessment data (vulnerability and/or compliance) for hosts. IRREVERSIBLE. |

#### `remediationtickets` — View, edit, and delete VM remediation tickets; ignore vulns on hosts.
*6 tools (read 3 / write 2 / destructive 1), API family: FO:6*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_view_ticket_list` | read | GET | `/msp/ticket_list.php` | list (implicit — dedicated endpoint, no action param) | View remediation tickets in the account. At least one filter is required. |
| `qualys_get_ticket_info` | read | GET | `/msp/get_tickets.php` | get (implicit — dedicated endpoint, no action param) | Get remediation ticket information for third-party integration. |
| `qualys_view_deleted_tickets` | read | GET | `/msp/ticket_list_deleted.php` | list (deleted; implicit, no action param) | List deleted remediation tickets. At least one filter is required. |
| `qualys_edit_tickets` | write | POST | `/msp/ticket_edit.php` | edit (implicit — dedicated endpoint, no action param) | Bulk-edit remediation tickets matching the given selection filters. |
| `qualys_set_ignore_vulns` | write | POST | `/api/2.0/fo/ignore_vuln/index.php` | ignore \| restore (via `action` param, default ignore) | Ignore or restore vulnerabilities on hosts (vulnerability/host pairs). |
| `qualys_delete_tickets` | destructive | POST | `/msp/ticket_delete.php` | delete (implicit — dedicated endpoint, no action param) | Permanently delete remediation tickets matching the given filters. |

#### `reports` — Launch, monitor, download, and manage Qualys reports and scorecards.
*9 tools (read 3 / write 5 / destructive 1), API family: FO:9*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_reports` | read | GET | `/api/2.0/fo/report/` | list | List reports in the user's Report Share account. |
| `qualys_download_report` | read | GET | `/api/2.0/fo/report/` | fetch | Download a finished saved report from Report Share. |
| `qualys_scheduled_reports_list` | read | GET | `/api/2.0/fo/schedule/report/` | list | List scheduled reports in the user's account. |
| `qualys_launch_report` | write | POST | `/api/2.0/fo/report/` | launch | Launch a report in Report Share and return its new report ID. |
| `qualys_launch_scorecard` | write | POST | `/api/2.0/fo/report/scorecard/` | launch | Launch a vulnerability scorecard report in Report Share. |
| `qualys_cancel_report` | write | POST | `/api/2.0/fo/report/` | cancel | Cancel a running report. |
| `qualys_launch_scheduled_report` | write | POST | `/api/2.0/fo/schedule/report/` | launch_now | Launch a scheduled report immediately. |
| `qualys_asset_search_report` | write | GET | `/api/2.0/fo/report/asset/` | search | Run an immediate (non-queued) asset search report. |
| `qualys_delete_report` | destructive | POST | `/api/2.0/fo/report/` | delete | Permanently delete a saved report from Report Share. IRREVERSIBLE. |

#### `reporttemplates` — List and export Qualys VM report templates (scan, PCI, patch, map).
*5 tools (read 5 / write 0 / destructive 0), API family: FO:5*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_report_templates` | read | GET | `/msp/report_template_list.php` | list (implicit — dedicated endpoint, no action param) | List all available report templates (all types) in the account. |
| `qualys_get_scan_template` | read | GET | `/api/2.0/fo/report/template/scan/` | export | Export one or all Scan report templates. |
| `qualys_get_pci_scan_template` | read | GET | `/api/2.0/fo/report/template/pciscan/` | export | Export one or all PCI Scan report templates. |
| `qualys_get_patch_template` | read | GET | `/api/2.0/fo/report/template/patch/` | export | Export one or all Patch report templates. |
| `qualys_get_map_template` | read | GET | `/api/2.0/fo/report/template/map/` | export | Export one or all Map report templates. |

#### `restrictedips` — List and manage the subscription restricted (allowed-source) IP list.
*2 tools (read 1 / write 1 / destructive 0), API family: FO:2*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_restricted_ips` | read | GET | `/api/2.0/fo/setup/restricted_ips/` | list | List the restricted IPs configured for the subscription. |
| `qualys_manage_restricted_ips` | write | POST | `/api/2.0/fo/setup/restricted_ips/` | activate \| add \| clear \| delete \| replace | Activate, populate, or clear the restricted IPs list. |

#### `scannerappliances` — List and manage Qualys scanner appliances (virtual and physical).
*9 tools (read 2 / write 6 / destructive 1), API family: FO:9*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_scanner_appliances` | read | GET | `/api/2.0/fo/appliance/` | list | List scanner appliances (physical, virtual, containerized, offline). |
| `qualys_get_scanner_vlans_routes` | read | GET | `/api/2.0/fo/appliance/` | list | View VLANs and static routes configured on scanner appliance(s). |
| `qualys_create_virtual_scanner` | write | POST | `/api/2.0/fo/appliance/` | create | Create a new virtual scanner appliance. |
| `qualys_update_virtual_scanner` | write | POST | `/api/2.0/fo/appliance/` | update | Update a virtual scanner appliance's settings and/or tags. |
| `qualys_update_physical_scanner` | write | POST | `/api/2.0/fo/appliance/physical/` | update | Update a physical scanner appliance's settings, tags, VLANs, or routes. |
| `qualys_replace_scanner_appliance` | write | GET | `/api/2.0/fo/appliance/replace_iscanner/` | replace | Replace one scanner appliance with another. |
| `qualys_set_scanner_vlans` | write | POST | `/api/2.0/fo/appliance/ \| /api/2.0/fo/appliance/physical/` | update | Set (add/update/remove) VLANs on a scanner appliance. |
| `qualys_set_scanner_routes` | write | POST | `/api/2.0/fo/appliance/ \| /api/2.0/fo/appliance/physical/` | update | Set (add/update/remove) static routes on a scanner appliance. |
| `qualys_delete_virtual_scanner` | destructive | POST | `/api/2.0/fo/appliance/` | delete | Permanently delete a virtual scanner appliance. IRREVERSIBLE. |

#### `scanschedules` — Create, update, list, and delete VM and PC recurring scan schedules.
*8 tools (read 2 / write 4 / destructive 2), API family: FO:8*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_vm_scan_schedules` | read | GET | `/api/5.0/fo/schedule/scan/` | list | List recurring VM scan schedules in the subscription. |
| `qualys_list_compliance_scan_schedules` | read | GET | `/api/2.0/fo/schedule/scan/compliance/` | list | List recurring Policy Compliance (PC) scan schedules in the subscription. |
| `qualys_create_vm_scan_schedule` | write | POST | `/api/2.0/fo/schedule/scan/` | create | Create a recurring VM scan schedule. |
| `qualys_update_vm_scan_schedule` | write | POST | `/api/2.0/fo/schedule/scan/` | update | Update an existing recurring VM scan schedule. |
| `qualys_create_compliance_scan_schedule` | write | POST | `/api/2.0/fo/schedule/scan/compliance/` | create | Create a recurring Policy Compliance (PC) scan schedule. |
| `qualys_update_compliance_scan_schedule` | write | POST | `/api/2.0/fo/schedule/scan/compliance/` | update | Update an existing recurring Policy Compliance (PC) scan schedule. |
| `qualys_delete_vm_scan_schedule` | destructive | POST | `/api/2.0/fo/schedule/scan/` | delete | Permanently delete a VM scan schedule. IRREVERSIBLE. |
| `qualys_delete_compliance_scan_schedule` | destructive | POST | `/api/2.0/fo/schedule/scan/compliance/` | delete | Permanently delete a Policy Compliance (PC) scan schedule. IRREVERSIBLE. |

#### `scap` — List SCAP policies and generate SCAP compliance reports.
*3 tools (read 3 / write 0 / destructive 0), API family: FO:3*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_scap_policies` | read | GET | `/api/2.0/fo/compliance/fdcc_policy/` | list | List SCAP (FDCC) policies visible to the user. |
| `qualys_get_cyberscope_report` | read | GET | `/api/2.0/fo/asset/host/cyberscope/fdcc/scan/ \| /api/2.0/fo/asset/host/cyberscope/fdcc/policy/ \| /api/2.0/fo/asset/host/cyberscope/` | fetch (path selected by `report_type`: scan/policy/global) | Generate a Cyberscope-compatible XML report (LASR format) for FISMA reporting. |
| `qualys_get_scap_arf_report` | read | GET | `/api/2.0/fo/compliance/scap/arf/` | get (implicit — dedicated endpoint, no action param) | Generate a SCAP scan report in Asset Reporting Format (ARF 1.1 Schema). |

#### `searchlists` — Create and manage static and dynamic QID search lists.
*8 tools (read 2 / write 4 / destructive 2), API family: FO:8*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_static_search_lists` | read | GET | `/api/2.0/fo/qid/search_list/static/` | list | List static search lists. |
| `qualys_list_dynamic_search_lists` | read | GET | `/api/2.0/fo/qid/search_list/dynamic/` | list | List dynamic search lists. |
| `qualys_create_static_search_list` | write | POST | `/api/2.0/fo/qid/search_list/static/` | create | Create a static search list from an explicit QID set. |
| `qualys_update_static_search_list` | write | POST | `/api/2.0/fo/qid/search_list/static/` | update | Update a static search list's title, membership, or comments. |
| `qualys_create_dynamic_search_list` | write | POST | `/api/2.0/fo/qid/search_list/dynamic/` | create | Create a dynamic search list from filter criteria. |
| `qualys_update_dynamic_search_list` | write | POST | `/api/2.0/fo/qid/search_list/dynamic/` | update | Update a dynamic search list's title, criteria, or comments. |
| `qualys_delete_static_search_list` | destructive | POST | `/api/2.0/fo/qid/search_list/static/` | delete | Permanently delete a static search list. IRREVERSIBLE. |
| `qualys_delete_dynamic_search_list` | destructive | POST | `/api/2.0/fo/qid/search_list/dynamic/` | delete | Permanently delete a dynamic search list. IRREVERSIBLE. |

#### `users` — Manage subscription users and review user activity.
*5 tools (read 2 / write 3 / destructive 0), API family: FO:6*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_users` | read | GET | `/msp/user_list.php` | list (implicit — dedicated endpoint, no action param) | List users visible to the calling account in the subscription. |
| `qualys_export_user_activity_log` | read | GET | `/api/2.0/fo/activity_log/` | list | Export the subscription's user activity log (CSV output only). |
| `qualys_add_or_edit_user` | write | POST | `/msp/user.php` | add \| edit | Add a new user account, or edit an existing one. |
| `qualys_activate_deactivate_user` | write | POST | `/msp/user.php` | activate \| deactivate | Activate an inactive user account, or deactivate an active one. |
| `qualys_change_login_password` | write | POST | `/api/2.0/fo/user/change_password/` | change_password (implicit, single-purpose endpoint) | Change the login password for the account making this API call. |

#### `vaults` — List and manage third-party authentication vault definitions.
*5 tools (read 2 / write 2 / destructive 1), API family: FO:5*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_vaults` | read | GET | `/api/2.0/fo/vault/` | list | List authentication vault definitions configured in the subscription. |
| `qualys_get_vault` | read | GET | `/api/2.0/fo/vault/` | view | View full settings for a single authentication vault. |
| `qualys_create_vault` | write | POST | `/api/2.0/fo/vault/` | create | Create a new third-party authentication vault definition. |
| `qualys_update_vault` | write | POST | `/api/2.0/fo/vault/` | update | Update settings for an existing authentication vault. |
| `qualys_delete_vault` | destructive | POST | `/api/2.0/fo/vault/` | delete | Permanently delete an authentication vault definition. IRREVERSIBLE. |

#### `virtualhosts` — List and manage virtual host (IP:port -> FQDN) configurations.
*3 tools (read 1 / write 1 / destructive 1), API family: FO:3*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_virtual_hosts` | read | GET | `/api/2.0/fo/asset/vhost/` | list | List virtual hosts in the account. |
| `qualys_manage_virtual_host` | write | POST | `/api/2.0/fo/asset/vhost/` | add_fqdn \| create \| delete_fqdn \| update | Create, update, or add/remove FQDNs on a virtual host configuration. |
| `qualys_delete_virtual_host` | destructive | POST | `/api/2.0/fo/asset/vhost/` | delete | Permanently delete a virtual host configuration. IRREVERSIBLE. |

#### `vmscans` — Launch, monitor, and manage VM scans.
*12 tools (read 7 / write 4 / destructive 1), API family: FO:12*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_scans` | read | GET | `/api/2.0/fo/scan/` | list | List VM scans in the subscription. |
| `qualys_fetch_scan_results` | read | GET | `/api/2.0/fo/scan/` | fetch | Fetch results for a finished scan. |
| `qualys_vm_scan_statistics` | read | GET | `/api/2.0/fo/scan/stats/` | list | List unprocessed VM scans and the VM recrypt processing backlog. |
| `qualys_vm_scan_summary` | read | GET | `/api/2.0/fo/scan/vm/summary/` | list | Identify hosts scanned/not-scanned and why, for one or more VM scans. |
| `qualys_scan_summary` | read | GET | `/api/2.0/fo/scan/summary/` | list | Original VM Scan Summary API — hosts not scanned and why. |
| `qualys_scanner_details` | read | GET | `/api/2.0/fo/scan/scanner/` | list | Identify which scanner appliance/external scanner scanned given IPs. |
| `qualys_get_pci_share_status` | read | GET | `/api/2.0/fo/scan/pci/` | status | Get the export status of a PCI scan previously shared with a merchant account. |
| `qualys_launch_scan` | write | POST | `/api/2.0/fo/scan/` | launch | Launch a new VM scan. |
| `qualys_launch_scan_on_ec2` | write | POST | `/api/2.0/fo/scan/` | launch | Launch a VM scan against Amazon EC2 hosts. |
| `qualys_manage_scan` | write | POST | `/api/2.0/fo/scan/` | cancel \| pause \| resume | Pause, resume, or cancel a running scan (reversible operations). |
| `qualys_share_pci_scan` | write | POST | `/api/2.0/fo/scan/pci/` | share | Export (share) a finished PCI scan to a PCI Merchant account. |
| `qualys_delete_scan` | destructive | POST | `/api/2.0/fo/scan/` | delete | Permanently delete a scan and its results. IRREVERSIBLE. |

### QPS REST API (`/qps/rest/`)

#### `assettags` — Search, create, update, and delete asset tags via the QPS AM API.
*5 tools (read 2 / write 2 / destructive 1), API family: QPS:5*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_search_tags` | read | POST | `/qps/rest/2.0/search/am/tag` | search | Search asset tags in the subscription. |
| `qualys_get_tag` | read | GET | `/qps/rest/2.0/get/am/tag/{tag_id}` | get | Fetch full details for a single asset tag by ID. |
| `qualys_create_tag` | write | POST | `/qps/rest/2.0/create/am/tag` | create | Create a new asset tag, optionally as a dynamic (rule-based) tag. |
| `qualys_update_tag` | write | POST | `/qps/rest/2.0/update/am/tag/{tag_id}` | update | Update an existing asset tag's name, color, or dynamic rule. |
| `qualys_delete_tag` | destructive | POST | `/qps/rest/2.0/delete/am/tag/{tag_id}` | delete | Permanently delete an asset tag. IRREVERSIBLE. |

#### `cloudagent` — List and manage Qualys Cloud Agents, activation keys, and config profiles.
*6 tools (read 4 / write 1 / destructive 1), API family: QPS:6*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_agents` | read | POST | `/qps/rest/1.0/search/ca/agent` | search | Search/list Cloud Agent-managed hosts. |
| `qualys_get_agent` | read | GET | `/qps/rest/1.0/get/ca/agent/{asset_id}` | get | Fetch full detail for a single Cloud Agent host by asset ID. |
| `qualys_list_activation_keys` | read | POST | `/qps/rest/1.0/search/ca/activationkey` | search | List Cloud Agent activation keys available in the subscription. |
| `qualys_list_config_profiles` | read | POST | `/qps/rest/1.0/search/ca/configurationprofile` | search | List Cloud Agent configuration profiles in the subscription. |
| `qualys_activate_agent` | write | POST | `/qps/rest/1.0/activate/ca/agent/{asset_id}` | activate | Activate (or reactivate) Cloud Agent modules on an asset. |
| `qualys_uninstall_agent` | destructive | POST | `/qps/rest/1.0/uninstall/ca/agent/{asset_id}` | uninstall | Uninstall the Cloud Agent from a host. IRREVERSIBLE. |

#### `hostassetam` — Read-only search/fetch over the QPS Asset Management (AM) inventory.
*5 tools (read 5 / write 0 / destructive 0), API family: QPS:5*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_search_host_assets` | read | POST | `/qps/rest/2.0/search/am/hostasset` | search | Search the normalized host asset inventory. |
| `qualys_get_host_asset` | read | GET | `/qps/rest/2.0/get/am/hostasset/{host_asset_id}` | get | Fetch full detail for a single host asset by ID. |
| `qualys_count_host_assets` | read | POST | `/qps/rest/2.0/count/am/hostasset` | count | Count host assets matching the given filters (no result rows returned). |
| `qualys_search_assets` | read | POST | `/qps/rest/2.0/search/am/asset` | search | Search the generic normalized asset inventory (all asset types). |
| `qualys_get_asset` | read | GET | `/qps/rest/2.0/get/am/asset/{asset_id}` | get | Fetch full detail for a single normalized asset by ID. |

#### `wasauth` — Search, inspect, and manage WAS web application authentication records.
*5 tools (read 2 / write 2 / destructive 1), API family: QPS:5*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_search_was_auth_records` | read | POST | `/qps/rest/3.0/search/was/webappauthrecord` | search | Search web application authentication records. |
| `qualys_get_was_auth_record` | read | GET | `/qps/rest/3.0/get/was/webappauthrecord/{auth_record_id}` | get | Fetch full detail for a single authentication record. |
| `qualys_create_was_auth_record` | write | POST | `/qps/rest/3.0/create/was/webappauthrecord/` | create | Create a new web application authentication record. |
| `qualys_update_was_auth_record` | write | POST | `/qps/rest/3.0/update/was/webappauthrecord/{auth_record_id}` | update | Update an existing authentication record's fields. |
| `qualys_delete_was_auth_record` | destructive | POST | `/qps/rest/3.0/delete/was/webappauthrecord/{auth_record_id}` | delete | Permanently delete an authentication record. IRREVERSIBLE. |

#### `wasfindings` — Search WAS findings (vulnerabilities/sensitive content/info gathered) and manage their status.
*4 tools (read 3 / write 1 / destructive 0), API family: QPS:4*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_search_was_findings` | read | POST | `/qps/rest/3.0/search/was/finding` | search | Search WAS findings. |
| `qualys_get_was_finding` | read | GET | `/qps/rest/3.0/get/was/finding/{finding_id}` | get | Fetch full detail for a single finding. |
| `qualys_count_was_findings` | read | POST | `/qps/rest/3.0/count/was/finding` | count | Count findings matching optional filters. |
| `qualys_update_was_finding` | write | POST | `/qps/rest/3.0/update/was/finding/{finding_id}` | update | Ignore or reactivate a finding. |

#### `wasreports` — Search, generate, download, and delete WAS reports.
*4 tools (read 2 / write 1 / destructive 1), API family: QPS:4*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_search_was_reports` | read | POST | `/qps/rest/3.0/search/was/report` | search | Search generated/in-progress WAS reports. |
| `qualys_download_was_report` | read | GET | `/qps/rest/3.0/download/was/report/{report_id}` | download | Download a generated report's contents. |
| `qualys_create_was_report` | write | POST | `/qps/rest/3.0/create/was/report` | create | Generate a new WAS report. |
| `qualys_delete_was_report` | destructive | POST | `/qps/rest/3.0/delete/was/report/{report_id}` | delete | Permanently delete a report. IRREVERSIBLE. |

#### `wasscans` — Search, launch, monitor, and manage WAS scans.
*6 tools (read 3 / write 2 / destructive 1), API family: QPS:6*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_search_was_scans` | read | POST | `/qps/rest/3.0/search/was/wasscan` | search | Search WAS scans. |
| `qualys_get_was_scan` | read | GET | `/qps/rest/3.0/get/was/wasscan/{scan_id}` | get | Fetch full detail for a single scan (includes status, target, profile). |
| `qualys_get_was_scan_status` | read | GET | `/qps/rest/3.0/get/was/wasscan/{scan_id}` | get | Fetch the current status of a scan. |
| `qualys_launch_was_scan` | write | POST | `/qps/rest/3.0/launch/was/wasscan/` | launch | Launch a new WAS scan against a web application. |
| `qualys_cancel_was_scan` | write | POST | `/qps/rest/3.0/cancel/was/wasscan/{scan_id}` | cancel | Cancel a running scan (reversible in the sense that it does not delete data). |
| `qualys_delete_was_scan` | destructive | POST | `/qps/rest/3.0/delete/was/wasscan/{scan_id}` | delete | Permanently delete a scan and its results. IRREVERSIBLE. |

#### `wasschedules` — Search, inspect, and manage WAS recurring scan schedules.
*5 tools (read 2 / write 2 / destructive 1), API family: QPS:5*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_search_was_schedules` | read | POST | `/qps/rest/3.0/search/was/wasscanschedule` | search | Search recurring WAS scan schedules. |
| `qualys_get_was_schedule` | read | GET | `/qps/rest/3.0/get/was/wasscanschedule/{schedule_id}` | get | Fetch full detail for a single scan schedule. |
| `qualys_create_was_schedule` | write | POST | `/qps/rest/3.0/create/was/wasscanschedule` | create | Create a recurring scan schedule for a web application. |
| `qualys_update_was_schedule` | write | POST | `/qps/rest/3.0/update/was/wasscanschedule/{schedule_id}` | update | Update an existing scan schedule (also used to activate/deactivate it). |
| `qualys_delete_was_schedule` | destructive | POST | `/qps/rest/3.0/delete/was/wasscanschedule/{schedule_id}` | delete | Permanently delete a scan schedule. IRREVERSIBLE. |

#### `waswebapps` — Search, inspect, and manage WAS Web Application assets.
*6 tools (read 3 / write 2 / destructive 1), API family: QPS:6*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_search_was_webapps` | read | POST | `/qps/rest/3.0/search/was/webapp` | search | Search WAS web application assets. |
| `qualys_get_was_webapp` | read | GET | `/qps/rest/3.0/get/was/webapp/{webapp_id}` | get | Fetch full detail for a single web application. |
| `qualys_count_was_webapps` | read | POST | `/qps/rest/3.0/count/was/webapp` | count | Count web applications matching optional filters. |
| `qualys_create_was_webapp` | write | POST | `/qps/rest/3.0/create/was/webapp` | create | Create a new WAS web application asset. |
| `qualys_update_was_webapp` | write | POST | `/qps/rest/3.0/update/was/webapp/{webapp_id}` | update | Update an existing web application's basic fields. |
| `qualys_delete_was_webapp` | destructive | POST | `/qps/rest/3.0/delete/was/webapp/{webapp_id}` | delete | Permanently delete a web application. IRREVERSIBLE. |

### Gateway / JWT API

#### `certview` — Read-only search and inspection of the CertView certificate inventory.
*5 tools (read 5 / write 0 / destructive 0), API family: Gateway:5*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_search_certificates` | read | POST | `/certview/v2/certificates` | search | Search the certificate inventory (v2 — no fixed result cap). |
| `qualys_get_certificate` | read | GET | `/certview/v2/certificates/{certificate_id}` | get | Fetch full detail for a single certificate by its CertView ID/hash. |
| `qualys_list_certificate_instances` | read | POST | `/certview/v2/instances` | search | List certificate/server instances (where certificates are deployed). |
| `qualys_list_certificate_authorities` | read | POST | `/certview/v2/cas` | search | List certificate authorities (issuers) seen across the inventory. |
| `qualys_count_certificates` | read | POST | `/certview/v2/certificates/count` | count | Count certificates matching a filter (no certificate rows returned). |

#### `cloudviewconnectors` — Manage TotalCloud/CloudView cloud connectors (AWS, Azure, GCP).
*8 tools (read 2 / write 5 / destructive 1), API family: Gateway:8*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_cloud_connectors` | read | GET | `/cloudview-api/rest/v1/{provider}/connectors` | list | List cloud connectors for a provider. |
| `qualys_get_cloud_connector` | read | GET | `/cloudview-api/rest/v1/{provider}/connectors/{connector_id}` | get | Get details for a single cloud connector. |
| `qualys_create_aws_connector` | write | POST | `/cloudview-api/rest/v1/aws/connectors` | create | Create a new AWS cloud connector (cross-account IAM role based). |
| `qualys_create_azure_connector` | write | POST | `/cloudview-api/rest/v1/azure/connectors` | create | Create a new Azure cloud connector (service principal based). |
| `qualys_create_gcp_connector` | write | POST | `/cloudview-api/rest/v1/gcp/connectors` | create | Create a new GCP cloud connector (service account key based). |
| `qualys_update_cloud_connector` | write | PUT | `/cloudview-api/rest/v1/{provider}/connectors/{connector_id}` | update | Update an existing cloud connector. |
| `qualys_run_connector_sync` | write | POST | `/cloudview-api/rest/v1/{provider}/connectors/run` | run (sync) | Trigger an on-demand sync ("run") for one or more connectors. |
| `qualys_delete_cloud_connector` | destructive | DELETE | `/cloudview-api/rest/v1/{provider}/connectors/{connector_id}` | delete | Permanently delete a cloud connector. IRREVERSIBLE. |

#### `cloudviewposture` — Query TotalCloud/CloudView controls, evaluations (posture), and resources.
*7 tools (read 7 / write 0 / destructive 0), API family: Gateway:7*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_cloudview_controls` | read | GET | `/cloudview-api/rest/v1/controls/metadata/list` | list | List CloudView control metadata (the CSPM control library). |
| `qualys_get_cloudview_control` | read | GET | `/cloudview-api/rest/v1/controls/metadata/{control_id}` | get | Get metadata for a single CloudView control. |
| `qualys_list_cloudview_evaluations` | read | GET | `/cloudview-api/rest/v1/{provider}/evaluations/{account_id}` | list | List control evaluations (posture) for a cloud account/subscription/project. |
| `qualys_list_control_evaluation_resources` | read | GET | `/cloudview-api/rest/v1/{provider}/evaluations/{account_id}/resources/{control_id}` | list | List the evaluated resources (pass/fail) for one control in an account. |
| `qualys_get_cloudview_evaluation_stats` | read | GET | `/cloudview-api/rest/v1/{provider}/evaluations/stats/{control_id}/{connector_id}` | get_stats | Get evaluation statistics for a control on a connector (optionally one resource). |
| `qualys_list_cloudview_resources` | read | GET | `/cloudview-api/rest/v1/resource/{resource_type}/{provider.upper()}` | list | List (and inspect details of) cloud resources of a given type. |
| `qualys_list_cloudview_policies` | read | GET | `/cloudview-api/rest/v1/policy` | list | List CloudView policies / mandates (control frameworks). |

#### `cloudviewremediation` — List, inspect, and trigger TotalCloud/CloudView remediation, and manage rules.
*4 tools (read 2 / write 2 / destructive 0), API family: Gateway:4*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_remediation_activities` | read | GET | `/cloudview-api/rest/v1/remediation/activities` | list | List remediation activities across cloud providers. |
| `qualys_get_remediation_activity` | read | GET | `/cloudview-api/rest/v1/remediation/activities/{activity_id}` | get | Get details for a single remediation activity. |
| `qualys_trigger_remediation` | write | POST | `/cloudview-api/rest/v1/remediation` | create (trigger) | Trigger one-click remediation for a failing resource/control. |
| `qualys_set_remediation_rule` | write | PATCH | `/cloudview-api/rest/v1/remediation/rules/{rule_id}` | update (rule) | Enable or disable a remediation rule. |

#### `complianceframeworkreports` — Build and retrieve mandate/framework-based Policy Compliance (PC) reports.
*8 tools (read 7 / write 1 / destructive 0), API family: Gateway:9*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_preferred_frameworks` | read | GET | `/pcrs/1.0/mandate/list` | list | List preferred compliance frameworks (mandates) configured for the subscription. |
| `qualys_list_framework_policies` | read | GET | `/pcrs/1.0/policy/list` | list | List all active compliance policies available for framework reports. |
| `qualys_list_framework_asset_groups` | read | GET | `/pcrs/1.0/assetGroup/list` | list | List asset groups available for scoping a framework report. |
| `qualys_list_framework_asset_tags` | read | GET | `/pcrs/1.0/assetTag/list` | list | List the hierarchical asset tag tree available for scoping a framework report. |
| `qualys_list_framework_report_sources` | read | GET | `/pcrs/1.0/mandate/report/sources` | list | List the available asset source options for creating a framework report. |
| `qualys_create_framework_report` | write | POST | `/pcrs/1.0/mandate/report` | create | Create (generate) a new compliance framework report. |
| `qualys_get_framework_report_status` | read | GET | `/pcrs/1.0/mandate/report/status` | get_status | Get the generation status of a compliance framework report. |
| `qualys_download_framework_report` | read | GET | `/pcrs/1.0/mandate/report/download/html` | download | Download a completed compliance framework report (HTML format, zipped). |

#### `csam` — Search/inspect the CSAM asset inventory and manage user-defined asset tags.
*7 tools (read 5 / write 2 / destructive 0), API family: QPS:2+Gateway:5*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_search_csam_assets` | read | POST | `/rest/2.0/search/am/asset` | search | Search the CyberSecurity Asset Management inventory using QQL. |
| `qualys_get_csam_asset` | read | GET | `/rest/2.0/get/am/asset` | get | Get full CSAM detail for a single asset by ID. |
| `qualys_count_csam_assets` | read | POST | `/rest/2.0/count/am/asset` | count | Count CSAM assets matching a QQL filter (no result rows returned). |
| `qualys_list_csam_software` | read | POST | `/rest/2.0/am/asset/component/{asset_id}` | list (POST filter body) | List installed software (components) across assets or for one asset. |
| `qualys_list_csam_asset_tags` | read | GET | `/rest/2.0/get/am/asset` | get (tags inline on asset record) | List the tags currently assigned to a specific CSAM asset. |
| `qualys_add_csam_asset_tags` | write | POST | `/qps/rest/2.0/update/am/hostasset/` | update (add tags) | Assign one or more user-defined tags to one or more assets. |
| `qualys_remove_csam_asset_tags` | write | POST | `/qps/rest/2.0/update/am/hostasset/` | update (remove tags) | Remove one or more user-defined tags from one or more assets. |

#### `cscontainers` — List, inspect, and manage Container Security container assets.
*5 tools (read 4 / write 0 / destructive 1), API family: Gateway:5*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_cs_containers` | read | GET | `/csapi/v1.3/containers` | list | List containers in the subscription. |
| `qualys_get_cs_container` | read | GET | `/csapi/v1.3/containers/{container_sha}` | get | Fetch full metadata for a single container. |
| `qualys_get_cs_container_vulnerabilities` | read | GET | `/csapi/v1.3/containers/{container_sha}/vuln` | list_vulnerabilities | Fetch the vulnerability findings for a container. |
| `qualys_get_cs_container_software` | read | GET | `/csapi/v1.3/containers/{container_sha}/software` | list_software | Fetch the installed software packages for a container. |
| `qualys_delete_cs_container` | destructive | DELETE | `/csapi/v1.3/containers/{container_sha}` | delete | Permanently delete a container from the subscription. IRREVERSIBLE. |

#### `csimages` — List, inspect, and manage Container Security image assets.
*5 tools (read 4 / write 0 / destructive 1), API family: Gateway:5*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_cs_images` | read | GET | `/csapi/v1.3/images` | list | List container images in the subscription. |
| `qualys_get_cs_image` | read | GET | `/csapi/v1.3/images/{image_sha}` | get | Fetch full metadata for a single image. |
| `qualys_get_cs_image_vulnerabilities` | read | GET | `/csapi/v1.3/images/{image_sha}/vuln` | list_vulnerabilities | Fetch the vulnerability findings for an image. |
| `qualys_get_cs_image_software` | read | GET | `/csapi/v1.3/images/{image_sha}/software` | list_software | Fetch the installed software packages for an image. |
| `qualys_delete_cs_image` | destructive | DELETE | `/csapi/v1.3/images/{image_sha}` | delete | Permanently delete an image from the subscription. IRREVERSIBLE. |

#### `cspolicies` — List, inspect, and manage Container Security (centralized) policies.
*5 tools (read 2 / write 2 / destructive 1), API family: Gateway:5*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_cs_policies` | read | GET | `/csapi/v1.3/centralizedPolicy` | list | List container security policies (and their assessment status). |
| `qualys_get_cs_policy` | read | GET | `/csapi/v1.3/centralizedPolicy/{policy_id}` | get | Fetch details of a single policy. |
| `qualys_create_cs_policy` | write | POST | `/csapi/v1.3/centralizedPolicy` | create | Create a new centralized policy (admission-controller or CI-CD). |
| `qualys_update_cs_policy` | write | PUT | `/csapi/v1.3/centralizedPolicy/{policy_id}` | update | Update an existing centralized policy. |
| `qualys_delete_cs_policy` | destructive | DELETE | `/csapi/v1.3/centralizedPolicy/{policy_id}` | delete | Permanently delete a policy. IRREVERSIBLE. |

#### `csregistries` — List, inspect, configure, and scan Container Security registries.
*6 tools (read 2 / write 3 / destructive 1), API family: Gateway:6*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_cs_registries` | read | GET | `/csapi/v1.3/registry` | list | List configured container registries. |
| `qualys_get_cs_registry` | read | GET | `/csapi/v1.3/registry/{registry_id}` | get | Fetch details of a single registry. |
| `qualys_create_cs_registry` | write | POST | `/csapi/v1.3/registry` | create | Create (connect) a new container registry. |
| `qualys_update_cs_registry` | write | PUT | `/csapi/v1.3/registry/{registry_id}` | update | Update an existing registry connection. |
| `qualys_run_cs_registry_scan` | write | POST | `/csapi/v1.3/registry/{registry_id}/schedule` | schedule_scan | Trigger a scan of a registry's images. |
| `qualys_delete_cs_registry` | destructive | DELETE | `/csapi/v1.3/registry/{registry_id}` | delete | Permanently delete (disconnect) a registry. IRREVERSIBLE. |

#### `cssensors` — List, inspect, and delete deployed Container Security sensors.
*3 tools (read 2 / write 0 / destructive 1), API family: Gateway:3*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_cs_sensors` | read | GET | `/csapi/v1.3/sensors` | list | List deployed container security sensors. |
| `qualys_get_cs_sensor` | read | GET | `/csapi/v1.3/sensors/{sensor_id}` | get | Fetch details of a single sensor. |
| `qualys_delete_cs_sensor` | destructive | DELETE | `/csapi/v1.3/sensors/{sensor_id}` | delete | Permanently delete a sensor. IRREVERSIBLE. |

#### `easm` — List/search external assets and attack surface findings; drive discovery.
*5 tools (read 3 / write 2 / destructive 0), API family: Gateway:5*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_external_assets` | read | POST | `/rest/2.0/search/am/asset` | search | Search external (internet-facing) assets in the CSAM/EASM inventory. |
| `qualys_get_external_asset` | read | GET | `/rest/2.0/get/am/asset/{asset_id}` | get | Fetch full detail for a single external/CSAM asset by ID. |
| `qualys_list_attack_surface_findings` | read | POST | `/easm/v1/findings/search` | search | List external attack surface findings/risks (exposures on external assets). |
| `qualys_trigger_easm_discovery` | write | POST | `/easm/v1/profile/{profile_id}/discovery` | start_discovery | Trigger an on-demand EASM discovery run for a profile. |
| `qualys_add_easm_seed` | write | POST | `/easm/v1/profile/{profile_id}/seeds` | add_seed | Add a seed (domain/subdomain/IP) to an EASM profile's discovery scope. |

#### `edr` — Search EDR events/assets and perform response actions on endpoints.
*5 tools (read 3 / write 0 / destructive 2), API family: Gateway:5*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_search_edr_events` | read | POST | `/ioc/events/search` | search | Search EDR detection events. |
| `qualys_get_edr_event` | read | GET | `/ioc/events/{event_id}` | get | Fetch full detail for a single EDR event by ID. |
| `qualys_list_edr_assets` | read | GET | `/ioc/asset/all` | list | List assets monitored by EDR. |
| `qualys_quarantine_edr_asset` | destructive | POST | `/ioc/remediation-actions/performQuarantineHostAction` | performQuarantineHostAction | Quarantine (network-isolate) an EDR asset. DISRUPTIVE / gated. |
| `qualys_kill_edr_process` | destructive | POST | `/ioc/remediation-actions/performAction` | performAction (kill process) | Kill a running process on an EDR-monitored asset. DISRUPTIVE / gated. |

#### `fim` — List FIM events/incidents/profiles and create/approve incidents.
*8 tools (read 6 / write 2 / destructive 0), API family: Gateway:8*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_fim_events` | read | POST | `/fim/v2/events/search` | search | Search FIM change events. |
| `qualys_get_fim_event` | read | GET | `/fim/v2/events/{event_id}` | get | Fetch full detail for a single FIM event by ID. |
| `qualys_list_fim_incidents` | read | POST | `/fim/v3/incidents/search` | search | Search FIM incidents. |
| `qualys_list_fim_profiles` | read | POST | `/fim/v3/profiles/search` | search | List FIM monitoring profiles. |
| `qualys_list_fim_rules` | read | GET | `/fim/v3/profiles/{profile_id}/rules` | list | List monitoring rules within a FIM profile. |
| `qualys_list_fim_ignored_events` | read | POST | `/fim/v2/events/ignore/search` | search (ignored) | Search ignored FIM events (events suppressed by ignore rules). |
| `qualys_create_fim_incident` | write | POST | `/fim/v2/incidents` | create | Create a manual FIM incident from a set of events. |
| `qualys_approve_fim_incident` | write | POST | `/fim/v3/incidents/{incident_id}/approve` | approve | Approve (or set the approval status of) a FIM incident. |

#### `gav` — Read-only Global AssetView asset inventory over the gateway API.
*4 tools (read 4 / write 0 / destructive 0), API family: Gateway:4*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_gav_assets` | read | POST | `/rest/2.0/search/am/asset` | search | List/search all assets in the Global AssetView inventory. |
| `qualys_get_gav_asset` | read | GET | `/rest/2.0/get/am/asset` | get | Get full detail for a single asset by its GAV asset ID. |
| `qualys_count_gav_assets` | read | POST | `/rest/2.0/count/am/asset` | count | Count assets in the Global AssetView inventory matching a QQL filter. |
| `qualys_list_gav_host_instances` | read | GET | `/am/v2/sn/assets/host/{asset_id}` | get | List the software instances reported for a host asset. |

#### `patchmgmt` — Search patches, inspect PM assets, and manage patch deployment jobs.
*12 tools (read 7 / write 4 / destructive 1), API family: Gateway:12*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_search_pm_patches` | read | POST | `/pm/v3/patches` | search | Search the Patch Management patch inventory using QQL. |
| `qualys_get_pm_patch` | read | GET | `/pm/v3/patches/{patch_uuid}` | get | Get details for a single patch by its UUID. |
| `qualys_count_pm_patches` | read | POST | `/pm/v3/patches/count` | count | Count Patch Management patches matching a QQL filter (no rows returned). |
| `qualys_list_pm_assets` | read | POST | `/pm/v1/assets` | search | List Patch Management assets, optionally filtered by QQL. |
| `qualys_list_patch_catalog` | read | GET | `/pm/v1/patchcatalog/patches` | list | List patches from the Patch Management catalog (Windows/Linux). |
| `qualys_list_deployment_jobs` | read | GET | `/pm/v1/deploymentjobs` | list | List patch deployment jobs in the subscription. |
| `qualys_get_deployment_job` | read | GET | `/pm/v1/deploymentjob/{job_id}` | get | Get the full configuration of a single deployment job. |
| `qualys_create_deployment_job` | write | POST | `/pm/v1/deploymentjob` | create | Create a patch deployment job. |
| `qualys_update_deployment_job` | write | PATCH | `/pm/v1/deploymentjob/update/{job_id}` | update | Update an existing patch deployment job. |
| `qualys_enable_deployment_job` | write | PATCH | `/pm/v1/deploymentjob/update/{job_id}` | update (status=Enabled) | Enable (activate) a patch deployment job. |
| `qualys_disable_deployment_job` | write | PATCH | `/pm/v1/deploymentjob/update/{job_id}` | update (status=Disabled) | Disable (deactivate) a patch deployment job. |
| `qualys_delete_deployment_job` | destructive | DELETE | `/pm/v1/deploymentjobs` | delete (bulk, job id list body) | Permanently delete one or more patch deployment jobs. IRREVERSIBLE. |

#### `pcaspolicies` — Author Policy Compliance (PC) policies via the PCAS API, and browse the PCAS library.
*25 tools (read 10 / write 14 / destructive 1), API family: Gateway:26*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_get_pcas_policy` | read | GET | `/pcas/v3/policy` | get | Export a compliance policy in JSON via the PCAS Policy API. |
| `qualys_update_pcas_policy` | write | PUT | `/pcas/v3/policy` | update | Update a compliance policy's title, cover page, and/or active status. |
| `qualys_lock_pcas_policy` | write | PUT | `/pcas/v3/policy/lock` | lock | Lock or unlock a compliance policy. |
| `qualys_delete_pcas_policy` | destructive | DELETE | `/pcas/v3/policy` | delete | Permanently delete a compliance policy, its exceptions, and posture data. IRREVERSIBLE. |
| `qualys_list_pcas_policy_technologies` | read | GET | `/pcas/v3/policy/technology` | list | List all technologies associated with a compliance policy. |
| `qualys_add_pcas_policy_technologies` | write | POST | `/pcas/v3/policy/technology` | add | Add technologies to a compliance policy (existing technologies are unaffected). |
| `qualys_remove_pcas_policy_technology` | write | DELETE | `/pcas/v3/policy/technology` | remove | Remove one technology from a compliance policy. |
| `qualys_get_pcas_policy_section` | read | GET | `/pcas/v3/policy/section` | get | Get the details of one section within a compliance policy. |
| `qualys_add_pcas_policy_section` | write | POST | `/pcas/v3/policy/section` | add | Add a new section to a compliance policy. |
| `qualys_update_pcas_policy_section` | write | PUT | `/pcas/v3/policy/section` | update | Rename an existing section within a compliance policy. |
| `qualys_delete_pcas_policy_section` | write | DELETE | `/pcas/v3/policy/section` | delete | Delete a section (and its controls' section membership) from a compliance policy. |
| `qualys_get_pcas_policy_section_control` | read | GET | `/pcas/v3/policy/section/control` | get | Get one control's details within a specific policy section. |
| `qualys_add_pcas_policy_section_control` | write | POST | `/pcas/v3/policy/section/control` | add | Add one control to a section within a compliance policy. |
| `qualys_update_pcas_policy_section_control` | write | PUT | `/pcas/v3/policy/section/control` | update | Update a control within a section of a compliance policy. |
| `qualys_delete_pcas_policy_section_control` | write | DELETE | `/pcas/v3/policy/section/control` | delete | Remove a control from a section within a compliance policy. |
| `qualys_list_pcas_control_technologies` | read | GET | `/pcas/v3/policy/section/control/technology` | list | List technologies associated with a control within a policy section. |
| `qualys_add_pcas_control_technologies` | write | POST | `/pcas/v3/policy/section/control/technology` | add | Add technologies to a control within a policy section. |
| `qualys_remove_pcas_control_technology` | write | DELETE | `/pcas/v3/policy/section/control/technology` | remove | Remove one technology from a control within a policy section. |
| `qualys_get_pcas_control_technology_evaluation` | read | GET | `/pcas/v3/policy/section/control/technology/evaluation` | get | Get the evaluation fields for one technology on a control within a policy section. |
| `qualys_update_pcas_control_technology_evaluation` | write | PUT | `/pcas/v3/policy/section/control/technology/evaluation` | update | Update evaluation fields for one technology on a control within a policy section. |
| `qualys_list_pcas_library_labels` | read | GET | `/pcas/v1/library/label` | list | List all supported PCAS library labels (e.g. CIS, DISA STIG, Vendor, Mandate). |
| `qualys_list_pcas_library_label_technologies` | read | GET | `/pcas/v1/library/technology` | list | List technologies associated with a PCAS library label. |
| `qualys_list_pcas_library_policies` | read | GET | `/pcas/v1/library/policy/list` | list | List library policies, optionally filtered by label and/or technology. |
| `qualys_get_pcas_library_policy` | read | GET | `/pcas/v1/library/policy` | get | Get details for a specific PCAS library policy. |
| `qualys_import_pcas_library_policy` | write | POST | `/pcas/v1/library/policy/import` | import | Import a PCAS library policy into the subscription as a new compliance policy. |

#### `pcposture` — Retrieve Policy Compliance (PC) posture information.
*4 tools (read 4 / write 0 / destructive 0), API family: FO:1+Gateway:4*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_posture_policies` | read | GET | `/pcrs/{api_version}/posture/policy/list` | get (policy list) | List policy IDs for use with the PC Posture Streaming APIs. |
| `qualys_resolve_posture_host_ids` | read | GET | `/pcrs/{api_version}/posture/hostids` | get | Resolve host IDs for one or more policies (streaming sequence step 2). |
| `qualys_list_posture_info` | read | GET | `/api/2.0/fo/compliance/posture/info/` | list | List compliance posture info records for one or more policies (non-streaming). |
| `qualys_stream_posture_info` | read | POST | `/pcrs/{api_version}/posture/postureInfo` | get (POST body, streamed) | Stream compliance posture info for resolved host IDs (streaming sequence step 3). |

#### `pcrs` — Read policy posture in bulk via the PCRS (Posture Streaming) Gateway API.
*6 tools (read 6 / write 0 / destructive 0), API family: Gateway:6*

| Tool | Tier | HTTP | Endpoint | Action(s) | Capability |
|---|---|---|---|---|---|
| `qualys_list_pcrs_policies` | read | GET | `/pcrs/{version}/posture/policy/list` | list | List policies that have been evaluated (PCRS policy list). |
| `qualys_get_pcrs_policy` | read | GET | `/pcrs/{version}/posture/policy/list` | list (filtered client-side by policy_id) | Fetch metadata for a single policy via PCRS. |
| `qualys_resolve_pcrs_host_ids` | read | GET | `/pcrs/1.0/posture/hostids` | get | Resolve the host IDs scanned for a policy (step before posture fetch). |
| `qualys_get_pcrs_posture` | read | POST | `/pcrs/1.0/posture/postureInfo` | get (POST body) | Stream posture info for a policy and a set of host IDs. |
| `qualys_list_pcrs_controls` | read | GET | `/pcrs/1.0/posture/controls` | list | List the controls defined in a policy. |
| `qualys_get_pcrs_control` | read | GET | `/pcrs/1.0/posture/controls/{control_id}` | get | Fetch metadata for a single compliance control by ID. |

## D. Legend / notes

**Safety tiers** (`qualys_mcp/modules/base.py`):
- **read** — never mutates state; `readOnlyHint=True`. Always registered.
- **write** — creates/updates/launches/pauses/imports state; reversible.
  Always registered (not gated by `QUALYS_ENABLE_DESTRUCTIVE`).
- **destructive** — deletes/purges/uninstalls/irreversibly changes state.
  Only registered when the server process is started with
  `QUALYS_ENABLE_DESTRUCTIVE=true`; even then, the tool's own body must be
  called with `confirm=<the target id/name>` (validated by
  `BaseModule._confirm_or_error`) or it returns a `CONFIRMATION_REQUIRED`
  error instead of acting. A caller cannot trigger a destructive action by
  accident through tool discovery alone — it must not exist on a
  destructive-disabled console, and even where it exists, the id must be
  echoed back deliberately.
- One documented safety-tier gap carried over from `COVERAGE_MATRIX.md`:
  `qualys_manage_restricted_ips`'s `clear`/`delete` operations (which can
  fully disable the subscription's IP allow-list) are tiered **write**, not
  destructive — no `confirm` is required and it is available even with
  `QUALYS_ENABLE_DESTRUCTIVE=false`.

**API family / auth differences** (`qualys_mcp/client.py`):
- **FO** (`self._fo`, classic `/api/2.0/fo/` + `/msp/`) — HTTP Basic auth
  plus a mandatory `X-Requested-With` header; form-encoded request bodies;
  XML responses (normalized to a dict). Reads use `params=` with GET; write
  actions use `data=` with POST and (almost always) an explicit
  `"action": "..."` field — the Action(s) column reflects that literal
  value, or the set of values a dispatcher tool can send (e.g.
  `qualys_manage_scan` sends `pause`/`resume`/`cancel` depending on its
  `operation` argument). A few legacy `/msp/*.php` endpoints have no
  `action` field at all — the endpoint URL itself is the single action;
  those are noted as "(implicit — dedicated endpoint, no action param)".
- **QPS** (`self._qps`, `/qps/rest/...`) — also HTTP Basic auth. The action
  verb is a path segment, not a body field (e.g.
  `/qps/rest/3.0/search/was/webapp`, `/qps/rest/2.0/update/am/tag/{id}`),
  so it's derived directly from the URL for every QPS tool in this table.
- **Gateway** (`self._gateway`, JWT) — bearer-token auth: the client POSTs
  username/password to `{gateway_url}/auth` to obtain a JWT, caches it, and
  refreshes once on a 401. Bodies are JSON (a couple of GAV/CSAM endpoints
  use raw XML `<FilterRequest>` bodies via `content=`/`accept="xml"`
  instead). Gateway REST endpoints have no `action` field; the Action(s)
  column is inferred from the combination of HTTP verb and path shape
  (e.g. `GET .../containers` → `list`, `GET .../containers/{id}` → `get`,
  `POST .../search` → `search`, `DELETE .../{id}` → `delete`).

**Get-by-id / detail tools require an id.** Any tool whose endpoint
template contains a `{...}` placeholder (e.g. `{tag_id}`, `{scan_ref}`,
`{policy_id}`, `{container_sha}`) needs that identifier supplied by the
caller — it is not a listing call. Most modules pair each such tool with a
sibling `list_*`/`search_*` tool that has no placeholder and is the
intended way to discover ids first (e.g. `qualys_search_tags` →
`qualys_get_tag`). A few FO "get" tools (e.g. `qualys_get_auth_record`)
are implemented as a `list` call filtered to specific ids/`details=All`,
since the underlying classic API has no dedicated per-id GET verb — this
is noted in their Action(s) cell.

**Endpoint template notation**: `{name}` is a value substituted from the
tool's own parameter of that name; `{a|b|c}` denotes a small fixed set of
possible path segments selected by a parameter (e.g.
`/api/2.0/fo/subscription/option_profile/{vm|pci|pc}/` selected by
`profile_type`). Action(s) cells joined with `|` indicate a single tool
that can dispatch more than one Qualys action depending on an argument
(documented in the tool's own docstring); this was the case the audit
brief specifically asked to be captured (e.g. `manage_scan`,
`manage_restricted_ips`, `manage_virtual_host`,
`manage_policy_asset_tags`/`_groups`).

**Everything in this document resolved cleanly from source** — no
tool's endpoint or action had to be left as an unresolved "(varies)"
placeholder. A small number of entries required reading past the direct
`self._fo/_qps/_gateway(...)` call site (dispatch tables, ternary path
selection, module-level path constants, or `PATCH`-only "enable/disable"
tools that share one endpoint with `update`); those are annotated inline
in their Action(s) or Capability cell rather than hidden.
