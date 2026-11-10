"""Generate the action list and shot times from their authoritative data."""
from pathlib import Path
import json,subprocess
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'motions.json').read_text(encoding='utf8'))
catalog=json.loads(subprocess.check_output(['node','-p',"JSON.stringify(require('./lib/catalog.js'))"],cwd=ROOT))
rows=['| ID | 动作 | 秒 | 播放 |','| --- | --- | ---: | --- |']
for name,a in data['actions'].items():rows.append(f'| {name} | {a["label"]} | {a["duration"]} | {"循环" if a["loop"] else "单次"} |')
p=ROOT/'README.md';s=p.read_text(encoding='utf8').split('## 剧情动作与道具')[0].rstrip()+'\n';start=s.index('| ID |');end=s.index('## 接入')
s=s[:start]+'\n'.join(rows)+'\n\n'+s[end:]
s=s.replace('墨影 · 基础动作库','墨影 · 动作库 v2').replace('48 秒动作展示','120 秒动作展示').replace('ink-motion-assets-v1.zip','ink-motion-assets-v2.zip')
s=s.replace('墨影与火柴人同时钟对照，支持','30 个动作按类别浏览；基础 11 项保留火柴人对照，新增 19 项展示关键姿态。支持')
s=s.replace('`x/y/scale`。','`x/y/scale`、`props`（默认 true）。')
s=s.replace('需要路径或道具绑定时使用 runtime。','14 个道具动作同时提供纯角色版和 `-props` 版，共 44 个透明视频；需要路径或自定义道具绑定时使用 runtime。')
s=s.replace('手部锚点指手掌外侧接触面，绘制掌心沿前臂稍退','空手锚点指手掌外侧接触面；握住内置道具时锚点改为握持中心')
if 'node character/ink/scripts/verify-story.cjs' not in s:s=s.replace('node character/ink/scripts/verify-rig.cjs','node character/ink/scripts/verify-rig.cjs\nnode character/ink/scripts/verify-story.cjs\n.venv/Scripts/python.exe -X utf8 character/ink/scripts/build-catalog.py')
s+='''
## 剧情动作与道具

`paperTake → paperRead → paperFlip`、`gunRaise → gunAim → gunFire → gunLower` 具有共同端态，可以用各自局部时钟顺序接上。阅读和瞄准可以延长循环。`fallBack`、`fallForward` 末态有不同身体朝向，接起身需要编排过渡，不能直接硬切 `recover`。

`actor.render('gunFire',t,{props:true})` 自动画出握持道具与 0.18s 的单次枪口闪光，1.3s 完成回弹；`props:false` 隐藏道具，姿态不变。动作默认单次，重复开枪应显式开始新的局部时钟。镜像时枪口和回弹一起镜像。

`ShuyuInk.propPoint(pose,offset)` 将道具局部点转换成角色局部点。再加 `pose.root`，按角色的 `scale`、`mirror` 和 `x/y` 转为场景坐标。每个 `propRig.grips` 存握持偏移，`events` 存触发时刻及道具局部 anchor。手与纸页转角使用 IK；翻页手跟随页角，翻后纸页保持可见。

`storyUse` 是对应镜头建议，`beats` 是拆解时间，`viewScale` 是目录/导出的取景比例，均不改变动作时间。梯子和悬杆只在预览中显示；透明素材中不带环境，影片应按固定锚点摆放支撑物。纸页递出、星离手后的路径是演示路径，接收者及真实星轨需在镜头中接管。

新增动作生成源是 `scripts/add-story-actions.py`，显式运行会覆盖这 19 个动作；编辑 motions.json 后只运行 build-data.py。不要运行首次迁移脚本 retarget.py，否则会重建为基础动作集。v1 完整版本保存于 output/character-ink/renders/versions/v01-ink-motion/。
'''
p.write_text(s,encoding='utf8')
rows=['# 墨影 v3 动作目录分镜','',f'{catalog["duration"]} 秒，1920×1080，30fps，静音。通常前 0.25 秒停在初态，开枪为 0.08 秒；单次动作在末态停稳，循环动作按自身周期。基础动作右侧是火柴人；新增动作右侧是三个墨影关键姿态。','','| 时间 | 动作 | 可见动作 / 影片用途 |','| --- | --- | --- |']
for shot in catalog['shots']:
 a=data['actions'][shot['a']];rows.append(f'| {shot["start"]:g}–{shot["end"]:g}s | {a["label"]} | {a.get("description","")} {a.get("storyUse","")} |')
(ROOT/'STORYBOARD.md').write_text('\n'.join(rows)+'\n',encoding='utf8')
