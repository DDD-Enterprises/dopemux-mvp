# How-To: PDF Fallback Ingestion (iMessage)

Ingest conversation PDFs when the database isn’t available.

## Command
```bash
chatx imessage pdf --pdf ./conversation.pdf --me "Your Name" --out ./out
```

## OCR Fallback
- If the PDF has no text layer, enable OCR:
  ```bash
  chatx imessage pdf --pdf ./img_only.pdf --me "Your Name" --ocr --out ./out
  ```
- OCR runs locally (when configured); otherwise ingestion is text-first only.

## Output
- `out/messages_<pdf_name>.json`, with `source_meta.mode="pdf_fallback"` for provenance.

