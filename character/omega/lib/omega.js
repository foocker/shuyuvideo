/* ShuYu Omega — deterministic SVG character rig, no runtime dependencies. */
(function(root,factory){
  const shape=typeof module==='object'&&module.exports?require('./omega-shape.js'):root.ShuyuOmegaShape;
  const api=factory(shape);if(typeof module==='object'&&module.exports)module.exports=api;else root.ShuyuOmega=api;
})(globalThis,function(shape){
  'use strict';
  const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
  const lerp=(a,b,t)=>a+(b-a)*t;
  const ease=t=>(t=clamp(t),t*t*t*(10+t*(-15+6*t)));
  const span=(t,a,b)=>ease((t-a)/(b-a));
  const gate=(t,a,b,c,d)=>span(t,a,b)*(1-span(t,c,d));
  const blink=(t,c,w=.17)=>Math.abs(t-c)>=w?1:1-Math.pow(Math.cos((t-c)/w*Math.PI/2),2);
  const mod=(n,d)=>((n%d)+d)%d;
  const hands={relaxed:[.38,.32,.25,.55],open:[1,1,.9,1],fist:[.03,.03,.03,.15],point:[1,.03,.03,.25],thumb:[.03,.03,.03,1]};
  const palettes={
    ink:{label:'墨色',body:'#141413',face:'#fffdf6',paper:'#eaeae2'},
    clay:{label:'陶土',body:'#cc5a36',face:'#241c19',paper:'#f7f3ed'},
    blue:{label:'参考蓝',body:'#13a9dc',face:'#101c23',paper:'#111313'},
    jade:{label:'青绿',body:'#277f78',face:'#ffffff',paper:'#f1f3e9'}
  };
  const expressions={
    neutral:{label:'平静',smile:.28},happy:{label:'开心',smile:1,eyeL:.88,eyeR:.9,browUpL:4,browUpR:5},
    curious:{label:'好奇',smile:.1,browR:-.24,browUpR:10,eyeL:.86},
    thinking:{label:'思考',smile:-.15,eyeL:.72,eyeR:.9,browL:.17,browR:-.2,lookX:.65,lookY:-.55},
    surprised:{label:'惊讶',open:.95,eyeL:1.07,eyeR:1.1,browUpL:8,browUpR:10,smile:0},
    doubtful:{label:'疑惑',eyeL:.62,eyeR:.97,browL:.18,browR:-.24,browUpR:8,smile:-.3},
    sad:{label:'难过',smile:-1,eyeL:.8,eyeR:.82,browL:-.25,browR:.25,lookY:.3},
    focused:{label:'认真',eyeL:.78,eyeR:.78,browL:.23,browR:-.23,smile:0},
    sleepy:{label:'困倦',eyeL:.42,eyeR:.38,browUpL:-8,browUpR:-7,smile:0,lookY:.5},
    wink:{label:'眨单眼',eyeL:.025,smile:.95,browUpR:4},
    talk:{label:'说话',smile:.5,talk:1}
  };
  const actions={
    idle:{label:'待机呼吸',duration:4,loop:true,description:'安静等待，目光保持交流。'},
    blink:{label:'自然眨眼',duration:2.4,loop:false,description:'眼睑闭合，再轻轻睁开。'},
    look:{label:'四处看看',duration:4.8,loop:false,description:'眼睛先看过去，身体随后跟上。'},
    wave:{label:'挥手招呼',duration:3.6,loop:false,description:'看向你，抬手打个招呼。'},
    pointRight:{label:'指向右侧',duration:3.4,loop:false,description:'用目光和食指，引出右侧的内容。'},
    pointLeft:{label:'指向左侧',duration:3.4,loop:false,description:'用目光和食指，引出左侧的内容。'},
    explain:{label:'开口讲解',duration:4.8,loop:false,description:'交替展开双手，配合说话嘴型。'},
    think:{label:'歪头思考',duration:4.4,loop:false,description:'稍微歪头，把问题想一想。'},
    nod:{label:'点头认可',duration:2.6,loop:false,description:'轻点两次头，给出肯定的回应。'},
    shake:{label:'摇头否定',duration:2.8,loop:false,description:'目光与身体左右摆动。'},
    shrug:{label:'摊手疑问',duration:3.2,loop:false,description:'摊开双手，留一个问题。'},
    jump:{label:'轻轻跳跃',duration:2.6,loop:false,description:'先蹲下，再起跳，落地后缓冲。'},
    walk:{label:'迈步行走',duration:2,loop:true,description:'两端笔画交替迈步，支撑脚落稳。'},
    bow:{label:'鞠躬致意',duration:3.2,loop:false,description:'脚底站稳，低头，再缓缓起身。'},
    celebrate:{label:'开心庆祝',duration:4,loop:false,description:'双手抬起，带一点轻快的弹跳。'}
  };
  function rest(){return {
    rootX:0,rootY:0,bodyX:0,bodyY:0,lean:0,sx:1,sy:1,
    footLX:0,footLY:0,footRX:0,footRY:0,
    lookX:0,lookY:0,eyeL:1,eyeR:1,browL:0,browR:0,browUpL:0,browUpR:0,
    smile:.28,open:0,talk:0,
    armL:{ex:-179,ey:-143,x:-193,y:-84,angle:-165,fingers:[...hands.relaxed]},
    armR:{ex:179,ey:-143,x:193,y:-84,angle:165,fingers:[...hands.relaxed]}
  };}
  function blend(a,b,t){
    if(typeof a==='number')return lerp(a,b,t);
    if(Array.isArray(a))return a.map((v,i)=>blend(v,b[i],t));
    const result={};for(const key of Object.keys(a))result[key]=blend(a[key],b[key],t);return result;
  }
  function mood(p,name,amount=1){for(const [key,value] of Object.entries(expressions[name]||{}))if(typeof value==='number')p[key]=lerp(p[key],value,amount);}
  function arm(p,side,target,amount=1){
    const a=p['arm'+side];for(const key of ['ex','ey','x','y','angle'])if(key in target)a[key]=lerp(a[key],target[key],amount);
    if(target.hand)a.fingers=a.fingers.map((v,i)=>lerp(v,hands[target.hand][i],amount));
  }
  function sample(action='idle',seconds=0,options={}){
    if(!actions[action])throw new Error('Unknown Omega action: '+action);
    const spec=actions[action],t=spec.loop?mod(seconds,spec.duration):clamp(seconds,0,spec.duration),u=t/spec.duration,p=rest();
    const g=gate(u,.035,.23,.76,1);
    p.bodyY=-1.3*Math.sin(2*Math.PI*u);p.sy=1+.006*Math.sin(2*Math.PI*u);
    let closure=action==='idle'?blink(t,2.75):1;
    if(action==='blink'){closure=blink(t,.72,.19)*blink(t,1.13,.16);}
    if(action==='look'){
      const keys=[[0,0,0],[.17,-1,.1],[.38,1,0],[.65,.2,-.9],[.84,0,0],[1,0,0]];
      let k=0;while(k<keys.length-2&&u>keys[k+1][0])k++;
      const a=keys[k],b=keys[k+1],v=ease((u-a[0])/(b[0]-a[0]));p.lookX=lerp(a[1],b[1],v);p.lookY=lerp(a[2],b[2],v);
      p.lean=p.lookX*6;p.bodyX=p.lookX*3;mood(p,'curious',g*.7);
    }
    if(action==='wave'){
      arm(p,'R',{ex:174,ey:-197,x:218,y:-285,angle:-12+Math.sin((u-.23)*Math.PI*9)*23,hand:'open'},g);
      arm(p,'L',{ex:-167,ey:-130,x:-177,y:-99,angle:-150},g*.5);
      p.lean=-6*g;p.smile=lerp(p.smile,1,g);p.eyeL=lerp(1,.9,g);p.eyeR=lerp(1,.92,g);
    }
    if(action==='pointRight'||action==='pointLeft'){
      const s=action==='pointRight'?1:-1,side=s===1?'R':'L';
      p.lookX=s*gate(u,0,.14,.77,.98);p.lean=s*7*g;
      arm(p,side,{ex:s*191,ey:-188,x:s*271,y:-202,angle:s*90,hand:'point'},g);
      arm(p,s===1?'L':'R',{ex:-s*191,ey:-121,x:-s*130,y:-92,angle:-s*90,hand:'fist'},g);
      p.browUpL=3*g;p.browUpR=5*g;
    }
    if(action==='explain'){
      const left=gate(u,.07,.26,.51,.72),right=gate(u,.36,.56,.77,1);
      arm(p,'L',{ex:-183,ey:-161,x:-245,y:-187,angle:-72,hand:'open'},left);
      arm(p,'R',{ex:187,ey:-147,x:239,y:-183,angle:76,hand:'open'},right);
      p.lookX=.25*(right-left);p.lean=4*(right-left);p.open=g*(.18+.55*Math.pow(Math.sin(t*8.5),2));p.smile=.6;
    }
    if(action==='think'){
      mood(p,'thinking',g);p.lean=-8*g;
      arm(p,'R',{ex:215,ey:-202,x:95,y:-284,angle:-18,hand:'point'},g);
      arm(p,'L',{ex:-180,ey:-123,x:-129,y:-98,angle:-85,hand:'fist'},g);
      p.bodyY=2*g;
    }
    if(action==='nod'){
      const n=Math.pow(Math.sin(Math.PI*3*u),2)*g;
      p.sy=1-.065*n;p.bodyY=7*n;p.lookY=.5*n;p.smile=lerp(p.smile,.8,g);
    }
    if(action==='shake'){
      const n=Math.sin(Math.PI*6*u)*g;p.bodyX=10*n;p.lean=7*n;p.lookX=.7*n;p.smile=-.25*g;
    }
    if(action==='shrug'){
      arm(p,'L',{ex:-184,ey:-147,x:-227,y:-214,angle:-65,hand:'open'},g);
      arm(p,'R',{ex:184,ey:-147,x:227,y:-214,angle:65,hand:'open'},g);
      mood(p,'doubtful',g);p.bodyY=-7*g;p.sy=1-.015*g;
    }
    if(action==='jump'){
      const squat=gate(t,0,.3,.43,.62),landing=gate(t,1.52,1.66,1.79,2.17);
      const flight=clamp((t-.56)/1.04);p.rootY=t>.56&&t<1.6?-96*4*flight*(1-flight):0;
      p.sy=1-.13*squat-.11*landing+.055*gate(t,.48,.64,1.4,1.59);p.sx=1+.055*(squat+landing);
      arm(p,'L',{ex:-183,ey:-203,x:-218,y:-255,angle:-22,hand:'open'},gate(t,.38,.66,1.38,1.8));
      arm(p,'R',{ex:183,ey:-203,x:218,y:-255,angle:22,hand:'open'},gate(t,.42,.7,1.4,1.84));
      p.open=.65*gate(t,.55,.74,1.28,1.6);p.smile=lerp(.28,1,gate(t,1.6,1.9,2.2,2.6));
    }
    if(action==='walk'){
      for(const [side,phase] of [['L',t],['R',mod(t+1,2)]]){
        const swing=phase-1;
        // Hermite swing: local foot velocity is -28 at BOTH contacts, so
        // moving mode's +28 root velocity leaves the planted foot stationary.
        p['foot'+side+'X']=phase<1?14-28*phase:-14-28*swing+168*swing*swing-112*swing*swing*swing;
        p['foot'+side+'Y']=phase<1?0:-43*Math.pow(Math.sin(Math.PI*(phase-1)),2);
      }
      p.bodyY=-4+3*Math.cos(2*Math.PI*t);p.lean=4*Math.sin(Math.PI*t);p.lookX=.2;
      arm(p,'L',{ex:-177,ey:-145,x:-193-13*Math.sin(Math.PI*t),y:-91-10*Math.cos(Math.PI*t),angle:-160});
      arm(p,'R',{ex:177,ey:-145,x:193-13*Math.sin(Math.PI*t),y:-91+10*Math.cos(Math.PI*t),angle:160});
      if(options.travel)p.rootX=28*seconds;
    }
    if(action==='bow'){
      const b=gate(u,.04,.36,.55,.98);p.sy=1-.20*b;p.sx=1+.025*b;p.lookY=.9*b;p.eyeL=1-.52*b;p.eyeR=1-.52*b;
      arm(p,'L',{ex:-167,ey:-100,x:-136,y:-58,angle:-165,hand:'relaxed'},b);
      arm(p,'R',{ex:167,ey:-100,x:136,y:-58,angle:165,hand:'relaxed'},b);p.smile=.6;
    }
    if(action==='celebrate'){
      arm(p,'L',{ex:-182,ey:-222,x:-193,y:-318,angle:-25,hand:'open'},g);
      arm(p,'R',{ex:182,ey:-222,x:193,y:-318,angle:25,hand:'open'},gate(u,.07,.26,.78,1));
      p.rootY=-22*Math.pow(Math.sin(t*Math.PI*2),2)*g;p.sy=1-.035*Math.sin(t*Math.PI*4)*g;mood(p,'happy',g);
    }
    if(options.expression&&options.expression!=='auto')mood(p,options.expression);
    if(p.talk)p.open=.2+.55*Math.pow(Math.sin(seconds*8.5),2);
    p.eyeL*=closure;p.eyeR*=lerp(1,closure,.97);
    if(options.look){p.lookX=clamp(options.look[0],-1,1);p.lookY=clamp(options.look[1],-1,1);}
    for(const side of ['L','R']){
      const h=options[side==='L'?'leftHand':'rightHand'];if(h&&h!=='auto'&&hands[h])p['arm'+side].fingers=[...hands[h]];
    }
    if(options.mouth!==undefined)p.open=clamp(options.mouth);
    return p;
  }
  function warp(point,p){
    const [x,y]=point,w=span(y,-170,-8),s=x<0?'L':'R';
    return [x*(1+(p.sx-1)*(1-w))+(p.bodyX+p.lean*(-y/300))*(1-w)+p['foot'+s+'X']*w,
      y*(1+(p.sy-1)*(1-w))+p.bodyY*(1-w)+p['foot'+s+'Y']*w];
  }
  function outline(p){return shape.commands.map(([op,...points])=>op+points.map(pt=>warp(pt,p).map(n=>n.toFixed(3)).join(',')).join(' ')).join(' ');}
  let instance=0;
  function create(container,options={}){
    const ns='http://www.w3.org/2000/svg',doc=container.ownerDocument;
    const id=options.id||'omega-'+(++instance);
    const svg=doc.createElementNS(ns,'svg');svg.setAttribute('xmlns',ns);svg.setAttribute('viewBox',options.viewBox||'-350 -480 700 540');svg.setAttribute('role','img');svg.setAttribute('aria-label','数语 Omega 角色');
    svg.style.cssText='display:block;width:100%;height:100%;overflow:visible';container.appendChild(svg);
    function el(tag,attrs={},parent=svg){const n=doc.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);parent.appendChild(n);return n;}
    function attr(n,values){for(const [k,v] of Object.entries(values))n.setAttribute(k,v);}
    const defs=el('defs');
    const shadow=el('ellipse',{cx:0,cy:8,rx:154,ry:10,fill:'#141413',opacity:.09,'data-part':'shadow'});
    const actor=el('g',{'data-part':'actor'}),arms={},handNodes={};
    for(const side of ['L','R']){
      arms[side]=el('path',{fill:'none','stroke-width':10,'stroke-linecap':'round','data-part':'arm-'+side},actor);
      const h=el('g',{'data-part':'hand-'+side},actor);el('ellipse',{cx:0,cy:-9,rx:11,ry:14},h);
      const fingers=Array.from({length:4},()=>el('path',{fill:'none','stroke-width':6.5,'stroke-linecap':'round'},h));handNodes[side]={group:h,fingers};
    }
    const body=el('path',{'data-part':'omega-body','stroke-linejoin':'round','stroke-width':1.4},actor);
    const mouth=el('path',{'data-part':'mouth','stroke-linecap':'round','stroke-linejoin':'round'},actor);
    const eyes={};
    for(const side of ['L','R']){
      const group=el('g',{'data-part':'eye-'+side},actor),clip=el('clipPath',{id:id+'-clip-'+side},defs),clipShape=el('ellipse',{},clip);
      const white=el('ellipse',{'stroke-width':2.3},group);
      const pupilGroup=el('g',{'clip-path':'url(#'+id+'-clip-'+side+')'},group);
      const pupil=el('ellipse',{fill:'#141413'},pupilGroup),highlight=el('circle',{r:2.7,fill:'#fffdf6'},pupilGroup);
      const lid=el('path',{fill:'none','stroke-width':3.3,'stroke-linecap':'round'},group);
      const brow=el('path',{fill:'none','stroke-width':3.8,'stroke-linecap':'round'},group);
      eyes[side]={white,pupil,highlight,lid,brow,clipShape};
    }
    let lastPose=rest(),lastSettings={};
    function draw(p,settings={}){
      lastPose=p;lastSettings=settings;
      const color=palettes[settings.palette||options.palette||'ink']||palettes.ink;
      const s=options.scale||1,x=(options.x||0)+p.rootX*s,y=(options.y||0)+p.rootY*s;
      attr(actor,{transform:`translate(${x} ${y}) scale(${s})`});
      const ground=(options.y||0)+8*s;
      attr(shadow,{cx:x,cy:ground,rx:154*s*(1+p.rootY/500),ry:10*s,opacity:settings.shadow===false?0:.09*clamp(1+p.rootY/150,.15,1)});
      attr(body,{d:outline(p),fill:color.body,stroke:color.body});
      for(const side of ['L','R']){
        const a=p['arm'+side],sgn=side==='L'?-1:1,root=warp([sgn*130,-177],p);
        const ex=a.ex+p.bodyX*.6,ey=a.ey+p.bodyY*.45,wx=a.x+p.bodyX*.35,wy=a.y+p.bodyY*.25;
        attr(arms[side],{d:`M${root} Q${ex},${ey} ${wx},${wy}`,stroke:color.body});
        const h=handNodes[side];attr(h.group,{transform:`translate(${wx} ${wy}) rotate(${a.angle})`,fill:color.body,stroke:color.body});
        for(let i=0;i<3;i++){
          const fx=[-6,1,7][i],len=[15,18,13][i]*a.fingers[i];
          attr(h.fingers[i],{d:`M${fx},-18 Q${fx-1},${-21-len*.5} ${fx-1},${-21-len}`});
        }
        attr(h.fingers[3],{d:`M-8,-7 Q${-11-4*a.fingers[3]},-12 ${-11-9*a.fingers[3]},${-10-5*a.fingers[3]}`});
      }
      const mouthCenter=warp([0,-290.5],p),mx=mouthCenter[0],my=mouthCenter[1],op=clamp(p.open);
      if(op>.05){
        const rx=8+4*op,ry=1.5+5.4*op;
        attr(mouth,{d:`M${mx-rx},${my} C${mx-rx},${my-ry} ${mx+rx},${my-ry} ${mx+rx},${my} C${mx+rx},${my+ry} ${mx-rx},${my+ry} ${mx-rx},${my}Z`,fill:color.face,stroke:'none'});
      }else attr(mouth,{d:`M${mx-11},${my-2} Q${mx},${my-2+9*p.smile} ${mx+11},${my-2}`,fill:'none',stroke:color.face,'stroke-width':2.1});
      for(const side of ['L','R']){
        const e=eyes[side],sign=side==='L'?-1:1,o=clamp(p['eye'+side],.025,1.15),center=warp([sign*37,-318+27*(1-o)],p);
        const cx=center[0],cy=center[1],rx=25,ry=32*o;
        attr(e.white,{cx,cy,rx,ry,fill:'#fffdf6',stroke:color.body,opacity:span(o,.025,.12)});attr(e.clipShape,{cx,cy,rx:rx-1,ry:Math.max(.1,ry-1)});
        const px=cx+clamp(p.lookX,-1,1)*10,py=cy+clamp(p.lookY,-1,1)*12*o;
        attr(e.pupil,{cx:px,cy:py,rx:10.5,ry:11.5*o,opacity:span(o,.025,.12)});
        attr(e.highlight,{cx:px-3.4,cy:py-4.2*o,r:2.7*Math.min(1,o),opacity:span(o,.15,.4)});
        attr(e.lid,{d:`M${cx-20},${cy} Q${cx},${cy+3} ${cx+20},${cy}`,stroke:color.body,opacity:1-span(o,.025,.12)});
        const tilt=p['brow'+side]*25,by=cy-ry-10-p['browUp'+side];
        attr(e.brow,{d:`M${cx-16},${by-tilt} Q${cx},${by-5} ${cx+16},${by+tilt}`,stroke:color.body});
      }
      return p;
    }
    function render(action,t,settings={}){return draw(sample(action,t,settings),settings);}
    function toSVG({shadow:includeShadow=false}={}){
      const copy=svg.cloneNode(true);if(!includeShadow)copy.querySelector('[data-part="shadow"]').remove();
      copy.removeAttribute('style');copy.setAttribute('width','1400');copy.setAttribute('height','1080');
      return new XMLSerializer().serializeToString(copy);
    }
    draw(rest());
    return {svg,draw,render,toSVG,destroy(){svg.remove();},get pose(){return lastPose;},get settings(){return lastSettings;}};
  }
  const showcase=['wave','look','think','explain','pointRight','shrug','jump','walk','bow'];
  function showcaseAt(t){
    const index=Math.min(showcase.length-1,Math.floor(clamp(t,0,35.999)/4)),action=showcase[index],local=clamp(t-index*4,0,4);
    const p=sample(action,actions[action].loop?local:local/4*actions[action].duration);
    const weight=gate(local,0,.32,3.68,4);
    return {action,index,pose:blend(rest(),p,weight)};
  }
  return {version:'1.0.0',actions,expressions,palettes,hands,rest,sample,blend,warp,outline,create,showcase,showcaseAt,duration:36};
});
