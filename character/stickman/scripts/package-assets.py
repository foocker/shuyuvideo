"""Create a portable, offline asset browser and zip from verified exports."""
from pathlib import Path
import json,shutil,zipfile,html
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'output/character-stickman';assets=OUT/'assets'
data=json.loads((ROOT/'motions.json').read_text(encoding='utf8'));manifest=json.loads((assets/'manifest.json').read_text(encoding='utf8'))
assert len(manifest['assets'])==len(data['actions'])
(assets/'runtime').mkdir(exist_ok=True)
for file in ('motions.js','stickman.js'):shutil.copy2(ROOT/'lib'/file,assets/'runtime'/file)
for file in ('motions.json','SOURCES.md'):shutil.copy2(ROOT/file,assets/file)
cards=[]
for name,a in data['actions'].items():
 cards.append(f'<article><video controls muted loop playsinline preload="metadata" poster="{name}.png" src="{name}-alpha.webm"></video><h2>{html.escape(a["label"])}</h2><p><a href="{name}-alpha.webm" download>WebM</a> · <a href="{name}.svg" download>SVG</a> · <a href="{name}.png" download>PNG</a></p></article>')
page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>火柴人透明动作</title><style>*{box-sizing:border-box}body{margin:0;background:#151b20;color:#efece4;font:16px/1.6 system-ui,sans-serif}main{max-width:1400px;margin:auto;padding:30px}h1{margin:0;font-size:30px}header p{color:#b4bbbf}nav{display:flex;gap:12px;margin:20px 0}button{background:#29323a;color:white;border:1px solid #68737b;border-radius:5px;padding:8px 18px;cursor:pointer}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:18px}article{background:#20282f;border:1px solid #3a444a;border-radius:10px;overflow:hidden}video{display:block;width:100%;aspect-ratio:1;background:var(--stage,#0c1014)}h2{font-size:18px;padding:0 18px;margin:12px 0 0}article p{padding:0 18px;margin:5px 0 18px}a{color:#ffbd73}footer{margin-top:30px;color:#b4bbbf}code{color:#ffbd73}</style></head><body><main><header><h1>火柴人 · 透明动作</h1><p>11 个基础动作。点击播放；切换底色检查透明叠加。</p></header><nav><button data-bg="#0c1014">深色底</button><button data-bg="#f5f0e8">浅色底</button><button data-bg="#315560">青色底</button></nav><div class="grid">'''+''.join(cards)+'''</div><footer>脚本接入、关键帧编辑与来源说明见 README.md。一次动作在素材浏览器中循环播放；实际使用时可播放一次并保持末态。</footer></main><script>document.querySelectorAll('button').forEach(b=>b.onclick=()=>document.documentElement.style.setProperty('--stage',b.dataset.bg));</script></body></html>'''
(assets/'preview.html').write_text(page,encoding='utf8')
(assets/'README.md').write_text('''# 火柴人透明动作包

打开 preview.html，点击各动作播放，切换背景检查透明叠加。11 个 WebM 动作均为 640×640、30fps、无道具、无音轨。走跑各有两个周期，其余是一个完整动作；文件规格见 manifest.json。另附代表姿态 SVG/PNG。

脚本接入：依次加载 runtime/motions.js、runtime/stickman.js；使用 ShuyuStickman.create(container, {viewBox:'0 0 640 640',x:320,y:520,scale:1.3})，再调用 actor.render('pick',seconds)。支持 color、mirror、rate、loop、travel。actor.joint('handFront') 返回手部世界坐标，用来绑定道具。全部动作与接口由本地代码执行，不需要网络或第三方运行时。

motions.json 是可编辑的关节关键帧，改后需在原项目中运行 scripts/build-data.py 更新 JavaScript。完整编辑器与原片对照入口位于工作区 tools/shuyuvideo/character/stickman/study.html。

这是手工动作研究版本，参考与补画范围、开源工具调研见 SOURCES.md；不是原作者发布的骨骼工程或开放授权角色包。
''',encoding='utf8')
dest=OUT/'stickman-motion-assets-v2.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(assets.rglob('*')):
  if f.is_file() and f.suffix!='.log':z.write(f,f.relative_to(assets))
print(dest, dest.stat().st_size,'bytes')
