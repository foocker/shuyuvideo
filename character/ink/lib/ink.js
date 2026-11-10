/* Ink / 墨影 — deterministic, standalone vector actor. All positions use sole=0. */
(function(g){
  'use strict';
  const data=typeof module!=='undefined'&&module.exports?require('./motions.js'):g.InkMotionData;
  const {actions,joints}=data;
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  const mix=(a,b,t)=>a+(b-a)*t;
  const mod=(x,n)=>((x%n)+n)%n;
  const clone=p=>Object.fromEntries(Object.entries(p).map(([k,v])=>[k,Array.isArray(v)?[...v]:v]));
  const blend=(a,b,t)=>Object.fromEntries([...new Set([...Object.keys(a),...Object.keys(b)])].map(k=>{
    const fallback=k==='propAlpha'?1:0,v=a[k]??fallback,w=b[k]??fallback,u=clamp(t,0,1);
    return [k,k==='propKind'?(u<.5?v:w):Array.isArray(v)?v.map((x,i)=>mix(x,w[i],u)):mix(v,w,u)];
  }));

  // Monotone cubic interpolation has continuous velocity at moving keys and
  // zero velocity through authored holds. Unlike a smoothstep at every key,
  // it does not brake the body repeatedly during one continuous action.
  function tangent(keys,i,get,loop){
    let prev=keys[i-1],next=keys[i+1],at=keys[i];
    if(loop&&(i===0||i===keys.length-1)){
      const duration=keys[keys.length-1].t;
      prev={...keys[keys.length-2],t:keys[keys.length-2].t-duration+(i?duration:0)};
      next={...keys[1],t:keys[1].t+(i?duration:0)};
    }
    if(!prev||!next)return 0;
    const h0=at.t-prev.t,h1=next.t-at.t;
    const d0=(get(at)-get(prev))/h0,d1=(get(next)-get(at))/h1;
    if(d0*d1<=0)return 0;
    const w0=2*h1+h0,w1=h1+2*h0;
    return (w0+w1)/(w0/d0+w1/d1);
  }
  function channel(keys,t,get,loop=false){
    if(t<=keys[0].t)return get(keys[0]);
    if(t>=keys[keys.length-1].t)return get(keys[keys.length-1]);
    let i=0;while(keys[i+1].t<t)i++;
    const a=keys[i],b=keys[i+1],h=b.t-a.t,u=(t-a.t)/h;
    const m0=tangent(keys,i,get,loop),m1=tangent(keys,i+1,get,loop);
    return (2*u**3-3*u*u+1)*get(a)+(u**3-2*u*u+u)*h*m0+(-2*u**3+3*u*u)*get(b)+(u**3-u*u)*h*m1;
  }
  function keySample(a,t){
    return Object.fromEntries(Object.entries(a.keys[0].pose).map(([j,v])=>[j,
      j==='propKind'?(a.keys.findLast(k=>k.t<=t)||a.keys[0]).pose[j]:
      Array.isArray(v)?v.map((_,i)=>channel(a.keys,t,k=>k.pose[j][i],a.loop)):
      channel(a.keys,t,k=>k.pose[j],a.loop)]));
  }
  function ik(a,b,l1,l2,bend=1){
    const dx=b[0]-a[0],dy=b[1]-a[1],raw=Math.hypot(dx,dy),d=clamp(raw,.001,l1+l2-.001);
    const along=(l1*l1-l2*l2+d*d)/(2*d),h=Math.sqrt(Math.max(0,l1*l1-along*along));
    return [a[0]+dx/(raw||1)*along+dy/(raw||1)*h*bend,a[1]+dy/(raw||1)*along-dx/(raw||1)*h*bend];
  }
  function sample(name,seconds,options={}){
    const a=actions[name];if(!a)throw new RangeError('Unknown Ink action: '+name);
    if(!Number.isFinite(seconds))throw new TypeError('Time must be finite');
    const rate=options.rate??1;if(!Number.isFinite(rate)||rate<=0)throw new RangeError('rate must be positive');
    const raw=Math.max(0,seconds*rate),loop=options.loop??a.loop,t=loop?mod(raw,a.duration):clamp(raw,0,a.duration);
    const p=keySample(a,t);p.turn=0;p.footAngleFront=p.footAngleFront||0;p.footAngleBack=p.footAngleBack||0;
    if(a.gait){
      const c=a.gait,time=loop?raw:t;
      p.root=[options.travel?time/a.duration*c.stride:0,0];
      const delayed=keySample(a,mod(t-a.armDelay,a.duration));
      for(const j of ['elbowBack','handBack','elbowFront','handFront'])p[j]=delayed[j];
      for(const [side,offset] of [['Front',0],['Back',.5]]){
        const q=mod(time/a.duration+offset,1);let x,y;
        if(q<=c.stance){x=c.touchdown-c.stride*q;y=0;}
        else{
          const u=(q-c.stance)/(1-c.stance),h=u*u*(3-2*u),v=-c.stride*(1-c.stance);
          x=(1-h)*(c.touchdown-c.stride*c.stance)+h*c.touchdown+v*(2*u**3-3*u*u+u);
          y=-c.lift*Math.sin(Math.PI*u)**1.25;
          p['footAngle'+side]=-22*Math.sin(Math.PI*u);
        }
        p['foot'+side]=[x,y];p['knee'+side]=ik(p.hip,[x,y],c.thigh,c.shin);
      }
    }
    if(a.airborne){
      const c=a.airborne,u=clamp((t-c.takeoff)/(c.landing-c.takeoff),0,1);
      p.root[1]-=4*c.height*u*(1-u);p.root[0]+=options.travel?c.distance*u:0;
      const turns=(c.rotation||[[0,0],[1,0]]).map(v=>({t:v[0],angle:v[1]}));
      const angle=channel(turns,u,k=>k.angle),r=angle*Math.PI/180,cs=Math.cos(r),sn=Math.sin(r),[cx,cy]=c.pivot;
      for(const j of joints){const [x,y]=p[j];p[j]=[cx+(x-cx)*cs-(y-cy)*sn,cy+(x-cx)*sn+(y-cy)*cs];}
      p.headTilt+=angle;p.turn=angle;p.footAngleFront=angle;p.footAngleBack=angle;
    }
    if(a.legRig){
      const c=a.legRig;
      for(const side of ['Front','Back'])p['knee'+side]=ik(p.hip,p['foot'+side],c.thigh,c.shin,c.bend);
    }
    const eyes=a.gaze.map(v=>({t:v[0],v:v.slice(1)}));
    p.gaze=[0,1].map(i=>channel(eyes,t,k=>k.v[i]));
    p.blink=Math.max(p.eyeClose||0,...a.blinks.map(b=>Math.max(0,1-Math.abs(t-b)/.085)**1.5));
    // A small, delayed flick of the ink tip follows acceleration; no random
    // wobble. It settles to the same pose at every loop boundary.
    p.tipFlex=a.gait?1.1*Math.sin(2*Math.PI*t/a.duration-.45):
      a.airborne?2.2*Math.sin(Math.PI*clamp((t-a.airborne.takeoff)/(a.airborne.landing-a.airborne.takeoff),0,1)):0;
    if(a.propRig){
      for(const [side,offset] of Object.entries(a.propRig.grips)){
        const weight=p['grip'+side]||0;
        if(weight<=0)continue;
        const target=propPoint(p,offset),j='hand'+side,elbow='elbow'+side;
        p[j]=p[j].map((v,i)=>mix(v,target[i],weight));
        const lens=a.propRig.armLengths||[26,27],solved=ik(lerpPoint(p.neck,p.waist,.08),p[j],...lens,-1);
        p[elbow]=p[elbow].map((v,i)=>mix(v,solved[i],weight));
      }
      if(p.pageGrip>0){
        const target=propPoint(p,[-12.5+25*Math.cos(Math.PI*p.propPage),-18]);
        p.handFront=p.handFront.map((v,i)=>mix(v,target[i],p.pageGrip));
        const elbow=ik(lerpPoint(p.neck,p.waist,.08),p.handFront,...a.propRig.armLengths,-1);
        p.elbowFront=p.elbowFront.map((v,i)=>mix(v,elbow[i],p.pageGrip));
      }
      p.flash=Math.max(0,...(a.events||[]).filter(e=>e.type==='muzzle'&&t>=e.t&&t<e.t+e.duration).map(e=>1-(t-e.t)/e.duration));
    }
    return p;
  }
  function propPoint(p,offset=[0,0]){
    const r=(p.propAngle||0)*Math.PI/180,c=Math.cos(r),s=Math.sin(r);
    return [(p.propX||0)+offset[0]*c-offset[1]*s,(p.propY||0)+offset[0]*s+offset[1]*c];
  }
  function worldJoint(p,j,o={}){
    const s=o.scale??1,f=o.mirror?-1:1;
    return [(o.x??0)+(p[j][0]+p.root[0])*s*f,(o.y??0)+(p[j][1]+p.root[1])*s];
  }
  const fmt=n=>Number(n.toFixed(3)),xy=p=>p.map(fmt).join(' ');
  const lerpPoint=(a,b,t)=>a.map((v,i)=>mix(v,b[i],t));
  function quad(a,b,c,t){return a.map((v,i)=>(1-t)**2*v+2*(1-t)*t*b[i]+t*t*c[i]);}
  function ribbon(points,w0,w1){
    const left=[],right=[];
    for(let i=0;i<points.length;i++){
      const prev=points[Math.max(0,i-1)],next=points[Math.min(points.length-1,i+1)];
      const dx=next[0]-prev[0],dy=next[1]-prev[1],len=Math.hypot(dx,dy)||1;
      const w=mix(w0,w1,i/(points.length-1))/2;
      left.push([points[i][0]-dy/len*w,points[i][1]+dx/len*w]);
      right.push([points[i][0]+dy/len*w,points[i][1]-dx/len*w]);
    }
    const cap=(p,r)=>` M ${fmt(p[0]-r)} ${fmt(p[1])} a ${r} ${r} 0 1 0 ${2*r} 0 a ${r} ${r} 0 1 0 ${-2*r} 0 Z`;
    return 'M '+left.map(xy).join(' L ')+' L '+right.reverse().map(xy).join(' L ')+' Z'+cap(points[0],w0/2)+cap(points[points.length-1],w1/2);
  }
  function limb(a,m,b,w0,w1,round=.36){
    const before=lerpPoint(m,a,round),after=lerpPoint(m,b,round),points=[];
    for(let i=0;i<=5;i++)points.push(lerpPoint(a,before,i/5));
    for(let i=1;i<=12;i++)points.push(quad(before,m,after,i/12));
    for(let i=1;i<=5;i++)points.push(lerpPoint(after,b,i/5));
    return ribbon(points,w0,w1);
  }
  function createProps(el,parent){
    const layer=el('g',{'data-part':'prop','stroke-linejoin':'round','stroke-linecap':'round'},parent);
    const shape={};
    for(let i=1;i<=6;i++)shape[i]=el('g',{'data-prop-kind':i},layer);
    // The paper is an original, schematic page, not a historical facsimile.
    const paper=shape[1];
    el('path',{d:'M -13 -17 L 12 -17 L 14 17 L -11 18 Z',fill:'#ded4bf',stroke:'#8e826e','stroke-width':.8},paper);
    el('path',{d:'M -12.5 -18 L 12.5 -18 L 12.5 17 L -12.5 17 Z',fill:'#fffaf0',stroke:'#938774','stroke-width':.8},paper);
    el('path',{d:'M -8 -12 H 6 M -8 -9 H 9 M -8 -3 H 8 M -8 0 H 6 M -8 3 H 9 M -8 10 H 5',fill:'none',stroke:'#7d817d','stroke-width':.65},paper);
    el('path',{d:'M -8 6 L -6 7 L -4 4 H 8',fill:'none',stroke:'#ab7253','stroke-width':.7},paper);
    const pageGroup=el('g',{'data-part':'turning-page'},paper);
    const page=el('path',{fill:'#fffaf0',stroke:'#938774','stroke-width':.7},pageGroup);
    const pageLines=el('path',{d:'M -8 -12 H 6 M -8 -9 H 9 M -8 -3 H 8 M -8 0 H 6 M -8 3 H 9 M -8 10 H 5',fill:'none',stroke:'#7d817d','stroke-width':.65},pageGroup);
    const gun=shape[2];
    el('path',{d:'M -3 -2 Q -3 3 -7 12 Q -4 16 2 13 L 6 2 L 11 -1 Z',fill:'#805638',stroke:'#503d30','stroke-width':.9},gun);
    el('path',{d:'M -5 -8 L 30 -8 L 31 -2 L 9 1 L -4 -1 Z',fill:'#657178',stroke:'#263640','stroke-width':1},gun);
    el('path',{d:'M 3 1 Q 15 0 12 8 L 4 8',fill:'none',stroke:'#263640','stroke-width':1.3},gun);
    el('path',{d:'M -3 -6 L -7 -11 L -5 -13 L 0 -8',fill:'#263640'},gun);
    el('path',{d:'M 27 -9 L 29 -9 L 29 -7',fill:'#263640'},gun);
    const flash=el('path',{d:'M 31 -5 L 39 -9 L 37 -5 L 46 -4 L 37 -1 L 40 3 L 31 -2 Z',fill:'#e9a347',stroke:'#fff0c3','stroke-width':.7,'data-part':'muzzle-flash'},gun);
    const star=shape[3],points=[];
    for(let i=0;i<10;i++){const r=i%2?2.8:6.6,angle=-Math.PI/2+i*Math.PI/5;points.push([r*Math.cos(angle),r*Math.sin(angle)]);}
    el('path',{d:'M '+points.map(xy).join(' L ')+' Z',fill:'#c94e39',stroke:'#8e352b','stroke-width':.6},star);
    el('circle',{cx:0,cy:-1,r:1.2,fill:'#ffe2ba'},star);
    el('path',{d:'M 0 0 L 0 -40',stroke:'#6b797b','stroke-width':4,fill:'none'},shape[4]);
    el('circle',{cx:0,cy:-40,r:5,fill:'#ae6d40',stroke:'#795137','stroke-width':.8},shape[4]);
    el('circle',{cx:0,cy:0,r:6,fill:'#c8c9bf',stroke:'#6b797b','stroke-width':1.3},shape[4]);
    el('circle',{cx:0,cy:0,r:18,fill:'none',stroke:'#ae7843','stroke-width':2.8},shape[5]);
    el('path',{d:'M -18 0 H 18 M 0 -18 V 18',stroke:'#8c9b96','stroke-width':1.7,fill:'none'},shape[5]);
    el('circle',{cx:0,cy:0,r:4,fill:'#e6decc',stroke:'#8c9b96','stroke-width':1.1},shape[5]);
    for(let i=0;i<5;i++){const a=-Math.PI/2+i*Math.PI*2/5;el('circle',{cx:18*Math.cos(a),cy:18*Math.sin(a),r:2.3,fill:['#c6533e','#688c97','#c8ac5e','#7f986e','#9085ab'][i]},shape[5]);}
    el('path',{d:'M -14 -27 H 17 V 34 H -14 Z',fill:'#d8ddd5',stroke:'#84968e','stroke-width':1.1},shape[6]);
    el('path',{d:'M -9 -21 H 11 M -9 27 H 11',stroke:'#a9b5aa','stroke-width':1.1,fill:'none'},shape[6]);
    return {layer,draw(p,visible){
      const kind=Math.round(p.propKind||0);layer.setAttribute('opacity',visible?(p.propAlpha??1):0);
      layer.setAttribute('transform',`translate(${p.propX||0} ${p.propY||0}) rotate(${p.propAngle||0})`);
      for(const [key,group]of Object.entries(shape))group.setAttribute('display',+key===kind?'inline':'none');
      const f=p.propPage||0,w=25*Math.cos(Math.PI*f),bend=(p.propBend||0)+Math.sin(Math.PI*f)*5;
      page.setAttribute('d',`M -12.5 -18 Q ${-12.5+w/2} ${-18-bend} ${-12.5+w} -18 L ${-12.5+w} 17 Q ${-12.5+w/2} ${17-bend} -12.5 17 Z`);
      pageGroup.setAttribute('opacity',f>0?1:0);
      pageLines.setAttribute('transform',`translate(-12.5 0) scale(${Math.cos(Math.PI*f)} 1) translate(12.5 0)`);
      flash.setAttribute('opacity',p.flash||0);
    }};
  }
  function create(container,defaults={}){
    if(!container)throw new TypeError('A container is required');
    const ns='http://www.w3.org/2000/svg';
    function el(tag,attrs={},parent){const n=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(parent)parent.appendChild(n);return n;}
    const svg=el('svg',{xmlns:ns,viewBox:defaults.viewBox||'0 0 640 640',width:'100%',height:'100%',role:'img','aria-label':'墨影动作'});
    const body=el('g',{'stroke-linecap':'round','stroke-linejoin':'round'},svg);
    const outline=el('g',{'data-part':'outline',fill:'none'},body),paint=el('g',{},body),parts={},rims={};
    for(const name of ['armBack','handBack','legBack','footBack','torso','legFront','footFront','armFront','handFront','neck']){
      const tag=name.startsWith('hand')?'circle':'path';
      rims[name]=el(tag,{},outline);parts[name]=el(tag,{'data-part':name},paint);
    }
    const props=createProps(el,paint);paint.insertBefore(props.layer,parts.handFront);
    const heldBack=el('circle',{'data-part':'gripping-hand-back',r:3.45},paint);
    const headRim=el('g',{},outline),head=el('g',{'data-part':'face'},paint);
    parts.tip=el('path',{},head);parts.head=el('ellipse',{},head);
    rims.tip=el('path',{},headRim);rims.head=el('ellipse',{},headRim);
    const eyePairs=[-4.6,4.6].map(x=>({white:el('ellipse',{cx:x,cy:-1.2,rx:2.9,ry:3.6,fill:'#f8f3e8'},head),pupil:el('ellipse',{fill:'#16212a'},head)}));
    const debug=el('g',{'data-part':'skeleton',fill:'#df8243',stroke:'#fff6e8','stroke-width':.5},body);
    const dots=Object.fromEntries(joints.map(j=>[j,el('circle',{r:1.45},debug)]));
    container.appendChild(svg);
    function set(name,attrs){for(const[k,v]of Object.entries(attrs)){parts[name].setAttribute(k,v);rims[name].setAttribute(k,v);}}
    const api={svg,pose:null,options:null,render(name,t,o={}){return api.draw(sample(name,t,o),o);},
      draw(p,options={}){
        const o={...defaults,...options},s=o.scale??3.1,color=o.color||data.rig.color;
        body.setAttribute('transform',`translate(${o.x??320} ${o.y??520}) scale(${o.mirror?-s:s} ${s}) translate(${xy(p.root)})`);
        paint.setAttribute('fill',color);outline.setAttribute('stroke',o.rimColor||'#e8e1d4');outline.setAttribute('stroke-width',o.rim??0);outline.setAttribute('fill',o.rimColor||'#e8e1d4');
        for(const side of ['Back','Front']){
          const shoulder=lerpPoint(p.neck,p.waist,.08),foot=p['foot'+side],angle=(p['footAngle'+side]||0)*Math.PI/180;
          const cs=Math.cos(angle),sn=Math.sin(angle),ankle=[foot[0]+2.7*sn,foot[1]-2.7*cs];
          // Hand joints mark the outside contact surface. Retreat the palm
          // centre along the forearm so a planted palm cannot sink below it.
          const target=p['hand'+side],elbow=p['elbow'+side],len=Math.hypot(elbow[0]-target[0],elbow[1]-target[1])||1;
          const grip=Math.max(p['grip'+side]||0,side==='Front'?(p.pageGrip||0):0);
          const palm=target.map((v,i)=>v+(elbow[i]-v)/len*3.45*(1-grip));
          if(Math.abs(target[1]+p.root[1])<.001)palm[1]=Math.min(palm[1],-p.root[1]-3.45);
          set('arm'+side,{d:limb(shoulder,elbow,palm,6.5,4.6,.42)});
          set('hand'+side,{cx:palm[0],cy:palm[1],r:3.45});
          if(side==='Back'){heldBack.setAttribute('cx',palm[0]);heldBack.setAttribute('cy',palm[1]);heldBack.setAttribute('fill',o.backColor||(o.color?color:data.rig.backColor));heldBack.setAttribute('opacity',p.gripBack||0);}
          set('leg'+side,{d:limb(p.hip,p['knee'+side],ankle,7.2,5.2,.30)});
          // Foot is a filled sole with its bottom exactly on the contact point.
          const shape='M -3.2 -4.4 Q 1 -5.1 7.5 -3.3 Q 10 -2.5 9.2 0 L -3.2 0 Q -5 -1.7 -3.2 -4.4 Z';
          set('foot'+side,{d:shape,transform:`translate(${xy(foot)}) rotate(${p['footAngle'+side]||0})`});
          for(const n of ['arm','hand','leg','foot'])parts[n+side].setAttribute('fill',side==='Back'?(o.backColor||(o.color?color:data.rig.backColor)):color);
        }
        const control=p.waist.map((v,i)=>2*v-(p.neck[i]+p.hip[i])/2),torso=[];
        for(let i=0;i<=30;i++)torso.push(quad(p.neck,control,p.hip,i/30));
        set('torso',{d:ribbon(torso,15,8.5)});
        set('neck',{d:limb(p.neck,lerpPoint(p.neck,p.head,.5),p.head,8,7)});
        const transform=`translate(${xy(p.head)}) rotate(${p.headTilt}) scale(${xy(p.headScale)})`;
        head.setAttribute('transform',transform);headRim.setAttribute('transform',transform);
        set('head',{cx:0,cy:0,rx:12.5,ry:12.5});
        set('tip',{d:`M -5 -10 C -5 -15 3 -15 ${5+(p.tipFlex||0)} -21 C ${9+(p.tipFlex||0)} -16 7 -10 3 -9 Z`});
        props.draw(p,o.props!==false);
        eyePairs.forEach((pair,i)=>{const x=(i?4.6:-4.6),open=Math.max(.045,1-(p.blink||0)),gaze=p.gaze||[0,0];
          pair.white.setAttribute('ry',3.6*open);
          pair.pupil.setAttribute('cx',x+clamp(gaze[0],-1,1)*1.1);pair.pupil.setAttribute('cy',-1.2+clamp(gaze[1],-1,1)*1.5*open);
          pair.pupil.setAttribute('rx',1.4);pair.pupil.setAttribute('ry',1.6*open);
        });
        debug.setAttribute('opacity',o.skeleton?1:0);for(const j of joints){dots[j].setAttribute('cx',p[j][0]);dots[j].setAttribute('cy',p[j][1]);}
        api.pose=clone(p);api.options=o;return api;
      },
      joint(j){return worldJoint(api.pose,j,{x:defaults.x??320,y:defaults.y??520,scale:defaults.scale??3.1,...api.options});},
      toSVG(){return new XMLSerializer().serializeToString(svg);},destroy(){svg.remove();}};
    return api;
  }
  const api={version:data.version,actions,data,joints,sample,blend,worldJoint,propPoint,create};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else g.ShuyuInk=api;
})(globalThis);
