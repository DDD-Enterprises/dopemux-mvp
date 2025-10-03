"""
Hybrid Search + BM25 Fusion - Task 5
Combines dense vector search with sparse BM25 using RRF fusion.
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from rank_bm25 import BM25Okapi

from .dense_search import MultiVectorSearch, SearchResult, SearchProfile


logger = logging.getLogger(__name__)


def code_aware_tokenizer(text: str) -> List[str]:
    """
    Tokenizer optimized for code search.

    Handles:
    - camelCase: "getUserData" → ["get", "user", "data"]
    - snake_case: "get_user_data" → ["get", "user", "data"]
    - Punctuation: "user.name" → ["user", "name"]
    - Numbers: "user123" → ["user", "123"]

    Args:
        text: Text to tokenize

    Returns:
        List of tokens (lowercased)
    """
    # Split camelCase
    # Insert space before uppercase letters that follow lowercase
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

    # Split numbers from letters
    text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)

    # Replace underscores with spaces (for snake_case)
    text = text.replace('_', ' ')

    # Split on non-alphanumeric characters and extract tokens
    tokens = re.findall(r'[a-zA-Z0-9]+', text)

    # Lowercase all tokens
    tokens = [t.lower() for t in tokens if t]

    return tokens


def reciprocal_rank_fusion(
    rankings: List[List[Tuple[str, float]]],
    k: int = 60,
) -> List[Tuple[str, float]]:
    """
    Reciprocal Rank Fusion (RRF) for combining multiple rankings.

    Formula: score(doc) = Σ(1 / (k + rank_i))

    Args:
        rankings: List of rankings, each is [(doc_id, score), ...]
        k: Constant for RRF formula (default: 60, research standard)

    Returns:
        Fused ranking as [(doc_id, fused_score), ...] sorted by score
    """
    fused_scores: Dict[str, float] = {}

    for ranking in rankings:
        for rank, (doc_id, _score) in enumerate(ranking):
            # RRF formula: 1 / (k + rank)
            # rank starts at 0, so rank+1 for 1-based ranking
            rrf_score = 1.0 / (k + rank + 1)

            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + rrf_score

    # Sort by fused score (descending)
    sorted_results = sorted(
        fused_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return sorted_results


class BM25Index:
    """
    BM25 sparse search index for keyword-based retrieval.

    Features:
    - Code-aware tokenization
    - In-memory index (MVP)
    - Fast keyword search
    """

    def __init__(self, tokenizer=None):
        """
        Initialize BM25 index.

        Args:
            tokenizer: Custom tokenizer function (defaults to code_aware_tokenizer)
        """
        self.tokenizer = tokenizer or code_aware_tokenizer
        self.bm25 = None
        self.documents: List[Dict] = []
        self.doc_ids: List[str] = []

    def build_index(self, documents: List[Dict]):
        """
        Build BM25 index from documents.

        Args:
            documents: List of dicts with 'id' and searchable fields
                      Expected fields: raw_code, function_name, context_snippet
        """
        self.documents = documents
        self.doc_ids = [doc['id'] for doc in documents]

        # Create searchable corpus
        # Combine code, function name, and context for better matching
        corpus = []
        for doc in documents:
            searchable_text = " ".join([
                doc.get('raw_code', ''),
                doc.get('function_name', ''),
                doc.get('context_snippet', ''),
                doc.get('file_path', ''),
            ])

            tokens = self.tokenizer(searchable_text)
            corpus.append(tokens)

        # Build BM25 index
        self.bm25 = BM25Okapi(corpus)

        logger.info(f"Built BM25 index with {len(documents)} documents")

    def search(self, query: str, top_k: int = 100) -> List[Tuple[str, float]]:
        """
        Search index with BM25.

        Args:
            query: Search query (plain text)
            top_k: Number of results to return

        Returns:
            List of (doc_id, score) tuples, sorted by score
        """
        if self.bm25 is None:
            logger.warning("BM25 index not built, returning empty results")
            return []

        # Tokenize query
        query_tokens = self.tokenizer(query)

        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Get top-k results
        # Sort by score and get indices
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        # Create results (BM25 scores can be negative, which is fine for ranking)
        results = [
            (self.doc_ids[i], float(scores[i]))
            for i in top_indices
        ]

        logger.debug(
            f"BM25 search: query='{query}' returned {len(results)} results"
        )

        return results

    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get document by ID."""
        for doc in self.documents:
            if doc['id'] == doc_id:
                return doc
        return None


class HybridSearch:
    """
    Hybrid search combining dense vectors (MultiVectorSearch) and
    sparse keywords (BM25) using Reciprocal Rank Fusion.

    Search flow:
    1. Dense search (multi-vector) → ranked results
    2. Sparse search (BM25) → ranked results
    3. RRF fusion → combined ranking
    4. Weight application → final scores
    5. Return top-K SearchResult objects
    """

    def __init__(
        self,
        dense_search: MultiVectorSearch,
        bm25_index: BM25Index,
        rrf_k: int = 60,
    ):
        """
        Initialize hybrid search.

        Args:
            dense_search: MultiVectorSearch instance from Task 4
            bm25_index: BM25Index instance
            rrf_k: RRF constant (default: 60)
        """
        self.dense_search = dense_search
        self.bm25_index = bm25_index
        self.rrf_k = rrf_k

    async def search(
        self,
        query_vectors: Dict[str, List[float]],
        query_text: str,
        profile: Optional[SearchProfile] = None,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
        top_k: int = 100,
        filter_by: Optional[Dict] = None,
    ) -> List[SearchResult]:
        """
        Hybrid search with dense + sparse fusion.

        Args:
            query_vectors: Dict with 'content', 'title', 'breadcrumb' vectors
            query_text: Plain text query for BM25
            profile: Search profile for dense search
            dense_weight: Weight for dense search results (0-1)
            sparse_weight: Weight for sparse search results (0-1)
            top_k: Final number of results to return
            filter_by: Optional filters for dense search

        Returns:
            List of SearchResult objects, sorted by hybrid score
        """
        if profile is None:
            profile = SearchProfile.implementation()

        # 1. Dense search
        dense_results = await self.dense_search.search(
            query_content_vector=query_vectors.get('content', []),
            query_title_vector=query_vectors.get('title', []),
            query_breadcrumb_vector=query_vectors.get('breadcrumb', []),
            profile=profile,
            filter_by=filter_by,
        )

        # Convert to ranking: [(doc_id, score), ...]
        dense_ranking = [(r.id, r.score) for r in dense_results]

        # 2. Sparse search (BM25)
        sparse_ranking = self.bm25_index.search(
            query=query_text,
            top_k=profile.top_k,
        )

        logger.debug(
            f"Hybrid search: {len(dense_ranking)} dense, "
            f"{len(sparse_ranking)} sparse results"
        )

        # 3. RRF fusion
        fused_ranking = reciprocal_rank_fusion(
            rankings=[dense_ranking, sparse_ranking],
            k=self.rrf_k,
        )

        # 4. Apply weights and create SearchResult objects
        # Create lookup maps for dense and sparse scores
        dense_scores = {doc_id: score for doc_id, score in dense_ranking}
        sparse_scores = {doc_id: score for doc_id, score in sparse_ranking}

        # Create final results
        results = []
        dense_results_map = {r.id: r for r in dense_results}

        for doc_id, rrf_score in fused_ranking[:top_k]:
            # Get base scores
            dense_score = dense_scores.get(doc_id, 0.0)
            sparse_score = sparse_scores.get(doc_id, 0.0)

            # Weighted combination
            # Normalize by max score in each ranking to 0-1 range
            max_dense = max([s for _, s in dense_ranking], default=1.0)
            max_sparse = max([s for _, s in sparse_ranking], default=1.0)

            normalized_dense = dense_score / max_dense if max_dense > 0 else 0.0
            normalized_sparse = sparse_score / max_sparse if max_sparse > 0 else 0.0

            final_score = (
                dense_weight * normalized_dense +
                sparse_weight * normalized_sparse
            )

            # Get SearchResult from dense search or create from BM25 doc
            if doc_id in dense_results_map:
                result = dense_results_map[doc_id]
                # Update score to hybrid score
                result.score = final_score
                results.append(result)
            else:
                # Document only in sparse results
                bm25_doc = self.bm25_index.get_document(doc_id)
                if bm25_doc:
                    results.append(
                        SearchResult(
                            id=doc_id,
                            score=final_score,
                            payload=bm25_doc,
                            file_path=bm25_doc.get('file_path', ''),
                            function_name=bm25_doc.get('function_name'),
                            language=bm25_doc.get('language', ''),
                            content=bm25_doc.get('raw_code', ''),
                            context_snippet=bm25_doc.get('context_snippet'),
                        )
                    )

        # Sort by final hybrid score
        results.sort(key=lambda r: r.score, reverse=True)

        logger.info(
            f"Hybrid search returned {len(results)} results "
            f"(dense_weight={dense_weight}, sparse_weight={sparse_weight})"
        )

        return results


# Example usage
async def main():
    """Example usage of HybridSearch."""
    from .dense_search import MultiVectorSearch

    # Setup
    dense_search = MultiVectorSearch(collection_name="code_index")
    await dense_search.create_collection()

    # Create BM25 index
    documents = [
        {
            'id': '1',
            'raw_code': 'def calculate_user_score(user_id):\n    return score',
            'function_name': 'calculate_user_score',
            'context_snippet': 'Calculate engagement score for user',
            'file_path': 'src/scoring.py',
        },
        {
            'id': '2',
            'raw_code': 'def get_user_data(user_id):\n    return data',
            'function_name': 'get_user_data',
            'context_snippet': 'Fetch user data from database',
            'file_path': 'src/users.py',
        },
    ]

    bm25_index = BM25Index()
    bm25_index.build_index(documents)

    # Create hybrid search
    hybrid = HybridSearch(
        dense_search=dense_search,
        bm25_index=bm25_index,
    )

    # Search
    query_vectors = {
        'content': [0.1] * 1024,
        'title': [0.2] * 1024,
        'breadcrumb': [0.3] * 1024,
    }

    results = await hybrid.search(
        query_vectors=query_vectors,
        query_text="user score calculation",
        dense_weight=0.7,
        sparse_weight=0.3,
    )

    print(f"Found {len(results)} results:")
    for r in results:
        print(f"  {r.file_path}:{r.function_name} (score: {r.score:.4f})")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
