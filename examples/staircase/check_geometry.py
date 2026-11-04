"""Check the final staircase tiling using actual browser bounding rectangles.

This example uses axis-aligned squares at the final 180-degree rotation.
Bounding rectangles are not a general test for arbitrary rotated polygons.
"""
import argparse
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from workspace import output_dir


def tiling_errors(blocks, container, tolerance=0.01):
    errors = []
    for box in [container, *blocks]:
        if (any(not math.isfinite(box[k]) for k in ('x', 'y', 'width', 'height'))
                or box['width'] <= 0 or box['height'] <= 0):
            return ['Non-finite or empty rectangle']
    for i, a in enumerate(blocks):
        if (a['x'] < container['x'] - tolerance or a['y'] < container['y'] - tolerance
                or a['x'] + a['width'] > container['x'] + container['width'] + tolerance
                or a['y'] + a['height'] > container['y'] + container['height'] + tolerance):
            errors.append(f'Block {i} extends outside the rectangle')
        for j, b in enumerate(blocks[:i]):
            dx = min(a['x'] + a['width'], b['x'] + b['width']) - max(a['x'], b['x'])
            dy = min(a['y'] + a['height'], b['y'] + b['height']) - max(a['y'], b['y'])
            if dx > tolerance and dy > tolerance:
                errors.append(f'Blocks {j} and {i} overlap')
    area = sum(b['width'] * b['height'] for b in blocks)
    if abs(area - container['width'] * container['height']) > tolerance:
        errors.append('Block area does not cover the rectangle exactly')
    return errors


def main():
    from playwright.sync_api import sync_playwright

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', type=Path)
    args = parser.parse_args()
    out = output_dir('staircase-test')
    with sync_playwright() as playwright:
        options = {'executable_path': str(args.browser)} if args.browser else {'channel': 'chrome'}
        browser = playwright.chromium.launch(headless=True, **options)
        try:
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.goto((out / 'index.html').as_uri(), wait_until='load')
            geometry = page.evaluate('''() => {
                const tl = window.__timelines.stairs;
                tl.pause().totalTime(tl.totalDuration(), false);
                gsap.ticker.sleep();
                const box = el => { const {x,y,width,height} = el.getBoundingClientRect();
                    return {x,y,width,height}; };
                return {blocks: [...document.querySelectorAll('.fig-block')].map(box),
                    container: box(document.querySelector('.fig-rect'))};
            }''')
        finally:
            browser.close()
    errors = tiling_errors(**geometry)
    if len(geometry['blocks']) != 20:
        errors.append('Expected two ten-block staircases')
    report = {'ok': not errors, 'errors': errors, **geometry,
              'scope': 'Final axis-aligned block boxes: contained, disjoint and equal total area; borders and rounded paint excluded.'}
    path = out / 'geometry-report.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': report['ok'], 'errors': errors, 'report': str(path)}))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
