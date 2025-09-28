"""
Text search index implementations for lexical search.

Provides BM25 and other text-based search implementations optimized
for keyword matching and lexical retrieval.
"""

import logging
import pickle
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

from ..core import IndexError as EmbeddingIndexError
from .base import BaseTextIndex

logger = logging.getLogger(__name__)


class BM25Index(BaseTextIndex):
    """
    BM25 text search index for lexical keyword matching.

    Implements the Best Matching 25 algorithm for probabilistic lexical
    search, providing excellent keyword-based retrieval capabilities.
    """

    def __init__(self, language: str = "english"):
        """
        Initialize BM25 index.

        Args:
            language: Language for tokenization (affects stop words)

        Raises:
            ImportError: If rank-bm25 is not available
        """
        if BM25Okapi is None:
            raise ImportError("rank-bm25 not available. Install with: pip install rank-bm25")

        self.language = language
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[str] = []
        self.doc_ids: List[str] = []
        self.tokenized_docs: List[List[str]] = []

        # Basic tokenization patterns
        self.token_pattern = re.compile(r'\b\w+\b')
        self.stop_words = self._get_stop_words(language)

    def _get_stop_words(self, language: str) -> Set[str]:
        """
        Get stop words for the specified language.

        Args:
            language: Language code

        Returns:
            Set of stop words
        """
        # Basic English stop words - in production, use NLTK or spaCy
        english_stops = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'the', 'this', 'but', 'they', 'have',
            'had', 'what', 'said', 'each', 'which', 'their', 'time', 'if'
        }

        if language.lower() == "english":
            return english_stops
        else:
            logger.warning(f"⚠️ Stop words for '{language}' not implemented, using English")
            return english_stops

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25 indexing.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        # Convert to lowercase and extract words
        tokens = self.token_pattern.findall(text.lower())

        # Remove stop words and short tokens
        tokens = [
            token for token in tokens
            if token not in self.stop_words and len(token) > 2
        ]

        return tokens

    def add_documents(self, documents: List[str], ids: List[str]) -> None:
        """
        Add documents to the BM25 index.

        Args:
            documents: List of document texts
            ids: Corresponding document IDs

        Raises:
            EmbeddingIndexError: When document addition fails
        """
        try:
            if len(documents) != len(ids):
                raise ValueError("Number of documents must match number of IDs")

            # Tokenize documents
            new_tokenized = [self._tokenize(doc) for doc in documents]

            # Add to storage
            self.documents.extend(documents)
            self.doc_ids.extend(ids)
            self.tokenized_docs.extend(new_tokenized)

            # Rebuild BM25 index
            if self.tokenized_docs:
                self.bm25 = BM25Okapi(self.tokenized_docs)

            logger.debug(f"➕ Added {len(documents)} documents to BM25 index")

        except Exception as e:
            logger.error(f"❌ Failed to add documents to BM25 index: {e}")
            raise EmbeddingIndexError(f"BM25 document addition failed: {e}") from e

    def search(self, query: str, k: int) -> List[Tuple[str, float]]:
        """
        Search BM25 index for relevant documents.

        Args:
            query: Search query text
            k: Number of results to return

        Returns:
            List of (document_id, score) tuples ordered by relevance

        Raises:
            EmbeddingIndexError: When search fails
        """
        try:
            if self.bm25 is None or len(self.doc_ids) == 0:
                return []

            # Tokenize query
            query_tokens = self._tokenize(query)

            if not query_tokens:
                return []

            # Get BM25 scores for all documents
            scores = self.bm25.get_scores(query_tokens)

            # Get top-k results
            top_indices = np.argsort(scores)[::-1][:k]

            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only return non-zero scores
                    results.append((self.doc_ids[idx], float(scores[idx])))

            return results

        except Exception as e:
            logger.error(f"❌ BM25 search failed: {e}")
            raise EmbeddingIndexError(f"BM25 search failed: {e}") from e

    def save(self, path: str) -> None:
        """
        Save BM25 index.

        Args:
            path: File path to save the index

        Raises:
            EmbeddingIndexError: When saving fails
        """
        try:
            data = {
                "documents": self.documents,
                "doc_ids": self.doc_ids,
                "tokenized_docs": self.tokenized_docs,
                "language": self.language
            }

            with open(path, 'wb') as f:
                pickle.dump(data, f)

            logger.info(f"💾 BM25 index saved to {path}")

        except Exception as e:
            logger.error(f"❌ Failed to save BM25 index: {e}")
            raise EmbeddingIndexError(f"BM25 save failed: {e}") from e

    def load(self, path: str) -> None:
        """
        Load BM25 index.

        Args:
            path: File path to load the index from

        Raises:
            EmbeddingIndexError: When loading fails
        """
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)

            self.documents = data["documents"]
            self.doc_ids = data["doc_ids"]
            self.tokenized_docs = data["tokenized_docs"]
            self.language = data.get("language", "english")

            # Rebuild BM25
            if self.tokenized_docs:
                self.bm25 = BM25Okapi(self.tokenized_docs)

            logger.info(f"📁 BM25 index loaded from {path} ({len(self.doc_ids):,} documents)")

        except Exception as e:
            logger.error(f"❌ Failed to load BM25 index: {e}")
            raise EmbeddingIndexError(f"BM25 load failed: {e}") from e

    def get_stats(self) -> Dict[str, Any]:
        """
        Get BM25 index statistics.

        Returns:
            Dictionary with index statistics
        """
        try:
            vocab_size = 0
            total_tokens = 0
            avg_doc_length = 0

            if self.tokenized_docs:
                # Calculate vocabulary size
                all_tokens = set()
                for doc_tokens in self.tokenized_docs:
                    all_tokens.update(doc_tokens)
                    total_tokens += len(doc_tokens)

                vocab_size = len(all_tokens)
                avg_doc_length = total_tokens / len(self.tokenized_docs)

            return {
                "document_count": len(self.doc_ids),
                "vocabulary_size": vocab_size,
                "total_tokens": total_tokens,
                "avg_document_length": avg_doc_length,
                "language": self.language,
                "stop_words_count": len(self.stop_words),
                "has_index": self.bm25 is not None
            }

        except Exception as e:
            logger.error(f"❌ Failed to get BM25 stats: {e}")
            return {"error": str(e)}

    def get_document_scores(self, query: str) -> List[float]:
        """
        Get BM25 scores for all documents for a given query.

        Args:
            query: Search query text

        Returns:
            List of scores for all documents in order

        Raises:
            EmbeddingIndexError: When scoring fails
        """
        try:
            if self.bm25 is None:
                return []

            query_tokens = self._tokenize(query)
            if not query_tokens:
                return [0.0] * len(self.doc_ids)

            scores = self.bm25.get_scores(query_tokens)
            return scores.tolist()

        except Exception as e:
            logger.error(f"❌ Failed to get BM25 document scores: {e}")
            raise EmbeddingIndexError(f"BM25 scoring failed: {e}") from e

    def update_document(self, doc_id: str, new_content: str) -> None:
        """
        Update an existing document in the index.

        Args:
            doc_id: Document ID to update
            new_content: New document content

        Raises:
            EmbeddingIndexError: When update fails
        """
        try:
            if doc_id not in self.doc_ids:
                raise ValueError(f"Document ID not found: {doc_id}")

            # Find document index
            doc_idx = self.doc_ids.index(doc_id)

            # Update document
            self.documents[doc_idx] = new_content
            self.tokenized_docs[doc_idx] = self._tokenize(new_content)

            # Rebuild BM25 index
            self.bm25 = BM25Okapi(self.tokenized_docs)

            logger.debug(f"✏️ Updated document {doc_id} in BM25 index")

        except Exception as e:
            logger.error(f"❌ Failed to update BM25 document: {e}")
            raise EmbeddingIndexError(f"BM25 update failed: {e}") from e

    def remove_document(self, doc_id: str) -> None:
        """
        Remove a document from the index.

        Args:
            doc_id: Document ID to remove

        Raises:
            EmbeddingIndexError: When removal fails
        """
        try:
            if doc_id not in self.doc_ids:
                raise ValueError(f"Document ID not found: {doc_id}")

            # Find document index
            doc_idx = self.doc_ids.index(doc_id)

            # Remove document
            del self.documents[doc_idx]
            del self.doc_ids[doc_idx]
            del self.tokenized_docs[doc_idx]

            # Rebuild BM25 index if documents remain
            if self.tokenized_docs:
                self.bm25 = BM25Okapi(self.tokenized_docs)
            else:
                self.bm25 = None

            logger.debug(f"🗑️ Removed document {doc_id} from BM25 index")

        except Exception as e:
            logger.error(f"❌ Failed to remove BM25 document: {e}")
            raise EmbeddingIndexError(f"BM25 removal failed: {e}") from e