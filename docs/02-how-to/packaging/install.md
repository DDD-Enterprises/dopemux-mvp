---
id: INSTALL
title: Install
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Install (explanation) for dopemux documentation and developer workflows.
---
# Installation Guide

## Prerequisites
- **Python 3.10+**
- **GitHub CLI (`gh`)**: Must be authenticated (`gh auth login`).
- **Permissions**: The user/agent must have `write` access to the target repository.

## Install Path
```bash
# Clone the repository
git clone https://github.com/hu3mann/dopemux-mvp.git
cd dopemux-mvp

# Install dependencies
pip install -r requirements.txt
```

## Tool Verification
```bash
python3 -m src.dopemux_pr_merge_specialist.cli --version
```
