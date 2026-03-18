from typing import Any, Dict

PRESCAN_INTELLIGENCE_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Prescan Intelligence",
    "type": "object",
    "properties": {
        "version": {"type": "string"},
        "generated_at": {"type": "string", "format": "date-time"},
        "repo_root": {"type": "string"},
        "corpus_summary": {
            "type": "object",
            "properties": {
                "total_files_scanned": {"type": "integer"},
                "included_files": {"type": "integer"},
                "total_included_size_bytes": {"type": "integer"},
                "by_authority_class": {
                    "type": "object",
                    "additionalProperties": {"type": "integer"}
                },
                "by_extension": {
                    "type": "object",
                    "additionalProperties": {"type": "integer"}
                }
            }
        },
        "duplicate_groups": {
            "type": "object",
            "additionalProperties": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "version_chains": {
            "type": "object",
            "additionalProperties": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "ordinal": {"type": "integer"},
                        "is_latest": {"type": "boolean"}
                    }
                }
            }
        },
        "extraction_hints": {
            "type": "object",
            "properties": {
                "skip_duplicates": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "compress_candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "chain_id": {"type": "string"},
                            "send_summary_instead": {"type": "boolean"},
                            "summary_hint": {"type": "string"}
                        }
                    }
                }
            }
        },
        "code_intelligence": {
            "type": "object",
            "properties": {
                "analyzed_files": {"type": "integer"},
                "api_surfaces": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "dependency_clusters": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "topological_order": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "cost_estimate": {
            "type": "object",
            "properties": {
                "net_estimates": {
                    "type": "object",
                    "properties": {
                        "total_cost_usd": {"type": "number"}
                    }
                }
            }
        }
    },
    "required": ["version", "generated_at", "corpus_summary"]
}
