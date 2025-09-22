#!/usr/bin/env python3
import os, re, sys, datetime, yaml
if len(sys.argv) < 2: sys.exit("Usage: rfc_promote.py docs/91-rfc/rfc-####-slug.md")
rfc_path = sys.argv[1]
txt = open(rfc_path,"r",encoding="utf-8").read()
end = txt.find("\n---\n", 4); front = yaml.safe_load(txt[4:end])
if front.get("type") != "rfc": sys.exit("Not an RFC.")
title = front["title"]; rid = front["id"]
today = datetime.date.today().isoformat()
base = "docs/90-adr"; os.makedirs(base, exist_ok=True)
def next_num():
    n=1
    for fn in os.listdir(base):
        m=re.match(r"ADR-(\d{4})-", fn)
        if m: n=max(n,int(m.group(1))+1)
    return f"{n:04d}"
num = next_num()
slug = re.sub(r"[^a-z0-9]+","-", title.lower()).strip("-")
fname = f"ADR-{num}-{today}-{slug}.md"; path = f"{base}/{fname}"
open(path,"w",encoding="utf-8").write(f"""---
id: adr-{num}
title: {title}
type: adr
status: proposed
date: {today}
author: @hu3mann
derived_from: {rid}
---

## Context

## Decision Drivers

## Considered Options

## Decision Outcome

## Consequences
""")
print("Created", path)
