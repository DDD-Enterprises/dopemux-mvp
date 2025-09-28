**Title:** Image Psychology Model — Research Plan
**Status:** Draft | Owner: TBD | Last Updated: 2025-09-03 PT

Objective
- Select a local-first, privacy-safe VLM to infer social/relationship and psychological signals from images, mapped to labels.yml, as an append-only feature alongside the existing text pipeline.

Key Questions
- Which open VLM best infers interaction type, emotion hints, power balance, boundary health from images?
- How stable and deterministic are outputs under JSON-locked prompts and low temperature?
- What are compute/memory footprints (CPU-only fallback vs consumer GPU), quantization options, and cold-start latencies?
- How safely can we constrain outputs (no biometric identification; conservative failure modes)?

Candidates
- Qwen2.5-VL (7B instruct) — strong reasoning/VQA, open weights, good local viability.
- LLaVA-NeXT (7B class) — robust instruction following, wide adoption.
- InternVL 2.5 — strong vision backbone; larger footprint.
- Baseline complement: Florence-2 for literal caption/grounding (kept regardless of psych model choice).

Datasets & Fixtures
- Project fixtures: screenshots, document photos, casual photos (ensure no PII faces close-up; blur if needed).
- Public benchmarks (for relative signals; qualitative):
  - MMBench-Reasoning/MMMU/MME: general reasoning.
  - Social Relationship Detection (e.g., PISC/VSRD-like samples) for qualitative checks.
  - Visual commonsense (e.g., VisualCOMET-like tasks) where permissible.

Evaluation Dimensions
- Psychological/Relational Inference (Primary):
  - Emotion hint alignment (neutral/joy/anger/sadness/fear/surprise/disgust).
  - Interaction type (argument/apology/request/etc.).
  - Power balance estimate (sign and relative magnitude stability).
  - Boundary health (clear/blurred/violated/rigid/none).
  - Mapping to labels.yml via normalize→validate→co-occurrence→split.
- Determinism & Robustness:
  - JSON validity rate (% valid parses over 50 prompts).
  - Stability under seed/temp=0.1; prompt perturbations (± synonyms) — label set Jaccard similarity.
- Performance:
  - Cold start time; p95 latency per image; throughput on 1x consumer GPU; CPU-only fallback feasibility (reduced prompt budget).
- Footprint & Ops:
  - VRAM/RAM usage at chosen quant; model weight size; ONNX/OpenVINO paths available.
- Privacy Safety:
  - False identity/biometric inferences rate (should be 0 with guardrails wording); conservative “none/neutral” fallback frequency.

Methodology
1) Prompt Design:
   - JSON-only, strict schema: {coarse_labels, fine_labels_local, emotion_hint, interaction_type, power_balance, boundary_health, confidence}.
   - Deterministic settings: temp 0.1, top_p 0.9, fixed seed, small max tokens.
   - Inject optional nearby text (±5 min) as context.
2) Trials:
   - For each candidate, run N=50 images across categories (people, objects, documents, screenshots).
   - Record JSON validity, outputs, and latency.
3) Scoring:
   - Weighted composite: Psych inference 40%, Determinism 20%, Performance 20%, Footprint/Ops 10%, Privacy Safety 10%.
4) Analysis:
   - Aggregate metrics; qualitative review of 10 representative cases per model.
   - Map labels through labels.yml; compute coarse vs fine split counts and co-occurrence enrichment rates.
5) Decision:
   - Choose default psych model; document trade-offs; update spec and add ADR if approach shifts materially.

Exa Research Queries (run when network enabled)
- "best open-source VLM for social scene understanding 2024 2025 benchmark"
- "visual social relationship detection SOTA 2024 benchmark mAP"
- "VLM Theory of Mind image tasks comparison LLaVA Qwen InternVL 2025"
- "Qwen2.5-VL social reasoning examples"
- "InternVL 2.5 reasoning MMBench MMMU results"

Deliverables
- Model comparison table + composite scores.
- Short memo recommending default and alternatives, with config guidance (quant, hardware).
- Prompt template (JSON-locked) and guardrails text.
- Test artifacts: schema validation logs, stability metrics, latency stats.
- If design shifts: ADR referencing this plan and results.

Timeline (indicative)
- Day 1: Finalize prompts, assemble fixtures, wire evaluation harness (mocks for CI).
- Day 2–3: Run trials for 2–3 models; collect metrics.
- Day 4: Analysis + recommendation memo; update docs/spec/ADR.

Append-Only Integration Plan
- Keep existing text multi-pass enrichment untouched.
- Add image-only psych module and sidecar fields per spec; all local-first; policy shield ensures cloud-safe handling of coarse labels only.

