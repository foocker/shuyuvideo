/* ShuYu camera: a 1920x1080 "world" layer viewed through a camera.
   cam = {x, y, z}: world point (x, y) sits at the screen centre, zoom z (>1 is closer).
   Pure function of time, so it is seek-safe in HyperFrames. No dependencies. */
(function (root) {
  'use strict';
  const W = 1920, H = 1080;
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const eases = {
    linear: u => u,
    smooth: u => u * u * u * (u * (6 * u - 15) + 10),
    out: u => 1 - Math.pow(1 - u, 3),
    in: u => u * u * u
  };
  const HOME = { x: W / 2, y: H / 2, z: 1 };

  // Camera that frames a world box [x, y, width, height] with `pad` margin on each side.
  function frame(box, pad = 0.1) {
    const z = Math.min(W / (box[2] * (1 + 2 * pad)), H / (box[3] * (1 + 2 * pad)));
    return { x: box[0] + box[2] / 2, y: box[1] + box[3] / 2, z };
  }

  // Positions ease linearly in space; zoom eases in log space, so a push-in feels even.
  function mix(a, b, u) {
    return { x: a.x + (b.x - a.x) * u, y: a.y + (b.y - a.y) * u, z: a.z * Math.pow(b.z / a.z, u) };
  }

  // moves: [{at, dur, to: {x,y,z} | box: [x,y,w,h], pad, ease}] in time order.
  function track(start, moves) {
    const first = start.box ? frame(start.box, start.pad) : { ...HOME, ...start };
    const steps = moves.map(m => ({ ...m, to: m.box ? frame(m.box, m.pad) : { ...HOME, ...m.to } }));
    return function at(t) {
      let cam = first;
      for (const m of steps) {
        if (t <= m.at) break;
        const u = clamp((t - m.at) / m.dur);
        cam = mix(cam, m.to, (eases[m.ease] || eases.smooth)(u));
        if (u < 1) break;
      }
      return cam;
    };
  }

  // The world element must be 1920x1080, absolutely positioned at 0,0.
  function apply(el, cam) {
    el.style.transformOrigin = '0 0';
    el.style.transform = `translate(${W / 2 - cam.x * cam.z}px, ${H / 2 - cam.y * cam.z}px) scale(${cam.z})`;
  }

  const toScreen = (cam, x, y) => [W / 2 + (x - cam.x) * cam.z, H / 2 + (y - cam.y) * cam.z];
  const toWorld = (cam, sx, sy) => [cam.x + (sx - W / 2) / cam.z, cam.y + (sy - H / 2) / cam.z];

  root.ShuyuCamera = { HOME, frame, mix, track, apply, toScreen, toWorld, eases };
})(globalThis);
