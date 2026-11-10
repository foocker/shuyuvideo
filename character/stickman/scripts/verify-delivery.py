"""Inspect decoded delivery frames and packaged transparent videos."""
from pathlib import Path
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
import json,io,subprocess,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'output/character-stickman';reports=OUT/'reports';movie=OUT/'renders/stickman-actions.mp4'
def frame(file,t,alpha=False):
 cmd=['ffmpeg','-v','error']+(['-c:v','libvpx-vp9'] if alpha else [])+['-ss',str(t),'-i',str(file),'-frames:v','1','-f','image2pipe','-vcodec','png','pipe:1']
 return Image.open(io.BytesIO(subprocess.check_output(cmd))).convert('RGBA' if alpha else 'RGB')
times=[1,4.8,8,14.5,19.8,23.8,27.8,33.3,35.8,37.27,41.36,45.36]
sheet=Image.new('RGB',(1440,1200),'#11171c');d=ImageDraw.Draw(sheet)
for i,t in enumerate(times):
 im=frame(movie,t);im.save(reports/f'delivered-{t:.1f}.png');im.thumbnail((480,270));x=i%3*480;y=i//3*300;sheet.paste(im,(x,y));d.text((x+12,y+278),f'{t:.2f}s',fill='white')
sheet.save(reports/'delivered-sheet.jpg',quality=94)
runSheet=Image.new('RGB',(1280,720),'#11171c');draw=ImageDraw.Draw(runSheet)
for i in range(8):
 t=7.25+i*.6/8;im=frame(movie,t).crop((340,260,1050,970));im.thumbnail((320,320));x=i%4*320;y=i//4*360;runSheet.paste(im,(x,y));draw.text((x+12,y+334),f'run {t-7.25:.3f}s',fill='white')
runSheet.save(reports/'delivered-run.jpg',quality=94)
for name,start in [('jump',36.25),('frontflip',40.25),('backflip',44.25)]:
 strip=Image.new('RGB',(1280,720),'#11171c');sd=ImageDraw.Draw(strip)
 for i,local in enumerate([0,.4,.58,.85,1.1,1.48,1.78,2.4]):
  im=frame(movie,start+local).crop((330,50,1080,900));im.thumbnail((320,320));x=i%4*320;y=i//4*360;strip.paste(im,(x,y));sd.text((x+12,y+334),f'{name} {local:.2f}s',fill='white')
 strip.save(reports/f'delivered-{name}.jpg',quality=94)
manifest=json.loads((OUT/'assets/manifest.json').read_text(encoding='utf8'));alphaChecks=[]
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);page=b.new_page(viewport={'width':640,'height':640});page.goto((ROOT/'export.html').as_uri())
 for a in manifest['assets']:
  file=OUT/'assets'/a['file'];assert hashlib.sha256(file.read_bytes()).hexdigest()==a['sha256']
  for t in [0,a['duration']*.5,max(0,a['duration']-1/a['fps'])]:
   im=frame(file,t,True);assert im.getchannel('A').getextrema()==(0,255)
   page.evaluate('([a,t])=>drawStickman(a,t,{loop:ShuyuStickman.actions[a].loop})',[a['action'],t]);head=page.evaluate('rig.joint("head")')
   assert im.getpixel(tuple(round(v) for v in head))[3]==0,(a['action'],t,'head hole')
   box=im.getchannel('A').getbbox();assert box[0]>0 and box[1]>0 and box[2]<640 and box[3]<640
   alphaChecks.append({'action':a['action'],'time':t,'headHoleAlpha':0,'bounds':box})
 page.set_viewport_size({'width':1440,'height':1080});page.goto((OUT/'assets/preview.html').as_uri());page.get_by_role('button',name='浅色底').click()
 page.evaluate('''async()=>{await Promise.all([...document.querySelectorAll("video")].map(v=>new Promise(resolve=>{v.controls=false;v.requestVideoFrameCallback(resolve);v.currentTime=.4;})));}''')
 page.screenshot(path=str(reports/'encoded-alpha-on-white.png'),full_page=True);b.close()
with zipfile.ZipFile(OUT/'stickman-motion-assets-v2.zip') as z:
 assert z.testzip() is None
 for a in manifest['assets']:assert hashlib.sha256(z.read(a['file'])).hexdigest()==a['sha256']
result={'passed':True,'movie':str(movie),'decodedShowcaseFrames':len(times)+32,'alphaFrames':alphaChecks,'zipIntegrity':'passed','zipFilesMatchManifest':True,'sourceRuntimeMatchesPackage':all((ROOT/'lib'/f).read_bytes()==(OUT/'assets/runtime'/f).read_bytes() for f in ['motions.js','stickman.js'])}
(reports/'delivery-check.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('Delivery passed:',len(times)+32,'MP4 frames;',len(alphaChecks),'decoded alpha frames; zip matched')
