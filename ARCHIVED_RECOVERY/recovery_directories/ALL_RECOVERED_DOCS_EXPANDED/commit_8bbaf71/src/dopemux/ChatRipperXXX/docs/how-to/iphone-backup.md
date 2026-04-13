# How-To: iMessage from iPhone Backup

This guide shows how to extract iMessage from a Finder/iTunes backup.

## Path
- macOS backups live under: `~/Library/Application Support/MobileSync/Backup/<UDID>`

## Steps
1. Ensure the backup exists (unencrypted or know the password).
2. Grant Full Disk Access to your terminal app (System Settings → Privacy & Security → Full Disk Access).
3. Run:
   ```bash
   chatx imessage pull \
     --contact "+15551234567" \
     --from-backup "~/Library/Application Support/MobileSync/Backup/<UDID>" \
     --out ./out
   ```

## Notes
- If the backup is encrypted, ChatX prompts for the password. We do not bypass encryption.
- Outputs:
  - `out/messages_<contact>.json`
  - `out/missing_attachments.json` (if attachments were included and some are missing)
  - `out/run_report.json`, `out/metrics.jsonl`

