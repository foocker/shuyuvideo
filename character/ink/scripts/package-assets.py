"""Package transparent clips plus an offline editor and standalone runtime."""
from pathlib import Path
import json,shutil,zipfile,html,argparse
parser=argparse.ArgumentParser();parser.add_argument('--zip',default='ink-motion-assets-v3.zip');args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'output/character-ink';assets=OUT/'assets'
data=json.loads((ROOT/'motions.json').read_text(encoding='utf8'));manifest=json.loads((assets/'manifest.json').read_text(encoding='utf8'))
assert len(manifest['assets'])==sum(2 if a.get('propRig') else 1 for a in data['actions'].values())
for folder in ['lib','reference']:
 shutil.copytree(ROOT/folder,assets/folder,dirs_exist_ok=True)
for name in ['motions.json','SOURCES.md','README.md','study.html','export.html']:
 shutil.copy2(ROOT/name,assets/name)
(assets/'scripts').mkdir(exist_ok=True);shutil.copy2(ROOT/'scripts/build-data.py',assets/'scripts/build-data.py')
cards=[]
for name,a in data['actions'].items():
 for variant in (['actor','props'] if a.get('propRig') else ['actor']):
  stem=name+('-props' if variant=='props' else '')
  tag='含道具' if variant=='props' else '纯角色'
  cards.append(f'<article><video controls muted {"loop" if a.get("loop") else ""} playsinline preload="metadata" poster="{stem}.png" src="{stem}-alpha.webm"></video><h2>{html.escape(a["label"])} · {tag}</h2><p><a href="{stem}-alpha.webm" download>WebM</a> · <a href="{stem}.svg" download>SVG</a> · <a href="{stem}.png" download>PNG</a></p></article>')
page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>墨影透明动作</title><style>*{box-sizing:border-box}body{margin:0;background:#ebe7df;color:#263640;font:16px/1.6 system-ui,sans-serif}main{max-width:1400px;margin:auto;padding:30px}h1{margin:0;font-size:30px}header p{color:#667279}nav{display:flex;gap:12px;margin:20px 0;flex-wrap:wrap}button{background:#f9f6ed;color:#263640;border:1px solid #aab1af;border-radius:5px;padding:8px 18px;cursor:pointer}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:18px}article{background:#f4f0e7;border:1px solid #cecac0;border-radius:10px;overflow:hidden}video{display:block;width:100%;aspect-ratio:1;background:var(--stage,#f4f0e7)}h2{font-size:18px;padding:0 18px;margin:12px 0 0}article p{padding:0 18px;margin:5px 0 18px}a{color:#98633a}footer{margin-top:30px;color:#667279}</style></head><body><main><header><h1>墨影 · 透明动作</h1><p>11 个独立动作。点击播放，切换背景查看透明叠加。<a href="study.html">打开动作对照与导出</a></p></header><nav><button data-bg="#f4f0e7">浅色底</button><button data-bg="#90aab0">青色底</button><button data-bg="#bba6b0">灰紫底</button></nav><div class="grid">'''+''.join(cards)+'''</div><footer>WebM 是无描边的透明角色，适合浅底。深底可在动作页启用深色背景，使用带描边的 SVG / PNG 或 runtime。视频素材不含道具、地面或音轨。</footer></main><script>document.querySelectorAll('button').forEach(b=>b.onclick=()=>document.documentElement.style.setProperty('--stage',b.dataset.bg));</script></body></html>'''
page=page.replace('11 个独立动作','30 个动作，44 个透明视频（含 14 个道具版本）').replace('打开动作对照与导出','打开动作预览与导出').replace('视频素材不含道具、地面或音轨。','含道具版保留纸页、枪、星或机关；纯角色版移除道具。均不含地面和音轨。')
(assets/'preview.html').write_text(page,encoding='utf8')
(assets/'README.md').write_text('''# 墨影透明动作包 v1

打开 preview.html 播放 11 个透明 WebM；打开 study.html 同步对照火柴人，慢放、镜像、行进、拖动、换底色和导出 SVG / PNG。全部离线。

每个 WebM 是 640×640、30fps、原地、静音。走跑两个周期，其余一个完整动作。对应 SVG / PNG 是代表姿态。manifest.json 记录时长、周期、帧数与 SHA-256。

接入只需 lib/motions.js 和 lib/ink.js，使用 ShuyuInk.create(container,{viewBox:'0 0 640 640',x:320,y:540,scale:3.1})；actor.render('jump',seconds,{loop:false})。支持 mirror、color、backColor、rim、skeleton、travel、rate。暗背景建议 rim:1.05。手脚世界接触锚点用 actor.joint('handFront')、actor.joint('footFront')。

坐标以脚底 y=0，手部关节表示掌外接触面。一次动作默认保持末态，walk/run/hang 默认循环。sample 是纯函数，直接传绝对时间；不要在绘制过程中累积姿态。改变 motions.json 后运行 scripts/build-data.py 更新数据。reference/ 仅供对照，透明角色运行时不依赖它。

角色与动作来源、改编范围见 SOURCES.md。源码项目位于工作区 character/ink/，当前还未替换进《置换之梦》完整影片。
''',encoding='utf8')
readme=(assets/'README.md').read_text(encoding='utf8').replace('动作包 v1','动作包 v3').replace('11 个透明 WebM','30 个动作、44 个透明 WebM').replace('同步对照火柴人','查看基础动作与火柴人对照，以及新增动作的关键姿态').replace('rim、skeleton、travel、rate','rim、skeleton、travel、rate、props').replace('walk/run/hang 默认循环','动作数据 loop:true 的动作默认循环')
readme+='\n论文、枪、星与机关动作有纯角色和 -props 两种文件；runtime 默认显示道具，传 props:false 隐藏。events 记录击发等时刻，propRig 记录握持点。更多接入说明见源码 character/ink/README.md。\n'
(assets/'README.md').write_text(readme,encoding='utf8')
dest=OUT/args.zip
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(assets.rglob('*')):
  if f.is_file() and f.suffix!='.log':z.write(f,f.relative_to(assets))
print(dest,dest.stat().st_size,'bytes')
