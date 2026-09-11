"""W01 common A/D Codex isolation profile -> argv derivation.

Route A and Route D both import this one module and derive their child argv
segment from the one frozen profile file, so A_D_CONFIG_BYTES_IDENTICAL is
mechanically guaranteed by construction rather than asserted by inspection.
"""
import hashlib
import json
from pathlib import Path

PROFILE_PATH = Path(__file__).resolve().parent / 'W01_COMMON_CODEX_ISOLATION_PROFILE.json'


def load_profile(path=None):
    return json.loads(Path(path or PROFILE_PATH).read_text())


def profile_sha256(path=None):
    return hashlib.sha256(Path(path or PROFILE_PATH).read_bytes()).hexdigest()


def isolation_argv(profile):
    """Deterministic argv segment: frozen flag order, then -c overrides sorted
    by key with compact canonical JSON values."""
    args = list(profile['cli_flags'])
    overrides = profile['config_overrides']
    for key in sorted(overrides):
        args += ['-c', key + '=' + json.dumps(overrides[key], separators=(',', ':'), sort_keys=True)]
    return args


def argv_sha256(profile):
    blob = '\0'.join(isolation_argv(profile)).encode()
    return hashlib.sha256(blob).hexdigest()


def assert_repository_cwd_forbidden(cwd, repo_root='/Users/hue/code/dopemux-mvp'):
    """REPOSITORY_CWD_FORBIDDEN: the child must not run inside the repository."""
    cwd = Path(cwd).resolve()
    repo = Path(repo_root).resolve()
    if cwd == repo or repo in cwd.parents:
        raise RuntimeError('REPOSITORY_CWD_FORBIDDEN')
    return str(cwd)
