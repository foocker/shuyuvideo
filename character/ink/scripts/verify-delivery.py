"""Inspect decoded delivery frames and packaged transparent videos."""
from pathlib import Path
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
import json,io,subprocess,hashlib,zipfile,argparse
parser=argparse.ArgumentParser();parser.add_argument('--zip',default='ink-motion-assets-v3.zip');args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'output/character-ink';reports=OUT/'reports';movie=OUT/'renders/ink-actions.mp4'
def frame(file,t,alpha=False):
 cmd=['ffmpeg','-v','error']+(['-c:v','libvpx-vp9'] if alpha else [])+['-ss',str(t),'-i',str(file),'-frames:v','1','-f','image2pipe','-vcodec','png','pipe:1']
 return Image.open(io.BytesIO(subprocess.check_output(cmd))).convert('RGBA' if alpha else 'RGB')
data=json.loads((ROOT/'motions.json').read_text(encoding='utf8'));catalog=json.loads((reports/'catalog.json').read_text(encoding='utf8'))
times=[s['start']+s['lead']+data['actions'][s['a']]['beats'][1] for s in catalog['shots']]
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
assert abs(float(probe['format']['duration'])-catalog['duration'])<.04
assert probe['streams'][0]['width']==1920 and probe['streams'][0]['height']==1080 and probe['streams'][0]['r_frame_rate']=='30/1'
assert all(s['codec_type']!='audio' for s in probe['streams'])
subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-f','null','-'],check=True,capture_output=True)
sheet=Image.new('RGB',(1440,300*((len(times)+2)//3)),'#f4f0e7');d=ImageDraw.Draw(sheet)
for i,t in enumerate(times):
 im=frame(movie,t);im.save(reports/f'delivered-{t:.1f}.png');im.thumbnail((480,270));x=i%3*480;y=i//3*300;sheet.paste(im,(x,y));d.text((x+12,y+278),f'{t:.2f}s',fill='#263640')
sheet.save(reports/'delivered-sheet.jpg',quality=94)
runSheet=Image.new('RGB',(1280,720),'#f4f0e7');draw=ImageDraw.Draw(runSheet)
for i in range(8):
 t=7.25+i*.6/8;im=frame(movie,t).crop((220,130,1060,900));im.thumbnail((320,320));x=i%4*320;y=i//4*360;runSheet.paste(im,(x,y));draw.text((x+12,y+334),f'run {t-7.25:.3f}s',fill='#263640')
runSheet.save(reports/'delivered-run.jpg',quality=94)
for name,start in [('jump',36.25),('frontflip',40.25),('backflip',44.25)]:
 strip=Image.new('RGB',(1280,720),'#f4f0e7');sd=ImageDraw.Draw(strip)
 for i,local in enumerate([0,.4,.58,.85,1.1,1.48,1.78,2.4]):
  im=frame(movie,start+local).crop((220,130,1060,900));im.thumbnail((320,320));x=i%4*320;y=i//4*360;strip.paste(im,(x,y));sd.text((x+12,y+334),f'{name} {local:.2f}s',fill='#263640')
 strip.save(reports/f'delivered-{name}.jpg',quality=94)
storyFrames=0
for name,locals in {'paperFlip':[0,.75,1,1.4,1.7,1.85,2.1,2.8],'gunFire':[0,.15,.18,.2,.25,.36,.56,1.2],'fallBack':[0,.52,.83,1.18,1.48,1.62,1.9,2.5],'fallForward':[0,.57,.85,1.14,1.42,1.57,1.85,2.5],'climbUp':[0,.3,.85,1.05,1.75,2.05,2.55,3.05]}.items():
 shot=next(s for s in catalog['shots'] if s['a']==name);start=shot['start']+shot['lead'];strip=Image.new('RGB',(1280,720),'#f4f0e7');sd=ImageDraw.Draw(strip)
 for i,local in enumerate(locals):
  im=frame(movie,start+local).crop((130,100,1080,900));im.thumbnail((320,320));x=i%4*320;y=i//4*360;strip.paste(im,(x,y));sd.text((x+12,y+334),f'{name} {local:.3f}s',fill='#263640');storyFrames+=1
 strip.save(reports/f'delivered-{name}.jpg',quality=94)
manifest=json.loads((OUT/'assets/manifest.json').read_text(encoding='utf8'));alphaChecks=[]
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);page=b.new_page(viewport={'width':640,'height':640});page.goto((ROOT/'export.html').as_uri())
 for a in manifest['assets']:
  file=OUT/'assets'/a['file'];assert hashlib.sha256(file.read_bytes()).hexdigest()==a['sha256']
  for t in [0,a['duration']*.5,max(0,a['duration']-1/a['fps'])]:
   im=frame(file,t,True);assert im.getchannel('A').getextrema()==(0,255)
   page.evaluate('([a,t,props])=>drawInk(a,t,{loop:ShuyuInk.actions[a].loop,props})',[a['action'],t,a.get('variant')=='props']);head=page.evaluate('rig.joint("head")')
   assert im.getpixel(tuple(round(v) for v in head))[3]==255,(a['action'],t,'solid head')
   box=im.getchannel('A').getbbox();assert box[0]>0 and box[1]>0 and box[2]<640 and box[3]<640
   alphaChecks.append({'action':a['action'],'variant':a.get('variant','actor'),'time':t,'solidHeadAlpha':255,'bounds':box})
 page.set_viewport_size({'width':1440,'height':1080});page.goto((OUT/'assets/preview.html').as_uri());page.get_by_role('button',name='浅色底').click()
 page.evaluate('''async()=>{await Promise.all([...document.querySelectorAll("video")].map(v=>new Promise(resolve=>{v.controls=false;v.requestVideoFrameCallback(resolve);v.currentTime=.4;})));}''')
 page.screenshot(path=str(reports/'encoded-alpha-on-white.png'),full_page=True);b.close()
with zipfile.ZipFile(OUT/args.zip) as z:
 assert z.testzip() is None
 for a in manifest['assets']:assert hashlib.sha256(z.read(a['file'])).hexdigest()==a['sha256']
result={'passed':True,'movie':str(movie),'duration':catalog['duration'],'fullMovieDecode':'passed','decodedShowcaseFrames':len(times)+32+storyFrames,'alphaFrames':alphaChecks,'zipIntegrity':'passed','zipFilesMatchManifest':True,'sourceRuntimeMatchesPackage':all((ROOT/'lib'/f).read_bytes()==(OUT/'assets/lib'/f).read_bytes() for f in ['motions.js','ink.js','catalog.js','guides.js'])}
assert result['sourceRuntimeMatchesPackage'],'Packaged runtime is stale'
(reports/'delivery-check.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('Delivery passed:',len(times)+32+storyFrames,'MP4 frames;',len(alphaChecks),'decoded alpha frames; zip matched')
