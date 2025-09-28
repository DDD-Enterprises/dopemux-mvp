from __future__ import annotations

from pathlib import Path

from chatx.pdf_ingest.reader import PDFIngestOptions, extract_messages_from_pdf


def test_pdf_text_first_parsing(tmp_path: Path) -> None:
    pdf = tmp_path / "chat.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%...stub...")
    text_pages = [
        "Me: Hello there\nFriend: Hi!\nMe: How are you?",
    ]
    messages = extract_messages_from_pdf(
        pdf,
        options=PDFIngestOptions(me_name="Me", ocr=False),
        text_pages_override=text_pages,
    )
    assert len(messages) == 3
    assert messages[0].sender == "Me" and messages[0].is_me is True
    assert messages[1].sender == "Friend" and messages[1].is_me is False
    assert messages[0].platform == "imessage"
    assert messages[0].source_meta.get("mode") == "pdf_fallback"


def test_pdf_ocr_fallback_injection(tmp_path: Path) -> None:
    pdf = tmp_path / "chat.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%...stub...")
    # No text pages; supply OCR fallback lines
    ocr_pages = [
        "Friend: Photo caption\nMe: Looks great!",
    ]
    messages = extract_messages_from_pdf(
        pdf,
        options=PDFIngestOptions(me_name="Me", ocr=True),
        text_pages_override=[],
        ocr_text_override=ocr_pages,
    )
    assert len(messages) == 2
    assert any(m.is_me for m in messages)
    assert all(m.source_meta.get("mode") == "pdf_fallback" for m in messages)

