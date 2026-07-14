"""One-shot diagnostic: dump Qualys rate-limit / concurrency headers.

Makes exactly two GET calls (about.php + one small list) and prints every
rate-limit / concurrency response header plus status, so we can see the real
per-account limits and tune the audit pacing. Read-only, minimal footprint.
"""

import sys

from qualys_mcp.client import QualysClient
from qualys_mcp.config import QualysConfig


def _dump(label: str, resp) -> None:
    print(f"\n[{label}] HTTP {resp.status_code}")
    for k, v in resp.headers.items():
        kl = k.lower()
        if "ratelimit" in kl or "concurrency" in kl or kl in ("retry-after",):
            print(f"    {k}: {v}")
    if resp.status_code >= 400:
        print("    body:", resp.text[:300].replace("\n", " "))


def main() -> int:
    cfg = QualysConfig.from_env(console_label="diag")
    cfg.require_credentials()
    c = QualysClient(cfg)
    auth = (cfg.username or "", cfg.password or "")
    hdr = {"X-Requested-With": "qualys-mcp"}

    r1 = c.http.get(f"{cfg.api_url}/msp/about.php", auth=auth, headers=hdr)
    _dump("about.php", r1)

    r2 = c.http.get(
        f"{cfg.api_url}/api/2.0/fo/asset/group/",
        params={"action": "list", "truncation_limit": "1"},
        auth=auth,
        headers=hdr,
    )
    _dump("asset/group list", r2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
