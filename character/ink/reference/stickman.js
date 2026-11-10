/* Editable reference-study rig. No clocks, raster artwork or external dependencies. */
(function (g) {
  'use strict';
  const data = typeof module !== 'undefined' && module.exports ? require('./motions.js') : g.StickmanMotionData;
  const actions = data.actions;
  const joints = data.joints;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const mix = (a, b, t) => a + (b - a) * t;
  const mod = (v, n) => ((v % n) + n) % n;
  const copy = p => Object.fromEntries(Object.entries(p).map(([k, v]) => [k, Array.isArray(v) ? [...v] : v]));
  function blend(a, b, amount) {
    const t = clamp(amount, 0, 1), out = {};
    for (const k of Object.keys(a)) out[k] = Array.isArray(a[k]) ? a[k].map((v, i) => mix(v, b[k][i], t)) : mix(a[k], b[k], t);
    return out;
  }
  function keySample(action, t) {
    const keys = action.keys;
    if (t >= action.duration) return copy(keys[keys.length - 1].pose);
    let i = 0;
    while (i + 1 < keys.length && keys[i + 1].t <= t) i++;
    const a = keys[i], b = keys[i + 1];
    let u = clamp((t - a.t) / (b.t - a.t), 0, 1);
    if (a.ease !== 'linear') u = u * u * (3 - 2 * u);
    return blend(a.pose, b.pose, u);
  }
  // Two-bone solution: gait feet are solved from their world-space contact,
  // rather than being translated along with the body during stance.
  function ik(a, b, l1, l2, bend) {
    const dx = b[0] - a[0], dy = b[1] - a[1], raw = Math.hypot(dx, dy);
    const d = clamp(raw, 0.001, l1 + l2 - 0.001);
    const along = (l1*l1 - l2*l2 + d*d) / (2*d);
    const height = Math.sqrt(Math.max(0, l1*l1 - along*along));
    const ux = dx / (raw || 1), uy = dy / (raw || 1);
    return [a[0] + ux*along + uy*height*bend, a[1] + uy*along - ux*height*bend];
  }
  function gait(p, action, time, travel) {
    const c = action.gait, phase = mod(time / action.duration, 1);
    p.root = [travel ? time / action.duration * c.stride : 0, 0];
    for (const [side, offset] of [['Front', 0], ['Back', .5]]) {
      const q = mod(phase + offset, 1), stance = q <= c.stance;
      let x, y;
      if (stance) { x = c.touchdown - c.stride*q; y = 0; }
      else {
        const u = (q - c.stance) / (1 - c.stance);
        // Constant tangential velocity at both ends; the foot reverses in the air.
        const h = u*u*(3-2*u), v = -c.stride*(1-c.stance);
        x = (1-h)*(c.touchdown-c.stride*c.stance) + h*c.touchdown + v*(2*u*u*u-3*u*u+u);
        y = -c.lift * Math.pow(Math.sin(Math.PI*u), 1.25);
      }
      p['foot'+side] = [x, y];
      p['knee'+side] = ik(p.hip, [x, y], c.thigh, c.shin, 1);
    }
    return p;
  }
  function sample(name, seconds, options = {}) {
    const action = actions[name];
    if (!action) throw new RangeError('Unknown stickman action: ' + name);
    if (!Number.isFinite(seconds)) throw new TypeError('Time must be finite');
    const rate = options.rate ?? 1;
    if (!Number.isFinite(rate) || rate <= 0) throw new RangeError('rate must be positive');
    const raw = Math.max(0, seconds * rate);
    const loop = options.loop ?? action.loop;
    const t = loop ? mod(raw, action.duration) : clamp(raw, 0, action.duration);
    const pose = keySample(action, t);
    if (action.gait) gait(pose, action, loop ? raw : t, !!options.travel);
    if (action.airborne) {
      const c = action.airborne, u = clamp((t-c.takeoff)/(c.landing-c.takeoff),0,1);
      pose.root[1] -= 4*c.height*u*(1-u);
      pose.root[0] += options.travel ? c.distance*u : 0;
      // Rotate the posed, tucked body about its centre of mass. The feet and
      // hands returned to consumers are already rotated, not just the SVG.
      let angle=0;
      const turns=c.rotation||[[0,0],[1,0]];
      for(let i=0;i<turns.length-1;i++)if(u>=turns[i][0]&&u<=turns[i+1][0]){
        const f=(u-turns[i][0])/(turns[i+1][0]-turns[i][0]);
        angle=mix(turns[i][1],turns[i+1][1],f);break;
      }
      const r=angle*Math.PI/180,cos=Math.cos(r),sin=Math.sin(r),[cx,cy]=c.pivot;
      for(const j of joints){const [x,y]=pose[j];pose[j]=[cx+(x-cx)*cos-(y-cy)*sin,cy+(x-cx)*sin+(y-cy)*cos];}
      pose.headTilt+=angle;
    }
    return pose;
  }
  function worldJoint(pose, joint, options = {}) {
    const s = options.scale ?? 1, direction = options.mirror ? -1 : 1;
    return [(options.x ?? 0) + (pose[joint][0] + pose.root[0])*s*direction,
      (options.y ?? 0) + (pose[joint][1] + pose.root[1])*s];
  }
  const fmt = x => Number(x.toFixed(3));
  const xy = p => p.map(fmt).join(' ');
  let instance = 0;
  function limb(a, m, b, round = .23) {
    const before = [mix(m[0], a[0], round), mix(m[1], a[1], round)];
    const after = [mix(m[0], b[0], round), mix(m[1], b[1], round)];
    return `M ${xy(a)} Q ${xy(a)} ${xy(before)} Q ${xy(m)} ${xy(after)} Q ${xy(b)} ${xy(b)}`;
  }
  function create(container, defaults = {}) {
    if (!container) throw new TypeError('A container is required');
    const ns = 'http://www.w3.org/2000/svg';
    const el = (tag, attrs = {}, parent) => {
      const n = document.createElementNS(ns, tag);
      for (const [k,v] of Object.entries(attrs)) n.setAttribute(k,v);
      if (parent) parent.appendChild(n);
      return n;
    };
    const svg = el('svg', {xmlns: ns, viewBox: defaults.viewBox || '0 0 640 640', width: '100%', height: '100%', role: 'img', 'aria-label': '火柴人动作'});
    // The head is hollow. Clip body strokes behind it without painting a fake
    // background colour, so the opening stays transparent on any destination.
    const maskId = `stickman-head-hole-${++instance}`;
    const defs = el('defs', {}, svg);
    const mask = el('mask', {id:maskId,maskUnits:'userSpaceOnUse',x:-10000,y:-10000,width:20000,height:20000}, defs);
    el('rect', {x:-10000,y:-10000,width:20000,height:20000,fill:'white'}, mask);
    const hole = el('ellipse', {fill:'black'}, mask);
    const body = el('g', {fill: 'none', 'stroke-linecap': 'round', 'stroke-linejoin': 'round'}, svg);
    const limbs = el('g', {mask:`url(#${maskId})`}, body);
    const parts = {};
    for (const name of ['armBack','legBack','torso','legFront','armFront']) parts[name] = el('path', {'data-part': name}, limbs);
    parts.head = el('ellipse', {'data-part':'head'}, body);
    const debug = el('g', {'data-part':'skeleton',fill: '#90d9ff', stroke: '#0b1726', 'stroke-width': 1.3}, body);
    const dots = Object.fromEntries(joints.map(j => [j, el('circle', {r: 3.2}, debug)]));
    container.appendChild(svg);
    const api = {svg, pose: null, options: null, render(name, t, options = {}) {return api.draw(sample(name, t, options), options);},
      draw(p, options = {}) {
        const o = {...defaults, ...options}, scale = o.scale ?? 1.5;
        body.setAttribute('transform', `translate(${o.x ?? 320} ${o.y ?? 500}) scale(${o.mirror ? -scale : scale} ${scale}) translate(${xy(p.root)})`);
        body.setAttribute('stroke', o.color || data.rig.color);
        body.setAttribute('stroke-width', o.strokeWidth ?? data.rig.stroke);
        parts.armBack.setAttribute('d', limb(p.neck, p.elbowBack, p.handBack, .42));
        parts.armFront.setAttribute('d', limb(p.neck, p.elbowFront, p.handFront, .42));
        parts.legBack.setAttribute('d', limb(p.hip, p.kneeBack, p.footBack));
        parts.legFront.setAttribute('d', limb(p.hip, p.kneeFront, p.footFront));
        const control = [2*p.waist[0]-(p.neck[0]+p.hip[0])/2, 2*p.waist[1]-(p.neck[1]+p.hip[1])/2];
        parts.torso.setAttribute('d', `M ${xy(p.neck)} Q ${xy(control)} ${xy(p.hip)}`);
        for (const [k,v] of Object.entries({cx:p.head[0], cy:p.head[1], rx:data.rig.headRadius*p.headScale[0], ry:data.rig.headRadius*p.headScale[1], transform:`rotate(${p.headTilt} ${xy(p.head)})`})) {parts.head.setAttribute(k,v);hole.setAttribute(k,v);}
        debug.setAttribute('opacity', o.skeleton ? 1 : 0);
        for (const j of joints) {dots[j].setAttribute('cx',p[j][0]);dots[j].setAttribute('cy',p[j][1]);}
        api.pose = copy(p); api.options = o; return api;
      },
      joint(name) {return worldJoint(api.pose, name, {x:defaults.x??320,y:defaults.y??500,scale:defaults.scale??1.5,...api.options});},
      toSVG() {return new XMLSerializer().serializeToString(svg);},
      destroy() {svg.remove();}
    };
    return api;
  }
  const api = {version:'2.0.0', actions, data, joints, sample, blend, create, worldJoint};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else g.ShuyuStickman = api;
})(globalThis);
