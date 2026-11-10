/* Human-operated preview clock; the reusable rig itself is time-independent. */
(()=>{
  const api=ShuyuOmega,$=id=>document.getElementById(id),rig=api.create($('actor'),{id:'study'});
  let action='wave',t=0,playing=true,previous=performance.now(),palette='ink',look=null,transition=null;
  const selected=()=>({palette,expression:$('expression').value,leftHand:$('hand-left').value,rightHand:$('hand-right').value,look,shadow:!$('checker').checked});
  function draw(){
    let pose=api.sample(action,t,selected());
    if(transition){const amount=Math.min(1,(performance.now()-transition.at)/240);pose=api.blend(transition.pose,pose,amount*amount*(3-2*amount));if(amount===1)transition=null;}
    rig.draw(pose,selected());$('seek').value=t;$('time').textContent=t.toFixed(2)+' / '+api.actions[action].duration.toFixed(2);$('play').textContent=playing?'暂停':'播放';
  }
  function choose(name,{animate=true}={}){
    if(animate)transition={pose:rig.pose,at:performance.now()};else transition=null;
    action=name;t=0;playing=true;$('seek').max=api.actions[action].duration;$('stage-name').textContent=api.actions[action].label;
    document.querySelectorAll('[data-action]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.action===name));draw();
  }
  for(const [id,item] of Object.entries(api.actions)){
    const button=document.createElement('button');button.textContent=item.label;button.dataset.action=id;button.title=item.description;button.onclick=()=>choose(id);$('actions').appendChild(button);
  }
  for(const [id,item] of Object.entries(api.expressions)){const option=document.createElement('option');option.value=id;option.textContent=item.label;$('expression').appendChild(option);}
  for(const id of ['hand-left','hand-right'])for(const [value,text] of Object.entries({auto:'跟随动作',relaxed:'放松',open:'张开',fist:'握拳',point:'食指指向',thumb:'伸出拇指'})){
    const option=document.createElement('option');option.value=value;option.textContent=text;$(id).appendChild(option);
  }
  for(const [id,item] of Object.entries(api.palettes)){
    const b=document.createElement('button');b.className='swatch';b.style.setProperty('--color',item.body);b.title=item.label;b.setAttribute('aria-label',item.label);b.dataset.palette=id;
    b.onclick=()=>{palette=id;applyPalette();draw()};$('palettes').appendChild(b);
  }
  function applyPalette(){
    document.querySelectorAll('[data-palette]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.palette===palette));
    $('stage').style.backgroundColor=api.palettes[palette].paper;$('stage-name').style.color=palette==='blue'?'#b8bcb8':'#68685f';
  }
  $('play').onclick=()=>{playing=!playing;if(playing&&t>=api.actions[action].duration)t=0;previous=performance.now();draw()};
  $('restart').onclick=()=>choose(action,{animate:false});
  $('seek').oninput=()=>{t=+$('seek').value;playing=false;transition=null;draw()};
  for(const id of ['expression','hand-left','hand-right'])$(id).onchange=()=>{transition={pose:rig.pose,at:performance.now()};draw()};
  $('checker').onchange=()=>{$('stage').classList.toggle('checker',$('checker').checked);draw()};
  document.querySelectorAll('[data-look]').forEach(b=>b.onclick=()=>{look=b.dataset.look.split(',').map(Number);$('follow').checked=false;draw()});
  $('gaze-auto').onclick=()=>{look=null;$('follow').checked=false;draw()};
  $('follow').onchange=()=>{look=null;draw()};
  $('actor').onpointermove=e=>{if(!$('follow').checked)return;const pt=rig.svg.createSVGPoint();pt.x=e.clientX;pt.y=e.clientY;const local=pt.matrixTransform(rig.svg.getScreenCTM().inverse());look=[local.x/180,(local.y+310)/160];draw()};
  $('actor').onpointerleave=()=>{if($('follow').checked){look=null;draw()}};
  function download(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);$('status').textContent='已导出 '+name;}
  $('save-svg').onclick=()=>download(new Blob([rig.toSVG()],{type:'image/svg+xml'}),'shuyu-omega-'+action+'.svg');
  $('save-png').onclick=async()=>{
    const url=URL.createObjectURL(new Blob([rig.toSVG()],{type:'image/svg+xml'})),img=new Image();
    await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=reject;img.src=url});
    const canvas=document.createElement('canvas');canvas.width=1400;canvas.height=1080;canvas.getContext('2d').drawImage(img,0,0);URL.revokeObjectURL(url);
    canvas.toBlob(blob=>download(blob,'shuyu-omega-'+action+'.png'));
  };
  function tick(now){
    const dt=Math.min(.1,(now-previous)/1000);previous=now;
    if(playing){t+=dt*+$('speed').value;const d=api.actions[action].duration;if(t>=d){if($('cycle').value==='repeat')t%=d;else{t=d;playing=false;}}}
    draw();requestAnimationFrame(tick);
  }
  applyPalette();choose('wave',{animate:false});requestAnimationFrame(tick);
  window.omegaStudy={rig,choose(name){choose(name,{animate:false});playing=false;draw()},seek(value){t=value;playing=false;transition=null;draw()},set(options){if(options.expression)$('expression').value=options.expression;if(options.palette){palette=options.palette;applyPalette()}look=options.look||null;transition=null;draw()},get state(){return{action,t,playing}}};
})();
