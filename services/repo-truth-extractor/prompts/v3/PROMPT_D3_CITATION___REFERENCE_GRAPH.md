OUTPUTS:
- DOC_CITATION_GRAPH.json

Goal: DOC_CITATION_GRAPH.json

Prompt:
- Build graph edges:
  - doc A references doc B (links, filenames, "see also", explicit citations)
  - doc A references code path
  - doc A references service name/config name
- Output top referenced docs, hub docs, cross-plane edges.