"""Review the catalogue's action cuts from the actual encoded MP4."""
from pathlib import Path
import io,json,subprocess
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'output/character-ink';reports=OUT/'reports'
cuts=[3,7,11,17.4,22.2,26,30.5,36,40,44]
sheet=Image.new('RGB',(1800,230*len(cuts)),'#f4f0e7');d=ImageDraw.Draw(sheet)
for row,cut in enumerate(cuts):
 for col,offset in enumerate([-.2,-.1,0,.1,.2]):
  t=cut+offset
  raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(OUT/'renders/ink-actions.mp4'),'-frames:v','1','-f','image2pipe','-vcodec','png','pipe:1'])
  im=Image.open(io.BytesIO(raw));im.thumbnail((360,203));sheet.paste(im,(col*360,row*230));d.text((col*360+8,row*230+207),f'{t:.2f}s',fill='#263640')
sheet.save(reports/'review-seams.jpg',quality=92)
im=Image.open(OUT/'renders/ink-actions-cover.jpg');im.thumbnail((360,203));im.save(reports/'cover-phone.jpg',quality=95)
(reports/'seam-check.json').write_text(json.dumps({'cuts':cuts,'samplesPerCut':5,'frames':50,'intent':'separate action catalogue items; hard cuts with initial pose hold'},indent=2),encoding='utf8')
print('Decoded 50 cut frames and cover phone thumbnail')
