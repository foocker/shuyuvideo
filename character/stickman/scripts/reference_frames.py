"""Local motion reference crops. These are evidence, not runtime artwork."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import io,json,subprocess,argparse
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];VIDEO=R.parents[1]/'downloads/Alan_Becker/Animation_vs._Geometry.mp4';OUT=R/'output/character-stickman/reports/reference';OUT.mkdir(parents=True,exist_ok=True)
windows={'walk':(37.4,40.0,10),'look-pick':(40.2,45.8,15),'run':(257.8,259.0,13),'drag':(93.5,96.5,10),'hang':(118.5,121,10),'recover':(21.0,24.0,10),'land':(128.8,132,10),'jump':(142.0,144.3,10),'press':(70.0,74.0,10),'jump-basic':(225.8,229.6,20),'flip-study':(320.8,324.8,20),'tumble-study':(147.2,150.6,18)}
parser=argparse.ArgumentParser();parser.add_argument('--only');args=parser.parse_args()
if args.only:windows={k:windows[k] for k in args.only.split(',')}
def extract(spec):
 name,(a,b,n)=spec;rows=[];records=[]
 for i,t in enumerate(np.linspace(a,b,n)):
  raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(VIDEO),'-frames:v','1','-f','image2pipe','-vcodec','png','pipe:1'])
  im=Image.open(io.BytesIO(raw)).convert('RGB');rgb=np.array(im).astype(float)
  mask=(rgb[:,:,0]>140)&(rgb[:,:,1]>35)&(rgb[:,:,1]<210)&(rgb[:,:,2]<120)&(rgb[:,:,0]>rgb[:,:,1]*1.35)&(rgb[:,:,1]>rgb[:,:,2]*1.5)
  # Orange character is the only orange object in these selected windows.
  yy,xx=np.where(mask)
  if not len(xx):continue
  box=[max(0,int(xx.min())-35),max(0,int(yy.min())-35),min(1920,int(xx.max())+36),min(1080,int(yy.max())+36)]
  crop=im.crop(box);scale=min(310/crop.width,280/crop.height);crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
  file=OUT/f'{name}-{i:02}.png';im.save(file)
  rows.append((float(t),crop));records.append({'time':float(t),'box':box,'frame':file.name})
 sheet=Image.new('RGB',(320*5,320*((len(rows)+4)//5)),'#15191e');d=ImageDraw.Draw(sheet)
 for i,(t,crop) in enumerate(rows):
  x=i%5*320;y=i//5*320;sheet.paste(crop,(x+(320-crop.width)//2,y+(280-crop.height)//2));d.text((x+10,y+293),f'{name} | {t:.3f}s',fill='white')
 sheet.save(OUT/f'{name}.jpg',quality=94)
 return name,records
result=json.loads((OUT/'manifest.json').read_text(encoding='utf8')) if (OUT/'manifest.json').exists() else {}
with ThreadPoolExecutor(max_workers=3) as ex:result.update(dict(ex.map(extract,windows.items())))
(OUT/'manifest.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(OUT)
