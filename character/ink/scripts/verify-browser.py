"""Render the actual SVG and exercise the portable comparison UI."""
from pathlib import Path
import json,io
from PIL import Image,ImageDraw,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'output/character-ink/reports';OUT.mkdir(parents=True,exist_ok=True)
errors=[];files=[];bounds=[]
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);page=b.new_page(viewport={'width':640,'height':640})
 page.on('pageerror',lambda e:errors.append(str(e)));page.goto((ROOT/'export.html').as_uri())
 actions=page.evaluate('ShuyuInk.actions')
 overview=Image.new('RGB',(1280,360*((len(actions)+3)//4)),'#f4f0e7');d=ImageDraw.Draw(overview)
 for index,(name,a) in enumerate(actions.items()):
  chosen={'pick':[0,.8,1.2,1.6,2.4,2.8,3.6,5.2],'gunFire':[0,.15,.18,.2,.25,.36,.56,1.2],'paperFlip':[0,.75,1,1.4,1.7,1.85,2.1,2.8]}
  times=[min(a['duration']-.001,t) for t in chosen.get(name,[a['duration']*i/7 for i in range(8)])]
  sheet=Image.new('RGB',(1280,720),'#f4f0e7');sd=ImageDraw.Draw(sheet)
  for i,t in enumerate(times):
   page.evaluate('([a,t])=>drawInk(a,t)',[name,t]);im=Image.open(io.BytesIO(page.screenshot(omit_background=True))).convert('RGBA')
   box=im.getchannel('A').getbbox();bounds.append([name,t,box]);assert box and box[0]>0 and box[1]>0 and box[2]<640 and box[3]<640,(name,t,box)
   head=page.evaluate('rig.joint("head")');assert im.getpixel(tuple(round(v) for v in head))[3]==255,(name,t,'head must be solid')
   im.thumbnail((320,320));x=i%4*320;y=i//4*360;sheet.paste(im,(x,y),im);sd.text((x+14,y+330),f'{name} / {t:.3f}s',fill='#263640')
   if i==4:
    x=index%4*320;y=index//4*360;overview.paste(im,(x,y),im);d.text((x+14,y+330),name,fill='#263640')
  file=OUT/f'poses-{name}.jpg';sheet.save(file,quality=94);files.append(str(file))
 overview.save(OUT/'actions-overview.jpg',quality=94)
 # Reuse v1 transparent clips only after the actual browser pixels match.
 old=b.new_page(viewport={'width':640,'height':640});old.goto((OUT.parent/'renders/versions/v01-ink-motion/source/export.html').as_uri())
 regressions=0;maxAlphaDiff=0;maxColorDiff=0;maxChangedPixels=0
 for name,a in actions.items():
  if a.get('category')!='basic':continue
  for t in [0,a['duration']*.5,a['duration']-.001]:
   page.evaluate('([a,t])=>drawInk(a,t,{props:false})',[name,t]);old.evaluate('([a,t])=>drawInk(a,t)',[name,t])
   before=Image.open(io.BytesIO(old.screenshot(omit_background=True))).convert('RGBA');after=Image.open(io.BytesIO(page.screenshot(omit_background=True))).convert('RGBA')
   diff=ImageChops.difference(before,after)
   extrema=diff.getextrema();alphaDiff=extrema[3][1];colorDiff=0
   for bg in ['white','black']:
    left=Image.alpha_composite(Image.new('RGBA',before.size,bg),before);right=Image.alpha_composite(Image.new('RGBA',after.size,bg),after)
    colorDiff=max(colorDiff,max(e[1] for e in ImageChops.difference(left,right).getextrema()[:3]))
   changed=sum(1 for px in diff.get_flattened_data() if any(px))
   maxAlphaDiff=max(maxAlphaDiff,alphaDiff);maxColorDiff=max(maxColorDiff,colorDiff);maxChangedPixels=max(maxChangedPixels,changed)
   assert alphaDiff<=2 and colorDiff<=3 and changed<250,(name,t,'v1 visible regression',extrema,colorDiff,changed)
   regressions+=1
 old.close()
 page.set_viewport_size({'width':1440,'height':1100});page.goto((ROOT/'study.html').as_uri());page.wait_for_function('window.inkStudy')
 for name in actions:
  page.get_by_role('button',name=actions[name]['label'],exact=True).click();page.evaluate('inkStudy.seek(ShuyuInk.actions[inkStudy.action].duration*.6)')
  assert page.evaluate('Number.isFinite(inkStudy.rig.pose.head[0])')
  if actions[name].get('airborne') or actions[name].get('gait'):
   for mirrored in [False,True]:
    page.locator('#mirror').set_checked(mirrored);page.locator('#travel').check()
    for step in range(17):
     page.evaluate('t=>inkStudy.seek(t)',actions[name]['duration']*step/16)
     valid=page.evaluate('''()=>{const r=inkStudy.rig;const pts=ShuyuInk.joints.map(j=>r.joint(j));const h=r.joint('head'),rad=22*r.options.scale;pts.push([h[0]-rad,h[1]-rad],[h[0]+rad,h[1]+rad]);return pts.every(([x,y])=>x>3&&x<637&&y>3&&y<437);}''')
     assert valid,(name,mirrored,step,'study preview cropped')
 page.locator('#mirror').uncheck();page.evaluate('inkStudy.select("paperFlip");inkStudy.seek(1.4)');page.screenshot(path=str(OUT/'study-desktop.png'),full_page=True)
 page.locator('#props').uncheck();assert page.locator('#actor [data-part="prop"]').get_attribute('opacity')=='0';page.locator('#props').check()
 page.locator('#category').select_option('paper');assert page.locator('[data-action]:visible').count()==5;page.locator('#category').select_option('all')
 page.locator('#background').select_option('dark');page.screenshot(path=str(OUT/'study-dark.png'),full_page=True);page.locator('#background').select_option('light')
 for name in ['mirror','skeleton','travel']:
  page.evaluate('inkStudy.select("walk")');page.locator('#'+name).check()
 with page.expect_download() as download:page.locator('#svg-export').click()
 assert download.value.suggested_filename.endswith('.svg')
 with page.expect_download() as download:page.locator('#png-export').click()
 assert download.value.suggested_filename.endswith('.png')
 page.locator('#play').click();page.wait_for_timeout(180);assert page.evaluate('inkStudy.time>0');page.locator('#play').click()
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(OUT/'study-mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 b.close()
assert not errors,errors
(OUT/'browser-check.json').write_text(json.dumps({'passed':True,'runtimeErrors':errors,'actions':len(actions),'poseFrames':len(actions)*8,'v1PixelRegression':{'frames':regressions,'maxAlphaDifference':maxAlphaDiff,'maxCompositedColorDifference':maxColorDiff,'maxChangedPixels':maxChangedPixels,'tolerance':'alpha<=2, composited white/black RGB<=3, changed<250 of 409600 pixels; geometry checked exactly'},'propsToggle':True,'categoryFilter':True,'alphaBounds':'inside canvas','solidHead':True,'svgAndPngDownload':True,'mobileHorizontalOverflow':False,'sheets':files,'bounds':bounds},indent=2),encoding='utf8')
print('Browser check passed:',len(actions)*8,'poses')
