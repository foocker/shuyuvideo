const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const lib = require('../lib/stickman.js');
const near = (a,b,eps=1e-8) => assert.ok(Math.abs(a-b)<eps,`${a} != ${b}`);
let samples=0,maxContactDrift=0,maxLoopError=0;
for(const [name,a] of Object.entries(lib.actions)){
  const ts=Array.from({length:Math.ceil(a.duration*120)+1},(_,i)=>Math.min(i/120,a.duration));
  const poses=ts.map(t=>lib.sample(name,t,{loop:false}));
  poses.forEach(p=>{for(const [k,v] of Object.entries(p)){for(const n of Array.isArray(v)?v:[v])assert.ok(Number.isFinite(n),`${name}.${k}`);}samples++;});
  // Seeking must be pure even when evaluated backwards and out of order.
  [...ts].reverse().forEach(t=>assert.deepEqual(lib.sample(name,t,{loop:false}),poses[ts.indexOf(t)]));
  const one=lib.sample(name,.2);one.head[0]=9999;assert.notEqual(lib.sample(name,.2).head[0],9999);
  for(const c of a.contacts||[]){
    const first=lib.sample(name,c.start,{loop:false})[c.joint];
    for(let t=c.start;t<c.end;t+=1/120){const p=lib.sample(name,t,{loop:false})[c.joint];maxContactDrift=Math.max(maxContactDrift,Math.hypot(p[0]-first[0],p[1]-first[1]));}
  }
  if(a.loop){const p=lib.sample(name,0,{loop:false}),q=lib.sample(name,a.duration,{loop:false});for(const k of lib.joints)for(let i=0;i<2;i++)maxLoopError=Math.max(maxLoopError,Math.abs(p[k][i]-q[k][i]));}
  if(a.gait){
    for(const side of ['Front','Back']){
      const offset=side==='Front'?0:.5;
      let last=null;
      for(let i=0;i<Math.ceil(a.duration*360);i++){
        const t=i/120,phase=((t/a.duration+offset)%1+1)%1;
        const p=lib.sample(name,t,{travel:true}),foot=lib.worldJoint(p,'foot'+side);
        if(phase<a.gait.stance && last && phase>last.phase){maxContactDrift=Math.max(maxContactDrift,Math.hypot(foot[0]-last.foot[0],foot[1]-last.foot[1]));}
        last=phase<a.gait.stance?{phase,foot}:null;
        // IK must reach its foot without stretching in any sampled pose.
        const k=p['knee'+side],f=p['foot'+side];
        near(Math.hypot(k[0]-p.hip[0],k[1]-p.hip[1]),a.gait.thigh,1e-5);
        near(Math.hypot(k[0]-f[0],k[1]-f[1]),a.gait.shin,1e-5);
      }
    }
  }
  if(a.airborne){
    const c=a.airborne;
    for(let t=0;t<a.duration;t+=1/240){
      const p=lib.sample(name,t,{loop:false});
      for(const j of ['footFront','footBack'])assert.ok(lib.worldJoint(p,j)[1]<.01,`${name} floor penetration at ${t} ${j}`);
      assert.ok(p.head[1]+p.root[1]+lib.data.rig.headRadius<0,`${name} head hits floor at ${t}`);
    }
    const atMid=lib.sample(name,(c.takeoff+c.landing)/2);near(atMid.root[1],-c.height);
    near(lib.sample(name,c.takeoff).root[1],0);near(lib.sample(name,c.landing).root[1],0);
    const end=lib.sample(name,a.duration,{travel:true});near(end.root[0],c.distance);
    const aPose=lib.sample(name,c.landing,{travel:true}),bPose=lib.sample(name,c.landing+.2,{travel:true});
    for(const j of ['footFront','footBack'])for(let i=0;i<2;i++)near(lib.worldJoint(aPose,j)[i],lib.worldJoint(bPose,j)[i]);
  }
  const p=lib.sample(name,.4),m=lib.worldJoint(p,'head',{mirror:true,x:100,scale:2});near(m[0],100-2*(p.head[0]+p.root[0]));
  assert.deepEqual(lib.sample(name,.4,{rate:2}),lib.sample(name,.8));
  if(!a.loop)assert.deepEqual(lib.sample(name,a.duration+100),lib.sample(name,a.duration));
}
assert.ok(maxContactDrift<1e-7,`contact drift ${maxContactDrift}`);assert.ok(maxLoopError<1e-7);
assert.throws(()=>lib.sample('missing',0));assert.throws(()=>lib.sample('walk',NaN));
const out=path.resolve(__dirname,'../../../output/character-stickman/reports/rig-check.json');fs.mkdirSync(path.dirname(out),{recursive:true});
const report={passed:true,actions:Object.keys(lib.actions).length,samples,maxContactDrift,maxLoopError,checks:['finite coordinates','reverse/random seek equality','snapshot isolation','fixed contacts','world-space gait planting','two-bone reach','loop seams','retime','mirror','end holds']};fs.writeFileSync(out,JSON.stringify(report,null,2));console.log(JSON.stringify(report));
