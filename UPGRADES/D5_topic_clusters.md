## D5: DOC_TOPIC_CLUSTERS.json (mechanical clustering, instruction-weight aware)

Output file
	•	DOC_TOPIC_CLUSTERS.json

ROLE: Mechanical clustering engine. No reasoning. JSON only. ASCII only.

INPUTS:
- DOC_INVENTORY.json
- DOC_INDEX.json
- DOC_CLAIMS.json
- DOC_BOUNDARIES.json
- DOC_WORKFLOWS.json
- DOC_INTERFACES.json
- DOC_DECISIONS.json
- DOC_CITATION_GRAPH.json

TOKEN SOURCES per doc:
- title + headings
- claims original_quote tokens
- workflows step tokens
- boundary tokens
- interfaces: interface_type + language_hint only (not full blocks)
- decisions: first 2 lines tokens
- citation targets tokens (weak)

TOKENIZATION:
- lowercase
- split on non-alphanumeric
- keep tokens len >= 4
- remove stopwords
- cap 500 tokens per doc

WEIGHTING:
- if is_archive=true: drop lowest 30% frequency tokens in that doc
- if path contains "/custom-instructions/" or "/_opus_inputs/" or "/_handoff/":
  duplicate the token set once (multiset doubling)

SIMILARITY:
- Jaccard overlap on token sets

CLUSTERING:
- deterministic greedy:
  sort docs by citation_in_degree desc, then path asc
  seed cluster with first unassigned doc
  add docs with sim >= 0.18
  do one extra expansion pass, then finalize cluster

OUTPUT DOC_TOPIC_CLUSTERS.json:
- cluster_id c001...
- doc_paths[]
- top_tokens (top 25 by document frequency within cluster)
- anchor_docs (top 3 docs by average similarity inside cluster)
- cluster_stats: doc_count, avg_similarity_estimate, total_citation_in, total_citation_out

RULES:
- no semantic labels
- JSON only
- deterministic ordering
