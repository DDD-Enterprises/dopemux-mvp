"""Production message enrichment pipeline with confidence gating."""

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from datetime import datetime

from chatx.enrichment.models import (
    MessageEnrichment,
    EnrichmentRequest,
    EnrichmentResponse,
    BatchEnrichmentRequest,
    BatchEnrichmentResponse
)
from chatx.enrichment.ollama_client import ProductionOllamaClient, OllamaModelConfig
from chatx.schemas.validator import validate_data, quarantine_invalid_data

logger = logging.getLogger(__name__)


class ConfidenceGateConfig:
    """Configuration for confidence-based processing gates."""
    
    def __init__(
        self,
        tau: float = 0.7,  # Primary confidence threshold
        tau_low: float = 0.62,  # Hysteresis low threshold
        tau_high: float = 0.78,  # Hysteresis high threshold
        min_confidence: float = 0.3,  # Minimum acceptable confidence
    ):
        self.tau = tau
        self.tau_low = tau_low
        self.tau_high = tau_high
        self.min_confidence = min_confidence
        
        if not (0.0 <= tau_low <= tau <= tau_high <= 1.0):
            raise ValueError("Thresholds must satisfy: 0 ≤ tau_low ≤ tau ≤ tau_high ≤ 1")
        
        if not (0.0 <= min_confidence <= tau_low):
            raise ValueError("min_confidence must be ≤ tau_low")


class EnrichmentMetrics:
    """Metrics tracking for enrichment pipeline."""
    
    def __init__(self):
        self.messages_processed = 0
        self.enrichments_generated = 0
        self.low_confidence_count = 0
        self.validation_errors = 0
        self.processing_errors = 0
        self.total_processing_time_ms = 0.0
        self.confidence_distribution = {"low": 0, "medium": 0, "high": 0}
        
    def record_enrichment(self, response: EnrichmentResponse) -> None:
        """Record metrics for a single enrichment."""
        self.messages_processed += 1
        self.total_processing_time_ms += response.processing_time_ms
        
        if response.enrichment:
            self.enrichments_generated += 1
            confidence = response.enrichment.confidence_llm
            
            if confidence < 0.4:
                self.confidence_distribution["low"] += 1
                self.low_confidence_count += 1
            elif confidence < 0.7:
                self.confidence_distribution["medium"] += 1
            else:
                self.confidence_distribution["high"] += 1
        else:
            self.processing_errors += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        avg_latency = (
            self.total_processing_time_ms / self.messages_processed
            if self.messages_processed > 0 else 0
        )
        
        success_rate = (
            self.enrichments_generated / self.messages_processed
            if self.messages_processed > 0 else 0
        )
        
        return {
            "messages_processed": self.messages_processed,
            "enrichments_generated": self.enrichments_generated,
            "success_rate": success_rate,
            "average_latency_ms": avg_latency,
            "low_confidence_rate": self.low_confidence_count / max(1, self.messages_processed),
            "confidence_distribution": self.confidence_distribution,
            "validation_errors": self.validation_errors,
            "processing_errors": self.processing_errors,
        }


class MessageEnricher:
    """Production pipeline for enriching messages with LLM metadata."""
    
    def __init__(
        self,
        ollama_client: Optional[ProductionOllamaClient] = None,
        confidence_config: Optional[ConfidenceGateConfig] = None,
        output_dir: Optional[Path] = None,
        validate_schemas: bool = True,
    ):
        """Initialize message enricher.
        
        Args:
            ollama_client: Ollama client (will create default if None)
            confidence_config: Confidence gating configuration
            output_dir: Directory for outputs and quarantine files
            validate_schemas: Whether to validate against JSON schemas
        """
        self.ollama_client = ollama_client
        self.confidence_config = confidence_config or ConfidenceGateConfig()
        self.output_dir = output_dir or Path("./out")
        self.validate_schemas = validate_schemas
        
        # Metrics tracking
        self.metrics = EnrichmentMetrics()
        
        # Run tracking
        self.run_id = str(uuid.uuid4())
        
        logger.info(f"Initialized enricher with run_id: {self.run_id}")
        logger.info(f"Confidence thresholds: τ={self.confidence_config.tau}, "
                   f"τ_low={self.confidence_config.tau_low}, τ_high={self.confidence_config.tau_high}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self.ollama_client is None:
            self.ollama_client = ProductionOllamaClient(
                model_config=OllamaModelConfig()
            )
        
        await self.ollama_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.ollama_client:
            await self.ollama_client.__aexit__(exc_type, exc_val, exc_tb)
    
    def _apply_confidence_gate(
        self, 
        enrichments: List[MessageEnrichment]
    ) -> Tuple[List[MessageEnrichment], List[MessageEnrichment]]:
        """Apply confidence thresholds to filter enrichments.
        
        Args:
            enrichments: List of enrichments to filter
            
        Returns:
            Tuple of (high_confidence, low_confidence) enrichments
        """
        high_confidence = []
        low_confidence = []
        
        for enrichment in enrichments:
            confidence = enrichment.confidence_llm
            
            # Apply hysteresis-based gating
            if confidence >= self.confidence_config.tau_high:
                high_confidence.append(enrichment)
            elif confidence <= self.confidence_config.tau_low:
                low_confidence.append(enrichment)
            elif confidence >= self.confidence_config.tau:
                # In middle band - use primary threshold
                high_confidence.append(enrichment)
            else:
                low_confidence.append(enrichment)
        
        logger.info(f"Confidence gate: {len(high_confidence)} high, {len(low_confidence)} low confidence")
        return high_confidence, low_confidence
    
    def _validate_and_quarantine_enrichments(
        self,
        enrichments: List[MessageEnrichment]
    ) -> List[MessageEnrichment]:
        """Validate enrichments and quarantine invalid ones."""
        if not self.validate_schemas:
            return enrichments
        
        # Convert to dictionaries for validation
        enrichment_dicts = []
        for enrichment in enrichments:
            try:
                enrichment_dicts.append(enrichment.dict())
            except Exception as e:
                logger.error(f"Error converting enrichment to dict: {e}")
                self.metrics.validation_errors += 1
        
        # Validate against schema
        valid_dicts, invalid_dicts = quarantine_invalid_data(
            enrichment_dicts,
            "enrichment_message",
            quarantine_dir=self.output_dir / "quarantine"
        )
        
        if invalid_dicts:
            logger.warning(f"Quarantined {len(invalid_dicts)} invalid enrichments")
            self.metrics.validation_errors += len(invalid_dicts)
        
        # Return only valid enrichments
        valid_enrichments = []
        for enrichment, enrichment_dict in zip(enrichments, enrichment_dicts):
            if enrichment_dict in valid_dicts:
                valid_enrichments.append(enrichment)
        
        return valid_enrichments
    
    async def enrich_chunk_messages(
        self,
        chunk: Dict[str, Any],
        contact: str = "unknown"
    ) -> Tuple[List[MessageEnrichment], Dict[str, Any]]:
        """Enrich messages from a conversation chunk.
        
        Args:
            chunk: Conversation chunk with message_ids and metadata
            contact: Contact identifier for context
            
        Returns:
            Tuple of (enrichments, enrichment_metadata)
        """
        message_ids = chunk.get("meta", {}).get("message_ids", [])
        if not message_ids:
            logger.warning(f"No message_ids in chunk {chunk.get('chunk_id', 'unknown')}")
            return [], {"error": "no_message_ids"}
        
        # For now, we'll work with the chunk text since we don't have access to individual messages
        # In a full implementation, you'd fetch individual messages by ID
        chunk_text = chunk.get("text", "")
        if not chunk_text:
            logger.warning(f"No text in chunk {chunk.get('chunk_id', 'unknown')}")
            return [], {"error": "no_text"}
        
        # Parse chunk text into individual messages (simplified approach)
        messages = self._parse_chunk_text_to_messages(chunk_text, message_ids, contact)
        
        # Create enrichment requests
        requests = []
        for msg in messages:
            requests.append(EnrichmentRequest(
                msg_id=msg["msg_id"],
                text=msg["text"],
                contact=contact,
                platform=chunk.get("meta", {}).get("platform", "unknown"),
                timestamp=datetime.now(),  # Would use actual timestamp in full implementation
                context=messages[-3:]  # Last 3 messages as context
            ))
        
        # Process batch
        batch_request = BatchEnrichmentRequest(requests=requests)
        batch_response = await self.ollama_client.enrich_batch(batch_request)
        
        # Extract successful enrichments
        enrichments = []
        for response in batch_response.responses:
            self.metrics.record_enrichment(response)
            
            if response.enrichment:
                enrichments.append(response.enrichment)
            elif response.error:
                logger.warning(f"Enrichment error for {response.msg_id}: {response.error}")
        
        # Apply confidence gating
        high_conf, low_conf = self._apply_confidence_gate(enrichments)
        
        # Validate high confidence enrichments
        valid_enrichments = self._validate_and_quarantine_enrichments(high_conf)
        
        # Build metadata
        metadata = {
            "total_messages": len(requests),
            "enrichments_generated": len(enrichments),
            "high_confidence_count": len(high_conf),
            "low_confidence_count": len(low_conf),
            "valid_after_validation": len(valid_enrichments),
            "processing_time_ms": batch_response.total_processing_time_ms,
        }
        
        return valid_enrichments, metadata
    
    def _parse_chunk_text_to_messages(
        self, 
        chunk_text: str, 
        message_ids: List[str], 
        contact: str
    ) -> List[Dict[str, Any]]:
        """Parse chunk text into individual message structures.
        
        This is a simplified implementation - in production you'd have
        access to the original message data.
        """
        lines = chunk_text.split("\n")
        messages = []
        
        for i, line in enumerate(lines):
            if line.strip() and ": " in line:
                # Extract timestamp and sender
                try:
                    timestamp_part, rest = line.split("] ", 1)
                    timestamp_part = timestamp_part.lstrip("[")
                    sender, text = rest.split(": ", 1)
                    
                    # Use provided message IDs if available, otherwise generate
                    msg_id = message_ids[i] if i < len(message_ids) else f"synthetic_{i}"
                    
                    messages.append({
                        "msg_id": msg_id,
                        "text": text.strip(),
                        "sender": sender.strip(),
                        "is_me": sender.strip() == "ME",
                        "timestamp": timestamp_part,
                    })
                except (ValueError, IndexError):
                    # Skip malformed lines
                    continue
        
        return messages
    
    async def process_chunks_stream(
        self,
        chunks: AsyncIterator[Dict[str, Any]],
        contact: str = "unknown"
    ) -> AsyncIterator[Tuple[List[MessageEnrichment], Dict[str, Any]]]:
        """Process chunks as a stream and yield enrichments."""
        async for chunk in chunks:
            try:
                enrichments, metadata = await self.enrich_chunk_messages(chunk, contact)
                yield enrichments, metadata
            except Exception as e:
                logger.error(f"Error processing chunk {chunk.get('chunk_id', 'unknown')}: {e}")
                yield [], {"error": str(e)}
    
    async def enrich_chunks(
        self,
        chunks: List[Dict[str, Any]],
        contact: str = "unknown",
        output_file: Optional[Path] = None
    ) -> Tuple[List[MessageEnrichment], Path]:
        """Enrich all messages in conversation chunks.
        
        Args:
            chunks: List of conversation chunks
            contact: Contact identifier
            output_file: Optional output file path
            
        Returns:
            Tuple of (all_enrichments, output_file_path)
        """
        logger.info(f"Starting enrichment of {len(chunks)} chunks for contact {contact}")
        start_time = datetime.now()
        
        all_enrichments = []
        
        # Process chunks sequentially to avoid overwhelming Ollama
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}: {chunk.get('chunk_id', 'unknown')}")
            
            try:
                enrichments, metadata = await self.enrich_chunk_messages(chunk, contact)
                all_enrichments.extend(enrichments)
                
                logger.info(f"Chunk {i+1} processed: {len(enrichments)} enrichments, "
                           f"{metadata.get('processing_time_ms', 0):.1f}ms")
                
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {e}")
                continue
        
        finished_time = datetime.now()
        total_time = (finished_time - start_time).total_seconds()
        
        # Save enrichments to file
        if not output_file:
            timestamp = start_time.strftime("%Y%m%d_%H%M%S")
            contact_clean = contact.replace("@", "_at_").replace("+", "_plus_")
            output_file = self.output_dir / f"enrichments_{contact_clean}_{timestamp}.jsonl"
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            for enrichment in all_enrichments:
                f.write(json.dumps(enrichment.dict(), ensure_ascii=False) + "\n")
        
        logger.info(f"Enrichment complete: {len(all_enrichments)} enrichments saved to {output_file}")
        logger.info(f"Total processing time: {total_time:.2f}s")
        logger.info(f"Throughput: {len(all_enrichments) / total_time:.1f} enrichments/s")
        
        return all_enrichments, output_file
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        base_metrics = self.metrics.get_summary()
        
        ollama_metrics = {}
        if self.ollama_client:
            ollama_metrics = self.ollama_client.get_performance_metrics()
        
        return {
            "run_id": self.run_id,
            "enrichment_metrics": base_metrics,
            "ollama_metrics": ollama_metrics,
            "confidence_config": {
                "tau": self.confidence_config.tau,
                "tau_low": self.confidence_config.tau_low,
                "tau_high": self.confidence_config.tau_high,
                "min_confidence": self.confidence_config.min_confidence,
            },
            "timestamp": datetime.now().isoformat(),
        }
