"""Psychology-specialized embedding provider using PsychBERT and related models."""

import logging
from typing import List, Optional, Set
import asyncio

try:
    from sentence_transformers import SentenceTransformer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from .base import BaseEmbeddingProvider, EmbeddingConfig, ModelInfo
from .hardware import get_optimal_device, get_recommended_batch_size, HardwareDetector


logger = logging.getLogger(__name__)


class PsychologyEmbeddingProvider(BaseEmbeddingProvider):
    """Psychology-specialized embedding provider using domain-specific models.
    
    Uses models trained on mental health and psychology datasets for better
    representation of psychological constructs, relationship dynamics, and
    emotional patterns compared to generic embedding models.
    """

    # Psychology-specialized models
    PSYCHOLOGY_MODELS = {
        "mental/mental-bert-base-uncased": {
            "dimension": 768,
            "max_seq_length": 512,
            "size_mb": 438,
            "description": "BERT trained on mental health texts"
        },
        "nlpaueb/legal-bert-base-uncased": {
            "dimension": 768, 
            "max_seq_length": 512,
            "size_mb": 438,
            "description": "BERT trained on legal texts (useful for forensic analysis)"
        },
        "sentence-transformers/all-MiniLM-L6-v2": {
            "dimension": 384,
            "max_seq_length": 256,
            "size_mb": 80,
            "description": "Fallback general-purpose model"
        }
    }

    # Keywords that indicate psychological content
    PSYCHOLOGICAL_KEYWORDS = {
        'boundaries', 'boundary', 'toxic', 'codependent', 'manipulation',
        'manipulative', 'gaslighting', 'emotional', 'trauma', 'trigger',
        'attachment', 'abandonment', 'narcissistic', 'abuse', 'abusive',
        'relationship', 'intimacy', 'connection', 'disconnection', 'conflict',
        'escalation', 'repair', 'healing', 'therapy', 'therapeutic',
        'anxiety', 'depression', 'mood', 'emotion', 'feeling', 'stressed',
        'overwhelmed', 'vulnerable', 'insecure', 'rejected', 'abandoned',
        'betrayed', 'hurt', 'angry', 'frustrated', 'disappointed', 'sad',
        'grief', 'loss', 'mourning', 'support', 'understanding', 'empathy',
        'compassion', 'validation', 'acceptance', 'judgment', 'criticism',
        'control', 'controlling', 'power', 'powerless', 'dominance',
        'submission', 'passive', 'aggressive', 'assertive', 'defensive'
    }

    def __init__(self):
        """Initialize psychology embedding provider."""
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError(
                "sentence-transformers and torch are required for psychology embeddings. "
                "Install with: pip install sentence-transformers torch"
            )
        
        self.model: Optional[SentenceTransformer] = None
        self.config: Optional[EmbeddingConfig] = None
        self.hardware_info = HardwareDetector().detect()
        
    async def load_model(self, config: EmbeddingConfig) -> None:
        """Load psychology-specialized embedding model.
        
        Args:
            config: Configuration for the embedding model
            
        Raises:
            RuntimeError: If model loading fails
        """
        try:
            # Validate model is psychology-compatible
            if config.model_name not in self.PSYCHOLOGY_MODELS:
                logger.warning(
                    f"Model {config.model_name} not in psychology models list. "
                    f"Consider using: {list(self.PSYCHOLOGY_MODELS.keys())}"
                )
            
            # Determine optimal device
            model_size_mb = self.PSYCHOLOGY_MODELS.get(
                config.model_name, {"size_mb": 500}
            )["size_mb"]
            
            device = get_optimal_device(
                self.hardware_info, 
                model_size_mb, 
                config.device if config.device != "auto" else None
            )
            
            logger.info(f"Loading psychology model {config.model_name} on {device}")
            
            # Load model in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, 
                lambda: SentenceTransformer(
                    config.model_name,
                    device=device,
                    cache_folder=config.cache_folder,
                    trust_remote_code=config.trust_remote_code
                )
            )
            
            # Update config with actual device
            self.config = EmbeddingConfig(
                model_name=config.model_name,
                max_seq_length=config.max_seq_length,
                dimension=config.dimension,
                batch_size=get_recommended_batch_size(
                    self.hardware_info, device, model_size_mb
                ),
                device=device,
                trust_remote_code=config.trust_remote_code,
                cache_folder=config.cache_folder
            )
            
            logger.info(
                f"Psychology model loaded successfully. Device: {device}, "
                f"Batch size: {self.config.batch_size}"
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to load psychology model {config.model_name}: {e}")

    async def encode(self, text: str) -> List[float]:
        """Encode single text using psychology-specialized model.
        
        Args:
            text: Text to encode
            
        Returns:
            List of floats representing the embedding
            
        Raises:
            RuntimeError: If encoding fails or no model loaded
        """
        if self.model is None:
            raise RuntimeError("No model loaded. Call load_model() first.")
            
        try:
            # Check if text contains psychological content
            is_psychological = self._is_psychological_content(text)
            
            if is_psychological:
                logger.debug("Detected psychological content, using specialized encoding")
            
            # Truncate text to model's max length
            if len(text) > self.config.max_seq_length:
                text = text[:self.config.max_seq_length]
                logger.debug(f"Truncated text to {self.config.max_seq_length} characters")
            
            # Encode in executor to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self.model.encode(text, convert_to_numpy=True)
            )
            
            return embedding.tolist()
            
        except Exception as e:
            raise RuntimeError(f"Failed to encode text: {e}")

    async def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts using psychology-specialized model.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of embedding vectors
            
        Raises:
            RuntimeError: If batch encoding fails
        """
        if self.model is None:
            raise RuntimeError("No model loaded. Call load_model() first.")
            
        if not texts:
            return []
            
        try:
            # Count psychological content
            psychological_count = sum(
                1 for text in texts if self._is_psychological_content(text)
            )
            
            logger.debug(
                f"Batch encoding {len(texts)} texts "
                f"({psychological_count} psychological, {len(texts) - psychological_count} general)"
            )
            
            # Truncate texts to model's max length
            truncated_texts = []
            for text in texts:
                if len(text) > self.config.max_seq_length:
                    text = text[:self.config.max_seq_length]
                truncated_texts.append(text)
            
            # Encode in executor with optimal batch size
            batch_size = min(self.config.batch_size, len(truncated_texts))
            
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model.encode(
                    truncated_texts, 
                    batch_size=batch_size,
                    convert_to_numpy=True,
                    show_progress_bar=len(truncated_texts) > 100
                )
            )
            
            return [emb.tolist() for emb in embeddings]
            
        except Exception as e:
            raise RuntimeError(f"Failed to encode batch: {e}")

    def get_model_info(self) -> ModelInfo:
        """Get information about the loaded psychology model.
        
        Returns:
            ModelInfo with model specifications
            
        Raises:
            RuntimeError: If no model is loaded
        """
        if self.model is None or self.config is None:
            raise RuntimeError("No model loaded. Call load_model() first.")
            
        model_spec = self.PSYCHOLOGY_MODELS.get(
            self.config.model_name,
            {
                "dimension": self.config.dimension,
                "max_seq_length": self.config.max_seq_length,
                "size_mb": 500,  # Default estimate
                "description": "Custom psychology model"
            }
        )
        
        return ModelInfo(
            name=self.config.model_name,
            dimension=model_spec["dimension"],
            max_seq_length=model_spec["max_seq_length"],
            size_mb=model_spec["size_mb"],
            requires_trust_remote=self.config.trust_remote_code,
            recommended_hardware=["cuda", "mps", "cpu"]
        )

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model.
        
        Returns:
            Embedding dimension as integer
            
        Raises:
            RuntimeError: If no model is loaded
        """
        if self.config is None:
            raise RuntimeError("No model loaded. Call load_model() first.")
            
        return self.PSYCHOLOGY_MODELS.get(
            self.config.model_name, 
            {"dimension": self.config.dimension}
        )["dimension"]

    async def cleanup(self) -> None:
        """Clean up resources and unload model."""
        if self.model is not None:
            # Clear CUDA cache if using GPU
            if hasattr(torch, 'cuda') and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Delete model reference
            del self.model
            self.model = None
            self.config = None
            
            logger.info("Psychology model cleaned up successfully")

    def _is_psychological_content(self, text: str) -> bool:
        """Detect if text contains psychological content.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if text appears to contain psychological content
        """
        text_lower = text.lower()
        return any(
            keyword in text_lower 
            for keyword in self.PSYCHOLOGICAL_KEYWORDS
        )

    def get_psychology_confidence(self, text: str) -> float:
        """Get confidence score for psychological content detection.
        
        Args:
            text: Text to analyze
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not text.strip():
            return 0.0
            
        text_lower = text.lower()
        words = text_lower.split()
        
        if not words:
            return 0.0
            
        # Count psychological keywords
        psychology_count = sum(
            1 for word in words 
            if any(keyword in word for keyword in self.PSYCHOLOGICAL_KEYWORDS)
        )
        
        # Simple confidence based on keyword density
        confidence = min(psychology_count / len(words) * 10, 1.0)
        return confidence