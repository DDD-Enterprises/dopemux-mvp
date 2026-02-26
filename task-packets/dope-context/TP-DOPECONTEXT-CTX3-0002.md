# Task Packet: TP-DOPECONTEXT-CTX3-0002 · Dope-Context · Grouped Docs Invariants

## Objective
Enforce fail-closed grouped-by-document indexing invariants for docs embeddings.

## Scope
IN:
- `/Users/hue/code/dopemux-mvp/services/dope-context/src/pipeline/docs_pipeline.py`
- `/Users/hue/code/dopemux-mvp/services/dope-context/src/preprocessing/document_processor.py`
- `/Users/hue/code/dopemux-mvp/services/dope-context/src/embeddings/contextualized_embedder.py`
- `/Users/hue/code/dopemux-mvp/services/dope-context/tests/test_docs_pipeline_invariants.py`

OUT:
- Query-side routing behavior

## Acceptance
- Non-contiguous ordinals fail closed.
- Embedding-count mismatch fails closed with no partial upsert.
