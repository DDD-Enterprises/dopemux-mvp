"""
Predictive Context Restoration for Working Memory Assistant

This module provides intelligent context restoration using TF-IDF similarity
and KNN pattern matching on historical WMA snapshots and ConPort data.
Focuses on ADHD-optimized suggestions and high performance.
"""

import asyncio
import json
import math
import time
import hashlib
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
import logging
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from wma_core import DevelopmentSnapshot
from conport_client import ConPortClient

logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """Result of predictive context restoration"""
    prediction_confidence: float
    suggested_context: Dict[str, Any]
    recovery_recommendations: List[Dict[str, Any]]
    similar_historical_contexts: List[Dict[str, Any]]
    adhd_optimized_suggestions: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]

@dataclass
class ContextPattern:
    """Historical context pattern for KNN matching"""
    context_vector: List[float]  # TF-IDF vector representation
    context_data: Dict[str, Any]  # Original snapshot/context data
    timestamp: datetime
    context_type: str  # 'wma_snapshot', 'decision', 'progress_entry', 'system_pattern'

class TFIDFVectorizer:
    """TF-IDF vectorizer optimized for development context data"""

    def __init__(self, max_features: int = 1000):
        self.max_features = max_features
        self.vocabulary: Dict[str, int] = {}
        self.idf_scores: Dict[str, float] = {}
        self.total_documents = 0

    def _extract_text_features(self, context_data: Dict[str, Any]) -> str:
        """Extract relevant text features from context data for TF-IDF"""
        text_parts = []

        # Extract task-related text
        if 'current_task' in context_data:
            text_parts.append(context_data['current_task'])
        if 'thought_process' in context_data:
            text_parts.append(context_data['thought_process'])

        # Extract file and code context
        if 'current_file' in context_data and context_data['current_file']:
            file_info = context_data['current_file']
            if 'path' in file_info:
                text_parts.append(file_info['path'])
            if 'content' in file_info:
                # Take first 500 chars of content for context
                text_parts.append(file_info['content'][:500])

        # Extract decisions, progress, patterns
        if 'summary' in context_data:
            text_parts.append(context_data['summary'])
        if 'rationale' in context_data:
            text_parts.append(context_data['rationale'])
        if 'description' in context_data:
            text_parts.append(context_data['description'])
        if 'tags' in context_data and context_data['tags']:
            text_parts.extend(context_data['tags'])

        # Extract interruption type and cognitive load
        if 'interruption_type' in context_data:
            text_parts.append(context_data['interruption_type'])
        if 'cognitive_load' in context_data:
            text_parts.append(f"cognitive_load_{context_data['cognitive_load']}")

        return ' '.join(text_parts).lower()

    def fit_transform(self, contexts: List[Dict[str, Any]]) -> List[List[float]]:
        """Fit TF-IDF model and transform contexts to vectors"""
        self.total_documents = len(contexts)

        # Build vocabulary from all contexts
        all_texts = []
        for context in contexts:
            text = self._extract_text_features(context)
            all_texts.append(text)

            # Update vocabulary
            words = text.split()
            for word in words:
                if word not in self.vocabulary:
                    self.vocabulary[word] = len(self.vocabulary)
                    if len(self.vocabulary) >= self.max_features:
                        break

        # Calculate document frequencies
        doc_freq = Counter()
        for text in all_texts:
            words = set(text.split())
            for word in words:
                if word in self.vocabulary:
                    doc_freq[word] += 1

        # Calculate IDF scores
        for word, freq in doc_freq.items():
            self.idf_scores[word] = math.log(self.total_documents / (1 + freq))

        # Transform all contexts to TF-IDF vectors
        return [self._transform_single(text) for text in all_texts]

    def _transform_single(self, text: str) -> List[float]:
        """Transform single text to TF-IDF vector"""
        words = text.split()
        word_counts = Counter(words)

        # Calculate TF-IDF for each vocabulary word
        vector = [0.0] * len(self.vocabulary)
        total_words = len(words)

        if total_words == 0:
            return vector

        for word, count in word_counts.items():
            if word in self.vocabulary:
                tf = count / total_words
                idf = self.idf_scores.get(word, 0.0)
                vector[self.vocabulary[word]] = tf * idf

        return vector

    def transform(self, context: Dict[str, Any]) -> List[float]:
        """Transform single context to TF-IDF vector using fitted model"""
        text = self._extract_text_features(context)
        return self._transform_single(text)

class KNNPatternMatcher:
    """KNN implementation for pattern matching on historical context data"""

    def __init__(self, k: int = 5):
        self.k = k
        self.patterns: List[ContextPattern] = []

    def add_pattern(self, pattern: ContextPattern):
        """Add a historical pattern to the matcher"""
        self.patterns.append(pattern)

    def add_patterns(self, patterns: List[ContextPattern]):
        """Add multiple patterns at once"""
        self.patterns.extend(patterns)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def find_similar_patterns(
        self,
        query_vector: List[float],
        context_type_filter: Optional[str] = None,
        max_age_hours: Optional[int] = None
    ) -> List[Tuple[ContextPattern, float]]:
        """Find k most similar historical patterns"""
        similarities = []

        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=max_age_hours) if max_age_hours else None

        for pattern in self.patterns:
            # Apply filters
            if context_type_filter and pattern.context_type != context_type_filter:
                continue

            if cutoff_time and pattern.timestamp < cutoff_time:
                continue

            similarity = self._cosine_similarity(query_vector, pattern.context_vector)
            similarities.append((pattern, similarity))

        # Sort by similarity (descending) and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:self.k]

    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored patterns"""
        if not self.patterns:
            return {"total_patterns": 0}

        context_types = Counter(p.context_type for p in self.patterns)
        ages = [(datetime.now() - p.timestamp).total_seconds() / 3600 for p in self.patterns]

        return {
            "total_patterns": len(self.patterns),
            "context_types": dict(context_types),
            "avg_age_hours": sum(ages) / len(ages) if ages else 0,
            "oldest_pattern_hours": max(ages) if ages else 0,
            "newest_pattern_hours": min(ages) if ages else 0
        }

class ADHDContextOptimizer:
    """ADHD-aware context suggestion and ranking optimizer"""

    def __init__(self):
        self.attention_patterns = {
            'focused': {'max_suggestions': 10, 'complexity_threshold': 0.8, 'diversity_weight': 0.3},
            'scattered': {'max_suggestions': 5, 'complexity_threshold': 0.5, 'diversity_weight': 0.7},
            'overwhelmed': {'max_suggestions': 3, 'complexity_threshold': 0.3, 'diversity_weight': 0.9},
            'unknown': {'max_suggestions': 7, 'complexity_threshold': 0.6, 'diversity_weight': 0.5}
        }

    async def get_attention_state(self, user_id: str = "current_user") -> str:
        """Get current attention state from ADHD Engine"""
        try:
            from adhd_integration import ADHDEngineIntegration
            integration = ADHDEngineIntegration()
            adhd_context = await integration.get_adhd_context(user_id)
            return adhd_context.attention_state
        except Exception as e:
            return 'unknown'

            logger.error(f"Error: {e}")
    def optimize_suggestions(
        self,
        similar_patterns: List[Tuple[ContextPattern, float]],
        attention_state: str,
        energy_level: float
    ) -> List[Dict[str, Any]]:
        """Optimize suggestions based on ADHD state and energy level"""
        if attention_state not in self.attention_patterns:
            attention_state = 'unknown'

        config = self.attention_patterns[attention_state]

        # Filter by complexity and energy
        filtered_patterns = []
        for pattern, similarity in similar_patterns:
            complexity = pattern.context_data.get('complexity_score', 0.5)

            # Skip high-complexity patterns if energy is low
            if energy_level < 0.4 and complexity > 0.7:
                continue

            # Skip low-complexity patterns if energy is high (unless in overwhelm)
            if energy_level > 0.7 and complexity < 0.3 and attention_state != 'overwhelmed':
                continue

            filtered_patterns.append((pattern, similarity))

        # Apply diversity weighting
        if config['diversity_weight'] > 0:
            filtered_patterns = self._apply_diversity_weighting(
                filtered_patterns, config['diversity_weight']
            )

        # Limit number of suggestions
        filtered_patterns = filtered_patterns[:config['max_suggestions']]

        # Convert to suggestion format
        suggestions = []
        for pattern, similarity in filtered_patterns:
            suggestion = {
                'context_type': pattern.context_type,
                'similarity_score': round(similarity, 3),
                'context_data': {
                    'current_task': pattern.context_data.get('current_task', ''),
                    'complexity_score': pattern.context_data.get('complexity_score', 0.5),
                    'timestamp': pattern.timestamp.isoformat(),
                    'recovery_relevance': self._calculate_recovery_relevance(pattern, energy_level)
                },
                'adhd_optimized': True,
                'attention_state': attention_state
            }

            if 'summary' in pattern.context_data:
                suggestion['context_data']['summary'] = pattern.context_data['summary']

            suggestions.append(suggestion)

        return suggestions

    def _apply_diversity_weighting(
        self,
        patterns: List[Tuple[ContextPattern, float]],
        diversity_weight: float
    ) -> List[Tuple[ContextPattern, float]]:
        """Apply diversity weighting to prevent similar suggestions"""
        if len(patterns) <= 1:
            return patterns

        diverse_patterns = []

        # Start with highest similarity
        diverse_patterns.append(patterns[0])

        for pattern, similarity in patterns[1:]:
            # Calculate diversity penalty based on similarity to existing diverse patterns
            max_similarity_to_existing = 0
            for existing_pattern, _ in diverse_patterns:
                existing_vector = existing_pattern.context_vector
                pattern_vector = pattern.context_vector
                sim = self._cosine_similarity(existing_vector, pattern_vector)
                max_similarity_to_existing = max(max_similarity_to_existing, sim)

            # Apply diversity penalty
            diversity_penalty = diversity_weight * max_similarity_to_existing
            adjusted_similarity = similarity * (1 - diversity_penalty)

            diverse_patterns.append((pattern, adjusted_similarity))

        # Re-sort by adjusted similarity
        diverse_patterns.sort(key=lambda x: x[1], reverse=True)
        return diverse_patterns

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _calculate_recovery_relevance(self, pattern: ContextPattern, energy_level: float) -> float:
        """Calculate how relevant this pattern is for current recovery context"""
        relevance = 0.5  # Base relevance

        # Energy-appropriate complexity boost
        complexity = pattern.context_data.get('complexity_score', 0.5)
        energy_complexity_fit = 1 - abs(energy_level - complexity)
        relevance += energy_complexity_fit * 0.3

        # Recency boost (newer patterns more relevant)
        hours_old = (datetime.now() - pattern.timestamp).total_seconds() / 3600
        recency_boost = max(0, 1 - (hours_old / 168))  # 168 hours = 1 week
        relevance += recency_boost * 0.2

        return min(relevance, 1.0)

class PredictiveContextRestoration:
    """Main predictive context restoration engine"""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.vectorizer = TFIDFVectorizer(max_features=1000)
        self.pattern_matcher = KNNPatternMatcher(k=10)
        self.adhd_optimizer = ADHDContextOptimizer()
        self.conport_client = ConPortClient(workspace_id=workspace_id)

        # Performance optimizations
        self._pattern_cache = {}
        self._prediction_cache = {}  # Cache predictions by context hash
        self._vector_cache = {}      # Cache TF-IDF vectors
        self._last_training = None
        self._cache_ttl = 3600  # 1 hour
        self._prediction_cache_ttl = 300  # 5 minutes for predictions

        # Redis client for distributed caching (optional)
        self.redis_client = self._init_redis_client()

        # Thread pool for CPU-intensive operations
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="predictive")

        # Performance metrics
        self.performance_stats = {
            'training_time': 0,
            'prediction_time': 0,
            'similarity_calculations': 0,
            'cache_hit_rate': 0.0,
            'redis_cache_hits': 0,
            'redis_cache_misses': 0,
            'vector_cache_hits': 0,
            'vector_cache_misses': 0
        }

    def _init_redis_client(self):
        """Initialize Redis client for distributed caching"""
        try:
            import redis
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 1))  # Use different DB for predictions

            client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=False,  # Store bytes for vectors
                socket_connect_timeout=1.0,
                socket_timeout=1.0
            )

            # Test connection
            client.ping()
            logger.info(f"Connected to Redis for predictive caching at {redis_host}:{redis_port}")
            return client
        except Exception as e:
            logger.debug(f"Redis connection failed for predictions, using in-memory: {e}")
            return None

    async def initialize(self):
        """Initialize the predictive restoration engine"""
        await self._train_model()
        logger.info("Predictive Context Restoration initialized")

    async def _train_model(self):
        """Train the model on historical data from WMA and ConPort"""
        start_time = time.perf_counter()

        # Gather historical data
        historical_contexts = await self._gather_historical_data()

        if not historical_contexts:
            logger.warning("No historical data available for training")
            return

        # Convert to ContextPattern objects
        patterns = []
        for context_data in historical_contexts:
            # Create TF-IDF vector (will be fitted below)
            text = self.vectorizer._extract_text_features(context_data)
            temp_vector = self.vectorizer._transform_single(text)  # Placeholder

            pattern = ContextPattern(
                context_vector=temp_vector,  # Will be updated after fitting
                context_data=context_data,
                timestamp=context_data.get('timestamp', datetime.now()),
                context_type=context_data.get('context_type', 'unknown')
            )
            patterns.append(pattern)

        if len(patterns) < 2:
            logger.warning("Insufficient historical data for meaningful training")
            return

        # Fit TF-IDF model and update vectors
        context_dicts = [p.context_data for p in patterns]
        fitted_vectors = self.vectorizer.fit_transform(context_dicts)

        for pattern, vector in zip(patterns, fitted_vectors):
            pattern.context_vector = vector

        # Add patterns to KNN matcher
        self.pattern_matcher.add_patterns(patterns)

        training_time = (time.perf_counter() - start_time) * 1000
        self.performance_stats['training_time'] = training_time

        logger.info(f"Trained on {len(patterns)} historical patterns in {training_time:.1f}ms")

    async def _gather_historical_data(self) -> List[Dict[str, Any]]:
        """Gather historical WMA snapshots and ConPort data"""
        all_contexts = []

        # Get WMA snapshots (last 100 for efficiency)
        try:
            # This would integrate with MemoryManager in production
            wma_snapshots = []  # Would load from Redis/memory

            # Add mock WMA snapshot data for now
            mock_wma_data = {
                'context_type': 'wma_snapshot',
                'timestamp': datetime.now() - timedelta(hours=2),
                'current_task': 'Implementing authentication flow',
                'thought_process': 'Need to handle JWT validation and error cases',
                'complexity_score': 0.7,
                'cognitive_load': 0.6,
                'interruption_type': 'manual',
                'current_file': {'path': '/src/auth.py', 'cursor_position': {'line': 42, 'column': 10}}
            }
            all_contexts.append(mock_wma_data)

        except Exception as e:
            logger.debug(f"WMA snapshot loading failed: {e}")

        # Get ConPort data
        try:
            # Recent decisions (last 50)
            decisions = await self.conport_client.get_decisions(limit=50)
            for decision in decisions:
                context = {
                    'context_type': 'decision',
                    'timestamp': datetime.fromisoformat(decision.get('created_at', datetime.now().isoformat())),
                    'summary': decision.get('summary', ''),
                    'rationale': decision.get('rationale', ''),
                    'tags': decision.get('tags', []),
                    **decision
                }
                all_contexts.append(context)

            # Active progress entries
            progress = await self.conport_client.get_progress(limit=50)
            for item in progress:
                context = {
                    'context_type': 'progress_entry',
                    'timestamp': datetime.fromisoformat(item.get('created_at', datetime.now().isoformat())),
                    'description': item.get('description', ''),
                    'status': item.get('status', 'TODO'),
                    **item
                }
                all_contexts.append(context)

            # System patterns
            patterns = await self.conport_client.get_system_patterns(limit=20)
            for pattern in patterns:
                context = {
                    'context_type': 'system_pattern',
                    'timestamp': datetime.fromisoformat(pattern.get('created_at', datetime.now().isoformat())),
                    'name': pattern.get('name', ''),
                    'description': pattern.get('description', ''),
                    'tags': pattern.get('tags', []),
                    **pattern
                }
                all_contexts.append(context)

        except Exception as e:
            logger.debug(f"ConPort data loading failed: {e}")

        return all_contexts

    async def predict_context(
        self,
        current_context: Dict[str, Any],
        user_id: str = "current_user"
    ) -> PredictionResult:
        """Predict optimal recovery context based on current situation with caching"""
        start_time = time.perf_counter()

        try:
            # Create cache key from context (exclude timestamps for consistency)
            cache_key = self._create_context_cache_key(current_context, user_id)

            # Check prediction cache first
            cached_result = await self._get_cached_prediction(cache_key)
            if cached_result:
                self.performance_stats['redis_cache_hits'] += 1
                cached_result.performance_metrics['cache_hit'] = True
                return cached_result

            self.performance_stats['redis_cache_misses'] += 1

            # Get current ADHD state
            attention_state = await self.adhd_optimizer.get_attention_state(user_id)
            energy_level = current_context.get('energy_level', 0.5)

            # Check if model needs retraining
            await self._check_model_freshness()

            # Transform current context to vector (with caching)
            query_vector = await self._get_cached_vector(current_context)

            # Find similar historical patterns using thread pool for CPU-intensive work
            loop = asyncio.get_event_loop()
            similar_patterns = await loop.run_in_executor(
                self.executor,
                self.pattern_matcher.find_similar_patterns,
                query_vector,
                None,  # context_type_filter
                168    # max_age_hours
            )

            # Apply ADHD optimization
            optimized_suggestions = self.adhd_optimizer.optimize_suggestions(
                similar_patterns, attention_state, energy_level
            )

            # Generate recovery recommendations
            recovery_recommendations = await self._generate_recovery_recommendations(
                optimized_suggestions, current_context
            )

            # Calculate prediction confidence
            avg_similarity = sum(s['similarity_score'] for s in optimized_suggestions) / len(optimized_suggestions) if optimized_suggestions else 0
            confidence = min(avg_similarity * 0.8 + 0.2, 0.95)  # Boost minimum confidence

            # Extract suggested context from best match
            suggested_context = {}
            if optimized_suggestions:
                best_match = optimized_suggestions[0]
                suggested_context = best_match['context_data']

            # Performance metrics
            prediction_time = (time.perf_counter() - start_time) * 1000

            result = PredictionResult(
                prediction_confidence=round(confidence, 3),
                suggested_context=suggested_context,
                recovery_recommendations=recovery_recommendations,
                similar_historical_contexts=optimized_suggestions,
                adhd_optimized_suggestions=optimized_suggestions,
                performance_metrics={
                    'prediction_time_ms': round(prediction_time, 2),
                    'patterns_analyzed': len(similar_patterns),
                    'suggestions_generated': len(optimized_suggestions),
                    'attention_state': attention_state,
                    'energy_level': energy_level,
                    'cache_hit': False
                }
            )

            # Cache the result
            await self._cache_prediction(cache_key, result)

            # Update performance stats
            self.performance_stats['prediction_time'] = prediction_time
            self.performance_stats['similarity_calculations'] = len(similar_patterns)

            return result

        except Exception as e:
            logger.error(f"Context prediction failed: {e}")
            # Return minimal result on error
            return PredictionResult(
                prediction_confidence=0.0,
                suggested_context={},
                recovery_recommendations=[],
                similar_historical_contexts=[],
                adhd_optimized_suggestions=[],
                performance_metrics={'error': str(e)}
            )

    def _create_context_cache_key(self, context: Dict[str, Any], user_id: str) -> str:
        """Create a cache key from context, excluding volatile fields"""
        # Create a stable representation for caching
        stable_context = {
            k: v for k, v in context.items()
            if k not in ['timestamp', 'session_id'] and not k.startswith('_')
        }

        import hashlib
        import json

        # Create deterministic JSON string
        context_str = json.dumps(stable_context, sort_keys=True, default=str)
        context_hash = hashlib.md5(context_str.encode()).hexdigest()[:16]

        return f"pred:{user_id}:{context_hash}"

    async def _get_cached_prediction(self, cache_key: str) -> Optional[PredictionResult]:
        """Get cached prediction result"""
        try:
            if self.redis_client:
                # Try Redis first
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    # Deserialize cached result
                    import pickle, json
                    try:
                        return json.loads(cached_data)
                    except Exception:
                        try:
                            return pickle.loads(cached_data)
                        except Exception:
                            logger.warning("Cached prediction deserialization failed; entry ignored")
                            return None

            # Fall back to in-memory cache
            if cache_key in self._prediction_cache:
                entry = self._prediction_cache[cache_key]
                if time.time() - entry['timestamp'] < self._prediction_cache_ttl:
                    return entry['result']

        except Exception as e:
            logger.debug(f"Cache retrieval failed: {e}")

        return None

    async def _cache_prediction(self, cache_key: str, result: PredictionResult):
        """Cache prediction result"""
        try:
            if self.redis_client:
                # Cache in Redis
                import pickle
                serialized = pickle.dumps(result)
                self.redis_client.setex(cache_key, self._prediction_cache_ttl, serialized)
            else:
                # Cache in memory
                self._prediction_cache[cache_key] = {
                    'result': result,
                    'timestamp': time.time()
                }

                # Clean up old entries (keep last 100)
                if len(self._prediction_cache) > 100:
                    oldest_keys = sorted(
                        self._prediction_cache.keys(),
                        key=lambda k: self._prediction_cache[k]['timestamp']
                    )[:20]  # Remove oldest 20
                    for key in oldest_keys:
                        del self._prediction_cache[key]

        except Exception as e:
            logger.debug(f"Cache storage failed: {e}")

    async def _get_cached_vector(self, context: Dict[str, Any]) -> List[float]:
        """Get cached TF-IDF vector or compute and cache it"""
        # Create vector cache key
        import hashlib
        context_str = json.dumps(context, sort_keys=True, default=str)
        vector_key = hashlib.md5(context_str.encode()).hexdigest()[:16]

        # Check cache
        if vector_key in self._vector_cache:
            self.performance_stats['vector_cache_hits'] += 1
            return self._vector_cache[vector_key]

        self.performance_stats['vector_cache_misses'] += 1

        # Compute vector
        vector = self.vectorizer.transform(context)

        # Cache vector (limit cache size)
        if len(self._vector_cache) < 200:  # Keep last 200 vectors
            self._vector_cache[vector_key] = vector

        return vector

    async def _check_model_freshness(self):
        """Check if model needs retraining based on data freshness"""
        cache_key = f"{self.workspace_id}_patterns"
        current_time = datetime.now()

        # Check if we have cached patterns and they're recent
        if cache_key in self._pattern_cache:
            cache_entry = self._pattern_cache[cache_key]
            if (current_time - cache_entry['timestamp']).seconds < self._cache_ttl:
                return  # Cache is fresh

        # Retrain model with fresh data
        await self._train_model()

        # Update cache
        self._pattern_cache[cache_key] = {
            'patterns': self.pattern_matcher.patterns.copy(),
            'timestamp': current_time
        }

    async def _generate_recovery_recommendations(
        self,
        suggestions: List[Dict[str, Any]],
        current_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate personalized recovery recommendations"""
        recommendations = []

        if not suggestions:
            # Fallback recommendations when no similar context found
            recommendations.append({
                'type': 'fallback',
                'action': 'standard_recovery',
                'description': 'Use standard WMA recovery when no similar historical context available',
                'confidence': 0.8,
                'adhd_friendly': True
            })
            return recommendations

        # Generate recommendations based on top suggestions
        for i, suggestion in enumerate(suggestions[:3]):
            rec_type = 'primary' if i == 0 else 'secondary'

            recommendation = {
                'type': rec_type,
                'action': self._determine_recovery_action(suggestion),
                'description': self._generate_description(suggestion, current_context),
                'confidence': suggestion['similarity_score'],
                'context_type': suggestion['context_type'],
                'adhd_friendly': True,
                'estimated_complexity': suggestion['context_data'].get('complexity_score', 0.5)
            }

            recommendations.append(recommendation)

        return recommendations

    def _determine_recovery_action(self, suggestion: Dict[str, Any]) -> str:
        """Determine the best recovery action for this suggestion"""
        context_type = suggestion['context_type']
        complexity = suggestion['context_data'].get('complexity_score', 0.5)

        if context_type == 'wma_snapshot':
            return 'snapshot_recovery' if complexity > 0.6 else 'partial_recovery'
        elif context_type == 'decision':
            return 'decision_context'
        elif context_type == 'progress_entry':
            return 'progress_context'
        elif context_type == 'system_pattern':
            return 'pattern_guidance'
        else:
            return 'standard_recovery'

    def _generate_description(self, suggestion: Dict[str, Any], current_context: Dict[str, Any]) -> str:
        """Generate human-readable description for recovery recommendation"""
        context_type = suggestion['context_type']
        similarity = suggestion['similarity_score']

        descriptions = {
            'wma_snapshot': f"Recover to similar development session (similarity: {similarity:.2f})",
            'decision': f"Apply historical decision pattern (similarity: {similarity:.2f})",
            'progress_entry': f"Resume similar work pattern (similarity: {similarity:.2f})",
            'system_pattern': f"Follow established system pattern (similarity: {similarity:.2f})"
        }

        return descriptions.get(context_type, f"Apply similar historical context (similarity: {similarity:.2f})")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        pattern_stats = self.pattern_matcher.get_pattern_statistics()

        # Calculate cache hit rates
        total_cache_requests = self.performance_stats['redis_cache_hits'] + self.performance_stats['redis_cache_misses']
        redis_hit_rate = self.performance_stats['redis_cache_hits'] / total_cache_requests if total_cache_requests > 0 else 0.0

        total_vector_requests = self.performance_stats['vector_cache_hits'] + self.performance_stats['vector_cache_misses']
        vector_hit_rate = self.performance_stats['vector_cache_hits'] / total_vector_requests if total_vector_requests > 0 else 0.0

        return {
            'model_stats': {
                'vocabulary_size': len(self.vectorizer.vocabulary),
                'total_patterns': pattern_stats.get('total_patterns', 0),
                'context_types': pattern_stats.get('context_types', {}),
                'avg_pattern_age_hours': pattern_stats.get('avg_age_hours', 0)
            },
            'performance': self.performance_stats,
            'adhd_optimizer': {
                'attention_states_tracked': list(self.adhd_optimizer.attention_patterns.keys())
            },
            'cache_stats': {
                'pattern_cache_entries': len(self._pattern_cache),
                'prediction_cache_entries': len(self._prediction_cache),
                'vector_cache_entries': len(self._vector_cache),
                'cache_ttl_seconds': self._cache_ttl,
                'prediction_cache_ttl_seconds': self._prediction_cache_ttl,
                'redis_enabled': self.redis_client is not None,
                'redis_hit_rate': round(redis_hit_rate, 3),
                'vector_hit_rate': round(vector_hit_rate, 3)
            },
            'thread_pool_stats': {
                'max_workers': self.executor._max_workers,
                'active_threads': len(self.executor._threads) if hasattr(self.executor, '_threads') else 0
            }
        }

# Integration point for WMA service
async def create_predictive_restoration(workspace_id: str) -> PredictiveContextRestoration:
    """Factory function to create and initialize predictive context restoration"""
    restoration = PredictiveContextRestoration(workspace_id)
    await restoration.initialize()
    return restoration

async def test_predictive_restoration():
    """Test the predictive context restoration functionality"""
    workspace_id = "/Users/hue/code/dopemux-mvp"

    # Initialize restoration engine
    restoration = await create_predictive_restoration(workspace_id)

    # Test with sample context
    test_context = {
        'current_task': 'Implementing user authentication',
        'thought_process': 'Need to handle JWT validation',
        'energy_level': 0.7,
        'attention_state': 'focused',
        'complexity_score': 0.6,
        'interruption_type': 'manual'
    }

    # Make prediction
    result = await restoration.predict_context(test_context)

    logger.info("Prediction Results:")
    logger.info(f"Confidence: {result.prediction_confidence}")
    logger.info(f"Performance: {result.performance_metrics}")
    logger.info(f"Suggestions: {len(result.adhd_optimized_suggestions)}")

    for suggestion in result.adhd_optimized_suggestions[:3]:
        logger.info(f"  - {suggestion['context_type']}: {suggestion['similarity_score']:.3f}")

if __name__ == "__main__":
    asyncio.run(test_predictive_restoration())