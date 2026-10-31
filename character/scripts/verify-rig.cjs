/* Contract checks: seeking, loop seams, planted feet and an open Omega. */
const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');
const api=require('../lib/omega.js');
const flatten=o=>typeof o==='number'?[o]:Object.values(o).flatMap(flatten);
let frames=0,minimumGap=Infinity,maxLoopError=0;
const standing=['idle','blink','look','wave','pointLeft','pointRight','explain','think','nod','shake','shrug','bow'];
for(const [name,spec] of Object.entries(api.actions)){
  for(let i=0;i<=Math.ceil(spec.duration*60);i++){
    const t=Math.min(spec.duration,i/60),p=api.sample(name,t);assert(flatten(p).every(Number.isFinite),name+' finite');
    assert(p.sx>.7&&p.sy>.7&&p.rootY<=1e-7,name+' body limits');
    const l=api.warp([-21.89,0],p),r=api.warp([22.50,0],p);minimumGap=Math.min(minimumGap,r[0]-l[0]);
    assert(r[0]-l[0]>10,name+' Omega opening must remain visible');
    if(standing.includes(name))for(const x of [-120,-70,70,120])assert(Math.abs(api.warp([x,0],p)[1]+p.rootY)<1e-7,name+' planted sole');
    frames++;
  }
  const a=flatten(api.sample(name,0)),b=flatten(api.sample(name,spec.duration));
  const difference=Math.max(...a.map((v,i)=>Math.abs(v-b[i])));maxLoopError=Math.max(maxLoopError,difference);
  assert(difference<1e-7,name+' cycle seam');
  const before=api.sample(name,spec.duration*.43);api.sample('jump',1.1);assert.deepEqual(before,api.sample(name,spec.duration*.43));
}
let footDrift=0;
for(const [side,offset] of [['L',0],['R',1]]){
  const positions=[.1,.2,.45,.7,.9].map(t=>{const p=api.sample('walk',t+offset,{travel:true});return p.rootX+api.warp([side==='L'?-90:90,0],p)[0]});
  const drift=Math.max(...positions)-Math.min(...positions);footDrift=Math.max(footDrift,drift);assert(drift<1e-9,'world stance foot drift');
}
const right=api.sample('pointRight',1.5),left=api.sample('pointLeft',1.5);
assert(right.armR.x>250&&right.lookX>.9&&left.armL.x< -250&&left.lookX<-.9,'pointing and gaze agree');
assert(api.sample('blink',.72).eyeL<.03,'eyelid closes');
assert(api.sample('jump',1.08).rootY< -90,'jump has actual flight');
const report={fps:60,actions:Object.keys(api.actions).length,frames,minimumOmegaOpening:minimumGap,maxCycleSeamError:maxLoopError,worldStanceFootDrift:footDrift,randomSeek:'passed',standingSoles:'fixed',pointingGaze:'passed',blinkAndJump:'passed'};
const out=path.join(__dirname,'../output');fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'rig-verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
