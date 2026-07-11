$ git rev-parse --show-toplevel
/Users/hue/code/dopemux-merge-integrity-0001

$ git branch --show-current
codex/tp-dmx-merge-integrity-0001-investigation-adr

$ git rev-parse HEAD
b176747b339685e781de04268c46b7ae123abfbf

$ git status --short --branch
## codex/tp-dmx-merge-integrity-0001-investigation-adr
?? proof/TP-DMX-MERGE-INTEGRITY-0001/

$ git remote -v
mvp	https://github.com/DDD-Enterprises/dopemux-mvp.git (fetch)
mvp	https://github.com/DDD-Enterprises/dopemux-mvp.git (push)
origin	https://github.com/DDD-Enterprises/dopemux-mvp.git (fetch)
origin	https://github.com/DDD-Enterprises/dopemux-mvp.git (push)

$ git ls-files -v .claude/claude_config.json
S .claude/claude_config.json
