"""Privacy redaction system (Policy Shield)."""

import json
import logging
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from chatx.redaction.patterns import PIIPatterns, HardFailDetector, ConsistentTokenizer, PIIMatch
from chatx.schemas.validator import validate_redaction_report
from chatx.privacy.differential_privacy import DifferentialPrivacyEngine, PrivacyBudget, StatisticalQuery, DPResult

logger = logging.getLogger(__name__)


@dataclass
class PrivacyPolicy:
    """Privacy policy configuration."""
    threshold: float = 0.995  # Coverage threshold (99.5%)
    strict_mode: bool = False  # Use 99.9% threshold if True
    block_hard_fail: bool = True  # Block processing on hard-fail classes
    pseudonymize: bool = True  # Use consistent pseudonymization
    detect_names: bool = True  # Detect common names as PII
    opaque_tokens: bool = True  # Use opaque tokens instead of categories
    enable_differential_privacy: bool = True  # Enable DP for statistical aggregation
    dp_epsilon: float = 1.0  # Privacy parameter for differential privacy
    dp_delta: float = 1e-6  # Failure probability for (ε,δ)-DP
    
    def get_effective_threshold(self) -> float:
        """Get the effective coverage threshold."""
        return 0.999 if self.strict_mode else self.threshold


@dataclass
class RedactionReport:
    """Report on redaction quality and coverage."""
    coverage: float
    strict: bool
    hardfail_triggered: bool
    messages_total: int
    tokens_redacted: int
    placeholders: dict[str, int]
    coarse_label_counts: dict[str, int]
    visibility_leaks: list[str]
    notes: list[str]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class PolicyShield:
    """Privacy redaction system for protecting sensitive data."""
    
    def __init__(self, policy: Optional[PrivacyPolicy] = None, salt_file: Optional[Path] = None) -> None:
        """Initialize Policy Shield with privacy policy.
        
        Args:
            policy: Privacy policy configuration
            salt_file: Path to salt file for consistent tokenization
        """
        self.policy = policy or PrivacyPolicy()
        self.pii_detector = PIIPatterns()
        self.hard_fail_detector = HardFailDetector()
        
        # Initialize tokenizer
        salt = self._load_or_create_salt(salt_file) if salt_file else None
        self.tokenizer = ConsistentTokenizer(salt=salt)
        
        # Initialize differential privacy engine if enabled
        if self.policy.enable_differential_privacy:
            # Use salt as seed for reproducible noise if available
            seed = int.from_bytes(salt.encode()[:8], 'big') % (2**32) if salt else None
            self.dp_engine = DifferentialPrivacyEngine(random_seed=seed)
        else:
            self.dp_engine = None
        
        logger.info(f"Initialized Policy Shield with threshold: {self.policy.get_effective_threshold()}, DP enabled: {self.policy.enable_differential_privacy}")
    
    def _load_or_create_salt(self, salt_file: Path) -> str:
        """Load salt from file or create new one."""
        if salt_file.exists():
            with open(salt_file) as f:
                return f.read().strip()
        else:
            # Create new salt
            import secrets
            salt = secrets.token_hex(32)
            salt_file.parent.mkdir(parents=True, exist_ok=True)
            with open(salt_file, 'w') as f:
                f.write(salt)
            logger.info(f"Created new salt file: {salt_file}")
            return salt
    
    def _detect_pii_in_text(self, text: str) -> list[PIIMatch]:
        """Detect PII entities in text."""
        return self.pii_detector.detect_pii(text, include_names=self.policy.detect_names)
    
    def _redact_text(self, text: str) -> tuple[str, list[PIIMatch], int]:
        """Redact PII from text.
        
        Args:
            text: Original text
            
        Returns:
            Tuple of (redacted_text, pii_matches, tokens_redacted)
        """
        pii_matches = self._detect_pii_in_text(text)
        if not pii_matches:
            return text, [], 0
        
        # Sort matches by position (reverse order to maintain indices)
        sorted_matches = sorted(pii_matches, key=lambda x: x.start, reverse=True)
        
        redacted_text = text
        tokens_redacted = 0
        
        for match in sorted_matches:
            # Generate replacement token
            if self.policy.pseudonymize:
                replacement = self.tokenizer.tokenize_pii(match.text, match.type)
            else:
                replacement = f"[{match.type.upper()}]"
            
            # Replace in text
            redacted_text = (
                redacted_text[:match.start] + 
                replacement + 
                redacted_text[match.end:]
            )
            
            # Count tokens redacted (rough estimate)
            tokens_redacted += len(match.text.split())
        
        return redacted_text, pii_matches, tokens_redacted
    
    def _calculate_coverage(self, original_text: str, pii_matches: list[PIIMatch]) -> float:
        """Calculate redaction coverage.
        
        Args:
            original_text: Original text
            pii_matches: Detected PII matches
            
        Returns:
            Coverage ratio (0.0 to 1.0)
        """
        if not original_text.strip():
            return 1.0
        
        total_tokens = len(original_text.split())
        if total_tokens == 0:
            return 1.0
        
        pii_tokens = sum(len(match.text.split()) for match in pii_matches)
        coverage = max(0.0, (total_tokens - pii_tokens) / total_tokens)
        
        return coverage
    
    def _check_hard_fail_classes(self, text: str) -> list[str]:
        """Check for hard-fail content classes.
        
        Args:
            text: Text to check
            
        Returns:
            List of detected hard-fail classes
        """
        return self.hard_fail_detector.detect_hard_fail_classes(text)
    
    def redact_chunk_text(self, text: str) -> tuple[str, dict[str, Any]]:
        """Redact text chunk and return metadata.
        
        Args:
            text: Text to redact
            
        Returns:
            Tuple of (redacted_text, redaction_metadata)
        """
        # Check for hard-fail classes first
        hard_fail_classes = self._check_hard_fail_classes(text)
        if hard_fail_classes and self.policy.block_hard_fail:
            raise ValueError(f"Hard-fail classes detected: {hard_fail_classes}")
        
        # Redact PII
        redacted_text, pii_matches, tokens_redacted = self._redact_text(text)
        
        # Calculate coverage
        coverage = self._calculate_coverage(text, pii_matches)
        
        # Check coverage threshold
        threshold = self.policy.get_effective_threshold()
        if coverage < threshold:
            logger.warning(f"Coverage {coverage:.3f} below threshold {threshold}")
        
        # Build metadata
        metadata = {
            'coverage': coverage,
            'tokens_redacted': tokens_redacted,
            'pii_types': [match.type for match in pii_matches],
            'hard_fail_classes': hard_fail_classes,
            'threshold_met': coverage >= threshold,
        }
        
        return redacted_text, metadata
    
    def redact_chunks(self, chunks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], RedactionReport]:
        """Redact conversation chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Tuple of (redacted_chunks, redaction_report)
        """
        logger.info(f"Starting redaction of {len(chunks)} chunks")
        
        redacted_chunks = []
        total_tokens_redacted = 0
        coverage_scores = []
        placeholder_counts: dict[str, int] = {}
        hard_fail_triggered = False
        visibility_leaks = []
        notes = []
        
        for i, chunk in enumerate(chunks):
            try:
                original_text = chunk.get('text', '')
                if not original_text:
                    redacted_chunks.append(chunk)
                    continue
                
                # Redact the text
                redacted_text, metadata = self.redact_chunk_text(original_text)
                
                # Update chunk
                redacted_chunk = chunk.copy()
                redacted_chunk['text'] = redacted_text
                
                # Add redaction metadata to provenance
                if 'provenance' not in redacted_chunk:
                    redacted_chunk['provenance'] = {}
                redacted_chunk['provenance']['redaction'] = {
                    'coverage': metadata['coverage'],
                    'tokens_redacted': metadata['tokens_redacted'],
                    'pii_types': metadata['pii_types'],
                    'threshold_met': metadata['threshold_met'],
                }
                
                # Track statistics
                coverage_scores.append(metadata['coverage'])
                total_tokens_redacted += metadata['tokens_redacted']
                
                # Count PII types
                for pii_type in metadata['pii_types']:
                    placeholder_counts[pii_type] = placeholder_counts.get(pii_type, 0) + 1
                
                # Check for hard-fail
                if metadata['hard_fail_classes']:
                    hard_fail_triggered = True
                    notes.append(f"Chunk {i}: Hard-fail classes detected: {metadata['hard_fail_classes']}")
                
                redacted_chunks.append(redacted_chunk)
                
            except Exception as e:
                logger.error(f"Error redacting chunk {i}: {e}")
                notes.append(f"Chunk {i}: Redaction error: {str(e)}")
                # Skip this chunk or add to visibility leaks
                visibility_leaks.append(f"chunk_{i}")
        
        # Calculate overall coverage
        overall_coverage = sum(coverage_scores) / len(coverage_scores) if coverage_scores else 1.0
        
        # Build report
        report = RedactionReport(
            coverage=overall_coverage,
            strict=self.policy.strict_mode,
            hardfail_triggered=hard_fail_triggered,
            messages_total=len(chunks),
            tokens_redacted=total_tokens_redacted,
            placeholders=placeholder_counts,
            coarse_label_counts={},  # Would be populated from label taxonomy
            visibility_leaks=visibility_leaks,
            notes=notes,
        )
        
        logger.info(f"Redaction complete: {overall_coverage:.3f} coverage, {total_tokens_redacted} tokens redacted")
        return redacted_chunks, report
    
    def save_redaction_report(self, report: RedactionReport, output_file: Path) -> None:
        """Save redaction report to file.
        
        Args:
            report: Redaction report
            output_file: Output file path
        """
        # Validate report against schema
        try:
            is_valid, errors = validate_redaction_report(report.to_dict(), strict=False)
            if not is_valid:
                logger.warning(f"Redaction report validation warnings: {errors}")
        except Exception as e:
            logger.warning(f"Could not validate redaction report: {e}")
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        logger.info(f"Redaction report saved to: {output_file}")
    
    def get_tokenizer_stats(self) -> dict[str, Any]:
        """Get tokenizer statistics."""
        return self.tokenizer.get_mapping_stats()
    
    def preflight_cloud_check(
        self,
        redacted_chunks: list[dict[str, Any]],
        report: RedactionReport
    ) -> tuple[bool, list[str]]:
        """Preflight check for cloud processing readiness.
        
        Args:
            redacted_chunks: Redacted chunks
            report: Redaction report
            
        Returns:
            Tuple of (passed, blocking_issues)
        """
        blocking_issues = []
        
        # Check coverage threshold
        threshold = self.policy.get_effective_threshold()
        if report.coverage < threshold:
            blocking_issues.append(f"Coverage {report.coverage:.3f} below required {threshold}")
        
        # Check for hard-fail triggers
        if report.hardfail_triggered:
            blocking_issues.append("Hard-fail classes detected")
        
        # Check for visibility leaks
        if report.visibility_leaks:
            blocking_issues.append(f"Visibility leaks detected: {report.visibility_leaks}")
        
        # Check for fine-grained labels (should not exist in redacted data)
        for chunk in redacted_chunks:
            meta = chunk.get('meta', {})
            if 'labels_fine_local' in meta and meta['labels_fine_local']:
                blocking_issues.append("Fine-grained labels present in redacted data")
                break
        
        passed = len(blocking_issues) == 0
        return passed, blocking_issues
    
    def aggregate_statistics_with_dp(self, 
                                     data: list[dict[str, Any]], 
                                     queries: list[StatisticalQuery]) -> dict[str, DPResult]:
        """Perform differentially private statistical aggregation on data.
        
        This method enables safe statistical analysis over sensitive data by adding
        calibrated noise to protect individual privacy while preserving utility.
        
        Args:
            data: List of records to analyze
            queries: List of statistical queries to execute
            
        Returns:
            Dictionary mapping query names to differentially private results
            
        Raises:
            ValueError: If differential privacy is not enabled
        """
        if not self.policy.enable_differential_privacy or self.dp_engine is None:
            raise ValueError("Differential privacy is not enabled in policy")
        
        if not data:
            logger.warning("No data provided for statistical aggregation")
            return {}
        
        results = {}
        budget = PrivacyBudget(
            epsilon=self.policy.dp_epsilon / len(queries),  # Split budget across queries
            delta=self.policy.dp_delta / len(queries),
            sensitivity=1.0  # Default sensitivity
        )
        
        for i, query in enumerate(queries):
            query_name = f"{query.query_type}_{query.field_name}_{i}"
            
            try:
                if query.query_type == "count":
                    result = self.dp_engine.count_query(data, query, budget)
                elif query.query_type == "sum":
                    result = self.dp_engine.sum_query(data, query, budget)
                elif query.query_type == "histogram":
                    result = self.dp_engine.histogram_query(data, query, budget)
                elif query.query_type == "mean":
                    # Need bounds for mean queries - use reasonable defaults
                    value_bounds = (-1000.0, 1000.0)  # Can be configured per query
                    result = self.dp_engine.mean_query(data, query, budget, value_bounds)
                else:
                    logger.error(f"Unsupported query type: {query.query_type}")
                    continue
                
                results[query_name] = result
                logger.debug(f"Executed DP query {query_name}: privacy cost ε={budget.epsilon:.3f}")
                
            except Exception as e:
                logger.error(f"Error executing DP query {query_name}: {e}")
                continue
        
        logger.info(f"Completed {len(results)} differential privacy queries")
        return results
    
    def generate_privacy_safe_summary(self, 
                                      redacted_chunks: list[dict[str, Any]], 
                                      include_label_distribution: bool = True) -> dict[str, Any]:
        """Generate privacy-safe statistical summary of redacted data.
        
        Uses differential privacy to provide aggregate insights while protecting
        individual privacy. Safe for cloud processing or external analysis.
        
        Args:
            redacted_chunks: List of redacted conversation chunks
            include_label_distribution: Whether to include label distribution statistics
            
        Returns:
            Privacy-safe summary statistics
        """
        if not self.policy.enable_differential_privacy or self.dp_engine is None:
            logger.warning("Differential privacy not enabled - returning basic counts only")
            return {
                'total_chunks': len(redacted_chunks),
                'privacy_method': 'none',
                'warning': 'Differential privacy not enabled'
            }
        
        # Prepare queries for key statistics
        queries = [
            StatisticalQuery(query_type="count", field_name="chunk_id"),
            StatisticalQuery(query_type="sum", field_name="text", 
                           filter_conditions=None),  # Total text length approximation
        ]
        
        # Add label distribution queries if requested
        if include_label_distribution:
            # Get unique coarse labels from the data
            all_labels = set()
            for chunk in redacted_chunks:
                labels = chunk.get('meta', {}).get('labels_coarse', [])
                all_labels.update(labels)
            
            # Create count queries for each label (simplified approach)
            for label in all_labels:
                queries.append(
                    StatisticalQuery(
                        query_type="count", 
                        field_name=f"has_label_{label}",
                        filter_conditions=None  # Will count records where has_label_{label} = 1
                    )
                )
        
        # Flatten chunks for DP engine (it expects flat dict records)
        flat_data = []
        for chunk in redacted_chunks:
            flat_record = {
                'chunk_id': chunk.get('chunk_id', ''),
                'text': len(chunk.get('text', '')),  # Use length instead of content
                'platform': chunk.get('meta', {}).get('platform', ''),
                'date': chunk.get('meta', {}).get('date_start', ''),
            }
            
            # Flatten labels for filtering
            labels = chunk.get('meta', {}).get('labels_coarse', [])
            for label in labels:
                flat_record[f'has_label_{label}'] = 1
            
            # Ensure all label fields exist (set to 0 if not present)
            all_labels = set()
            for c in redacted_chunks:
                all_labels.update(c.get('meta', {}).get('labels_coarse', []))
            for label in all_labels:
                if f'has_label_{label}' not in flat_record:
                    flat_record[f'has_label_{label}'] = 0
            
            flat_data.append(flat_record)
        
        # Execute DP queries
        dp_results = self.aggregate_statistics_with_dp(flat_data, queries)
        
        # Build privacy-safe summary
        total_chunks = 0
        total_text_length = 0
        
        # Extract values from DPResult objects
        for query_name, result in dp_results.items():
            if 'count_chunk_id' in query_name:
                total_chunks = result.value
            elif 'sum_text' in query_name:
                total_text_length = result.value
        
        summary = {
            'total_chunks': total_chunks,
            'avg_chunk_length': total_text_length / max(1, len(flat_data)) if total_text_length > 0 else 0,
            'privacy_method': 'differential_privacy',
            'privacy_parameters': {
                'epsilon': self.policy.dp_epsilon,
                'delta': self.policy.dp_delta,
                'noise_calibrated': True
            },
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        # Add label distribution if requested
        if include_label_distribution:
            label_counts = {}
            for query_name, result in dp_results.items():
                if query_name.startswith('count_has_label_'):
                    # Extract label name from query name
                    label_name = query_name.replace('count_has_label_', '').split('_')[0]
                    label_counts[label_name] = result.value
            
            if label_counts:
                summary['label_distribution'] = label_counts
        
        logger.info(f"Generated privacy-safe summary with ε={self.policy.dp_epsilon}")
        return summary
    
    def get_differential_privacy_budget_summary(self) -> dict[str, float]:
        """Get summary of differential privacy budget usage.
        
        Returns:
            Dictionary mapping query types to cumulative epsilon usage
        """
        if not self.dp_engine:
            return {}
        return self.dp_engine.get_privacy_budget_summary()
