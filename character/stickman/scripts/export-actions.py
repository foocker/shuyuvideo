"""Export reusable character-only transparent VP9 clips and pose SVG/PNG files."""
from pathlib import Path
import argparse,json,subprocess,hashlib,io
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'output/character-stickman/assets'
parser=argparse.ArgumentParser();parser.add_argument('--action');parser.add_argument('--fps',type=int,default=30);args=parser.parse_args()
if args.fps<1:raise ValueError('fps must be positive')
OUT.mkdir(parents=True,exist_ok=True);records=[]
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);page=b.new_page(viewport={'width':640,'height':640});page.goto((ROOT/'export.html').as_uri())
 actions=page.evaluate('ShuyuStickman.actions')
 if args.action and args.action not in actions:raise ValueError('Unknown action '+args.action)
 for name,a in actions.items():
  if args.action and name!=args.action:continue
  duration=a['duration']*(2 if a.get('gait') else 1);frames=round(duration*args.fps);dest=OUT/f'{name}-alpha.webm'
  cmd=['ffmpeg','-v','error','-y','-f','image2pipe','-vcodec','png','-r',str(args.fps),'-i','pipe:0','-an','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v','0','-crf','24','-row-mt','1','-deadline','good','-cpu-used','4','-metadata:s:v:0','alpha_mode=1',str(dest)]
  with dest.with_suffix('.log').open('wb') as log:
   process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
   try:
    for i in range(frames):
     page.evaluate('([a,t])=>drawStickman(a,t,{loop:ShuyuStickman.actions[a].loop})',[name,i/args.fps]);process.stdin.write(page.screenshot(omit_background=True))
   finally:process.stdin.close()
   assert process.wait()==0,dest
  page.evaluate('([a,t])=>drawStickman(a,t)',[name,min(a['duration']*.6,a['duration']-.001)])
  (OUT/f'{name}.svg').write_text(page.evaluate('rig.toSVG()'),encoding='utf8');page.screenshot(path=str(OUT/f'{name}.png'),omit_background=True)
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(dest)]))
  assert {k.lower():v for k,v in probe['streams'][0].get('tags',{}).items()}.get('alpha_mode')=='1'
  subprocess.run(['ffmpeg','-v','error','-c:v','libvpx-vp9','-i',str(dest),'-f','null','-'],check=True,capture_output=True)
  raw=subprocess.check_output(['ffmpeg','-v','error','-c:v','libvpx-vp9','-ss',str(duration*.5),'-i',str(dest),'-frames:v','1','-f','image2pipe','-vcodec','png','pipe:1']);im=Image.open(io.BytesIO(raw)).convert('RGBA')
  assert im.getchannel('A').getextrema()==(0,255) and im.getpixel((0,0))[3]==0
  records.append(dict(action=name,file=dest.name,duration=duration,cycle=a['duration'],fps=args.fps,frames=frames,size=[640,640],alphaRange=[0,255],fullDecode='passed',sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
  print(name,frames,'frames exported',flush=True)
 b.close()
manifest=OUT/'manifest.json';previous=json.loads(manifest.read_text(encoding='utf8'))['assets'] if args.action and manifest.exists() else []
records=[r for r in previous if r['action'] not in {x['action'] for x in records}]+records
manifest.write_text(json.dumps(dict(schema='shuyu-stickman-exports/v1',background='transparent',audio='none',prop='none',assets=records),indent=2),encoding='utf8')
