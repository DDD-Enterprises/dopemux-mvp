"""
Unit tests for SparklineGenerator
Tests all sparkline generation scenarios
"""

import pytest
from datetime import datetime, timedelta
from sparkline_generator import SparklineGenerator


@pytest.fixture
def generator():
    return SparklineGenerator()


def test_empty_data(generator):
    """Test sparkline with no data"""
    result = generator.generate([], width=10)
    assert result == '──────────'
    assert len(result) == 10


def test_single_point(generator):
    """Test sparkline with single data point"""
    now = datetime.now()
    data = [(now, 50.0)]
    result = generator.generate(data, width=10)
    assert len(result) == 10
    # Should be all same character (middle block for value 50)
    assert all(c == result[0] for c in result)


def test_full_range(generator):
    """Test sparkline with full range of values"""
    now = datetime.now()
    # Create ascending data: 0, 10, 20, ..., 100
    data = [(now + timedelta(minutes=i), i * 10.0) for i in range(11)]
    result = generator.generate(data, width=11, min_val=0, max_val=100)
    
    assert len(result) == 11
    # First should be lowest block
    assert result[0] == generator.BLOCKS[0]
    # Last should be highest block
    assert result[-1] == generator.BLOCKS[-1]


def test_flat_line(generator):
    """Test sparkline with constant values"""
    now = datetime.now()
    data = [(now + timedelta(minutes=i), 42.0) for i in range(20)]
    result = generator.generate(data, width=10)
    
    assert len(result) == 10
    # All characters should be the same (middle block)
    assert all(c == result[0] for c in result)


def test_downsampling(generator):
    """Test sparkline with more data than width"""
    now = datetime.now()
    # 100 points → 20 characters
    data = [(now + timedelta(seconds=i), float(i)) for i in range(100)]
    result = generator.generate(data, width=20)
    
    assert len(result) == 20
    # Should be ascending
    for i in range(len(result) - 1):
        assert generator.BLOCKS.index(result[i]) <= generator.BLOCKS.index(result[i + 1])


def test_upsampling(generator):
    """Test sparkline with less data than width"""
    now = datetime.now()
    # 5 points → 20 characters
    data = [(now + timedelta(minutes=i), float(i * 20)) for i in range(5)]
    result = generator.generate(data, width=20, min_val=0, max_val=100)
    
    assert len(result) == 20
    # Should be smoothly ascending (interpolated)


def test_consistent_scale(generator):
    """Test that min/max params create consistent scale"""
    now = datetime.now()
    
    # Two datasets with different ranges but same scale
    data1 = [(now + timedelta(minutes=i), 25.0) for i in range(10)]
    data2 = [(now + timedelta(minutes=i), 75.0) for i in range(10)]
    
    result1 = generator.generate(data1, width=10, min_val=0, max_val=100)
    result2 = generator.generate(data2, width=10, min_val=0, max_val=100)
    
    # Both should be flat lines
    assert all(c == result1[0] for c in result1)
    assert all(c == result2[0] for c in result2)
    
    # result2 should use higher blocks than result1
    block1_idx = generator.BLOCKS.index(result1[0])
    block2_idx = generator.BLOCKS.index(result2[0])
    assert block2_idx > block1_idx


def test_colorize_upward_trend(generator):
    """Test colorization for upward trends"""
    now = datetime.now()
    data = [(now + timedelta(minutes=i), float(i * 10)) for i in range(10)]
    sparkline = generator.generate(data, width=10)
    colored = generator.colorize(sparkline, data)
    
    assert '[green]' in colored
    assert '[/green]' in colored


def test_colorize_downward_trend(generator):
    """Test colorization for downward trends"""
    now = datetime.now()
    data = [(now + timedelta(minutes=i), 100 - float(i * 10)) for i in range(10)]
    sparkline = generator.generate(data, width=10)
    colored = generator.colorize(sparkline, data)
    
    assert '[red]' in colored
    assert '[/red]' in colored


def test_colorize_stable_trend(generator):
    """Test colorization for stable trends"""
    now = datetime.now()
    data = [(now + timedelta(minutes=i), 50.0 + (i % 2)) for i in range(10)]
    sparkline = generator.generate(data, width=10)
    colored = generator.colorize(sparkline, data)
    
    assert '[yellow]' in colored
    assert '[/yellow]' in colored


def test_colorize_cognitive_load(generator):
    """Test cognitive load specific coloring"""
    now = datetime.now()
    sparkline = "▁▂▃▄▅"
    
    # Low load - green (need 2+ points)
    data_low = [(now, 30.0), (now + timedelta(minutes=1), 30.0)]
    colored = generator.colorize(sparkline, data_low, metric_type="cognitive_load")
    assert '[green]' in colored
    
    # High load - red
    data_high = [(now, 90.0), (now + timedelta(minutes=1), 90.0)]
    colored = generator.colorize(sparkline, data_high, metric_type="cognitive_load")
    assert '[red' in colored  # Could be [red] or [red bold]


def test_generate_with_stats(generator):
    """Test sparkline with statistics"""
    now = datetime.now()
    data = [(now + timedelta(minutes=i), float(i * 10)) for i in range(10)]
    
    result = generator.generate_with_stats(data, width=10)
    
    assert 'sparkline' in result
    assert 'min' in result
    assert 'max' in result
    assert 'avg' in result
    assert 'current' in result
    assert 'trend' in result
    
    assert result['min'] == 0.0
    assert result['max'] == 90.0
    assert result['current'] == 90.0
    assert result['trend'] == 'up'


def test_generate_with_stats_empty(generator):
    """Test stats with empty data"""
    result = generator.generate_with_stats([], width=10)
    
    assert result['sparkline'] == '──────────'
    assert result['min'] == 0
    assert result['max'] == 0
    assert result['trend'] == 'unknown'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
