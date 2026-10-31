/* ShuYu stage: direct the Omega character over a whole film from a cue list.
   Position, size, action and visibility are all functions of film time.
   Needs omega-shape.js and omega.js loaded first.

   cues (time order), each optional field keeps its previous value:
     {at: 2.0, x: 1560, y: 980, scale: 0.5, move: 0.8, walk: true,
      action: 'think', expression: 'curious', look: [-0.8, -0.3],
      leftHand: 'relaxed', rightHand: 'point', show: true}
   (x, y) is the point between the feet, in 1920x1080 screen pixels.
   `move` seconds to glide from the previous spot (default 0.8); `walk` plays
   the walk cycle while moving. `show: false` fades the character out. */
(function (root) {
  'use strict';
  const O = root.ShuyuOmega;
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const smooth = u => (u = clamp(u), u * u * u * (u * (6 * u - 15) + 10));
  const BOX = { w: 700, h: 540, footX: 350, footY: 480 };
  const FADE = 0.3, SETTLE = 0.45;

  function plan(cues) {
    const out = [];
    let pos = null, look = {}, shown = false;
    for (const c of cues) {
      const from = pos;
      const to = pos ? { ...pos } : { x: 960, y: 980, scale: 0.5 };
      for (const k of ['x', 'y', 'scale']) if (c[k] !== undefined) to[k] = c[k];
      look = { ...look };
      for (const k of ['action', 'expression', 'look', 'leftHand', 'rightHand', 'palette'])
        if (c[k] !== undefined) look[k] = c[k];
      const show = c.show === undefined ? true : c.show;
      out.push({ at: c.at, from: from || to, to, move: from ? (c.move ?? 0.8) : 0, walk: !!c.walk,
                 look, show, fadeFrom: shown ? 1 : 0 });
      pos = to; shown = show;
    }
    return out;
  }

  function create(container, cues, options = {}) {
    const holder = container.ownerDocument.createElement('div');
    holder.style.cssText = `position:absolute;left:0;top:0;width:${BOX.w}px;height:${BOX.h}px;transform-origin:0 0;will-change:transform,opacity`;
    container.appendChild(holder);
    const rig = O.create(holder, { id: options.id || 'stage-omega', palette: options.palette || 'ink' });
    const steps = plan(cues);

    function render(t) {
      let i = -1;
      while (i + 1 < steps.length && steps[i + 1].at <= t) i++;
      if (i < 0) { holder.style.opacity = 0; return; }
      const s = steps[i], local = t - s.at;
      const u = s.move ? smooth(local / s.move) : 1;
      const x = s.from.x + (s.to.x - s.from.x) * u, y = s.from.y + (s.to.y - s.from.y) * u;
      const k = s.from.scale + (s.to.scale - s.from.scale) * u;
      holder.style.transform = `translate(${x - BOX.footX * k}px, ${y - BOX.footY * k}px) scale(${k})`;
      const fade = clamp(local / FADE);
      holder.style.opacity = s.show ? s.fadeFrom + (1 - s.fadeFrom) * fade : (1 - fade) * s.fadeFrom;

      const settings = { expression: s.look.expression, look: s.look.look,
                         leftHand: s.look.leftHand, rightHand: s.look.rightHand };
      let pose;
      if (s.walk && local < s.move) pose = O.sample('walk', local, settings);
      else {
        const action = s.look.action || 'idle', spec = O.actions[action];
        const at = s.walk ? local - s.move : local;
        pose = O.sample(action, at, settings);
        // A one-shot action eases back into breathing instead of freezing.
        if (!spec.loop && at > spec.duration)
          pose = O.blend(pose, O.sample('idle', at, settings), smooth((at - spec.duration) / SETTLE));
      }
      rig.draw(pose, { palette: s.look.palette || options.palette || 'ink' });
    }
    render(0);
    return { render, rig, steps };
  }

  root.ShuyuStage = { create, plan };
})(globalThis);
