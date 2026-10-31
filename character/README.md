# 数语 Ω 角色基础库

先打开 [study.html](study.html)：选择动作、表情、视线与左右手势，支持播放、半速、逐帧拖动、鼠标目光跟随、换色，以及当前姿态的透明 SVG / PNG 导出。Chrome / Edge 直接双击打开即可，不需要安装依赖或启动服务。

[36 秒动作总览](output/shuyu-omega-showcase.mp4) · [15 个动作姿态](output/action-sheet.png) · [11 种表情](output/expression-sheet.png) · [挥手透明动画](output/wave-alpha.webm)

## 角色结构

以数语网站 `../../ShuYu2/src/app/icon.svg` 使用的 Georgia 大写 **Ω** 为字形依据。原始品牌图标保存在 assets/brand-icon.svg，字体轮廓已固化为矢量控制点，不依赖浏览器临时寻找字体。参考图为 `../../shuyuvideostudy/pi.png`。

- **身体与脚**：Ω 拱形是身体，下方两个末端就是脚；每只脚可分别抬起与迈步，底部缺口保留。呼吸、歪头和鞠躬时脚底固定。
- **眼睛**：两只眼白、各自的瞳孔与高光、独立眼睑和眉毛。支持闭眼、单眼眨动、凝视和跟随目标；瞳孔裁切在眼白内。
- **手臂与手**：双臂连续连接字形两侧；掌、拇指和三根手指独立于身体。预设为放松、张开、握拳、食指指向、伸出拇指。
- **嘴型**：微笑、平口、下弯、张嘴与说话循环。可传入逐时刻张口幅度；当前说话动作没有绑定语音音素。
- **外观**：墨色、陶土、参考蓝、青绿四套配色。角色为二维正面设计，支持侧倾、压缩与拉伸；此版没有三维背身转身。

左右以**画面左右**为准。所有动态都由绝对时间计算，播放、随机拖动和逐帧渲染共用一套状态。

## 动作与表情

| 动作 ID | 动作 | 原始周期 |
| --- | --- | --- |
| idle | 待机呼吸与自然眨眼 | 4 秒 |
| blink | 连续眨眼 | 2.4 秒 |
| look | 左、右、上方观察 | 4.8 秒 |
| wave | 挥手招呼 | 3.6 秒 |
| pointRight / pointLeft | 目光先行，再指向一侧 | 各 3.4 秒 |
| explain | 交替展开双手、说话嘴型 | 4.8 秒 |
| think | 歪头、抬手思考 | 4.4 秒 |
| nod / shake | 点头认可、摇头否定 | 2.6 / 2.8 秒 |
| shrug | 摊手疑问 | 3.2 秒 |
| jump | 蓄势、起跳、落地缓冲 | 2.6 秒 |
| walk | 原地或移动行走 | 2 秒 |
| bow | 鞠躬致意 | 3.2 秒 |
| celebrate | 举手与小跳庆祝 | 4 秒 |

表情 ID：`neutral`、`happy`、`curious`、`thinking`、`surprised`、`doubtful`、`sad`、`focused`、`sleepy`、`wink`、`talk`。默认 `auto` 跟随动作，可以任意叠加。

## 接入其他片段

复制 lib/omega-shape.js 和 lib/omega.js 即可，角色运行时不依赖 GSAP、字体、网络或位图。下面是一个可直接使用的 HTML 例子：

```html
<div id="mascot" style="width:960px;height:540px"></div>
<script src="lib/omega-shape.js"></script>
<script src="lib/omega.js"></script>
<script>
  const omega = ShuyuOmega.create(document.getElementById('mascot'), {
    id: 'lesson-guide',
    viewBox: '0 0 1920 1080',
    x: 440, y: 880, scale: 1.5
  });
  omega.render('pointRight', 1.4, {
    expression: 'curious',
    palette: 'clay',
    look: [0.8, -0.1],
    leftHand: 'relaxed',
    rightHand: 'point',
    shadow: false
  });
</script>
```

HyperFrames 中用暂停 GSAP 时间轴的 `onUpdate` 调用 `omega.render(action, time, options)`，示例在 compositions/showcase.html。Remotion 中传入 `frame / fps`。不要在角色库里另启播放时钟。

`look: [x,y]` 的每个值限制在 −1 到 1，向右、向下为正。省略它时目光跟随动作。`mouth: 0…1` 可覆盖说话周期。

更细的控制使用 `sample()` 与 `draw()`：

```js
const pose = ShuyuOmega.sample('idle', 1.2);
pose.eyeL = 0;           // 单独闭合画面左眼
pose.eyeR = 1;
pose.footLY = -30;       // 抬起左脚，保持字形连续
omega.draw(pose, { palette: 'ink' });

// 两个姿态可平滑混合，不需要直接跳切。
const a = ShuyuOmega.sample('wave', 2.8);
const b = ShuyuOmega.sample('think', 1.6);
omega.draw(ShuyuOmega.blend(a, b, 0.35));

// 移动行走：每秒向右 28 个模型单位，支撑阶段脚底保持不动。
omega.render('walk', 3.2, { travel: true });
```

`create()` 返回 `svg`、`render()`、`draw()`、`toSVG()`、`destroy()` 和当前 `pose`。单页可创建多个独立角色，眼睛裁切 ID 不会串用。自定义原始姿态时仍需自行检查夸张幅度；已验证的范围是内置动作与控件预设。

## 素材导出与重建

- 预览页可直接导出当前姿态的透明 SVG、1400×1080 PNG。
- `output/wave-alpha.webm` 是 3.6 秒、30 fps 的透明 VP9 示例，可叠加到视频上。普通播放器可能以黑色显示透明背景；合成时使用 alpha 通道。
- `output/shuyu-omega-showcase.mp4` 是 1920×1080、30 fps、36 秒的静音展示。动作素材保持静音，供后续影片统一配声音。

```powershell
# 仅重建字体轮廓、检查或导出时需要；普通预览不需要安装。
python -m pip install -r scripts/requirements.txt
npm run build
npm run verify
npm run check
npm run render
npm run verify:render
npm run export:wave

# 导出另一个透明动作
python scripts/export-action.py --action think --palette clay --output output/think-alpha.webm
```

使用 Chrome、FFmpeg/ffprobe 和 Python。生成透明 WebM 时直接编码透明 PNG 帧，未使用黑底抠像。重新提取字形需要 Windows 本机 Georgia；当前固化矢量已经可直接使用。

## 文件与验证

`lib/omega.js` 集中维护身体、表情、手势和动作；`lib/omega-shape.js` 只保存字形轮廓。`study.html` 是人用动作面板，`index.html` 是 HyperFrames 入口，`export.html` 是无背景导出入口。结果与检查都在被 Git 忽略的 output/ 中。

[REVIEW.md](REVIEW.md) 记录动作边界、脚底稳定性、透明通道、随机跳转与成片检查。后台时间轴预览为 http://localhost:9416/#project/character；其中的 Edit with Framey 可连接 [HyperFrames 桌面应用](https://hyperframes.studio/studio/download?os=windows&src=cli)。
