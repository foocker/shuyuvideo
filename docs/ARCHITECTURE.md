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

## 工作区边界

唯一配置在 [workspace.json](../workspace.json)，统一入口是根目录 `shuyu.ps1`（跨平台使用 `python scripts/shuyu.py`）。模块不再拥有独立输出根和安装环境。

```text
能力模块 + films/作品 + examples/示例
                  │ shuyu prepare <项目>
                  ▼
       output/<项目>/project/   离线构建包
                  │
     check / snapshot / render
                  ▼
       reports/          renders/
                  ▲
 shuyu math --project <项目> → math/<任务>/
```

- `motion/`、`math/`、`sound/`、`character/` 等保存公共代码和说明；源码按能力分工，生成物按作品归属。
- `examples/` 保存跨模块验证样例；台阶和同胚已从模块内移入这里。
- 一个根 `.venv`，一个根 `node_modules`；Manim 是根环境的可选依赖组。Astra 不再使用相邻仓库的解释器。
- HyperFrames 版本由项目注册表选择。旧作品保留已验证版本，新项目继承默认版本；统一入口不强行升级历史渲染器。
- 字体由 `style/fonts.json` 与 `scripts/font_assets.py` 管理，子集按内容缓存。构建包保留可搬运的离线副本及许可记录。
- 历史影片的输出实体迁到 `output/<项目>/archive/`，原位置仅保留兼容链接。研究输入与来源证据不属于构建缓存。

`shuyu layout` 检查模块是否重新出现独立产物或依赖目录。安装与迁移说明见 [SETUP.md](SETUP.md)。

## 选哪个引擎做镜头

各引擎擅长的事不同。按**镜头主体**选，不按习惯选。

| 镜头主体 | 用 | 原因 |
| --- | --- | --- |
| 公式逐项显现、着色、少量项移动与分组替换 | **HyperFrames + KaTeX + GSAP / SVG** | TeX 负责排版；合成层按语义组组织动作，并与图形、主体共用时间 |
| 大量连续代数推导、复杂项匹配与精确几何共演 | **Manim**（`MathTex` + `TransformMatchingTex` 等） | 原生数学对象与变换工具较齐全；仍须核对符号身份及等价条件 |
| 函数图像、坐标系、精确几何构造 | **Manim** | 坐标、切线、面积等由数学定义直接生成 |
| 2D 图形、计数、拼图、标注、文字 | **HyperFrames**（SVG + GSAP） | 编写最快，可在 Studio 中直接修改，中文排版好 |
| 曲面、拓扑形变、立体物体 | **Three.js**，放在 HyperFrames 场景里 | 已有作品的几何与材质可复用（[films/](../films/)） |
| 公式排版 | **KaTeX**，构建期或初始化时渲染为 HTML | 与正文同一图层；排版结果可作为动画对象，KaTeX 本身不负责动画 |
| Ω 角色 | **HyperFrames** 角色层（[character/](../character/README.md)） | 始终叠在最上层，任意镜头都可加入 |
| 几何烘焙、曲面数据、声音合成 | **Python**（numpy） | 离线计算，结果写成静态文件 |

规则：

- **合成只在 HyperFrames 里做。** Manim 片段导出为 1920×1080、30 fps 的 MP4，以 `<video>` 放进场景，再叠上 Ω、标注和转场。
- **Manim 片段必须用暖白主题**（[manim_theme.py](../style/adapters/manim_theme.py)）。底色与 HyperFrames 场景一致（`#F4F2EC`），否则切换处能看出接缝。
- **公式只用 TeX。** HyperFrames 里用 KaTeX，Manim 里用 `MathTex`。不用 Unicode 字符拼写公式（`x²`、`−`、`₁`）。
- **知识讲解片默认带 Ω 讲解角色。** 用 `compositions/guide.html` + `ShuyuStage`（[character/stage.js](../character/stage.js)）按口播锚点给出位置和动作，站在画面留白处，不遮挡图形和公式。参考 `films/staircase-sum`、`films/what-is-equal`。
- 能用 HyperFrames 写的 2D 镜头不要绕道 Manim。Manim 每改一次都要重新渲染，HyperFrames 可以实时预览、逐帧拖动。
- 渲染环境离线。GSAP、KaTeX、字体都放在作品的 `assets/` 下，不引用 CDN。

公式镜头先区分“增加模型项、加约束、等价整理、简化模型”，再选显现、移动或归并动作。详细做法见 [动画与公式一起讲解](../motion/references/formula-explanation.md)。当前 TeX 适配器只负责排版，尚无公共公式语义匹配或图式联动引擎；这些动作先在作品里实现与验证。

### 什么时候走 Astra

Astra（`shuyu math`）是“模型写数学依据和 Manim 场景、再由模型审核”的流水线。引擎和 Astra 分开决定：

| 情况 | 做法 |
| --- | --- |
| 镜头按上表该用 Manim（连续推导、函数图像、精确几何构造） | 用 `shuyu math run --project <作品> --clock <anchors.resolved.json>` 生成片段，审核通过后以 `<video>` 放进合成 |
| 镜头用 HyperFrames，但数学不是一眼可查（新定义、证明步骤、计数、对应关系） | 画面在 HyperFrames 里做；数学写进作品的 `mathematics.md`（对象、命题、推导、画面对应、不说的内容）。需要第二意见时，可用 `shuyu math prepare` 只生成数学依据，不采用它的场景 |
| 镜头只是计数、标注、已讲过的结论复现 | 直接在 HyperFrames 里做，不需要单独的数学依据 |

模型审核不是证明。无论走哪条路，交付前都要人核对数学依据和画面是否一致（交付前检查第 4 项）。例子：`films/what-is-equal` 的三连段用 HyperFrames 画立方体图，数学依据在 `mathematics.md`。

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
| [motion/](../motion/SKILL.md) | 动作设计、[镜头运动](../motion/references/camera.md)、[场景转场](../motion/references/transitions.md)，以及路径、衔接和时间取样检查 |
| [character/](../character/README.md) | Ω 角色。每个镜头单独指定位置、动作和朝向，不固定在角落 |
| [style/](../style/README.md) | 颜色、字号、语义角色 |

motion 内按职责分层，镜头与转场不再是与 motion 并列的能力目录：

```text
motion/
  SKILL.md          动作、镜头与转场的统一入口
  references/       设计规范、API 与检查契约
  runtime/          camera.js、transitions.js
  checks/           continuity.js、SVG 分析与浏览器取样
scripts/validation/ 素材来源与主画面分镜覆盖验证
```

构建时，`scripts/prepare-film.py` 将运行时准备到既有 `assets/lib/camera.js` 和 `assets/lib/transitions.js`。转场包包含唯一的对象衔接检查实现，保留 `ShuyuTransitions.check` 兼容入口；新增使用 `ShuyuMotionChecks.continuity`。作品无需修改原 script 路径。

素材来源、许可记录、文件哈希和分镜覆盖是跨模块制作检查，使用 `shuyu validate assets/timeline`，输入契约见 [公共验证](VALIDATION.md)。

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

环境准备与诊断见 [SETUP.md](SETUP.md)，先确保公共 `doctor` 没有阻断项。以下作品检查仍需逐片执行。

1. `shuyu check <项目>` 退出成功：HyperFrames 检查无错误，且屏幕文字扫描（`reports/screen-text.json`）没有乱码问号、裸露的 TeX 源码、Unicode 冒充的公式符号、TeX 中未包在 `\text{}` 里的中文，或制作备注（斜杠分隔的说明、镜头编号、TODO）。扫描只看源码中写出的文字，运行时拼出的文字仍要抽帧看。
2. `sound/mix.py` 必须退出成功，且最新 `mix-report.json` 的 `status` 为 `passed`；响度在 -17 到 -15 LUFS 之间，真峰值不高于 -1.5 dBTP。
3. `shuyu render <项目>` 退出成功：`films/` 下的作品默认在正片前接 3 秒品牌片头（`--no-intro` 关闭，见 [brand/](../brand/README.md)）；渲染后自动核对 MP4（`reports/render-check.json`），包括画布尺寸、有配乐时必须有音轨、音视频时长差不超过 0.08 秒、经过 `mix.py` 的作品编码后响度仍在上述范围。口型和口播节奏仍需看一遍成片。
4. 数学内容与 Astra 审核记录或作品的 `mathematics.md` 一致。用了口播时钟的 Astra 片段，导出时长须与时钟 `end` 相差不超过 0.5 秒。
