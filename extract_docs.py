import os
import json
import hashlib
import re

DOCS_DIR = "/Users/hue/code/dopemux-mvp/docs"
MEGA_DIR = "/Users/hue/code/dopemux-mvp/MEGA"

def get_sha256(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def extract_docs():
    doc_index = []
    doc_claims = []
    doc_workflows = []
    doc_boundaries = []
    doc_supersession = []
    doc_glossary = []

    claim_keywords = ["MUST", "SHOULD", "MUST NOT", "SHALL", "REQUIRED", "GUARANTEE", "DEFAULT", "INVARIANT", "SINGLE SOURCE OF TRUTH", "FAIL-CLOSED", "APPEND-ONLY"]
    boundary_patterns = [
        r"(.*?) is authoritative for (.*?)",
        r"(.*?) must not do (.*?)",
        r"(.*?) writes to (.*?)",
        r"Only (.*?) may (.*?)"
    ]
    workflow_verbs = ["ingest", "redact", "promote", "rank", "emit", "route", "store", "mirror", "query"]

    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith(".md"):
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, DOCS_DIR)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.splitlines()

                # 1. DOC_INDEX
                title = ""
                headings = []
                for line in lines:
                    if line.startswith("# "):
                        title = line[2:].strip()
                    elif line.startswith("## ") or line.startswith("### "):
                        headings.append(line.strip("# ").strip())
                
                status = "ACTIVE"
                if "DEPRECATED" in content.upper(): status = "DEPRECATED"
                elif "DRAFT" in content.upper(): status = "DRAFT"

                anchors = []
                for i, line in enumerate(lines):
                    if len(line.strip()) > 10 and len(line.split()) <= 12:
                        anchors.append({"text": line.strip(), "line": i+1})
                        if len(anchors) >= 3: break

                doc_index.append({
                    "path": rel_path,
                    "sha256": get_sha256(content),
                    "title": title or file,
                    "headings": headings[:10],
                    "status": status,
                    "anchors": anchors
                })

                # 2. DOC_CLAIMS
                for i, line in enumerate(lines):
                    for kw in claim_keywords:
                        if kw in line.upper():
                            # Atomic claim extraction: look for sentences
                            sentences = re.split(r'(?<=[.!?]) +', line)
                            for s in sentences:
                                if kw in s.upper():
                                    doc_claims.append({
                                        "claim_type": kw,
                                        "normalized_text": s.strip(),
                                        "original_quote": s.strip(),
                                        "doc_path": rel_path,
                                        "line_range": [i+1, i+1],
                                        "heading_path": "" # Simplified
                                    })

                # 3. DOC_WORKFLOWS
                # Look for lists or numbered steps that contain workflow verbs
                current_workflow = None
                for i, line in enumerate(lines):
                    if line.startswith("#"):
                        current_workflow = line.strip("# ").strip()
                    
                    if re.match(r"^(\d+\.|\-|\*)\s", line):
                        if any(verb in line.lower() for verb in workflow_verbs):
                            doc_workflows.append({
                                "name": current_workflow or "General",
                                "step": line.strip(),
                                "doc_path": rel_path,
                                "line": i+1
                            })

                # 4. DOC_BOUNDARIES
                for i, line in enumerate(lines):
                    for pattern in boundary_patterns:
                        if re.search(pattern, line, re.I):
                            doc_boundaries.append({
                                "statement": line.strip(),
                                "doc_path": rel_path,
                                "line": i+1
                            })

                # 5. DOC_SUPERSESSION
                if "supersedes" in content.lower() or "deprecated" in content.lower():
                    for i, line in enumerate(lines):
                        if "supersedes" in line.lower() or "deprecated" in line.lower():
                            doc_supersession.append({
                                "text": line.strip(),
                                "doc_path": rel_path,
                                "line": i+1
                            })

                # 6. DOC_GLOSSARY
                # Look for Bold Term: Definition or Bold Term - Definition
                glossary_matches = re.findall(r"^\*\*([^*]+)\*\*[:\-]\s*(.*)", content, re.MULTILINE)
                for term, definition in glossary_matches:
                    doc_glossary.append({
                        "term": term.strip(),
                        "definition": definition.strip(),
                        "doc_path": rel_path
                    })

    # Write output files
    with open(os.path.join(MEGA_DIR, "DOC_INDEX.json"), "w") as f:
        json.dump(doc_index, f, indent=2)
    with open(os.path.join(MEGA_DIR, "DOC_CLAIMS.json"), "w") as f:
        json.dump(doc_claims, f, indent=2)
    with open(os.path.join(MEGA_DIR, "DOC_WORKFLOWS.json"), "w") as f:
        json.dump(doc_workflows, f, indent=2)
    with open(os.path.join(MEGA_DIR, "DOC_BOUNDARIES.json"), "w") as f:
        json.dump(doc_boundaries, f, indent=2)
    with open(os.path.join(MEGA_DIR, "DOC_SUPERSESSION.json"), "w") as f:
        json.dump(doc_supersession, f, indent=2)
    with open(os.path.join(MEGA_DIR, "DOC_GLOSSARY.json"), "w") as f:
        json.dump(doc_glossary, f, indent=2)

if __name__ == "__main__":
    extract_docs()
