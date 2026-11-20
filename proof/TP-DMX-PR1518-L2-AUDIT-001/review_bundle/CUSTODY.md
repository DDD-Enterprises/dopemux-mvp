# Off-repo custody

Read-only originals kept outside the public repo:

| File | sha256 |
|---|---|
| `~/.local/share/dopemux/evidence/pr1518/r1/custody/GROK_OUTPUT_RAW.jsonl` | `703dc4d9d42a29d02e44b893cf8a78728e361c07fe2423fadd6dd1e574f8a75e` |
| `~/.local/share/dopemux/evidence/pr1518/r1/custody/GROK_TOOL_PROBE_RAW.jsonl` | `0f6ea97761f98bbdc0d12d0e5c166efb4c7d5d8393b47b0e69d6d5499cb57686` |
| `~/.local/share/dopemux/evidence/pr1518/r1/custody/cli-20261119_210803.log` | `6f550cd7d922a3ee8cdd67e765e16169434838264a04a044eeb00b2c142c99cb` |
| `~/.local/share/dopemux/evidence/pr1518/r1/custody/e16290c6-dd8a-4697-9c13-914f5dca4b2a.db` | `1a1b2444031fbda6b0bcce27957f4e1b2406b671a5146d62a872fd5fbc56b8af` |
| `~/.local/share/dopemux/evidence/pr1518/r1/custody/parse_probe.py` | `936aaf33b05be61d021fd27b11f21fe611238d9aef34e5fb56327fef1224a88c` |

Live-read evidence. It holds real task titles and host paths, so it is not in this public bundle:

| File | sha256 |
|---|---|
| `~/.local/share/dopemux/evidence/pr1518/live/SUMMARY.md` | `0ac301d7610589ebb1ca7fe4617ae49fee420ee76218a61434cb1ed9f78c41d9` |
| `~/.local/share/dopemux/evidence/pr1518/live/baseline_before_switch.meta.txt` | `11db0e2ce71ba49e53259f817ffd30a44321efb78626edf3277dd613440a5072` |
| `~/.local/share/dopemux/evidence/pr1518/live/baseline_before_switch.response.json` | `f01e3855292256f608b8acb8c369ed44998ffc82e6fbef83c57441f3dc08649c` |
| `~/.local/share/dopemux/evidence/pr1518/live/baseline_before_switch.server.log` | `a1650ed7ce9783479f5addaf622f6101a6ba3248697b44a7cef82fbd5b060743` |
| `~/.local/share/dopemux/evidence/pr1518/live/cockpit_task_queue_ok_2026-11-19.jpg` | `e77f3e5c7fd0c86e7998e3a07c108f3c710c06444a31b93858180b81456fbb51` |
| `~/.local/share/dopemux/evidence/pr1518/live/ok_read_after_switch.meta.txt` | `4cffa913ff5fa9dcbd629630c0d5466ea5d549cca91a46503e87ae182e97e9e6` |
| `~/.local/share/dopemux/evidence/pr1518/live/ok_read_after_switch.response.json` | `7ecb3ae63b39d60a301b0475451729fd8f4a10107369b380b882ac262db6b7fc` |
| `~/.local/share/dopemux/evidence/pr1518/live/ok_read_after_switch.server.log` | `a1650ed7ce9783479f5addaf622f6101a6ba3248697b44a7cef82fbd5b060743` |
| `~/.local/share/dopemux/evidence/pr1518/live/ok_read_at_df8b6bc5d.meta.txt` | `f814efac3b9807e0c8857295b394bba01b7187eaff9f72329db72acdbe4418e3` |
| `~/.local/share/dopemux/evidence/pr1518/live/ok_read_at_df8b6bc5d.response.json` | `9a905069035acfcbd94ea66eef68506c3cf46ea87542f76cd4f5ce840311c558` |
| `~/.local/share/dopemux/evidence/pr1518/live/ok_read_at_df8b6bc5d.server.log` | `a1650ed7ce9783479f5addaf622f6101a6ba3248697b44a7cef82fbd5b060743` |
| `~/.local/share/dopemux/evidence/pr1518/live/run_read.sh` | `dea801be405636dc17c19c24ee50895e60307682214cc54d2b6482b298171dc3` |
| `~/.local/share/dopemux/evidence/pr1518/live/supervisor_read_at_audited_head_df8b6bc5d.meta.txt` | `41d9795fd5ad2e147a678281b97ac21d73a5a08c780f125bb6ef98c1ebf3d54e` |
| `~/.local/share/dopemux/evidence/pr1518/live/supervisor_read_at_audited_head_df8b6bc5d.response.json` | `39fb9cefe67eb0f215f125297dc088d5e3a7ff547905bb563fb469bf61be8b58` |
| `~/.local/share/dopemux/evidence/pr1518/live/supervisor_read_at_audited_head_df8b6bc5d.server.log` | `a1650ed7ce9783479f5addaf622f6101a6ba3248697b44a7cef82fbd5b060743` |

The sealed-run dirs `r1/agy/` and `r1/grok/` held only `AUDIT_PROMPT.txt` (same sha256 as this bundle's copy).
