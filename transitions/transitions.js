/* ShuYu transitions: tweens added to a scene's own paused GSAP timeline.
   Every helper uses fromTo, so seeking backwards is exact. Needs gsap. */
(function (root) {
  'use strict';

  // Crossfade: the incoming scene's host overlaps the outgoing one by `dur`
  // seconds and sits above it (higher z-index); its content fades in.
  function crossIn(tl, el, dur = 0.5, at = 0) {
    tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: dur, ease: 'none' }, at);
  }

  // Fade a scene's content out at its end, to the background colour (a dip).
  function fadeOut(tl, el, end, dur = 0.4) {
    tl.fromTo(el, { opacity: 1 }, { opacity: 0, duration: dur, ease: 'power1.in', immediateRender: false }, end - dur);
  }

  // Push-in: the outgoing camera dives into an object (see camera.track); the
  // incoming scene starts as that object full-frame and fades in over the last
  // part of the dive, so the viewer arrives inside it.
  function pushArrive(tl, el, dur = 0.35, at = 0) {
    tl.fromTo(el, { opacity: 0, scale: 1.04 }, { opacity: 1, scale: 1, duration: dur, ease: 'power2.out' }, at);
  }

  // Object continuity has no tween: the last frame of scene A and the first
  // frame of scene B draw the same object at the same place and size, then a
  // hard cut joins them. check() reports how far apart the two placements are.
  function check(a, b) {
    const d = Math.hypot(a.x - b.x, a.y - b.y), s = Math.abs(a.size - b.size) / Math.max(a.size, b.size);
    return { offsetPx: Math.round(d * 10) / 10, sizeChange: Math.round(s * 1000) / 1000, ok: d < 2 && s < 0.01 };
  }

  root.ShuyuTransitions = { crossIn, fadeOut, pushArrive, check };
})(globalThis);
