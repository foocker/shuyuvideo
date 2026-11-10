"""Capture every catalogue item and cut in the real, mounted composition."""
from pathlib import Path
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
import io,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'output/character-ink';R=OUT/'reports'
html=(OUT/'project/compositions/showcase.html').read_text(encoding='utf8').replace('<template>','').replace('</template>','')
errors=[]
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);page=b.new_page(viewport={'width':1920,'height':1080});page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto((OUT/'project/index.html').as_uri())
 page.evaluate('html=>{document.body.innerHTML=html;for(const script of [...document.body.querySelectorAll("script")]){const n=document.createElement("script");n.textContent=script.textContent;script.replaceWith(n);}}',html)
 page.wait_for_function('window.__inkShowcase')
 shots=page.evaluate('__inkShowcase.shots');frames=[]
 sheet=Image.new('RGB',(1440,300*((len(shots)+2)//3)),'#f4f0e7');d=ImageDraw.Draw(sheet)
 phone=Image.new('RGB',(1080,230*((len(shots)+2)//3)),'#f4f0e7');pd=ImageDraw.Draw(phone)
 for i,s in enumerate(shots):
  a=page.evaluate('id=>ShuyuInk.actions[id]',s['a']);t=s['start']+s['lead']+a['beats'][1]
  page.evaluate('t=>__inkShowcase.draw(t)',t);im=Image.open(io.BytesIO(page.screenshot())).convert('RGB');frames.append({'action':s['a'],'time':t})
  if s['a'] in ['paperFlip','gunFire','fallBack','fallForward','climbUp','release']:im.save(R/f'catalog-{s["a"]}.png')
  thumb=im.resize((480,270));x=i%3*480;y=i//3*300;sheet.paste(thumb,(x,y));d.text((x+10,y+277),f'{s["a"]} {t:.2f}s',fill='#263640')
  thumb=im.resize((360,203));x=i%3*360;y=i//3*230;phone.paste(thumb,(x,y));pd.text((x+8,y+207),s['a'],fill='#263640')
 sheet.save(R/'catalog-beats.jpg',quality=94);phone.save(R/'catalog-phone.jpg',quality=94)
 seam=Image.new('RGB',(1440,180*(len(shots)-1)),'#f4f0e7');sd=ImageDraw.Draw(seam)
 for i,s in enumerate(shots[1:]):
  for j,offset in enumerate([-.2,-1/30,0,1/30,.2]):
   t=s['start']+offset;page.evaluate('t=>__inkShowcase.draw(t)',t);im=Image.open(io.BytesIO(page.screenshot())).convert('RGB').resize((288,162));seam.paste(im,(j*288,i*180));sd.text((j*288+5,i*180+164),f'{t:.3f}s',fill='#263640')
 seam.save(R/'catalog-seams.jpg',quality=90)
 b.close()
assert not errors,errors
(R/'catalog-check.json').write_text(json.dumps({'passed':True,'runtimeErrors':errors,'actions':frames,'cuts':len(shots)-1,'cutFrames':(len(shots)-1)*5},indent=2),encoding='utf8')
print('Catalogue captured:',len(frames),'actions and',len(shots)-1,'cuts')
