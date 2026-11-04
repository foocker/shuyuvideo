/* The staircase figure, shared by the stairs and formula scenes so the cut
   between them joins the same drawing at the same place. World units = px. */
(function (root) {
  'use strict';
  const N = 4, B = 90, X0 = 700, Y0 = 830;          // staircase bottom-left corner
  const SHIFT = { x: -520, y: -B };                   // one row up completes N x (N+1)
  const COPY_LEFT = X0 + 520, TOP = Y0 - (N + 1) * B; // rectangle top
  const BRACE_Y = Y0 + 112, BRACE_X = X0 + N * B + 48, D = 20;
  // Camera when the figure moves to the left third, held across the cut.
  const CAM_END = { x: 1520, y: 640, z: 1 };
  const SVG = 'http://www.w3.org/2000/svg';

  function brace(x1, y1, x2, y2) {
    // Two S-curves meeting at a tip, pointing away from the figure.
    const mx = (x1 + x2) / 2, my = (y1 + y2) / 2, horiz = y1 === y2;
    const nx = horiz ? 0 : D, ny = horiz ? D : 0;
    const c = (ax, ay) => `M${ax} ${ay} C${ax + nx} ${ay + ny} ${mx} ${my} ${mx + nx} ${my + ny}`;
    return c(x1, y1) + ' ' + c(x2, y2);
  }

  function el(doc, tag, attrs, parent, ns) {
    const n = ns ? doc.createElementNS(ns, tag) : doc.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) n.setAttribute(k, v);
    parent.appendChild(n);
    return n;
  }

  function block(doc, parent, left, top, cls) {
    return el(doc, 'div', { class: 'fig-block ' + cls,
      style: `left:${left}px;top:${top}px;width:${B}px;height:${B}px` }, parent);
  }

  function build(world) {
    const doc = world.ownerDocument;
    const columns = [], labels = [];
    for (let k = 1; k <= N; k++) {
      const col = [];
      for (let j = 1; j <= k; j++) col.push(block(doc, world, X0 + (k - 1) * B, Y0 - j * B, 'fig-a'));
      columns.push(col);
      labels.push(el(doc, 'div', { class: 'fig-num', 'data-tex': String(k),
        style: `left:${X0 + (k - 1) * B}px;top:${Y0 + 46}px;width:${B}px` }, world));
    }
    const slide = el(doc, 'div', { class: 'fig-copy',
      style: `left:${COPY_LEFT}px;top:${Y0 - N * B}px;width:${N * B}px;height:${N * B}px` }, world);
    const turn = el(doc, 'div', { class: 'fig-turn', style: `width:${N * B}px;height:${N * B}px` }, slide);
    const copyBlocks = [];
    for (let k = 1; k <= N; k++)
      for (let j = 1; j <= k; j++) copyBlocks.push(block(doc, turn, (k - 1) * B, (N - j) * B, 'fig-b'));

    const svg = el(doc, 'svg', { class: 'fig-lines', width: 1920, height: 1080, viewBox: '0 0 1920 1080' }, world, SVG);
    const rect = el(doc, 'rect', { x: X0, y: TOP, width: N * B, height: (N + 1) * B, class: 'fig-rect',
      pathLength: 100, 'stroke-dasharray': 100, 'stroke-dashoffset': 100 }, svg, SVG);
    const braceW = el(doc, 'path', { d: brace(X0, BRACE_Y, X0 + N * B, BRACE_Y), class: 'fig-brace',
      pathLength: 100, 'stroke-dasharray': 100, 'stroke-dashoffset': 100 }, svg, SVG);
    const braceH = el(doc, 'path', { d: brace(BRACE_X, TOP, BRACE_X, Y0), class: 'fig-brace',
      pathLength: 100, 'stroke-dasharray': 100, 'stroke-dashoffset': 100 }, svg, SVG);
    const labelW = el(doc, 'div', { class: 'fig-label', 'data-tex': 'n',
      style: `left:${X0}px;top:${BRACE_Y + D + 6}px;width:${N * B}px` }, world);
    const labelH = el(doc, 'div', { class: 'fig-label fig-label-side', 'data-tex': 'n+1',
      style: `left:${BRACE_X + D + 14}px;top:${(TOP + Y0) / 2 - 34}px` }, world);
    return { columns, labels, slide, turn, copyBlocks, rect, braceW, braceH, labelW, labelH };
  }

  // The state the stairs scene ends on; the formula scene starts from it.
  function finish(gsap, f) {
    gsap.set([...f.columns.flat(), ...f.labels, ...f.copyBlocks, f.labelW, f.labelH], { opacity: 1 });
    gsap.set(f.slide, { opacity: 1, x: SHIFT.x, y: SHIFT.y });
    gsap.set(f.turn, { rotation: 180 });
    gsap.set([f.rect, f.braceW, f.braceH], { attr: { 'stroke-dashoffset': 0 } });
  }

  root.StairFigure = { N, B, X0, Y0, TOP, SHIFT, CAM_END, build, finish };
})(globalThis);
