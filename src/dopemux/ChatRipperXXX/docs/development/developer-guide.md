Developer Guide

Status: Draft | Owner: You | Last Updated: 2025-09-02 PT

Setup
	•	Python 3.11+.
	•	uv or pip to install.
	•	Optional local LLM via Ollama (e.g., gemma:2-9b-q4_K_M).
	•	Copy .env.example to .env (do not commit). Cloud disabled by default.

Running the Pipeline (Extraction)
1.	iMessage (local DB): `chatx imessage pull --contact "<id>" --db ~/Library/Messages/chat.db --out ./out`
2.	iMessage (iPhone backup): `chatx imessage pull --contact "<id>" --from-backup "~/Library/Application Support/MobileSync/Backup/<UDID>" --out ./out`
3.	Instagram (official ZIP): `chatx instagram pull --zip ./instagram.zip --user "<Your Name>" --out ./out`

Full Disk Access (FDA)
- On macOS, grant Full Disk Access to your terminal: System Settings → Privacy & Security → Full Disk Access → enable for your terminal app. This allows reading `~/Library/Messages/chat.db` and `~/Library/Messages/Attachments/**`.

CLI Examples
- Metadata only: `chatx imessage pull --contact "+15551234567" --out ./out`
- Include attachments: `chatx imessage pull --contact "friend@example.com" --include-attachments --out ./out`
- Copy binaries: `chatx imessage pull --contact "friend@example.com" --include-attachments --copy-binaries --out ./out`
- Transcribe voice notes locally: `chatx imessage pull --contact "friend@example.com" --include-attachments --transcribe-audio local --out ./out`
 - Backup mode (read-only sms.db): `chatx imessage pull --contact "<id>" --from-backup "~/Library/Application Support/MobileSync/Backup/<UDID>" --out ./out`
 - Backup mode + transcription without copying: `chatx imessage pull --contact "<id>" --from-backup "<BackupPath>" --include-attachments --transcribe-audio local --out ./out`
 - Backup mode + copy binaries: `chatx imessage pull --contact "<id>" --from-backup "<BackupPath>" --include-attachments --copy-binaries --out ./out`
 - Instagram (author filter): `chatx instagram pull --zip ./instagram.zip --user "Your Name" --author-only "FriendA" --out ./out`

Artifacts
- Messages: `out/messages_<contact>.json`
- Missing attachments report: `out/missing_attachments_report.json`
- Quarantine (invalid messages): `out/quarantine/messages_bad.jsonl`
- Run report (metrics): `out/run_report.json`

Backup Mode Notes
- Backups live under `~/Library/Application Support/MobileSync/Backup/<UDID>` on macOS. Use `--from-backup` to enable this path; if encrypted, pass `--backup-password`.
- Attachments in backups are stored as hashed fileIDs. The tool resolves them via `Manifest.db` and can:
  - transcribe audio directly (without `--copy-binaries`), or
  - copy to `out/attachments/**` with `--copy-binaries`.
  In both cases, no data is sent to cloud.

Perf Smoke
- Disabled by default. To run locally: `CHATX_RUN_PERF=1 pytest -m perf -q`
- Optional soft floor warning in CLI: set `CHATX_SOFT_FLOOR_MSGS_MIN=5000` to warn if throughput is below 5k msgs/min.
	2.	Transform: chatx transform --input ./out/raw/*.json --to jsonl --chunk turns:40 --stride 10 --contact CN_xxx
	3.	Redact: chatx redact --input ./out/chunks/*.json --pseudonymize --opaque --threshold 0.995 --salt-file ./salt.key --report ./out/redaction_report.json
	4.	Index: chatx index --input ./out/redacted/*.json --store chroma --collection chatx_<contact>
	5.	Query: chatx query "What changed after Feb?" --contact CN_xxx --since 2025-02-01 --k 32

Troubleshooting
	•	SQLite lock: ensure DB temp copy includes WAL; open read-only.
	•	Apple epoch drift: see IMESSAGE_SPEC.md.
	•	Determinism: disable streaming; fix seeds in config.
