# Qualys MCP — Build Summary

Status as of the offline build (pre‑go‑live). Live verification against the two
consoles happens once API‑user credentials + POD are provided.

## Result
- **59 modules**, **360 tools** by default / **403** with `QUALYS_ENABLE_DESTRUCTIVE=true`
  (43 destructive tools, all confirm‑guarded and hidden by default).
  (Counts include the Wave‑4 backlog closure: report‑template CRUD, scan‑schedule
  run‑history, KnowledgeBase reset, Accept‑EULA + admin password‑change, JSON‑body
  fix for change_login_password, and 20 additional typed auth‑record tools.)
- Three API regimes behind one client: **31 FO**, **9 QPS**, **19 Gateway** (a few span two).
- `ruff` clean; **18 tests** pass (foundation + all‑module smoke + per‑regime).
- No duplicate tool names; every tool `qualys_`‑prefixed; lazy auth (`--check` works offline).

## How it was built (waves)
- **Wave 0** — foundation (client/auth/registry/server/base/safety/ops scripts), by the orchestrator.
- **Wave 1** — 8 parallel builder agents (FO/QPS clusters).
- **Wave 2** — 4 of those agents resumed for Gateway/JWT modules (no new spawns).
- **Wave 3** — 3 fresh audit agents (coverage/gap, safety+fixes, tests+docs).
- Total: **11 agent spawns** (within the 15 cap), orchestrator owning all shared files.

## Audit artifacts (in `docs/`)
- `MODULE_INDEX.md` — every module, family, tool counts, description.
- `COVERAGE_MATRIX.md` — module × tool table vs the VM/PC PDF, with cited gaps.
- `SAFETY_AUDIT.md` — destructive‑gating verification (39/39 pass).
- `VERIFICATION_CHECKLIST.md` — 256 `TODO(verify)` markers grouped by module for go‑live.

## Known coverage gaps — status after Wave 4
- Scan‑schedule **run‑history** (VM + Compliance) — **CLOSED**.
- **Report Template CRUD** (Scan/PCI/Patch/Map create/update/delete) — **CLOSED**
  (the API documents no `import` action, so none was added).
- **KnowledgeBase** `action=reset` — **CLOSED** (`reset_vulnerability`).
- **Users** Accept‑EULA + admin batch password‑change — **CLOSED**.
- **Auth records**: 21 technology types now have dedicated typed tools; the
  remaining ~17 types are fully usable via the generic
  `create_auth_record(record_type=..., extra_params=...)` passthrough (by design).

## Correctness items to confirm at go‑live (highest priority)
- `users.change_login_password` — **FIXED** (JSON body per PDF pp.1873‑74); confirm live.
- QPS/Gateway base paths for `was_schedules`, `host_asset_am`, `cloud_agent`, `patch_mgmt`
  (`/pm/v1` vs `/pm/v3`), `fim`, `easm` — built from docs research, verify live.
- GAV/CSAM filter body (JSON vs XML `<FilterRequest>`) — client supports both; pick per live.

## Go‑live steps (needs user: API‑user creds + POD per console)
1. `.\encrypt-qualys-creds.ps1 -Console consulting -Platform <POD>`
2. `.\encrypt-qualys-creds.ps1 -Console cloud -Platform <POD>`
3. `.\start-qualys-mcp.ps1`  (add `-EnableDestructive cloud` only when intended)
4. Run the live read‑only audit (connectivity + read tools per module, per console).
5. `.\register-qualys-mcp-task.ps1` for persistence.
