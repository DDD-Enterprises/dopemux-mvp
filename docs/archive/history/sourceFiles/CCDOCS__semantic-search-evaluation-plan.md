# Semantic Search Evaluation Plan

## Datasets

- **200 mixed queries:** 100 code, 100 docs.

## Metrics

- **precision@k** (k∈{1,5,8})
- **MRR** (Mean Reciprocal Rank)
- **latency** (p50, p95)
- **rerank delta** (improvement from reranking)

## Procedures

- **Nightly regression:** automated evaluation runs
- **Change budgets:** for weights/params adjustments
- **CI reporting:** results integrated into CI pipeline

## Evaluation Query Examples

### Code Queries
- "How to initialize a new user session?"
- "Find error handling in authentication flow"
- "Show database connection configuration"

### Document Queries
- "What are the deployment requirements?"
- "Find security policy for API access"
- "Show architecture decision for microservices"