"""Copy shared libraries into a film and subset its Chinese font.

Usage: python scripts/prepare-film.py films/<name>

HyperFrames resolves assets only inside the film folder (no ../ paths, no
network), so each film carries its own copies. Re-run after editing a shared
library or adding new on-screen text. Needs `npm ci` in tools/shuyuvideo.
"""
import re
import shutil
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

REPO = Path(__file__).resolve().parents[1]
NPM = REPO / 'node_modules'
FILES = {
    'vendor/gsap.min.js': NPM / 'gsap/dist/gsap.min.js',
    'vendor/katex/katex.min.js': NPM / 'katex/dist/katex.min.js',
    'vendor/katex/katex.min.css': NPM / 'katex/dist/katex.min.css',
    'lib/omega-shape.js': REPO / 'character/lib/omega-shape.js',
    'lib/omega.js': REPO / 'character/lib/omega.js',
    'lib/stage.js': REPO / 'character/stage.js',
    'lib/camera.js': REPO / 'camera/camera.js',
    'lib/transitions.js': REPO / 'transitions/transitions.js',
    'lib/tex.js': REPO / 'style/adapters/tex.js',
    'style/tokens.css': REPO / 'style/tokens.css',
}
FONTS = [('shuyu', 'msyh.ttc'), ('shuyu-bold', 'msyhbd.ttc')]


def main(film):
    assets = film / 'assets'
    for target, source in FILES.items():
        dest = assets / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    fonts = assets / 'vendor/katex/fonts'
    fonts.mkdir(parents=True, exist_ok=True)
    for f in (NPM / 'katex/dist/fonts').glob('*.woff2'):
        shutil.copy2(f, fonts / f.name)

    pages = [film / 'index.html', *sorted((film / 'compositions').glob('*.html'))]
    text = ''.join(p.read_text(encoding='utf-8') for p in pages if p.exists())
    text = ''.join(sorted(set(re.findall(r'[^\x00-\x7f]', text)))) + ''.join(map(chr, range(32, 127)))
    (assets / 'fonts').mkdir(parents=True, exist_ok=True)
    for name, source in FONTS:
        font = TTFont(Path('C:/Windows/Fonts') / source, fontNumber=0)
        sub = subset.Subsetter(options=subset.Options())
        sub.populate(text=text)
        sub.subset(font)
        font.flavor = 'woff2'
        font.save(assets / 'fonts' / f'{name}.woff2')
    print(f'copied {len(FILES)} libraries and KaTeX fonts; font subset has {len(text)} characters')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(Path(sys.argv[1]).resolve())
