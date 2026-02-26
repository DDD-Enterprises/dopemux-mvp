OUTPUTS:
- DOC_TOPIC_CLUSTERS.json

Goal: DOC_TOPIC_CLUSTERS.json

Prompt:
- Input: merged docs index (plus optionally raw text samples).
- Cluster by token overlap (no semantic labeling).
- Output:
  - cluster_id
  - doc_paths
  - top_tokens (weighted)
  - doc_count
  - newest_mtime + oldest_mtime (for recency awareness)
- No "this cluster is architecture" labeling.