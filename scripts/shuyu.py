"""Repository entry point: one environment, project registry and output root."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from workspace import ROOT, config, inside, output_dir, projects, project_config, python_path, hyperframes_version

sys.path.insert(0, str(ROOT / 'writing'))
from manuscript import check_if_managed, check_prepared


def invoke(command, **kwargs):
    return subprocess.run([str(x) for x in command], cwd=kwargs.pop('cwd', ROOT), check=True, **kwargs)


SOURCE_MANIFEST = '.shuyu-source.json'


def source_files(source, ignore):
    found = []
    for parent, dirs, files in os.walk(source):
        skipped = ignore(parent, dirs + files)
        dirs[:] = [d for d in dirs if d not in skipped]
        found += [(Path(parent) / f).relative_to(source).as_posix() for f in files if f not in skipped]
    return sorted(found)


def remove_deleted_sources(source, destination, ignore):
    """Drop build copies of files deleted or renamed in source since the last prepare.

    Only files recorded as copied from source are candidates, so voice takes,
    mixes and other files generated inside the build are never removed.
    """
    manifest = destination / SOURCE_MANIFEST
    current = source_files(source, ignore)
    if manifest.exists():
        previous = json.loads(manifest.read_text(encoding='utf-8'))['files']
        for name in sorted(set(previous) - set(current)):
            path = inside(destination.relative_to(ROOT) / name)
            if path.is_file():
                path.unlink()
    manifest.write_text(json.dumps({'files': current}, ensure_ascii=False, indent=1), encoding='utf-8')


def prepare_project(project):
    record = project_config(project)
    if record.get('engine') == 'manim':
        raise ValueError('Use shuyu math prepare/run --project <id> for Manim projects')
    source = inside(record['source'])
    check_if_managed(source)
    if record.get('build'):
        invoke([sys.executable, '-X', 'utf8', inside(record['build'])])
        check_prepared(source, output_dir(project))
        return output_dir(project)
    destination = output_dir(project, 'project', create=True)
    # Fresh source remains authoritative. Caches and archived results are not
    # copied into another build, avoiding recursive output copies.
    ignore = shutil.ignore_patterns('output', 'out', 'renders', 'node_modules', '.git',
                                   '.hyperframes', '__pycache__', '.pytest_cache')
    remove_deleted_sources(source, destination, ignore)
    shutil.copytree(source, destination, dirs_exist_ok=True, ignore=ignore)
    invoke([sys.executable, '-X', 'utf8', ROOT / 'scripts/prepare-film.py', destination])
    from font_assets import build_subset
    aliases = record.get('fonts', {})
    if aliases:
        text = ''.join(p.read_text(encoding='utf-8') for suffix in ('*.html', '*.js')
                       for p in source.rglob(suffix) if 'vendor' not in p.parts)
        for name, font in aliases.items():
            build_subset(font, text, destination / f'assets/fonts/{name}.woff2')
    # Package scripts in the copy are no longer relative to the source directory.
    # HyperFrames only needs the entry HTML and root registry owns CLI dispatch.
    package = destination / 'package.json'
    if package.exists():
        package.write_text(json.dumps({'name': project, 'private': True}), encoding='utf-8')
    check_prepared(source, destination)
    return destination


def layout_report():
    cfg = config()
    errors, aliases = [], []
    for old, new in cfg.get('legacyOutputAliases', {}).items():
        path = ROOT / old
        if path.exists() and path.resolve() == inside(new):
            aliases.append({'path': old, 'target': new})
        elif path.exists():
            errors.append(f'Legacy output has independent storage: {old}')
    for module in ('motion', 'math', 'character', 'brand', 'sound', 'writing', 'cover', 'publish', 'examples'):
        for parent, dirs, files in os.walk(ROOT / module, followlinks=False):
            for name in list(dirs):
                path = Path(parent) / name
                if name in ('node_modules', '.venv', 'output', 'out', 'renders', 'runs'):
                    if any(path.iterdir()):
                        errors.append(f'Module owns generated/dependency directory: {path.relative_to(ROOT)}')
                    dirs.remove(name)
                elif name in ('.hyperframes', '__pycache__', '.pytest_cache'):
                    dirs.remove(name)
    return {'ok': not errors, 'errors': errors, 'python': python_path().relative_to(ROOT).as_posix(),
            'dependencyManifests': ['package.json', 'package-lock.json', 'requirements.txt', 'requirements-math.txt', 'requirements-dev.txt'],
            'outputs': cfg['outputRoot'], 'fontRegistry': cfg['fonts'],
            'fontCache': cfg['cacheRoot'] + '/fonts', 'legacyAliases': aliases}


def setup(args):
    target = python_path()
    if not target.is_file():
        invoke([sys.executable, '-m', 'venv', target.parent.parent])
    requirements = 'requirements-math.txt' if '--math' in args else 'requirements.txt'
    invoke([target, '-m', 'pip', 'install', '-r', ROOT / requirements])
    if '--dev' in args:
        invoke([target, '-m', 'pip', 'install', '-r', ROOT / 'requirements-dev.txt'])
    invoke([shutil.which('npm') or 'npm', 'ci', '--no-audit', '--no-fund'])
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    target = python_path()
    # npm, PowerShell and direct Python invocations all converge here.
    if target.is_file() and Path(sys.prefix).resolve() != target.parent.parent.resolve():
        return subprocess.call([str(target), '-X', 'utf8', str(Path(__file__).resolve()), *argv], cwd=ROOT)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['setup', 'list', 'layout', 'doctor', 'test', 'math', 'writing', 'cover', 'deliver', 'publish', 'validate',
                                           'prepare', 'render', 'check', 'snapshot', 'preview', 'exec'])
    parser.add_argument('args', nargs=argparse.REMAINDER)
    opts = parser.parse_args(argv)
    args = opts.args
    if opts.command == 'setup':
        return setup(args)
    if opts.command in ('list', 'layout'):
        report = layout_report() if opts.command == 'layout' else [
            {'id': key, **value, 'output': str(output_dir(key).relative_to(ROOT))}
            for key, value in projects().items()]
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if opts.command == 'list' or report['ok'] else 1
    if opts.command == 'doctor':
        invoke([sys.executable, ROOT / 'scripts/doctor.py', *args])
    elif opts.command == 'test':
        invoke([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
        if '--math' in args:
            temporary = output_dir('verification', 'math-tests', create=True) / uuid.uuid4().hex
            invoke([sys.executable, '-m', 'pytest', '-c', 'math/pytest.ini', 'math/tests', '--basetemp', temporary,
                    '-o', 'cache_dir=' + str(output_dir('verification', 'pytest-cache'))])
    elif opts.command == 'math':
        invoke([sys.executable, '-X', 'utf8', ROOT / 'math/shuyu_astra.py', *args])
    elif opts.command == 'writing':
        from manuscript import main as writing_main
        return writing_main(args)
    elif opts.command == 'publish':
        sys.path.insert(0, str(ROOT / 'publish'))
        from publishing import main as publish_main
        return publish_main(args)
    elif opts.command in ('cover', 'deliver'):
        sys.path.insert(0, str(ROOT / 'cover'))
        from production import main as cover_main, delivery_main
        return cover_main(args) if opts.command == 'cover' else delivery_main(args)
    elif opts.command == 'validate':
        if args[:1] == ['screen']:
            invoke([sys.executable, '-X', 'utf8', ROOT / 'scripts/validation/screen_text.py', *args[1:]])
        elif args[:1] and args[0] in ('defects', 'retro', 'summary', 'reuse'):
            invoke([sys.executable, '-X', 'utf8', ROOT / 'scripts/validation/accumulation.py', *args])
        else:
            invoke([sys.executable, '-X', 'utf8', ROOT / 'scripts/validation/validate.py', *args])
    elif opts.command == 'exec':
        if not args:
            parser.error('exec requires a repository script path')
        script = inside(args[0])
        invoke([sys.executable, '-X', 'utf8', script, *args[1:]])
    else:
        if not args:
            parser.error('Provide a project ID; use shuyu list')
        project, extra = args[0], args[1:]
        record = project_config(project)
        if opts.command == 'render':
            sys.path.insert(0, str(ROOT / 'cover'))
            import production as cover
            cover.invalidate_delivery(project)
            if cover.required(record):
                cover.preflight(project)
        directory = prepare_project(project)
        if opts.command == 'prepare':
            print(directory)
            return 0
        command = [shutil.which('npx') or 'npx', '--yes', f'hyperframes@{hyperframes_version(project)}', opts.command]
        if opts.command == 'render':
            sys.path.insert(0, str(ROOT / 'sound'))
            from audio_state import validate_mix_state
            validate_mix_state(directory)
            if any(x in ('-o', '--output') or x.startswith('--output=') for x in extra):
                parser.error('Render output is managed by the workspace; change the project video name in workspace.json')
            import intro
            choice = True if '--intro' in extra else False if '--no-intro' in extra else None
            extra = [x for x in extra if x not in ('--intro', '--no-intro')]
            with_intro = intro.wanted(project, choice)
            movie = output_dir(project, 'renders', create=True) / record.get('video', project + '.mp4')
            # With the intro, HyperFrames writes the body beside the delivery file.
            body = movie.with_name(movie.stem + '-body.mp4') if with_intro else movie
            command += ['--output', str(body), '--quality', 'delivery']
            invoke([*command, *extra], cwd=directory)
            if with_intro:
                seconds = intro.join(intro.intro_file(), body, movie)
                print(f'brand intro {seconds:.2f}s + {body.name} -> {movie.relative_to(ROOT).as_posix()}')
            report = output_dir(project, 'reports', create=True) / 'render-check.json'
            result = subprocess.call([sys.executable, '-X', 'utf8', ROOT / 'scripts/validation/render_check.py',
                                      movie, '--project', directory, '--report', report], cwd=ROOT)
            if result:
                return result
            if cover.required(record):
                cover.build(project)
                cover.package_delivery(project, json.loads(report.read_text(encoding='utf-8')))
                print(f'video + cover: {movie} | {cover.paths(project)["cover"]}')
            return 0
        elif opts.command == 'snapshot':
            command += ['--output', str(output_dir(project, 'reports', 'snapshots', create=True))]
        elif opts.command == 'check':
            command += ['--json']
        elif opts.command == 'preview':
            command += ['--background']
        if opts.command == 'check':
            # HyperFrames exits non-zero on failed checks; keep its report either way.
            result = subprocess.run([str(x) for x in (*command, *extra)], cwd=directory,
                                    stdout=subprocess.PIPE, text=True, encoding='utf-8')
            reports = output_dir(project, 'reports', create=True)
            report = reports / 'check.json'
            report.write_text(result.stdout, encoding='utf-8')
            try:
                ok = json.loads(result.stdout).get('ok') is True
            except json.JSONDecodeError:
                ok = False
            sys.path.insert(0, str(ROOT / 'scripts/validation'))
            from screen_text import scan
            findings = scan(directory)
            screen = reports / 'screen-text.json'
            screen.write_text(json.dumps({'ok': not findings, 'kind': 'screen-text', 'findings': findings},
                                         ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(json.dumps({'ok': ok and not findings, 'hyperframes': ok, 'report': report.relative_to(ROOT).as_posix(),
                              'screenText': not findings, 'screenTextReport': screen.relative_to(ROOT).as_posix(),
                              'screenTextFindings': len(findings)}, ensure_ascii=False))
            return 0 if ok and not findings else 1
        invoke([*command, *extra], cwd=directory)
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
