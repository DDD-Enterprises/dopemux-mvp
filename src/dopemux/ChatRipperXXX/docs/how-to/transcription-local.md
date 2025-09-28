# How-To: Local Transcription Setup

Configure local transcription for iMessage voice notes.

## Engines
- Default: faster-whisper (CTranslate2) if installed; falls back to classic whisper; tests use a mock engine.

## Install (optional)
```bash
pip install faster-whisper
```

## Use
```bash
chatx imessage pull --contact "+15551234567" --include-attachments --transcribe-audio local --out ./out
```

## Tuning (env)
- `CHATX_STT_ENGINE=whisper-fast` (default when local)
- `CHATX_STT_MODEL=small-int8` (default)
- `CHATX_STT_DEV=cpu|cuda`
- `CHATX_STT_CACHE_DIR=~/.cache/chatx/models`

See ADR-0017 for SLAs and guidance.

