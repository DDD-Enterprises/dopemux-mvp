"""Tests for hardware detection functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from chatx.embeddings.hardware import (
    HardwareDetector,
    HardwareInfo,
    get_optimal_device,
    get_recommended_batch_size
)


class TestHardwareDetector:
    """Test HardwareDetector functionality."""
    
    @patch('chatx.embeddings.hardware.torch.cuda.is_available')
    @patch('chatx.embeddings.hardware.torch.backends.mps.is_available')
    @patch('chatx.embeddings.hardware.psutil.virtual_memory')
    @patch('chatx.embeddings.hardware.psutil.cpu_count')
    def test_detect_apple_silicon(self, mock_cpu_count, mock_memory, mock_mps, mock_cuda):
        """Test detection on Apple Silicon Mac."""
        mock_cuda.return_value = False
        mock_mps.return_value = True
        mock_memory.return_value = Mock(total=17179869184)  # 16GB
        mock_cpu_count.return_value = 8
        
        detector = HardwareDetector()
        info = detector.detect()
        
        assert info.has_cuda is False
        assert info.has_mps is True
        assert info.memory_gb == 16.0
        assert info.cpu_cores == 8
        assert info.recommended_device == "mps"
    
    @patch('chatx.embeddings.hardware.torch.cuda.is_available')
    @patch('chatx.embeddings.hardware.torch.backends.mps.is_available')  
    @patch('chatx.embeddings.hardware.torch.cuda.device_count')
    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_count')
    def test_detect_cuda_system(self, mock_cpu_count, mock_memory, mock_device_count, mock_mps, mock_cuda):
        """Test detection on CUDA-enabled system."""
        mock_cuda.return_value = True
        mock_mps.return_value = False
        mock_device_count.return_value = 1
        mock_memory.return_value = Mock(total=34359738368)  # 32GB
        mock_cpu_count.return_value = 16
        
        detector = HardwareDetector()
        info = detector.detect()
        
        assert info.has_cuda is True
        assert info.has_mps is False
        assert info.memory_gb == 32.0
        assert info.cpu_cores == 16
        assert info.recommended_device == "cuda"
    
    @patch('chatx.embeddings.hardware.torch.cuda.is_available')
    @patch('chatx.embeddings.hardware.torch.backends.mps.is_available')
    @patch('chatx.embeddings.hardware.psutil.virtual_memory')
    @patch('chatx.embeddings.hardware.psutil.cpu_count')
    def test_detect_cpu_only(self, mock_cpu_count, mock_memory, mock_mps, mock_cuda):
        """Test detection on CPU-only system."""
        mock_cuda.return_value = False
        mock_mps.return_value = False
        mock_memory.return_value = Mock(total=8589934592)  # 8GB
        mock_cpu_count.return_value = 4
        
        detector = HardwareDetector()
        info = detector.detect()
        
        assert info.has_cuda is False
        assert info.has_mps is False
        assert info.memory_gb == 8.0
        assert info.cpu_cores == 4
        assert info.recommended_device == "cpu"
    
    @patch('chatx.embeddings.hardware.torch.cuda.is_available')
    @patch('chatx.embeddings.hardware.torch.backends.mps.is_available')
    def test_detect_handles_exceptions(self, mock_mps, mock_cuda):
        """Test graceful handling of detection exceptions."""
        mock_cuda.side_effect = RuntimeError("CUDA error")
        mock_mps.side_effect = RuntimeError("MPS error")
        
        detector = HardwareDetector()
        info = detector.detect()
        
        # Should fall back to CPU with minimal specs
        assert info.has_cuda is False
        assert info.has_mps is False
        assert info.recommended_device == "cpu"
        assert info.memory_gb > 0
        assert info.cpu_cores > 0


class TestOptimalDevice:
    """Test optimal device selection logic."""
    
    def test_get_optimal_device_cuda_preferred(self):
        """Test CUDA is preferred when available."""
        hardware = HardwareInfo(
            has_cuda=True,
            has_mps=True,
            memory_gb=16.0,
            cpu_cores=8,
            recommended_device="cuda"
        )
        
        device = get_optimal_device(hardware, model_size_mb=2800)
        assert device == "cuda"
    
    def test_get_optimal_device_mps_fallback(self):
        """Test MPS fallback when CUDA unavailable."""
        hardware = HardwareInfo(
            has_cuda=False,
            has_mps=True,
            memory_gb=16.0,
            cpu_cores=8,
            recommended_device="mps"
        )
        
        device = get_optimal_device(hardware, model_size_mb=2800)
        assert device == "mps"
    
    def test_get_optimal_device_cpu_fallback(self):
        """Test CPU fallback for large models on low memory."""
        hardware = HardwareInfo(
            has_cuda=False,
            has_mps=True,
            memory_gb=4.0,  # Low memory
            cpu_cores=4,
            recommended_device="cpu"
        )
        
        device = get_optimal_device(hardware, model_size_mb=6000)  # Large model
        assert device == "cpu"
    
    def test_get_optimal_device_respects_preference(self):
        """Test explicit device preference is honored."""
        hardware = HardwareInfo(
            has_cuda=True,
            has_mps=True,
            memory_gb=16.0,
            cpu_cores=8,
            recommended_device="cuda"
        )
        
        device = get_optimal_device(hardware, model_size_mb=1000, preferred_device="mps")
        assert device == "mps"


class TestBatchSizeRecommendation:
    """Test batch size recommendation logic."""
    
    def test_recommend_batch_size_cuda(self):
        """Test batch size for CUDA devices."""
        hardware = HardwareInfo(
            has_cuda=True,
            has_mps=False,
            memory_gb=24.0,
            cpu_cores=16,
            recommended_device="cuda"
        )
        
        batch_size = get_recommended_batch_size(hardware, "cuda", model_size_mb=2800)
        assert batch_size >= 16  # Large model reduces batch size
        assert batch_size <= 512
    
    def test_recommend_batch_size_mps(self):
        """Test batch size for MPS devices."""
        hardware = HardwareInfo(
            has_cuda=False,
            has_mps=True,
            memory_gb=16.0,
            cpu_cores=8,
            recommended_device="mps"
        )
        
        batch_size = get_recommended_batch_size(hardware, "mps", model_size_mb=2800)
        assert batch_size >= 16
        assert batch_size <= 128
    
    def test_recommend_batch_size_cpu(self):
        """Test batch size for CPU-only systems."""
        hardware = HardwareInfo(
            has_cuda=False,
            has_mps=False,
            memory_gb=8.0,
            cpu_cores=4,
            recommended_device="cpu"
        )
        
        batch_size = get_recommended_batch_size(hardware, "cpu", model_size_mb=2800)
        assert batch_size >= 1  # Large model reduces batch size further
        assert batch_size <= 32
    
    def test_recommend_batch_size_scales_with_memory(self):
        """Test batch size scales appropriately with available memory."""
        low_memory = HardwareInfo(
            has_cuda=True, has_mps=False, memory_gb=8.0, 
            cpu_cores=8, recommended_device="cuda"
        )
        high_memory = HardwareInfo(
            has_cuda=True, has_mps=False, memory_gb=32.0,
            cpu_cores=16, recommended_device="cuda"
        )
        
        low_batch = get_recommended_batch_size(low_memory, "cuda", model_size_mb=2800)
        high_batch = get_recommended_batch_size(high_memory, "cuda", model_size_mb=2800)
        
        assert high_batch > low_batch