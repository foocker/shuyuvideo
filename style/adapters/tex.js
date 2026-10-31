/* Render every element with data-tex through local KaTeX, once at load.
   Write TeX in HTML attributes with single backslashes: data-tex="\frac{n}{2}".
   A TeX error throws, so a broken formula fails the check instead of showing raw source. */
(function (root) {
  'use strict';
  function renderAll(scope) {
    for (const el of (scope || document).querySelectorAll('[data-tex]')) {
      root.katex.render(el.getAttribute('data-tex'), el, {
        displayMode: el.hasAttribute('data-display'), throwOnError: true, output: 'html', strict: 'error'
      });
    }
  }
  root.ShuyuTex = { renderAll };
})(globalThis);
