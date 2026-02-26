import glob
import os
import re

files = glob.glob('services/repo-truth-extractor/prompts/v3/PROMPT_[CDR]*.md')

for file_path in files:
    with open(file_path, 'r') as f:
        content = f.read()

    if "OUTPUTS:" in content:
        continue

    print(f"Adding OUTPUTS to {file_path}")

    # Find what json files it might be expecting.
    # Look for things like `CODE_INVENTORY.json` or `DOC_PARTITIONS.json`
    outputs_found = set(re.findall(r'([A-Z_]+\.json)', content))
    
    # Exclude INVENTORY and PARTITIONS from the inputs section if possible, 
    # but usually the Goal/Task specifies the actual outputs.
    # A simple heuristic: any .json file mentioned in the markdown block is an output candidate.
    
    # Let's extract just the final markdown block
    if "```markdown" in content:
        block = content.split("```markdown")[-1]
        block_outputs = set(re.findall(r'([A-Z_]+\.json)', block))
        if block_outputs:
            outputs_found = block_outputs
            
    outputs_found = sorted(list(outputs_found))

    if not outputs_found:
        # Fallback based on filename prefix
        basename = os.path.basename(file_path)
        prefix = basename.split('_')[1]
        phase = prefix[0]
        if phase == 'C':
            outputs_found = ['CODE_INVENTORY.json', 'CODE_PARTITIONS.json']
        elif phase == 'D':
             outputs_found = ['DOC_INVENTORY.json', 'DOC_PARTITIONS.json']
        elif phase == 'R':
             outputs_found = ['TRUTH_MAP.json']

    outputs_text = '\nOUTPUTS:\n' + '\n'.join([f'\t•\t{out}' for out in outputs_found]) + '\n'

    if '```markdown' in content:
        lines = content.split('\n')
        for i in range(len(lines)-1, -1, -1):
            if lines[i].startswith('```'):
                lines.insert(i, outputs_text)
                break
        new_content = '\n'.join(lines)
    else:
        new_content = content + '\n```markdown\n' + outputs_text + '```\n'
    
    with open(file_path, 'w') as f:
        f.write(new_content)
