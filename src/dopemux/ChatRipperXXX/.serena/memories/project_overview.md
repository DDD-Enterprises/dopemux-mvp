# ChatX - Project Overview

## Purpose
ChatX is a privacy-focused, local-first CLI tool for forensic chat analysis. It extracts, transforms, and analyzes chat data from multiple platforms (iMessage, Instagram DM, WhatsApp) while maintaining strict privacy controls.

## Key Features
- Multi-platform support for chat extraction
- Privacy-first with local processing
- Differential privacy for statistical aggregation  
- Lossless extraction with source metadata preservation
- Schema-driven data formats
- Plugin-based architecture for extensibility

## Architecture
Pipeline-based approach:
1. Extract: Platform-specific extractors → canonical JSON
2. Transform: Data normalization and validation
3. Redact: Privacy redaction via Policy Shield
4. Enrich: Optional LLM processing (with consent)
5. Analyze: Generate insights and reports

## Main Entry Point
CLI tool accessible via `chatx` command after installation.