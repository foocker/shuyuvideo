"""Astra resolves the same root installation used by all video tools."""
import json
from pathlib import Path
import pytest
from astra import runtime


def installed_runtime(folder, version='0.156.1'):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'package.json').write_text(json.dumps({'dependencies': {'@openai/codex': '0.156.1'}}))
    for name in ('codex', 'codex-sdk'):
        package = folder / f'node_modules/@openai/{name}'
        package.mkdir(parents=True)
        (package / 'package.json').write_text(json.dumps({'version': version}))
    cli = folder / 'node_modules/@openai/codex/bin/codex.js'
    cli.parent.mkdir()
    cli.write_text('')
    return folder


def test_shared_root_runtime_is_selected(tmp_path, monkeypatch):
    root = installed_runtime(tmp_path / 'workspace')
    monkeypatch.setattr(runtime, 'REPOSITORY', root)
    assert runtime.runtime_directory() == root


def test_wrong_version_requires_root_setup(tmp_path, monkeypatch):
    root = installed_runtime(tmp_path / 'workspace', '0.156.0')
    monkeypatch.setattr(runtime, 'REPOSITORY', root)
    with pytest.raises(RuntimeError, match='shuyu setup'):
        runtime.runtime_directory()


def test_setup_uses_root_and_strips_credentials(tmp_path, monkeypatch):
    root = tmp_path / 'workspace'
    root.mkdir()
    monkeypatch.setattr(runtime, 'REPOSITORY', root)
    monkeypatch.setattr(runtime.shutil, 'which', lambda name: name)
    monkeypatch.setenv('OPENAI_API_KEY', 'test')
    monkeypatch.setenv('EXAMPLE_API_KEY', 'test')
    def install(command, **kwargs):
        assert command == ['npm', 'ci', '--no-audit', '--no-fund']
        assert kwargs['cwd'] == root
        assert 'OPENAI_API_KEY' not in kwargs['env'] and 'EXAMPLE_API_KEY' not in kwargs['env']
        installed_runtime(root)
    monkeypatch.setattr(runtime.subprocess, 'run', install)
    assert runtime.setup_runtime() == root


def test_sdk_and_cli_pins_match():
    data = json.loads((runtime.REPOSITORY / 'package.json').read_text(encoding='utf-8'))
    assert data['dependencies']['@openai/codex-sdk'] == runtime.codex_version()
