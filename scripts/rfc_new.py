#!/usr/bin/env python3
import os, re, sys, datetime, textwrap
if len(sys.argv) < 2:
    sys.exit("Usage: rfc_new.py "Title" [feature_id]")
title = sys.argv[1]
feature = sys.argv[2] if len(sys.argv) > 2 else ""
base = "docs/91-rfc"; os.makedirs(base, exist_ok=True)
def next_num():
    n=1
    for fn in os.listdir(base):
        m=re.match(r"rfc-(\d{4})-", fn)
        if m: n=max(n,int(m.group(1))+1)
    return f"{n:04d}"
num = next_num()
slug = re.sub(r"[^a-z0-9]+","-", title.lower()).strip("-")
today = datetime.date.today().isoformat()
path = f"{base}/rfc-{num}-{slug}.md"
fm = f"""---
id: rfc-{num}
title: {title}
type: rfc
status: draft
author: @hu3mann
created: {today}
last_review: {today}
sunset: {today}
feature_id: {feature}
tags: []
---

## Problem

## Context

## Options
| Option | Pros | Cons |
|---|---|---|

## Proposed Direction

## Open Questions

## Risks

## Timeline

## Reviewers
"""
open(path,"w",encoding="utf-8").write(fm)
print("Created", path)
