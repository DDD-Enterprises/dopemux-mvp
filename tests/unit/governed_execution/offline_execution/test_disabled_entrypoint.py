"""No product/source enrollment or executable activation from the staged module."""
from pathlib import Path
import importlib.util
import os
import sqlite3
import subprocess


def load_disabled(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('DISABLED_ENTRYPOINT_EFFECT')
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setattr(sqlite3, 'connect', forbidden)
    monkeypatch.setattr(Path, 'mkdir', forbidden)
    original_open = os.open
    def read_only(path, flags, *args, **kwargs):
        assert not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT)
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(os, 'open', read_only)
    source = Path(__file__).resolve().parents[4]/'src/dopemux/governed_execution/offline_execution/disabled_entrypoint.py'
    spec = importlib.util.spec_from_file_location('_strict_disabled_staging', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_import_is_inert(monkeypatch):
    module = load_disabled(monkeypatch)
    assert module.status()['state'] == 'DISABLED'


def test_status_ignores_ambient_enable(monkeypatch):
    monkeypatch.setenv('GOVERNANCE_ENABLED', '1')
    monkeypatch.setenv('GOV_OFFLINE_ENABLE', 'true')
    module = load_disabled(monkeypatch)
    assert module.status() == {'state': 'DISABLED', 'dispatch': 'HELD',
        'scope': 'PRIVATE_STAGING_ONLY', 'activation': 'NOT_AUTHORIZED'}


def test_help_is_inert(monkeypatch, capsys):
    module = load_disabled(monkeypatch)
    assert module.main(['--help']) == 0
    assert 'DISABLED' in capsys.readouterr().out


def test_dispatch_always_held(monkeypatch):
    module = load_disabled(monkeypatch)
    assert module.dispatch(enabled=True, grant=object(), callback=object()) == {
        'status': 'HELD', 'reason': 'DISABLED', 'fixture': False}


# Package-resolution tests exercise only the disabled integration. Root conftest
# imports the pre-existing dopemux parent before these guards; that is not new
# entrypoint behavior and is not represented as a newly proven inert parent.
def _load_staged_package(monkeypatch):
    import builtins
    import importlib
    import io
    import socket
    import sys

    def forbidden(*args, **kwargs):
        raise AssertionError('DISABLED_PACKAGE_EFFECT')

    def guarded_open(original):
        def checked(file, mode='r', *args, **kwargs):
            if any(flag in mode for flag in 'wax+'):
                forbidden()
            return original(file, mode, *args, **kwargs)
        return checked

    monkeypatch.setattr(builtins, 'open', guarded_open(builtins.open))
    monkeypatch.setattr(io, 'open', guarded_open(io.open))
    original_os_open = os.open

    def read_only_open(path, flags, *args, **kwargs):
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            forbidden()
        return original_os_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, 'open', read_only_open)
    for name in ('mkdir', 'makedirs', 'remove', 'unlink', 'rmdir', 'rename', 'replace', 'system'):
        monkeypatch.setattr(os, name, forbidden)
    for name in ('Popen', 'run', 'call', 'check_call', 'check_output'):
        monkeypatch.setattr(subprocess, name, forbidden)
    monkeypatch.setattr(sqlite3, 'connect', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket.socket, 'connect_ex', forbidden)
    prefix = 'dopemux.governed_execution'
    for name in list(sys.modules):
        if name == prefix or name.startswith(prefix + '.'):
            monkeypatch.delitem(sys.modules, name)
    return importlib.import_module(prefix + '.offline_execution.disabled_entrypoint')


def test_staged_package_resolves_to_intended_source(monkeypatch):
    module = _load_staged_package(monkeypatch)
    root = Path(__file__).resolve().parents[4]
    expected = root / 'src/dopemux/governed_execution/offline_execution/disabled_entrypoint.py'
    assert Path(module.__file__).resolve() == expected.resolve()
    assert module.__name__ == 'dopemux.governed_execution.offline_execution.disabled_entrypoint'
    assert module.status()['activation'] == 'NOT_AUTHORIZED'


def test_explicit_packages_without_activation_script():
    import tomllib
    root = Path(__file__).resolve().parents[4]
    config = tomllib.loads((root / 'pyproject.toml').read_text())
    packages = config['tool']['setuptools']['packages']
    assert packages.count('dopemux.governed_execution') == 1
    assert packages.count('dopemux.governed_execution.offline_execution') == 1
    assert config['tool']['setuptools']['package-dir'][''] == 'src'
    assert not any('governed_execution' in value for value in config['project']['scripts'].values())


def test_new_package_markers_are_inert():
    import ast
    root = Path(__file__).resolve().parents[4] / 'src/dopemux/governed_execution'
    for path in (root / '__init__.py', root / 'offline_execution/__init__.py'):
        body = ast.parse(path.read_text()).body
        assert len(body) == 1
        assert isinstance(body[0], ast.Expr)
        assert isinstance(body[0].value, ast.Constant)
        assert isinstance(body[0].value.value, str)


import pytest


@pytest.mark.parametrize('command', ['activate', 'dispatch', 'run'])
def test_package_refuses_activation_commands(monkeypatch, capsys, command):
    module = _load_staged_package(monkeypatch)
    assert module.main([command]) == 2
    assert capsys.readouterr().out == 'HELD: DISABLED. No activation or dispatch command is available.\n'


def test_package_status_and_help_are_inert(monkeypatch, capsys):
    module = _load_staged_package(monkeypatch)
    assert module.main(['status']) == 0
    assert capsys.readouterr().out == 'DISABLED; dispatch HELD; PRIVATE_STAGING_ONLY\n'
    assert module.main(['--help']) == 0
    assert 'No activation command.' in capsys.readouterr().out


def test_package_ignores_ambient_activation(monkeypatch):
    monkeypatch.setenv('GOVERNANCE_ENABLED', '1')
    monkeypatch.setenv('GOV_OFFLINE_ENABLE', 'true')
    module = _load_staged_package(monkeypatch)
    assert module.status() == {'state': 'DISABLED', 'dispatch': 'HELD',
        'scope': 'PRIVATE_STAGING_ONLY', 'activation': 'NOT_AUTHORIZED'}
    assert module.dispatch(enabled=True) == {'status': 'HELD', 'reason': 'DISABLED', 'fixture': False}


def test_package_does_not_evaluate_grant_or_callback(monkeypatch):
    class Opaque:
        def __bool__(self):
            raise AssertionError('authority evaluated')
        def __call__(self, *args, **kwargs):
            raise AssertionError('callback invoked')
        def __iter__(self):
            raise AssertionError('authority iterated')
        def __getattr__(self, name):
            raise AssertionError('authority attribute read')

    module = _load_staged_package(monkeypatch)
    assert module.dispatch(Opaque(), enabled=Opaque(), grant=Opaque(), callback=Opaque()) == {
        'status': 'HELD', 'reason': 'DISABLED', 'fixture': False}


def test_package_results_cannot_enable_later_calls(monkeypatch):
    module = _load_staged_package(monkeypatch)
    status = module.status()
    status['state'] = 'ENABLED'
    dispatch = module.dispatch()
    dispatch['status'] = 'RUNNING'
    assert module.status()['state'] == 'DISABLED'
    assert module.dispatch() == {'status': 'HELD', 'reason': 'DISABLED', 'fixture': False}


def test_package_import_does_not_enroll_framework(monkeypatch):
    import sys
    _load_staged_package(monkeypatch)
    loaded = {name for name in sys.modules if name.startswith('dopemux.governed_execution')}
    assert loaded == {'dopemux.governed_execution',
        'dopemux.governed_execution.offline_execution',
        'dopemux.governed_execution.offline_execution.disabled_entrypoint'}
