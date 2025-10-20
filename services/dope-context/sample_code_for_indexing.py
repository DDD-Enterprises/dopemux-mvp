"""
Sample Code for Testing Contextualized Multi-Vector Indexing

This file contains various code patterns to test:
1. Function definitions with different complexity
2. Class definitions with methods
3. Nested structures
"""


def simple_function(x: int, y: int) -> int:
    """Add two numbers together."""
    return x + y


def complex_calculation(data: list[float]) -> dict:
    """
    Perform complex statistical calculations on data.

    Args:
        data: List of numeric values

    Returns:
        Dictionary with mean, median, and standard deviation
    """
    if not data:
        raise ValueError("Data cannot be empty")

    # Calculate mean
    mean = sum(data) / len(data)

    # Calculate median
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n % 2 == 0:
        median = (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
    else:
        median = sorted_data[n // 2]

    # Calculate standard deviation
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = variance ** 0.5

    return {
        "mean": mean,
        "median": median,
        "std_dev": std_dev,
        "count": len(data),
    }


class DataProcessor:
    """Process and analyze data with various methods."""

    def __init__(self, name: str):
        """Initialize processor with a name."""
        self.name = name
        self.processed_count = 0

    def process(self, items: list) -> list:
        """
        Process a list of items.

        This method demonstrates a simple processing workflow
        with filtering and transformation.
        """
        result = []

        for item in items:
            if item is not None:
                # Transform the item
                transformed = self._transform(item)

                # Validate
                if self._validate(transformed):
                    result.append(transformed)

        self.processed_count += len(result)
        return result

    def _transform(self, item):
        """Transform an item (private method)."""
        # Simple transformation logic
        if isinstance(item, str):
            return item.upper()
        elif isinstance(item, (int, float)):
            return item * 2
        else:
            return str(item)

    def _validate(self, item) -> bool:
        """Validate a transformed item."""
        # Basic validation
        if item is None or item == "":
            return False
        return True

    def get_statistics(self) -> dict:
        """Get processing statistics."""
        return {
            "processor_name": self.name,
            "items_processed": self.processed_count,
        }
