"""Shared repository paths and configuration. No optional dependencies."""
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def config():
    data = json.loads((ROOT / 'workspace.json').read_text(encoding='utf-8'))
    local = ROOT / 'workspace.local.json'
    if local.exists():
        overrides = json.loads(local.read_text(encoding='utf-8'))
        # Machine-specific fonts and sound libraries only; outputs and engines stay repository-owned.
        data['fontOverrides'] = overrides.get('fonts', {})
        data['soundLibraries'] = overrides.get('soundLibraries', [])
    return data


def inside(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f'Path escapes repository: {relative}')
    return path


def output_dir(project, *parts, create=False):
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', project):
        raise ValueError(f'Invalid project ID: {project}')
    base = inside(config()['outputRoot']) / project
    path = base.joinpath(*parts).resolve()
    if not path.is_relative_to(base):
        raise ValueError('Output path escapes project')
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def python_path():
    base = inside(config()['pythonEnvironment'])
    return base / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def projects():
    result = dict(config()['projects'])
    # Local films are intentionally ignored by Git; discover their manifests.
    for path in sorted((ROOT / 'films').glob('*/package.json')):
        project = path.parent.name
        result.setdefault(project, {'source': path.parent.relative_to(ROOT).as_posix()})
    return result


def project_config(project):
    available = projects()
    if project in available:
        return available[project]
    candidate = inside(project)
    matches = [value for value in available.values() if inside(value['source']) == candidate]
    if len(matches) == 1:
        return matches[0]
    raise ValueError(f'Unknown project: {project}; run shuyu list')


def hyperframes_version(project=None):
    cfg = config()
    if not project:
        return cfg['hyperframes']
    record = project_config(project)
    return record.get('hyperframes', cfg['hyperframes'])


def font_record(name):
    cfg = config()
    data = json.loads(inside(cfg['fonts']).read_text(encoding='utf-8'))['fonts'][name]
    return {**data, **cfg.get('fontOverrides', {}).get(name, {})}


def system_font_dirs():
    """Standard font folders of this machine, found at run time, never stored."""
    home = Path.home()
    if os.name == 'nt':
        return [Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts',
                Path(os.environ.get('LOCALAPPDATA', home / 'AppData/Local')) / 'Microsoft/Windows/Fonts']
    return [Path('/System/Library/Fonts'), Path('/Library/Fonts'), home / 'Library/Fonts',
            Path('/usr/share/fonts'), Path('/usr/local/share/fonts'), home / '.local/share/fonts', home / '.fonts']


def font_path(name):
    """Resolve a registered font: a local `path` override, else `file` in the system font folders.

    style/fonts.json records only the file name so the repository holds no
    machine paths; workspace.local.json may give a path (relative to the
    repository or absolute) for fonts installed elsewhere.
    """
    record = font_record(name)
    if record.get('path'):
        path = Path(os.path.expandvars(record['path'])).expanduser()
        candidates = [path if path.is_absolute() else ROOT / path]
    else:
        candidates = [folder / record['file'] for folder in system_font_dirs()]
    found = next((p for p in candidates if p.is_file()), None)
    if found is None and not record.get('path'):
        # Linux distributions keep fonts in nested folders.
        found = next((p for folder in system_font_dirs() if folder.is_dir()
                      for p in folder.rglob(record['file'])), None)
    if found is None:
        raise FileNotFoundError(f"Font {name}: {record.get('path') or record['file']} not found; "
                                f'configure workspace.local.json fonts.{name}.path')
    return found.resolve()
