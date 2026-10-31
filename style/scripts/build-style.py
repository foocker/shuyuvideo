"""Generate CSS/JS and contrast evidence from tokens.json; optionally sample existing films.

Run: python style/scripts/build-style.py [--references]
No original compositions or video files are modified.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

STYLE = Path(__file__).resolve().parents[1]
ROOT = STYLE.parent


def luminance(h):
    rgb = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]
    lin = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in rgb]
    return sum(x * w for x, w in zip(lin, (.2126, .7152, .0722)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--references', action='store_true')
    args = parser.parse_args()
    tokens = json.loads((STYLE / 'tokens.json').read_text(encoding='utf-8'))
    assert set(tokens['colors']) == set(tokens['roles'])
    for key, value in tokens['colors'].items():
        assert re.fullmatch(r'#[0-9A-Fa-f]{6}', value), key
    for key, role in tokens['roles'].items():
        source = ROOT / role['source'].rsplit(':', 1)[0]
        assert source.is_file(), source
        # All v1 colors are exact source literals, not sampled display colors.
        content = source.read_text(encoding='utf-8').lower()
        assert tokens['colors'][key][1:].lower() in content, (key, source)
    css = ['/* Generated from tokens.json by scripts/build-style.py. */', ':root {']
    for key, value in tokens['colors'].items():
        kebab = re.sub(r'([A-Z])', lambda m: '-' + m[1].lower(), key)
        css.append(f'  --shuyu-{kebab}: {value};')
    css.extend(['  --shuyu-font: "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;', '}'])
    (STYLE / 'tokens.css').write_text('\n'.join(css) + '\n', encoding='utf-8')
    (STYLE / 'tokens.js').write_text('// Generated from tokens.json; do not edit.\nwindow.ShuyuStyle = ' + json.dumps(tokens, ensure_ascii=False, indent=2) + ';\n', encoding='utf-8')
    bg = luminance(tokens['colors']['background'])
    ratios = {}
    for key, value in tokens['colors'].items():
        fg = luminance(value)
        ratio = (max(bg, fg) + .05) / (min(bg, fg) + .05)
        ratios[key] = {'color': value, 'ratio': round(ratio, 3), 'normalText45': ratio >= 4.5, 'largeTextOrGraphic3': ratio >= 3}
    assert all(ratios[k]['normalText45'] for k in tokens['policy']['smallTextRoles'])
    out = STYLE / 'evidence'
    out.mkdir(exist_ok=True)
    (out / 'contrast.json').write_text(json.dumps({'background': tokens['colors']['background'], 'method': 'sRGB relative luminance (WCAG contrast). Flat opaque colors only; not a certification of animated/video accessibility.', 'roles': ratios}, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.references:
        records = []
        for name, relative, time in [
            ('glyph', 'films/topology-mistakes/output/topology-mistakes-final.mp4', 33),
            ('mobius', 'films/mobius/renders/mobius.mp4', 108),
            ('human', 'films/human-to-sphere/renders/human-to-sphere-revised.mp4', 40),
            ('unlock', 'films/topology-unlock/output/topology-unlock-final.mp4', 30.5),
            ('definition', 'films/human-to-sphere/film/output/human-to-sphere-story-final.mp4', 147),
            ('omega', 'character/output/shuyu-omega-showcase.mp4', 2),
        ]:
            video = ROOT / relative
            dest = out / (name + '.jpg')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(time), '-i', str(video), '-frames:v', '1', '-vf', 'scale=960:-2', '-q:v', '2', str(dest)], check=True)
            with video.open('rb') as fp:
                sha = hashlib.file_digest(fp, 'sha256').hexdigest()
            records.append({'id': name, 'video': relative, 'timeSeconds': time, 'videoSha256': sha, 'image': 'evidence/' + dest.name})
        (out / 'references.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Generated tokens.css, tokens.js and contrast.json. All source color references verified.')


if __name__ == '__main__':
    main()
