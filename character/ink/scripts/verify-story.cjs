const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const l=require('../lib/ink.js');
const old=require('../../../output/character-ink/renders/versions/v01-ink-motion/source/lib/ink.js');
let samples=0,maxGripError=0;const reaches={};
for(const [n,a]of Object.entries(l.actions)){
 let max=0,worst=0;
 for(let t=0;t<=a.duration;t+=1/120){
  const p=l.sample(n,t,{loop:false});samples++;
  if(a.propRig)assert.equal(p.propKind,a.keys[0].pose.propKind,`${n}: fractional/missing prop at ${t}`);
  if(old.actions[n]){const q=old.sample(n,t,{loop:false});for(const k of Object.keys(q))assert.deepEqual(p[k],q[k],`${n} v1 regression ${k} at ${t}`);}
  if(a.propRig)for(const [side,offset]of Object.entries(a.propRig.grips)){
   if(p['grip'+side]>.999999){
    const target=l.propPoint(p,offset),hand=p['hand'+side];maxGripError=Math.max(maxGripError,Math.hypot(...target.map((v,i)=>v-hand[i])));
    const shoulder=p.neck.map((v,i)=>v+(p.waist[i]-v)*.08),d=Math.hypot(...hand.map((v,i)=>v-shoulder[i]));
    if(d>max){max=d;worst=t;}
   }
  }
  if(p.pageGrip>.999999){const grip=l.propPoint(p,[-12.5+25*Math.cos(Math.PI*p.propPage),-18]);assert.ok(Math.hypot(...grip.map((v,i)=>v-p.handFront[i]))<1e-7);const shoulder=p.neck.map((v,i)=>v+(p.waist[i]-v)*.08);assert.ok(Math.hypot(...grip.map((v,i)=>v-shoulder[i]))<53);}
 }
 if(a.propRig)reaches[n]={maxReach:max,available:a.propRig.armLengths.reduce((a,b)=>a+b),time:worst};
}
for(const [n,r]of Object.entries(reaches))assert.ok(r.maxReach<r.available,`${n}: unreachable grip ${r.maxReach} > ${r.available} at ${r.time}`);
assert.ok(maxGripError<1e-7);
for(const [a,b]of [['observe','paperRead'],['paperRead','observe']]){const mixed=l.blend(l.sample(a,0),l.sample(b,0),.5);for(const v of Object.values(mixed))assert.ok((Array.isArray(v)?v:[v]).every(Number.isFinite),'mixed v1/v2 channels');}
for(const [a,b]of [['gunRaise','gunAim'],['gunAim','gunFire'],['gunFire','gunLower'],['paperTake','paperRead'],['paperRead','paperFlip']]){
 const p=l.sample(a,l.actions[a].duration,{loop:false}),q=l.sample(b,0,{loop:false});
 for(const k of [...l.joints,'propX','propY','propAngle'])assert.deepEqual(p[k],q[k],`${a} -> ${b}: ${k}`);
}
for(const [t,on]of [[.179,false],[.18,true],[.2,true],[.256,false],[.5,false]])assert.equal(l.sample('gunFire',t).flash>0,on);
for(const name of ['fallBack','fallForward'])for(let t=0;t<=l.actions[name].duration;t+=1/240){const p=l.sample(name,t);for(const j of l.joints)assert.ok(p[j][1]<=0.001,`${name}.${j} below ground ${t}`);assert.ok(p.head[1]+12.5<0,`${name} head below ground ${t}`);}
const report={passed:true,samples,maxGripError,reaches,v1PoseRegression:'11 actions unchanged',checks:['prop grips coincide','arms reach grips','gun and paper seams','muzzle timing','falls ground clearance','v1 regression']};
fs.writeFileSync(path.resolve(__dirname,'../../../output/character-ink/reports/story-check.json'),JSON.stringify(report,null,2));
console.log('Story checks passed');
