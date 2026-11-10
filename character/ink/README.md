# 墨影 · 动作库 v3

《置换之梦》的角色现在有独立动作库。保留实心头、笔锋、白眼、墨滴躯干和短脚掌；以已经认可的火柴人动作迁移节奏，重新处理墨影比例、宽肢体、眼神和接触位置。

直接打开 [study.html](study.html)：30 个动作按类别浏览；基础 11 项保留火柴人对照，新增 19 项展示关键姿态。支持慢放、逐姿态拖动、镜像、关节、行进、换底色和透明 SVG / PNG 导出。

[117.5 秒动作展示](../../output/character-ink/renders/ink-actions.mp4) · [透明素材浏览](../../output/character-ink/assets/preview.html) · [素材包](../../output/character-ink/ink-motion-assets-v3.zip)

v3 修正抓握与攀爬的 O 型腿：单手悬挂、松手落地、攀爬一级使用与已认可走路相同的腿长（大腿/小腿各 25.667 单位），膝盖朝同一方向弯。攀爬改为一脚踩稳、换高抓点、蹬起、后脚跟上；以 14–18 单位的脚距代替宽站姿。查看 [攀爬新旧对比](../../output/character-ink/reports/contact-compare-climbUp.jpg)。

同版修复全部道具的偶发闪帧：`propKind` 是离散类型，不走曲线插值。开枪改为 0.18s 击发，目录中的瞄准段缩至 1.5s，开枪项额外初态停留仅 0.08s。

| ID | 动作 | 秒 | 播放 |
| --- | --- | ---: | --- |
| observe | 站立 · 低头观察 | 2.4 | 单次 |
| walk | 行走循环 | 1.2 | 循环 |
| run | 奔跑循环 | 0.6 | 循环 |
| pick | 蹲下 · 拾取 · 端详 | 5.6 | 单次 |
| press | 蹲姿按压 | 4 | 单次 |
| drag | 低姿拖拽 | 3 | 单次 |
| hang | 双手悬挂 | 2.5 | 循环 |
| recover | 躺下 · 坐起 · 站立 | 3 | 单次 |
| jump | 跳跃 · 落地缓冲 | 2.4 | 单次 |
| frontflip | 前空翻 | 2.6 | 单次 |
| backflip | 后空翻 | 2.6 | 单次 |
| paperTake | 接过论文 | 2.8 | 单次 |
| paperRead | 持纸阅读 | 3 | 循环 |
| paperFlip | 翻阅一页 | 3 | 单次 |
| paperOffer | 递出论文 | 3.1 | 单次 |
| paperGuard | 迎风护稿 | 3.6 | 单次 |
| gunRaise | 举枪 | 1.9 | 单次 |
| gunAim | 持枪瞄准 | 2.4 | 循环 |
| gunFire | 开枪与回弹 | 1.3 | 单次 |
| gunLower | 收枪放低 | 2 | 单次 |
| fallBack | 失衡后倒 | 2.6 | 单次 |
| fallForward | 绊倒与撑地 | 2.6 | 单次 |
| catchStar | 接住落星 | 2.4 | 单次 |
| placeStar | 送回星轨 | 3.1 | 单次 |
| pullLever | 双手拉杆 | 3.3 | 单次 |
| turnWheel | 双手转轮 | 3 | 循环 |
| push | 抵住并推开 | 3.5 | 单次 |
| hangOne | 单手悬挂 | 2.6 | 循环 |
| release | 松手落地 | 2.4 | 单次 |
| climbUp | 抓握攀上一级 | 3.1 | 单次 |

## 接入

```html
<div id="actor" style="width:640px;height:640px"></div>
<script src="lib/motions.js"></script>
<script src="lib/ink.js"></script>
<script>
const actor = ShuyuInk.create(document.getElementById('actor'), {
  viewBox:'0 0 640 640', x:320, y:540, scale:3.1
});
actor.render('jump', 1.0, {loop:false});
// In your paused timeline update: actor.render(action, absoluteSeconds).
const contact = actor.joint('handFront');
</script>
```

`render(name,t,options)` / `sample(name,t,options)` 接受 `rate`（正数）、`loop`、`travel`。绘制接受 `mirror`、`color`、`backColor`、`rim`、`rimColor`、`skeleton`、`x/y/scale`、`props`（默认 true）。暗背景建议 `rim:1.05`。`travel:true` 令走跑连续前进；腾空动作按数据里的水平位移移动，落地停住。镜像时位移方向一起反转。

`sample` 是无 DOM 的绝对时间纯函数，可在 Node 中调用。`draw(pose,options)` 绘制自定义姿态；`blend(a,b,u)` 混合姿态；`worldJoint(pose,joint,options)` 或实例 `joint(name)` 返回世界锚点；`toSVG()` 导出矢量；`destroy()` 清理实例。混合姿态不自动锁定脚，影片中需要给动作衔接安排共同支撑点。

所有坐标单位以脚底 y=0、y 向下。空手锚点指手掌外侧接触面；握住内置道具时锚点改为握持中心；脚部锚点指脚底。躯干、头、手脚的真实轮廓都在 SVG 内，不需要字体或图片。透明 WebM 为 640×640、30fps；走跑输出两个周期，其他动作一个完整周期，均为原地版本。14 个道具动作同时提供纯角色版和 `-props` 版，共 44 个透明视频；需要路径或自定义道具绑定时使用 runtime。

## 数据与重建

`motions.json` 是墨影自己的编辑源，`lib/motions.js` 为其离线编译版，`lib/ink.js` 为独立渲染器。`reference/` 仅用于对照，与运行时及透明素材无关。

在 `tools/shuyuvideo` 根目录运行：

```powershell
.venv/Scripts/python.exe -X utf8 character/ink/scripts/build-data.py
node character/ink/scripts/verify-rig.cjs
node character/ink/scripts/verify-story.cjs
.venv/Scripts/python.exe -X utf8 character/ink/scripts/build-catalog.py
.venv/Scripts/python.exe -X utf8 character/ink/scripts/verify-browser.py
.venv/Scripts/python.exe -X utf8 scripts/shuyu.py check character-ink
.venv/Scripts/python.exe -X utf8 scripts/shuyu.py preview character-ink --port 3029
.venv/Scripts/python.exe -X utf8 scripts/shuyu.py render character-ink
.venv/Scripts/python.exe -X utf8 character/ink/scripts/export-actions.py
.venv/Scripts/python.exe -X utf8 character/ink/scripts/package-assets.py
```

`scripts/retarget.py` 是首次导入用的可复现迁移脚本，重新运行会重建 motions.json；手工编辑后不要把它当编译脚本。`scripts/prepare-reference.py` 冻结当前火柴人参考。源码与已有影片均独立，暂未把这组动作替换进 12 分钟成片。

来源与改编范围见 [SOURCES.md](SOURCES.md)，检验和目视审查见 [REVIEW.md](REVIEW.md)。

## 剧情动作与道具

`paperTake → paperRead → paperFlip`、`gunRaise → gunAim → gunFire → gunLower` 具有共同端态，可以用各自局部时钟顺序接上。阅读和瞄准可以延长循环。`fallBack`、`fallForward` 末态有不同身体朝向，接起身需要编排过渡，不能直接硬切 `recover`。

`actor.render('gunFire',t,{props:true})` 自动画出握持道具与 0.18s 的单次枪口闪光，1.3s 完成回弹；`props:false` 隐藏道具，姿态不变。动作默认单次，重复开枪应显式开始新的局部时钟。镜像时枪口和回弹一起镜像。

`ShuyuInk.propPoint(pose,offset)` 将道具局部点转换成角色局部点。再加 `pose.root`，按角色的 `scale`、`mirror` 和 `x/y` 转为场景坐标。每个 `propRig.grips` 存握持偏移，`events` 存触发时刻及道具局部 anchor。手与纸页转角使用 IK；翻页手跟随页角，翻后纸页保持可见。

`storyUse` 是对应镜头建议，`beats` 是拆解时间，`viewScale` 是目录/导出的取景比例，均不改变动作时间。梯子和悬杆只在预览中显示；透明素材中不带环境，影片应按固定锚点摆放支撑物。纸页递出、星离手后的路径是演示路径，接收者及真实星轨需在镜头中接管。

新增动作生成源是 `scripts/add-story-actions.py`，显式运行会覆盖这 19 个动作；编辑 motions.json 后只运行 build-data.py。不要运行首次迁移脚本 retarget.py，否则会重建为基础动作集。v1 完整版本保存于 output/character-ink/renders/versions/v01-ink-motion/。
