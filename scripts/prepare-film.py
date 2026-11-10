"""Prepare shared libraries and font subsets inside a portable film bundle.

Workspace entry: shuyu prepare <project>
Direct helper: python scripts/prepare-film.py output/<project>/project

HyperFrames resolves assets only inside the film folder (no ../ paths, no
network), so each film carries its own copies. Re-run after editing a shared
library or adding new on-screen text. Needs `npm ci` in tools/shuyuvideo.
"""
import re
import shutil
import sys
from pathlib import Path

from font_assets import build_subset
import json

REPO = Path(__file__).resolve().parents[1]
NPM = REPO / 'node_modules'
FILES = {
    'vendor/gsap.min.js': NPM / 'gsap/dist/gsap.min.js',
    'vendor/katex/katex.min.js': NPM / 'katex/dist/katex.min.js',
    'vendor/katex/katex.min.css': NPM / 'katex/dist/katex.min.css',
    'lib/omega-shape.js': REPO / 'character/lib/omega-shape.js',
    'lib/omega.js': REPO / 'character/lib/omega.js',
    'lib/stage.js': REPO / 'character/stage.js',
    'lib/camera.js': REPO / 'motion/runtime/camera.js',
    'lib/travel.js': REPO / 'motion/runtime/travel.js',
    'lib/tex.js': REPO / 'style/adapters/tex.js',
    'lib/sanlian.js': REPO / 'brand/lib/sanlian.js',
    'style/tokens.css': REPO / 'style/tokens.css',
}
BUNDLES = {
    # Preserve the published file and legacy check API without duplicating
    # the continuity implementation in the animation runtime.
    'lib/transitions.js': (
        REPO / 'motion/checks/continuity.js',
        REPO / 'motion/runtime/transitions.js',
    ),
}
FONTS = [('shuyu', 'sans'), ('shuyu-bold', 'sans-bold')]


def prepare_libraries(assets):
    for target, source in FILES.items():
        dest = assets / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        if target == 'vendor/katex/katex.min.css':
            # KaTeX_Main is shipped below. HyperFrames otherwise resolves the
            # unused Times fallback to remote EB Garamond and can stall offline.
            css = dest.read_text(encoding='utf-8')
            dest.write_text(css.replace('KaTeX_Main,Times New Roman,serif',
                                       'KaTeX_Main,serif'), encoding='utf-8')
    for target, sources in BUNDLES.items():
        dest = assets / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text('\n;\n'.join(source.read_text(encoding='utf-8') for source in sources), encoding='utf-8')


def main(film):
    assets = film / 'assets'
    prepare_libraries(assets)
    fonts = assets / 'vendor/katex/fonts'
    fonts.mkdir(parents=True, exist_ok=True)
    for f in (NPM / 'katex/dist/fonts').glob('*.woff2'):
        shutil.copy2(f, fonts / f.name)

    # Text written by scripts (labels, captions) needs glyphs too; vendored and
    # copied library files under assets/ are not film text.
    pages = [film / 'index.html', *sorted((film / 'compositions').rglob('*.html')),
             *sorted(film.glob('*.js')), *sorted((film / 'compositions').rglob('*.js'))]
    text = ''.join(p.read_text(encoding='utf-8') for p in pages if p.exists())
    text = ''.join(sorted(set(re.findall(r'[^\x00-\x7f]', text)))) + ''.join(map(chr, range(32, 127)))
    (assets / 'fonts').mkdir(parents=True, exist_ok=True)
    records = [build_subset(source, text, assets / 'fonts' / f'{name}.woff2') for name, source in FONTS]
    (assets / 'fonts/manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    shutil.copy2(NPM / 'katex/LICENSE', assets / 'vendor/katex/LICENSE')
    # The npm GSAP package declares its license in package.json and README;
    # it does not ship a standalone LICENSE file in this pinned release.
    gsap_package = json.loads((NPM / 'gsap/package.json').read_text(encoding='utf-8'))
    gsap_notice = (NPM / 'gsap/README.md').read_text(encoding='utf-8').split('### License', 1)[1].strip()
    (assets / 'vendor/GSAP-NOTICE.txt').write_text(
        f"GSAP {gsap_package['version']}\n\n{gsap_notice}\n", encoding='utf-8')
    print(f'prepared {len(FILES) + len(BUNDLES)} libraries and KaTeX fonts; font subset has {len(text)} characters')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(Path(sys.argv[1]).resolve())
