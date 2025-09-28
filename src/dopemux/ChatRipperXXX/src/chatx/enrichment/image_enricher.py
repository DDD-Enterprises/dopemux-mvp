"""Image enrichment pipeline for detecting objects, OCR, and psychological analysis."""

import asyncio
import hashlib
import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ImageEnrichmentRequest:
    """Request for image enrichment processing."""
    
    def __init__(
        self,
        msg_id: str,
        attachment_index: int,
        image_path: Optional[Path] = None,
        image_data: Optional[bytes] = None,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.msg_id = msg_id
        self.attachment_index = attachment_index
        self.image_path = image_path
        self.image_data = image_data
        self.provenance = provenance or {}
        
    @property
    def hash_sha256(self) -> str:
        """Compute SHA256 hash of image data."""
        if self.image_data:
            return hashlib.sha256(self.image_data).hexdigest()
        elif self.image_path and self.image_path.exists():
            with open(self.image_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        return ""


class ImageEnrichment:
    """Complete image enrichment result."""
    
    def __init__(
        self,
        msg_id: str,
        attachment_index: int,
        hash_sha256: str,
        provenance: Dict[str, Any],
        objects: Optional[List[Dict[str, Any]]] = None,
        psych: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.msg_id = msg_id
        self.attachment_index = attachment_index
        self.hash_sha256 = hash_sha256
        self.provenance = provenance
        self.objects = objects or []
        self.psych = psych
        
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "msg_id": self.msg_id,
            "attachment_index": self.attachment_index,
            "hash_sha256": self.hash_sha256,
            "provenance": self.provenance,
        }
        
        if self.objects:
            result["objects"] = self.objects
        if self.psych:
            result["psych"] = self.psych
            
        return result


class ImageEnricher:
    """Privacy-focused image enrichment pipeline."""
    
    def __init__(self, object_detection_enabled: bool = True, vlm_enabled: bool = True) -> None:
        self.object_detection_enabled = object_detection_enabled
        self.vlm_enabled = vlm_enabled
        self.run_id = str(uuid.uuid4())
        logger.info(f"Initialized ImageEnricher with run_id: {self.run_id}")
        
    async def __aenter__(self) -> "ImageEnricher":
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        pass
        
    async def enrich_image(
        self,
        request: ImageEnrichmentRequest
    ) -> Tuple[Optional[ImageEnrichment], Dict[str, Any]]:
        """Enrich a single image with objects and psychological analysis."""
        try:
            start_time = datetime.now()
            
            # Basic validation
            if not request.image_data and not (request.image_path and request.image_path.exists()):
                return None, {"error": "no_image_data"}
            
            # Create proper provenance for this enrichment
            enricher_provenance = {
                "schema_v": "1",
                "run_id": self.run_id,
                "model_id": "image-enricher-v1",
                "prompt_hash": "detector-pipeline-hash",
                "source": "local"
            }
            
            # Object detection
            objects_result = None
            if self.object_detection_enabled:
                objects_result = await self._detect_objects(request)
                
            # Psychological analysis
            psych_result = None
            if self.vlm_enabled:
                psych_result = await self._analyze_psychology(request, enricher_provenance)
            
            # Create enrichment result
            enrichment = ImageEnrichment(
                msg_id=request.msg_id,
                attachment_index=request.attachment_index,
                hash_sha256=request.hash_sha256,
                provenance=enricher_provenance,
                objects=objects_result,
                psych=psych_result,
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            metadata = {
                "processing_time_ms": processing_time,
                "run_id": self.run_id,
                "features_processed": {
                    "objects": objects_result is not None,
                    "psych": psych_result is not None,
                }
            }
            
            return enrichment, metadata
            
        except Exception as e:
            logger.error(f"Error enriching image {request.msg_id}: {e}")
            return None, {"error": str(e)}
    
    async def _detect_objects(self, request: ImageEnrichmentRequest) -> Optional[List[Dict[str, Any]]]:
        """Detect objects in image (placeholder implementation)."""
        logger.debug(f"Object detection for {request.msg_id} (placeholder)")
        
        # Return placeholder result for testing
        return [
            {
                "label": "person",
                "conf": 0.85,
                "box": [0.1, 0.2, 0.3, 0.4]
            }
        ]
    
    async def _analyze_psychology(
        self, 
        request: ImageEnrichmentRequest, 
        enricher_provenance: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Analyze psychological signals in image (placeholder VLM implementation)."""
        logger.debug(f"Psychological analysis for {request.msg_id} (placeholder)")
        
        # Return placeholder psych analysis structure matching schema
        return {
            "coarse_labels": ["communication"],
            "fine_labels_local": ["casual_interaction"],
            "emotion_hint": "neutral",
            "interaction_type": "other",
            "power_balance": 0.0,
            "boundary_health": "none",
            "confidence": 0.8,
            "provenance": enricher_provenance  # Use the enricher provenance here
        }
