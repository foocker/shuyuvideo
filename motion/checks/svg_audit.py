"""Report local SVG path tangents and complexity; corners remain a design decision."""
import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib.path import parse_path

TOKEN = re.compile(r'[MmZzLlHhVvCcSsQqTtAa]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?|[\s,]+')


def vector(a, b):
    return b[0] - a[0], b[1] - a[1]


def angle(a, b):
    size = math.hypot(*a) * math.hypot(*b)
    return None if size < 1e-12 else math.degrees(math.acos(max(-1, min(1, (a[0] * b[0] + a[1] * b[1]) / size))))


def inspect_path(data, threshold):
    # The fontTools parser supports arcs and smooth commands. Reject unknown
    # characters first so tokenization cannot silently drop a bad command.
    if TOKEN.sub('', data):
        raise ValueError('unrecognized SVG path token')
    pen = RecordingPen()
    parse_path(data, pen)
    current = origin = None
    first_tangent = previous = None
    segments, warnings, line_lengths = 0, [], []
    for op, points in pen.value:
        if any(not math.isfinite(n) for point in points for n in point):
            raise ValueError('path has non-finite coordinates')
        if op == 'moveTo':
            current = origin = points[0]
            first_tangent = previous = None
            continue
        if op == 'endPath':
            current = previous = first_tangent = None
            continue
        closing = op == 'closePath'
        if closing:
            if current != origin:
                points = (origin,)
            else:
                a = angle(previous, first_tangent) if previous and first_tangent else None
                if a is not None and a > threshold:
                    warnings.append({'kind': 'tangent-change', 'segment': segments, 'degrees': round(a, 3), 'closure': True})
                current = previous = first_tangent = None
                continue
        if current is None or not points:
            raise ValueError('segment without a start point')
        start = next((vector(current, p) for p in points if p != current), (0, 0))
        chain = (current, *points)
        end = next((vector(p, points[-1]) for p in reversed(chain[:-1]) if p != points[-1]), (0, 0))
        if previous:
            a = angle(previous, start)
            if a is not None and a > threshold:
                warnings.append({'kind': 'tangent-change', 'segment': segments, 'degrees': round(a, 3)})
        if first_tangent is None:
            first_tangent = start
        if math.hypot(*start) < 1e-12:
            warnings.append({'kind': 'degenerate-segment', 'segment': segments})
        if op == 'lineTo' or closing:
            line_lengths.append(math.dist(current, points[-1]))
        previous, current = end, points[-1]
        segments += 1
        if closing:
            a = angle(previous, first_tangent) if previous and first_tangent else None
            if a is not None and a > threshold:
                warnings.append({'kind': 'tangent-change', 'segment': segments, 'degrees': round(a, 3), 'closure': True})
            current = previous = first_tangent = None
    tiny = sum(length <= 1 for length in line_lengths)
    if len(line_lengths) >= 20 and tiny / len(line_lengths) >= .75:
        warnings.append({'kind': 'many-tiny-lines', 'count': tiny, 'note': 'Local SVG units; inspect enlarged before deciding.'})
    if not segments:
        raise ValueError('path contains no drawable segments')
    return {'segments': segments, 'lineSegments': len(line_lengths), 'warnings': warnings}


def audit(path, threshold=8):
    document = ET.parse(path).getroot()
    if document.tag.rsplit('}', 1)[-1] != 'svg':
        raise ValueError('input is not an SVG document')
    results, errors = [], []
    for index, node in enumerate(document.iter()):
        if node.tag.rsplit('}', 1)[-1] != 'path':
            continue
        label = node.get('id', f'path-{index}')
        try:
            item = inspect_path(node.get('d', ''), threshold)
            results.append({'id': label, **item})
        except (ValueError, IndexError, KeyError, TypeError, AssertionError) as exc:
            errors.append(f'{label}: {exc}')
    if not results and not errors:
        errors.append('No path geometry found; text, rects and external use references are not path-audited')
    return {'ok': not errors, 'paths': results, 'errors': errors,
            'scope': 'Path-local geometry. Transforms, masks, fonts, intersections and rendered appearance require separate inspection.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('svg', type=Path)
    parser.add_argument('--angle', type=float, default=8)
    parser.add_argument('--strict', action='store_true', help='Fail on advisory geometry warnings too; use only for paths intended to be smooth')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        if not math.isfinite(args.angle) or not 0 <= args.angle <= 180:
            raise ValueError('--angle must be between 0 and 180 degrees')
        report = audit(args.svg, args.angle)
        if args.strict and any(item['warnings'] for item in report['paths']):
            report['ok'] = False
    except (OSError, ValueError, ET.ParseError) as exc:
        report = {'ok': False, 'errors': [str(exc)]}
    content = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(content + '\n', encoding='utf-8')
    print(content)
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
