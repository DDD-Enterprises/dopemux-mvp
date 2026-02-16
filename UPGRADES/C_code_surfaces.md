# Phase C: Code Surfaces

## C: Code Surfaces (Tier 1)

Output files
	•	C1_CODE_SURFACES.json
	•	C2_CODE_DEPENDENCIES.json

ROLE: Code Analyst / Architect. JSON only. No code generation.

TARGET: Repo working tree.
- src/**
- services/**

SCOPE:
- **src/dopemux/cli.py** (Entry points)
- **src/dopemux/extraction/** (Document pipeline)
- **src/dopemux/memory/** (Chronicle/Capture)
- **services/serena/** (MCP Server)
- **services/conport/** (MCP Server)
- **services/zen/** (MCP Server)

OUTPUT 1: C1_CODE_SURFACES.json
Extract public interfaces (classes, functions, methods) for key subsystems.
Structure:
{
  "subsystems": [
    {
      "name": "dopemux.extraction",
      "interfaces": [
        { "name": "UnifiedDocumentPipeline", "methods": [...] }
      ]
    },
    ...
  ]
}

OUTPUT 2: C2_CODE_DEPENDENCIES.json
Map dependencies between subsystems (imports, calls).
Structure:
{
  "dependencies": [
    { "source": "dopemux.cli", "target": "dopemux.extraction", "type": "import" }
  ]
}

RULES:
- Focus on architectural boundaries.
- Extract docstrings as descriptions.
- Identify key classes and their responsibilities.
- Ignore test files.
