# Security Policy

## Reporting a vulnerability

If you discover a security issue in Qualys MCP, please **do not open a public
issue**. Instead, report it privately via GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
on this repository (Security → Report a vulnerability). Include a description,
affected version/commit, and reproduction steps. Please allow reasonable time
for a fix before any public disclosure.

## Handling credentials (operator guidance)

This server talks to your Qualys subscription with a real API user. Treat it
accordingly:

- **Never commit credentials.** `.env*`, `.secrets/`, `*.dat`, `logs/`, and
  `reports/` are git‑ignored. Keep it that way.
- **Prefer a dedicated, least‑privilege API user** scoped to only the modules
  you use (`QUALYS_MCP_MODULES`).
- On Windows, credentials are stored as **DPAPI‑encrypted, user‑scoped blobs**
  under `.secrets/` (via `encrypt-qualys-creds.ps1`). On other platforms,
  provide them through environment variables from your own secret store — never
  hard‑code them.
- **Bind to localhost.** The HTTP transport defaults to `127.0.0.1`. If you must
  expose it, put it behind an authenticated reverse proxy and set
  `QUALYS_MCP_API_KEY`.
- **Keep destructive tools off by default.** `QUALYS_ENABLE_DESTRUCTIVE` should
  be `true` only on consoles where you intend to run deletes/purges, and every
  destructive call still requires an explicit confirmation token.

## Scope

This project is an independent API client. Vulnerabilities in the Qualys
platform itself should be reported to Qualys directly.
