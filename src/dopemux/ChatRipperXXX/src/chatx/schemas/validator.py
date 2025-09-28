"""Schema validation utilities for ChatX."""

import json
import logging
from pathlib import Path
from typing import Any, Optional, Union

import jsonschema
from jsonschema.validators import Draft202012Validator

logger = logging.getLogger(__name__)

# Schema paths
SCHEMA_DIR = Path(__file__).parent.parent.parent.parent / "schemas"
SCHEMA_CACHE: dict[str, dict[str, Any]] = {}


def load_schema(schema_name: str) -> dict[str, Any]:
    """Load and cache a JSON schema.
    
    Args:
        schema_name: Name of schema file (e.g., 'message', 'chunk', 'enrichment_message')
        
    Returns:
        Loaded schema dictionary
        
    Raises:
        FileNotFoundError: If schema file not found
        json.JSONDecodeError: If schema is invalid JSON
    """
    if schema_name in SCHEMA_CACHE:
        return SCHEMA_CACHE[schema_name]
    
    schema_file = SCHEMA_DIR / f"{schema_name}.schema.json"
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema not found: {schema_file}")
    
    with open(schema_file) as f:
        schema: dict[str, Any] = json.load(f)
    
    SCHEMA_CACHE[schema_name] = schema
    logger.debug(f"Loaded schema: {schema_name}")
    return schema


def validate_data(
    data: Union[dict[str, Any], list[dict[str, Any]]],
    schema_name: str,
    strict: bool = True
) -> tuple[bool, list[str]]:
    """Validate data against a schema.
    
    Args:
        data: Data to validate (single dict or list of dicts)
        schema_name: Name of schema to validate against
        strict: If True, raise on validation errors; if False, return error list
        
    Returns:
        Tuple of (is_valid, error_messages)
        
    Raises:
        jsonschema.ValidationError: If strict=True and validation fails
    """
    schema = load_schema(schema_name)
    validator = Draft202012Validator(schema)
    
    errors = []
    is_valid = True
    
    # Handle both single items and lists
    items = data if isinstance(data, list) else [data]
    
    for i, item in enumerate(items):
        validation_errors = list(validator.iter_errors(item))
        if validation_errors:
            is_valid = False
            for error in validation_errors:
                error_msg = f"Item {i}: {error.message}"
                if error.absolute_path:
                    error_msg += f" at path: {'.'.join(str(p) for p in error.absolute_path)}"
                errors.append(error_msg)
                logger.warning(f"Schema validation error: {error_msg}")
    
    if strict and not is_valid:
        raise jsonschema.ValidationError(f"Validation failed for {schema_name}: {errors}")
    
    return is_valid, errors


def validate_chunk(chunk: dict[str, Any], strict: bool = True) -> tuple[bool, list[str]]:
    """Validate a conversation chunk."""
    return validate_data(chunk, "chunk", strict)


def validate_message_enrichment(
    enrichment: dict[str, Any], strict: bool = True
) -> tuple[bool, list[str]]:
    """Validate message-level enrichment."""
    return validate_data(enrichment, "enrichment_message", strict)


def validate_cu_enrichment(
    enrichment: dict[str, Any], strict: bool = True
) -> tuple[bool, list[str]]:
    """Validate conversation unit enrichment."""
    return validate_data(enrichment, "enrichment_cu", strict)


def validate_redaction_report(
    report: dict[str, Any], strict: bool = True
) -> tuple[bool, list[str]]:
    """Validate redaction report."""
    return validate_data(report, "redaction_report", strict)


def validate_run_report(
    report: dict[str, Any], strict: bool = True
) -> tuple[bool, list[str]]:
    """Validate run report."""
    return validate_data(report, "run_report", strict)


class ValidationError(Exception):
    """Custom validation error with details."""

    def __init__(self, message: str, errors: list[str]) -> None:
        super().__init__(message)
        self.errors = errors


def quarantine_invalid_data(
    data: list[dict[str, Any]],
    schema_name: str,
    quarantine_dir: Optional[Path] = None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Separate valid and invalid data items.
    
    Args:
        data: List of data items to validate
        schema_name: Schema to validate against
        quarantine_dir: Optional directory to write invalid items
        
    Returns:
        Tuple of (valid_items, invalid_items)
    """
    valid_items = []
    invalid_items = []
    
    for item in data:
        is_valid, errors = validate_data(item, schema_name, strict=False)
        if is_valid:
            valid_items.append(item)
        else:
            # Add validation errors to item for debugging
            invalid_item = item.copy()
            invalid_item["_validation_errors"] = errors
            invalid_items.append(invalid_item)
            logger.warning(f"Quarantined invalid item: {errors}")
    
    # Optionally write quarantined items to disk
    if quarantine_dir and invalid_items:
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        quarantine_file = quarantine_dir / f"quarantined_{schema_name}.json"
        with open(quarantine_file, "w") as f:
            json.dump(invalid_items, f, indent=2)
        logger.info(f"Wrote {len(invalid_items)} invalid items to {quarantine_file}")
    
    return valid_items, invalid_items


def validate_pipeline_data(
    messages: Optional[list[dict[str, Any]]] = None,
    chunks: Optional[list[dict[str, Any]]] = None,
    enrichments: Optional[list[dict[str, Any]]] = None,
    strict: bool = False
) -> dict[str, tuple[bool, list[str]]]:
    """Validate multiple pipeline data types.
    
    Args:
        messages: Optional message data
        chunks: Optional chunk data
        enrichments: Optional enrichment data
        strict: Whether to raise on validation errors
        
    Returns:
        Dictionary of validation results by data type
    """
    results = {}
    
    if messages is not None:
        results["messages"] = validate_data(messages, "message", strict)
    
    if chunks is not None:
        results["chunks"] = validate_data(chunks, "chunk", strict)
    
    if enrichments is not None:
        results["enrichments"] = validate_data(enrichments, "enrichment_message", strict)
    
    return results
