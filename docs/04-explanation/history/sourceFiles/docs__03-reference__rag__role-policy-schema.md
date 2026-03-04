# Role Policy Schema Reference

## Overview

The Dopemux RAG system uses JSON-configured policies to adapt retrieval behavior based on user roles and current tasks. This document defines the complete schema, provides examples for each role, and explains configuration options.

## Policy Key Format

```
{role}:{task}
```

**Examples:**
- `Developer:CodeImplementation`
- `Architect:SystemDesign`
- `SRE:IncidentResponse`
- `PM:FeatureDiscussion`

## Schema Definition

### Root Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "patternProperties": {
    "^[A-Za-z]+:[A-Za-z]+$": {
      "$ref": "#/definitions/PolicyDefinition"
    }
  },
  "additionalProperties": false
}
```

### Policy Definition Schema
```json
{
  "definitions": {
    "PolicyDefinition": {
      "type": "object",
      "properties": {
        "source_weights": {
          "$ref": "#/definitions/SourceWeights"
        },
        "rerank_instruction": {
          "type": "string",
          "description": "Natural language instruction for reranker model"
        },
        "filters": {
          "$ref": "#/definitions/FilterConfiguration"
        },
        "fusion_weights": {
          "$ref": "#/definitions/FusionWeights"
        },
        "context_limits": {
          "$ref": "#/definitions/ContextLimits"
        },
        "must_include": {
          "$ref": "#/definitions/MustIncludeRules"
        }
      },
      "required": ["source_weights", "rerank_instruction"],
      "additionalProperties": false
    }
  }
}
```

### Source Weights Schema
```json
{
  "SourceWeights": {
    "type": "object",
    "properties": {
      "ProjectCode": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0,
        "description": "Weight for code collection results"
      },
      "ProjectDocs": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0,
        "description": "Weight for documentation collection results"
      }
    },
    "required": ["ProjectCode", "ProjectDocs"],
    "additionalProperties": false
  }
}
```

### Filter Configuration Schema
```json
{
  "FilterConfiguration": {
    "type": "object",
    "properties": {
      "include_modules": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Code modules/directories to include"
      },
      "exclude_modules": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Code modules/directories to exclude"
      },
      "include_doc_types": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["ADR", "RFC", "Spec", "Requirement", "Runbook", "PostMortem", "README", "Tutorial", "HowTo"]
        },
        "description": "Document types to include"
      },
      "exclude_doc_types": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["ADR", "RFC", "Spec", "Requirement", "Runbook", "PostMortem", "README", "Tutorial", "HowTo"]
        },
        "description": "Document types to exclude"
      },
      "language_filter": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Programming languages to include for code"
      },
      "recency_days": {
        "type": "integer",
        "minimum": 1,
        "description": "Only include content updated within N days"
      }
    },
    "additionalProperties": false
  }
}
```

### Fusion Weights Schema
```json
{
  "FusionWeights": {
    "type": "object",
    "properties": {
      "docs_dense": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0,
        "default": 0.65,
        "description": "Dense vector weight for document search"
      },
      "docs_sparse": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0,
        "default": 0.35,
        "description": "BM25 weight for document search"
      },
      "code_dense": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0,
        "default": 0.55,
        "description": "Dense vector weight for code search"
      },
      "code_sparse": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0,
        "default": 0.45,
        "description": "BM25 weight for code search"
      }
    },
    "additionalProperties": false
  }
}
```

### Context Limits Schema
```json
{
  "ContextLimits": {
    "type": "object",
    "properties": {
      "max_candidates": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 64,
        "description": "Maximum candidates from Stage 1 retrieval"
      },
      "max_results": {
        "type": "integer",
        "minimum": 1,
        "maximum": 20,
        "default": 10,
        "description": "Maximum results after reranking"
      },
      "max_tokens": {
        "type": "integer",
        "minimum": 500,
        "maximum": 5000,
        "default": 2500,
        "description": "Maximum tokens in context header"
      }
    },
    "additionalProperties": false
  }
}
```

### Must Include Rules Schema
```json
{
  "MustIncludeRules": {
    "type": "object",
    "properties": {
      "latest_adr": {
        "type": "boolean",
        "default": false,
        "description": "Always include most recent ADR if relevant"
      },
      "related_commits": {
        "type": "boolean",
        "default": false,
        "description": "Include recent git commits for code queries"
      },
      "error_patterns": {
        "type": "boolean",
        "default": false,
        "description": "Include error handling patterns for error queries"
      }
    },
    "additionalProperties": false
  }
}
```

## Complete Role Policy Examples

### Developer Policies

#### Code Implementation
```json
{
  "Developer:CodeImplementation": {
    "source_weights": {
      "ProjectCode": 0.6,
      "ProjectDocs": 0.4
    },
    "rerank_instruction": "Prioritize code snippets, implementation details, and concrete examples. Surface working code over documentation. Focus on executable patterns, API usage, and best practices. Include relevant test examples if available.",
    "filters": {
      "include_modules": ["src/", "lib/", "app/"],
      "exclude_modules": ["test/", "docs/"],
      "exclude_doc_types": ["ADR"],
      "language_filter": []
    },
    "fusion_weights": {
      "code_dense": 0.5,
      "code_sparse": 0.5
    },
    "context_limits": {
      "max_candidates": 64,
      "max_results": 12,
      "max_tokens": 2800
    },
    "must_include": {
      "latest_adr": false,
      "related_commits": true,
      "error_patterns": false
    }
  }
}
```

#### Debugging
```json
{
  "Developer:Debugging": {
    "source_weights": {
      "ProjectCode": 0.7,
      "ProjectDocs": 0.3
    },
    "rerank_instruction": "Emphasize error handling code, debugging utilities, logging implementations, and troubleshooting patterns. Prioritize code that demonstrates error conditions, exception handling, and diagnostic tools. Include runbooks only if they contain technical debugging steps.",
    "filters": {
      "include_modules": ["src/", "lib/", "test/"],
      "include_doc_types": ["Runbook", "PostMortem"],
      "language_filter": []
    },
    "fusion_weights": {
      "code_dense": 0.4,
      "code_sparse": 0.6
    },
    "context_limits": {
      "max_candidates": 48,
      "max_results": 10,
      "max_tokens": 2500
    },
    "must_include": {
      "error_patterns": true,
      "related_commits": true,
      "latest_adr": false
    }
  }
}
```

#### Code Review
```json
{
  "Developer:CodeReview": {
    "source_weights": {
      "ProjectCode": 0.8,
      "ProjectDocs": 0.2
    },
    "rerank_instruction": "Focus on code patterns, style guidelines, security best practices, and existing implementations of similar functionality. Prioritize examples of good practices and anti-patterns. Include coding standards and architectural patterns.",
    "filters": {
      "include_modules": ["src/", "lib/"],
      "include_doc_types": ["Spec", "README"],
      "recency_days": 90
    },
    "context_limits": {
      "max_candidates": 48,
      "max_results": 8,
      "max_tokens": 2000
    }
  }
}
```

### Architect Policies

#### System Design
```json
{
  "Architect:SystemDesign": {
    "source_weights": {
      "ProjectDocs": 0.8,
      "ProjectCode": 0.2
    },
    "rerank_instruction": "Surface high-level architecture documents, design patterns, system interaction diagrams, and architectural decision records. Include relevant code only as examples of architectural patterns. Emphasize design rationale, trade-offs, and system-wide implications.",
    "filters": {
      "include_doc_types": ["ADR", "RFC", "Spec", "README"],
      "exclude_modules": ["test/", "scripts/"],
      "include_modules": ["src/core/", "src/services/"]
    },
    "fusion_weights": {
      "docs_dense": 0.7,
      "docs_sparse": 0.3
    },
    "context_limits": {
      "max_candidates": 64,
      "max_results": 12,
      "max_tokens": 3000
    },
    "must_include": {
      "latest_adr": true,
      "related_commits": false,
      "error_patterns": false
    }
  }
}
```

#### Technology Evaluation
```json
{
  "Architect:TechnologyEvaluation": {
    "source_weights": {
      "ProjectDocs": 0.9,
      "ProjectCode": 0.1
    },
    "rerank_instruction": "Prioritize technology comparisons, evaluation criteria, proof of concepts, and decision rationale. Focus on architectural trade-offs, performance characteristics, and integration considerations. Include benchmarks and comparative analysis.",
    "filters": {
      "include_doc_types": ["ADR", "RFC", "Spec"],
      "exclude_modules": ["src/"],
      "recency_days": 180
    },
    "context_limits": {
      "max_results": 8,
      "max_tokens": 2500
    }
  }
}
```

### SRE Policies

#### Incident Response
```json
{
  "SRE:IncidentResponse": {
    "source_weights": {
      "ProjectDocs": 0.5,
      "ProjectCode": 0.5
    },
    "rerank_instruction": "Include operational runbooks, incident response procedures, monitoring configurations, and deployment code. Prioritize actionable troubleshooting steps, system recovery procedures, and diagnostic tools. Focus on production systems and operational guidance.",
    "filters": {
      "include_doc_types": ["Runbook", "PostMortem"],
      "include_modules": ["infra/", "deploy/", "monitoring/", "scripts/"]
    },
    "fusion_weights": {
      "docs_dense": 0.6,
      "docs_sparse": 0.4,
      "code_dense": 0.4,
      "code_sparse": 0.6
    },
    "context_limits": {
      "max_candidates": 48,
      "max_results": 10,
      "max_tokens": 2500
    },
    "must_include": {
      "error_patterns": true,
      "related_commits": false,
      "latest_adr": false
    }
  }
}
```

#### Performance Analysis
```json
{
  "SRE:PerformanceAnalysis": {
    "source_weights": {
      "ProjectCode": 0.6,
      "ProjectDocs": 0.4
    },
    "rerank_instruction": "Focus on performance-critical code, monitoring configurations, benchmarking results, and optimization techniques. Include profiling data, performance test results, and system metrics. Prioritize code that affects system performance.",
    "filters": {
      "include_modules": ["src/", "monitoring/", "benchmarks/"],
      "include_doc_types": ["Runbook", "PostMortem"],
      "language_filter": ["python", "go", "rust", "javascript"]
    },
    "context_limits": {
      "max_results": 12,
      "max_tokens": 3000
    }
  }
}
```

### PM Policies

#### Feature Discussion
```json
{
  "PM:FeatureDiscussion": {
    "source_weights": {
      "ProjectDocs": 0.9,
      "ProjectCode": 0.1
    },
    "rerank_instruction": "Focus exclusively on user-facing feature descriptions, product requirements, specifications, and business rationale. Avoid technical implementation details and raw code. Emphasize user stories, acceptance criteria, and product impact.",
    "filters": {
      "include_doc_types": ["Spec", "Requirement", "README"],
      "exclude_modules": ["src/", "lib/", "test/"],
      "exclude_doc_types": []
    },
    "fusion_weights": {
      "docs_dense": 0.8,
      "docs_sparse": 0.2
    },
    "context_limits": {
      "max_candidates": 48,
      "max_results": 8,
      "max_tokens": 2000
    },
    "must_include": {
      "latest_adr": false,
      "related_commits": false,
      "error_patterns": false
    }
  }
}
```

#### Requirements Analysis
```json
{
  "PM:RequirementsAnalysis": {
    "source_weights": {
      "ProjectDocs": 0.95,
      "ProjectCode": 0.05
    },
    "rerank_instruction": "Prioritize requirement specifications, user stories, acceptance criteria, and feature definitions. Focus on business logic, user workflows, and functional requirements. Include examples of similar features and their specifications.",
    "filters": {
      "include_doc_types": ["Spec", "Requirement", "ADR"],
      "exclude_modules": ["src/", "test/"]
    },
    "context_limits": {
      "max_results": 6,
      "max_tokens": 1800
    }
  }
}
```

## Default Fallback Policy

```json
{
  "Default:General": {
    "source_weights": {
      "ProjectDocs": 0.6,
      "ProjectCode": 0.4
    },
    "rerank_instruction": "Provide balanced coverage of documentation and code relevant to the query. Prioritize clear explanations and practical examples.",
    "filters": {},
    "fusion_weights": {
      "docs_dense": 0.65,
      "docs_sparse": 0.35,
      "code_dense": 0.55,
      "code_sparse": 0.45
    },
    "context_limits": {
      "max_candidates": 64,
      "max_results": 10,
      "max_tokens": 2500
    },
    "must_include": {
      "latest_adr": false,
      "related_commits": false,
      "error_patterns": false
    }
  }
}
```

## Policy Resolution Algorithm

```python
def resolve_policy(role: str, task: str, policies: dict) -> dict:
    """Resolve the appropriate policy for role and task."""

    # Try exact match first
    exact_key = f"{role}:{task}"
    if exact_key in policies:
        return policies[exact_key]

    # Try role with default task
    role_default = f"{role}:General"
    if role_default in policies:
        return policies[role_default]

    # Try task with default role
    task_default = f"Default:{task}"
    if task_default in policies:
        return policies[task_default]

    # Fall back to global default
    return policies.get("Default:General", get_hardcoded_default())

def get_hardcoded_default():
    """Return hardcoded default policy if no configuration exists."""
    return {
        "source_weights": {"ProjectDocs": 0.6, "ProjectCode": 0.4},
        "rerank_instruction": "Provide balanced and relevant information.",
        "filters": {},
        "context_limits": {"max_results": 10, "max_tokens": 2500}
    }
```

## Policy Validation

```python
import jsonschema

def validate_policy(policy_data: dict) -> tuple[bool, list]:
    """Validate policy against schema."""
    try:
        jsonschema.validate(policy_data, ROLE_POLICY_SCHEMA)

        # Additional validation
        errors = []

        for policy_key, policy in policy_data.items():
            # Validate weights sum to 1.0
            source_weights = policy.get("source_weights", {})
            weight_sum = sum(source_weights.values())
            if not (0.99 <= weight_sum <= 1.01):  # Allow for floating point precision
                errors.append(f"Source weights for {policy_key} sum to {weight_sum}, should be 1.0")

            # Validate fusion weights if present
            fusion_weights = policy.get("fusion_weights", {})
            if fusion_weights:
                docs_sum = fusion_weights.get("docs_dense", 0) + fusion_weights.get("docs_sparse", 0)
                code_sum = fusion_weights.get("code_dense", 0) + fusion_weights.get("code_sparse", 0)

                if docs_sum > 0 and not (0.99 <= docs_sum <= 1.01):
                    errors.append(f"Docs fusion weights for {policy_key} sum to {docs_sum}")
                if code_sum > 0 and not (0.99 <= code_sum <= 1.01):
                    errors.append(f"Code fusion weights for {policy_key} sum to {code_sum}")

        return len(errors) == 0, errors

    except jsonschema.ValidationError as e:
        return False, [str(e)]
```

## Configuration Loading

```python
import json
import os
from typing import Dict, Any

class PolicyManager:
    def __init__(self, config_path: str = "config/rag/role-policies.json"):
        self.config_path = config_path
        self.policies = {}
        self.load_policies()

    def load_policies(self):
        """Load policies from configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                policies = json.load(f)

            is_valid, errors = validate_policy(policies)
            if not is_valid:
                raise ValueError(f"Invalid policy configuration: {errors}")

            self.policies = policies

        except FileNotFoundError:
            logger.warning(f"Policy file {self.config_path} not found, using defaults")
            self.policies = {"Default:General": get_hardcoded_default()}

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in policy file: {e}")
            raise

    def get_policy(self, role: str, task: str) -> Dict[str, Any]:
        """Get resolved policy for role and task."""
        return resolve_policy(role, task, self.policies)

    def reload_policies(self):
        """Hot-reload policies from file."""
        self.load_policies()
```

## Environment-Specific Overrides

```json
{
  "environments": {
    "development": {
      "global_overrides": {
        "context_limits": {
          "max_candidates": 32,
          "max_results": 8,
          "max_tokens": 2000
        }
      }
    },
    "production": {
      "global_overrides": {
        "context_limits": {
          "max_candidates": 64,
          "max_results": 12,
          "max_tokens": 3000
        }
      }
    }
  }
}
```

## Related Documentation

- **[RAG System Overview](../../94-architecture/rag/rag-system-overview.md)** - Complete system architecture
- **[Hybrid Retrieval Design](../../94-architecture/rag/hybrid-retrieval-design.md)** - Pipeline implementation
- **[Setup Guide](../../02-how-to/rag/setup-rag-pipeline.md)** - Implementation instructions
- **[Configuration Templates](../../../config/rag/role-policies.json)** - Default policy configuration

---

**Status**: Schema Complete
**Last Updated**: 2025-09-23
**Version**: 1.0