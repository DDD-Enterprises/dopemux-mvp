
#!/usr/bin/env python3
"""Ensure every docs/*.md has required YAML front-matter.
- Adds missing front-matter
- Updates last_review to today if stale
- Fills owner if missing (default @hu3mann)
Usage:
  python scripts/docs_frontmatter_guard.py --fix
"""
import sys, re, os, datetime, yaml, io

TODAY = datetime.date.today()
DEFAULT_OWNER = "@hu3mann"
REQUIRED = ["id","title","type","owner","last_review","next_review"]

def parse_frontmatter(text):
    if text.startswith('---\n'):
        end = text.find('\n---\n', 4)
        if end != -1:
            fm = text[4:end]
            body = text[end+5:]
            data = yaml.safe_load(fm) or {}
            return data, body
    return None, text

def build_frontmatter(data):
    buf = io.StringIO()
    yaml.safe_dump(data, buf, sort_keys=False)
    return f"---\n{buf.getvalue()}---\n"

def ensure_fm(path, fix=False):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    data, body = parse_frontmatter(text)
    changed = False
    if data is None:
        # Create new front-matter
        slug = os.path.splitext(os.path.basename(path))[0]
        title = slug.replace('-', ' ').title()
        data = {
            "id": slug,
            "title": title,
            "type": guess_type(path),
            "owner": DEFAULT_OWNER,
            "last_review": str(TODAY),
            "next_review": str(TODAY + datetime.timedelta(days=90)),
        }
        changed = True
    else:
        # Fill missing keys
        for k in REQUIRED:
            if k not in data:
                if k == "id":
                    data[k] = os.path.splitext(os.path.basename(path))[0]
                elif k == "title":
                    data[k] = os.path.splitext(os.path.basename(path))[0].replace('-', ' ').title()
                elif k == "type":
                    data[k] = guess_type(path)
                elif k == "owner":
                    data[k] = DEFAULT_OWNER
                elif k == "last_review":
                    data[k] = str(TODAY)
                elif k == "next_review":
                    data[k] = str(TODAY + datetime.timedelta(days=90))
                changed = True
    if changed and fix:
        fm = build_frontmatter(data)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(fm + body.lstrip())
    return changed

def guess_type(path):
    p = path.replace('\\','/')
    if '/90-adr/' in p: return 'adr'
    if '/91-rfc/' in p: return 'rfc'
    if '/92-runbooks/' in p: return 'runbook'
    if '/01-tutorials/' in p: return 'tutorial'
    if '/02-how-to/' in p: return 'how-to'
    if '/03-reference/' in p: return 'reference'
    if '/04-explanation/' in p: return 'explanation'
    return 'explanation'

def main():
    fix = '--fix' in sys.argv
    changed_files = []
    for root, _, files in os.walk('docs'):
        for fn in files:
            if fn.endswith('.md'):
                path = os.path.join(root, fn)
                if ensure_fm(path, fix=fix):
                    changed_files.append(path)
    if changed_files:
        print(f"Updated {len(changed_files)} files:")
        for p in changed_files:
            print(" -", p)
        raise SystemExit(1 if not fix else 0)
    else:
        print("All docs have front-matter.")
        raise SystemExit(0)

if __name__ == '__main__':
    main()
