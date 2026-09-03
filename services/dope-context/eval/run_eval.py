#!/usr/bin/env python3
"""
Wave 0 offline retrieval evaluation harness for dope-context.

Self-contained: chunks the dope-context ``src/`` corpus with the repo's own
``CodeChunker``, embeds it under several embedding "profiles", indexes each
profile into a throwaway Qdrant collection, runs a fixed query set against
it, computes retrieval metrics, and deletes the collection (even on
failure). No dependency beyond what the mcp-dope-context container already
has: this repo's ``preprocessing.code_chunker``, ``voyageai``,
``qdrant-client``, and (only for profile Bhl) ``openai``.

Profiles:
  A    - documents AND queries embedded with voyage-context-4 via
         contextualized_embed (context-aware both sides).
  B    - documents AND queries embedded with voyage-code-4 via the flat
         embed endpoint (no cross-chunk context).
  Bh   - B, but the embedded document text is prefixed with a scope header
         (file path + qualified symbol name). Queries unchanged.
  Bhl  - Bh, plus a 1-2 sentence LLM-generated situating context (OpenAI
         gpt-5.6-luna) prepended to the document text. NOT_RUN if
         OPENAI_API_KEY is absent from the environment, or if any call to
         it fails after retries.
  CTRL - the historical index/query embedding-space mismatch, run as a
         control: documents are profile A's already-computed
         voyage-context-4 contextual embeddings (reused, not
         re-embedded), but QUERIES are embedded with voyage-code-3 on the
         flat endpoint. This deliberately indexes and queries in two
         different vector spaces.

Guardrails:
  - Refuses to run unless --corpus resolves to a path ending in
    services/dope-context/src (never embeds anything else).
  - Aborts a single profile (FAILED, not silently skipped) if its
    projected input tokens exceed MAX_INPUT_TOKENS_PER_PROFILE, checked
    BEFORE any embedding API call is made.
  - Retries every embedding / chat-completion API call up to MAX_RETRIES
    times with exponential backoff before giving up.
  - Every throwaway Qdrant collection (``eval_<profile>_<8hex>``) is
    deleted in a try/finally, regardless of whether the profile
    succeeded, failed, or was skipped mid-way.

Usage (inside the mcp-dope-context container):
    python run_eval.py \
        --corpus /path/to/services/dope-context/src \
        --queries /path/to/eval/queries.jsonl \
        --profiles A,B,Bh,Bhl,CTRL \
        --json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --------------------------------------------------------------------------
# Guardrails / constants
# --------------------------------------------------------------------------

MAX_INPUT_TOKENS_PER_PROFILE = 200_000
MAX_RETRIES = 3
DEFAULT_TOP_K = 20
VALID_PROFILES = ("A", "B", "Bh", "Bhl", "CTRL")

# Pricing per the Wave 0 task brief (A/B/Bh/Bhl models) plus this repo's own
# model_registry.py for voyage-code-3 (used only by the CTRL control).
# D/Dh profiles added per https://docs.voyageai.com/docs/pricing (read 2026-09-03):
# voyage-code-4 and rerank-3 are verified accepted by the Voyage API.
PRICE_PER_M = {
    "voyage-context-4": 0.12,
    "voyage-code-4": 0.12,
    "voyage-code-3": 0.18,
    "rerank-3": 0.05,
    "gpt-5.6-luna-in": 0.20,
    "gpt-5.6-luna-out": 1.20,
}

# Rough "does this query mention a code identifier" detector: camelCase or
# snake_case tokens.
IDENTIFIER_RE = re.compile(r"\b([a-z]+[A-Z][a-zA-Z0-9]*|[a-z][a-z0-9]*_[a-z0-9_]+)\b")


def approx_tokens(text: str) -> int:
    """Cheap guardrail estimate: ~4 chars/token. Not billed usage."""
    return max(1, len(text) // 4)


def query_has_identifier(query_text: str) -> bool:
    return bool(IDENTIFIER_RE.search(query_text))


def call_with_retries(fn, *args, max_retries: int = MAX_RETRIES, **kwargs):
    last_exc: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - eval harness: log & retry
            last_exc = exc
            if attempt == max_retries:
                raise
            sleep_s = min(2**attempt, 20)
            print(
                f"  retry {attempt}/{max_retries} after error: {exc} "
                f"(sleeping {sleep_s}s)",
                file=sys.stderr,
            )
            time.sleep(sleep_s)
    raise last_exc  # pragma: no cover - unreachable


# --------------------------------------------------------------------------
# Corpus loading
# --------------------------------------------------------------------------


@dataclass
class ChunkRecord:
    rel_path: str
    qualified_name: Optional[str]
    symbol_name: Optional[str]
    parent_symbol: Optional[str]
    chunk_type: str
    content: str
    start_line: int
    end_line: int
    tokens_estimate: int
    file_key: str  # groups chunks belonging to the same source file


def is_whole_file_duplicate(chunk) -> bool:
    """CodeChunker's Python 'module' target type collapses to
    chunk_type == 'block' with no symbol/parent, spanning the whole file
    (tree-sitter is available in this container, so the pure line-based
    fallback -- which also emits chunk_type == 'block' -- is never invoked
    for .py files, making this filter unambiguous here). That whole-file
    node duplicates every other chunk's content and must be excluded from
    the corpus."""
    return (
        chunk.chunk_type == "block"
        and chunk.symbol_name is None
        and chunk.parent_symbol is None
    )


def build_corpus(corpus_root: Path) -> List[ChunkRecord]:
    if str(corpus_root) not in sys.path:
        sys.path.insert(0, str(corpus_root))
    from preprocessing.code_chunker import CodeChunker  # type: ignore

    chunker = CodeChunker()
    records: List[ChunkRecord] = []
    py_files = sorted(corpus_root.rglob("*.py"))
    for f in py_files:
        chunks = chunker.chunk_file(f)
        rel = f.relative_to(corpus_root)
        rel_path = "src/" + str(rel).replace(os.sep, "/")
        for c in chunks:
            if is_whole_file_duplicate(c):
                continue
            if c.parent_symbol and c.symbol_name:
                qualified = f"{c.parent_symbol}.{c.symbol_name}"
            else:
                qualified = c.symbol_name
            records.append(
                ChunkRecord(
                    rel_path=rel_path,
                    qualified_name=qualified,
                    symbol_name=c.symbol_name,
                    parent_symbol=c.parent_symbol,
                    chunk_type=c.chunk_type,
                    content=c.content,
                    start_line=c.start_line,
                    end_line=c.end_line,
                    tokens_estimate=c.tokens_estimate,
                    file_key=rel_path,
                )
            )
    return records


def group_by_file(records: List[ChunkRecord]) -> Dict[str, List[ChunkRecord]]:
    groups: Dict[str, List[ChunkRecord]] = {}
    for r in records:
        groups.setdefault(r.file_key, []).append(r)
    return groups


# --------------------------------------------------------------------------
# Document text builders per profile
# --------------------------------------------------------------------------


def doc_text_plain(r: ChunkRecord) -> str:
    return r.content


def scope_header(r: ChunkRecord) -> str:
    sym = r.qualified_name or "(module scope)"
    return f"# file: {r.rel_path}\n# symbol: {sym}\n# type: {r.chunk_type}\n\n"


def doc_text_scoped(r: ChunkRecord) -> str:
    return scope_header(r) + r.content


def apply_llm_contexts(
    records: List[ChunkRecord],
    texts: List[str],
    file_text_cache: Dict[str, str],
    corpus_root: Path,
) -> Tuple[List[str], int, int]:
    """Prepend a 1-2 sentence LLM-generated situating context to each
    document text. The whole file is sent as a fixed leading user message,
    repeated verbatim per chunk of the same file, so OpenAI's automatic
    server-side prompt caching applies; only the trailing chunk-specific
    instruction varies."""
    from openai import OpenAI

    client = OpenAI()
    grouped = group_by_file(records)
    index_of = {id(r): i for i, r in enumerate(records)}
    contexts_by_index: Dict[int, str] = {}
    total_in = 0
    total_out = 0

    system_msg = {
        "role": "system",
        "content": (
            "You write a single short (1-2 sentence) situating context for "
            "a code chunk, given the whole file it comes from. State what "
            "the chunk does and where it fits in the file. Do not repeat "
            "the code."
        ),
    }

    for file_key, recs in grouped.items():
        if file_key not in file_text_cache:
            file_path = corpus_root / file_key[len("src/"):]
            try:
                file_text_cache[file_key] = file_path.read_text(encoding="utf-8")
            except Exception:
                file_text_cache[file_key] = ""
        file_text = file_text_cache[file_key]
        file_msg = {
            "role": "user",
            "content": f"Whole file ({file_key}):\n\n{file_text}",
        }
        for r in recs:
            chunk_msg = {
                "role": "user",
                "content": (
                    f"Chunk (lines {r.start_line}-{r.end_line}, "
                    f"symbol={r.qualified_name or 'n/a'}):\n\n{r.content}\n\n"
                    "Give the 1-2 sentence situating context now."
                ),
            }
            resp = call_with_retries(
                client.chat.completions.create,
                model="gpt-5.6-luna",
                messages=[system_msg, file_msg, chunk_msg],
                max_completion_tokens=160,
            )
            ctx_text = (resp.choices[0].message.content or "").strip()
            contexts_by_index[index_of[id(r)]] = ctx_text
            if getattr(resp, "usage", None):
                total_in += resp.usage.prompt_tokens or 0
                total_out += resp.usage.completion_tokens or 0

    new_texts: List[str] = []
    for i, base_text in enumerate(texts):
        ctx = contexts_by_index.get(i, "")
        new_texts.append(f"{ctx}\n\n{base_text}" if ctx else base_text)
    return new_texts, total_in, total_out


# --------------------------------------------------------------------------
# Embedding calls
# --------------------------------------------------------------------------


def get_voyage_client():
    import voyageai

    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        raise RuntimeError("VOYAGE_API_KEY not set in environment")
    return voyageai.Client(api_key=api_key)


def embed_flat(
    client,
    texts: List[str],
    model: str,
    input_type: str,
    batch_size: int = 100,
) -> Tuple[List[List[float]], int]:
    vectors: List[List[float]] = []
    total_tokens = 0
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        result = call_with_retries(
            client.embed,
            texts=batch,
            model=model,
            input_type=input_type,
            output_dimension=1024,
            output_dtype="float",
        )
        vectors.extend(result.embeddings)
        total_tokens += result.total_tokens
    return vectors, total_tokens


def embed_contextual(
    client,
    grouped_texts: List[List[str]],
    model: str,
    input_type: str,
    batch_size_docs: int = 20,
) -> Tuple[List[List[List[float]]], int]:
    all_results: List[List[List[float]]] = []
    total_tokens = 0
    for i in range(0, len(grouped_texts), batch_size_docs):
        batch = grouped_texts[i : i + batch_size_docs]
        result = call_with_retries(
            client.contextualized_embed,
            inputs=batch,
            model=model,
            input_type=input_type,
            output_dimension=1024,
        )
        for doc_result in result.results:
            all_results.append(doc_result.embeddings)
        total_tokens += result.total_tokens
    return all_results, total_tokens


def embed_queries_contextual(client, model: str, query_texts: List[str]):
    grouped = [[q] for q in query_texts]
    results, total_tokens = embed_contextual(client, grouped, model=model, input_type="query")
    vectors = [r[0] for r in results]
    return vectors, total_tokens


def embed_queries_flat(client, model: str, query_texts: List[str]):
    return embed_flat(client, query_texts, model=model, input_type="query")


# --------------------------------------------------------------------------
# Qdrant
# --------------------------------------------------------------------------


def get_qdrant_client(url: str):
    from qdrant_client import QdrantClient

    return QdrantClient(url=url)


def create_collection(qdrant, name: str, dim: int, distance: str):
    from qdrant_client import models

    dist = models.Distance.DOT if distance == "dot" else models.Distance.COSINE
    qdrant.create_collection(
        collection_name=name,
        vectors_config=models.VectorParams(size=dim, distance=dist),
    )


def upsert_points(
    qdrant,
    name: str,
    vectors: List[List[float]],
    payloads: List[Dict[str, Any]],
    batch_size: int = 200,
):
    from qdrant_client import models

    total = len(vectors)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        points = [
            models.PointStruct(id=idx, vector=vectors[idx], payload=payloads[idx])
            for idx in range(start, end)
        ]
        qdrant.upsert(collection_name=name, points=points, wait=True)


def run_query(qdrant, name: str, vector: List[float], top_k: int):
    from qdrant_client import models

    result = qdrant.query_points(
        collection_name=name,
        query=vector,
        limit=top_k,
        search_params=models.SearchParams(exact=True),
        with_payload=True,
    )
    return result.points


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------


def record_matches_expected(payload: Dict[str, Any], expected: Dict[str, str]) -> bool:
    rel_path = payload.get("rel_path") or ""
    if not rel_path.endswith(expected["rel_path"]):
        return False
    exp_symbol = expected["symbol"]
    qualified = payload.get("qualified_name") or ""
    symbol = payload.get("symbol_name") or ""
    return qualified == exp_symbol or symbol == exp_symbol


def compute_query_metrics(
    hit_payloads: List[Dict[str, Any]], expected: List[Dict[str, str]]
) -> Dict[str, float]:
    n_expected = len(expected)

    def recall_at(k: int) -> float:
        if not n_expected:
            return 0.0
        found = set()
        for payload in hit_payloads[:k]:
            for ei, exp in enumerate(expected):
                if record_matches_expected(payload, exp):
                    found.add(ei)
        return len(found) / n_expected

    mrr = 0.0
    for rank, payload in enumerate(hit_payloads, start=1):
        if any(record_matches_expected(payload, exp) for exp in expected):
            mrr = 1.0 / rank
            break

    def ndcg_at(k: int) -> float:
        dcg = 0.0
        for rank, payload in enumerate(hit_payloads[:k], start=1):
            if any(record_matches_expected(payload, exp) for exp in expected):
                dcg += 1.0 / math.log2(rank + 1)
        ideal_hits = min(n_expected, k)
        idcg = sum(1.0 / math.log2(r + 1) for r in range(1, ideal_hits + 1))
        return dcg / idcg if idcg > 0 else 0.0

    return {
        "recall_at_5": recall_at(5),
        "recall_at_20": recall_at(20),
        "mrr": mrr,
        "ndcg_at_10": ndcg_at(10),
    }


# --------------------------------------------------------------------------
# Profile orchestration
# --------------------------------------------------------------------------


@dataclass
class ProfileResult:
    profile: str
    status: str = "OK"  # OK | NOT_RUN | FAILED
    reason: Optional[str] = None
    collection_name: Optional[str] = None
    chunks_indexed: int = 0
    doc_tokens: int = 0
    query_tokens: int = 0
    llm_tokens_in: int = 0
    llm_tokens_out: int = 0
    cost_usd: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)
    identifier_subset: Dict[str, Any] = field(default_factory=dict)


def run_profile(
    profile: str,
    records: List[ChunkRecord],
    queries: List[Dict[str, Any]],
    voyage_client,
    qdrant_url: str,
    openai_key_present: bool,
    cache: Dict[str, Any],
    top_k: int,
    corpus_root: Path,
) -> ProfileResult:
    result = ProfileResult(profile=profile)

    if profile == "Bhl" and not openai_key_present:
        result.status = "NOT_RUN"
        result.reason = "OPENAI_API_KEY not set in mcp-dope-context container"
        return result

    collection_name = f"eval_{profile.lower()}_{uuid.uuid4().hex[:8]}"
    result.collection_name = collection_name
    qdrant = get_qdrant_client(qdrant_url)

    try:
        # ---- document side ----
        if profile in ("A", "CTRL"):
            if "a_doc_vectors" not in cache:
                grouped_by_file = group_by_file(records)
                file_keys = list(grouped_by_file.keys())
                grouped_texts = [[r.content for r in grouped_by_file[fk]] for fk in file_keys]
                approx_in = sum(approx_tokens(t) for texts in grouped_texts for t in texts)
                if approx_in > MAX_INPUT_TOKENS_PER_PROFILE:
                    raise RuntimeError(
                        f"projected input tokens {approx_in} exceeds guardrail "
                        f"{MAX_INPUT_TOKENS_PER_PROFILE} for profile A/CTRL document embedding"
                    )
                doc_results, doc_tokens = embed_contextual(
                    voyage_client, grouped_texts, model="voyage-context-4", input_type="document"
                )
                flat_vectors: List[List[float]] = []
                flat_records: List[ChunkRecord] = []
                for fk, vecs in zip(file_keys, doc_results):
                    for rec, vec in zip(grouped_by_file[fk], vecs):
                        flat_vectors.append(vec)
                        flat_records.append(rec)
                cache["a_doc_vectors"] = flat_vectors
                cache["a_doc_records"] = flat_records
                cache["a_doc_tokens"] = doc_tokens
            doc_vectors = cache["a_doc_vectors"]
            doc_records = cache["a_doc_records"]
            result.doc_tokens = cache["a_doc_tokens"] if profile == "A" else 0
            distance = "dot"
        else:  # B, Bh, Bhl
            if profile == "B":
                texts = [doc_text_plain(r) for r in records]
            else:
                texts = [doc_text_scoped(r) for r in records]
            if profile == "Bhl":
                texts, llm_in, llm_out = apply_llm_contexts(
                    records, texts, cache.setdefault("file_text_cache", {}), corpus_root
                )
                result.llm_tokens_in = llm_in
                result.llm_tokens_out = llm_out
            approx_in = sum(approx_tokens(t) for t in texts)
            if approx_in > MAX_INPUT_TOKENS_PER_PROFILE:
                raise RuntimeError(
                    f"projected input tokens {approx_in} exceeds guardrail "
                    f"{MAX_INPUT_TOKENS_PER_PROFILE} for profile {profile} document embedding"
                )
            doc_vectors, doc_tokens = embed_flat(
                voyage_client, texts, model="voyage-code-4", input_type="document"
            )
            doc_records = records
            result.doc_tokens = doc_tokens
            distance = "dot"

        create_collection(qdrant, collection_name, dim=1024, distance=distance)
        payloads = [
            {
                "rel_path": r.rel_path,
                "qualified_name": r.qualified_name,
                "symbol_name": r.symbol_name,
                "parent_symbol": r.parent_symbol,
                "chunk_type": r.chunk_type,
                "start_line": r.start_line,
                "end_line": r.end_line,
            }
            for r in doc_records
        ]
        upsert_points(qdrant, collection_name, doc_vectors, payloads)
        result.chunks_indexed = len(doc_vectors)

        # ---- query side ----
        query_texts = [q["query"] for q in queries]
        if profile == "A":
            q_vectors, q_tokens = embed_queries_contextual(voyage_client, "voyage-context-4", query_texts)
        elif profile == "CTRL":
            q_vectors, q_tokens = embed_queries_flat(voyage_client, "voyage-code-3", query_texts)
        else:
            q_vectors, q_tokens = embed_queries_flat(voyage_client, "voyage-code-4", query_texts)
        result.query_tokens = q_tokens

        per_query_metrics = []
        identifier_flags = []
        for q, qvec in zip(queries, q_vectors):
            hits = run_query(qdrant, collection_name, qvec, top_k)
            hit_payloads = [h.payload for h in hits]
            per_query_metrics.append(compute_query_metrics(hit_payloads, q["expected"]))
            identifier_flags.append(query_has_identifier(q["query"]))

        def avg(key: str) -> float:
            vals = [m[key] for m in per_query_metrics]
            return sum(vals) / len(vals) if vals else 0.0

        result.metrics = {
            "recall_at_5": avg("recall_at_5"),
            "recall_at_20": avg("recall_at_20"),
            "mrr": avg("mrr"),
            "ndcg_at_10": avg("ndcg_at_10"),
        }

        id_subset = [m for m, flag in zip(per_query_metrics, identifier_flags) if flag]
        result.identifier_subset = {
            "count": len(id_subset),
            "recall_at_20": (sum(m["recall_at_20"] for m in id_subset) / len(id_subset))
            if id_subset
            else None,
        }

        # ---- cost ----
        if profile == "A":
            doc_cost = (result.doc_tokens / 1_000_000) * PRICE_PER_M["voyage-context-4"]
            q_price = PRICE_PER_M["voyage-context-4"]
        elif profile == "CTRL":
            doc_cost = 0.0  # reused profile A's already-paid-for document embeddings
            q_price = PRICE_PER_M["voyage-code-3"]
        else:
            doc_cost = (result.doc_tokens / 1_000_000) * PRICE_PER_M["voyage-code-4"]
            q_price = PRICE_PER_M["voyage-code-4"]
        query_cost = (result.query_tokens / 1_000_000) * q_price
        llm_cost = (
            (result.llm_tokens_in / 1_000_000) * PRICE_PER_M["gpt-5.6-luna-in"]
            + (result.llm_tokens_out / 1_000_000) * PRICE_PER_M["gpt-5.6-luna-out"]
        )
        result.cost_usd = round(doc_cost + query_cost + llm_cost, 6)

    except Exception as exc:  # noqa: BLE001 - report, don't crash the whole run
        result.status = "FAILED"
        result.reason = str(exc)
    finally:
        try:
            qdrant.delete_collection(collection_name=collection_name)
        except Exception as cleanup_exc:  # noqa: BLE001
            print(
                f"WARNING: failed to delete collection {collection_name}: {cleanup_exc}",
                file=sys.stderr,
            )

    return result


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Wave 0 offline retrieval eval harness for dope-context")
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--queries", required=True, type=Path)
    parser.add_argument("--profiles", default="A,B,Bh,Bhl", help="Comma-separated: A,B,Bh,Bhl,CTRL")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--qdrant-url", default="http://mcp-qdrant:6333")
    parser.add_argument("--json", action="store_true", help="accepted for CLI compatibility; output is always JSON")
    args = parser.parse_args()

    corpus_root = args.corpus.resolve()
    normalized = str(corpus_root).replace(os.sep, "/")
    if not normalized.endswith("services/dope-context/src"):
        print(
            f"REFUSING: corpus root {corpus_root} does not end with "
            "services/dope-context/src -- refusing to embed anything outside it",
            file=sys.stderr,
        )
        return 2

    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]
    for p in profiles:
        if p not in VALID_PROFILES:
            print(f"REFUSING: unknown profile '{p}'. Valid: {VALID_PROFILES}", file=sys.stderr)
            return 2

    queries: List[Dict[str, Any]] = []
    with open(args.queries, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                queries.append(json.loads(line))

    print(f"Building corpus from {corpus_root} ...", file=sys.stderr)
    records = build_corpus(corpus_root)
    print(f"  {len(records)} chunks across "
          f"{len({r.rel_path for r in records})} files", file=sys.stderr)

    openai_key_present = bool(os.environ.get("OPENAI_API_KEY"))
    voyage_client = get_voyage_client()

    cache: Dict[str, Any] = {}
    profile_results: Dict[str, ProfileResult] = {}
    for p in profiles:
        print(f"Running profile {p} ...", file=sys.stderr)
        profile_results[p] = run_profile(
            p, records, queries, voyage_client, args.qdrant_url,
            openai_key_present, cache, args.top_k, corpus_root,
        )
        print(f"  {p}: {profile_results[p].status}", file=sys.stderr)

    output = {
        "run_id": uuid.uuid4().hex[:8],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "corpus_root": str(corpus_root),
        "corpus_files": len({r.rel_path for r in records}),
        "corpus_chunks": len(records),
        "queries_count": len(queries),
        "top_k": args.top_k,
        "profiles": {p: asdict(r) for p, r in profile_results.items()},
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
