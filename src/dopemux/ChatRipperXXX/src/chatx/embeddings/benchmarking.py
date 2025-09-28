"""Performance benchmarking framework for embedding models."""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import gc

from .base import BaseEmbeddingProvider, EmbeddingMetrics


logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """Configuration for embedding model benchmarks."""
    
    num_texts: int = 1000
    text_lengths: List[int] = field(default_factory=lambda: [50, 150, 300])
    batch_sizes: List[int] = field(default_factory=lambda: [1, 16, 32, 64])
    warmup_runs: int = 3
    measurement_runs: int = 5
    include_memory_profiling: bool = True


@dataclass
class BenchmarkResult:
    """Results from embedding model benchmark."""
    
    model_name: str
    device: str
    avg_time_per_text: float
    throughput_texts_per_second: float
    peak_memory_mb: float
    batch_performance: Dict[int, float]  # batch_size -> time_per_text
    dimension: int
    psychology_metrics: Optional[Dict[str, float]] = None  # Psychology-specific metrics


class BenchmarkRunner:
    """Runs performance benchmarks on embedding providers."""
    
    def __init__(self, config: BenchmarkConfig):
        """Initialize benchmark runner.
        
        Args:
            config: Benchmark configuration
        """
        self.config = config
    
    async def run_benchmark(self, provider: BaseEmbeddingProvider, 
                          device: str) -> BenchmarkResult:
        """Run comprehensive benchmark on a provider.
        
        Args:
            provider: Embedding provider to benchmark
            device: Device being used for inference
            
        Returns:
            BenchmarkResult with performance metrics
        """
        model_info = provider.get_model_info()
        logger.info(f"Benchmarking {model_info.name} on {device}")
        
        # Generate test corpus
        test_texts = create_test_corpus(
            self.config.num_texts, 
            self.config.text_lengths
        )
        
        # Warmup runs
        await self._run_warmup(provider, test_texts[:100])
        
        # Measure single text performance
        single_perf = await self._measure_single_performance(provider, test_texts)
        
        # Measure batch performance 
        batch_perf = await self._measure_batch_performance(provider, test_texts)
        
        # Calculate throughput
        throughput = 1.0 / single_perf if single_perf > 0 else 0.0
        
        return BenchmarkResult(
            model_name=model_info.name,
            device=device,
            avg_time_per_text=single_perf,
            throughput_texts_per_second=throughput,
            peak_memory_mb=0.0,  # TODO: Implement memory profiling
            batch_performance=batch_perf,
            dimension=provider.get_embedding_dimension()
        )
    
    async def compare_models(self, providers: List[BaseEmbeddingProvider],
                           devices: List[str]) -> 'ModelComparison':
        """Compare multiple embedding providers.
        
        Args:
            providers: List of embedding providers
            devices: List of devices to test on
            
        Returns:
            ModelComparison with results
        """
        results = []
        
        for provider, device in zip(providers, devices):
            try:
                result = await self.run_benchmark(provider, device)
                results.append(result)
            except Exception as e:
                logger.error(f"Benchmark failed for {provider}: {e}")
        
        return ModelComparison(results)
    
    async def _run_warmup(self, provider: BaseEmbeddingProvider, 
                         texts: List[str]) -> None:
        """Run warmup to stabilize performance."""
        logger.debug(f"Running {self.config.warmup_runs} warmup runs")
        
        for _ in range(self.config.warmup_runs):
            # Mix single and batch operations
            await provider.encode(texts[0])
            await provider.encode_batch(texts[:16])
            gc.collect()  # Force garbage collection between runs
    
    async def _measure_single_performance(self, provider: BaseEmbeddingProvider,
                                        texts: List[str]) -> float:
        """Measure single text encoding performance."""
        times = []
        sample_texts = random.sample(texts, min(100, len(texts)))
        
        for _ in range(self.config.measurement_runs):
            start_time = time.perf_counter()
            
            for text in sample_texts:
                await provider.encode(text)
            
            elapsed = time.perf_counter() - start_time
            times.append(elapsed / len(sample_texts))
        
        return sum(times) / len(times)
    
    async def _measure_batch_performance(self, provider: BaseEmbeddingProvider,
                                       texts: List[str]) -> Dict[int, float]:
        """Measure batch encoding performance for different batch sizes."""
        batch_performance = {}
        
        for batch_size in self.config.batch_sizes:
            if batch_size > len(texts):
                continue
                
            times = []
            
            for _ in range(self.config.measurement_runs):
                batch_texts = random.sample(texts, batch_size)
                
                start_time = time.perf_counter()
                await provider.encode_batch(batch_texts)
                elapsed = time.perf_counter() - start_time
                
                times.append(elapsed / batch_size)  # Time per text
            
            batch_performance[batch_size] = sum(times) / len(times)
        
        return batch_performance


class ModelComparison:
    """Comparison of multiple embedding model benchmark results."""
    
    def __init__(self, results: List[BenchmarkResult]):
        """Initialize comparison with benchmark results.
        
        Args:
            results: List of benchmark results to compare
        """
        self.results = results
        
        # Calculate comparison metrics
        self.fastest_model = min(results, key=lambda r: r.avg_time_per_text).model_name
        self.highest_throughput = max(results, key=lambda r: r.throughput_texts_per_second).model_name
        self.lowest_memory = min(results, key=lambda r: r.peak_memory_mb).model_name
    
    def get_recommendation(self, priority: str = "balanced") -> BenchmarkResult:
        """Get model recommendation based on priority.
        
        Args:
            priority: Priority for recommendation ("speed", "quality", "memory", "balanced")
            
        Returns:
            Recommended benchmark result
        """
        if priority == "speed":
            return min(self.results, key=lambda r: r.avg_time_per_text)
        elif priority == "quality":
            # Prefer higher dimensional models as proxy for quality
            return max(self.results, key=lambda r: r.dimension)
        elif priority == "memory":
            return min(self.results, key=lambda r: r.peak_memory_mb)
        else:  # balanced
            # Weighted score considering speed and dimension
            def balanced_score(result: BenchmarkResult) -> float:
                speed_score = 1.0 / result.avg_time_per_text
                quality_score = result.dimension / 1024.0  # Normalize
                return speed_score * 0.6 + quality_score * 0.4
            
            return max(self.results, key=balanced_score)
    
    def generate_report(self) -> str:
        """Generate human-readable comparison report.
        
        Returns:
            Formatted comparison report
        """
        lines = ["Embedding Model Benchmark Comparison", "=" * 40, ""]
        
        for result in sorted(self.results, key=lambda r: r.avg_time_per_text):
            lines.append(f"Model: {result.model_name}")
            lines.append(f"  Device: {result.device}")
            lines.append(f"  Avg time per text: {result.avg_time_per_text:.4f}s")
            lines.append(f"  Throughput: {result.throughput_texts_per_second:.1f} texts/sec")
            lines.append(f"  Peak memory: {result.peak_memory_mb:.1f}MB")
            lines.append(f"  Dimension: {result.dimension}")
            lines.append("")
        
        lines.extend([
            "Summary:",
            f"  Fastest: {self.fastest_model}",
            f"  Highest throughput: {self.highest_throughput}",
            f"  Lowest memory: {self.lowest_memory}"
        ])
        
        return "\n".join(lines)


def create_test_corpus(num_texts: int = 1000, 
                      text_lengths: Optional[List[int]] = None) -> List[str]:
    """Create a test corpus for benchmarking.
    
    Args:
        num_texts: Number of texts to generate
        text_lengths: Target lengths for generated texts
        
    Returns:
        List of test texts
    """
    if text_lengths is None:
        text_lengths = [50, 150, 300]
    
    # Sample conversational patterns
    patterns = [
        "Hey {name}, how was your {event} today?",
        "Thanks for {action}, really appreciate it!",
        "What do you think about {topic}? I'm curious to hear your perspective.",
        "Just wanted to check in and see how you're doing with {situation}.",
        "Can you help me understand {concept}? I'm having trouble with it.",
        "I love how you {quality}. It always makes me feel better.",
        "Remember when we {memory}? That was such a great time.",
        "I'm excited about {future_event}. Are you planning to {action}?",
        "Sorry about {mistake}. I'll make sure to {resolution} next time.",
        "Your advice about {topic} really helped me with {outcome}."
    ]
    
    # Sample words for filling patterns
    names = ["Alex", "Sam", "Jordan", "Casey", "Riley", "Taylor"]
    events = ["meeting", "interview", "presentation", "workout", "class"]
    actions = ["helping out", "being there", "listening", "understanding"]
    topics = ["work", "travel", "hobbies", "goals", "relationships"]
    situations = ["the new job", "moving", "the project", "family stuff"]
    
    corpus = []
    
    for _ in range(num_texts):
        # Choose target length
        target_length = random.choice(text_lengths)
        
        # Start with a pattern
        pattern = random.choice(patterns)
        text = pattern.format(
            name=random.choice(names),
            event=random.choice(events),
            action=random.choice(actions),
            topic=random.choice(topics),
            situation=random.choice(situations),
            concept=random.choice(topics),
            quality="explain things so clearly",
            memory="went to the concert",
            future_event="the weekend trip",
            mistake="yesterday's confusion",
            resolution="double-check everything",
            outcome="my presentation"
        )
        
        # Extend or trim to target length
        while len(text) < target_length:
            text += f" I think it's important to remember that {random.choice(topics)} can really make a difference."
        
        if len(text) > target_length:
            # Truncate at word boundary
            words = text[:target_length].split()
            if words:
                text = " ".join(words[:-1])
        
        corpus.append(text)
    
    return corpus


class PsychologyBenchmarkRunner(BenchmarkRunner):
    """Psychology-specialized benchmarking for embedding providers."""

    # Psychology test cases with known ground truth labels
    PSYCHOLOGY_TEST_CASES = [
        # Boundary violations
        ("You always ignore what I say", ["boundary_violation", "invalidation"]),
        ("Stop telling me what to do", ["boundary_setting", "assertiveness"]),
        ("I feel like you don't respect my decisions", ["autonomy", "respect"]),
        
        # Emotional manipulation
        ("If you loved me, you would do this", ["manipulation", "guilt_tripping"]),
        ("You're being too sensitive", ["gaslighting", "minimization"]),
        ("I never said that", ["gaslighting", "reality_denial"]),
        
        # Power dynamics
        ("You need to listen to me", ["control", "dominance"]),
        ("I'm just trying to help you", ["codependence", "enabling"]),
        ("You can't handle this on your own", ["undermining", "dependence"]),
        
        # Emotional states
        ("I feel anxious about our relationship", ["anxiety", "relationship_concern"]),
        ("I'm devastated by what happened", ["grief", "emotional_pain"]),
        ("I feel so connected to you right now", ["intimacy", "positive_emotion"]),
        
        # Repair attempts
        ("I'm sorry, I was wrong", ["repair", "accountability"]),
        ("Can we talk about what happened?", ["repair", "communication"]),
        ("I want to understand your perspective", ["empathy", "repair"]),
        
        # Escalation patterns
        ("This is ridiculous!", ["escalation", "frustration"]),
        ("Fine, whatever!", ["withdrawal", "escalation"]),
        ("You always do this!", ["criticism", "pattern_accusation"]),
    ]

    def __init__(self, config: BenchmarkConfig):
        """Initialize psychology benchmark runner."""
        super().__init__(config)

    async def run_psychology_benchmark(self, provider: BaseEmbeddingProvider, 
                                     device: str) -> BenchmarkResult:
        """Run psychology-specialized benchmark.
        
        Args:
            provider: Psychology embedding provider to benchmark
            device: Device being used for inference
            
        Returns:
            BenchmarkResult with psychology-specific metrics
        """
        # Run standard benchmark first
        standard_result = await super().run_benchmark(provider, device)
        
        # Add psychology-specific metrics
        psychology_metrics = await self._run_psychology_tests(provider)
        
        # Return enhanced result
        return BenchmarkResult(
            model_name=standard_result.model_name,
            device=standard_result.device,
            avg_time_per_text=standard_result.avg_time_per_text,
            throughput_texts_per_second=standard_result.throughput_texts_per_second,
            peak_memory_mb=standard_result.peak_memory_mb,
            batch_performance=standard_result.batch_performance,
            dimension=standard_result.dimension,
            psychology_metrics=psychology_metrics
        )

    async def _run_psychology_tests(self, provider: BaseEmbeddingProvider) -> Dict[str, float]:
        """Run psychology-specific evaluation tests.
        
        Args:
            provider: Provider to test
            
        Returns:
            Dictionary of psychology metric scores
        """
        try:
            # Test psychology content detection if provider supports it
            if hasattr(provider, 'get_psychology_confidence'):
                psychology_detection_score = await self._test_psychology_detection(provider)
            else:
                psychology_detection_score = 0.0
            
            # Test embedding similarity for psychological constructs
            construct_similarity_score = await self._test_construct_similarity(provider)
            
            # Test consistency on psychology vs generic content
            consistency_score = await self._test_psychology_consistency(provider)
            
            return {
                'psychology_detection_accuracy': psychology_detection_score,
                'psychological_construct_similarity': construct_similarity_score,
                'psychology_generic_consistency': consistency_score,
                'overall_psychology_score': (
                    psychology_detection_score * 0.4 +
                    construct_similarity_score * 0.4 + 
                    consistency_score * 0.2
                )
            }
            
        except Exception as e:
            logger.warning(f"Psychology benchmarking failed: {e}")
            return {'error': str(e)}

    async def _test_psychology_detection(self, provider) -> float:
        """Test psychology content detection accuracy."""
        correct_predictions = 0
        total_tests = 0
        
        # Test on known psychology vs non-psychology content
        psychology_texts = [text for text, _ in self.PSYCHOLOGY_TEST_CASES[:10]]
        generic_texts = [
            "The weather is nice today",
            "I need to go to the store", 
            "The meeting is at 3pm",
            "Can you pass the salt?",
            "The movie was interesting"
        ]
        
        for text in psychology_texts:
            confidence = provider.get_psychology_confidence(text)
            if confidence > 0.5:  # Should detect as psychological
                correct_predictions += 1
            total_tests += 1
        
        for text in generic_texts:
            confidence = provider.get_psychology_confidence(text)
            if confidence <= 0.5:  # Should detect as non-psychological
                correct_predictions += 1
            total_tests += 1
        
        return correct_predictions / total_tests if total_tests > 0 else 0.0

    async def _test_construct_similarity(self, provider: BaseEmbeddingProvider) -> float:
        """Test embedding similarity for related psychological constructs."""
        # Test pairs of related psychological concepts
        related_pairs = [
            ("I feel manipulated", "You're gaslighting me"),
            ("I'm setting a boundary", "I need you to respect my limits"),
            ("I feel anxious", "This makes me worried"),
            ("I'm sorry I hurt you", "I want to make this right"),
            ("You're controlling me", "I feel dominated by you")
        ]
        
        unrelated_pairs = [
            ("I feel anxious", "The weather is nice"),
            ("You're manipulating me", "I need groceries"),
            ("I'm setting boundaries", "The car is red"),
        ]
        
        try:
            # Get embeddings for all texts
            related_similarities = []
            for text1, text2 in related_pairs:
                emb1 = await provider.encode(text1)
                emb2 = await provider.encode(text2)
                similarity = self._cosine_similarity(emb1, emb2)
                related_similarities.append(similarity)
            
            unrelated_similarities = []
            for text1, text2 in unrelated_pairs:
                emb1 = await provider.encode(text1)
                emb2 = await provider.encode(text2)
                similarity = self._cosine_similarity(emb1, emb2)
                unrelated_similarities.append(similarity)
            
            # Related pairs should have higher similarity than unrelated
            avg_related = sum(related_similarities) / len(related_similarities)
            avg_unrelated = sum(unrelated_similarities) / len(unrelated_similarities)
            
            # Score based on separation between related and unrelated
            separation = avg_related - avg_unrelated
            return min(max(separation, 0.0), 1.0)  # Clamp between 0 and 1
            
        except Exception as e:
            logger.warning(f"Construct similarity test failed: {e}")
            return 0.0

    async def _test_psychology_consistency(self, provider: BaseEmbeddingProvider) -> float:
        """Test consistency of embeddings across multiple runs."""
        test_text = "I feel like you're violating my boundaries"
        
        try:
            # Generate embeddings multiple times
            embeddings = []
            for _ in range(5):
                emb = await provider.encode(test_text)
                embeddings.append(emb)
            
            # Calculate pairwise similarities
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = self._cosine_similarity(embeddings[i], embeddings[j])
                    similarities.append(sim)
            
            # Return average similarity (should be close to 1.0 for deterministic models)
            return sum(similarities) / len(similarities) if similarities else 0.0
            
        except Exception as e:
            logger.warning(f"Consistency test failed: {e}")
            return 0.0

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            import math
            
            # Calculate dot product
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            
            # Calculate magnitudes
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(a * a for a in vec2))
            
            # Avoid division by zero
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
            
        except Exception:
            return 0.0


def create_psychology_test_corpus(num_texts: int = 1000) -> List[str]:
    """Create a psychology-focused test corpus for benchmarking.
    
    Args:
        num_texts: Number of texts to generate
        
    Returns:
        List of psychology-focused test texts
    """
    psychology_patterns = [
        # Boundary and autonomy patterns
        "I need you to respect my {boundary_type} about {topic}",
        "You're crossing my boundaries when you {behavior}",
        "I feel like you don't respect my {autonomy_aspect}",
        
        # Emotional manipulation patterns  
        "If you really {cared_verb} me, you would {demand}",
        "You're being too {dismissive_word} about {concern}",
        "I never said {denial_phrase}",
        
        # Relationship dynamics
        "I feel {emotion} when you {behavior}",
        "This relationship feels {dynamic_type}",
        "I'm {repair_verb} about what happened {timeframe}",
        
        # Power and control
        "You need to {control_verb} and let me {autonomy_verb}",
        "I feel {power_emotion} in this relationship",
        "Stop {controlling_behavior} me",
    ]
    
    # Fill-in values for psychological patterns
    boundary_types = ["boundaries", "limits", "space", "privacy", "decisions"]
    topics = ["work", "family", "money", "time", "friendships", "personal choices"]
    behaviors = ["interrupting", "dismissing", "controlling", "criticizing", "ignoring"]
    autonomy_aspects = ["decisions", "feelings", "perspective", "choices", "values"]
    
    cared_verbs = ["loved", "cared about", "understood", "respected", "valued"]
    demands = ["do this for me", "change your plans", "put me first", "agree with me"]
    dismissive_words = ["sensitive", "dramatic", "emotional", "reactive", "needy"]
    concerns = ["my feelings", "this issue", "what happened", "my perspective"]
    denial_phrases = ["that", "those words", "anything like that", "what you heard"]
    
    emotions = ["anxious", "hurt", "frustrated", "disconnected", "unheard", "unseen"]
    dynamic_types = ["codependent", "toxic", "imbalanced", "unhealthy", "strained"]
    repair_verbs = ["sorry", "apologetic", "remorseful", "regretful", "concerned"]
    timeframes = ["yesterday", "earlier", "last week", "between us", "in our fight"]
    
    control_verbs = ["stop", "listen", "back off", "give me space", "respect"]
    autonomy_verbs = ["decide", "choose", "think", "feel", "be myself"]
    power_emotions = ["powerless", "controlled", "dominated", "manipulated", "trapped"]
    controlling_behaviors = ["telling", "forcing", "pressuring", "guilting", "manipulating"]
    
    corpus = []
    fill_values = {
        'boundary_type': boundary_types,
        'topic': topics, 
        'behavior': behaviors,
        'autonomy_aspect': autonomy_aspects,
        'cared_verb': cared_verbs,
        'demand': demands,
        'dismissive_word': dismissive_words,
        'concern': concerns,
        'denial_phrase': denial_phrases,
        'emotion': emotions,
        'dynamic_type': dynamic_types,
        'repair_verb': repair_verbs,
        'timeframe': timeframes,
        'control_verb': control_verbs,
        'autonomy_verb': autonomy_verbs,
        'power_emotion': power_emotions,
        'controlling_behavior': controlling_behaviors,
    }
    
    for _ in range(num_texts):
        pattern = random.choice(psychology_patterns)
        
        # Fill in pattern variables
        filled_pattern = pattern
        for var, values in fill_values.items():
            if '{' + var + '}' in filled_pattern:
                filled_pattern = filled_pattern.replace(
                    '{' + var + '}', 
                    random.choice(values)
                )
        
        corpus.append(filled_pattern)
    
    return corpus