import os
import yaml
import re
import json

PROMPTSET_PATH = "services/repo-truth-extractor/promptsets/v4/promptset.yaml"

def parse_markdown_sections(text):
    sections = {}
    current_section = None
    lines = []
    
    for line in text.split('\n'):
        match = re.match(r'^#+\s+(.+)$', line.strip())
        if match:
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(lines).strip()
            
            # Start new section
            # remove any trailing/leading spaces, normalize casing might help but lets keep exact
            current_section = match.group(1).strip()
            lines = []
        else:
            if current_section:
                lines.append(line)
    
    if current_section:
        sections[current_section] = '\n'.join(lines).strip()
        
    return sections

def count_words(text):
    # simple word count removing special chars
    words = re.findall(r'\b\w+\b', text)
    return len(words)

def main():
    if not os.path.exists(PROMPTSET_PATH):
        print(f"Error: {PROMPTSET_PATH} not found.")
        return

    with open(PROMPTSET_PATH, 'r') as f:
        promptset = yaml.safe_load(f)

    required_sections = promptset.get('required_prompt_sections', [])
    print(f"Required sections from promptset.yaml: {required_sections}")

    phases = promptset.get('phases', {})
    prompt_files = []
    for phase_name, phase_data in phases.items():
        for step in phase_data.get('steps', []):
            if 'prompt_file' in step:
                prompt_files.append(step['prompt_file'])
    
    print(f"Discovered {len(prompt_files)} prompt files from promptset.yaml.")

    results = []
    
    STUB_THRESHOLD = 5 # Words
    
    counts = {
        'complete': 0,
        'partial': 0,
        'stub': 0,
        'missing_file': 0
    }

    issues = []

    for pf in prompt_files:
        if not os.path.exists(pf):
            counts['missing_file'] += 1
            issues.append(f"MISSING FILE: {pf}")
            continue
            
        with open(pf, 'r') as f:
            content = f.read()

        sections = parse_markdown_sections(content)
        
        # We need to map observed section titles to required ones, 
        # as sometimes they might be formatted slightly differently, 
        # but let's try exact or case-insensitive matching first.
        sections_lower = {k.lower(): v for k, v in sections.items()}
        
        missing_sections = []
        stub_sections = []
        
        for req in required_sections:
            req_l = req.lower()
            if req_l not in sections_lower:
                missing_sections.append(req)
            else:
                words = count_words(sections_lower[req_l])
                if words <= STUB_THRESHOLD:
                    stub_sections.append((req, words))

        is_stub = len(stub_sections) > 0 and len(missing_sections) == 0
        is_partial = len(missing_sections) > 0

        if is_partial:
            counts['partial'] += 1
            issues.append(f"PARTIAL: {pf}\n  Missing: {missing_sections}\n  Stubs: {stub_sections}")
        elif is_stub:
            counts['stub'] += 1
            issues.append(f"STUB: {pf}\n  Stubs: {stub_sections}")
        else:
            counts['complete'] += 1

        results.append({
            'file': pf,
            'missing': missing_sections,
            'stubs': [s[0] for s in stub_sections]
        })

    print("-" * 50)
    print("AUDIT RESULTS SUMMARY")
    print("-" * 50)
    print(f"Total files checked: {len(prompt_files)}")
    for k, v in counts.items():
        print(f"  {k}: {v}")

    print("\nISSUES:")
    for iss in issues:
        print(iss)

    with open('AUDIT_RESULTS.json', 'w') as f:
        json.dump({
            'counts': counts,
            'issues': issues,
            'results': results
        }, f, indent=2)
    print("\nDetailed results written to AUDIT_RESULTS.json.")

if __name__ == "__main__":
    main()
