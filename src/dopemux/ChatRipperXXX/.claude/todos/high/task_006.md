## Task: Integrate local Stella-1.5B-v5 embedding provider with memory optimization
- **ID**: 20250906-185622
- **Priority**: High
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [5], [4]

### Description
Add a local SOTA provider for Stella-1.5B-v5 with FP16/4-bit options, async lazy load, and standardized output.

### Implementation Details
Implementation:
- Model sourcing: configure via settings.model_ids['stella'] to the correct HF repo for Stella-1.5B-v5
- Load path options:
  1) sentence-transformers API if the repo is ST-compatible
     from sentence_transformers import SentenceTransformer
     model = SentenceTransformer(model_id, device=pick_device())
  2) transformers + custom pooling when needed
     from transformers import AutoModel, AutoTokenizer
     tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
     kwargs = {}
     if torch.cuda.is_available(): kwargs.update({"torch_dtype": torch.float16})
     if settings.enable_4bit: kwargs.update({"load_in_4bit": True})
     mdl = AutoModel.from_pretrained(model_id, trust_remote_code=True, **kwargs)
     def encode(texts):
       batch = tok(texts, padding=True, truncation=True, return_tensors='pt').to(device)
       with torch.inference_mode(): out = mdl(**batch)
       # Pooling: mean pooling over last_hidden_state masked by attention
       emb = (out.last_hidden_state * batch.attention_mask.unsqueeze(-1)).sum(dim=1) / batch.attention_mask.sum(dim=1, keepdim=True)
       return torch.nn.functional.normalize(emb, p=2, dim=1).cpu().tolist()
- Wrap in EmbeddingProvider impl with AsyncLazyResource init
- Provide config knobs: max_seq_len, normalize=True, device_map='auto', enable_4bit (requires bitsandbytes)
- Determine dim at runtime by a test encode and len(vector)
- Security/perf: set torch.set_grad_enabled(False)
- Logging: log model id, dtype, device, dim
- Hardware considerations: document minimum VRAM; 4-bit suggested for 1.5B on 8–12GB GPUs


### Test Strategy
- Unit test provider encodes sample inputs and returns consistent dims, cosine sim of duplicate texts ~1.0
- If CUDA available, ensure dtype is float16; otherwise CPU path works
- Benchmark micro-test within test marked slow to ensure throughput reasonable and no memory leak
- Skip tests gracefully if model cannot be downloaded (offline), asserting ProblemDetails on failure

### Migration Notes
- Originally Task ID: 6
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: high
- Status mapping: pending
- Dependencies: [5, 4]

### Related Files
- Original: .taskmaster/tasks/tasks.json
