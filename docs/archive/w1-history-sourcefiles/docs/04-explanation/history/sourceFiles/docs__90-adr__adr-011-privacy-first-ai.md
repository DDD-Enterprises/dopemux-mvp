# ADR-011: Privacy-First AI Classification Strategy

**Status**: Proposed
**Date**: 2025-09-22
**Deciders**: Dopemux Team

## Context

The Intelligent Memory Layer requires AI classification of development activities that may contain:
- **Proprietary code snippets**
- **Business logic and algorithms**
- **Architecture decisions and trade-offs**
- **Internal project discussions**
- **Security considerations and vulnerabilities**

We need an AI strategy that provides intelligent classification while protecting sensitive development information.

## Decision

We will implement a **privacy-first AI strategy** with multiple processing options:

1. **Local-First Processing**: Default to local AI models (Ollama, local embeddings)
2. **Graduated Privacy Levels**: Different AI backends for different sensitivity levels
3. **Content Filtering**: Remove sensitive information before external AI processing
4. **User Control**: Explicit consent and configuration for each AI processing level

## Rationale

### Developer Privacy Requirements
Development work contains highly sensitive information:
- **Trade secrets** in business logic
- **Security vulnerabilities** in early stages
- **Competitive advantages** in algorithmic approaches
- **Client information** in comments and variable names

Sending this to external AI services without careful consideration violates developer privacy and potentially legal/contractual obligations.

### ADHD Developer Needs
Neurodivergent developers particularly benefit from:
- **Predictable privacy controls** - no unexpected data sharing
- **Transparent processing** - clear understanding of what goes where
- **Paranoia-friendly options** - maximum privacy when needed
- **Simple defaults** - privacy-first configuration out of the box

### Business Reality
Organizations have varying privacy requirements:
- **Startups** may accept cloud AI for better accuracy
- **Enterprise** may require completely local processing
- **Regulated industries** may have legal restrictions
- **Open source projects** may have different considerations

## Privacy Level Architecture

### Level 0: Completely Local (Default)
```python
class LocalPrivacyProcessor:
    """All processing happens on local machine"""

    def __init__(self):
        self.llm = OllamaClient(model="llama2:7b")
        self.embeddings = SentenceTransformers("all-MiniLM-L6-v2")

    async def classify_content(self, content: str, context: dict):
        """Classify using only local models"""
        try:
            # Local LLM classification
            classification = await self.llm.classify(content, context)

            # Local embedding generation
            embedding = self.embeddings.encode(content)

            return ProcessingResult(
                classification=classification,
                embedding=embedding,
                processing_location="local",
                privacy_level=0
            )
        except Exception as e:
            # Fallback to pattern matching
            return await self.pattern_fallback(content, context)
```

### Level 1: Filtered Cloud Processing
```python
class FilteredCloudProcessor:
    """Remove sensitive content before cloud processing"""

    def __init__(self):
        self.content_filter = SensitiveContentFilter()
        self.cloud_llm = OpenAIClient()

    async def classify_content(self, content: str, context: dict):
        """Filter content then use cloud AI"""

        # Remove sensitive information
        filtered_content = self.content_filter.remove_sensitive(content)

        if self.content_filter.too_much_removed():
            # Fallback to local processing if too much filtered
            return await LocalPrivacyProcessor().classify_content(content, context)

        # Use cloud AI on filtered content
        classification = await self.cloud_llm.classify(filtered_content, context)

        return ProcessingResult(
            classification=classification,
            embedding=await self.cloud_llm.embed(filtered_content),
            processing_location="cloud_filtered",
            privacy_level=1,
            filtering_applied=self.content_filter.get_applied_filters()
        )
```

### Level 2: Full Cloud Processing (Opt-in)
```python
class FullCloudProcessor:
    """Full content to cloud AI (user explicitly opted in)"""

    def __init__(self):
        self.cloud_llm = OpenAIClient()
        self.user_consent = UserConsentManager()

    async def classify_content(self, content: str, context: dict):
        """Use cloud AI with full content (with explicit consent)"""

        # Verify explicit consent for this content type
        if not self.user_consent.has_consent_for(context.content_type):
            raise ConsentRequiredError(f"No consent for {context.content_type}")

        # Log what's being sent for transparency
        self.transparency_log.log_cloud_processing(content, context)

        classification = await self.cloud_llm.classify(content, context)

        return ProcessingResult(
            classification=classification,
            embedding=await self.cloud_llm.embed(content),
            processing_location="cloud_full",
            privacy_level=2,
            consent_verified=True
        )
```

## Content Filtering Strategy

### Sensitive Content Detection
```python
class SensitiveContentFilter:
    """Remove or mask sensitive information"""

    SENSITIVE_PATTERNS = [
        # API keys and secrets
        r'[A-Za-z0-9]{32,}',  # Long random strings
        r'(?i)(api_key|secret|token|password)\s*[=:]\s*["\']?([^"\'\s]+)',

        # Email addresses and personal info
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',

        # File paths with usernames
        r'/Users/[^/\s]+',
        r'C:\\Users\\[^\\s]+',

        # IP addresses
        r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',

        # URLs with credentials
        r'https?://[^:\s]+:[^@\s]+@',
    ]

    def remove_sensitive(self, content: str) -> str:
        """Remove/mask sensitive content"""
        filtered = content

        for pattern in self.SENSITIVE_PATTERNS:
            filtered = re.sub(pattern, '[FILTERED]', filtered)

        # Remove code blocks that look proprietary
        filtered = self.remove_proprietary_code(filtered)

        return filtered

    def remove_proprietary_code(self, content: str) -> str:
        """Remove code that appears to contain business logic"""
        lines = content.split('\n')
        filtered_lines = []

        for line in lines:
            if self.looks_proprietary(line):
                filtered_lines.append('[CODE_FILTERED]')
            else:
                filtered_lines.append(line)

        return '\n'.join(filtered_lines)

    def looks_proprietary(self, line: str) -> bool:
        """Heuristics for proprietary code detection"""
        proprietary_indicators = [
            'algorithm',
            'proprietary',
            'confidential',
            'secret',
            'internal',
            'copyright',
            'license',
            # Add domain-specific terms
        ]

        return any(indicator in line.lower() for indicator in proprietary_indicators)
```

## User Configuration and Consent

### Privacy Configuration
```yaml
# ~/.dopemux/privacy-settings.yaml
ai_processing:
  default_level: 0  # 0=local, 1=filtered_cloud, 2=full_cloud

  # Per-content-type settings
  content_preferences:
    git_commits: 1      # OK to filter and send
    code_snippets: 0    # Never send code
    conversations: 1    # Filter and send discussions
    file_changes: 0     # Keep file changes local

  # Cloud AI settings
  preferred_provider: "openai"  # openai, anthropic, local

  # Consent tracking
  explicit_consent:
    cloud_processing: false
    data_retention: false
    model_training: false

  # Transparency
  log_cloud_requests: true
  show_filtering_results: true
```

### Consent Management
```python
class UserConsentManager:
    """Manage explicit user consent for privacy levels"""

    def request_consent_for_cloud_processing(self):
        """Interactive consent request"""

        consent_dialog = ConsentDialog([
            "Do you consent to sending filtered development content to cloud AI?",
            "This will improve classification accuracy but sends data externally.",
            "Sensitive information will be filtered out before sending.",
            "You can revoke this consent at any time.",
            "",
            "What information would be sent:",
            "• Commit messages (with secrets filtered)",
            "• Code comments (with proprietary terms filtered)",
            "• Conversation text (with personal info filtered)",
            "",
            "What will NOT be sent:",
            "• Complete source code",
            "• API keys or credentials",
            "• File paths with usernames",
            "• Proprietary algorithms"
        ])

        return consent_dialog.get_user_response()

    def show_transparency_report(self):
        """Show user what has been sent to cloud AI"""

        report = TransparencyReport()
        report.show_monthly_summary()
        report.show_data_sent()
        report.show_filtering_effectiveness()
        report.show_revocation_options()
```

## Implementation Strategy

### Default Configuration (Privacy-First)
```python
# Default settings prioritize privacy
DEFAULT_CONFIG = {
    'ai_processing_level': 0,  # Local only
    'cloud_consent': False,
    'content_filtering': 'aggressive',
    'transparency_logging': True,
    'fallback_behavior': 'local_only'
}
```

### Graceful Degradation
```python
class PrivacyAwareProcessor:
    def __init__(self, user_config: PrivacyConfig):
        self.config = user_config
        self.processors = {
            0: LocalPrivacyProcessor(),
            1: FilteredCloudProcessor(),
            2: FullCloudProcessor()
        }

    async def process_content(self, content: str, context: dict):
        """Process with appropriate privacy level"""

        target_level = self.config.get_level_for_content(context.content_type)

        try:
            processor = self.processors[target_level]
            return await processor.classify_content(content, context)
        except (NetworkError, ConsentRequiredError, ModelUnavailableError):
            # Gracefully degrade to more private option
            return await self.fallback_to_more_private(content, context, target_level)
```

## Benefits

### Privacy Protection
- **Local-first processing** protects all sensitive content by default
- **Graduated options** allow users to choose their comfort level
- **Content filtering** removes sensitive information before external processing
- **Explicit consent** ensures users know what's being shared

### ADHD Developer Support
- **Predictable privacy** reduces anxiety about data sharing
- **Simple defaults** require no configuration for privacy
- **Transparent operation** shows exactly what happens to data
- **User control** allows adjustment based on comfort level

### Business Compliance
- **Enterprise-friendly** with local-only options
- **Regulatory compliance** through data residency control
- **Audit trails** for transparency and compliance
- **Consent management** for legal requirements

## Trade-offs

### Accuracy vs Privacy
- **Local models** provide lower accuracy but complete privacy
- **Cloud models** offer higher accuracy but require data sharing
- **Filtered cloud** balances both but may miss context

### Performance vs Privacy
- **Local processing** is slower but private
- **Cloud processing** is faster but requires network and consent
- **Hybrid approach** optimizes based on content sensitivity

## Risks and Mitigations

### Accidental Data Exposure
**Risk**: Sensitive content accidentally sent to cloud AI
**Mitigation**: Aggressive content filtering, explicit consent requirements, transparency logging

### Privacy Configuration Complexity
**Risk**: Users choose wrong settings due to confusion
**Mitigation**: Safe defaults, clear explanations, guided setup process

### Local Model Quality
**Risk**: Local models provide poor classification accuracy
**Mitigation**: High-quality local models, pattern fallbacks, optional cloud enhancement

### Consent Fatigue
**Risk**: Too many consent requests overwhelm users
**Mitigation**: Smart defaults, batch consent requests, remember preferences

## Consequences

### Positive
- **Strong privacy protection** builds user trust
- **User control** over data sharing decisions
- **Compliance-ready** for enterprise environments
- **ADHD-friendly** through predictable, transparent operation

### Negative
- **Complex configuration** options for users to understand
- **Lower accuracy** with privacy-first defaults
- **Implementation complexity** supporting multiple AI backends
- **Performance variability** based on privacy choices

## Success Metrics

- **Default privacy compliance**: 95% of users never send unfiltered content to cloud
- **User understanding**: Users can correctly explain their privacy settings
- **Filtering effectiveness**: <1% sensitive content detected in cloud-sent data
- **Performance acceptable**: Local processing meets accuracy thresholds for common cases

This privacy-first AI strategy ensures that intelligent memory classification respects developer privacy while providing the accuracy benefits of AI when users explicitly choose to use cloud services.