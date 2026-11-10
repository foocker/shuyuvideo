"""Catch disappearing props across all render times, including loop boundaries."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parents[1];R=ROOT.parents[1]/'output/character-ink/reports'
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);page=b.new_page(viewport={'width':640,'height':640});page.goto((ROOT/'export.html').as_uri())
 result=page.evaluate('''()=>{const failures=[],records=[];for(const [name,a]of Object.entries(ShuyuInk.actions)){if(!a.propRig)continue;let count=0;for(const fps of [24,30,60,120])for(let i=0;i<Math.ceil(a.duration*fps)*(a.loop?3:1);i++){
  const t=i/fps;drawInk(name,t,{loop:a.loop,props:true});const groups=[...rig.svg.querySelectorAll('[data-prop-kind]')],visible=groups.filter(n=>getComputedStyle(n).display!=='none');
  if(visible.length!==1||Number(visible[0].dataset.propKind)!==a.keys[0].pose.propKind)failures.push({name,t,fps,visible:visible.length,kind:rig.pose.propKind});count++;
 }records.push({name,frames:count});}return {passed:!failures.length,records,failures,total:records.reduce((s,r)=>s+r.frames,0)};}''')
 assert result['passed'],result['failures'][:10]
 for name in ['turnWheel','push']:
  for t in [.1,.13333333333333333,1.3,2.2666666666666684]:
   page.evaluate('([a,t])=>drawInk(a,t,{props:true})',[name,t]);page.screenshot(path=str(R/f'prop-stable-{name}-{t:.3f}.png'),omit_background=True)
 b.close()
(R/'prop-visibility-check.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('Props stable:',len(result['records']),'actions,',result['total'],'rendered poses')
