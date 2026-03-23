import re

with open("src/dopemux/pm/reads.py", "r") as f:
    content = f.read()

# Replace all empty string checks with proper type checks and empty checks
content = re.sub(
    r'if not project_id:',
    r'if not project_id or not isinstance(project_id, str):',
    content
)

with open("src/dopemux/pm/reads.py", "w") as f:
    f.write(content)
