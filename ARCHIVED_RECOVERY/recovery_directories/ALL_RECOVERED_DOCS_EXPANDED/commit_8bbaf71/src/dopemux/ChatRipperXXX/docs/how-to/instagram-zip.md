# How-To: Instagram Official Data ZIP

Parse Instagram DMs from the official “Download your information” ZIP export.

## Command
```bash
chatx instagram pull --zip ./instagram.zip --user "Your Name" --out ./out
```

## Filters
- `--user` (required): your display name; filters threads and marks `is_me`.
- `--author-only <name>`: restricts to messages authored by the named user(s).

## Safety
- Prevents path traversal (Zip Slip) and does not upload media; references only.

## Output
- `out/instagram_messages.json` (canonical Message JSON)

