import json, subprocess

def get_json(commit, path):
    content = subprocess.check_output(['git', 'show', f'{commit}:{path}'])
    return json.loads(content)

old = get_json('728d7c42e9ab', 'proof/CCAR-002/SOURCE_MANIFEST.json')
new = get_json('176d965e8b', 'proof/CCAR-002/SOURCE_MANIFEST.json')

changed_personas = []
for k, v in new.get('active_personas', {}).items():
    if v['sha256'] != old['active_personas'][k]['sha256']:
        changed_personas.append(k)
        actual_hash = subprocess.check_output(['shasum', '-a', '256', v['path']]).decode().split()[0]
        if actual_hash != v['sha256']:
            print(f"FAIL hash mismatch for {k}: {actual_hash} != {v['sha256']}")
        else:
            print(f"OK hash match for {k}: {actual_hash}")
            # check the diff
            diff = subprocess.check_output(['git', 'diff', '728d7c42e9ab..176d965e8b', '--', v['path']]).decode()
            print(f"Diff for {k}:")
            for line in diff.splitlines():
                if line.startswith('+') or line.startswith('-'):
                    print(line)

print(f"Changed personas count: {len(changed_personas)}")

changed_agents = []
for k, v in new.get('active_agents', {}).items():
    if v['sha256'] != old['active_agents'][k]['sha256']:
        changed_agents.append(k)

print(f"Changed agents count: {len(changed_agents)}")

