"""Compare the exact v2 contact poses with the corrected side-view actions."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
import io,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'output/character-ink';R=OUT/'reports'
OLD=OUT/'renders/versions/v02-story-actions/source'
selected={'hangOne':[0,.65,1.95],'release':[.72,1.16,1.95],'climbUp':[.85,1.75,2.7]}
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True)
 pages=[b.new_page(viewport={'width':640,'height':640}) for _ in range(2)]
 for page,src in zip(pages,[OLD,ROOT]):page.goto((src/'export.html').as_uri())
 for name,times in selected.items():
  im=Image.new('RGB',(1440,1040),'#f4f0e7');d=ImageDraw.Draw(im)
  for row,page in enumerate(pages):
   for i,t in enumerate(times):
    page.evaluate('([a,t])=>drawInk(a,t)',[name,t]);shot=Image.open(io.BytesIO(page.screenshot(omit_background=True))).convert('RGBA');shot.thumbnail((480,480));x=i*480;y=row*520;im.paste(shot,(x,y),shot);d.text((x+20,y+486),f'{"BEFORE v2" if row==0 else "AFTER v3"} / {name} / {t:.2f}s',fill='#263640')
  im.save(R/f'contact-compare-{name}.jpg',quality=95)
 page=pages[1];page.set_viewport_size({'width':1440,'height':1100});page.goto((ROOT/'study.html').as_uri());page.evaluate('inkStudy.select("climbUp");inkStudy.seek(1.75)');page.screenshot(path=str(R/'contact-study.png'),full_page=True)
 b.close()
print('Saved 3 before/after sheets and corrected study preview')
