"""
Sparkline Generator - ASCII/Unicode Data Visualization
Converts time-series data into compact, readable sparklines
Based on Edward Tufte's sparkline principles
"""

from datetime import datetime
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SparklineGenerator:
    """
    Generates Unicode sparklines from time-series data
    
    Design principles:
    - High data density (maximum info in minimal space)
    - Clear trend direction (visual patterns)
    - ADHD-optimized (color-coded, quick perception)
    """
    
    # Unicode block characters for smooth rendering (8 levels)
    BLOCKS = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    
    # Alternative characters for different styles
    BLOCKS_THIN = ['⎯', '⎯', '⎽', '⎼', '⎻', '⎺', '⎺', '⎺']
    BLOCKS_BOLD = ['▔', '▔', '▀', '▀', '▄', '▄', '█', '█']
    
    def generate(
        self,
        data: List[Tuple[datetime, float]],
        width: int = 20,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        style: str = "blocks"
    ) -> str:
        """
        Generate sparkline from time-series data
        
        Args:
            data: List of (timestamp, value) tuples
            width: Desired character width of sparkline
            min_val: Force minimum value (for consistent scale across sparklines)
            max_val: Force maximum value (for consistent scale)
            style: Rendering style ("blocks", "thin", "bold")
        
        Returns:
            Unicode sparkline string
        
        Example:
            >>> gen = SparklineGenerator()
            >>> data = [(now(), 10), (now(), 20), (now(), 30)]
            >>> sparkline = gen.generate(data, width=10)
            >>> print(sparkline)  # "▁▁▃▃▅▅▆▆██"
        """
        if not data:
            return '─' * width  # Empty line if no data
        
        # Select character set
        blocks = self.BLOCKS
        if style == "thin":
            blocks = self.BLOCKS_THIN
        elif style == "bold":
            blocks = self.BLOCKS_BOLD
        
        # Extract values only
        values = [v for _, v in data]
        
        # Resample to desired width
        if len(values) > width:
            # Downsample - take average of each bucket
            values = self._downsample(values, width)
        elif len(values) < width:
            # Upsample - linear interpolation
            values = self._interpolate(values, width)
        
        # Determine scale
        min_v = min_val if min_val is not None else min(values)
        max_v = max_val if max_val is not None else max(values)
        
        if max_v == min_v:
            # Flat line - use middle block
            return blocks[len(blocks) // 2] * width
        
        # Normalize to 0-(n-1) range where n is number of blocks
        num_levels = len(blocks)
        normalized = []
        for v in values:
            # Scale to 0.0 - 1.0
            scaled = (v - min_v) / (max_v - min_v)
            # Map to block index
            block_idx = int(scaled * (num_levels - 0.001))  # Avoid index out of range
            block_idx = max(0, min(num_levels - 1, block_idx))
            normalized.append(block_idx)
        
        # Render sparkline
        return ''.join(blocks[n] for n in normalized)
    
    def _downsample(self, values: List[float], target_len: int) -> List[float]:
        """
        Downsample by averaging buckets
        
        Better than just picking every Nth value - reduces noise
        """
        bucket_size = len(values) / target_len
        result = []
        
        for i in range(target_len):
            start_idx = int(i * bucket_size)
            end_idx = int((i + 1) * bucket_size)
            bucket = values[start_idx:end_idx]
            result.append(sum(bucket) / len(bucket) if bucket else 0)
        
        return result
    
    def _interpolate(self, values: List[float], target_len: int) -> List[float]:
        """
        Linear interpolation to expand data
        
        Makes sparklines smoother when we have few data points
        """
        if len(values) == 1:
            return values * target_len
        
        result = []
        step = (len(values) - 1) / (target_len - 1)
        
        for i in range(target_len):
            idx = i * step
            idx_low = int(idx)
            idx_high = min(idx_low + 1, len(values) - 1)
            weight = idx - idx_low
            
            # Linear interpolation
            val = values[idx_low] * (1 - weight) + values[idx_high] * weight
            result.append(val)
        
        return result
    
    def colorize(
        self,
        sparkline: str,
        data: List[Tuple[datetime, float]],
        metric_type: str = "auto"
    ) -> str:
        """
        Add ADHD-optimized color based on trends and values
        
        Args:
            sparkline: Plain sparkline string
            data: Original time-series data
            metric_type: Type of metric ("cognitive_load", "velocity", "switches", "auto")
        
        Returns:
            Sparkline wrapped in Rich color tags
        """
        if not data or len(data) < 2:
            return f"[dim white]{sparkline}[/dim white]"
        
        values = [v for _, v in data]
        
        # Auto-detect metric type or use specific coloring
        if metric_type == "cognitive_load":
            return self._color_cognitive_load(sparkline, values)
        elif metric_type == "velocity":
            return self._color_velocity(sparkline, values)
        elif metric_type == "switches":
            return self._color_switches(sparkline, values)
        else:
            # Auto: trend-based coloring
            return self._color_trend(sparkline, values)
    
    def _color_trend(self, sparkline: str, values: List[float]) -> str:
        """Color based on trend direction"""
        if len(values) < 3:
            return sparkline
        
        # Compare recent average to older average
        recent_avg = sum(values[-3:]) / min(3, len(values))
        older_avg = sum(values[:3]) / min(3, len(values))
        
        if recent_avg > older_avg * 1.1:
            # Upward trend - green
            return f"[green]{sparkline}[/green]"
        elif recent_avg < older_avg * 0.9:
            # Downward trend - red
            return f"[red]{sparkline}[/red]"
        else:
            # Stable - yellow
            return f"[yellow]{sparkline}[/yellow]"
    
    def _color_cognitive_load(self, sparkline: str, values: List[float]) -> str:
        """Color cognitive load based on current level"""
        current = values[-1] if values else 50
        
        if current < 50:
            return f"[green]{sparkline}[/green]"  # Optimal
        elif current < 70:
            return f"[yellow]{sparkline}[/yellow]"  # Moderate
        elif current < 85:
            return f"[orange]{sparkline}[/orange]"  # High
        else:
            return f"[red bold]{sparkline}[/red bold]"  # Critical
    
    def _color_velocity(self, sparkline: str, values: List[float]) -> str:
        """Color task velocity - higher is better"""
        if len(values) < 2:
            return sparkline
        
        current = values[-1]
        avg = sum(values) / len(values)
        
        if current > avg * 1.2:
            return f"[green bold]{sparkline}[/green bold]"  # Excellent
        elif current > avg:
            return f"[green]{sparkline}[/green]"  # Good
        elif current > avg * 0.8:
            return f"[yellow]{sparkline}[/yellow]"  # Average
        else:
            return f"[red]{sparkline}[/red]"  # Below average
    
    def _color_switches(self, sparkline: str, values: List[float]) -> str:
        """Color context switches - lower is better"""
        if len(values) < 2:
            return sparkline
        
        current = values[-1]
        avg = sum(values) / len(values)
        
        if current < avg * 0.8:
            return f"[green]{sparkline}[/green]"  # Few switches - good!
        elif current < avg:
            return f"[yellow]{sparkline}[/yellow]"  # Normal
        elif current < avg * 1.2:
            return f"[orange]{sparkline}[/orange]"  # High
        else:
            return f"[red]{sparkline}[/red]"  # Very high - bad!
    
    def generate_with_stats(
        self,
        data: List[Tuple[datetime, float]],
        width: int = 20,
        **kwargs
    ) -> dict:
        """
        Generate sparkline with additional statistics
        
        Returns:
            {
                'sparkline': str,
                'min': float,
                'max': float,
                'avg': float,
                'current': float,
                'trend': str  # 'up', 'down', 'stable'
            }
        """
        sparkline = self.generate(data, width, **kwargs)
        
        if not data:
            return {
                'sparkline': sparkline,
                'min': 0,
                'max': 0,
                'avg': 0,
                'current': 0,
                'trend': 'unknown'
            }
        
        values = [v for _, v in data]
        
        # Calculate stats
        min_val = min(values)
        max_val = max(values)
        avg_val = sum(values) / len(values)
        current_val = values[-1]
        
        # Determine trend
        if len(values) >= 3:
            recent_avg = sum(values[-3:]) / min(3, len(values))
            older_avg = sum(values[:3]) / min(3, len(values))
            
            if recent_avg > older_avg * 1.1:
                trend = 'up'
            elif recent_avg < older_avg * 0.9:
                trend = 'down'
            else:
                trend = 'stable'
        else:
            trend = 'unknown'
        
        return {
            'sparkline': sparkline,
            'min': min_val,
            'max': max_val,
            'avg': avg_val,
            'current': current_val,
            'trend': trend
        }
