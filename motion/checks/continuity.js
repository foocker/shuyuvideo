/* Compare placements across a cut. Coordinates must use the same screen space. */
(function (root) {
  'use strict';

  function continuity(a, b) {
    const d = Math.hypot(a.x - b.x, a.y - b.y), s = Math.abs(a.size - b.size) / Math.max(a.size, b.size);
    return { offsetPx: Math.round(d * 10) / 10, sizeChange: Math.round(s * 1000) / 1000, ok: d < 2 && s < 0.01 };
  }

  root.ShuyuMotionChecks = { continuity };
})(globalThis);
