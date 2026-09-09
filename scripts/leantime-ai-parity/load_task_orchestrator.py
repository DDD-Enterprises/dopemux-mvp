#!/usr/bin/env python3
"""Dry-run-first loader for LTAIP Task Orchestrator workflow epics."""
from __future__ import annotations
import argparse, json, os, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

APPROVAL = "LTAIP_TASK_ORCHESTRATOR_LOAD"
ALLOWED_PRIORITY = {"critical","high","medium","low"}
ALLOWED_STATUS = {"planned","in-planning","ready","in-progress","done"}

def request_json(method, url, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read().decode("utf-8")
        return resp.status, json.loads(body) if body else {}

def validate_entry(entry):
    req = entry["request"]
    for key in ("title","description","business_value","acceptance_criteria","priority","status","tags","adhd_metadata","idempotency_key"):
        if key not in req:
            raise ValueError(f"{entry['client_ref']}: missing request field {key}")
    if req["priority"] not in ALLOWED_PRIORITY: raise ValueError("invalid priority")
    if req["status"] not in ALLOWED_STATUS: raise ValueError("invalid status")
    if not req["idempotency_key"]: raise ValueError("missing idempotency_key")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--payload", required=True)
    mode=ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    ap.add_argument("--approve")
    ap.add_argument("--base-url", default=os.getenv("TASK_ORCHESTRATOR_URL","http://localhost:8000"))
    ap.add_argument("--receipts", default="task-orchestrator-load-receipts.json")
    args=ap.parse_args()
    doc=json.loads(Path(args.payload).read_text())
    entries=[doc["root_epic"],*doc["epics"]]
    for entry in entries: validate_entry(entry)
    print(json.dumps({"mode":"apply" if args.apply else "dry-run","base_url":args.base_url,"entries":len(entries),"client_refs":[e["client_ref"] for e in entries]},indent=2))
    if not args.apply:
        return 0
    if args.approve != APPROVAL:
        print(f"Refusing apply: pass --approve {APPROVAL}", file=sys.stderr); return 2
    base=args.base_url.rstrip("/")
    try:
        status, health=request_json("GET",base+"/health")
    except Exception as exc:
        print(f"Health check failed: {exc}",file=sys.stderr); return 3
    if status != 200:
        print(f"Unexpected health status {status}",file=sys.stderr); return 3
    query=urllib.parse.urlencode({"tag":"program:LTAIP","limit":100})
    _, existing_doc=request_json("GET",base+"/api/workflow/epics?"+query)
    existing={e.get("idempotency_key"):e for e in existing_doc.get("epics",[]) if e.get("idempotency_key")}
    receipts=[]
    for entry in entries:
        key=entry["request"]["idempotency_key"]
        if key in existing:
            receipts.append({"client_ref":entry["client_ref"],"status":"SKIPPED_EXISTING","epic_id":existing[key].get("id"),"idempotency_key":key}); continue
        try:
            code, body=request_json("POST",base+"/api/workflow/epics",entry["request"])
            receipts.append({"client_ref":entry["client_ref"],"status":"CREATED","http_status":code,"epic_id":body.get("epic_id"),"idempotency_key":key})
        except Exception as exc:
            receipts.append({"client_ref":entry["client_ref"],"status":"FAILED","error":str(exc),"idempotency_key":key})
            Path(args.receipts).parent.mkdir(parents=True,exist_ok=True)
            Path(args.receipts).write_text(json.dumps({"partial":True,"receipts":receipts},indent=2)+"\n")
            print("Partial load. No delete endpoint is assumed. Reconcile receipts before retry.",file=sys.stderr); return 4
    Path(args.receipts).parent.mkdir(parents=True,exist_ok=True)
    Path(args.receipts).write_text(json.dumps({"partial":False,"receipts":receipts},indent=2)+"\n")
    print(json.dumps({"loaded":True,"receipts":args.receipts},indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
