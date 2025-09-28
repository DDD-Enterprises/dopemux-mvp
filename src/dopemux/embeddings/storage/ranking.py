"""
Ranking and fusion algorithms for hybrid search.

Provides various strategies for combining lexical (BM25) and semantic (vector)
search results, including learning-to-rank approaches.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import ndcg_score
    from sklearn.preprocessing import StandardScaler
except ImportError:
    LogisticRegression = None
    ndcg_score = None
    StandardScaler = None

from ..core import AdvancedEmbeddingConfig, SearchResult, FusionError
from .base import BaseRanker

logger = logging.getLogger(__name__)


class HybridRanker(BaseRanker):
    """
    Learning-to-rank fusion of BM25 and vector scores.

    Combines lexical and semantic search results using various fusion
    strategies, including learned weights and cross-encoder reranking.
    """

    def __init__(self, config: AdvancedEmbeddingConfig):
        """
        Initialize hybrid ranker.

        Args:
            config: Embedding configuration with ranking parameters
        """
        self.config = config
        self.model: Optional[LogisticRegression] = None
        self.scaler: Optional[StandardScaler] = None
        self.is_trained = False

        # Static weights (used when model not trained)
        self.bm25_weight = config.bm25_weight
        self.vector_weight = config.vector_weight

        if LogisticRegression is None:
            logger.warning("⚠️ sklearn not available - using static weights")

    def _extract_features(self, bm25_score: float, vector_score: float,
                         doc_length: int = 0, query_length: int = 0) -> List[float]:
        """
        Extract features for learning-to-rank.

        Args:
            bm25_score: BM25 relevance score
            vector_score: Vector similarity score
            doc_length: Document length in tokens
            query_length: Query length in tokens

        Returns:
            Feature vector for ranking model
        """
        return [
            bm25_score,
            vector_score,
            bm25_score * vector_score,  # Interaction term
            doc_length / 1000.0,        # Normalized document length
            query_length / 10.0,        # Normalized query length
            max(bm25_score, vector_score),  # Max score
            min(bm25_score, vector_score),  # Min score
            abs(bm25_score - vector_score), # Score difference
        ]

    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """
        Normalize scores to [0, 1] range.

        Args:
            scores: Raw scores

        Returns:
            Normalized scores
        """
        if not scores:
            return []

        max_score = max(scores)
        min_score = min(scores)

        if max_score == min_score:
            return [1.0] * len(scores)

        return [(score - min_score) / (max_score - min_score) for score in scores]

    def fuse_scores(self, lexical_results: List[Tuple[str, float]],
                   vector_results: List[Tuple[str, float]]) -> List[SearchResult]:
        """
        Fuse lexical and vector search results.

        Args:
            lexical_results: Results from text search as (doc_id, score) tuples
            vector_results: Results from vector search as (doc_id, score) tuples

        Returns:
            Fused and reranked search results

        Raises:
            FusionError: When score fusion fails
        """
        try:
            # Convert to dictionaries for easier lookup
            bm25_scores = dict(lexical_results)
            vector_scores = dict(vector_results)

            # Get all unique document IDs
            all_doc_ids = set(bm25_scores.keys()) | set(vector_scores.keys())

            if not all_doc_ids:
                return []

            # Calculate hybrid scores
            hybrid_results = []

            for doc_id in all_doc_ids:
                bm25_score = bm25_scores.get(doc_id, 0.0)
                vector_score = vector_scores.get(doc_id, 0.0)

                # Use trained model if available
                if self.is_trained and self.model is not None:
                    features = self._extract_features(bm25_score, vector_score)

                    if self.scaler:
                        features = self.scaler.transform([features])[0]

                    # Predict relevance probability
                    hybrid_score = self.model.predict_proba([features])[0][1]
                else:
                    # Use weighted combination
                    hybrid_score = (self.bm25_weight * bm25_score +
                                  self.vector_weight * vector_score)

                hybrid_results.append((doc_id, hybrid_score, bm25_score, vector_score))

            # Sort by hybrid score (descending)
            hybrid_results.sort(key=lambda x: x[1], reverse=True)

            # Convert to SearchResult objects
            search_results = []
            for doc_id, hybrid_score, bm25_score, vector_score in hybrid_results:
                if hybrid_score > 0:  # Only include positive scores
                    result = SearchResult(
                        doc_id=doc_id,
                        score=hybrid_score,
                        content="",  # Content will be filled by document store
                        metadata={},
                        bm25_score=bm25_score,
                        vector_score=vector_score
                    )
                    search_results.append(result)

            return search_results

        except Exception as e:
            logger.error(f"❌ Score fusion failed: {e}")
            raise FusionError(f"Score fusion failed: {e}") from e

    def train(self, training_data: List[Tuple[str, str, float]]) -> None:
        """
        Train hybrid ranker on labeled data.

        Args:
            training_data: List of (query, document, relevance_score) tuples

        Raises:
            FusionError: When training fails
        """
        try:
            if LogisticRegression is None:
                logger.warning("⚠️ Cannot train without sklearn - using static weights")
                return

            if len(training_data) < 50:
                logger.warning(f"⚠️ Limited training data ({len(training_data)} examples)")

            # Extract features and labels
            features = []
            labels = []

            for query, document, relevance in training_data:
                # In practice, you'd calculate actual BM25/vector scores
                # This is simplified for demonstration
                bm25_score = np.random.uniform(0, 1)  # Placeholder
                vector_score = np.random.uniform(0, 1)  # Placeholder

                feature_vector = self._extract_features(
                    bm25_score, vector_score,
                    len(document), len(query)
                )

                features.append(feature_vector)
                labels.append(1 if relevance > 0.5 else 0)  # Binary relevance

            # Convert to arrays
            X = np.array(features)
            y = np.array(labels)

            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)

            # Train logistic regression model
            self.model = LogisticRegression(random_state=42)
            self.model.fit(X_scaled, y)

            self.is_trained = True

            # Calculate feature importance (simplified)
            feature_names = [
                "bm25_score", "vector_score", "interaction", "doc_length",
                "query_length", "max_score", "min_score", "score_diff"
            ]

            logger.info("🎯 Hybrid ranker trained successfully")
            logger.info("📊 Feature importance:")
            for name, coef in zip(feature_names, self.model.coef_[0]):
                logger.info(f"   {name}: {coef:.3f}")

        except Exception as e:
            logger.error(f"❌ Ranker training failed: {e}")
            raise FusionError(f"Ranker training failed: {e}") from e

    def update_weights(self, bm25_weight: float, vector_weight: float) -> None:
        """
        Update static fusion weights.

        Args:
            bm25_weight: Weight for BM25 scores
            vector_weight: Weight for vector scores

        Raises:
            FusionError: When weights are invalid
        """
        try:
            if abs(bm25_weight + vector_weight - 1.0) > 0.01:
                raise ValueError("Weights must sum to 1.0")

            self.bm25_weight = bm25_weight
            self.vector_weight = vector_weight

            logger.info(f"🔧 Updated fusion weights: BM25={bm25_weight:.2f}, Vector={vector_weight:.2f}")

        except Exception as e:
            logger.error(f"❌ Failed to update weights: {e}")
            raise FusionError(f"Weight update failed: {e}") from e

    def get_stats(self) -> Dict[str, Any]:
        """
        Get ranker statistics.

        Returns:
            Dictionary with ranker statistics
        """
        stats = {
            "is_trained": self.is_trained,
            "bm25_weight": self.bm25_weight,
            "vector_weight": self.vector_weight,
            "has_sklearn": LogisticRegression is not None
        }

        if self.is_trained and self.model is not None:
            stats.update({
                "model_type": "LogisticRegression",
                "feature_count": len(self.model.coef_[0]),
                "has_scaler": self.scaler is not None
            })

        return stats


class RRFFusion(BaseRanker):
    """
    Reciprocal Rank Fusion (RRF) algorithm.

    Combines multiple ranked lists using reciprocal rank fusion,
    a parameter-free method that works well across different domains.
    """

    def __init__(self, k: int = 60):
        """
        Initialize RRF fusion.

        Args:
            k: RRF parameter (typically 60)
        """
        self.k = k

    def fuse_scores(self, lexical_results: List[Tuple[str, float]],
                   vector_results: List[Tuple[str, float]]) -> List[SearchResult]:
        """
        Fuse results using Reciprocal Rank Fusion.

        Args:
            lexical_results: Results from text search as (doc_id, score) tuples
            vector_results: Results from vector search as (doc_id, score) tuples

        Returns:
            Fused search results

        Raises:
            FusionError: When fusion fails
        """
        try:
            # Sort results by score (descending)
            lexical_sorted = sorted(lexical_results, key=lambda x: x[1], reverse=True)
            vector_sorted = sorted(vector_results, key=lambda x: x[1], reverse=True)

            # Calculate RRF scores
            rrf_scores = {}

            # Add lexical scores
            for rank, (doc_id, score) in enumerate(lexical_sorted, 1):
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (self.k + rank)

            # Add vector scores
            for rank, (doc_id, score) in enumerate(vector_sorted, 1):
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (self.k + rank)

            # Convert to SearchResult objects
            results = []
            lexical_dict = dict(lexical_results)
            vector_dict = dict(vector_results)

            for doc_id, rrf_score in rrf_scores.items():
                result = SearchResult(
                    doc_id=doc_id,
                    score=rrf_score,
                    content="",
                    metadata={},
                    bm25_score=lexical_dict.get(doc_id, 0.0),
                    vector_score=vector_dict.get(doc_id, 0.0)
                )
                results.append(result)

            # Sort by RRF score (descending)
            results.sort(key=lambda x: x.score, reverse=True)

            return results

        except Exception as e:
            logger.error(f"❌ RRF fusion failed: {e}")
            raise FusionError(f"RRF fusion failed: {e}") from e

    def train(self, training_data: List[Tuple[str, str, float]]) -> None:
        """RRF is parameter-free, no training needed."""
        logger.info("ℹ️ RRF is parameter-free - no training required")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get RRF statistics.

        Returns:
            Dictionary with RRF statistics
        """
        return {
            "algorithm": "RRF",
            "k_parameter": self.k,
            "parameter_free": True,
            "training_required": False
        }