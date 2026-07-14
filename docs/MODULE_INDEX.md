# Qualys MCP - Module Index

Full inventory of every module discovered by `qualys_mcp.registry.get_available_modules()`. Counts are derived from the offline `--check` validation (no credentials/network required):

```powershell
.\.venv\Scripts\python.exe -m qualys_mcp --check
$env:QUALYS_ENABLE_DESTRUCTIVE='true'; .\.venv\Scripts\python.exe -m qualys_mcp --check
```

- **Modules:** 59
- **Tools registered (default, destructive disabled):** 327 total (`324` module tools + 3 core tools -- `qualys_check_connectivity`, `qualys_list_enabled_modules`, `qualys_list_modules`)
- **Tools registered (`QUALYS_ENABLE_DESTRUCTIVE=true`):** 366 total (`363` module tools + 3 core tools)
- **Destructive-only tools:** 39 tools, spread across 34 modules (hidden unless `QUALYS_ENABLE_DESTRUCTIVE=true`)
- **API family split:** 31 FO, 9 QPS, 19 Gateway (4 modules span two regimes and are counted under their dominant family; see the Family column)

Family key: **FO** = classic `/api/2.0/fo/` + `/msp/` API (Basic auth + `X-Requested-With`, XML). **QPS** = `/qps/rest/` REST API (Basic auth, XML/JSON). **Gateway** = JWT-authenticated gateway host APIs (Container Security, TotalCloud, Patch, CSAM, EASM, PCAS, PCRS, ...). A family value like `FO + Gateway` means the module calls both regimes; the first name is the dominant one.

## Classic FO API (`/api/2.0/fo/`, `/msp/`)

| Registry name | API family | # tools (default / destructive) | Description |
|---|---|---|---|
| `assetgroups` | FO | 3 / 4 | List, create, edit, and delete asset groups. |
| `authrecords` | FO | 28 / 29 | Create, list, update, and delete Qualys scan authentication records. |
| `cloudinternalscans` | FO | 3 / 3 | Create, update, and list Azure/GCP cloud internal scan jobs (VM only). |
| `cloudperimeterscans` | FO | 5 / 5 | Create, update, and launch cloud perimeter scan jobs (VM/PC). |
| `compliancescans` | FO | 6 / 7 | Launch, monitor, and manage Policy Compliance (PC) and SCAP scans. |
| `containerizedscanner` | FO | 3 / 4 | Create, list, update, and delete containerized scanner appliances. |
| `excludedhosts` | FO | 4 / 5 | List, audit, and manage the subscription excluded-host list. |
| `hostassets` | FO | 3 / 3 | List, update, and pull vulnerability detections for scanned hosts. |
| `ipmanagement` | FO | 3 / 3 | List, add, and update IP addresses in the Qualys subscription. |
| `ipv6assets` | FO | 2 / 2 | List and add IPv4/IPv6 mapping records for IPv6 asset management. |
| `knowledgebase` | FO | 5 / 5 | Query the Qualys vulnerability KnowledgeBase (QIDs). |
| `maps` | FO | 10 / 13 | Launch and manage discovery scans (maps), scheduled tasks, and domains. |
| `networks` | FO | 4 / 4 | List, create, and update custom networks; assign scanner appliances to them. |
| `optionprofiles` | FO | 5 / 6 | List, export/import, and manage VM/PCI/PC option profiles. |
| `patches` | FO | 1 / 1 | List patches applicable to host assets. |
| `pccontrols` | FO + Gateway | 3 / 3 | Query Policy Compliance (PC) controls and their criticality. |
| `pcexceptions` | FO | 3 / 4 | List, request, update, and delete Policy Compliance (PC) exceptions. |
| `pcpolicies` | FO + Gateway | 7 / 8 | Manage Policy Compliance (PC) compliance policies. |
| `purgehosts` | FO | 0 / 1 | Purge vulnerability and/or compliance assessment data from hosts. |
| `remediationtickets` | FO | 5 / 6 | View, edit, and delete VM remediation tickets; ignore vulns on hosts. |
| `reports` | FO | 8 / 9 | Launch, monitor, download, and manage Qualys reports and scorecards. |
| `reporttemplates` | FO | 5 / 5 | List and export Qualys VM report templates (scan, PCI, patch, map). |
| `restrictedips` | FO | 2 / 2 | List and manage the subscription restricted (allowed-source) IP list. |
| `scannerappliances` | FO | 8 / 9 | List and manage Qualys scanner appliances (virtual and physical). |
| `scanschedules` | FO | 6 / 8 | Create, update, list, and delete VM and PC recurring scan schedules. |
| `scap` | FO | 3 / 3 | List SCAP policies and generate SCAP compliance reports. |
| `searchlists` | FO | 6 / 8 | Create and manage static and dynamic QID search lists. |
| `users` | FO | 5 / 5 | Manage subscription users and review user activity. |
| `vaults` | FO | 4 / 5 | List and manage third-party authentication vault definitions. |
| `virtualhosts` | FO | 2 / 3 | List and manage virtual host (IP:port -> FQDN) configurations. |
| `vmscans` | FO | 11 / 12 | Launch, monitor, and manage VM scans. |

## QPS REST API (`/qps/rest/`)

| Registry name | API family | # tools (default / destructive) | Description |
|---|---|---|---|
| `assettags` | QPS | 4 / 5 | Search, create, update, and delete asset tags via the QPS AM API. |
| `cloudagent` | QPS | 5 / 6 | List and manage Qualys Cloud Agents, activation keys, and config profiles. |
| `hostassetam` | QPS | 5 / 5 | Read-only search/fetch over the QPS Asset Management (AM) inventory. |
| `wasauth` | QPS | 4 / 5 | Search, inspect, and manage WAS web application authentication records. |
| `wasfindings` | QPS | 4 / 4 | Search WAS findings (vulnerabilities/sensitive content/info gathered) and manage their status. |
| `wasreports` | QPS | 3 / 4 | Search, generate, download, and delete WAS reports. |
| `wasscans` | QPS | 5 / 6 | Search, launch, monitor, and manage WAS scans. |
| `wasschedules` | QPS | 4 / 5 | Search, inspect, and manage WAS recurring scan schedules. |
| `waswebapps` | QPS | 5 / 6 | Search, inspect, and manage WAS Web Application assets. |

## Gateway / JWT API

| Registry name | API family | # tools (default / destructive) | Description |
|---|---|---|---|
| `certview` | Gateway | 5 / 5 | Read-only search and inspection of the CertView certificate inventory. |
| `cloudviewconnectors` | Gateway | 7 / 8 | Manage TotalCloud/CloudView cloud connectors (AWS, Azure, GCP). |
| `cloudviewposture` | Gateway | 7 / 7 | Query TotalCloud/CloudView controls, evaluations (posture), and resources. |
| `cloudviewremediation` | Gateway | 4 / 4 | List, inspect, and trigger TotalCloud/CloudView remediation, and manage rules. |
| `complianceframeworkreports` | Gateway | 8 / 8 | Build and retrieve mandate/framework-based Policy Compliance (PC) reports. |
| `csam` | Gateway + QPS | 7 / 7 | Search/inspect the CSAM asset inventory and manage user-defined asset tags. |
| `cscontainers` | Gateway | 4 / 5 | List, inspect, and manage Container Security container assets. |
| `csimages` | Gateway | 4 / 5 | List, inspect, and manage Container Security image assets. |
| `cspolicies` | Gateway | 4 / 5 | List, inspect, and manage Container Security (centralized) policies. |
| `csregistries` | Gateway | 5 / 6 | List, inspect, configure, and scan Container Security registries. |
| `cssensors` | Gateway | 2 / 3 | List, inspect, and delete deployed Container Security sensors. |
| `easm` | Gateway | 5 / 5 | List/search external assets and attack surface findings; drive discovery. |
| `edr` | Gateway | 3 / 5 | Search EDR events/assets and perform response actions on endpoints. |
| `fim` | Gateway | 8 / 8 | List FIM events/incidents/profiles and create/approve incidents. |
| `gav` | Gateway | 4 / 4 | Read-only Global AssetView asset inventory over the gateway API. |
| `patchmgmt` | Gateway | 11 / 12 | Search patches, inspect PM assets, and manage patch deployment jobs. |
| `pcaspolicies` | Gateway | 24 / 25 | Author Policy Compliance (PC) policies via the PCAS API, and browse the PCAS library. |
| `pcposture` | Gateway + FO | 4 / 4 | Retrieve Policy Compliance (PC) posture information. |
| `pcrs` | Gateway | 6 / 6 | Read policy posture in bulk via the PCRS (Posture Streaming) Gateway API. |

