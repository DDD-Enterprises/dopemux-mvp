"""Local transcription using faster-whisper (CTranslate2).

This module is optional. If faster-whisper is not installed, importing or
calling transcribe will raise ImportError, allowing callers to fall back.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class FWConfig:
    model: str = "small"
    compute_type: str = "int8"  # choices: "int8", "int8_float16", "float16", etc.
    device: str = "cpu"  # or "cuda"
    beam_size: int = 5
    vad: bool = False
    chunk_seconds: int = 30
    chunk_overlap_seconds: int = 5


def transcribe(audio_file_path: Path, cfg: Optional[FWConfig] = None) -> Optional[Dict[str, str]]:
    """Transcribe via faster-whisper if available.

    Returns dict with transcript, engine, and confidence estimate, or None.
    """
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception as e:  # pragma: no cover - triggered when package missing
        raise ImportError("faster-whisper not available") from e

    cfg = cfg or FWConfig()
    model = WhisperModel(cfg.model, device=cfg.device, compute_type=cfg.compute_type)

    # For simplicity, use built-in transcribe; chunking/VAD can be added with
    # manual splits if needed. We still provide a beam size.
    segments, info = model.transcribe(str(audio_file_path), beam_size=cfg.beam_size)

    text_parts = []
    conf_scores = []
    for seg in segments:
        # seg has .text and possibly .avg_logprob, .no_speech_prob
        if getattr(seg, "text", None):
            text_parts.append(seg.text)
        ns = getattr(seg, "no_speech_prob", None)
        if isinstance(ns, (int, float)):
            conf_scores.append(1.0 - float(ns))

    transcript_text = " ".join(part.strip() for part in text_parts).strip()
    if not transcript_text:
        return None

    if conf_scores:
        avg_conf = sum(conf_scores) / len(conf_scores)
        if avg_conf > 0.8:
            confidence = "high"
        elif avg_conf > 0.5:
            confidence = "medium"
        else:
            confidence = "low"
    else:
        confidence = "unknown"

    return {
        "transcript": transcript_text,
        "engine": f"whisper-fast-{cfg.model}",
        "confidence": confidence,
    }

