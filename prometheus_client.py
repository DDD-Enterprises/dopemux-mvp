"""
Prometheus Client - Time-Series Data Fetcher
Handles queries to Prometheus for historical metrics
"""

import httpx
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PrometheusConfig:
    """Configuration for Prometheus client"""
    base_url: str = "http://localhost:9090"
    timeout: float = 5.0
    max_retries: int = 3


class PrometheusClient:
    """Async client for Prometheus API"""
    
    def __init__(self, config: Optional[PrometheusConfig] = None):
        self.config = config or PrometheusConfig()
        self.client = httpx.AsyncClient(
            timeout=self.config.timeout,
            follow_redirects=True
        )
    
    async def query_range(
        self,
        query: str,
        hours: int = 24,
        step: str = "5m"
    ) -> List[Tuple[datetime, float]]:
        """
        Query Prometheus for time-series data
        
        Args:
            query: PromQL query (e.g., 'adhd_cognitive_load')
            hours: How far back to fetch (default: 24 hours)
            step: Resolution (1m, 5m, 15m, 1h, etc.)
        
        Returns:
            List of (timestamp, value) tuples, sorted by time
            Empty list if query fails or no data available
        
        Example:
            >>> client = PrometheusClient()
            >>> data = await client.query_range('adhd_cognitive_load', hours=2, step='5m')
            >>> print(f"Got {len(data)} data points")
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            params = {
                'query': query,
                'start': start_time.timestamp(),
                'end': end_time.timestamp(),
                'step': step
            }
            
            response = await self.client.get(
                f"{self.config.base_url}/api/v1/query_range",
                params=params
            )
            
            if response.status_code != 200:
                logger.warning(
                    f"Prometheus query failed with status {response.status_code}: {response.text}"
                )
                return []
            
            data = response.json()
            
            if data.get('status') != 'success':
                logger.warning(f"Prometheus query unsuccessful: {data.get('error', 'Unknown error')}")
                return []
            
            result = data.get('data', {}).get('result', [])
            if not result:
                logger.debug(f"No data returned for query: {query}")
                return []
            
            # Extract first result (assuming single metric)
            values = result[0].get('values', [])
            
            # Convert to (datetime, float) tuples
            parsed_values = []
            for timestamp, value in values:
                try:
                    dt = datetime.fromtimestamp(float(timestamp))
                    val = float(value)
                    parsed_values.append((dt, val))
                except (ValueError, TypeError) as e:
                    logger.debug(f"Skipping invalid data point: {e}")
                    continue
            
            return parsed_values
            
        except httpx.ConnectError:
            logger.warning(f"Cannot connect to Prometheus at {self.config.base_url}")
            return []
        except httpx.TimeoutException:
            logger.warning(f"Prometheus query timed out after {self.config.timeout}s")
            return []
        except Exception as e:
            logger.error(f"Unexpected error querying Prometheus: {e}")
            return []
    
    async def query_instant(self, query: str) -> Optional[float]:
        """
        Query Prometheus for instant value (current state)
        
        Args:
            query: PromQL query
        
        Returns:
            Current value or None if unavailable
        """
        try:
            response = await self.client.get(
                f"{self.config.base_url}/api/v1/query",
                params={'query': query}
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            if data.get('status') != 'success':
                return None
            
            result = data.get('data', {}).get('result', [])
            if not result:
                return None
            
            value = result[0].get('value', [None, None])[1]
            return float(value) if value is not None else None
            
        except Exception as e:
            logger.debug(f"Instant query failed: {e}")
            return None
    
    async def health_check(self) -> bool:
        """
        Check if Prometheus is reachable and healthy
        
        Returns:
            True if Prometheus is up, False otherwise
        """
        try:
            response = await self.client.get(f"{self.config.base_url}/-/healthy")
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Close the HTTP client connection"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
