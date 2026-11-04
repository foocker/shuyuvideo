"""Exercise the real browser controls, deterministic draws and transparent downloads."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from workspace import output_dir, font_path
from shuyu import prepare_project
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
ROOT=prepare_project('character');OUT=output_dir('character');OUT.mkdir(parents=True,exist_ok=True)
errors=[];seek_checks=[];shots=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1100},accept_downloads=True)
    page.on('pageerror',lambda e:errors.append(str(e)));page.goto((ROOT/'study.html').as_uri());page.wait_for_function('window.omegaStudy');page.evaluate('document.fonts.ready')
    catalog=page.evaluate('ShuyuOmega.actions')
    for action,entry in catalog.items():
        t=entry['duration']*.43
        page.evaluate('([a,t])=>{omegaStudy.choose(a);omegaStudy.seek(t)}',[action,t])
        first=page.locator('#actor').screenshot()
        page.evaluate("omegaStudy.choose('idle');omegaStudy.seek(3.2)")
        page.evaluate('([a,t])=>{omegaStudy.choose(a);omegaStudy.seek(t)}',[action,t])
        repeated=page.locator('#actor').screenshot();same=hashlib.sha256(first).digest()==hashlib.sha256(repeated).digest()
        seek_checks.append({'action':action,'time':t,'identicalAfterSeek':same});assert same,action
        dest=OUT/'poses'/f'{action}.png';dest.parent.mkdir(exist_ok=True);dest.write_bytes(repeated);shots.append((dest,entry['label']))
    # Two independent SVG instances cannot share eye clipping ids.
    ids=page.evaluate("""()=>{const boxes=[document.createElement('div'),document.createElement('div')];const rigs=boxes.map(b=>{document.body.appendChild(b);return ShuyuOmega.create(b)});const ids=rigs.flatMap(r=>Array.from(r.svg.querySelectorAll('clipPath')).map(n=>n.id));rigs.forEach(r=>r.destroy());boxes.forEach(b=>b.remove());return ids}""")
    assert len(set(ids))==4,ids
    # Embedded actors scale their locomotion and jump offset with the body.
    scaled=page.evaluate("""()=>{const box=document.createElement('div');document.body.appendChild(box);const r=ShuyuOmega.create(box,{scale:2,x:20,y:30});const p=ShuyuOmega.sample('jump',1.08);r.draw(p);const value=r.svg.querySelector('[data-part=actor]').transform.baseVal.consolidate().matrix.f;r.destroy();box.remove();return [value,30+2*p.rootY]}""")
    assert abs(scaled[0]-scaled[1])<.0001,scaled
    page.evaluate("omegaStudy.choose('wave');omegaStudy.seek(1.4)")
    page.locator('#expression').select_option('happy');page.wait_for_timeout(300)
    page.locator('[data-look="1,0"]').click();assert page.evaluate('omegaStudy.rig.pose.lookX')==1
    page.locator('#gaze-auto').click();page.locator('#checker').check()
    for button,suffix in [('save-svg','svg'),('save-png','png')]:
        with page.expect_download() as download:page.locator('#'+button).click()
        download.value.save_as(OUT/f'omega-wave.{suffix}')
    image=Image.open(OUT/'omega-wave.png');assert image.mode=='RGBA'
    alpha=image.getchannel('A');assert alpha.getextrema()==(0,255)
    assert 0<sum(1 for v in alpha.getdata() if v)>image.width*image.height*.02
    assert image.getpixel((0,0))[3]==0
    page.locator('#checker').uncheck();page.locator('#expression').select_option('auto');page.wait_for_timeout(300)
    page.evaluate("omegaStudy.choose('wave');omegaStudy.seek(1.4)");page.screenshot(path=str(OUT/'playground.png'))
    page.locator('#play').click();start=page.evaluate('omegaStudy.state.t');page.wait_for_timeout(200);assert page.evaluate('omegaStudy.state.t')>start
    page.locator('#play').click()
    browser.close()
font=ImageFont.truetype(str(font_path('sans')),22)
sheet=Image.new('RGB',(1500,((len(shots)+4)//5)*330),'#eaeae2');draw=ImageDraw.Draw(sheet)
for i,(f,label) in enumerate(shots):
    im=Image.open(f).convert('RGB');im.thumbnail((300,285));x=i%5*300;y=i//5*330;sheet.paste(im,(x+(300-im.width)//2,y));draw.text((x+18,y+294),label,font=font,fill='#141413')
sheet.save(OUT/'action-sheet.png')
report={'scriptErrors':errors,'actions':seek_checks,'independentEyeClipIds':ids,'scaledJumpTranslation':scaled,'controls':'passed','svgAndPngDownloads':'passed','pngDimensions':image.size,'pngAlphaRange':alpha.getextrema()}
(OUT/'player-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=True));assert not errors
