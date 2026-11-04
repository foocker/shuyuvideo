"""Find production traces in on-screen text before rendering.

Usage: python scripts/validation/screen_text.py <project-dir> [--report <report.json>]

Scans text nodes in index.html and compositions/ (including <template> content)
and string literals with Chinese text in inline and composition scripts. Text
in data-tex attributes is TeX for KaTeX and is checked only for Chinese
characters outside \\text{}. Mark an element data-literal-text when its symbols
are plain text, not a formula (e.g. an artwork size 34 × 47 cm). Static scan: text built at runtime from numbers or
hidden by animation is not seen; frames still need a visual check.
"""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

CJK = re.compile(r'[\u3400-\u9fff\uf900-\ufaff]')
RULES = [
    ('mojibake', re.compile(r'\ufffd|\?{2,}'), 'replacement character or repeated ?'),
    ('bare-tex', re.compile(r'\\[A-Za-z]+|\$[^$]*\$|[\^_]\{'), 'TeX source outside data-tex'),
    ('unicode-math', re.compile(r'[\u00b2\u00b3\u00b9\u2070-\u209f\u2212\u221a\u2211\u220f\u222b\u221e'
                                r'\u2264\u2265\u2260\u2248\u22ef\u00d7\u00f7\u03b1-\u03c9]'),
     'Unicode stand-in for a formula; write it as TeX in data-tex'),
    ('production-note', re.compile(r'TODO|FIXME|TBD|placeholder|占位|待定|待补|镜头\s*\d|[Ss]hot\s*\d|\bS\d{1,2}\b'),
     'production note or shot number'),
]
# In Chinese text an ASCII ? or / usually means lost characters or an editing note.
CJK_RULES = [
    ('mojibake', re.compile(r'\?'), 'ASCII ? in Chinese text; use ？ or fix the encoding'),
    ('production-note', re.compile(r'/|／'), 'slash-separated note in Chinese text'),
]
TAG = re.compile(r'<[^<>]+>')
STRING = re.compile(r"'((?:[^'\\\n]|\\.)*)'|\"((?:[^\"\\\n]|\\.)*)\"|`((?:[^`\\]|\\.)*)`")


class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.texts, self.scripts, self.tex = [], [], [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in ('br', 'img', 'meta', 'link', 'source', 'input', 'hr'):
            self.stack.append((tag, 'data-literal-text' in attrs))
        if attrs.get('data-tex'):
            self.tex.append((self.getpos()[0], attrs['data-tex']))

    def handle_endtag(self, tag):
        if any(name == tag for name, _ in self.stack):
            while self.stack and self.stack.pop()[0] != tag:
                pass

    def handle_data(self, data):
        line = self.getpos()[0]
        tags = [name for name, _ in self.stack]
        if 'script' in tags:
            self.scripts.append((line, data))
        elif 'style' not in tags and data.strip():
            self.texts.append((line, data.strip(), any(literal for _, literal in self.stack)))


def problems(value, literal=False):
    found = [(rule, note) for rule, pattern, note in RULES
             if pattern.search(value) and not (literal and rule == 'unicode-math')]
    if CJK.search(value):
        seen = {rule for rule, _ in found}
        found += [(rule, note) for rule, pattern, note in CJK_RULES if rule not in seen and pattern.search(value)]
    return found


def script_strings(code, first_line):
    for match in STRING.finditer(code):
        value = next(g for g in match.groups() if g is not None)
        # Only strings with Chinese are likely to reach the screen; selectors,
        # easing names and TeX passed to KaTeX are skipped.
        if CJK.search(value) and '${' not in value:
            # Markup inside the string is not visible text; drop tags before checking.
            yield first_line + code.count('\n', 0, match.start()), TAG.sub(' ', value), False


def scan_file(path, root):
    rel = path.relative_to(root).as_posix()
    source = path.read_text(encoding='utf-8', errors='replace')
    if '\ufffd' in source:
        yield {'file': rel, 'line': 1, 'rule': 'mojibake', 'note': 'file is not valid UTF-8', 'text': ''}
    if path.suffix == '.js':
        candidates, tex = list(script_strings(source, 1)), []
    else:
        collector = Collector()
        collector.feed(source)
        candidates = list(collector.texts)
        for line, code in collector.scripts:
            candidates += script_strings(code, line)
        tex = collector.tex
    for line, value, literal in candidates:
        for rule, note in problems(value, literal):
            yield {'file': rel, 'line': line, 'rule': rule, 'note': note, 'text': value[:80]}
    for line, value in tex:
        if CJK.search(re.sub(r'\\(?:text|mathrm|textbf)\{[^{}]*\}', '', value)):
            yield {'file': rel, 'line': line, 'rule': 'tex-cjk', 'note': 'Chinese in TeX must be inside \\text{}',
                   'text': value[:80]}


def scan(root):
    root = Path(root).resolve()
    files = [root / 'index.html', *sorted((root / 'compositions').rglob('*.html')),
             *sorted((root / 'compositions').rglob('*.js'))]
    return [item for path in files if path.is_file() for item in scan_file(path, root)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    findings = scan(args.project)
    report = {'ok': not findings, 'kind': 'screen-text', 'findings': findings,
              'scope': 'Static scan of authored on-screen text; runtime-built text and frames need visual review.'}
    content = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(content + '\n', encoding='utf-8')
    print(content)
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
