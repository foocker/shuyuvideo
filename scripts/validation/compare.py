"""Open two local video intervals for pacing, picture and sound review."""
import argparse
from html import escape
import math
from pathlib import Path
import subprocess

from render_check import probe


def video_panel(path, span, label):
    source = path.resolve(strict=True)
    info = probe(source)
    stream = next((row for row in info.get('streams', []) if row['codec_type'] == 'video'), None)
    if not stream:
        raise ValueError(f'No video stream: {path}')
    duration = float(stream.get('duration') or info['format']['duration'])
    start, end = span or (0, duration)
    if not math.isfinite(duration) or not 0 <= start < end <= duration:
        raise ValueError(f'{path.name}: use 0 <= start < end <= {duration:g} seconds')
    return f"""<section><h2>{label}</h2><p>{escape(path.name)} · {start:.2f}–{end:.2f} 秒</p>
<video controls playsinline preload="metadata" muted data-start="{start}" data-end="{end}"
src="{escape(source.as_uri(), quote=True)}"></video></section>"""


def compare(reference, trial, output, reference_at=None, trial_at=None):
    panels = [video_panel(reference, reference_at, '原片'), video_panel(trial, trial_at, '试作')]
    template = Path(__file__).with_name('compare.html').read_text(encoding='utf-8')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(template.replace('<!-- videos -->', '\n'.join(panels)), encoding='utf-8')
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('trial', type=Path)
    parser.add_argument('--reference-at', nargs=2, type=float, metavar=('START', 'END'))
    parser.add_argument('--trial-at', nargs=2, type=float, metavar=('START', 'END'))
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.output.suffix.lower() not in ('.html', '.htm'):
            raise ValueError('--output must be an HTML filename')
        print(compare(args.reference, args.trial, args.output, args.reference_at, args.trial_at))
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, str(exc) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
