"""Base extractor interface for chat platforms."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from chatx.schemas.message import CanonicalMessage
from chatx.utils.logging import get_logger

logger = get_logger(__name__)


class ExtractionReport:
    """Report of extraction results and statistics."""
    
    def __init__(self) -> None:
        self.messages_extracted: int = 0
        self.reactions_folded: int = 0
        self.attachments_found: int = 0
        self.unresolved_replies: int = 0
        self.errors: list[str] = []
        self.warnings: list[str] = []
    
    def to_dict(self) -> dict[str, object]:
        """Convert report to dictionary for serialization."""
        return {
            "messages_extracted": self.messages_extracted,
            "reactions_folded": self.reactions_folded,
            "attachments_found": self.attachments_found,
            "unresolved_replies": self.unresolved_replies,
            "errors": self.errors,
            "warnings": self.warnings,
        }


class BaseExtractor(ABC):
    """Abstract base class for platform-specific chat extractors.
    
    Each extractor implements platform-specific logic to convert
    platform data into the canonical message format while preserving
    original data in source_meta for lossless extraction.
    """
    
    def __init__(self, source_path: str | Path) -> None:
        """Initialize extractor with source path.
        
        Args:
            source_path: Path to the source data (e.g., chat.db, export file)
        """
        self.source_path = Path(source_path)
        self.report = ExtractionReport()
        
        if not self.source_path.exists():
            raise FileNotFoundError(f"Source path does not exist: {self.source_path}")
    
    @property
    @abstractmethod
    def platform(self) -> str:
        """Platform identifier (e.g., 'imessage', 'instagram', 'whatsapp')."""
        pass
    
    @abstractmethod
    def validate_source(self) -> bool:
        """Validate that the source is compatible with this extractor.
        
        Returns:
            True if source is valid for this platform
        """
        pass
    
    @abstractmethod
    def extract_messages(self) -> Iterator[CanonicalMessage]:
        """Extract messages from the source.
        
        Yields:
            CanonicalMessage instances in chronological order
            
        Raises:
            ExtractionError: If extraction fails
        """
        pass
    
    def extract_to_file(
        self,
        output_path: str | Path,
        validate_output: bool = True
    ) -> ExtractionReport:
        """Extract messages and write to JSONL file.
        
        Args:
            output_path: Path to output JSONL file
            validate_output: Whether to validate output against schema
            
        Returns:
            ExtractionReport with statistics and any errors
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Extracting {self.platform} messages from {self.source_path}")
        logger.info(f"Writing to {output_path}")
        
        try:
            with output_path.open("w") as f:
                for message in self.extract_messages():
                    # Validate message if requested
                    if validate_output:
                        try:
                            # Pydantic validation happens automatically
                            message.dict()
                        except Exception as e:
                            error_msg = f"Message validation failed for {message.msg_id}: {e}"
                            logger.error(error_msg)
                            self.report.errors.append(error_msg)
                            continue
                    
                    # Write message as JSON line
                    f.write(message.json() + "\n")
                    self.report.messages_extracted += 1
                    
                    # Count attachments
                    self.report.attachments_found += len(message.attachments)
                    
                    # Count reactions
                    self.report.reactions_folded += len(message.reactions)
        
        except Exception as e:
            error_msg = f"Extraction failed: {e}"
            logger.error(error_msg)
            self.report.errors.append(error_msg)
            raise ExtractionError(error_msg) from e
        
        logger.info(f"Extraction complete: {self.report.messages_extracted} messages")
        return self.report


class ExtractionError(Exception):
    """Raised when extraction fails."""
    pass


def detect_platform(source_path: str | Path) -> str | None:
    """Detect platform type from source path.
    
    Args:
        source_path: Path to source data
        
    Returns:
        Platform identifier if detected, None otherwise
    """
    source_path = Path(source_path)
    
    # iMessage: SQLite database with specific tables
    if source_path.suffix == '.db' and source_path.name in ('chat.db', 'sms.db'):
        return 'imessage'
    
    # Instagram: JSON export files
    if source_path.suffix == '.json' and 'instagram' in source_path.name.lower():
        return 'instagram'
    
    # WhatsApp: Text export files
    if source_path.suffix == '.txt' and 'whatsapp' in source_path.name.lower():
        return 'whatsapp'
    
    # Generic text files
    if source_path.suffix == '.txt':
        return 'txt'
    
    return None
