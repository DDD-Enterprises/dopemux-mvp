"""Offline scope, parity, packaging, workflow and proof pre-freeze checks.

Run from repository root with its test dependencies. Does not invoke models,
network, hooks or workflow commands. Historical stop receipts stay immutable.
"""
from __future__ import annotations

import copy
import fnmatch
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib

import jsonschema
import yaml

PACKET = "TP-DMX-CI-AUDIT-EVIDENCE-GATE-001-A5-R3-PROVENANCE-CLOSURE-001"
START = "13562c8df1bc6621229eb4a38473da42be199825"


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-c", "core.fsmonitor=false", *args], text=True
    )


def main() -> None:
    packet_path = Path("task-packets") / f"{PACKET}.json"
    packet = json.loads(packet_path.read_text())
    schema = json.loads(Path(
        "docs/03-reference/spec/dopetask/dopetask-canonical-spec.json"
    ).read_text())
    jsonschema.Draft7Validator(schema).validate(packet)
    allowlist = packet["commit"]["allowlist"]
    changed = git("diff", "--name-only", START, "--").splitlines()
    assert all(any(fnmatch.fnmatchcase(p, a) for a in allowlist) for p in changed)
    git("diff", "--check", START, "--")

    parity = {}
    for module in ("steward_gate.py", "queue_drain.py"):
        paths = [Path("src/dopemux_pr_merge_specialist") / module]
        paths.extend(Path(prefix) / "dopemux_pr_merge_specialist" / module for prefix in (
            "templates/skills/pr-merge-specialist/scripts",
            ".claude/skills/pr-merge-specialist/scripts",
            ".github/skills/pr-merge-specialist/scripts",
        ))
        hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        assert len(set(hashes.values())) == 1, hashes
        parity[module] = hashes

    original = tomllib.loads(git("show", f"{START}:pyproject.toml"))
    expected = copy.deepcopy(original)
    packages = expected["tool"]["setuptools"]["packages"]
    packages.insert(packages.index("dopemux.core_logging") + 1, "dopemux.dcp")
    assert expected == tomllib.loads(Path("pyproject.toml").read_text())

    allowed_steps = {
        ".github/workflows/embedded-audit.yml": "Enforce audit evidence gate",
        ".github/workflows/pr-steward.yml": "Select and download independent audit artifact",
    }
    workflow_results = {}
    for path, step_name in allowed_steps.items():
        before = yaml.load(git("show", f"{START}:{path}"), Loader=yaml.BaseLoader)
        after = yaml.load(Path(path).read_text(), Loader=yaml.BaseLoader)
        normalized = copy.deepcopy(after)
        modifications = 0
        for job_id, job in before["jobs"].items():
            old_steps = job["steps"]
            new_steps = normalized["jobs"][job_id]["steps"]
            assert len(old_steps) == len(new_steps)
            for old, new in zip(old_steps, new_steps):
                if old == new:
                    continue
                assert old.get("name") == new.get("name") == step_name
                for key in set(old) | set(new):
                    if key not in {"run", "env"}:
                        assert old.get(key) == new.get(key), (path, key)
                old_env = old.get("env", {})
                new_env = dict(new.get("env", {}))
                new_env.pop("EXPECTED_BASE_SHA", None)
                assert new_env == old_env
                subprocess.run(["bash", "-n"], input=new["run"], text=True, check=True)
                new.clear()
                new.update(old)
                modifications += 1
        assert normalized == before, path
        assert modifications == 1, (path, modifications)
        workflow_results[path] = "Only authorized step run/expected-base env changed; bash syntax PASS"

    proof_dir = Path("proof") / PACKET
    proof_json = sorted(proof_dir.rglob("*.json"))
    for path in proof_json:
        json.loads(path.read_text())
    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    excluded = [p for p in untracked if not any(fnmatch.fnmatchcase(p, a) for a in allowlist)]
    assert all(p.startswith("proof/pr_merge/run_") and Path(p).name in {
        "PREFLIGHT_RESULT.json", "RUN_MANIFEST.json"
    } for p in excluded), excluded
    print(json.dumps({
        "status": "PASS",
        "start_head": START,
        "observed_head": git("rev-parse", "HEAD").strip(),
        "scope": changed,
        "parity_sha256": parity,
        "packaging_only_existing_dcp_declaration": "PASS",
        "workflow_static_scope": workflow_results,
        "workflow_trigger_change": False,
        "workflow_permission_change": False,
        "packet_schema": "PASS",
        "proof_json_parse_count": len(proof_json),
        "excluded_untracked_preserved_not_for_export": excluded,
        "audit": "NOT_RUN",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
