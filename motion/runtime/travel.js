/* Seek-safe travel on a planar cubic path. Positions use [x,z] coordinates. */
(function(root){
  const TAU=2*Math.PI,clamp=v=>Math.max(0,Math.min(1,v));
  const smooth=v=>{v=clamp(v);return v*v*(3-2*v);};
  const angleDelta=(a,b)=>Math.atan2(Math.sin(b-a),Math.cos(b-a));
  const turn=(a,b,u)=>a+angleDelta(a,b)*smooth(u);
  function evaluate(c,t){
    const s=1-t;
    return [0,1].map(i=>s*s*s*c[0][i]+3*s*s*t*c[1][i]+3*s*t*t*c[2][i]+t*t*t*c[3][i]);
  }
  function tangent(c,t){
    const s=1-t,d=[0,1].map(i=>3*s*s*(c[1][i]-c[0][i])+6*s*t*(c[2][i]-c[1][i])+3*t*t*(c[3][i]-c[2][i]));
    if(Math.hypot(...d)<1e-10)throw new Error('Travel path has a stationary tangent');
    return d;
  }
  function path(segments,{samples=192}={}){
    if(!Array.isArray(segments)||!segments.length)throw new Error('Travel path needs cubic segments');
    if(!Number.isInteger(samples)||samples<16)throw new Error('Travel sampling must be an integer >=16');
    const curves=segments.map(s=>s.map(p=>p.slice()));
    curves.forEach((c,i)=>{
      if(c.length!==4||c.some(p=>p.length!==2||p.some(v=>!Number.isFinite(v))))throw new Error('Invalid cubic coordinates');
      if(i){
        const a=curves[i-1],d=tangent(a,1),e=tangent(c,0);
        if(Math.hypot(...c[0].map((v,j)=>v-a[3][j]))>1e-8)throw new Error('Travel segments must meet');
        if(Math.abs(angleDelta(Math.atan2(d[0],d[1]),Math.atan2(e[0],e[1])))>1e-6)throw new Error('Travel segments must share a tangent');
      }
    });
    const table=[];let length=0,previous,heading;
    curves.forEach((c,i)=>{
      for(let j=i?1:0;j<=samples;j++){
        const t=j/samples,point=evaluate(c,t),d=tangent(c,t),raw=Math.atan2(d[0],d[1]);
        if(previous)length+=Math.hypot(point[0]-previous[0],point[1]-previous[1]);
        heading=heading===undefined?raw:heading+angleDelta(heading,raw);
        table.push({distance:length,segment:i,t,heading});previous=point;
      }
    });
    if(length<1e-8)throw new Error('Travel path has no length');
    function sample(u){
      const distance=clamp(u)*length;let lo=0,hi=table.length-1;
      while(hi-lo>1){const m=(lo+hi)>>1;if(table[m].distance<distance)lo=m;else hi=m;}
      const a=table[lo],b=table[hi],q=(distance-a.distance)/Math.max(1e-12,b.distance-a.distance);
      const index=b.segment,t=a.segment===index?a.t+(b.t-a.t)*q:b.t*q;
      const point=evaluate(curves[index],t),d=tangent(curves[index],t),norm=Math.hypot(...d);
      const base=a.heading+(b.heading-a.heading)*q,raw=Math.atan2(d[0],d[1]);
      return {x:point[0],z:point[1],distance,heading:base+angleDelta(base,raw),tangent:d.map(v=>v/norm)};
    }
    // Ease only the acceleration/deceleration windows; do not stop at internal joins.
    function pose(t,start,end,{ramp=.18,stepLength=.64,startHeading,endHeading,phase=0}={}){
      if(!(end>start)||!(stepLength>0)||!(ramp>0&&ramp<=.5))throw new Error('Invalid travel timing');
      const u=clamp((t-start)/(end-start)),r=ramp;
      let s,v;
      if(u<r){s=u*u/(2*r);v=u/r;}
      else if(u>1-r){s=1-r-(1-u)*(1-u)/(2*r);v=(1-u)/r;}
      else{s=u-r/2;v=1;}
      s/=1-r;v/=1-r;
      const at=sample(s),speed=t<=start||t>=end?0:v*length/(end-start);
      if(startHeading!==undefined){const first=table[0].heading,aligned=first+angleDelta(first,startHeading);at.heading=aligned+(at.heading-aligned)*smooth((t-start+.35)/.65);}
      if(endHeading!==undefined){const last=table[table.length-1].heading,aligned=last+angleDelta(last,endHeading);at.heading+=(aligned-at.heading)*smooth((t-end+.1)/.5);}
      const a=sample(Math.max(0,s-.002)),b=sample(Math.min(1,s+.002));
      const curvature=angleDelta(a.heading,b.heading)/Math.max(.001,b.distance-a.distance);
      return {...at,speed,walk:(at.distance+phase)*TAU/stepLength,
        stride:.19*smooth(speed/.65),lean:Math.max(-.12,Math.min(.12,-curvature*speed*.045)),
        stepLength};
    }
    return {length,sample,pose};
  }
  function line(a,b){return path([[a,a.map((v,i)=>v+(b[i]-v)/3),a.map((v,i)=>v+2*(b[i]-v)/3),b]]);}
  const api={path,line,turn,angleDelta};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.ShuyuTravel=api;
})(typeof window!=='undefined'?window:globalThis);
