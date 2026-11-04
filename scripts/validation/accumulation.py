"""Keep the defect register, film retrospectives and shared-module reuse honest.

Usage:
  python scripts/validation/accumulation.py defects
  python scripts/validation/accumulation.py retro <retro.json> [--duration <seconds>]
  python scripts/validation/accumulation.py summary
  python scripts/validation/accumulation.py reuse

defects  every guarded defect names a check file that exists (films/ paths are
         skipped when the local films folder is absent).
retro    one film's retro.json uses known method IDs (studies/methods.md, local
         only; without it IDs are checked for format) and
         defect IDs (docs/defects.json); times fall inside the film.
summary  aggregates all films/*/retro.json and examples/*/retro.json by method.
reuse    counts projects that use each shared runtime copied by prepare-film.py.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
DEFECTS = ROOT / 'docs/defects.json'
METHODS = ROOT / 'studies/methods.md'
OUTCOMES = ('worked', 'unclear', 'failed')
# Shared code reaches films as copies under assets/; only authored files count as use.
COPIES = ('assets/lib/', 'assets/style/', 'assets/vendor/')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def method_ids():
    """Method IDs from the local research library, or None when studies/ is absent.

    studies/ is git-ignored, so a fresh clone cannot check method IDs.
    """
    if not METHODS.is_file():
        return None
    return set(re.findall(r'^## (M\d+)', METHODS.read_text(encoding='utf-8'), re.M))


def check_defects(register=None):
    register = register or load(DEFECTS)
    errors, ids = [], set()
    if register.get('schema') != 'shuyu-defects/v1':
        return ['schema must be shuyu-defects/v1']
    for item in register.get('defects', []):
        key = item.get('id', '?')
        if key in ids:
            errors.append(f'{key}: duplicate id')
        ids.add(key)
        for field in ('symptom', 'cause', 'status'):
            if not item.get(field):
                errors.append(f'{key}: {field} is required')
        if item.get('status') not in ('guarded', 'open'):
            errors.append(f'{key}: status must be guarded or open')
        check = item.get('check', '')
        if item.get('status') == 'guarded':
            if not check:
                errors.append(f'{key}: a guarded defect must name its check')
            elif not (ROOT / check).exists() and not (check.startswith('films/') and not (ROOT / 'films').is_dir()):
                errors.append(f'{key}: check {check} does not exist')
    return errors


def check_retro(retro, duration=None):
    errors = []
    if retro.get('schema') != 'shuyu-retro/v1':
        return ['schema must be shuyu-retro/v1']
    for field in ('project', 'date'):
        if not retro.get(field):
            errors.append(f'{field} is required')
    known_methods = method_ids()
    known_defects = {d['id'] for d in load(DEFECTS)['defects']}
    duration = duration or retro.get('duration')
    for i, use in enumerate(retro.get('methods', [])):
        where = f"methods[{i}] {use.get('id', '?')}"
        if not isinstance(use.get('id'), str) or not re.fullmatch(r'M\d+', use['id']):
            errors.append(f'{where}: method id must look like M01')
        elif known_methods is not None and use['id'] not in known_methods:
            errors.append(f'{where}: unknown method; see studies/methods.md')
        if use.get('outcome') not in OUTCOMES:
            errors.append(f'{where}: outcome must be one of {OUTCOMES}')
        if not use.get('purpose'):
            errors.append(f'{where}: purpose (the viewer obstacle it addressed) is required')
        span = use.get('at')
        if not (isinstance(span, list) and len(span) == 2 and all(isinstance(t, (int, float)) for t in span)
                and 0 <= span[0] < span[1] and (duration is None or span[1] <= duration)):
            errors.append(f'{where}: at must be [start, end] seconds inside the film')
    for i, found in enumerate(retro.get('defects', [])):
        if found.get('id') not in known_defects:
            errors.append(f"defects[{i}]: {found.get('id')!r} is not in docs/defects.json; register it first")
        if not found.get('fix'):
            errors.append(f'defects[{i}]: fix is required')
    return errors


def retro_files():
    return sorted([*(ROOT / 'films').glob('*/retro.json'), *(ROOT / 'examples').glob('*/retro.json')])


def summary(paths=None):
    methods, defects = {}, {}
    for path in paths if paths is not None else retro_files():
        retro = load(path)
        for use in retro.get('methods', []):
            entry = methods.setdefault(use['id'], {'uses': 0, 'projects': set(), **{o: 0 for o in OUTCOMES}})
            entry['uses'] += 1
            entry['projects'].add(retro['project'])
            entry[use['outcome']] += 1
        for found in retro.get('defects', []):
            defects.setdefault(found['id'], set()).add(retro['project'])
    return {'methods': {k: {**v, 'projects': sorted(v['projects'])} for k, v in sorted(methods.items())},
            'defects': {k: sorted(v) for k, v in sorted(defects.items())},
            # None when the local research library is absent.
            'unused': None if method_ids() is None else sorted(method_ids() - set(methods))}


def shared_runtimes():
    """Exported globals of each shared file copied into film bundles."""
    spec = importlib.util.spec_from_file_location('prepare_film', ROOT / 'scripts/prepare-film.py')
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / 'scripts'))
    spec.loader.exec_module(module)
    sources = [s for s in module.FILES.values() if 'node_modules' not in s.parts]
    sources += [s for group in getattr(module, 'BUNDLES', {}).values() for s in group]
    result = {}
    for source in sources:
        text = source.read_text(encoding='utf-8')
        names = set(re.findall(r'root\.(Shuyu\w+)\s*=', text))
        if source.suffix == '.css':
            names = {source.name}
        if names:
            result[source.relative_to(ROOT).as_posix()] = sorted(names)
    return result


def project_of(path):
    parts = path.relative_to(ROOT).parts
    return '/'.join(parts[:2]) if parts[0] in ('films', 'examples') else parts[0]


def reuse():
    runtimes = shared_runtimes()
    authored = [p for top in ('films', 'examples', 'brand') if (ROOT / top).is_dir()
                for suffix in ('*.html', '*.js') for p in (ROOT / top).rglob(suffix)
                if not any(c in p.relative_to(ROOT).as_posix() for c in COPIES)
                and 'node_modules' not in p.parts and 'output' not in p.parts]
    texts = {p: p.read_text(encoding='utf-8', errors='replace') for p in authored}
    report = {}
    for source, names in runtimes.items():
        users = sorted({project_of(p) for p, text in texts.items() if any(n in text for n in names)})
        # Examples are derived from films (staircase copies staircase-sum), so
        # they show the module still runs but are not independent reuse.
        works = [u for u in users if not u.startswith('examples/')]
        report[source] = {'globals': names, 'works': works,
                          'examples': [u for u in users if u.startswith('examples/')],
                          'proven': len(works) >= 2}
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=('defects', 'retro', 'summary', 'reuse'))
    parser.add_argument('input', nargs='?', type=Path)
    parser.add_argument('--duration', type=float)
    args = parser.parse_args(argv)
    if args.command == 'retro':
        if not args.input:
            parser.error('retro needs a retro.json path')
        errors = check_retro(load(args.input), args.duration)
        report = {'ok': not errors, 'kind': 'retro', 'errors': errors}
        if method_ids() is None:
            report['warnings'] = ['studies/methods.md is absent; method IDs were checked for format only']
    elif args.command == 'defects':
        errors = check_defects()
        report = {'ok': not errors, 'kind': 'defects', 'errors': errors,
                  'open': [d['id'] for d in load(DEFECTS)['defects'] if d['status'] == 'open']}
    elif args.command == 'summary':
        report = {'ok': True, 'kind': 'retro-summary', 'retros': [p.relative_to(ROOT).as_posix() for p in retro_files()],
                  **summary()}
    else:
        report = {'ok': True, 'kind': 'reuse', 'modules': reuse(),
                  'rule': 'A shared module is proven once two independent works use it; examples do not count.'}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
