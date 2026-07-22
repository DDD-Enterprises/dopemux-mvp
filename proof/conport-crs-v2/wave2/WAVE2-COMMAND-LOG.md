# Wave 2 Command Log

All recorded inspection containers used `--network none`, no mounts, overridden entrypoints, and no application startup.

| Step | Result | Secret-safe evidence |
| --- | --- | --- |
| Clean paired Build A and Build B | PASS | Distinct local tags and image IDs recorded in `WAVE2-APT-BUILD-A.json` and `WAVE2-APT-BUILD-B.json`; sanitized logs are represented by SHA-256 only. |
| Installed package capture | PASS | Deterministic `dpkg-query` rows captured immediately for both images. |
| Manual package capture | PASS | Deterministic `apt-mark showmanual` sets captured for both images. |
| Source and architecture inspection | PASS | Matching snapshot source definitions and `arm64` captured from both images. |
| Snapshot-only build-network validation | PASS | Sanitized logs contain `snapshot.debian.org` and no known mutable Debian host; installed source definitions match both images. |
