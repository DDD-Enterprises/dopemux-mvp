# ChatX/ChatRipper - LLM Context Guide
*Status: Active | Owner: AI/ML Team | Last Updated: 2025-09-06*

## Purpose
This document provides context and guidance for Large Language Models (LLMs) working with the ChatX/ChatRipper codebase. It includes project-specific patterns, conventions, and implementation details to help LLMs understand and contribute effectively to the project.

---

## Project Overview for LLMs

### Core Identity
ChatX/ChatRipper is a **privacy-first, local-first forensic chat analysis platform** with these key characteristics:

- **Domain**: Digital forensics, chat analysis, privacy engineering
- **Architecture**: Modular pipeline (Extract → Transform → Redact → Index → Enrich → Query)
- **Tech Stack**: Python 3.11+, Typer CLI, Pydantic, SQLAlchemy, ChromaDB
- **Key Principles**: Privacy by default, deterministic outputs, evidence integrity

### LLM-Friendly Project Structure

```
src/chatx/
├── cli/           # Command-line interface (Typer)
├── extractors/    # Platform-specific data ingestion
├── transformers/  # Conversation chunking and normalization
├── redaction/     # Privacy enforcement (Policy Shield)
├── privacy/       # Differential privacy engine
├── enrichment/    # LLM integration and analysis
├── indexing/      # Vector storage and retrieval
├── schemas/       # Data validation (Pydantic)
├── utils/         # Shared utilities and helpers
└── obs/           # Observability and metrics
```

---

## Key Patterns & Conventions

### 1. Data Flow Pattern
**All processing follows this strict sequence:**
```python
# Input → Processing → Output pattern
input_data = load_input_file(input_path)  # JSON/JSONL
processed_data = processor.process(input_data)
write_output_file(processed_data, output_path)  # Schema-validated
```

### 2. Error Handling Pattern
**Structured errors with RFC-7807 compliance:**
```python
from chatx.cli_errors import emit_problem

# Use for fatal errors
emit_problem(
    code="INVALID_INPUT",
    title="Source path not found", 
    status=1,
    detail=f"Path does not exist: {path}",
    instance=str(path)
)

# Use for validation errors (non-fatal)
quarantine_invalid_data(invalid_data, reason="Schema validation failed")
```

### 3. Configuration Pattern
**Configuration follows hierarchical structure:**
```python
# Module-level config classes
class ProcessingConfig(BaseModel):
    batch_size: int = 100
    timeout: int = 30
    validate: bool = True

# Instance configuration with defaults
config = ProcessingConfig()
processor = SomeProcessor(config=config)
```

### 4. Logging Pattern
**Structured JSON logging throughout:**
```python
import logging
logger = logging.getLogger(__name__)

# Context-rich logging
logger.info(
    "Processing started", 
    extra={
        "component": "transformer",
        "contact": contact_id,
        "chunk_count": len(chunks)
    }
)
```

---

## Implementation Guidelines for LLMs

### When Adding New Features

1. **Start with Schema** (`src/chatx/schemas/`)
   ```python
   # Define data structures first
   class NewFeatureData(BaseModel):
       field: str = Field(..., description="Purpose of this field")
       config: Dict[str, Any] = Field(default_factory=dict)
   ```

2. **Follow Pipeline Convention**
   ```python
   # Input → Process → Output pattern
   def process_new_feature(input_data: NewFeatureData) -> ProcessedResult:
       # Validation
       validate_input(input_data)
       
       # Processing logic
       result = do_processing(input_data)
       
       # Output preparation
       return prepare_output(result)
   ```

3. **Integrate with CLI** (`src/chatx/cli/main.py`)
   ```python
   @app.command()
   def new_feature(
       input_file: Path = typer.Argument(..., help="Input file"),
       output: Path = typer.Option(None, "--output", "-o", help="Output file")
   ):
       # Standard CLI pattern
       data = load_input(input_file)
       result = process_new_feature(data)
       write_output(result, output)
   ```

### When Modifying Existing Code

1. **Maintain Backward Compatibility**
   ```python
   # Add new parameters as optional
   def existing_function(param1: str, new_param: Optional[str] = None):
       if new_param:
           # New functionality
       else:
           # Original behavior
   ```

2. **Update Schema Validation**
   ```python
   # Add new fields with defaults
   class ExistingSchema(BaseModel):
       original_field: str
       new_field: str = "default_value"  # Optional with default
   ```

3. **Consider Privacy Implications**
   ```python
   # Always check Policy Shield integration
   if involves_sensitive_data:
       from chatx.redaction.policy_shield import PolicyShield
       shield = PolicyShield()
       safe_data = shield.redact(unsafe_data)
   ```

---

## Common Tasks & Examples

### Task: Add New Platform Support

```python
# 1. Create extractor in src/chatx/extractors/new_platform.py
class NewPlatformExtractor(BaseExtractor):
    def extract_messages(self, source: Path) -> List[CanonicalMessage]:
        # Parse platform-specific format
        raw_messages = parse_platform_format(source)
        
        # Convert to canonical format
        return [
            CanonicalMessage(
                id=msg.id,
                text=msg.content,
                timestamp=msg.timestamp,
                sender=msg.sender,
                platform="new_platform",
                attachments=extract_attachments(msg)
            )
            for msg in raw_messages
        ]

# 2. Add CLI command in src/chatx/cli/main.py
@app.command()
def new_platform_pull(
    source: Path = typer.Argument(..., help="Source file"),
    out: Path = typer.Option(Path("./out"), "--out", help="Output directory")
):
    """Extract messages from New Platform."""
    extractor = NewPlatformExtractor()
    messages = extractor.extract_messages(source)
    write_messages_with_validation(messages, out / "messages_newplatform.json")
```

### Task: Add New Enrichment Type

```python
# 1. Define enrichment schema in src/chatx/schemas/enrichment.py
class NewEnrichmentData(BaseModel):
    analysis_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    findings: List[str] = Field(default_factory=list)

# 2. Implement enricher in src/chatx/enrichment/
class NewEnricher:
    async def enrich(self, chunk: Dict) -> NewEnrichmentData:
        # LLM analysis logic
        analysis = await llm_analyze(chunk["text"])
        
        return NewEnrichmentData(
            analysis_type="new_analysis",
            confidence=analysis.confidence,
            findings=analysis.findings
        )

# 3. Integrate with main enrichment pipeline
class MessageEnricher:
    async def enrich_chunks(self, chunks: List[Dict]):
        # ... existing enrichment
        
        # Add new enrichment
        new_enricher = NewEnricher()
        for chunk in chunks:
            chunk["enrichment"]["new_analysis"] = await new_enricher.enrich(chunk)
```

### Task: Add New Vector Store

```python
# 1. Implement BaseVectorStore interface
class NewVectorStore(BaseVectorStore):
    def __init__(self, config: IndexingConfig):
        self.config = config
        self.client = create_vector_client(config)
    
    def index_chunks(self, chunks: List[Dict], contact: str) -> Dict:
        # Convert chunks to vectors
        vectors = [chunk_to_vector(chunk) for chunk in chunks]
        
        # Store in vector database
        return self.client.store_vectors(vectors, collection=contact)
    
    def search(self, query: str, contact: str, k: int = 10) -> List[SearchResult]:
        # Query processing and similarity search
        results = self.client.search(query, collection=contact, limit=k)
        return format_search_results(results)

# 2. Add to indexing pipeline
class IndexingPipeline:
    def __init__(self, store_type: str = "chroma"):
        if store_type == "new_store":
            self.store = NewVectorStore(IndexingConfig())
        else:
            self.store = ChromaDBVectorStore(IndexingConfig())
```

---

## Privacy & Security Considerations

### Data Handling Rules

1. **Never expose raw PII** in logs, errors, or outputs
2. **Use Policy Shield** for any data that might contain sensitive information
3. **Validate cloud readiness** before any external data transmission
4. **Follow differential privacy** principles for statistical data

### Safe Patterns

```python
# UNSAFE: Raw data exposure
logger.error(f"Processing failed for user: {user_email}")

# SAFE: Tokenized data  
from chatx.redaction.policy_shield import PolicyShield
shield = PolicyShield()
safe_email = shield.redact_string(user_email)
logger.error(f"Processing failed for user: {safe_email}")

# UNSAFE: Direct cloud transmission
cloud_client.send(conversation_data)

# SAFE: Policy Shield validation
from chatx.redaction.policy_shield import validate_cloud_readiness
if validate_cloud_readiness(redacted_data):
    cloud_client.send(redacted_data)
else:
    raise PolicyViolationError("Data not safe for cloud processing")
```

---

## Testing & Validation Patterns

### Unit Test Structure

```python
# Test file naming: test_<module>_<functionality>.py
# Location: tests/unit/test_extractors_newplatform.py

def test_new_extractor_happy_path():
    """Test successful extraction from new platform."""
    extractor = NewPlatformExtractor()
    
    with tempfile.NamedTemporaryFile() as tmp:
        # Create test input
        create_test_input(tmp.name)
        
        # Execute extraction
        messages = extractor.extract_messages(Path(tmp.name))
        
        # Validate results
        assert len(messages) > 0
        for msg in messages:
            assert isinstance(msg, CanonicalMessage)
            assert msg.platform == "new_platform"

def test_new_extractor_invalid_input():
    """Test error handling for invalid input."""
    extractor = NewPlatformExtractor()
    
    with pytest.raises(ValidationError):
        extractor.extract_messages(Path("/invalid/path"))
```

### Integration Test Pattern

```python
def test_full_pipeline_integration():
    """Test complete pipeline from extraction to enrichment."""
    
    # Setup test environment
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)
        
        # Run extraction
        extract_messages(test_source, out_dir)
        
        # Run transformation  
        transform_messages(out_dir / "messages.json", out_dir)
        
        # Run redaction
        redact_chunks(out_dir / "chunks.jsonl", out_dir)
        
        # Run enrichment
        enrich_chunks(out_dir / "redacted.jsonl", out_dir)
        
        # Validate final output
        final_output = load_jsonl(out_dir / "enriched.jsonl")
        assert_all_valid_schema(final_output)
```

---

## Performance Optimization Guide

### Memory Efficiency

```python
# BAD: Loading everything into memory
with open(huge_file) as f:
    all_data = json.load(f)  # Memory explosion!

# GOOD: Streaming processing
with open(huge_file) as f:
    for line in f:
        chunk = json.loads(line)
        process_chunk(chunk)  # Process incrementally

# BAD: Large in-memory data structures
big_list = [create_large_object() for _ in range(1000000)]

# GOOD: Generator pattern
def chunk_generator():
    for i in range(1000000):
        yield create_large_object()  # Memory efficient
```

### Processing Efficiency

```python
# BAD: Sequential processing
for item in large_collection:
    result = expensive_operation(item)  # Slow

# GOOD: Batch processing
batch_size = 100
for i in range(0, len(large_collection), batch_size):
    batch = large_collection[i:i+batch_size]
    results = expensive_batch_operation(batch)  # Faster

# BAD: Repeated expensive operations
for chunk in chunks:
    embeddings = compute_embeddings(chunk["text"])  # Recomputes each time

# GOOD: Caching expensive operations
embedding_cache = {}
for chunk in chunks:
    text = chunk["text"]
    if text not in embedding_cache:
        embedding_cache[text] = compute_embeddings(text)
    chunk["embedding"] = embedding_cache[text]
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Schema Validation Failures
**Problem**: New data structures fail schema validation
**Solution**: Always define schemas first and validate early

```python
# Define schema before implementation
class NewData(BaseModel):
    field1: str
    field2: int = Field(ge=0)

# Validate immediately after creation
try:
    validated = NewData(**raw_data)
except ValidationError as e:
    quarantine_invalid_data(raw_data, str(e))
```

### Pitfall 2: Privacy Violations
**Problem**: Accidental exposure of sensitive data
**Solution**: Use Policy Shield for all user data

```python
# Always redact before processing
from chatx.redaction.policy_shield import PolicyShield

shield = PolicyShield()
safe_data = shield.redact_chunks(raw_chunks)

# Never log raw user data
logger.info("Processing data", extra={
    "redacted_text": shield.redact_string(sensitive_text)
})
```

### Pitfall 3: Performance Issues
**Problem**: Slow processing with large datasets
**Solution**: Use streaming and batching patterns

```python
# Process large files in streams
with open(large_file) as f:
    for line in f:
        process_item(json.loads(line))

# Use batch operations for efficiency
batch = []
for item in stream:
    batch.append(item)
    if len(batch) >= 1000:
        process_batch(batch)
        batch = []
```

---

## Quick Reference

### Import Patterns
```python
# Standard imports
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Project-specific imports
from chatx.schemas.message import CanonicalMessage
from chatx.redaction.policy_shield import PolicyShield
from chatx.utils.logging import setup_logging
```

### Common Utilities
```python
# JSON handling
from chatx.utils.json_output import write_messages_with_validation

# Error handling  
from chatx.cli_errors import emit_problem

# Configuration
from chatx.utils.config import load_config

# Metrics and reporting
from chatx.obs.run_artifacts import write_run_report
```

### CLI Command Structure
```python
@app.command()
def example_command(
    input_file: Path = typer.Argument(..., help="Input file"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Example command with standard pattern."""
    
    # Input validation
    if not input_file.exists():
        emit_problem(
            code="FILE_NOT_FOUND",
            title="Input file not found",
            status=1,
            detail=f"File does not exist: {input_file}",
            instance=str(input_file)
        )
    
    # Processing logic
    data = load_input(input_file)
    result = process_data(data)
    
    # Output handling
    write_output(result, output)
```

---

## Version Information

- **ChatX Version**: 1.0.0
- **Python**: 3.11+
- **Last Updated**: 2025-09-06
- **Maintainer**: AI/ML Team

*This document should be updated whenever new patterns, conventions, or guidelines are established for LLM collaboration on the ChatX/ChatRipper project.*