# 火柴人 · 基础动作资产

参照 Alan Becker《Animation vs. Geometry》中的橙色空心头火柴人，新增一个独立角色。11 个动作、可编辑关键帧、绝对时间求值和透明导出。原有 Ω 保留。

**打开 [study.html](study.html)**：动作切换、原片对照、暂停、拖动、慢放、镜像、改色、关节显示、SVG/PNG 导出。源码预览页可直接双击；参考视频需保留仓库内原路径，或在缺失提示中选择本地 MP4。

[48 秒动作展示](../../output/character-stickman/renders/stickman-actions.mp4) · [新增跳跃与空翻](../../output/character-stickman/renders/stickman-aerial-actions.mp4) · [透明素材浏览](../../output/character-stickman/assets/preview.html) · [完整素材包 ZIP](../../output/character-stickman/stickman-motion-assets-v2.zip)

| ID | 动作 | 时长 | 形式 |
|---|---|---|---|
| observe | 站立、低头观察 | 2.4s | 一次，返回站姿 |
| walk | 行走 | 1.2s | 循环，支持行进 |
| run | 奔跑 | 0.6s | 循环，支持行进 |
| pick | 蹲下、拾取、端详、伸手 | 5.6s | 一次，保持伸手姿态 |
| press | 蹲姿按压 | 4s | 一次，收回 |
| drag | 低姿拖拽 | 3s | 一次 |
| hang | 双手悬挂 | 2.5s | 循环 |
| recover | 躺下、坐起、站立 | 3s | 一次，保持站姿 |
| jump | 蓄力、跳跃、落地缓冲 | 2.4s | 一次，可选向前行进 |
| frontflip | 收腿前空翻、落地站稳 | 2.6s | 一次，可选向前行进 |
| backflip | 抬胸后空翻、落地站稳 | 2.6s | 一次，可选向后行进 |

这是手工关键帧研究版。循环、接触归一化和补画范围见 [SOURCES.md](SOURCES.md)，不声称已取得原片开放动作工程。开源编辑器中 StykAnimate 最值得继续试用。

## 接入

只需 `lib/motions.js` 和 `lib/stickman.js`；不需要 GSAP、字体、网络、参考视频或位图。

```html
<div id="actor" style="width:960px;height:540px"></div>
<script src="lib/motions.js"></script>
<script src="lib/stickman.js"></script>
<script>
const actor = ShuyuStickman.create(document.getElementById('actor'), {
  viewBox: '0 0 960 540', x: 330, y: 440, scale: 1.4
});
actor.render('pick', 3.2, { color: '#ff8808', mirror: false });
const hand = actor.joint('handFront'); // 世界坐标，道具绑在这里
actor.render('walk', 2.1, { travel: true });
</script>
```

`sample(action, seconds, options)` 返回独立姿态；`draw(pose, options)` 画自定义姿态；`blend(a,b,amount)` 混合两个姿态；`toSVG()` 导出当前 SVG；`destroy()` 移除实例。`rate` 为正数速度倍率，默认 1；`loop` 默认沿用动作配置。一次动作结束后保持最终姿态。世界坐标查询包含镜像、缩放和根位移。

`travel:true` 让走跑按步幅行进，支撑脚在地面固定。场景如自行修改角色 x，应同时维护地面接触。任意姿态混合不会自动维持 IK 接触，应在接触相同的姿态之间切换或在镜头中明确换支点。

跳跃和空翻默认原地完成，`travel:true` 时在腾空阶段产生位移，落地后停住。`airborne` 保存离地、着地、抛物线高度、位移、转体中心和非匀速角度关键帧；姿态关键帧同时控制蓄力、收腿、打开和缓冲。前空翻提炼自原片空中转体并补齐地面起落；后空翻是扩展动作，详见来源说明。

## 编辑与导出

`motions.json` 是关键帧权威来源，每帧存完整关节、时间和缓动；`gait` 是走跑的周期、步幅、支撑相、抬脚高度和腿长。修改后运行：

```powershell
# 从 tools/shuyuvideo 执行
.\shuyu.ps1 exec character/stickman/scripts/build-data.py
node character/stickman/scripts/verify-rig.cjs
.\shuyu.ps1 exec character/stickman/scripts/export-actions.py
.\shuyu.ps1 check character-stickman
.\shuyu.ps1 render character-stickman
```

透明导出默认全部 11 个动作，各自 640×640、30fps、VP9 WebM，另存代表姿态 SVG/PNG。导出全是原地动作、透明背景、无道具和声音；走跑连续导出两个周期便于使用。可用 `--action pick` 只导出一个。输出集中到 `output/character-stickman/`：`assets/` 是可复用文件，`renders/stickman-actions.mp4` 是 48 秒展示，`reports/` 是验证与参考证据。透明 WebM 在不支持透明的视频播放器中可能显示黑底，合成时使用 alpha 通道。

HyperFrames 场景在 `compositions/showcase.html`。互动页的播放时钟只在 `player.js` 中，角色库没有定时器；导出和视频求值同用 `sample`。验证范围与已知局限见 [REVIEW.md](REVIEW.md)。
