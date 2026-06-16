# Secret Risk Report

generated_at_utc=2026-06-16T06:14:59Z

This final zip includes Pack 5 manifest metadata/reports plus the preserved `gpt55_recon_source` prompt packet. It does not include large recon archives, repo source trees, or secret files.

Do not attach .env files, raw credentials, tunnel secrets, local auth stores, provider tokens, or interpolated compose config.

Known risk notes:
- Pack 2 repo-wide pytest is blocked due unexpected external HTTPS activity.
- Pack 4 ECC archive was produced from a third-party repository static clone; review before forwarding outside the trusted workflow.
- The preserved source recon pack contains formatting corruption and should be treated as raw input, not clean canonical markdown.
