"""Differential privacy mechanisms for statistical aggregation."""

import math
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)


class NoiseDistribution(str, Enum):
    """Supported noise distributions for differential privacy."""
    LAPLACE = "laplace"
    GAUSSIAN = "gaussian"


@dataclass
class PrivacyBudget:
    """Privacy budget configuration for differential privacy."""
    epsilon: float = 1.0  # Privacy parameter (smaller = more private)
    delta: float = 1e-6   # Failure probability for (ε,δ)-DP
    sensitivity: float = 1.0  # Global sensitivity of the query
    
    def __post_init__(self) -> None:
        """Validate privacy parameters."""
        if self.epsilon <= 0:
            raise ValueError("Epsilon must be positive")
        if self.delta < 0 or self.delta >= 1:
            raise ValueError("Delta must be in [0, 1)")
        if self.sensitivity <= 0:
            raise ValueError("Sensitivity must be positive")


@dataclass 
class StatisticalQuery:
    """Definition of a statistical query with privacy requirements."""
    query_type: str  # "count", "sum", "mean", "variance", "histogram"
    field_name: str  # Field to aggregate
    filter_conditions: Optional[Dict[str, Any]] = None
    bin_config: Optional[Dict[str, Any]] = None  # For histograms
    
    
@dataclass
class DPResult:
    """Result of a differentially private query."""
    value: Union[float, List[float]]  # The noisy result
    privacy_cost: PrivacyBudget  # Privacy budget consumed
    noise_scale: float  # Scale of noise added
    confidence_interval: Optional[tuple[float, float]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {
                'timestamp': datetime.utcnow().isoformat(),
                'algorithm': 'laplace_mechanism',
                'calibrated': True
            }


class DifferentialPrivacyEngine:
    """Engine for applying differential privacy to statistical queries."""
    
    def __init__(self, random_seed: Optional[int] = None):
        """Initialize differential privacy engine.
        
        Args:
            random_seed: Optional seed for reproducible noise generation
        """
        self.rng = np.random.Generator(np.random.PCG64(random_seed))
        self._budget_tracker: Dict[str, float] = {}  # Track cumulative epsilon usage
        
        logger.info("Initialized Differential Privacy Engine")
    
    def _generate_laplace_noise(self, scale: float, size: Optional[int] = None) -> Union[float, npt.NDArray[np.float64]]:
        """Generate Laplace noise with given scale.
        
        Args:
            scale: Scale parameter for Laplace distribution
            size: Number of samples (None for single value)
            
        Returns:
            Noise value(s) from Laplace distribution
        """
        return self.rng.laplace(0, scale, size)
    
    def _generate_gaussian_noise(self, scale: float, size: Optional[int] = None) -> Union[float, npt.NDArray[np.float64]]:
        """Generate Gaussian noise with given scale.
        
        Args:
            scale: Standard deviation for Gaussian distribution  
            size: Number of samples (None for single value)
            
        Returns:
            Noise value(s) from Gaussian distribution
        """
        return self.rng.normal(0, scale, size)
    
    def _calculate_noise_scale(self, budget: PrivacyBudget, distribution: NoiseDistribution) -> float:
        """Calculate noise scale for given privacy budget.
        
        Args:
            budget: Privacy budget configuration
            distribution: Type of noise distribution
            
        Returns:
            Scale parameter for noise distribution
        """
        if distribution == NoiseDistribution.LAPLACE:
            return budget.sensitivity / budget.epsilon
        elif distribution == NoiseDistribution.GAUSSIAN:
            # For (ε,δ)-DP with Gaussian mechanism
            if budget.delta == 0:
                raise ValueError("Delta must be > 0 for Gaussian mechanism")
            c = math.sqrt(2 * math.log(1.25 / budget.delta))
            return c * budget.sensitivity / budget.epsilon
        else:
            raise ValueError(f"Unsupported noise distribution: {distribution}")
    
    def _add_noise(self, value: Union[float, List[float]], 
                   budget: PrivacyBudget, 
                   distribution: NoiseDistribution = NoiseDistribution.LAPLACE) -> Union[float, List[float]]:
        """Add calibrated noise to a value or list of values.
        
        Args:
            value: True value(s) to protect
            budget: Privacy budget
            distribution: Type of noise to add
            
        Returns:
            Noisy value(s) 
        """
        scale = self._calculate_noise_scale(budget, distribution)
        
        if isinstance(value, list):
            noise = self._generate_laplace_noise(scale, len(value)) if distribution == NoiseDistribution.LAPLACE else self._generate_gaussian_noise(scale, len(value))
            if isinstance(noise, np.ndarray):
                return [float(v + n) for v, n in zip(value, noise)]
            else:
                # Single noise value for all list elements (shouldn't happen, but handle gracefully)
                return [float(v + noise) for v in value]
        else:
            noise = self._generate_laplace_noise(scale) if distribution == NoiseDistribution.LAPLACE else self._generate_gaussian_noise(scale)
            return float(value + noise)
    
    def _track_privacy_budget(self, query_id: str, epsilon_used: float) -> None:
        """Track cumulative privacy budget usage.
        
        Args:
            query_id: Identifier for the query
            epsilon_used: Privacy cost of this query
        """
        if query_id not in self._budget_tracker:
            self._budget_tracker[query_id] = 0.0
        self._budget_tracker[query_id] += epsilon_used
        
        logger.debug(f"Privacy budget for {query_id}: {self._budget_tracker[query_id]:.3f} total epsilon")
    
    def count_query(self, data: List[Dict[str, Any]], 
                    query: StatisticalQuery, 
                    budget: PrivacyBudget) -> DPResult:
        """Execute a differentially private count query.
        
        Args:
            data: List of records to count
            query: Query specification 
            budget: Privacy budget
            
        Returns:
            Differentially private count result
        """
        # Apply filter conditions if specified
        filtered_data = data
        if query.filter_conditions:
            filtered_data = [
                record for record in data
                if all(record.get(k) == v for k, v in query.filter_conditions.items())
            ]
        
        true_count = len(filtered_data)
        
        # Add noise to protect count
        noisy_count = self._add_noise(true_count, budget)
        
        # Ensure count is non-negative
        noisy_count = max(0.0, noisy_count)
        
        # Calculate noise scale for metadata
        noise_scale = self._calculate_noise_scale(budget, NoiseDistribution.LAPLACE)
        
        # Track privacy budget usage
        query_id = f"count_{query.field_name}_{hash(str(query.filter_conditions))}"
        self._track_privacy_budget(query_id, budget.epsilon)
        
        return DPResult(
            value=noisy_count,
            privacy_cost=budget,
            noise_scale=noise_scale,
            metadata={
                'query_type': 'count',
                'true_count': true_count,
                'field_name': query.field_name,
                'filter_conditions': query.filter_conditions,
                'timestamp': datetime.utcnow().isoformat(),
                'algorithm': 'laplace_mechanism'
            }
        )
    
    def sum_query(self, data: List[Dict[str, Any]], 
                  query: StatisticalQuery, 
                  budget: PrivacyBudget) -> DPResult:
        """Execute a differentially private sum query.
        
        Args:
            data: List of records
            query: Query specification
            budget: Privacy budget
            
        Returns:
            Differentially private sum result
        """
        # Apply filter conditions if specified
        filtered_data = data
        if query.filter_conditions:
            filtered_data = [
                record for record in data
                if all(record.get(k) == v for k, v in query.filter_conditions.items())
            ]
        
        # Extract values and compute sum
        values = [record.get(query.field_name, 0) for record in filtered_data]
        true_sum = sum(values)
        
        # Add noise to protect sum
        noisy_sum = self._add_noise(true_sum, budget)
        
        # Calculate noise scale for metadata
        noise_scale = self._calculate_noise_scale(budget, NoiseDistribution.LAPLACE)
        
        # Track privacy budget usage
        query_id = f"sum_{query.field_name}_{hash(str(query.filter_conditions))}"
        self._track_privacy_budget(query_id, budget.epsilon)
        
        return DPResult(
            value=noisy_sum,
            privacy_cost=budget,
            noise_scale=noise_scale,
            metadata={
                'query_type': 'sum',
                'true_sum': true_sum,
                'field_name': query.field_name,
                'filter_conditions': query.filter_conditions,
                'num_records': len(filtered_data),
                'timestamp': datetime.utcnow().isoformat(),
                'algorithm': 'laplace_mechanism'
            }
        )
    
    def histogram_query(self, data: List[Dict[str, Any]], 
                        query: StatisticalQuery, 
                        budget: PrivacyBudget) -> DPResult:
        """Execute a differentially private histogram query.
        
        Args:
            data: List of records
            query: Query specification with bin_config
            budget: Privacy budget
            
        Returns:
            Differentially private histogram result
        """
        if not query.bin_config:
            raise ValueError("bin_config required for histogram queries")
        
        # Apply filter conditions if specified
        filtered_data = data
        if query.filter_conditions:
            filtered_data = [
                record for record in data
                if all(record.get(k) == v for k, v in query.filter_conditions.items())
            ]
        
        # Extract values (filter out None values)
        values = []
        for record in filtered_data:
            val = record.get(query.field_name)
            if val is not None and isinstance(val, (int, float)):
                values.append(val)
        
        # Create histogram bins
        if 'bins' in query.bin_config:
            bins = query.bin_config['bins']
        elif 'num_bins' in query.bin_config:
            if values:
                min_val = min(values)
                max_val = max(values)
                bins = np.linspace(min_val, max_val, query.bin_config['num_bins'] + 1)
            else:
                # Default bins if no values
                bins = np.linspace(0, 1, query.bin_config['num_bins'] + 1)
        else:
            raise ValueError("bin_config must specify 'bins' or 'num_bins'")
        
        # Compute true histogram
        hist, bin_edges = np.histogram(values, bins=bins)
        true_counts = hist.tolist()
        
        # Add noise to each bin count (composition of privacy)
        # Each bin gets epsilon/num_bins to maintain total privacy budget
        bin_epsilon = budget.epsilon / max(1, len(true_counts))
        bin_budget = PrivacyBudget(epsilon=bin_epsilon, delta=budget.delta, sensitivity=budget.sensitivity)
        
        noisy_result = self._add_noise(true_counts, bin_budget)
        
        # Ensure result is a list and all counts are non-negative
        if isinstance(noisy_result, list):
            noisy_counts = [max(0.0, count) for count in noisy_result]
        else:
            # Single value returned - shouldn't happen for list input but handle gracefully
            noisy_counts = [max(0.0, noisy_result)]
        
        # Calculate noise scale for metadata
        noise_scale = self._calculate_noise_scale(bin_budget, NoiseDistribution.LAPLACE)
        
        # Track privacy budget usage
        query_id = f"histogram_{query.field_name}_{hash(str(query.filter_conditions))}"
        self._track_privacy_budget(query_id, budget.epsilon)
        
        return DPResult(
            value=noisy_counts,
            privacy_cost=budget,
            noise_scale=noise_scale,
            metadata={
                'query_type': 'histogram',
                'true_counts': true_counts,
                'bin_edges': bin_edges.tolist(),
                'field_name': query.field_name,
                'filter_conditions': query.filter_conditions,
                'num_bins': len(true_counts),
                'timestamp': datetime.utcnow().isoformat(),
                'algorithm': 'laplace_mechanism'
            }
        )
    
    def mean_query(self, data: List[Dict[str, Any]], 
                   query: StatisticalQuery, 
                   budget: PrivacyBudget,
                   value_bounds: tuple[float, float]) -> DPResult:
        """Execute a differentially private mean query.
        
        Args:
            data: List of records
            query: Query specification  
            budget: Privacy budget
            value_bounds: (min, max) bounds for values (required for mean)
            
        Returns:
            Differentially private mean result
        """
        # Apply filter conditions if specified
        filtered_data = data
        if query.filter_conditions:
            filtered_data = [
                record for record in data
                if all(record.get(k) == v for k, v in query.filter_conditions.items())
            ]
        
        # Extract values within bounds
        values = []
        for record in filtered_data:
            val = record.get(query.field_name)
            if val is not None and value_bounds[0] <= val <= value_bounds[1]:
                values.append(val)
        
        if not values:
            return DPResult(
                value=0.0,
                privacy_cost=budget,
                noise_scale=0.0,
                metadata={
                    'query_type': 'mean',
                    'num_values': 0,
                    'field_name': query.field_name,
                    'filter_conditions': query.filter_conditions,
                    'timestamp': datetime.utcnow().isoformat(),
                    'algorithm': 'laplace_mechanism'
                }
            )
        
        true_mean = sum(values) / len(values)
        
        # For mean, we need to account for sensitivity of average
        # Sensitivity = (max - min) / n, but n is also private
        # Use composition: noisy_sum / noisy_count
        
        # Split privacy budget between sum and count
        sum_budget = PrivacyBudget(epsilon=budget.epsilon/2, delta=budget.delta/2, 
                                   sensitivity=value_bounds[1] - value_bounds[0])
        count_budget = PrivacyBudget(epsilon=budget.epsilon/2, delta=budget.delta/2, 
                                     sensitivity=1.0)
        
        # Get noisy sum and count
        noisy_sum_result = self._add_noise(sum(values), sum_budget)
        noisy_count_result = self._add_noise(len(values), count_budget)
        
        # Ensure we have float values for division
        noisy_sum = float(noisy_sum_result) if not isinstance(noisy_sum_result, list) else float(noisy_sum_result[0])
        noisy_count = max(1.0, float(noisy_count_result) if not isinstance(noisy_count_result, list) else float(noisy_count_result[0]))
        
        noisy_mean = noisy_sum / noisy_count
        
        # Calculate noise scale for metadata (using sum budget as proxy)
        noise_scale = self._calculate_noise_scale(sum_budget, NoiseDistribution.LAPLACE)
        
        # Track privacy budget usage
        query_id = f"mean_{query.field_name}_{hash(str(query.filter_conditions))}"
        self._track_privacy_budget(query_id, budget.epsilon)
        
        return DPResult(
            value=noisy_mean,
            privacy_cost=budget,
            noise_scale=noise_scale,
            metadata={
                'query_type': 'mean',
                'true_mean': true_mean,
                'noisy_sum': noisy_sum,
                'noisy_count': noisy_count,
                'field_name': query.field_name,
                'filter_conditions': query.filter_conditions,
                'value_bounds': value_bounds,
                'num_values': len(values),
                'timestamp': datetime.utcnow().isoformat(),
                'algorithm': 'laplace_mechanism'
            }
        )
    
    def get_privacy_budget_summary(self) -> Dict[str, float]:
        """Get summary of privacy budget usage.
        
        Returns:
            Dictionary mapping query IDs to cumulative epsilon usage
        """
        return self._budget_tracker.copy()
    
    def reset_privacy_budget(self, query_id: Optional[str] = None) -> None:
        """Reset privacy budget tracking.
        
        Args:
            query_id: Specific query to reset, or None for all queries
        """
        if query_id:
            self._budget_tracker.pop(query_id, None)
            logger.info(f"Reset privacy budget for query: {query_id}")
        else:
            self._budget_tracker.clear()
            logger.info("Reset all privacy budgets")