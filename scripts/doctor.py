"""Check the Python, audio and local rendering environment; never install fixes.

Run from the repository: python scripts/doctor.py [--audio-only] [--project DIR] [--json]
The selected project's pinned HyperFrames CLI is resolved from the npm cache.
"""
import argparse
import importlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import workspace

ROOT = Path(__file__).resolve().parents[1]
IMPORTS = {'numpy': 'numpy', 'soundfile': 'soundfile', 'edge-tts': 'edge_tts',
           'fonttools': 'fontTools', 'brotli': 'brotli', 'Pillow': 'PIL',
           'playwright': 'playwright', 'matplotlib': 'matplotlib'}
AUDIO_PACKAGES = {'numpy', 'soundfile', 'edge-tts'}
# These features are not used by the repository's local render / edge-tts workflow.
OPTIONAL_HF_CHECKS = {'whisper-cpp', 'TTS (Kokoro)', 'BGM (MusicGen)', 'Docker', 'Docker running'}
DEFAULT_HF_VERSION = workspace.config()['hyperframes']


def result(name, ok, detail, fix='', optional=False):
    return {'name': name, 'status': 'ok' if ok else 'warn' if optional else 'fail',
            'detail': detail, 'fix': fix if not ok else ''}


def command(args, cwd=ROOT, timeout=30):
    run = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                         encoding='utf-8', errors='replace', timeout=timeout)
    if run.returncode:
        raise RuntimeError((run.stderr or run.stdout).strip()[-1500:])
    return run.stdout.strip()


def release(version):
    match = re.fullmatch(r'(\d+(?:\.\d+)*)(?:\.post\d+)?', version)
    if not match:
        raise ValueError(f'Unsupported or prerelease version: {version}')
    return tuple(int(part) for part in match[1].split('.'))


def requirement_rows(path):
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        match = re.fullmatch(r'([\w-]+)>=(\d+(?:\.\d+)*),<(\d+(?:\.\d+)*)', line)
        if not match:
            raise ValueError(f'Unsupported requirement: {line}')
        yield match[1], match[2], match[3]


def python_checks(audio_only=False):
    rows = [result('Python', sys.version_info >= (3, 11), f'{sys.version.split()[0]} — {sys.executable}',
                   'Install Python 3.11+ and create a project virtual environment; see docs/SETUP.md.')]
    python = f'& "{sys.executable}"' if os.name == 'nt' else f'"{sys.executable}"'
    fix = f'{python} -m pip install -r "{ROOT / "requirements.txt"}"'
    for name, minimum, maximum in requirement_rows(ROOT / 'requirements.txt'):
        if audio_only and name not in AUDIO_PACKAGES:
            continue
        try:
            version = importlib.metadata.version(name)
            module = importlib.import_module(IMPORTS[name])
            ok = release(minimum) <= release(version) < release(maximum)
            detail = f'{version}; requires >={minimum},<{maximum}; {module.__file__}'
            rows.append(result(name, ok, detail, fix))
        except Exception as exc:
            rows.append(result(name, False, str(exc), fix))
    return rows


def executable_check(name, args, fix, minimum=None):
    executable = shutil.which(name)
    if not executable:
        return result(name, False, 'Not found on PATH', fix)
    try:
        version = command([executable, *args]).splitlines()[0]
        ok = minimum is None or release(version.lstrip('v')) >= minimum
        return result(name, ok, f'{version} — {executable}', fix)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        return result(name, False, str(exc), fix)


def hyperframes_version(project):
    if project == ROOT:
        return DEFAULT_HF_VERSION
    for project_id, record in workspace.projects().items():
        if workspace.inside(record['source']) == project:
            return workspace.hyperframes_version(project_id)
    package = project / 'package.json'
    if not package.is_file():
        raise ValueError(f'Missing project package.json: {package}')
    config = json.loads(package.read_text(encoding='utf-8'))
    versions = set(re.findall(r'\bhyperframes@(\d+\.\d+\.\d+)\b', ' '.join(config.get('scripts', {}).values())))
    if len(versions) > 1:
        raise ValueError(f'Conflicting HyperFrames versions in {package}: {sorted(versions)}')
    if versions:
        return versions.pop()
    if project == ROOT:
        return DEFAULT_HF_VERSION
    raise ValueError(f'No pinned HyperFrames version in {package}; pin the project scripts first')


def classify_hyperframes(payload, version):
    checks = payload.get('checks')
    if not isinstance(checks, list) or not checks:
        raise ValueError('HyperFrames doctor returned no checks')
    rows = []
    for item in checks:
        name = item['name']
        fix = item.get('hint', f'npx --yes hyperframes@{version} doctor')
        if name == 'Chrome':
            fix = f'npx --yes hyperframes@{version} browser ensure'
        update_only = name == 'Version' and 'available' in item.get('detail', '')
        if update_only:
            fix = 'Optional update only; keep the project pin until an upgrade has been tested.'
        rows.append(result(f'HyperFrames / {name}', item.get('ok') is True,
                           item.get('detail', ''), fix, name in OPTIONAL_HF_CHECKS or update_only))
    # Never use the child's zero exit status as proof of readiness.
    if payload.get('ok') is not True and all(r['status'] == 'ok' for r in rows):
        rows.append(result('HyperFrames', False, 'Doctor reported ok=false without a failing check',
                           f'npx --yes hyperframes@{version} doctor'))
    return rows


def render_checks(project):
    rows = [executable_check('node', ['--version'], 'Install Node.js 22+ LTS: https://nodejs.org/', (22,)),
            executable_check('npm', ['--version'], 'Install Node.js 22+ LTS, which includes npm.')]
    manifest = json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))
    for package, expected in manifest['dependencies'].items():
        path = ROOT / 'node_modules' / package / 'package.json'
        try:
            actual = json.loads(path.read_text(encoding='utf-8'))['version']
            rows.append(result(package, actual == expected, f'{actual}; requires {expected}', f'npm --prefix "{ROOT}" ci'))
        except (OSError, ValueError, KeyError) as exc:
            rows.append(result(package, False, str(exc), f'npm --prefix "{ROOT}" ci'))
    for name in ('sans', 'sans-bold', 'omega'):
        try:
            path = workspace.font_path(name)
            detail = str(path)
            from fontTools.ttLib import TTFont
            with TTFont(path, fontNumber=workspace.font_record(name).get('faceIndex', 0)) as font:
                ok = bool(font.getBestCmap())
        except Exception as exc:
            ok, detail = False, str(exc)
        rows.append(result(f'Font / {name}', ok, detail,
                           'Configure a licensed font in workspace.local.json; see style/fonts.json.'))
    try:
        version = hyperframes_version(project)
        npx = shutil.which('npx')
        if not npx:
            raise RuntimeError('npx is not on PATH; install Node.js 22+ LTS')
        text = command([npx, '--offline', '--yes', f'hyperframes@{version}', 'doctor', '--json'], cwd=project, timeout=45)
        payload = json.loads(text)
        rows.extend(classify_hyperframes(payload, version))
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        version = locals().get('version', DEFAULT_HF_VERSION)
        rows.append(result('HyperFrames', False, str(exc), f'npx --yes hyperframes@{version} doctor --json'))
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio-only', action='store_true', help='Only Python audio dependencies, FFmpeg and ffprobe')
    parser.add_argument('--project', type=Path, default=ROOT, help='Use this project package.json to select the HyperFrames version')
    parser.add_argument('--json', action='store_true', help='Print machine-readable results')
    args = parser.parse_args(argv)
    try:
        checks = python_checks(args.audio_only)
        fix = ('winget install --id Gyan.FFmpeg --exact; then reopen the terminal'
               if os.name == 'nt' else 'Install FFmpeg and ffprobe with your system package manager, then add them to PATH.')
        checks.extend(executable_check(name, ['-version'], fix) for name in ('ffmpeg', 'ffprobe'))
        if not args.audio_only:
            checks.extend(render_checks(args.project.resolve()))
    except (OSError, ValueError, KeyError) as exc:
        checks = [result('Configuration', False, str(exc), 'Restore repository configuration files and retry.')]
    report = {'ok': all(c['status'] != 'fail' for c in checks), 'python': sys.executable,
              'scope': 'audio' if args.audio_only else 'local-production', 'checks': checks,
              'note': 'Environment checks only; no TTS request, film render or listening test is performed.'}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for check in checks:
            print(f'[{check["status"].upper()}] {check["name"]}: {check["detail"]}')
            if check['fix']:
                print(f'  Fix: {check["fix"]}')
        print('READY' if report['ok'] else 'NOT READY — resolve FAIL items and rerun.')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    sys.exit(main())
