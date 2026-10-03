import subprocess
import hashlib

def get_deleted_files():
    output = subprocess.check_output(['git', 'diff', '--name-status', '728d7c42e9ab..176d965e8b'])
    return [line.split('\t')[1] for line in output.decode().splitlines() if line.startswith('D')]

def get_file_content(commit, path):
    try:
        return subprocess.check_output(['git', 'show', f'{commit}:{path}'])
    except subprocess.CalledProcessError:
        return None

def get_all_head_files():
    output = subprocess.check_output(['git', 'ls-tree', '-r', 'HEAD', '--name-only'])
    return output.decode().splitlines()

deleted_files = get_deleted_files()
head_files = get_all_head_files()

head_contents = {}
for hf in head_files:
    if hf.startswith('proof/') or hf.startswith('reports/'):
        continue
    content = get_file_content('HEAD', hf)
    if content:
        head_contents[hf] = content

results = {}
for df in deleted_files:
    old_content = get_file_content('728d7c42e9ab', df)
    if df.endswith('zen-mcp-server__CLAUDE.md'):
        # superseded by the live docker/mcp-servers-source/pal/pal-mcp-server/CLAUDE.md
        live_content = head_contents.get('docker/mcp-servers-source/pal/pal-mcp-server/CLAUDE.md')
        if live_content and live_content == old_content:
             print(f"MATCH: {df} == docker/mcp-servers-source/pal/pal-mcp-server/CLAUDE.md")
             continue
        elif live_content:
             print(f"SPECIAL CHECK: {df} differs from docker/mcp-servers-source/pal/pal-mcp-server/CLAUDE.md")
             # Let's see if they are mostly the same or if I need to check something else. The instruction says "superseded by", maybe not byte identical?
             # Wait, instruction says: "identical to a kept file except... or (...) superseded by...". "superseded by" might mean it's not byte identical. I should output if they are exactly identical.
             pass

    found = False
    for hf, hc in head_contents.items():
        if hc == old_content:
            print(f"MATCH: {df} == {hf}")
            found = True
            break
        elif df.startswith('docs/archive/history/sourceFiles/'):
            # check 12 line yaml frontmatter
            lines = hc.split(b'\n')
            if len(lines) > 12 and b'\n'.join(lines[12:]) == old_content:
                print(f"MATCH (YAML): {df} == {hf} (without 12 lines)")
                found = True
                break
    if not found:
        print(f"NO MATCH: {df}")

