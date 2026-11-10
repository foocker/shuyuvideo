/* Preview UI only; clocks and download handlers stay out of the actor runtime. */
(()=>{
 const $=id=>document.getElementById(id),lib=ShuyuInk;
 const rig=lib.create($('actor'),{viewBox:'0 0 640 440',x:300,y:365,scale:2.5});
 const reference=ShuyuStickman.create($('reference'),{viewBox:'0 0 640 440',x:300,y:365,scale:1.1});
 const mini=[110,320,530].map(x=>lib.create($('breakdown'),{viewBox:'0 0 640 440',x,y:290,scale:.85}));
 let selected='observe',time=0,playing=false,last=0;
 const descriptions={observe:'先看，再低头，最后回正。',walk:'重心经过支撑脚，摆臂稍后跟上。',run:'身体前倾，腾空与支撑交替。',pick:'观察 → 蹲下 → 触碰 → 拾起 → 端详。',press:'手接触目标后，再压下重心。',drag:'低姿抓住目标，向后牵引。',hang:'双手固定，身体与腿在下方摆动。',recover:'撑起，坐着观察，收腿站稳。',jump:'蓄力，起跳，屈膝缓冲，站稳。',frontflip:'收腿前翻，打开身体，双脚着地。',backflip:'抬胸后翻，打开身体，屈膝缓冲。'};
 function draw(){
  const a=lib.actions[selected],air=!!a.airborne,travel=$('travel').checked&&!!(a.gait||air),mirror=$('mirror').checked;
  const right=(a.airborne?.distance??1)*(mirror?-1:1)>0,x=travel?(right?190:450):300;
  const scale=(air?1.85:2.5)*(a.viewScale||1),refScale=air?.82:1.1,dark=$('background').value!=='light',basic=!!ShuyuStickman.actions[selected];
  const opts={loop:false,x,y:365,scale,mirror,travel,props:$('props').checked,skeleton:$('skeleton').checked,color:$('color').value,backColor:$('color').value==='#263640'?'#40515b':$('color').value,rim:dark?1.05:0};
  rig.render(selected,time,opts);
  InkGuides.draw($('ink-guide'),a,rig);
  $('ref-title').textContent=basic?'火柴人':'动作拆解';$('ref-subtitle').textContent=basic?'同动作 · 同时钟':'准备 · 动作 · 收势';
  $('reference').hidden=!basic;$('ref-fixtures').toggleAttribute('hidden',!basic);$('ref-overlay').toggleAttribute('hidden',!basic);$('breakdown').hidden=basic;
  if(basic)reference.render(selected,time,{loop:false,x,scale:refScale,mirror,travel,skeleton:$('skeleton').checked});
  else mini.forEach((r,i)=>r.render(selected,a.beats[i],{...opts,x:[110,320,530][i],y:290,scale:.85*(a.viewScale||1),travel:false}));
  for(const [prefix,r,s] of basic?[['ink',rig,scale],['ref',reference,refScale]]:[['ink',rig,scale]]){
   $(prefix+'-floor').setAttribute('opacity',['hang','hangOne','climbUp'].includes(selected)?0:1);$(prefix+'-rail').setAttribute('opacity',selected==='hang'?1:0);
   const anchor=r.joint('handFront');$(prefix+'-rail').setAttribute('y1',anchor[1]);$(prefix+'-rail').setAttribute('y2',anchor[1]);
   const prop=(prefix==='ink'?a:ShuyuStickman.actions[selected]).prop;$(prefix+'-point').setAttribute('opacity',prop?1:0);
   if(prop){const p=prop.attach&&time>=prop.attachAt?r.joint(prop.attach):[x+prop.ground[0]*s*(mirror?-1:1),365+prop.ground[1]*s];$(prefix+'-point').setAttribute('cx',p[0]);$(prefix+'-point').setAttribute('cy',p[1]-5);}
  }
  $('seek').value=time;$('time').textContent=`${time.toFixed(2)} / ${a.duration.toFixed(2)} s`;
 }
 function select(name){selected=name;time=0;playing=false;last=0;$('play').textContent='播放';const a=lib.actions[name];$('seek').max=a.duration;$('label').textContent=a.label;$('description').textContent=descriptions[name]||a.description;$('travel').checked=false;$('travel').disabled=!(a.gait||a.airborne);document.querySelectorAll('[data-action]').forEach(b=>{b.classList.toggle('active',b.dataset.action===name);b.setAttribute('aria-pressed',b.dataset.action===name);});draw();}
 for(const [id,a]of Object.entries(lib.actions)){const b=document.createElement('button');b.textContent=a.label;b.dataset.action=id;b.onclick=()=>select(id);$('catalog').appendChild(b);}
 const setPlaying=value=>{playing=value;last=0;$('play').textContent=value?'暂停':'播放';};
 $('play').onclick=()=>{if(time>=lib.actions[selected].duration)time=0;setPlaying(!playing);};$('restart').onclick=()=>{time=0;draw();setPlaying(true);};
 $('seek').oninput=()=>{setPlaying(false);time=+$('seek').value;draw();};
 for(const id of ['mirror','skeleton','travel','color','props'])$(id).oninput=draw;
 for(const [id,label]of Object.entries(InkCatalog.groups)){const o=document.createElement('option');o.value=id;o.textContent=label;$('category').append(o);}
 $('category').onchange=()=>document.querySelectorAll('[data-action]').forEach(b=>b.hidden=$('category').value!=='all'&&lib.actions[b.dataset.action].category!==$('category').value);
 $('background').onchange=()=>{document.documentElement.style.setProperty('--stage',{light:'#f4f0e7',dark:'#131b22',teal:'#335963'}[$('background').value]);draw();};
 function download(blob,name){const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
 function cleanSVG(){const c=rig.svg.cloneNode(true);c.querySelector('[data-part="skeleton"]').setAttribute('opacity',0);return new XMLSerializer().serializeToString(c);}
 $('svg-export').onclick=()=>download(new Blob([cleanSVG()],{type:'image/svg+xml'}),`ink-${selected}-${time.toFixed(2)}.svg`);
 $('png-export').onclick=async()=>{const u=URL.createObjectURL(new Blob([cleanSVG()],{type:'image/svg+xml'})),im=new Image();await new Promise((resolve,reject)=>{im.onload=resolve;im.onerror=reject;im.src=u;});const c=document.createElement('canvas');c.width=1280;c.height=880;c.getContext('2d').drawImage(im,0,0,c.width,c.height);URL.revokeObjectURL(u);c.toBlob(b=>download(b,`ink-${selected}-${time.toFixed(2)}.png`));};
 function tick(now){if(playing){if(last)time+=(now-last)/1000*+$('rate').value;const a=lib.actions[selected];if(time>a.duration){if(a.loop)time%=a.duration;else{time=a.duration;setPlaying(false);}}draw();}last=now;requestAnimationFrame(tick);}
 window.inkStudy={select,draw,rig,reference,get action(){return selected;},get time(){return time;},seek(t){time=Math.max(0,Math.min(t,lib.actions[selected].duration));draw();}};
 const requested=decodeURIComponent(location.hash.slice(1));select(lib.actions[requested]?requested:selected);requestAnimationFrame(tick);
})();
