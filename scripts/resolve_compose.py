import sys

with open('compose.yml', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if '<<<<<<< HEAD' in line:
        skip = True
        continue
    if '=======' in line:
        skip = False
        continue
    if '>>>>>>> upstream/main' in line:
        continue
    if not skip:
        new_lines.append(line)

with open('compose.yml', 'w') as f:
    f.writelines(new_lines)
