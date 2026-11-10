const assert=require('node:assert/strict');
const T=require('../motion/runtime/travel.js');
const straight=T.line([0,0],[3,4]);
assert(Math.abs(straight.length-5)<1e-10);
assert(Math.abs(straight.sample(.6).x-1.8)<1e-9);
assert(Math.abs(straight.sample(.6).z-2.4)<1e-9);
// A quarter-turn joins a straight exit without stopping or snapping heading.
const route=T.path([[[0,2],[1,2],[2,1],[2,0]],[[2,0],[2,-.4],[2,-.8],[2,-1.2]]]);
const samples=Array.from({length:601},(_,i)=>route.pose(i/60,0,10));
for(let i=1;i<samples.length;i++){
  assert(samples[i].distance>=samples[i-1].distance);
  assert(Math.abs(T.angleDelta(samples[i-1].heading,samples[i].heading))<.02);
}
const nearA=route.sample(.45),nearB=route.sample(.55);
assert(Math.abs(nearB.distance-nearA.distance-route.length*.1)<1e-10);
// Identical travelled distance gives identical gait phase after a duration edit.
const slow=route.pose(5,0,10),fast=route.pose(2.5,0,5);
assert(Math.abs(slow.walk-fast.walk)<1e-10);
assert(Math.abs(fast.speed-2*slow.speed)<1e-10);
for(let i=samples.length-1;i>=0;i--)assert.deepEqual(route.pose(i/60,0,10),samples[i]);
assert.throws(()=>T.path([[[0,0],[1,0],[2,0],[3,0]],[[3,0],[3,1],[3,2],[3,3]]]),/tangent/);
assert.throws(()=>T.path([[[0,0],[1,0],[2,0],[3,0]],[[4,0],[5,0],[6,0],[7,0]]]),/meet/);
assert(Math.abs(T.turn(Math.PI-.02,-Math.PI+.02,.5)-Math.PI)<1e-9);
// Starting a U-turn exactly opposite a curved path must not switch ±pi branch.
const reverse=T.path([[[3,0],[3,1.5],[-1,1.7],[-3,1.7]]]);
const angles=Array.from({length:121},(_,i)=>reverse.pose(1+i/120,1.5,6,{startHeading:Math.PI}).heading);
for(let i=1;i<angles.length;i++)assert(Math.abs(angles[i]-angles[i-1])<.1);
console.log('Travel distance, smooth heading, retiming, reverse seek and invalid joins passed');
