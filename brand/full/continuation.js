// Appended to the SAME paused intro timeline by scripts/build-assets.py.
// The complete first 3 seconds stay identical to the approved short version.
tl.to('#intro-mark',{y:-100,scale:.88,transformOrigin:'50% 50%',duration:.72,ease:'power2.inOut'},3);
tl.to('#intro-wordmark-row',{y:-100,scale:.88,transformOrigin:'50% 50%',duration:.72,ease:'power2.inOut'},3);
tl.fromTo('#full-explore',{opacity:0,x:-12,y:12},{opacity:1,x:0,y:0,duration:.46,ease:'power2.out'},3.40);
tl.fromTo('#full-reason',{opacity:0,clipPath:'inset(0% 100% 0% 0%)'},
  {opacity:1,clipPath:'inset(0% 0% 0% 0%)',duration:.47,ease:'none'},3.60);
tl.fromTo('#full-and',{opacity:0},{opacity:1,duration:.28,ease:'sine.out'},3.92);
tl.fromTo('#full-imagine',{opacity:0},{opacity:1,duration:.25,ease:'sine.out'},4.04);
tl.fromTo('#full-imagine-a',{x:-8,y:-23,rotation:-5},
  {x:0,y:0,rotation:0,duration:.64,ease:'sine.out'},4.04);
tl.fromTo('#full-imagine-b',{x:8,y:-30,rotation:5},
  {x:0,y:0,rotation:0,duration:.66,ease:'sine.out'},4.12);
tl.fromTo('#full-of',{opacity:0},{opacity:1,duration:.30,ease:'sine.out'},4.20);
tl.fromTo('#full-boundary',{opacity:0},{opacity:1,duration:.28,ease:'sine.out'},4.31);
tl.fromTo('#full-boundary-a',{x:-11},{x:0,duration:.48,ease:'power2.out'},4.31);
tl.fromTo('#full-boundary-b',{x:11},{x:0,duration:.48,ease:'power2.out'},4.36);
// Omega notices the text, then looks back. No additional blink or body gesture.
tl.to('.intro-pupil',{y:4,duration:.30,ease:'sine.inOut'},3.52);
tl.to('.intro-pupil',{y:0,duration:.30,ease:'sine.inOut'},4.54);
tl.addLabel('brand-and-tagline',4.84);
tl.set({}, {}, 7);
