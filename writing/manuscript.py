"""Deterministic spoken-script import/export. Standard library only; no model calls."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile


MARKER = '<!-- shuyu-script/v1 -->'
STATE = '.writing.json'
LINE = re.compile(r'<!-- shuyu-line (\{.*\}) -->')
END = '<!-- /shuyu-line -->'
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}')
RESERVED = {'con', 'prn', 'aux', 'nul', *(f'com{i}' for i in range(1, 10)),
            *(f'lpt{i}' for i in range(1, 10))}


def loads(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result

    def invalid(value):
        raise ValueError(f'Non-finite JSON value: {value}')

    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def read_json(path):
    return loads(path.read_text(encoding='utf-8-sig'))


def digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def number(value, label):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError(f'{label}: expected a finite nonnegative number')


def validate(config):
    if not isinstance(config, dict) or not isinstance(config.get('voice'), str) or not config['voice'].strip():
        raise ValueError('Narration requires a nonempty voice setting')
    if 'rate' in config and (not isinstance(config['rate'], str)
                             or not re.fullmatch(r'[+-]\d+%', config['rate'])):
        raise ValueError('rate: expected a signed percentage, e.g. -3%')
    for key in ('lead', 'tail', 'gap', 'bedGain'):
        if key in config:
            number(config[key], key)
    rows = config.get('lines')
    if not isinstance(rows, list) or not rows:
        raise ValueError('Narration requires at least one line')
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Each narration line must be an object')
        name = row.get('id')
        if not isinstance(name, str) or not ID.fullmatch(name) or name.lower() in RESERVED:
            raise ValueError(f'Unsafe line ID for audio filenames: {name!r}')
        if name.casefold() in seen:
            raise ValueError(f'Duplicate line ID (case insensitive): {name}')
        seen.add(name.casefold())
        text = row.get('text')
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f'{name}: empty spoken text')
        # Match voice.py constraints; markup is a file-format error, not a style score.
        if any(c in text for c in ('$', '\\', '/', '?', '\ufffd', '<!--', '-->', '```', '\r')):
            raise ValueError(f'{name}: text contains markup or characters unsupported by voice.py')
        if any(re.match(r'\s*(#{1,6} |>|[-*] |\d+\. )', line) for line in text.splitlines()):
            raise ValueError(f'{name}: put Markdown headings, lists and notes outside spoken text')
        if 'scene' in row and (not isinstance(row['scene'], str) or not row['scene'].strip()):
            raise ValueError(f'{name}: scene must be a nonempty string')
        for key in ('pause', 'start'):
            if key in row:
                number(row[key], f'{name}.{key}')
    # Validate unknown extension fields as JSON too, without dropping them.
    digest(config)
    return config


def parse(text):
    lines = text.removeprefix('\ufeff').splitlines()
    if not lines or lines[0] != MARKER:
        raise ValueError('Missing shuyu-script/v1 marker; a legacy builder may have overwritten the script')
    config, rows = None, []
    i = 1
    while i < len(lines):
        item = lines[i]
        i += 1
        if not item.strip() or re.fullmatch(r'#{1,3} .+', item):
            continue
        if item == '```shuyu-voice':
            if config is not None or rows:
                raise ValueError('Use one shuyu-voice block before the spoken lines')
            start = i
            while i < len(lines) and lines[i] != '```':
                i += 1
            if i == len(lines):
                raise ValueError('Unclosed shuyu-voice block')
            config = loads('\n'.join(lines[start:i]))
            i += 1
            if not isinstance(config, dict) or 'lines' in config:
                raise ValueError('shuyu-voice must be a settings object without lines')
        elif match := LINE.fullmatch(item):
            if config is None:
                raise ValueError('shuyu-voice settings must precede spoken lines')
            row = loads(match[1])
            if not isinstance(row, dict) or 'text' in row:
                raise ValueError('Line metadata must be an object without text')
            start = i
            while i < len(lines) and lines[i] != END:
                i += 1
            if i == len(lines):
                raise ValueError(f'Unclosed spoken line: {row.get("id")}')
            row['text'] = '\n'.join(lines[start:i])
            i += 1
            rows.append(row)
        else:
            raise ValueError(f'Line {i}: unexpected content outside spoken blocks; move notes to DIRECTION.md')
    if config is None:
        raise ValueError('Missing shuyu-voice settings')
    return validate({**config, 'lines': rows})


def format_script(config, title='口播稿'):
    validate(config)
    if not title.strip() or '\n' in title or '\r' in title:
        raise ValueError('Title must be one nonempty line')
    settings = {key: value for key, value in config.items() if key != 'lines'}
    chunks = [MARKER, '# ' + title, '```shuyu-voice\n' +
              json.dumps(settings, ensure_ascii=False, indent=2, allow_nan=False) + '\n```']
    for row in config['lines']:
        meta = {key: value for key, value in row.items() if key != 'text'}
        chunks.append('<!-- shuyu-line ' + json.dumps(meta, ensure_ascii=False, allow_nan=False) +
                      ' -->\n' + row['text'] + '\n' + END)
    result = '\n\n'.join(chunks) + '\n'
    if digest(parse(result)) != digest(config):
        raise ValueError('Input cannot be represented losslessly by the manuscript format')
    return result


def script_path(film, name):
    if (not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.md', name)
            or Path(name).stem.lower() in RESERVED):
        raise ValueError('Script must be a local Markdown filename, e.g. SCRIPT.writing.md')
    path = film / name
    if path.is_symlink() or path.resolve().parent != film.resolve():
        raise ValueError('Script must stay directly inside the project')
    return path


def state_for(film):
    if not (film / STATE).exists():
        return None
    state = read_json(film / STATE)
    if (not isinstance(state, dict) or state.get('schema') != 'shuyu-writing/v1'
            or not isinstance(state.get('narrationSha256'), str)
            or not re.fullmatch(r'[0-9a-f]{64}', state['narrationSha256'])):
        raise ValueError('Invalid .writing.json; restore its last consistent version')
    script_path(film, state.get('script'))
    return state


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError(f'Refusing to replace a symbolic link: {path}')
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                         dir=path.parent, prefix='.' + path.name, delete=False) as stream:
            name = stream.name
            stream.write(text)
        os.replace(name, path)
    finally:
        if name and Path(name).exists():
            Path(name).unlink()


def save_state(film, script, config):
    state = {'schema': 'shuyu-writing/v1', 'script': script.name, 'narrationSha256': digest(config)}
    atomic_write(film / STATE, json.dumps(state, ensure_ascii=False, indent=2) + '\n')


def check_references(film, config):
    """Only anchors.json is a public line-reference contract; custom builders need review."""
    path = film / 'anchors.json'
    if not path.exists():
        return
    anchors = read_json(path)
    if not isinstance(anchors, dict):
        raise ValueError('anchors.json must be an object')
    rows = {row['id']: row['text'] for row in config['lines']}
    for name, spec in anchors.items():
        if not isinstance(spec, dict) or not isinstance(spec.get('line'), str) or spec['line'] not in rows:
            raise ValueError(f'Anchor {name}: unknown line reference')
        if 'word' in spec:
            word, nth = spec['word'], spec.get('nth', 1)
            if (not isinstance(word, str) or not word or type(nth) is not int or nth < 1
                    or rows[spec['line']].count(word) < nth):
                raise ValueError(f'Anchor {name}: word or occurrence absent from edited text')


def import_script(film, name='SCRIPT.md', title='口播稿'):
    path = script_path(film, name)
    if path.exists() or (film / STATE).exists():
        raise ValueError('Import never overwrites a script or managed project; for legacy SCRIPT.md use --script SCRIPT.writing.md')
    config = validate(read_json(film / 'narration.json'))
    content = format_script(config, title)
    check_references(film, config)
    # Exclusive create preserves drafts even when import is accidentally repeated.
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(content)
    save_state(film, path, config)
    return {'ok': True, 'action': 'import', 'script': path.name, 'lines': len(config['lines'])}


def load_script(film, name=None):
    state = state_for(film)
    if state and name and name != state['script']:
        raise ValueError('The managed script is ' + state['script'])
    path = script_path(film, name or (state['script'] if state else 'SCRIPT.md'))
    config = parse(path.read_text(encoding='utf-8-sig'))
    check_references(film, config)
    return state, path, config


def export_script(film, name=None, dry_run=False):
    state, path, config = load_script(film, name)
    destination = film / 'narration.json'
    old = read_json(destination) if destination.exists() else None
    changed = old is None or digest(old) != digest(config)
    if old is not None and changed and (not state or digest(old) != state['narrationSha256']):
        raise ValueError('narration.json changed outside writing; reconcile it with the manuscript before exporting')
    old_rows = {row['id']: row for row in old.get('lines', [])} if isinstance(old, dict) else {}
    new_rows = {row['id']: row for row in config['lines']}
    result = {'ok': True, 'action': 'export', 'dryRun': dry_run, 'changed': changed,
              'script': path.name, 'lines': len(new_rows),
              'changedLines': [key for key, row in new_rows.items()
                               if key not in old_rows or digest(old_rows[key]) != digest(row)],
              'removedLines': [key for key in old_rows if key not in new_rows],
              'requiresAudioRefresh': changed}
    if not dry_run:
        if changed:
            atomic_write(destination, json.dumps(config, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
        # A crash between narration and state writes is recoverable by repeating the same export.
        save_state(film, path, config)
    return result


def check_project(film):
    state, path, config = load_script(film)
    actual = read_json(film / 'narration.json')
    if digest(actual) != digest(config):
        raise ValueError(f'{path.name} and narration.json disagree; run writing export before production')
    if state is None or digest(actual) != state['narrationSha256']:
        raise ValueError('Writing export state is missing or stale; run writing export')
    return {'ok': True, 'action': 'check', 'script': path.name, 'lines': len(config['lines']),
            'scope': 'format, anchors.json references, narration synchronization; no listening or math review'}


def check_if_managed(film):
    if (film / STATE).exists():
        return check_project(film)
    return None


def check_prepared(source, destination):
    """Custom builders must carry the current managed text into the actual bundle."""
    managed = check_if_managed(source)
    if managed and not (destination / STATE).is_file():
        raise ValueError('Prepared bundle lacks writing files; copy the managed manuscript, .writing.json and narration.json')
    check_if_managed(destination)
    if managed and digest(read_json(source / 'narration.json')) != digest(read_json(destination / 'narration.json')):
        raise ValueError('Prepared bundle contains an older narration than the source manuscript')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ('import', 'export', 'check'):
        sub = commands.add_parser(command)
        sub.add_argument('film', type=Path, help='Project source directory, not a registry ID')
        if command != 'check':
            sub.add_argument('--script', help='Local Markdown filename')
        if command == 'import':
            sub.add_argument('--title', default='口播稿')
        if command == 'export':
            sub.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    try:
        film = args.film.resolve()
        if not film.is_dir():
            raise ValueError('Project directory does not exist: ' + str(film))
        if args.command == 'import':
            result = import_script(film, args.script or 'SCRIPT.md', args.title)
        elif args.command == 'export':
            result = export_script(film, args.script, args.dry_run)
        else:
            result = check_project(film)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
