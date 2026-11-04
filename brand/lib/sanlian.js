/* ShuYu 三连 icons: 点赞 (like), 收藏 (collect), 投币 (coin).
 *
 * Original drawings in a 100 x 100 box, coloured from style/tokens.json. No text
 * inside the icons, so films supply their own labels (and font subsets).
 *
 *   const icon = ShuyuSanlian.create(svgGroup, 'like', { x: 960, y: 540, size: 120 });
 *   ShuyuSanlian.light(tl, icon, 1.2);   // off -> on with a pop, at timeline time 1.2 s
 *   ShuyuSanlian.create(g, 'coin', { x, y, size, on: true });   // already lit
 *
 * The outer <g> carries the position as an SVG attribute; GSAP only animates the
 * inner `.sl-pop` group, so the two transforms never fight.
 */
(function (root) {
  const NS = 'http://www.w3.org/2000/svg';
  const ACTIONS = ['like', 'collect', 'coin'];
  const COLORS = { like: '#B64D35', collect: '#D2AA58', coin: '#C38460', off: '#536359', ground: '#F4F2EC' };

  function star(cx, cy, outer, inner) {
    const points = [];
    for (let i = 0; i < 10; i++) {
      const r = i % 2 ? inner : outer, a = -Math.PI / 2 + i * Math.PI / 5;
      points.push((cx + r * Math.cos(a)).toFixed(2) + ' ' + (cy + r * Math.sin(a)).toFixed(2));
    }
    return 'M' + points.join(' L') + ' Z';
  }

  // Each part: [tag, attributes, role]. `body` parts fill when lit; `detail`
  // parts are drawn on top and switch to the ground colour when lit.
  const SHAPES = {
    like: [
      ['rect', { x: 12, y: 44, width: 17, height: 42, rx: 4 }, 'body'],
      ['path', { d: 'M36 46 L50 21 C53 15 62 16 62 24 L60 40 L80 40 C87 40 91 46 89 53 L83 78 '
                  + 'C82 83 78 86 73 86 L36 86 Z' }, 'body'],
    ],
    collect: [['path', { d: star(50, 53, 43, 19) }, 'body']],
    coin: [
      // A round coin with a square hole (方孔钱): even-odd fill keeps the hole open.
      ['path', { d: 'M12 50 A38 38 0 1 0 88 50 A38 38 0 1 0 12 50 Z M41 41 L59 41 L59 59 L41 59 Z',
                 'fill-rule': 'evenodd' }, 'body'],
      ['circle', { cx: 50, cy: 50, r: 29 }, 'detail'],
    ],
  };
  const BURST = 6;

  function el(tag, attrs, parent) {
    const node = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    if (parent) parent.appendChild(node);
    return node;
  }

  function create(parent, action, options = {}) {
    if (!SHAPES[action]) throw new Error('unknown 三连 action: ' + action);
    const { x = 0, y = 0, size = 100, on = false, id } = options;
    const color = COLORS[action];
    const outer = el('g', { class: 'sanlian-icon', 'data-action': action,
      transform: `translate(${x - size / 2} ${y - size / 2}) scale(${size / 100})` }, parent);
    if (id) outer.id = id;
    const pop = el('g', { class: 'sl-pop' }, outer);
    const burst = el('g', { class: 'sl-burst', opacity: 0 }, pop);
    for (let i = 0; i < BURST; i++) {
      const a = -Math.PI / 2 + i * 2 * Math.PI / BURST;
      el('line', { x1: 50 + 54 * Math.cos(a), y1: 50 + 54 * Math.sin(a), x2: 50 + 66 * Math.cos(a),
        y2: 50 + 66 * Math.sin(a), stroke: color, 'stroke-width': 6, 'stroke-linecap': 'butt' }, burst);
    }
    const parts = SHAPES[action].map(([tag, attrs, role]) => {
      const node = el(tag, { ...attrs, 'stroke-width': 6, 'stroke-linejoin': 'round' }, pop);
      node.classList.add('sl-' + role);
      return node;
    });
    paint(outer, on);
    return outer;
  }

  function paint(icon, on) {
    const color = COLORS[icon.dataset.action];
    icon.querySelectorAll('.sl-body').forEach(n => {
      n.setAttribute('stroke', on ? color : COLORS.off);
      n.setAttribute('fill', color);
      n.setAttribute('fill-opacity', on ? 1 : 0);
    });
    icon.querySelectorAll('.sl-detail').forEach(n => {
      n.setAttribute('stroke', on ? COLORS.ground : COLORS.off);
      n.setAttribute('fill', 'none');
      n.setAttribute('stroke-width', on ? 4 : 3);
    });
  }

  // Off -> on on a paused GSAP timeline: the outline takes the colour, the shape
  // fills, the icon pops once and six short rays leave and fade. About 0.55 s.
  function light(tl, icon, at, options = {}) {
    const { pop = 1.22, burst = true } = options;
    const color = COLORS[icon.dataset.action];
    const inner = icon.querySelector('.sl-pop');
    tl.set(inner, { svgOrigin: '50 50' }, 0);
    // CSS properties rather than attributes: GSAP interpolates CSS colours.
    tl.to(icon.querySelectorAll('.sl-body'), { stroke: color, fillOpacity: 1, duration: 0.22, ease: 'power2.out' }, at);
    const details = icon.querySelectorAll('.sl-detail');  // only the coin has one
    if (details.length) tl.to(details, { stroke: COLORS.ground, strokeWidth: 4, duration: 0.22, ease: 'power2.out' }, at);
    tl.fromTo(inner, { scale: 1 }, { scale: pop, duration: 0.16, ease: 'power2.out' }, at);
    tl.to(inner, { scale: 1, duration: 0.3, ease: 'back.out(2.2)' }, at + 0.16);
    if (burst) {
      const rays = icon.querySelector('.sl-burst');
      tl.set(rays, { svgOrigin: '50 50' }, 0);
      tl.fromTo(rays, { opacity: 1, scale: 0.8 }, { scale: 1.25, duration: 0.45, ease: 'power2.out' }, at + 0.05);
      tl.to(rays, { opacity: 0, duration: 0.25, ease: 'power1.in' }, at + 0.25);
    }
    return tl;
  }

  // The three icons side by side, in the fixed order like, collect, coin.
  function row(parent, options = {}) {
    const { x = 0, y = 0, size = 100, gap = size * 0.35, on = [], idPrefix } = options;
    const step = size + gap, icons = {};
    ACTIONS.forEach((action, i) => {
      icons[action] = create(parent, action, { x: x + (i - 1) * step, y, size, on: on.includes(action),
        id: idPrefix ? `${idPrefix}-${action}` : undefined });
    });
    return icons;
  }

  root.ShuyuSanlian = { ACTIONS, COLORS, create, light, paint, row };
})(globalThis);
