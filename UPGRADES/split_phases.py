
import re
import os
from pathlib import Path

def split_phase_file(file_path):
    content = Path(file_path).read_text()
    # Sections start with "## A0:", "## H1:", etc.
    # regex to capture the code (A0) and the rest of the title
    pattern = re.compile(r'^##\s+([A-Z][0-9]+):\s+(.+)$', re.MULTILINE)
    
    matches = list(pattern.finditer(content))
    
    # Also find the header preamble (before first section) to check for global rules/context if needed
    # But usually per-prompt is self contained or we prepend a common header.
    # For now, let's just extract the sections.
    
    for i, match in enumerate(matches):
        section_code = match.group(1)
        section_title = match.group(2).strip()
        start = match.end()
        
        # End is start of next match or end of file
        if i < len(matches) - 1:
            end = matches[i+1].start()
        else:
            end = len(content)
            
        section_body = content[start:end].strip()
        
        # Construct new filename: PROMPT_A0_REPO_CONTROL_INVENTORY.md
        # logical name derivation
        slug = section_title.split('(')[0].strip().replace(' ', '_').upper()
        slug = re.sub(r'[^A-Z0-9_]', '_', slug) # Sanitize for fs
        # remove strictly duplicate "REPO_CONTROL_" if it makes it too long, but safety first
        
        filename = f"PROMPT_{section_code}_{slug}.md"
        output_path = Path("UPGRADES") / filename
        
        # Prepend a standard header if missing
        full_content = f"# Prompt {section_code}: {section_title}\n\n{section_body}"
        
        with open(output_path, "w") as f:
            f.write(full_content)
        print(f"Wrote {output_path}")

def main():
    upgrades_dir = Path("UPGRADES")
    phase_files = upgrades_dir.glob("PHASE_*.md")
    for p in phase_files:
        print(f"Processing {p.name}...")
        split_phase_file(p)

if __name__ == "__main__":
    main()
