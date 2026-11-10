"""Render actual browser poses and verify interactive controls before export."""
from pathlib import Path
import json,io
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'output/character-stickman/reports';OUT.mkdir(parents=True,exist_ok=True)
errors=[];files=[]
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);page=b.new_page(viewport={'width':640,'height':640})
 page.on('pageerror',lambda e:errors.append(str(e)));page.goto((ROOT/'export.html').as_uri())
 actions=page.evaluate('ShuyuStickman.actions')
 overview=Image.new('RGB',(1280,360*((len(actions)+3)//4)),'#11171c');d=ImageDraw.Draw(overview)
 for index,(name,a) in enumerate(actions.items()):
  times=[min(a['duration']-.001,t) for t in ([0,.8,1.2,1.6,2.4,2.8,3.6,5.2] if name=='pick' else [a['duration']*i/7 for i in range(8)])]
  sheet=Image.new('RGB',(1280,720),'#11171c');sd=ImageDraw.Draw(sheet)
  for i,t in enumerate(times):
   page.evaluate('([a,t])=>drawStickman(a,t)',[name,t]);im=Image.open(io.BytesIO(page.screenshot(omit_background=True))).convert('RGBA')
   box=im.getchannel('A').getbbox();assert box and box[0]>0 and box[1]>0 and box[2]<640 and box[3]<640,(name,t,box)
   head=page.evaluate('rig.joint("head")');assert im.getpixel(tuple(round(v) for v in head))[3]==0,(name,t,'head opening is not transparent')
   im.thumbnail((320,320));x=i%4*320;y=i//4*360;sheet.paste(im,(x,y),im);sd.text((x+14,y+330),f'{name} / {t:.3f}s',fill='#d2d9db')
   if i==4:
    x=index%4*320;y=index//4*360;overview.paste(im,(x,y),im);d.text((x+14,y+330),name,fill='#d2d9db')
  file=OUT/f'poses-{name}.jpg';sheet.save(file,quality=94);files.append(str(file))
 overview.save(OUT/'actions-overview.jpg',quality=94)
 page.set_viewport_size({'width':1440,'height':1100});page.goto((ROOT/'study.html').as_uri());page.wait_for_function('window.stickmanStudy && document.getElementById("video").readyState>0')
 for name in actions:
  page.get_by_role('button',name=actions[name]['label'],exact=True).click();page.evaluate('stickmanStudy.seek(ShuyuStickman.actions[stickmanStudy.action].duration*.6)')
  assert page.evaluate('Number.isFinite(stickmanStudy.rig.pose.head[0])')
  if actions[name].get('airborne'):
   for mirrored in [False,True]:
    page.locator('#mirror').set_checked(mirrored);page.locator('#travel').check()
    for step in range(17):
     page.evaluate('t=>stickmanStudy.seek(t)',actions[name]['duration']*step/16)
     bounds=page.evaluate('''()=>{const r=stickmanStudy.rig;const pts=ShuyuStickman.joints.map(j=>r.joint(j));const h=r.joint('head'),rad=42*r.options.scale;pts.push([h[0]-rad,h[1]-rad],[h[0]+rad,h[1]+rad]);return pts.every(([x,y])=>x>6&&x<634&&y>6&&y<434);}''')
     assert bounds,(name,mirrored,step,'study preview cropped')
 page.evaluate('stickmanStudy.select("pick");stickmanStudy.seek(3.2)');page.wait_for_function('!document.getElementById("video").seeking')
 page.screenshot(path=str(OUT/'study-desktop.png'),full_page=True)
 for label in ['mirror','skeleton','travel']:
  page.evaluate('stickmanStudy.select("walk")');page.locator('#'+label).check()
 with page.expect_download() as download:page.locator('#svg-export').click()
 assert download.value.suggested_filename.endswith('.svg')
 with page.expect_download() as download:page.locator('#png-export').click()
 assert download.value.suggested_filename.endswith('.png')
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(OUT/'study-mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 b.close()
assert not errors,errors
(OUT/'browser-check.json').write_text(json.dumps({'passed':True,'runtimeErrors':errors,'actions':len(actions),'poseFrames':len(actions)*8,'alphaBounds':'inside canvas','referenceLoaded':True,'svgAndPngDownload':True,'mobileHorizontalOverflow':False,'sheets':files},indent=2),encoding='utf8')
print('Browser check passed:',len(actions)*8,'poses')
