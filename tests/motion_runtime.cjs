const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const { gsap } = require('gsap');

// Load exactly the two published scripts existing films already reference.
const assets = process.argv[2];
for (const name of ['camera.js', 'transitions.js']) {
  vm.runInThisContext(readFileSync(path.join(assets, 'lib', name), 'utf8'));
}
const camera = globalThis.ShuyuCamera;
const transitions = globalThis.ShuyuTransitions;
const checks = globalThis.ShuyuMotionChecks;
const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-6, `${a} != ${b}`);

test('camera reaches its framing target and returns home regardless of seek order', () => {
  const box = [600, 250, 400, 300];
  const at = camera.track(camera.HOME, [
    { at: 2, dur: 1, box, pad: 0.15 },
    { at: 5, dur: 1, to: camera.HOME }
  ]);
  assert.deepEqual(at(0), camera.HOME);
  assert.deepEqual(at(3), camera.frame(box, 0.15));
  assert.deepEqual(at(6), camera.HOME);
  const samples = [0, 2, 2.5, 3, 4, 5, 5.5, 6].map(t => [t, at(t)]);
  for (const [t, expected] of samples.reverse()) assert.deepEqual(at(t), expected);
  const cam = at(2.5);
  const [sx, sy] = camera.toScreen(cam, 720, 310);
  const [x, y] = camera.toWorld(cam, sx, sy);
  close(x, 720);
  close(y, 310);
});

test('the prepared transition bundle preserves the old check API and its thresholds', () => {
  const a = { x: 960, y: 540, size: 300 };
  assert.deepEqual(transitions.check(a, a), { offsetPx: 0, sizeChange: 0, ok: true });
  for (const b of [a, { ...a, x: 961.9 }, { ...a, x: 962 }, { ...a, size: 297 }]) {
    assert.deepEqual(transitions.check(a, b), checks.continuity(a, b));
  }
  assert.equal(checks.continuity(a, { ...a, x: 961.9 }).ok, true);
  assert.equal(checks.continuity(a, { ...a, x: 962 }).ok, false);
  assert.equal(checks.continuity(a, { ...a, size: 297 }).ok, false);
});

test('the continuity checker also runs independently of GSAP and transitions', () => {
  const context = vm.createContext({});
  vm.runInContext(readFileSync(path.join(__dirname, '../motion/checks/continuity.js'), 'utf8'), context);
  assert.equal(context.ShuyuMotionChecks.continuity(
    { x: 0, y: 0, size: 10 }, { x: 0, y: 0, size: 10 }).ok, true);
});

test('all transitions preserve their endpoints and values after reverse seeking', () => {
  const cases = [
    { add: (tl, el) => transitions.crossIn(tl, el, 1), start: 0, end: 1 },
    { add: (tl, el) => transitions.fadeOut(tl, el, 1, 1), start: 1, end: 0 },
    { add: (tl, el) => transitions.pushArrive(tl, el, 1), start: 0, end: 1, scale: true }
  ];
  for (const item of cases) {
    const el = { opacity: 1, scale: 1 };
    const tl = gsap.timeline({ paused: true });
    item.add(tl, el);
    const samples = [0, 0.25, 0.5, 0.75, 1].map(t => {
      tl.seek(t);
      return { t, opacity: el.opacity, scale: el.scale };
    });
    close(samples[0].opacity, item.start);
    close(samples[4].opacity, item.end);
    if (item.scale) {
      close(samples[0].scale, 1.04);
      close(samples[4].scale, 1);
    }
    for (const sample of samples.reverse()) {
      tl.seek(sample.t);
      close(el.opacity, sample.opacity);
      close(el.scale, sample.scale);
    }
    tl.kill();
  }
  gsap.ticker.sleep();
});
