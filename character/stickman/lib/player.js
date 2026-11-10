/* Interactive study UI only. The reusable rig itself has no playback clock. */
(() => {
  const $ = id => document.getElementById(id), lib = ShuyuStickman;
  const rig = lib.create($('actor'), {viewBox:'0 0 640 440', x:300, y:352, scale:1.08});
  let selected = 'pick', time = 0, playing = false, last = 0, sourceTime = -1;
  const video = $('video'), ref = $('reference');
  const refMap = {observe:'look-pick',walk:'walk',run:'run',pick:'look-pick',press:'press',drag:'drag',hang:'hang',recover:'recover'};
  function seekVideo(t) {
    if (video.readyState && !video.seeking && Math.abs(video.currentTime-t) > .025) video.currentTime = t;
    sourceTime = t;
    const frames = StickmanReference[lib.actions[selected].reference.sheet || refMap[selected]], near = frames.reduce((a,b)=>Math.abs(a.time-t)<Math.abs(b.time-t)?a:b);
    const box = near.box, w = ref.clientWidth, h = ref.clientHeight;
    const s = Math.min(w*.84/(box[2]-box[0]),h*.92/(box[3]-box[1]));
    video.style.width = `${1920*s}px`; video.style.height = `${1080*s}px`;
    video.style.left = `${w/2-(box[0]+box[2])*s/2}px`;
    video.style.top = `${h/2-(box[1]+box[3])*s/2}px`;
    $('ref-time').textContent = `${t.toFixed(2)} s`;
  }
  function draw() {
    const a = lib.actions[selected], travel = $('travel').checked && !!(a.gait||a.airborne), mirror = $('mirror').checked;
    const duration = a.duration, local = Math.min(time,duration);
    // Travel preview spans one full cycle in a fixed camera; export remains in place.
    const rightward=(a.airborne?.distance??1)*(mirror?-1:1)>0;
    const x = travel ? (rightward ? 190 : 450) : 300;
    rig.render(selected,local,{loop:false,mirror,color:$('color').value,skeleton:$('skeleton').checked,travel,x,scale:a.airborne ? 0.86 : 1.08});
    $('time').textContent = `${local.toFixed(2)} / ${duration.toFixed(2)} s`;
    $('seek').value = local; $('floor').style.opacity = selected==='hang' ? '0' : '1';
    $('rail').style.opacity = selected==='hang' ? '1' : '0';
    const prop=a.prop;
    $('point').style.opacity = prop ? '1' : '0';
    if (prop) {
      const attached=prop.attach && local>=prop.attachAt;
      const p=attached?rig.joint(prop.attach):[x+prop.ground[0]*1.08*(mirror?-1:1),352+prop.ground[1]*1.08];
      $('point').setAttribute('cx',p[0]);$('point').setAttribute('cy',p[1]-7);
    }
    let source = a.reference.start + local;
    if (selected==='observe') source=a.reference.start+Math.min(local,1.1);
    if (selected==='walk') source=37.4+local;
    if (selected==='run') source=258.1+local;
    if (a.airborne) source=a.reference.start+local/a.duration*(a.reference.end-a.reference.start);
    seekVideo(Math.min(source,a.reference.end));
  }
  function select(name) {
    selected=name;time=0;const a=lib.actions[name];
    $('mirror').checked=['run','press','drag'].includes(name);
    $('travel').checked=false;$('travel').disabled=!(a.gait||a.airborne);
    $('seek').max=a.duration;$('label').textContent=a.label;$('description').textContent=a.description;
    $('source').textContent=`Animation vs. Geometry · ${a.reference.start}–${a.reference.end} s`;
    const notes={observe:'加了回到站姿的收尾，便于衔接。',walk:'整理为 1.2 秒循环，步幅与落脚点已归一化。',run:'整理为 0.6 秒循环；为便于对照，当前显示为原片方向。',pick:'按参考的观察、蹲下、拾取、端详、伸手顺序制作。',press:'原片朝左；资产补足到地面的接触，用作按压动作。',drag:'原片朝左；道具通过手部锚点随动。',hang:'抓点固定；原片出画的腿部已补画，并整理为循环。',recover:'去除镜头缩放；站起过渡补入中间姿态。'};
    $('adaptation').textContent=a.studyNote||notes[name];
    document.querySelectorAll('[data-action]').forEach(b=>{b.classList.toggle('active',b.dataset.action===name);b.setAttribute('aria-pressed',b.dataset.action===name);});draw();
  }
  for(const [id,a] of Object.entries(lib.actions)){const b=document.createElement('button');b.textContent=a.label;b.dataset.action=id;b.onclick=()=>select(id);$('catalog').appendChild(b);}
  function setPlaying(value){playing=value;last=0;$('play').textContent=value?'暂停':'播放';}
  $('play').onclick=()=>{if(time>=lib.actions[selected].duration)time=0;setPlaying(!playing);};
  $('restart').onclick=()=>{time=0;draw();setPlaying(true);};
  $('seek').oninput=()=>{setPlaying(false);time=+$('seek').value;draw();};
  for(const id of ['mirror','skeleton','color','travel'])$(id).oninput=draw;
  function download(blob,name){const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
  function cleanSVG(){const clone=rig.svg.cloneNode(true);clone.querySelector('[data-part="skeleton"]').setAttribute('opacity',0);return new XMLSerializer().serializeToString(clone);}
  $('svg-export').onclick=()=>download(new Blob([cleanSVG()],{type:'image/svg+xml'}),`${selected}-${time.toFixed(2)}.svg`);
  $('png-export').onclick=async()=>{const blob=new Blob([cleanSVG()],{type:'image/svg+xml'}),u=URL.createObjectURL(blob),im=new Image();await new Promise((resolve,reject)=>{im.onload=resolve;im.onerror=reject;im.src=u;});const c=document.createElement('canvas');c.width=1280;c.height=880;c.getContext('2d').drawImage(im,0,0,c.width,c.height);URL.revokeObjectURL(u);c.toBlob(b=>download(b,`${selected}-${time.toFixed(2)}.png`));};
  video.onerror=()=>{$('notice').hidden=false;};video.onloadedmetadata=()=>{$('notice').hidden=true;draw();};
  video.onseeked=()=>{if(Math.abs(video.currentTime-sourceTime)>.04)video.currentTime=sourceTime;};
  $('choose-video').onclick=()=>$('video-file').click();$('video-file').onchange=()=>{const f=$('video-file').files[0];if(f)video.src=URL.createObjectURL(f);};
  window.addEventListener('resize',draw);
  function tick(now){if(playing){if(last)time+=(now-last)/1000*+$('rate').value;const a=lib.actions[selected];if(time>a.duration){if(a.loop)time%=a.duration;else{time=a.duration;setPlaying(false);}}draw();}last=now;requestAnimationFrame(tick);}
  window.stickmanStudy={select,draw,rig,get action(){return selected;},get time(){return time;},seek(t){time=t;draw();}};
  select(selected);requestAnimationFrame(tick);
})();
