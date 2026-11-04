"""Render the same vector rig to transparent VP9 WebM; no black-screen keying."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from workspace import output_dir, font_path
from shuyu import prepare_project
import argparse,subprocess,json
from playwright.sync_api import sync_playwright
ROOT=prepare_project('character')
parser=argparse.ArgumentParser();parser.add_argument('--action',default='wave');parser.add_argument('--output',default='wave-alpha.webm');parser.add_argument('--palette',default='ink');parser.add_argument('--expression',default='auto');parser.add_argument('--fps',type=int,default=30);args=parser.parse_args()
dest=(output_dir('character')/args.output).resolve();dest.parent.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True);page=browser.new_page(viewport={'width':1400,'height':1080})
    page.goto((ROOT/'export.html').as_uri());duration=page.evaluate('a=>ShuyuOmega.actions[a]?.duration',args.action)
    if not duration:raise ValueError('Unknown action: '+args.action)
    frames=round(duration*args.fps)
    command=['ffmpeg','-v','error','-y','-f','image2pipe','-vcodec','png','-r',str(args.fps),'-i','pipe:0','-an','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v','0','-crf','28','-row-mt','1','-deadline','good','-cpu-used','4','-metadata:s:v:0','alpha_mode=1',str(dest)]
    with (dest.with_suffix('.render.log')).open('wb') as log:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
        for i in range(frames):
            page.evaluate('([a,t,o])=>drawOmega(a,t,o)',[args.action,i/args.fps,{'palette':args.palette,'expression':args.expression}])
            process.stdin.write(page.screenshot(omit_background=True))
        process.stdin.close();code=process.wait();assert code==0,'FFmpeg failed; inspect '+str(dest.with_suffix('.render.log'))
    browser.close()
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(dest)]));assert {k.lower():v for k,v in probe['streams'][0]['tags'].items()}.get('alpha_mode')=='1'
subprocess.run(['ffmpeg','-v','error','-c:v','libvpx-vp9','-i',str(dest),'-f','null','-'],check=True,capture_output=True)
check=dest.with_suffix('.alpha-check.png');subprocess.run(['ffmpeg','-v','error','-y','-c:v','libvpx-vp9','-ss','1','-i',str(dest),'-frames:v','1',str(check)],check=True,capture_output=True)
from PIL import Image
im=Image.open(check);assert im.mode=='RGBA' and im.getchannel('A').getextrema()==(0,255)
assert im.getpixel((0,0))[3]==0 and im.getpixel((700,650))[3]==0,'Background and Omega opening must stay transparent'
report={'file':str(dest),'action':args.action,'duration':duration,'fps':args.fps,'frames':frames,'dimensions':[1400,1080],'alphaRange':im.getchannel('A').getextrema(),'fullDecode':'passed'}
dest.with_suffix('.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
