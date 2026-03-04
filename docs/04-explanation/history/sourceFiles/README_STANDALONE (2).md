# Dopemux Standalone CLI

An ADHD-optimized document analysis tool that transforms any codebase into a structured, searchable knowledge base.

## Features

🧠 **ADHD-Optimized Processing**
- Gentle progress feedback with encouraging messages
- 25-minute processing chunks to match attention spans
- Visual completion summaries and statistics
- Clear next-step guidance

🔍 **Multi-Angle Analysis**
- Extracts features, components, and subsystems
- Identifies architectural decisions and constraints
- Maps technologies, patterns, and interfaces
- Creates comprehensive evidence links

🚀 **Semantic Search Ready**
- Voyage Context-3 embeddings for precise search
- Milvus Lite support for lightweight deployment
- Full traceability through evidence networks
- Export to TSV for further analysis

## Quick Start

### Installation

```bash
# Clone or download this repository
cd dopemux-mvp

# Run the installer
python install.py

# Add to PATH (follow installer instructions)
export PATH="$PATH:$HOME/.local/bin"
```

### Basic Usage

```bash
# Analyze current directory
dopemux analyze

# Analyze specific project
dopemux analyze /path/to/my/project

# With custom options
dopemux analyze . --output ./analysis --max-files 100

# Show all options
dopemux analyze --help
```

## Command Reference

### `dopemux analyze [DIRECTORY]`

Analyze a codebase with multi-angle document processing.

**Options:**
- `--output, -o`: Output directory for analysis results
- `--embedding-model, -m`: Embedding model (default: voyage-context-3)
- `--milvus-uri`: Milvus database URI (file path for Lite mode)
- `--max-files`: Maximum number of files to process
- `--batch-size`: Batch size for processing (default: 10)
- `--extensions`: Comma-separated file extensions to include
- `--exclude`: Comma-separated patterns to exclude

**Examples:**
```bash
# Basic analysis
dopemux analyze .

# Python project only
dopemux analyze . --extensions py,pyi,md

# Skip test directories
dopemux analyze . --exclude "*/tests/*,*/test/*"

# Large project with limits
dopemux analyze . --max-files 500 --batch-size 20

# With semantic embeddings
dopemux analyze . --milvus-uri ./embeddings.db
```

## Output Structure

After analysis, you'll find these files in the output directory:

```
.dopemux/analysis/
├── atomic_units.tsv           # Normalized document units
├── features_registry.tsv      # Extracted features
├── components_registry.tsv    # Technical components
├── subsystems_registry.tsv    # Architectural subsystems
├── research_registry.tsv      # Decisions, constraints, patterns
├── evidence_links.tsv         # Traceability relationships
└── embeddings/               # Vector database (if enabled)
```

## File Types Supported

- **Documentation**: `.md`, `.txt`, `.rst`, `.adoc`, `.org`
- **Code**: `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.html`, `.css`
- **Configuration**: `.yml`, `.yaml`, `.json`, `.toml`
- **Other**: `.tex` (LaTeX)

## ADHD Accommodations

### Processing Style
- **Gentle Feedback**: Encouraging progress messages
- **Chunked Processing**: Works in 25-minute focused segments
- **Visual Progress**: Clear completion indicators and statistics
- **Context Preservation**: Saves progress automatically

### Output Design
- **Structured Data**: TSV format for easy filtering and analysis
- **Clear Relationships**: Evidence links connect entities to sources
- **Actionable Results**: Ready for semantic search and navigation
- **Completion Celebration**: Positive reinforcement when finished

## Semantic Search Setup

For semantic search capabilities, specify a Milvus URI:

```bash
# Use Milvus Lite (file-based, no Docker needed)
dopemux analyze . --milvus-uri ./my-project-embeddings.db

# Results can then be searched programmatically
python -c "
from pymilvus import MilvusClient
client = MilvusClient('./my-project-embeddings.db')
results = client.search(
    collection_name='documents',
    data=[[0.1, 0.2, ...]],  # Your query vector
    limit=5
)
print(results)
"
```

## Integration with Development Workflows

### VS Code Integration
Use the generated TSV files with extensions like:
- **Excel Viewer**: View registries directly in VS Code
- **Rainbow CSV**: Syntax highlighting for TSV files
- **Search Results**: Quick navigation through evidence links

### CI/CD Integration
```yaml
# .github/workflows/analyze.yml
- name: Analyze Codebase
  run: |
    pip install -e .
    dopemux analyze . --output ./analysis-results

- name: Upload Analysis
  uses: actions/upload-artifact@v3
  with:
    name: codebase-analysis
    path: ./analysis-results/
```

### Documentation Generation
```bash
# Generate project knowledge base
dopemux analyze . --output ./docs/analysis

# Use results for automated documentation
python scripts/generate-docs.py --analysis ./docs/analysis
```

## Troubleshooting

### Installation Issues
```bash
# Check Python version (3.8+ required)
python --version

# Verify pip and venv
python -m pip --version
python -m venv --help

# Manual installation
pip install -e .
```

### Analysis Issues
```bash
# Test with small dataset first
dopemux analyze . --max-files 10

# Check file permissions
ls -la /path/to/analyze

# Verbose output for debugging
dopemux --verbose analyze .
```

### Performance Optimization
```bash
# Reduce batch size for memory-constrained systems
dopemux analyze . --batch-size 5

# Skip embeddings for faster processing
dopemux analyze . # (omit --milvus-uri)

# Focus on specific file types
dopemux analyze . --extensions md,py,js
```

## Advanced Usage

### Custom Extraction Patterns
The analysis uses 11 extraction patterns by default. For custom patterns, modify `src/dopemux/analysis/extractor.py`.

### Embedding Models
Supports various Voyage AI models:
- `voyage-context-3` (default, 1024D)
- `voyage-context-3-large` (2048D, higher quality)
- `voyage-code-2` (optimized for code)

### Database Options
- **Milvus Lite**: File-based, no Docker (`--milvus-uri ./file.db`)
- **Milvus Server**: Full server (`--milvus-uri http://localhost:19530`)

## Contributing

This standalone CLI is extracted from the larger Dopemux project. For contributions:

1. Fork the repository
2. Make changes to `src/dopemux/analysis/`
3. Test with `python -m pytest tests/`
4. Submit pull request

## License

MIT License - see LICENSE file for details.

---

🧠 **Built for neurodivergent developers** - Dopemux prioritizes cognitive accessibility, gentle feedback, and ADHD-friendly workflows in all its tools.