from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
dest=ROOT/'assets/cover/character.png';dest.parent.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(channel='chrome',headless=True)
    page=b.new_page(viewport={'width':1920,'height':1080})
    page.goto((ROOT/'export.html').as_uri())
    page.evaluate('rig.svg.setAttribute("viewBox","0 0 1920 1080");rig.render("paperRead",.6,{x:1370,y:870,scale:5.7})')
    page.screenshot(path=str(dest),omit_background=True);b.close()
print(dest)
