# Image Enrichment & Image Psychology (Local‑First, Append‑Only)

Status: Proposed | Owner: TBD | Last Updated: 2025‑09‑03 PT

Purpose
- Design a privacy‑safe, local‑first pipeline to understand images and fuse them with chat context.
- Emit machine‑readable enrichment sidecars without changing the canonical `Message` schema.
- Append an image‑specific psychology/relationships analysis using a dedicated VLM, mapped to `labels.yml`.
- Honor Policy Shield: local‑first by default, cloud optional and cloud‑safe only.

Scope
- Per‑image attachment enrichment; text pipeline remains unchanged.
- Sidecar: `image_enrichment.jsonl` (1 row per image attachment) as the primary artifact.
- Optional lightweight mirrors into `Message.source_meta.image.*` for quick lookups (local‑only fields).
- Append‑only: no changes to existing multi‑pass text enrichment pipeline/models.

Non‑Goals
- No cloud uploads of images or thumbnails by default.
- No face recognition (identification). Counting presence is allowed; optional blur flags are allowed.
- Do not alter the canonical `Message` schema.

Constraints & Privacy
- Local‑first models per ADRs; cloud only after Policy Shield preflight and explicit allow.
- EXIF GPS is never persisted; only `has_gps: true|false` in `source_meta.image`.
- No biometric identification; only non‑identifying attributes (e.g., faces.count) when needed.
- RFC‑7807 for error payloads; schemas validated in CI.

Pipeline (Per Image Attachment)
1) Stage A — Technical metadata
   - Read MIME/UTI, dimensions, EXIF, orientation.
   - Do not emit raw GPS; compute `has_gps: true|false` only.
   - HEIC/HEIF via `pillow-heif`.

2) Stage B — OCR (on‑image text)
   - Local OCR with Tesseract + preprocessing: grayscale → adaptive threshold → deskew → denoise.
   - Emit `ocr.text` (string), optional `ocr.spans[]` (boxes), and `ocr.langs[]`.

3) Stage C — Objects / Categories
   - Small, fast detector: YOLOv8‑s by default (YOLOv9 optional). Emit `objects[] = {label, conf, box}`.
   - Infer coarse `category`: photo | screenshot | document | whiteboard | meme | receipt | menu | other.
   - Optional segmentation (SAM) gated OFF by default.

4) Stage D — Caption & Attributes (VLM)
   - Local captioning for short, literal descriptions + single‑word tags.
   - Florence‑2 (OpenVINO/ONNX Runtime) as the default caption/grounding model.
   - Emit `caption.short`, `tags[]`, optional `nsfw_risk` (0–1, local only).

5) Stage E — Similarity & Retrieval
   - Perceptual hash (pHash/dHash/aHash) for near‑dupes.
   - OpenCLIP embeddings for semantic retrieval (kept local; store an opaque handle in sidecar).

6) Stage F — Context Fusion
   - Join image semantics with nearby chat context (±5 min / ±N turns), sender, thread, day.
   - Emit compact `context_hints` (e.g., `{prev_text:[], participants:[]}`) for later Q&A.

7) Stage G — Image Psychology & Relationships (Append‑Only Feature)
   - New, image‑specific psychological inference mapped to `labels.yml` (see Model Choices and JSON schema below).
   - This is a separate module and sidecar fields; the existing text 4‑pass pipeline is unchanged.

Sidecar: `image_enrichment.jsonl` (Primary Artifact)
```json
{
  "msg_id": "12345",
  "attachment_index": 0,
  "hash_sha256": "…",
  "ocr": {"text": "…", "langs": ["en"], "spans": [{"bbox":[x,y,w,h]}]},
  "objects": [{"label":"pizza","conf":0.91,"box":[…]}],
  "category": "document|screenshot|photo|…",
  "caption": {"short":"Two pizzas on a table"},
  "tags": ["food","pepperoni","indoor","evening"],
  "faces": {"count": 2, "blurred": false},
  "similarity": {"phash": "f0e1…", "clip_vec": "<opaque-local-ref>"},
  "context_hints": {"prev_text":["here's the menu"], "participants":["ME","CN_7"]},
  "nsfw_risk": 0.01,
  "psych": {
    "coarse_labels": ["support","conflict","communication"],
    "fine_labels_local": ["anxious_attachment"],
    "emotion_hint": "neutral",
    "interaction_type": "argument|apology|request|other",
    "power_balance": 0.1,
    "boundary_health": "clear|blurred|violated|rigid|none",
    "confidence": 0.78,
    "provenance": {"schema_v":"1","run_id":"…","model_id":"qwen2.5-vl-7b-instruct","prompt_hash":"…","source":"local"}
  },
  "provenance": {"schema_v":"1", "run_id":"…", "model_id":"florence2-base", "prompt_hash":"…", "source":"local"}
}
```

Model Choices (Append‑Only Image Psychology)
- Default (image psychology): Qwen2.5‑VL (≈7B instruct)
  - Rationale: Strong visual reasoning and VQA; effective at social/interaction inference beyond literal captioning; open weights; viable local quantization.
  - Role: Psychological/relationship inference from images using JSON‑locked prompts.
- Complementary (caption/grounding): Florence‑2
  - Rationale: Lightweight, promptable caption/detection/grounding; good local performance; used for literal descriptions and tags.
- Alternatives (optional):
  - LLaVA‑NeXT (7B class) — widely used, solid reasoning, local‑friendly.
  - InternVL 2.5 — strong vision backbone, heavier footprint; enable only if GPU headroom exists.
- Determinism: temp 0.1, top_p 0.9, fixed seed, small max tokens; strict JSON schema.

Label Taxonomy Integration (labels.yml)
- Normalize → validate → co‑occurrence → split: 
  - Use `LabelTaxonomy.normalize_label`, `validate_labels`, `apply_co_occurrence_rules`.
  - Split results into `coarse_labels` (cloud‑safe) and `fine_labels_local` (LOCAL‑ONLY).
- Cloud safety: Only `coarse_labels` are eligible for any optional cloud escalations; `fine_labels_local` remain on device.
- Polarity and scoring: derive from taxonomy where available; store model confidence.

JSON‑Locked Prompt (Image Psychology)
- System: “You are a vision model. Produce valid JSON only; no prose.”
- User template:
  ```
  TASK: Infer high‑level social and psychological signals from the attached image.
  RULES: No identity or biometric inferences; be conservative; if unsure choose neutral/none.
  CONTEXT (optional): nearby text within ±5 min: {…}
  OUTPUT_JSON_SCHEMA:
  {"coarse_labels":[string],"fine_labels_local":[string],"emotion_hint":"joy|anger|fear|sadness|disgust|surprise|neutral",
   "interaction_type":"collaboration|argument|planning|apology|request|celebration|other",
   "power_balance":number,"boundary_health":"clear|blurred|violated|rigid|none","confidence":number}
  IMAGE: <attached>
  ```

Append‑Only Integration (No Changes to Text Pipeline)
- New modules under `src/chatx/image_enrich/` (image‑only path):
  - `ocr.py`, `detect.py`, `caption.py`, `similarity.py`, `context.py`, `psych.py`, `writer.py`.
  - `psych.py` loads Qwen2.5‑VL for the JSON‑locked psychology task.
- Hook: run after attachment copy/thumbnail for `type=="image"`; write/update `image_enrichment.jsonl` row.
- Text multi‑pass enrichment (entities/structure/psychology/relationships) remains unchanged.

Test Strategy (TDD, Tiny Diffs)
- Add `schemas/image_enrichment.schema.json` with `psych` object and provenance.
- Tests under `tests/image_enrich/`:
  - Schema tests: every sidecar row validates.
  - OCR/doc/screenshot fixtures produce expected signals (non‑empty OCR or caption).
  - Psychology test: mocked VLM returns stable JSON; labels map via taxonomy; cloud safety enforced (coarse vs fine).
  - Run report counters: `{images_ocr_ok, images_ocr_empty, objects_detected, nsfw_flags}` increment as expected.
- CI gates: `ruff`, `mypy`, `pytest --cov=src --cov-fail-under=60` (target ≥90% for new modules), schema validation in tests.

Acceptance Criteria
- AC‑IMG‑ENR‑1: For an on‑disk image attachment, emit one `image_enrichment.jsonl` row with non‑empty `caption.short` or `ocr.text`; row validates.
- AC‑IMG‑ENR‑2: If EXIF GPS exists, only `has_gps=true` is recorded (no coordinates anywhere).
- AC‑IMG‑ENR‑3: Screenshot fixture → `category="screenshot"` and `ocr.text` contains ≥80% expected tokens.
- AC‑IMG‑ENR‑4: Doc‑photo fixture → `objects[]` includes `document|paper` and OCR has ≥1 line.
- AC‑IMG‑ENR‑5: Near‑duplicates → `similarity.phash` Hamming distance ≤ 6 and identical CLIP‑NNs.
- AC‑IMG‑ENR‑6: Provenance fields present for each stage; run report increments image counters.
- AC‑IMG‑ENR‑7: No biometric identification fields; only `faces.count` and optional blur flag.
- AC‑IMG‑PSY‑1: Image psychology produces `psych.coarse_labels` mapped to taxonomy; `fine_labels_local` remain local‑only; validates.
- AC‑IMG‑PSY‑2: Confidence ∈ [0,1]; `emotion_hint` ∈ allowed enums; `boundary_health` valid.
- AC‑IMG‑PSY‑3: Policy Shield: any optional cloud flow only receives `coarse_labels` and non‑sensitive fields.

Observability
- Add counters to `run_report.json`: `{images_ocr_ok, images_ocr_empty, objects_detected, nsfw_flags}`.
- Track per‑stage timing and success/fail counts in logs and optional metrics.

Open Questions (Pending Exa Research)
- Benchmark confirmation: Qwen2.5‑VL vs LLaVA‑NeXT vs InternVL 2.5 on social/psych reasoning tasks (MMBench‑Reasoning/MMMU, social relation datasets).
- Packaging and quantization guidance for local inference (7B class) across CPU‑only vs consumer GPUs.
- Optional SAM integration value for psychology (likely low benefit vs cost; confirm).

Next Actions (Micro‑PRs)
1) feat(image): ocr+tesseract runner — CPU OCR with preprocessing; sidecar scaffold; tests.
2) feat(image): detector (yolov8) + categories — label objects; screenshot/document heuristics; tests.
3) feat(image): captioner (florence‑2 local) — JSON prompt; tests.
4) feat(image): perceptual hash + clip embeddings — similarity; tests.
5) feat(image): context joiner — fuse with ±5‑minute window text; tests.
6) chore(ci): schema + run_report counters — add `image_enrichment.schema.json`; CI validation; tests.
7) feat(image): psychology (qwen2.5‑vl) — append‑only psych block; labels.yml mapping; strict JSON; tests (model mocked).

Notes
- This document consolidates the planned image pipeline and the append‑only image psychology feature without altering the existing text enrichment pipeline/models. When network tooling (Exa) is enabled, run the outlined research queries to finalize the model choice with citations and update this spec (and an ADR if design shifts).
