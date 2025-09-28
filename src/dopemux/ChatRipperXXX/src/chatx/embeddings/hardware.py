"""Hardware detection for optimal embedding model configuration."""

import logging
from typing import Optional

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from .base import HardwareInfo


logger = logging.getLogger(__name__)


class HardwareDetector:
    """Detects available hardware for embedding models."""
    
    def detect(self) -> HardwareInfo:
        """Detect hardware capabilities.
        
        Returns:
            HardwareInfo with detected capabilities
        """
        has_cuda = self._detect_cuda()
        has_mps = self._detect_mps()
        memory_gb = self._get_memory_gb()
        cpu_cores = self._get_cpu_cores()
        
        # Determine recommended device
        recommended_device = self._recommend_device(has_cuda, has_mps, memory_gb)
        
        return HardwareInfo(
            has_cuda=has_cuda,
            has_mps=has_mps,
            memory_gb=memory_gb,
            cpu_cores=cpu_cores,
            recommended_device=recommended_device
        )
    
    def _detect_cuda(self) -> bool:
        """Detect CUDA availability."""
        if not TORCH_AVAILABLE:
            return False
            
        try:
            return bool(torch.cuda.is_available())
        except Exception as e:
            logger.warning(f"Error detecting CUDA: {e}")
            return False
    
    def _detect_mps(self) -> bool:
        """Detect Metal Performance Shaders (MPS) availability."""
        if not TORCH_AVAILABLE:
            return False
            
        try:
            return bool(torch.backends.mps.is_available())
        except Exception as e:
            logger.warning(f"Error detecting MPS: {e}")
            return False
    
    def _get_memory_gb(self) -> float:
        """Get system memory in GB."""
        if not PSUTIL_AVAILABLE:
            return 8.0  # Conservative default
            
        try:
            memory = psutil.virtual_memory()
            return float(memory.total / (1024 ** 3))  # Convert bytes to GB
        except Exception as e:
            logger.warning(f"Error getting memory info: {e}")
            return 8.0
    
    def _get_cpu_cores(self) -> int:
        """Get number of CPU cores."""
        if not PSUTIL_AVAILABLE:
            return 4  # Conservative default
            
        try:
            return psutil.cpu_count(logical=False) or psutil.cpu_count() or 4
        except Exception as e:
            logger.warning(f"Error getting CPU core count: {e}")
            return 4
    
    def _recommend_device(self, has_cuda: bool, has_mps: bool, memory_gb: float) -> str:
        """Recommend optimal device based on capabilities."""
        # Prefer CUDA for best performance
        if has_cuda:
            return "cuda"
        
        # Fall back to MPS on Apple Silicon
        if has_mps:
            return "mps"
        
        # Default to CPU
        return "cpu"


def get_optimal_device(hardware: HardwareInfo, model_size_mb: int, 
                      preferred_device: Optional[str] = None) -> str:
    """Get optimal device considering model size and hardware.
    
    Args:
        hardware: Detected hardware information
        model_size_mb: Size of the model in MB
        preferred_device: User preference for device
        
    Returns:
        Recommended device string
    """
    # Honor explicit preference if valid
    if preferred_device:
        if preferred_device == "cuda" and hardware.has_cuda:
            return "cuda"
        elif preferred_device == "mps" and hardware.has_mps:
            return "mps"
        elif preferred_device == "cpu":
            return "cpu"
    
    # Check memory requirements (rough heuristic: model + 2x for processing)
    required_memory_gb = (model_size_mb * 3) / 1024  # MB to GB with buffer
    
    # Fallback to CPU if insufficient memory
    if required_memory_gb > hardware.memory_gb * 0.8:  # Leave 20% headroom
        logger.warning(
            f"Model size ({model_size_mb}MB) may exceed available memory "
            f"({hardware.memory_gb:.1f}GB). Using CPU."
        )
        return "cpu"
    
    # Use hardware recommendation
    return hardware.recommended_device


def get_recommended_batch_size(hardware: HardwareInfo, device: str, 
                              model_size_mb: int) -> int:
    """Get recommended batch size based on hardware and device.
    
    Args:
        hardware: Hardware information
        device: Target device
        model_size_mb: Model size in MB
        
    Returns:
        Recommended batch size
    """
    base_batch_size = {
        "cuda": 64,
        "mps": 32,
        "cpu": 8
    }.get(device, 8)
    
    # Scale based on memory
    memory_factor = min(hardware.memory_gb / 16.0, 2.0)  # Cap at 2x scaling
    adjusted_batch_size = int(base_batch_size * memory_factor)
    
    # Scale down for large models
    if model_size_mb > 2000:  # Large models
        adjusted_batch_size = max(adjusted_batch_size // 2, 1)
    
    # Ensure reasonable bounds
    if device == "cuda":
        return max(16, min(adjusted_batch_size, 512))
    elif device == "mps":
        return max(8, min(adjusted_batch_size, 128))
    else:  # CPU
        return max(1, min(adjusted_batch_size, 32))