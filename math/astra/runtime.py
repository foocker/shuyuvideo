"""Resolve Astra's Codex SDK/CLI from the shared ShuYu npm installation."""
import json
from pathlib import Path
import shutil
import subprocess

REPOSITORY = Path(__file__).resolve().parents[2]


def codex_version():
    return json.loads((REPOSITORY / 'package.json').read_text(encoding='utf-8'))['dependencies']['@openai/codex']


def is_installed(folder):
    expected = codex_version()
    for package in ('codex', 'codex-sdk'):
        path = folder / f'node_modules/@openai/{package}/package.json'
        try:
            if json.loads(path.read_text(encoding='utf-8'))['version'] != expected:
                return False
        except (OSError, ValueError, KeyError):
            return False
    return (folder / 'node_modules/@openai/codex/bin/codex.js').is_file()


def runtime_directory():
    if is_installed(REPOSITORY):
        return REPOSITORY
    raise RuntimeError('Codex runtime missing. Run npm ci at the shuyuvideo root or shuyu setup --math')


def setup_runtime():
    from astra.client import clean_environment
    npm = shutil.which('npm')
    if not npm or not shutil.which('node'):
        raise RuntimeError('Install Node.js 22+ and npm, then run shuyu setup --math')
    subprocess.run([npm, 'ci', '--no-audit', '--no-fund'], cwd=REPOSITORY,
                   env=clean_environment(), check=True, timeout=600)
    return runtime_directory()


def codex_command(*args):
    node = shutil.which('node')
    if not node:
        raise RuntimeError('Install Node.js 22+ and npm')
    return [node, str(runtime_directory() / 'node_modules/@openai/codex/bin/codex.js'), *args]
