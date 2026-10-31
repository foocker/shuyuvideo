# 技术架构：一部数学科普视频怎样做出来

一部片分五层，自上而下依赖：

| 层 | 负责 | 工具 | 产物 |
| --- | --- | --- | --- |
| 1 口播稿 | 讲什么、按什么顺序讲；全片的时钟 | 人写，[规范](NARRATION.md) | `SCRIPT.md`、`narration.json` |
| 2 数学核对 | 定义、推导、结论不出错 | [math/](../math/README.md)（Astra） | 数学依据、审核记录 |
| 3 镜头素材 | 每个镜头的主体动画 | Manim、HyperFrames、Three.js（见下） | 单个短片段或网页场景 |
| 4 合成 | 排版、公式、Ω 角色、转场、镜头运动、字幕 | HyperFrames（HTML + GSAP + KaTeX） | `index.html` + `compositions/` |
| 5 声音 | 配音、音效、混音、响度 | [sound/](../sound/README.md) | `narration.wav`、`final-mix.wav` |

口播稿先定稿，配音生成后得到逐词时间；画面按这些时间排，而不是先做画面再配旁白。

## 选哪个引擎做镜头

各引擎擅长的事不同。按**镜头主体**选，不按习惯选。

| 镜头主体 | 用 | 原因 |
| --- | --- | --- |
| 公式一步步变形、项的移动与合并 | **Manim**（`MathTex` + `TransformMatchingTex`） | LaTeX 原生排版，公式各部分可单独追踪与变形 |
| 函数图像、坐标系、精确几何构造 | **Manim** | 坐标、切线、面积等由数学定义直接生成 |
| 2D 图形、计数、拼图、标注、文字 | **HyperFrames**（SVG + GSAP） | 编写最快，可在 Studio 中直接修改，中文排版好 |
| 曲面、拓扑形变、立体物体 | **Three.js**，放在 HyperFrames 场景里 | 已有作品的几何与材质可复用（[films/](../films/)） |
| 屏幕上的公式（非变形） | **KaTeX**，构建期渲染为 HTML | 与正文同一图层，字号和颜色跟风格参数一致 |
| Ω 角色 | **HyperFrames** 角色层（[character/](../character/README.md)） | 始终叠在最上层，任意镜头都可加入 |
| 几何烘焙、曲面数据、声音合成 | **Python**（numpy） | 离线计算，结果写成静态文件 |

规则：

- **合成只在 HyperFrames 里做。** Manim 片段导出为 1920×1080、30 fps 的 MP4，以 `<video>` 放进场景，再叠上 Ω、标注和转场。
- **Manim 片段必须用暖白主题**（[manim_theme.py](../style/adapters/manim_theme.py)）。底色与 HyperFrames 场景一致（`#F4F2EC`），否则切换处能看出接缝。
- **公式只用 TeX。** HyperFrames 里用 KaTeX，Manim 里用 `MathTex`。不用 Unicode 字符拼写公式（`x²`、`−`、`₁`）。
- 能用 HyperFrames 写的 2D 镜头不要绕道 Manim。Manim 每改一次都要重新渲染，HyperFrames 可以实时预览、逐帧拖动。
- 渲染环境离线。GSAP、KaTeX、字体都放在作品的 `assets/` 下，不引用 CDN。

## 数据流

```
SCRIPT.md ──► narration.json ──► sound/voice.py ──► 逐句音频 + 逐词时间 (voice-timings.json)
                                                        │
              镜头按词时间排进 index.html ◄──────────────┘
                     │
              sound-cues.json（音效挂在画面事件上）
                     │
              sound/mix.py ──► final-mix.wav（-16 LUFS，峰值 ≤ -1.5 dBTP）
                     │
              hyperframes check / snapshot / render ──► MP4
```

## 合成层里的公共模块

| 模块 | 作用 |
| --- | --- |
| [camera/](../camera/README.md) | 镜头运动：推近、拉远、平移、聚焦局部再回到全景。整个场景放在一个"世界"图层里，由相机变换移动 |
| [transitions/](../transitions/README.md) | 镜头之间的衔接：硬切、交叉淡化、对象延续、推入切换 |
| [character/](../character/README.md) | Ω 角色。每个镜头单独指定位置、动作和朝向，不固定在角落 |
| [style/](../style/README.md) | 颜色、字号、语义角色 |

## 每部片的文件

```
films/<作品>/
  SCRIPT.md          口播稿（人读）
  narration.json     口播逐句、配音设置（机器读）
  voice-timings.json 配音后生成：每句与每个词的实际时间
  sound-cues.json    音效：时间、种类、增益、对应的画面事件
  index.html         根合成：场景、配音轨、音效轨
  compositions/      每个场景一个文件
  assets/            vendor（GSAP、KaTeX）、fonts、audio、clips（Manim 片段）
  REVIEW.md          检查记录
```

## 交付前检查

1. `npx hyperframes check --json` 无错误。
2. 抽帧看文字层：没有乱码问号、裸露的 TeX 源码（`\frac`、`^` 出现在可见文字中）或制作备注（斜杠分隔的说明、镜头编号）。
3. `npx hyperframes audio <成片> --json`：有声音，响度在 -17 到 -15 LUFS 之间，音效与画面对齐。
4. 数学内容与 Astra 审核记录或数学依据一致。
