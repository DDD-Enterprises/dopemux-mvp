"""Fixtures for the W03 auth tests: temp HOME and a stubbed ``security`` binary.

Nothing here touches the real keychain or the real ~/.config. The stub keeps its
fake keychain and its argv log OUTSIDE the temp HOME so that "no token in any
file under HOME" is a meaningful assertion.
"""

from __future__ import annotations

import json
import os
import stat
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

import pytest

STUB_SOURCE = textwrap.dedent(
    '''\
    #!{python}
    import json, os, shlex, sys, time

    STORE = os.environ["FAKE_SECURITY_STORE"]
    LOG = os.environ["FAKE_SECURITY_LOG"]
    MODE = os.environ.get("FAKE_SECURITY_MODE", "ok")


    def load():
        try:
            with open(STORE, encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            return {{}}


    def save(data):
        with open(STORE, "w", encoding="utf-8") as fh:
            json.dump(data, fh)


    def opt(args, flag):
        return args[args.index(flag) + 1]


    def run(args):
        verb = args[0]
        data = load()
        key = opt(args, "-s") + "|" + opt(args, "-a")
        if verb == "find-generic-password":
            if MODE == "locked":
                sys.exit(36)
            if MODE == "hang":
                time.sleep(30)
            if MODE == "empty":
                print("")
                return
            if key not in data:
                sys.exit(44)
            print(data[key])
        elif verb == "add-generic-password":
            if MODE == "write_fail":
                sys.exit(1)
            data[key] = opt(args, "-w")
            save(data)
        elif verb == "delete-generic-password":
            if key not in data:
                sys.exit(44)
            del data[key]
            save(data)
        else:
            sys.exit(2)


    argv = sys.argv[1:]
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({{"argv": argv}}) + "\\n")
    if argv == ["-i"]:
        for line in sys.stdin.read().splitlines():
            line = line.strip()
            if line:
                run(shlex.split(line))
    else:
        if argv and argv[0] == "find-generic-password":
            stdin_text = sys.stdin.read()
            with open(LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({{"stdin_len": len(stdin_text)}}) + "\\n")
        run(argv)
    '''
)


@dataclass
class Env:
    home: Path
    store: Path
    log: Path
    monkeypatch: pytest.MonkeyPatch

    @property
    def auth_dir(self) -> Path:
        return self.home / ".config" / "dopemux" / "auth"

    @property
    def hash_file(self) -> Path:
        return self.auth_dir / "memory-token-hashes.json"

    def keychain(self) -> dict:
        if not self.store.exists():
            return {}
        return json.loads(self.store.read_text(encoding="utf-8"))

    def keychain_token(self, principal: str) -> str:
        return self.keychain()[f"dopemux-mcp|{principal}"]

    def set_keychain_token(self, principal: str, token: str) -> None:
        data = self.keychain()
        data[f"dopemux-mcp|{principal}"] = token
        self.store.write_text(json.dumps(data), encoding="utf-8")

    def argv_calls(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        out = []
        for line in self.log.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if "argv" in row:
                out.append(row["argv"])
        return out

    def stdin_lens(self) -> list[int]:
        if not self.log.exists():
            return []
        return [
            json.loads(line)["stdin_len"]
            for line in self.log.read_text(encoding="utf-8").splitlines()
            if "stdin_len" in json.loads(line)
        ]

    def set_mode(self, mode: str) -> None:
        self.monkeypatch.setenv("FAKE_SECURITY_MODE", mode)

    def home_files_text(self) -> str:
        chunks = []
        for path in self.home.rglob("*"):
            if path.is_file():
                chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        return "\n".join(chunks)


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Env:
    home = tmp_path / "home"
    home.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    stub = outside / "security"
    stub.write_text(STUB_SOURCE.format(python=sys.executable), encoding="utf-8")
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    store = outside / "store.json"
    log = outside / "argv.log"

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("FAKE_SECURITY_STORE", str(store))
    monkeypatch.setenv("FAKE_SECURITY_LOG", str(log))
    monkeypatch.delenv("FAKE_SECURITY_MODE", raising=False)
    for name in ("DOPE_MEMORY_AUTH_DIR", "CONPORT_AUTH_DIR"):
        monkeypatch.delenv(name, raising=False)

    from dopemux.auth import keychain

    monkeypatch.setattr(keychain, "SECURITY_BIN", str(stub))
    monkeypatch.setattr(keychain, "TIMEOUT_SECONDS", 1.0)
    return Env(home=home, store=store, log=log, monkeypatch=monkeypatch)
