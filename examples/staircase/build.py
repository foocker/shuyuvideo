"""Build a standalone test page from the existing staircase shot snapshot.

Uses repository assets only. Generated fonts/vendor files and reports stay in output/.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from workspace import output_dir


def main():
    out = output_dir('staircase-test')
    out.mkdir(parents=True, exist_ok=True)
    template = (HERE / 'scene.html').read_text(encoding='utf-8')
    contents = re.search(r'<template>(.*?)</template>', template, re.S).group(1)
    contents = contents.replace('data-composition-id="stairs"', 'data-composition-id="stairs" data-start="0" data-duration="24.25" data-fps="60"')
    page = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>台阶求和：动作验证</title>
<link rel="stylesheet" href="assets/vendor/katex/katex.min.css">
<link rel="stylesheet" href="assets/style/tokens.css">
<link rel="stylesheet" href="assets/figure.css">
<style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#F4F2EC}</style>
<script src="assets/vendor/gsap.min.js"></script>
<script src="assets/vendor/katex/katex.min.js"></script>
<script src="assets/lib/tex.js"></script>
<script src="assets/lib/camera.js"></script>
<script src="assets/lib/transitions.js"></script>
<script src="assets/figure.js"></script>
<script src="assets/anchors.js"></script>
</head><body>''' + contents + '</body></html>'
    (out / 'index.html').write_text(page, encoding='utf-8')
    subprocess.run([sys.executable, str(ROOT / 'scripts/prepare-film.py'), str(out)], check=True)
    for name in ('figure.js', 'figure.css'):
        shutil.copy2(HERE / name, out / 'assets' / name)
    anchors = json.loads((HERE / 'anchors.resolved.json').read_text(encoding='utf-8'))
    (out / 'assets/anchors.js').write_text('window.ANCHORS = ' + json.dumps(anchors) + ';\n', encoding='utf-8')
    # The exact brace path from the real geometry is covered by the SVG auditor.
    (out / 'brace.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080"><path id="width-brace" d="M700 942 C700 962 880 942 880 962 M1060 942 C1060 962 880 942 880 962" fill="none" stroke="#203B35"/></svg>\n', encoding='utf-8')
    config = {'html': 'index.html', 'timeline': 'stairs', 'root': '#stairs', 'width': 1920, 'height': 1080,
              'times': [0, 7.3, 11.9, 13.685, 14.52, 15.0, 19.174, 19.424, 19.924, 24.25],
              'assertions': [
                  {'time': 15.0, 'selector': '.fig-copy', 'source': 'style', 'property': 'opacity', 'equals': 1, 'tolerance': 0},
                  {'time': 19.174, 'selector': '.fig-rect', 'source': 'attribute', 'property': 'stroke-dashoffset', 'equals': 87.5, 'tolerance': .01},
                  {'time': 19.424, 'selector': '.fig-rect', 'source': 'attribute', 'property': 'stroke-dashoffset', 'equals': 50, 'tolerance': .01},
                  {'time': 19.924, 'selector': '.fig-rect', 'source': 'attribute', 'property': 'stroke-dashoffset', 'equals': 0, 'tolerance': .01}]}
    (out / 'probe.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    asset = {'id': 'staircase-geometry', 'role': 'mathematical-diagram', 'path': 'assets/figure.js',
             'kind': 'project-original', 'source': 'shuyuvideo/films/staircase-sum/assets/figure.js',
             'license': 'project-internal', 'sha256': hashlib.sha256((out / 'assets/figure.js').read_bytes()).hexdigest()}
    (out / 'asset-manifest.json').write_text(json.dumps({'schema': 'shuyu-assets/v1', 'intendedUse': 'study', 'assets': [asset]}, indent=2), encoding='utf-8')
    # 24.25 s is not an integer number of frames at 30 fps; this standalone
    # audit samples 60 fps for 1455 frames, without changing the source clock.
    timeline = {'schema': 'shuyu-timeline/v1', 'fps': 60, 'durationFrames': 1455,
                'shots': [{'id': 'stairs', 'startFrame': 0, 'endFrame': 1455,
                           'subject': '两道同样的台阶', 'action': '复制、翻转并拼成长方形',
                           'readFrames': 30, 'assets': ['staircase-geometry']}]}
    (out / 'timeline.json').write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding='utf-8')
    print(out)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
