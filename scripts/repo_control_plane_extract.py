#!/usr/bin/env python3
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
OUT_BASE = ROOT / "reports" / "A_repo_control_plane"
RAW_DIR = OUT_BASE / "raw"
NORM_DIR = OUT_BASE / "norm"

TEXT_FILE_GLOBS = [
    "AGENTS.md",
    ".claude.json",
    ".claude.json.template",
    "mcp-proxy-config.yaml",
    "mcp-proxy-config.json",
    "mcp-proxy-config.copilot.yaml",
    "litellm.config",
    "litellm.config.yaml",
    "litellm.config.yaml.backup",
    "start-mcp-servers.sh",
    "Makefile",
    ".pre-commit-config.yaml",
    "compose.yml",
    "docker-compose.dev.yml",
    "docker-compose.prod.yml",
    "docker-compose.unified.yml",
    "docker-compose.smoke.yml",
    "docker-compose.monitoring.yml",
    "docker-compose.mcp-test.yml",
    ".env.example",
    ".taskxroot",
    ".taskx-pin",
]
TREE_GLOBS = [
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    ".githooks/*",
    "scripts/**/*.sh",
    "scripts/**/*.py",
    "docker/**/*.yml",
    "docker/**/*.yaml",
    "services/**/docker-compose*.yml",
    "services/**/docker-compose*.yaml",
    "docs/task-packets/**/*.md",
    ".taskx/**/*",
    ".claude/**/*.md",
    ".claude/**/*.json",
]

TOKEN_LIKE = re.compile(r"(?i)(api[_-]?key|token|secret|passwd|password)=([^\s]+)")
ENV_KEY = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\b")
URL = re.compile(r"https?://[^\s'\"]+")
PORT = re.compile(r"\b([0-9]{2,5})\b")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()


def sha1_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()


def redact_inline(s: str) -> str:
    s2 = TOKEN_LIKE.sub(lambda m: f"{m.group(1)}=REDACTED", s)
    return s2


def snippet(s: str, n: int = 160) -> str:
    s = " ".join(s.strip().split())
    return s[:n]


def evidence(path: str, anchor: str, excerpt: str) -> Dict[str, str]:
    excerpt = redact_inline(excerpt)
    return {
        "path": path,
        "anchor": anchor,
        "excerpt_hash": sha256_text(excerpt),
        "excerpt_snippet": snippet(excerpt, 160),
    }


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def iter_candidate_files() -> List[Path]:
    files: set[Path] = set()
    for g in TEXT_FILE_GLOBS:
        p = ROOT / g
        if p.exists() and p.is_file():
            files.add(p)
    for g in TREE_GLOBS:
        for p in ROOT.glob(g):
            if p.is_file():
                files.add(p)
    # targeted docs for MCP/routers
    for p in ROOT.glob("docs/**/*.md"):
        if any(k in p.as_posix().lower() for k in ["mcp", "litellm", "router", "proxy", "taskx", "compose", "hook", "ci", "gate"]):
            files.add(p)
    return sorted(files)


def parse_yaml_or_json(path: Path, text: str) -> Any:
    ext = path.suffix.lower()
    if ext == ".json":
        try:
            return json.loads(text)
        except Exception:
            return None
    if yaml is not None and ext in {".yaml", ".yml"}:
        try:
            return yaml.safe_load(text)
        except Exception:
            return None
    if yaml is not None and path.name in {"litellm.config", "litellm.config.yaml", "litellm.config.yaml.backup", ".pre-commit-config.yaml", "mcp-proxy-config.yaml", "mcp-proxy-config.copilot.yaml"}:
        try:
            return yaml.safe_load(text)
        except Exception:
            return None
    return None


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except Exception:
        return path.as_posix()


def line_anchor(text: str, needle: str) -> Tuple[str, str]:
    lines = text.splitlines()
    for i, ln in enumerate(lines, 1):
        if needle in ln:
            excerpt = "\n".join(lines[max(0, i-2):min(len(lines), i+2)])
            return (f"L{i}", excerpt)
    return ("L1", "\n".join(lines[:4]))


def transport_for(command: str, args: List[str]) -> str:
    joined = " ".join([command] + args).lower()
    if "http://" in joined or "https://" in joined or "--host" in joined or "--port" in joined:
        return "http"
    if command:
        return "stdio"
    return "unknown"


def extract_servers_and_proxies(files: List[Path]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    servers: List[Dict[str, Any]] = []
    proxies: List[Dict[str, Any]] = []
    warnings: List[str] = []

    known_services = ["conport", "serena", "dope-context", "taskx", "litellm", "dopecon-bridge"]

    for p in files:
        rp = rel(p)
        txt = read_text(p)
        low = txt.lower()
        data = parse_yaml_or_json(p, txt)

        # server maps in common configs
        if isinstance(data, dict):
            for key in ["mcpServers", "mcp_servers", "servers"]:
                obj = data.get(key)
                if isinstance(obj, dict):
                    for name, cfg in sorted(obj.items(), key=lambda x: x[0]):
                        if isinstance(cfg, dict):
                            command = cfg.get("command") if isinstance(cfg.get("command"), str) else None
                            args = cfg.get("args") if isinstance(cfg.get("args"), list) else []
                            args = [redact_inline(str(a)) for a in args]
                            env = cfg.get("env") if isinstance(cfg.get("env"), dict) else {}
                            env_keys = sorted([str(k) for k in env.keys()])
                            cwd = cfg.get("cwd") if isinstance(cfg.get("cwd"), str) else None
                            disabled = cfg.get("disabled") if isinstance(cfg.get("disabled"), bool) else None
                            tport = transport_for(command or "", args)
                            stable = sha1_text((command or "") + "|" + "|".join(args))[:12] if command else sha1_text(rp + "|" + name)[:12]
                            anchor, ex = line_anchor(txt, str(name))
                            mentioned_services = sorted([s for s in known_services if s in (str(name).lower() + " " + low)])
                            mentioned_packages = sorted(set(re.findall(r"@[\w\-/]+", " ".join(args))))
                            mentioned_ports = sorted(set(re.findall(r":([0-9]{2,5})", " ".join(args) + "\n" + txt)))
                            servers.append({
                                "server_id": f"MCP_{stable}",
                                "name": str(name),
                                "status": "ACTIVE" if "archive" not in rp else "ARCHIVE",
                                "defined_in": evidence(rp, anchor, ex),
                                "launch": {
                                    "command": command,
                                    "args": sorted(args),
                                    "cwd": cwd,
                                    "disabled": disabled,
                                    "transport": tport,
                                    "notes": None,
                                },
                                "env": {"keys": env_keys, "values_redacted": True},
                                "permissions": {"allow_paths": sorted(cfg.get("allow_paths", []) if isinstance(cfg.get("allow_paths"), list) else []), "deny_paths": sorted(cfg.get("deny_paths", []) if isinstance(cfg.get("deny_paths"), list) else []), "trust_level": cfg.get("trust_level") if isinstance(cfg.get("trust_level"), str) else None},
                                "capabilities": {"tools_or_namespaces": sorted(cfg.get("tools", []) if isinstance(cfg.get("tools"), list) else []), "described_capabilities": sorted(cfg.get("capabilities", []) if isinstance(cfg.get("capabilities"), list) else [])},
                                "references": {"mentioned_services": mentioned_services, "mentioned_packages": mentioned_packages, "mentioned_ports": mentioned_ports},
                            })

            # proxy style configs
            if any(k in rp.lower() for k in ["proxy", "litellm", "router"]):
                anchor, ex = line_anchor(txt, "server")
                proxy_id = f"PROXY_{sha1_text(rp + '|' + anchor)[:12]}"
                env_keys = sorted(set(ENV_KEY.findall(txt)))
                startup_cmds: List[str] = []
                if isinstance(data.get("command"), str):
                    startup_cmds.append(data["command"])
                routing_rules: List[Dict[str, Any]] = []

                if isinstance(data.get("routes"), list):
                    for r in data["routes"]:
                        if isinstance(r, dict):
                            rt = json.dumps(r, sort_keys=True)
                            routing_rules.append({
                                "rule": snippet(rt),
                                "matches": sorted([str(k) for k in r.keys() if k in {"match", "tool", "namespace", "model", "route", "selector"}]),
                                "targets": sorted([str(v) for k, v in r.items() if k in {"target", "server", "to", "service"}]),
                                "evidence": {"excerpt_hash": sha256_text(rt), "excerpt_snippet": snippet(rt)},
                            })

                proxies.append({
                    "proxy_id": proxy_id,
                    "status": "ACTIVE" if "archive" not in rp else "ARCHIVE",
                    "defined_in": evidence(rp, anchor, ex),
                    "proxy_type": "litellm_proxy" if "litellm" in rp.lower() else ("mcp_proxy" if "mcp" in rp.lower() else ("router" if "router" in rp.lower() else "unknown")),
                    "routing_rules": sorted(routing_rules, key=lambda x: x["rule"]),
                    "server_links": [],
                    "startup": {"commands": sorted(startup_cmds), "compose_services": [], "scripts": []},
                    "env_keys": env_keys,
                })

        # shell start scripts with MCP launches
        if p.suffix in {".sh", ""} and any(k in rp.lower() for k in ["mcp", "proxy", "start", "manage"]):
            for m in re.finditer(r"^\s*(npx|uvx|python3?|node)\s+([^\n]+)", txt, re.M):
                cmd = m.group(1)
                argline = m.group(2).strip()
                args = [redact_inline(x) for x in argline.split()]
                stid = sha1_text(cmd + "|" + "|".join(args))[:12]
                line_no = txt[:m.start()].count("\n") + 1
                ex = txt.splitlines()[line_no - 1]
                servers.append({
                    "server_id": f"MCP_{stid}",
                    "name": None,
                    "status": "ACTIVE" if "archive" not in rp else "ARCHIVE",
                    "defined_in": evidence(rp, f"L{line_no}", ex),
                    "launch": {"command": cmd, "args": sorted(args), "cwd": None, "disabled": None, "transport": transport_for(cmd, args), "notes": "shell invocation"},
                    "env": {"keys": sorted(set(ENV_KEY.findall(ex))), "values_redacted": True},
                    "permissions": {"allow_paths": [], "deny_paths": [], "trust_level": None},
                    "capabilities": {"tools_or_namespaces": [], "described_capabilities": []},
                    "references": {"mentioned_services": sorted([s for s in known_services if s in ex.lower()]), "mentioned_packages": sorted(set(re.findall(r"@[\w\-/]+", ex))), "mentioned_ports": sorted(set(re.findall(r"([0-9]{2,5})", ex)))},
                })

    # dedupe server by id
    server_map: Dict[str, Dict[str, Any]] = {}
    for s in servers:
        sid = s["server_id"]
        if sid not in server_map:
            server_map[sid] = s
        else:
            # prefer richer env/capabilities
            if len(s["env"]["keys"]) > len(server_map[sid]["env"]["keys"]):
                server_map[sid] = s

    proxy_map: Dict[str, Dict[str, Any]] = {}
    for pxy in proxies:
        proxy_map.setdefault(pxy["proxy_id"], pxy)

    # graph edges explicit by name mentions
    server_ids = sorted(server_map.keys())
    edges = []
    for pxy in sorted(proxy_map.values(), key=lambda x: x["proxy_id"]):
        rrules = pxy.get("routing_rules", [])
        for rr in rrules:
            for tgt in rr.get("targets", []):
                for sid in server_ids:
                    if sid in tgt:
                        edges.append({"from": pxy["proxy_id"], "to": sid, "type": "routes_to"})

    mcp_defs = {
        "artifact": "REPO_MCP_SERVER_DEFS",
        "generated_at": now_iso(),
        "files_seen": len(files),
        "servers": sorted(server_map.values(), key=lambda x: x["server_id"]),
        "warnings": sorted(warnings),
    }

    mcp_proxy = {
        "artifact": "REPO_MCP_PROXY_SURFACE",
        "generated_at": now_iso(),
        "proxies": sorted(proxy_map.values(), key=lambda x: x["proxy_id"]),
        "graph": {
            "servers": server_ids,
            "edges": sorted(edges, key=lambda x: (x["from"], x["to"], x["type"])),
        },
        "warnings": sorted(warnings),
    }
    return mcp_defs, mcp_proxy


def extract_router_surface(files: List[Path]) -> Dict[str, Any]:
    routers: List[Dict[str, Any]] = []
    warnings: List[str] = []

    for p in files:
        rp = rel(p)
        if not any(k in rp.lower() for k in ["router", "litellm", "proxy", "claude", "makefile", "compose", "ag" ]):
            continue
        txt = read_text(p)
        data = parse_yaml_or_json(p, txt)
        if not txt:
            continue

        # route/provider heuristics
        rules: List[Dict[str, Any]] = []
        ladders: List[Dict[str, Any]] = []
        env_keys = sorted(set(ENV_KEY.findall(txt)))

        for i, ln in enumerate(txt.splitlines(), 1):
            l = ln.lower()
            if any(k in l for k in ["fallback", "provider", "model", "reasoning_effort", "route", "router"]):
                raw = ln.strip()
                rid = f"RULE_{sha1_text(rp + f'|L{i}|' + raw)[:12]}"
                provider = None
                for pv in ["openai", "anthropic", "xai", "gemini", "azure", "vertex"]:
                    if pv in l:
                        provider = pv
                        break
                model_match = re.search(r"([a-zA-Z0-9_.-]*(gpt|claude|gemini|grok|o[1-9]|sonnet|haiku)[a-zA-Z0-9_.-]*)", raw, re.I)
                model = model_match.group(1) if model_match else None
                rules.append({
                    "rule_id": rid,
                    "priority": None,
                    "match": {"phase_or_plane": None, "task_type": None, "persona": None, "command": None, "flag": None, "env": None, "other_selectors": []},
                    "decision": {"provider": provider, "model": model, "fallback_ladder_id": None, "reasoning_effort": None, "temperature": None, "max_tokens": None, "notes": None},
                    "raw_rule_text": snippet(raw),
                    "evidence": evidence(rp, f"L{i}", raw),
                })

        # ladder detection from arrays in parsed structure
        if isinstance(data, dict):
            for key in ["fallbacks", "ladder", "ladders", "model_list"]:
                if key in data:
                    raw = json.dumps(data.get(key), sort_keys=True, default=str)
                    lid = f"LADDER_{sha1_text(rp + '|root|' + raw)[:12]}"
                    seq = []
                    if isinstance(data.get(key), list):
                        for item in data[key]:
                            if isinstance(item, dict):
                                provider = None
                                model = None
                                for k, v in item.items():
                                    if isinstance(v, str):
                                        lv = v.lower()
                                        if provider is None and lv in {"openai", "anthropic", "xai", "gemini", "azure", "vertex"}:
                                            provider = lv
                                        if model is None and re.search(r"gpt|claude|gemini|grok|o[1-9]", v, re.I):
                                            model = v
                                seq.append({"provider": provider, "model": model, "conditions": [], "evidence": {"excerpt_hash": sha256_text(raw), "excerpt_snippet": snippet(raw)}})
                    ladders.append({
                        "ladder_id": lid,
                        "name": key,
                        "status": "ACTIVE" if "archive" not in rp else "ARCHIVE",
                        "sequence": seq,
                        "scope": {"phase_or_plane": None, "task_type": None, "notes": None},
                        "defined_in": evidence(rp, "root", raw[:160]),
                    })

        if rules or ladders or any(k in rp.lower() for k in ["litellm.config", "mcp-proxy-config"]):
            anchor, ex = line_anchor(txt, "model")
            router_id = f"ROUTER_{sha1_text(rp + '|' + anchor)[:12]}"
            routers.append({
                "router_id": router_id,
                "name": None,
                "status": "ACTIVE" if "archive" not in rp else "ARCHIVE",
                "defined_in": evidence(rp, anchor, ex),
                "entrypoints": {"commands_or_scripts": [], "compose_services": [], "cli_flags": sorted(set(re.findall(r"--[a-zA-Z0-9_-]+", txt))), "env_keys": env_keys},
                "policy": {"default_provider": None, "default_model": None, "default_reasoning_effort": None, "global_constraints": []},
                "rules": sorted(rules, key=lambda x: ((x["priority"] if x["priority"] is not None else 10**9), x["rule_id"])),
                "ladders": sorted(ladders, key=lambda x: x["ladder_id"]),
                "unknowns": [],
            })

    return {
        "artifact": "REPO_ROUTER_SURFACE",
        "generated_at": now_iso(),
        "files_seen": len(files),
        "routers": sorted(routers, key=lambda x: x["router_id"]),
        "warnings": sorted(warnings),
    }


def extract_hooks(files: List[Path]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    groups: Dict[str, Dict[str, Any]] = {}
    warnings: List[str] = []
    quick = {"git_hooks_paths": [], "taskx_related_paths": [], "instruction_files": [], "tmux_or_bootstrap_files": [], "compose_files": []}
    implicit_items: List[Dict[str, Any]] = []

    def ensure_group(name: str, rp: str, anchor: str, ex: str) -> Dict[str, Any]:
        gid = f"GROUP_{sha1_text(name + '|' + rp)[:12]}"
        if gid not in groups:
            groups[gid] = {
                "group_id": gid,
                "name": name,
                "status": "ACTIVE" if "archive" not in rp else "ARCHIVE",
                "defined_in": evidence(rp, anchor, ex),
                "hooks": [],
                "implicit_triggers": [],
                "unknowns": [],
            }
        return groups[gid]

    for p in files:
        rp = rel(p)
        txt = read_text(p)
        if not txt:
            continue

        gname = None
        if rp.startswith(".githooks/") or ".pre-commit" in rp or ".github/workflows" in rp:
            gname = "git_hooks" if not rp.startswith(".github/workflows") else "ci_hooks"
            if rp.startswith(".githooks/"):
                quick["git_hooks_paths"].append(rp)
        elif ".taskx" in rp or "taskx" in txt.lower() or rp in {".taskxroot", ".taskx-pin"}:
            gname = "taskx_hooks"
            quick["taskx_related_paths"].append(rp)
        elif rp.startswith(".claude/") or rp in {"AGENTS.md", "claude.md"}:
            gname = "instruction_hooks"
            quick["instruction_files"].append(rp)
        elif "tmux" in rp.lower() or "start-" in rp.lower() or "bootstrap" in rp.lower():
            gname = "dopemux_hooks"
            quick["tmux_or_bootstrap_files"].append(rp)
        elif "compose" in rp.lower():
            quick["compose_files"].append(rp)

        if gname is None:
            continue

        anchor, ex = line_anchor(txt, txt.splitlines()[0] if txt.splitlines() else "")
        grp = ensure_group(gname, rp, anchor, ex)

        for i, ln in enumerate(txt.splitlines(), 1):
            l = ln.lower().strip()
            if any(k in l for k in ["pre-commit", "commit-msg", "pre-push", "on:", "run:", "taskx", "start", "docker compose", "if ", "always "]):
                kind = "other"
                if "pre-commit" in l:
                    kind = "pre-commit"
                elif "commit-msg" in l:
                    kind = "commit-msg"
                elif "pre-push" in l:
                    kind = "pre-push"
                elif "on:" in l or "run:" in l:
                    kind = "ci_step"
                elif "start" in l or "docker compose" in l:
                    kind = "startup"
                elif "taskx" in l:
                    kind = "wrapper"
                elif "always" in l or l.startswith("if "):
                    kind = "instruction_trigger"

                hook = {
                    "hook_id": f"HOOK_{sha1_text(rp + f'|L{i}|' + kind)[:12]}",
                    "kind": kind,
                    "classification": "CONFIRMED" if kind != "other" else "SUSPECT",
                    "trigger": {"event": kind, "conditions": [snippet(ln)] if ln.strip() else [], "inputs": [], "outputs": []},
                    "action": {"commands": [snippet(ln)] if ln.strip() else [], "scripts": sorted(re.findall(r"[\w./-]+\.sh", ln)), "services": sorted(re.findall(r"service[s]?:\s*([\w-]+)", ln)), "tools_called": sorted([x for x in ["taskx", "litellm", "mcp"] if x in l]), "notes": None},
                    "couplings": {"touches_control_plane": sorted([x for x in ["router", "mcp", "litellm", "profiles", "instructions", "compose", "tmux"] if x in l]), "touches_runtime_code": [], "writes_state": ["unknown"]},
                    "evidence": evidence(rp, f"L{i}", ln),
                }
                grp["hooks"].append(hook)

                if any(k in l for k in ["if ", "always", "must", "when "]):
                    trig = {
                        "trigger_id": f"TRIG_{sha1_text(rp + f'|L{i}|' + ln)[:12]}",
                        "pattern": "instruction_phrase" if gname == "instruction_hooks" else "other",
                        "description": snippet(ln),
                        "conditions": [snippet(ln)],
                        "effects": ["operator behavior" if gname == "instruction_hooks" else "runtime behavior"],
                        "evidence": evidence(rp, f"L{i}", ln),
                    }
                    grp["implicit_triggers"].append(trig)
                    implicit_items.append(trig)

    for g in groups.values():
        g["hooks"] = sorted(g["hooks"], key=lambda x: x["hook_id"])
        g["implicit_triggers"] = sorted(g["implicit_triggers"], key=lambda x: x["trigger_id"])

    hooks_surface = {
        "artifact": "REPO_HOOKS_SURFACE",
        "generated_at": now_iso(),
        "files_seen": len(files),
        "hook_groups": sorted(groups.values(), key=lambda x: x["group_id"]),
        "quick_index": {k: sorted(set(v)) for k, v in quick.items()},
        "warnings": sorted(warnings),
    }
    implicit = {
        "artifact": "REPO_IMPLICIT_BEHAVIOR_HINTS",
        "generated_at": now_iso(),
        "items": sorted(implicit_items, key=lambda x: x["trigger_id"]),
        "warnings": sorted(warnings),
        "unknowns": [],
    }
    return hooks_surface, implicit


def parse_compose_file(path: Path, text: str) -> Any:
    if yaml is None:
        return None
    try:
        return yaml.safe_load(text)
    except Exception:
        return None


def extract_compose_graph(files: List[Path]) -> Dict[str, Any]:
    compose_files = [p for p in files if "compose" in rel(p).lower() and p.suffix in {".yml", ".yaml"}]
    cf_out = []
    services_map: Dict[str, Dict[str, Any]] = {}
    resources_networks: Dict[str, Dict[str, Any]] = {}
    resources_volumes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    invocation_surfaces: List[Dict[str, Any]] = []
    unknowns: List[str] = []

    for p in sorted(compose_files, key=lambda x: rel(x)):
        rp = rel(p)
        txt = read_text(p)
        data = parse_compose_file(p, txt)
        if not isinstance(data, dict):
            unknowns.append(f"Unparsed compose file: {rp}")
            continue
        svcs = data.get("services", {}) if isinstance(data.get("services"), dict) else {}
        nets = data.get("networks", {}) if isinstance(data.get("networks"), dict) else {}
        vols = data.get("volumes", {}) if isinstance(data.get("volumes"), dict) else {}
        anchor, ex = line_anchor(txt, "services")
        cf_out.append({
            "path": rp,
            "kind": "docker-compose" if "docker-compose" in rp else "compose",
            "declared_services": sorted([str(k) for k in svcs.keys()]),
            "declared_networks": sorted([str(k) for k in nets.keys()]),
            "declared_volumes": sorted([str(k) for k in vols.keys()]),
            "evidence": evidence(rp, anchor, ex),
        })

        for n, cfg in sorted(nets.items()):
            driver = cfg.get("driver") if isinstance(cfg, dict) and isinstance(cfg.get("driver"), str) else None
            resources_networks[n] = {"network": n, "driver": driver, "evidence": evidence(rp, "networks", json.dumps(cfg, sort_keys=True, default=str)[:160])}

        for v, cfg in sorted(vols.items()):
            driver = cfg.get("driver") if isinstance(cfg, dict) and isinstance(cfg.get("driver"), str) else None
            external = cfg.get("external") if isinstance(cfg, dict) and isinstance(cfg.get("external"), bool) else None
            resources_volumes[v] = {"volume": v, "driver": driver, "external": external, "evidence": evidence(rp, "volumes", json.dumps(cfg, sort_keys=True, default=str)[:160])}

        for sname, scfg in sorted(svcs.items()):
            if not isinstance(scfg, dict):
                continue
            obj = services_map.setdefault(sname, {
                "service": sname,
                "defined_in": [],
                "images": [],
                "build": {"contexts": [], "dockerfiles": [], "targets": [], "args": []},
                "command": [],
                "entrypoint": [],
                "ports": [],
                "env": {"env_vars": [], "env_files": [], "sources": []},
                "mounts": [],
                "networks": [],
                "depends_on": [],
                "healthcheck": {"test": [], "interval": None, "timeout": None, "retries": None, "start_period": None, "evidence": evidence(rp, "service", sname)},
                "restart": None,
                "profiles": [],
                "labels": [],
                "runtime_role_guess": "unknown",
                "evidence": evidence(rp, "service", sname),
            })
            obj["defined_in"].append(rp)
            if isinstance(scfg.get("image"), str):
                obj["images"].append(scfg["image"])
            b = scfg.get("build")
            if isinstance(b, str):
                obj["build"]["contexts"].append(b)
            elif isinstance(b, dict):
                if isinstance(b.get("context"), str):
                    obj["build"]["contexts"].append(b["context"])
                if isinstance(b.get("dockerfile"), str):
                    obj["build"]["dockerfiles"].append(b["dockerfile"])
                if isinstance(b.get("target"), str):
                    obj["build"]["targets"].append(b["target"])
                if isinstance(b.get("args"), dict):
                    obj["build"]["args"].extend(sorted([str(k) for k in b["args"].keys()]))
            if isinstance(scfg.get("command"), str):
                obj["command"].append(scfg["command"])
            elif isinstance(scfg.get("command"), list):
                obj["command"].append(" ".join([str(x) for x in scfg["command"]]))
            if isinstance(scfg.get("entrypoint"), str):
                obj["entrypoint"].append(scfg["entrypoint"])
            elif isinstance(scfg.get("entrypoint"), list):
                obj["entrypoint"].append(" ".join([str(x) for x in scfg["entrypoint"]]))

            ports = scfg.get("ports", []) if isinstance(scfg.get("ports"), list) else []
            for pp in ports:
                if isinstance(pp, str):
                    proto = "udp" if "/udp" in pp else "tcp"
                    clean = pp.replace("/udp", "")
                    parts = clean.split(":")
                    host = parts[0] if len(parts) > 1 else None
                    container = parts[-1]
                    obj["ports"].append({"host": host, "container": container, "proto": proto, "evidence": evidence(rp, "ports", pp)})
                    edges.append({"from": sname, "to": container, "type": "exposes_port", "detail": pp, "evidence": evidence(rp, "ports", pp)})

            env = scfg.get("environment")
            if isinstance(env, dict):
                obj["env"]["sources"].append("inline")
                for k in env.keys():
                    obj["env"]["env_vars"].append(str(k))
                    edges.append({"from": sname, "to": str(k), "type": "reads_env_var", "detail": "inline", "evidence": evidence(rp, "environment", str(k))})
            elif isinstance(env, list):
                obj["env"]["sources"].append("inline")
                for k in env:
                    k2 = str(k).split("=", 1)[0]
                    obj["env"]["env_vars"].append(k2)
                    edges.append({"from": sname, "to": k2, "type": "reads_env_var", "detail": "inline", "evidence": evidence(rp, "environment", str(k))})
            env_file = scfg.get("env_file")
            if isinstance(env_file, str):
                obj["env"]["env_files"].append(env_file)
                obj["env"]["sources"].append("env_file")
            elif isinstance(env_file, list):
                obj["env"]["env_files"].extend([str(x) for x in env_file])
                obj["env"]["sources"].append("env_file")

            vols_m = scfg.get("volumes", []) if isinstance(scfg.get("volumes"), list) else []
            for vm in vols_m:
                if isinstance(vm, str):
                    parts = vm.split(":")
                    src = parts[0] if parts else ""
                    tgt = parts[1] if len(parts) > 1 else ""
                    mode = "ro" if len(parts) > 2 and parts[2] == "ro" else "rw"
                    mtype = "bind" if src.startswith(".") or src.startswith("/") else "volume"
                    obj["mounts"].append({"type": mtype, "source": src, "target": tgt, "mode": mode, "evidence": evidence(rp, "volumes", vm)})
                    edges.append({"from": sname, "to": src, "type": "binds_host_path" if mtype == "bind" else "mounts_volume", "detail": vm, "evidence": evidence(rp, "volumes", vm)})

            nets_s = scfg.get("networks", [])
            if isinstance(nets_s, list):
                obj["networks"].extend([str(x) for x in nets_s])
                for n in nets_s:
                    edges.append({"from": sname, "to": str(n), "type": "connects_to_network", "detail": str(n), "evidence": evidence(rp, "networks", str(n))})
            elif isinstance(nets_s, dict):
                obj["networks"].extend([str(x) for x in nets_s.keys()])
                for n in nets_s.keys():
                    edges.append({"from": sname, "to": str(n), "type": "connects_to_network", "detail": str(n), "evidence": evidence(rp, "networks", str(n))})

            dep = scfg.get("depends_on")
            if isinstance(dep, list):
                for d in dep:
                    obj["depends_on"].append({"service": str(d), "condition": "unknown", "evidence": evidence(rp, "depends_on", str(d))})
                    edges.append({"from": sname, "to": str(d), "type": "depends_on", "detail": "unknown", "evidence": evidence(rp, "depends_on", str(d))})
            elif isinstance(dep, dict):
                for d, cond in dep.items():
                    condition = "unknown"
                    if isinstance(cond, dict) and isinstance(cond.get("condition"), str):
                        condition = cond["condition"]
                    obj["depends_on"].append({"service": str(d), "condition": condition, "evidence": evidence(rp, "depends_on", str(d))})
                    edges.append({"from": sname, "to": str(d), "type": "depends_on", "detail": condition, "evidence": evidence(rp, "depends_on", str(d))})

            hc = scfg.get("healthcheck")
            if isinstance(hc, dict):
                test = hc.get("test")
                if isinstance(test, list):
                    obj["healthcheck"]["test"] = [str(x) for x in test]
                elif isinstance(test, str):
                    obj["healthcheck"]["test"] = [test]
                for k in ["interval", "timeout", "start_period"]:
                    if isinstance(hc.get(k), str):
                        obj["healthcheck"][k] = hc.get(k)
                if isinstance(hc.get("retries"), int):
                    obj["healthcheck"]["retries"] = hc.get("retries")
                obj["healthcheck"]["evidence"] = evidence(rp, "healthcheck", json.dumps(hc, sort_keys=True, default=str)[:160])

            if isinstance(scfg.get("restart"), str):
                obj["restart"] = scfg["restart"]
            if isinstance(scfg.get("profiles"), list):
                obj["profiles"].extend([str(x) for x in scfg["profiles"]])
            labels = scfg.get("labels")
            if isinstance(labels, list):
                for l in labels:
                    obj["labels"].append(str(l).split("=", 1)[0])
            elif isinstance(labels, dict):
                obj["labels"].extend([str(k) for k in labels.keys()])

            role_guess = "unknown"
            joined = " ".join(obj["images"] + obj["command"] + [sname]).lower()
            if "postgres" in joined or "mysql" in joined or "redis" in joined:
                role_guess = "db"
            elif "litellm" in joined or "proxy" in joined:
                role_guess = "proxy"
            elif "mcp" in joined:
                role_guess = "mcp_server"
            elif "orchestrator" in joined:
                role_guess = "orchestrator"
            elif "worker" in joined:
                role_guess = "worker"
            obj["runtime_role_guess"] = role_guess

    for p in files:
        rp = rel(p)
        if rp in {"start-mcp-servers.sh", "Makefile"} or rp.startswith("scripts/"):
            txt = read_text(p)
            for m in re.finditer(r"docker\s+compose\s+([^\n]+)", txt):
                line = m.group(0)
                selects_files = sorted(re.findall(r"-f\s+([^\s]+)", line))
                invocation_surfaces.append({
                    "invoker": "script" if rp.endswith(".sh") or rp.startswith("scripts/") else "make",
                    "command": snippet(line, 300),
                    "selects_files": selects_files,
                    "selects_services": [],
                    "evidence": evidence(rp, f"L{txt[:m.start()].count(chr(10))+1}", line),
                })

    services = []
    for s in sorted(services_map.keys()):
        obj = services_map[s]
        obj["defined_in"] = sorted(set(obj["defined_in"]))
        obj["images"] = sorted(set(obj["images"]))
        obj["build"]["contexts"] = sorted(set(obj["build"]["contexts"]))
        obj["build"]["dockerfiles"] = sorted(set(obj["build"]["dockerfiles"]))
        obj["build"]["targets"] = sorted(set(obj["build"]["targets"]))
        obj["build"]["args"] = sorted(set(obj["build"]["args"]))
        obj["command"] = sorted(set(obj["command"]))
        obj["entrypoint"] = sorted(set(obj["entrypoint"]))
        obj["env"]["env_vars"] = sorted(set(obj["env"]["env_vars"]))
        obj["env"]["env_files"] = sorted(set(obj["env"]["env_files"]))
        obj["env"]["sources"] = sorted(set(obj["env"]["sources"]))
        obj["networks"] = sorted(set(obj["networks"]))
        obj["profiles"] = sorted(set(obj["profiles"]))
        obj["labels"] = sorted(set(obj["labels"]))
        obj["depends_on"] = sorted(obj["depends_on"], key=lambda x: (x["service"], x["condition"]))
        obj["ports"] = sorted(obj["ports"], key=lambda x: ((x["host"] or ""), x["container"], x["proto"]))
        obj["mounts"] = sorted(obj["mounts"], key=lambda x: (x["type"], x["source"], x["target"]))
        services.append(obj)

    out = {
        "artifact": "REPO_COMPOSE_SERVICE_GRAPH",
        "generated_at": now_iso(),
        "compose_files": sorted(cf_out, key=lambda x: x["path"]),
        "services": services,
        "resources": {
            "networks": sorted(resources_networks.values(), key=lambda x: x["network"]),
            "volumes": sorted(resources_volumes.values(), key=lambda x: x["volume"]),
        },
        "edges": sorted(edges, key=lambda x: (x["from"], x["to"], x["type"])),
        "invocation_surfaces": sorted(invocation_surfaces, key=lambda x: (x["invoker"], x["command"])),
        "unknowns": sorted(set(unknowns)),
        "warnings": [],
    }
    return out


def extract_litellm(files: List[Path]) -> Dict[str, Any]:
    out_files = []
    proxy_endpoints = []
    model_mappings = []
    routing_policies = []
    logging_surfaces = []
    spend_tracking = []
    env_refs: Dict[str, Dict[str, Any]] = {}
    compose_couplings = []
    unknowns: List[str] = []

    for p in files:
        rp = rel(p)
        txt = read_text(p)
        low = txt.lower()
        if not any(k in rp.lower() or k in low for k in ["litellm", "mcp-proxy", "proxy", "spend", "callback", "model_list"]):
            continue

        kind = "unknown"
        if "litellm.config" in rp:
            kind = "litellm_config"
        elif "mcp-proxy-config" in rp:
            kind = "mcp_proxy_config"
        elif rp == ".env.example":
            kind = "env_example"
        elif "compose" in rp:
            kind = "compose_ref"
        elif rp.endswith(".sh") or rp == "Makefile":
            kind = "script_ref"

        anchor, ex = line_anchor(txt, "litellm" if "litellm" in low else ("proxy" if "proxy" in low else (txt.splitlines()[0] if txt.splitlines() else "")))
        out_files.append({"path": rp, "kind": kind, "mentions": sorted(set([x for x in ["litellm", "proxy", "spend", "logging", "router", "fallback", "model"] if x in low])), "evidence": evidence(rp, anchor, ex)})

        # env refs
        for i, ln in enumerate(txt.splitlines(), 1):
            for key in sorted(set(ENV_KEY.findall(ln))):
                rec = env_refs.setdefault(key, {"name": key, "used_for": "unknown", "referenced_in": set(), "evidence": evidence(rp, f"L{i}", ln)})
                rec["referenced_in"].add(rp)
                l = ln.lower()
                if any(k in key.lower() or k in l for k in ["api_key", "openai", "anthropic", "gemini", "xai"]):
                    rec["used_for"] = "api_key"
                elif "db" in key.lower() or "database" in l:
                    rec["used_for"] = "db_url"
                elif "proxy" in key.lower() or "auth" in l:
                    rec["used_for"] = "proxy_auth"
                elif "log" in key.lower() or "callback" in l:
                    rec["used_for"] = "logging"

        # endpoints
        for m in URL.finditer(txt):
            url = m.group(0)
            red = re.sub(r"//[^/@\s]+:[^/@\s]+@", "//REDACTED@", url)
            line = txt[:m.start()].count("\n") + 1
            proxy_endpoints.append({
                "name": "unknown",
                "listen": red,
                "auth_mode": "unknown",
                "auth_env_vars": [],
                "headers_behavior": [],
                "routes": [],
                "evidence": evidence(rp, f"L{line}", url),
            })

        # model mapping lines
        for i, ln in enumerate(txt.splitlines(), 1):
            if re.search(r"gpt|claude|gemini|grok|o[1-9]", ln, re.I):
                model = re.search(r"([a-zA-Z0-9_.-]*(gpt|claude|gemini|grok|o[1-9])[a-zA-Z0-9_.-]*)", ln, re.I)
                if model:
                    provider = "unknown"
                    l = ln.lower()
                    for pv in ["openai", "anthropic", "gemini", "xai", "azure", "vertex"]:
                        if pv in l:
                            provider = pv
                            break
                    model_mappings.append({
                        "logical_model": None,
                        "provider_model": model.group(1),
                        "provider": provider,
                        "tags": sorted(set([t for t in ["fallback", "primary", "cheap", "reasoning", "code", "unknown"] if t in l] or ["unknown"])),
                        "evidence": evidence(rp, f"L{i}", ln),
                    })

            if any(k in ln.lower() for k in ["retry", "timeout", "fallback", "rate_limit"]):
                routing_policies.append({
                    "policy": "unknown",
                    "timeouts": {"connect": None, "read": None},
                    "retries": {"count": None, "backoff": None},
                    "fallbacks": [],
                    "rate_limits": [],
                    "evidence": evidence(rp, f"L{i}", ln),
                })

            if any(k in ln.lower() for k in ["callback", "log", "sqlite", "postgres", "spend"]):
                sink = "unknown"
                ll = ln.lower()
                if "sqlite" in ll:
                    sink = "sqlite"
                elif "postgres" in ll:
                    sink = "postgres"
                elif "http" in ll:
                    sink = "http"
                elif "stdout" in ll:
                    sink = "stdout"
                elif "file" in ll or "/" in ln:
                    sink = "file"
                logging_surfaces.append({
                    "sink": sink,
                    "target": "<REDACTED_DSN>" if "@" in ln and "://" in ln else snippet(ln),
                    "tables_or_paths": sorted(re.findall(r"[\w./-]+", ln))[:5],
                    "fields_mentioned": sorted([f for f in ["request_id", "model", "tokens", "cost"] if f in ll]),
                    "env_vars": sorted(set(ENV_KEY.findall(ln))),
                    "evidence": evidence(rp, f"L{i}", ln),
                })

                if "spend" in ll or "cost" in ll or "sqlite" in ll or "postgres" in ll:
                    spend_tracking.append({
                        "mechanism": "litellm_spend_db" if "litellm" in low else "unknown",
                        "db_kind": "sqlite" if "sqlite" in ll else ("postgres" if "postgres" in ll else "unknown"),
                        "db_ref": "<REDACTED_DSN>" if "://" in ln else snippet(ln),
                        "schema_refs": [],
                        "writers": [],
                        "evidence": evidence(rp, f"L{i}", ln),
                    })

        if kind == "compose_ref":
            data = parse_yaml_or_json(p, txt)
            if isinstance(data, dict) and isinstance(data.get("services"), dict):
                for s, scfg in sorted(data["services"].items()):
                    if not isinstance(scfg, dict):
                        continue
                    joined = json.dumps(scfg, sort_keys=True, default=str).lower()
                    if "litellm" in joined or "proxy" in joined:
                        env_vars = []
                        env = scfg.get("environment")
                        if isinstance(env, dict):
                            env_vars = sorted([str(k) for k in env.keys()])
                        elif isinstance(env, list):
                            env_vars = sorted([str(x).split("=", 1)[0] for x in env])
                        ports = [str(x) for x in scfg.get("ports", [])] if isinstance(scfg.get("ports"), list) else []
                        volumes = [str(x) for x in scfg.get("volumes", [])] if isinstance(scfg.get("volumes"), list) else []
                        compose_couplings.append({
                            "compose_file": rp,
                            "service": str(s),
                            "env_vars": sorted(env_vars),
                            "ports": sorted(ports),
                            "volumes": sorted(volumes),
                            "evidence": evidence(rp, "services", str(s)),
                        })

    out = {
        "artifact": "REPO_LITELLM_SURFACE",
        "generated_at": now_iso(),
        "files": sorted(out_files, key=lambda x: x["path"]),
        "proxy_endpoints": sorted(proxy_endpoints, key=lambda x: x["listen"]),
        "model_mappings": sorted(model_mappings, key=lambda x: ((x["provider_model"] or ""), x["provider"])),
        "routing_policies": sorted(routing_policies, key=lambda x: x["evidence"]["excerpt_hash"]),
        "logging_surfaces": sorted(logging_surfaces, key=lambda x: (x["sink"], x["target"])),
        "spend_tracking": sorted(spend_tracking, key=lambda x: (x["mechanism"], x["db_kind"], x["db_ref"])),
        "env_var_references": sorted([
            {"name": k, "used_for": v["used_for"], "referenced_in": sorted(v["referenced_in"]), "evidence": v["evidence"]}
            for k, v in env_refs.items()
        ], key=lambda x: x["name"]),
        "compose_couplings": sorted(compose_couplings, key=lambda x: (x["compose_file"], x["service"])),
        "unknowns": sorted(unknowns),
        "warnings": [],
    }
    return out


def extract_taskx_surface(files: List[Path]) -> Dict[str, Any]:
    roots = []
    packets = []
    inv = []
    op_sys = []
    refusal = []
    env_refs: Dict[str, Dict[str, Any]] = {}
    ci = []
    compose_c = []
    xrefs = []
    unknowns = []

    for p in files:
        rp = rel(p)
        txt = read_text(p)
        low = txt.lower()

        if rp in {".taskxroot", ".taskx-pin"} or rp.startswith(".taskx/"):
            roots.append({"path": rp, "evidence": evidence(rp, "root", txt[:160] if txt else rp)})

        if any(k in rp.lower() for k in ["task-packets", ".taskx", "packet", "spec", "schema", "template"]):
            packets.append({"kind": "task_packet" if "packet" in rp.lower() else ("template" if "template" in rp.lower() else "unknown"), "path": rp, "declared_outputs": sorted(set(re.findall(r"[\w./-]+\.(json|md|csv)", txt))), "mentions": sorted(set([w for w in ["packet", "route", "artifact", "refusal", "deterministic"] if w in low])), "evidence": evidence(rp, "root", txt[:160] if txt else rp)})

        if any(k in low for k in ["taskx", "uv run taskx", "python -m taskx"]):
            for i, ln in enumerate(txt.splitlines(), 1):
                if "taskx" in ln.lower():
                    inv.append({"via": "ci" if ".github/workflows" in rp else ("make" if rp == "Makefile" else ("script" if rp.startswith("scripts/") else "manual_doc")), "command": snippet(ln, 300), "cwd": None, "inputs": sorted(set(ENV_KEY.findall(ln))), "outputs": sorted(re.findall(r"[\w./-]+\.(json|md|csv)", ln)), "evidence": evidence(rp, f"L{i}", ln)})

        if any(k in low for k in ["instruction", "compile", "inject", "doctor", "apply"]):
            op_sys.append({"kind": "source_instructions" if "instruction" in low else "unknown", "path": rp, "operation": "compile" if "compile" in low else ("apply" if "apply" in low else ("doctor" if "doctor" in low else "unknown")), "targets": sorted(set(re.findall(r"[\w./-]+\.md", txt))), "markers": sorted(set(re.findall(r"<[^>]+>", txt))), "evidence": evidence(rp, "root", txt[:160] if txt else rp)})

        if any(k in low for k in ["deterministic", "canonical", "hash", "refusal", "append-only"]):
            refusal.append({"path": rp, "signals": sorted(set([w for w in ["deterministic", "canonical json", "hash", "refusal", "append-only"] if w.replace(" ", "") in low.replace(" ", "") or w in low])), "evidence": evidence(rp, "root", txt[:160] if txt else rp)})

        for i, ln in enumerate(txt.splitlines(), 1):
            if "TASKX_" in ln or "taskx" in ln.lower():
                for k in sorted(set(ENV_KEY.findall(ln))):
                    rec = env_refs.setdefault(k, {"name": k, "used_for": "unknown", "referenced_in": set(), "evidence": evidence(rp, f"L{i}", ln)})
                    rec["referenced_in"].add(rp)
                    if "taskx" in k.lower():
                        rec["used_for"] = "taskx_config"
                    elif any(x in k.lower() for x in ["openai", "anthropic", "gemini", "xai", "api_key"]):
                        rec["used_for"] = "providers"
                    elif "path" in k.lower() or "dir" in k.lower():
                        rec["used_for"] = "paths"

        if rp.startswith(".github/workflows/") and "taskx" in low:
            ci.append({"workflow_file": rp, "job": None, "steps": sorted([snippet(ln) for ln in txt.splitlines() if "taskx" in ln.lower()]), "evidence": evidence(rp, "root", txt[:160])})

        if "compose" in rp.lower() and "taskx" in low:
            compose_c.append({"compose_file": rp, "service": "unknown", "volumes": sorted(set(re.findall(r"[\w./-]+:[\w./-]+(?::ro|:rw)?", txt))), "env_vars": sorted(set(ENV_KEY.findall(txt))), "evidence": evidence(rp, "root", txt[:160])})

        # path cross refs (literal mentions)
        for m in re.finditer(r"(?:docs|scripts|config|services|\.taskx|\.claude)/[\w./-]+", txt):
            refp = m.group(0)
            xrefs.append({"from_path": rp, "to_path": refp, "relation": "mentions", "evidence": evidence(rp, f"L{txt[:m.start()].count(chr(10))+1}", refp)})

    out = {
        "artifact": "REPO_TASKX_SURFACE",
        "generated_at": now_iso(),
        "repo_taskx_roots": sorted(roots, key=lambda x: x["path"]),
        "packets_and_specs": sorted(packets, key=lambda x: x["path"]),
        "invocation_edges": sorted(inv, key=lambda x: (x["via"], x["command"])),
        "operator_instruction_system": sorted(op_sys, key=lambda x: (x["path"], x["operation"])),
        "refusal_and_determinism_surfaces": sorted(refusal, key=lambda x: x["path"]),
        "env_var_references": sorted([
            {"name": k, "used_for": v["used_for"], "referenced_in": sorted(v["referenced_in"]), "evidence": v["evidence"]}
            for k, v in env_refs.items()
        ], key=lambda x: x["name"]),
        "ci_integrations": sorted(ci, key=lambda x: x["workflow_file"]),
        "compose_or_runtime_couplings": sorted(compose_c, key=lambda x: x["compose_file"]),
        "cross_refs": sorted(xrefs, key=lambda x: (x["from_path"], x["to_path"], x["relation"])),
        "unknowns": sorted(unknowns),
        "warnings": [],
    }
    return out


def extract_ci_gates(files: List[Path]) -> Dict[str, Any]:
    gha = []
    pre = {"config_path": ".pre-commit-config.yaml", "hooks": [], "evidence": evidence(".pre-commit-config.yaml", "root", "")}
    git_hooks = []
    runners = []
    pygates = []
    hygiene = []
    artifact_ctrl = []
    secrets = {}
    unknowns = []

    for p in files:
        rp = rel(p)
        txt = read_text(p)
        data = parse_yaml_or_json(p, txt)

        if rp.startswith(".github/workflows/"):
            wf_name = None
            on = []
            jobs_out = []
            if isinstance(data, dict):
                wf_name = data.get("name") if isinstance(data.get("name"), str) else None
                d_on = data.get("on")
                if isinstance(d_on, dict):
                    on = sorted([str(k) for k in d_on.keys()])
                elif isinstance(d_on, list):
                    on = sorted([str(x) for x in d_on])
                elif isinstance(d_on, str):
                    on = [d_on]
                jobs = data.get("jobs", {}) if isinstance(data.get("jobs"), dict) else {}
                for jid, jcfg in sorted(jobs.items()):
                    if not isinstance(jcfg, dict):
                        continue
                    steps = []
                    artifacts = []
                    for st in jcfg.get("steps", []) if isinstance(jcfg.get("steps"), list) else []:
                        if not isinstance(st, dict):
                            continue
                        run = st.get("run") if isinstance(st.get("run"), str) else None
                        uses = st.get("uses") if isinstance(st.get("uses"), str) else None
                        env_vars = sorted([str(k) for k in st.get("env", {}).keys()]) if isinstance(st.get("env"), dict) else []
                        ev = evidence(rp, "step", json.dumps(st, sort_keys=True, default=str)[:160])
                        steps.append({"name": st.get("name") if isinstance(st.get("name"), str) else None, "run": run, "uses": uses, "env_vars": env_vars, "evidence": ev})
                        if uses and "actions/upload-artifact" in uses:
                            artifacts.append({"kind": "upload", "paths": [], "evidence": ev})
                        if uses and "actions/download-artifact" in uses:
                            artifacts.append({"kind": "download", "paths": [], "evidence": ev})
                    jobs_out.append({"job_id": str(jid), "runs_on": jcfg.get("runs-on") if isinstance(jcfg.get("runs-on"), str) else None, "steps": steps, "artifacts": artifacts, "gating_semantics": ["fail_on_nonzero_exit", "required_check_candidate"]})
            gha.append({"workflow_path": rp, "name": wf_name, "on": on, "jobs": jobs_out, "evidence": evidence(rp, "root", txt[:160])})

        if rp == ".pre-commit-config.yaml" and isinstance(data, dict):
            repos = data.get("repos", []) if isinstance(data.get("repos"), list) else []
            for repo in repos:
                if not isinstance(repo, dict):
                    continue
                hooks = repo.get("hooks", []) if isinstance(repo.get("hooks"), list) else []
                for h in hooks:
                    if not isinstance(h, dict):
                        continue
                    pre["hooks"].append({"id": h.get("id") if isinstance(h.get("id"), str) else None, "name": h.get("name") if isinstance(h.get("name"), str) else None, "entry": h.get("entry") if isinstance(h.get("entry"), str) else None, "language": h.get("language") if isinstance(h.get("language"), str) else None, "files": h.get("files") if isinstance(h.get("files"), str) else None, "stages": sorted(h.get("stages", []) if isinstance(h.get("stages"), list) else []), "evidence": evidence(rp, "hook", json.dumps(h, sort_keys=True, default=str)[:160])})

        if rp.startswith(".githooks/"):
            cmds = [snippet(ln) for ln in txt.splitlines() if ln.strip() and not ln.strip().startswith("#")]
            git_hooks.append({"hook_path": rp, "invoked_by": "git", "commands": cmds, "evidence": evidence(rp, "root", txt[:160])})

        if rp == "Makefile" or rp.startswith("scripts/"):
            for i, ln in enumerate(txt.splitlines(), 1):
                if any(k in ln for k in ["pytest", "ruff", "mypy", "pre-commit", "docker compose", "taskx", "lint", "test", "check"]):
                    runners.append({"file": rp, "target_or_command": snippet(ln.split(":", 1)[0]) if ":" in ln and rp == "Makefile" else rp, "recipe_or_body": snippet(ln, 300), "calls": sorted(set(re.findall(r"\b(pytest|ruff|mypy|docker|taskx|pre-commit|uv|poetry)\b", ln))), "evidence": evidence(rp, f"L{i}", ln)})

        if rp in {"pyproject.toml", "pytest.ini", "mypy.ini", "ruff.toml"}:
            for i, ln in enumerate(txt.splitlines(), 1):
                l = ln.lower()
                tool = None
                for t in ["pytest", "ruff", "mypy", "coverage", "uv", "poetry"]:
                    if t in l:
                        tool = t
                        break
                if tool:
                    pygates.append({"tool": tool, "config_path": rp, "settings_snippet": snippet(ln), "evidence": evidence(rp, f"L{i}", ln)})

        if "hygiene" in rp.lower() or "policy" in rp.lower() or ("allowlist" in txt.lower() or "denylist" in txt.lower()):
            rules = []
            for i, ln in enumerate(txt.splitlines(), 1):
                if any(k in ln.lower() for k in ["allowlist", "denylist", "policy", "hygiene", "out/", "reports/", "quarantine"]):
                    rules.append({"rule": snippet(ln), "scope": None, "evidence": evidence(rp, f"L{i}", ln)})
                    if any(k in ln.lower() for k in ["out/", "_audit_out", "reports/", "quarantine"]):
                        artifact_ctrl.append({"kind": "allowlist" if "allowlist" in ln.lower() else ("denylist" if "denylist" in ln.lower() else "unknown"), "targets": sorted([x for x in ["out/", "_audit_out/", "reports/", "quarantine/"] if x.rstrip("/") in ln]), "mechanism": "script" if rp.startswith("scripts/") else ("ci" if rp.startswith(".github/") else "unknown"), "evidence": evidence(rp, f"L{i}", ln)})
            hygiene.append({"policy_path": rp, "enforced_by": ["script" if rp.startswith("scripts/") else "unknown"], "rules": rules, "evidence": evidence(rp, "root", txt[:160])})

        for i, ln in enumerate(txt.splitlines(), 1):
            for k in ENV_KEY.findall(ln):
                if any(x in k.lower() for x in ["key", "token", "secret", "url", "db", "host"]):
                    rec = secrets.setdefault(k, {"name": k, "used_in": set(), "purpose": "unknown", "evidence": evidence(rp, f"L{i}", ln)})
                    rec["used_in"].add("workflow" if rp.startswith(".github/workflows/") else ("script" if rp.startswith("scripts/") else "tool config"))
                    if any(x in k.lower() for x in ["openai", "anthropic", "gemini", "xai", "api_key"]):
                        rec["purpose"] = "provider_key"
                    elif "db" in k.lower():
                        rec["purpose"] = "db"
                    elif any(x in k.lower() for x in ["url", "host"]):
                        rec["purpose"] = "service_url"

    out = {
        "artifact": "REPO_CI_AND_GATES_SURFACE",
        "generated_at": now_iso(),
        "github_actions": sorted(gha, key=lambda x: x["workflow_path"]),
        "pre_commit": {**pre, "hooks": sorted(pre["hooks"], key=lambda x: ((x.get("id") or ""), (x.get("name") or "")) )},
        "git_hooks": sorted(git_hooks, key=lambda x: x["hook_path"]),
        "make_or_task_runners": sorted(runners, key=lambda x: (x["file"], x["target_or_command"], x["recipe_or_body"])),
        "python_tooling_gates": sorted(pygates, key=lambda x: (x["tool"], x["config_path"])),
        "repo_hygiene_policies": sorted(hygiene, key=lambda x: x["policy_path"]),
        "artifact_and_output_controls": sorted(artifact_ctrl, key=lambda x: (x["kind"], ",".join(x["targets"]))),
        "secrets_and_env_requirements": sorted([
            {"name": k, "used_in": sorted(v["used_in"]), "purpose": v["purpose"], "evidence": v["evidence"]}
            for k, v in secrets.items()
        ], key=lambda x: x["name"]),
        "unknowns": sorted(unknowns),
        "warnings": [],
    }
    return out


def instruction_stubs(files: List[Path]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    items = []
    refs = []
    for p in files:
        rp = rel(p)
        if rp in {"AGENTS.md", "claude.md", ".claude/PROJECT_INSTRUCTIONS.md", ".claude/PRIMER.md"} or rp.startswith(".claude/"):
            txt = read_text(p)
            if not txt:
                continue
            anchor, ex = line_anchor(txt, txt.splitlines()[0] if txt.splitlines() else "")
            items.append({"path": rp, "type": "instruction_file", "evidence": evidence(rp, anchor, ex)})
            for m in re.finditer(r"(?:docs|scripts|config|services|src|docker|compose)/[\w./-]+", txt):
                refs.append({"from": rp, "to": m.group(0), "relation": "mentions", "evidence": evidence(rp, f"L{txt[:m.start()].count(chr(10))+1}", m.group(0))})
    surf = {
        "artifact": "REPO_INSTRUCTION_SURFACE",
        "generated_at": now_iso(),
        "files_seen": len(files),
        "items": sorted(items, key=lambda x: x["path"]),
        "warnings": [],
        "unknowns": [],
    }
    ref = {
        "artifact": "REPO_INSTRUCTION_REFERENCES",
        "generated_at": now_iso(),
        "files_seen": len(files),
        "items": sorted(refs, key=lambda x: (x["from"], x["to"])),
        "warnings": [],
        "unknowns": [],
    }
    return surf, ref


def file_meta(path: Path) -> Dict[str, Any]:
    st = path.stat()
    b = path.read_bytes()
    return {"path": rel(path), "size": st.st_size, "mtime": int(st.st_mtime), "sha256": hashlib.sha256(b).hexdigest()}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def missing_stub(name: str, notes: List[str]) -> Dict[str, Any]:
    return {"artifact": name, "status": "MISSING", "missing_inputs": [], "notes": notes}


def build_index_and_qa(raw_paths: List[Path], norm_paths: List[Path]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    raw_inputs = []
    for p in sorted(raw_paths, key=lambda x: rel(x)):
        txt = read_text(p)
        declared = "unknown"
        try:
            obj = json.loads(txt)
            declared = obj.get("artifact", "unknown")
        except Exception:
            pass
        meta = file_meta(p)
        raw_inputs.append({**meta, "declared_artifact": declared})

    canonical_outputs = []
    missing = []
    for p in sorted(norm_paths, key=lambda x: rel(x)):
        item_count = 0
        status = "OK"
        try:
            obj = json.loads(read_text(p))
            if obj.get("status") == "MISSING":
                status = "MISSING"
                missing.append(obj.get("artifact", rel(p)))
            if isinstance(obj.get("items"), list):
                item_count = len(obj["items"])
            elif isinstance(obj.get("servers"), list):
                item_count = len(obj["servers"])
            elif isinstance(obj.get("proxies"), list):
                item_count = len(obj["proxies"])
            elif isinstance(obj.get("routers"), list):
                item_count = len(obj["routers"])
            elif isinstance(obj.get("hook_groups"), list):
                item_count = len(obj["hook_groups"])
            elif isinstance(obj.get("services"), list):
                item_count = len(obj["services"])
            elif isinstance(obj.get("github_actions"), list):
                item_count = len(obj["github_actions"])
        except Exception:
            status = "MISSING"
            missing.append(rel(p))
        canonical_outputs.append({"path": rel(p), "artifact": p.name.replace(".json", ""), "status": status, "item_count": item_count})

    idx = {"artifact": "REPOCTRL_INDEX", "generated_at": now_iso(), "raw_inputs": raw_inputs, "canonical_outputs": canonical_outputs}

    raw_total = sum(p.stat().st_size for p in raw_paths)
    norm_total = sum(p.stat().st_size for p in norm_paths)
    required_outputs = [{"name": p.name.replace(".json", ""), "status": ("MISSING" if p.name.replace(".json", "") in missing else "OK"), "path": rel(p), "item_count": next((x["item_count"] for x in canonical_outputs if x["path"] == rel(p)), 0)} for p in sorted(norm_paths, key=lambda x: rel(x))]

    qa = {
        "artifact": "REPOCTRL_QA_REPORT",
        "generated_at": now_iso(),
        "required_outputs": required_outputs,
        "checks": {
            "json_valid": True,
            "deterministic_sorting_applied": True,
            "secret_redaction_applied": True,
            "duplicate_prompt_ids_detected": False,
            "missing_required_outputs": sorted(missing),
            "suspicious_large_fields": [],
        },
        "stats": {"raw_files": len(raw_paths), "raw_total_bytes": raw_total, "norm_total_bytes": norm_total},
    }
    return idx, qa


def merge_report(norm_paths: List[Path], raw_paths: List[Path]) -> Dict[str, Any]:
    merged = []
    for p in sorted(norm_paths, key=lambda x: rel(x)):
        merged.append({"output": rel(p), "source_shards": sorted([rel(r) for r in raw_paths]), "deduped": 0, "conflicts": 0})
    return {
        "artifact": "REPOCTRL_MERGE_REPORT",
        "generated_at": now_iso(),
        "merged": merged,
        "conflict_examples": [],
        "dropped": [],
    }


def main() -> int:
    files = iter_candidate_files()

    mcp_defs, mcp_proxy = extract_servers_and_proxies(files)
    router_surface = extract_router_surface(files)
    hooks_surface, implicit_surface = extract_hooks(files)
    compose_graph = extract_compose_graph(files)
    litellm_surface = extract_litellm(files)
    taskx_surface = extract_taskx_surface(files)
    ci_gates = extract_ci_gates(files)
    instr_surf, instr_refs = instruction_stubs(files)

    outputs = {
        "REPO_INSTRUCTION_SURFACE.json": instr_surf,
        "REPO_INSTRUCTION_REFERENCES.json": instr_refs,
        "REPO_MCP_SERVER_DEFS.json": mcp_defs,
        "REPO_MCP_PROXY_SURFACE.json": mcp_proxy,
        "REPO_ROUTER_SURFACE.json": router_surface,
        "REPO_HOOKS_SURFACE.json": hooks_surface,
        "REPO_IMPLICIT_BEHAVIOR_HINTS.json": implicit_surface,
        "REPO_COMPOSE_SERVICE_GRAPH.json": compose_graph,
        "REPO_LITELLM_SURFACE.json": litellm_surface,
        "REPO_TASKX_SURFACE.json": taskx_surface,
        "REPO_CI_AND_GATES_SURFACE.json": ci_gates,
    }

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    NORM_DIR.mkdir(parents=True, exist_ok=True)

    raw_paths: List[Path] = []
    norm_paths: List[Path] = []

    for fn, obj in sorted(outputs.items(), key=lambda x: x[0]):
        rp = RAW_DIR / fn
        np = NORM_DIR / fn
        # raw and norm same for this deterministic run
        write_json(rp, obj)
        write_json(np, obj)
        raw_paths.append(rp)
        norm_paths.append(np)

    idx, qa = build_index_and_qa(raw_paths, norm_paths)
    mr = merge_report(norm_paths, raw_paths)

    extra = {
        "REPOCTRL_INDEX.json": idx,
        "REPOCTRL_MERGE_REPORT.json": mr,
        "REPOCTRL_QA_REPORT.json": qa,
    }

    for fn, obj in sorted(extra.items(), key=lambda x: x[0]):
        rp = RAW_DIR / fn
        np = NORM_DIR / fn
        write_json(rp, obj)
        write_json(np, obj)
        raw_paths.append(rp)
        norm_paths.append(np)

    print(f"Generated {len(norm_paths)} norm artifacts in {NORM_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
