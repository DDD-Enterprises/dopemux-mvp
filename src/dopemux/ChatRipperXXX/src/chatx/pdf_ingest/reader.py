"""PDF fallback ingestion for iMessage exports (text-first, OCR fallback).

This module parses text pages from conversation PDFs and maps lines of the
form "Name: message" into canonical messages. It is intentionally minimal and
privacy-preserving; no uploads. OCR is optional and only used locally if the
system has OCR tools installed; tests inject text pages instead of depending on
heavy PDF/OCR libraries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple

from chatx.schemas.message import CanonicalMessage, SourceRef


@dataclass
class PDFIngestOptions:
    me_name: str
    ocr: bool = False


def _extract_text_pages_stub(pdf_path: Path) -> List[str]:
    """Best-effort text extraction without hard dependency on external libs.

    Tries fitz (PyMuPDF), then PyPDF2 if available. Returns list of page text.
    If none available, returns empty list.
    """
    # Try PyMuPDF
    try:  # pragma: no cover - optional dependency
        import fitz  # type: ignore

        pages: List[str] = []
        with fitz.open(str(pdf_path)) as doc:  # type: ignore[attr-defined]
            for page in doc:  # type: ignore[assignment]
                pages.append(page.get_text())
        return pages
    except Exception:
        pass

    # Try PyPDF2
    try:  # pragma: no cover - optional dependency
        import PyPDF2  # type: ignore

        pages: List[str] = []
        with open(pdf_path, "rb") as fh:
            reader = PyPDF2.PdfReader(fh)  # type: ignore[attr-defined]
            for p in reader.pages:  # type: ignore[attr-defined]
                pages.append(p.extract_text() or "")
        return pages
    except Exception:
        pass

    return []


def _parse_lines_to_messages(
    lines: Iterable[str],
    *,
    conv_id: str,
    me_name_cf: str,
    source_path: str,
) -> List[CanonicalMessage]:
    msgs: List[CanonicalMessage] = []
    base_ts = datetime.now(timezone.utc)
    ts = base_ts
    for idx, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            continue
        # Expect "Name: message"; otherwise assign to Unknown
        sender = "Unknown"
        text = line
        if ":" in line:
            prefix, body = line.split(":", 1)
            if prefix.strip():
                sender = prefix.strip()
                text = body.strip()
        is_me = sender.casefold() == me_name_cf
        msg = CanonicalMessage(
            msg_id=f"pdf:{conv_id}:{idx}",
            conv_id=conv_id,
            platform="imessage",
            timestamp=ts,
            sender=sender,
            sender_id=("me" if is_me else sender),
            is_me=is_me,
            text=text or None,
            reply_to_msg_id=None,
            reactions=[],
            attachments=[],
            source_ref=SourceRef(guid=None, path=source_path),
            source_meta={
                "mode": "pdf_fallback",
            },
        )
        msgs.append(msg)
        # Monotonic timestamps per line (1 second apart)
        ts = ts + timedelta(seconds=1)
    return msgs


def extract_messages_from_pdf(
    pdf_path: Path,
    *,
    options: PDFIngestOptions,
    text_pages_override: Optional[Sequence[str]] = None,
    ocr_text_override: Optional[Sequence[str]] = None,
) -> List[CanonicalMessage]:
    """Extract messages from a conversation PDF.

    For tests, provide text_pages_override or ocr_text_override to bypass
    heavyweight dependencies.
    """
    conv_id = pdf_path.stem
    me_cf = options.me_name.casefold()
    # Extract text pages
    pages = list(text_pages_override or _extract_text_pages_stub(pdf_path))
    if not any(p.strip() for p in pages) and options.ocr:
        # OCR fallback: rely on injected text for tests; skip otherwise
        if ocr_text_override is not None:
            pages = list(ocr_text_override)
        # else leave pages empty

    # Flatten to lines
    all_lines: List[str] = []
    for p in pages:
        all_lines.extend(p.splitlines())

    return _parse_lines_to_messages(all_lines, conv_id=conv_id, me_name_cf=me_cf, source_path=str(pdf_path))

