"""Capture a standalone local GSAP scene and test reverse-seek determinism.

Configuration paths are relative to the config file. This does not mount
HyperFrames sub-compositions or implement its audio/video timing.
"""
import argparse
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import math
from pathlib import Path
import sys
import threading
from urllib.parse import quote, urlsplit

from PIL import Image, ImageChops, ImageDraw
from playwright.sync_api import sync_playwright


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def difference(first, second):
    a, b = Image.open(io.BytesIO(first)).convert('RGBA'), Image.open(io.BytesIO(second)).convert('RGBA')
    if a.size != b.size:
        raise ValueError(f'Image size mismatch: {a.size} vs {b.size}')
    # Compare every channel including alpha; Image.getbbox on RGBA alone can
    # overlook an RGB difference when alpha is identical.
    delta = ImageChops.difference(a, b)
    maxima = [channel.getextrema()[1] for channel in delta.split()]
    return {'identical': max(maxima) == 0, 'maxChannelDelta': max(maxima)}


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def run(config_path, out, browser_path=None):
    config = json.loads(config_path.read_text(encoding='utf-8'))
    root = config_path.resolve().parent
    html = (root / config['html']).resolve()
    if not html.is_relative_to(root) or not html.is_file():
        raise ValueError('html must be an existing file below the config directory')
    times = config['times']
    if not isinstance(times, list) or not times or any(not numeric(t) or t < 0 for t in times):
        raise ValueError('times must contain finite, non-negative seconds')
    if times != sorted(set(times)):
        raise ValueError('times must be unique and increasing')
    assertions = config.get('assertions', [])
    for assertion in assertions:
        if assertion['time'] not in times or not numeric(assertion['equals']) or not numeric(assertion.get('tolerance', 0)) or assertion.get('tolerance', 0) < 0:
            raise ValueError('assertions need a sampled time, finite equals and non-negative tolerance')
        if assertion['source'] not in ('attribute', 'style'):
            raise ValueError('assertion source must be attribute or style')
    out.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(root)))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    origin = f'http://127.0.0.1:{server.server_port}'
    url = origin + '/' + quote(html.relative_to(root).as_posix())
    errors, rows, first_frames, runtime_errors, blocked = [], [], [], [], []
    try:
        with sync_playwright() as playwright:
            options = {'headless': True}
            if browser_path:
                options['executable_path'] = str(browser_path)
            else:
                options['channel'] = config.get('browserChannel', 'chrome')
            browser = playwright.chromium.launch(**options)
            try:
                context = browser.new_context(viewport={'width': config.get('width', 1920), 'height': config.get('height', 1080)}, device_scale_factor=1, service_workers='block')
                def route_request(route):
                    parsed = urlsplit(route.request.url)
                    if route.request.url.startswith(origin + '/') or parsed.scheme in ('data', 'blob'):
                        route.continue_()
                    else:
                        blocked.append(route.request.url)
                        route.abort()
                context.route('**/*', route_request)
                page = context.new_page()
                page.on('pageerror', lambda error: runtime_errors.append(str(error)))
                page.on('response', lambda response: runtime_errors.append(f'HTTP {response.status}: {response.url}') if response.status >= 400 else None)
                page.goto(url, wait_until='load')
                if page.locator('[data-composition-src]').count() or page.locator('template').count() or page.locator('video,audio').count():
                    raise ValueError('Use HyperFrames check/snapshot for nested compositions, templates or timed media')
                key = config['timeline']
                page.wait_for_function('key => !!window.__timelines?.[key]', arg=key, timeout=10000)
                page.evaluate('async () => { await document.fonts.ready; await Promise.all([...document.images].map(i => i.decode())); }')
                duration = page.evaluate('key => window.__timelines[key].totalDuration()', key)
                if not numeric(duration) or duration <= 0 or times[-1] > duration:
                    raise ValueError(f'Samples exceed finite timeline duration {duration}')
                selector = config.get('root', '#root')
                if page.locator(selector).count() != 1:
                    raise ValueError('root selector must match exactly one element')

                def seek(t):
                    page.evaluate('([key,t]) => { const tl=window.__timelines[key]; tl.pause(); tl.totalTime(t,false); gsap.ticker.sleep(); }', [key, t])
                    page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')

                for index, t in enumerate(times):
                    seek(t)
                    samples = []
                    for rule in (a for a in assertions if a['time'] == t):
                        value = page.evaluate('r => { const nodes=document.querySelectorAll(r.selector); if(nodes.length!==1) throw Error("Assertion selector must match one element: "+r.selector); return r.source==="attribute" ? nodes[0].getAttribute(r.property) : getComputedStyle(nodes[0]).getPropertyValue(r.property); }', rule)
                        try:
                            actual = float(value)
                            passed = math.isfinite(actual) and abs(actual - rule['equals']) <= rule.get('tolerance', 0)
                        except (ValueError, TypeError):
                            passed = False
                        samples.append({**rule, 'actual': value, 'passed': passed})
                        if not passed:
                            errors.append(f'Assertion failed at {t}: {rule["selector"]} {rule["property"]} = {value}')
                    png = page.locator(selector).screenshot(timeout=10000)
                    name = f'frame-{index:03}.png'
                    (out / name).write_bytes(png)
                    first_frames.append(png)
                    rows.append({'time': t, 'image': name, 'sha256': hashlib.sha256(png).hexdigest(), 'assertions': samples})
                # Move elsewhere before every repeat, including the last sample.
                for index in reversed(range(len(times))):
                    seek(duration if times[index] < duration / 2 else 0)
                    seek(times[index])
                    comparison = difference(first_frames[index], page.locator(selector).screenshot(timeout=10000))
                    rows[index]['reverseSeek'] = comparison
                    if not comparison['identical']:
                        errors.append(f'Reverse seek differs at {times[index]} seconds')
                if config.get('reference'):
                    reference = (root / config['reference']).resolve()
                    if not reference.is_relative_to(root):
                        raise ValueError('reference must be below the config directory')
                    final_diff = difference(first_frames[-1], reference.read_bytes())
                    if not final_diff['identical']:
                        errors.append('Final frame differs from the declared reference')
                else:
                    final_diff = None
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
    errors.extend(runtime_errors)
    if blocked:
        errors.append('External resource requests were blocked: ' + ', '.join(sorted(set(blocked))))
    # Film strip is evidence for human inspection, never an aesthetic score.
    width, height = 480, 290
    strip = Image.new('RGB', (width * min(3, len(rows)), height * math.ceil(len(rows) / 3)), '#F4F2EC')
    draw = ImageDraw.Draw(strip)
    for i, (row, png) in enumerate(zip(rows, first_frames)):
        frame = Image.open(io.BytesIO(png)).convert('RGB')
        frame.thumbnail((width, height - 25))
        x, y = i % 3 * width, i // 3 * height
        strip.paste(frame, (x, y + 25))
        draw.text((x + 10, y + 5), f'{row["time"]:.3f}s', fill='#203B35')
    strip.save(out / 'contact-sheet.png')
    return {'ok': not errors, 'errors': errors, 'samples': rows, 'finalComparison': final_diff,
            'scope': 'Standalone GSAP scene: sampled assertions and reverse-seek pixels; not continuous playback or mathematical proof.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--browser', type=Path, help='Existing Chrome/Chromium executable')
    args = parser.parse_args()
    try:
        report = run(args.config, args.out, args.browser)
    except Exception as exc:
        report = {'ok': False, 'errors': [str(exc)]}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': report['ok'], 'errors': report['errors'], 'report': str(args.out / 'report.json')}, ensure_ascii=False))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
