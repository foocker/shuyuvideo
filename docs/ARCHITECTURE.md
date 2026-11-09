# 技术架构：一部数学科普视频怎样做出来

开工先按 [制作选项](PRODUCTION-OPTIONS.md) 选择讲解或无讲解模式，可用 `shuyu start <项目> --mode story-animation` 生成剧情动画的简报与导演稿。下表描述讲解片的依赖；无讲解模式以故事、分镜与粗动画为先，画外配音随后协调进动作窗口，具体见 [剧情动画](../writing/references/story-animation.md)。

一部讲解片分五层，自上而下依赖：

| 层 | 负责 | 工具 | 产物 |
| --- | --- | --- | --- |
| 1 口播稿 | 讲什么、按什么顺序讲；全片的时钟 | [writing](../writing/SKILL.md) 辅助构思与编辑，[规范](NARRATION.md) | `SCRIPT.md` 或 `SCRIPT.writing.md`、`narration.json` |
| 2 数学核对 | 定义、推导、结论不出错 | `mathematics.md`；可选 [Astra](../math/README.md) 辅助审核 | 数学依据、审核记录 |
| 3 镜头素材 | 每个镜头的主体动画 | Manim、HyperFrames、Three.js（见下） | 单个短片段或网页场景 |
| 4 合成 | 排版、公式、Ω 角色、转场、镜头运动、字幕 | HyperFrames（HTML + GSAP + KaTeX） | `index.html` + `compositions/` |
| 5 声音 | 配音、音效、混音、响度 | [sound/](../sound/README.md) | `narration.wav`、`final-mix.wav` |

讲解模式写稿时规划画面承担的解释，口播稿先定稿，配音生成后得到逐词时间，画面实现按这些时间排。两种模式都将配音正文与导演说明分开；写作模块的编辑入口和确定性导出见 [文件契约](../writing/references/files.md)。

讲解模式制作顺序是：定稿与数学核对 → 按信息密度标记局部语速和停顿 → 生成配音并核对真实节奏 → 用实际语音时钟编排画面、字幕与动作 → 混音与成片检查。写稿阶段就考虑画面解释任务；节奏不合适时回到配音设置重生成时钟，再同步后续画面。详见 [语速与留白](NARRATION.md#信息密度语速与留白)。

无讲解模式先建立目标、阻碍、尝试与结果的因果分镜，数学规则影响行动；粗动画验证节奏后实测画外配音，再锁定动画、字幕和声音时间。Omega 讲解层关闭，故事中的角色可以行动。当前声音链仍以 `voice-timings.json` 的总长混音，纯动画的时间段与片尾须计入该时钟，不能只延长 HTML。

封面由 [cover/](../cover/SKILL.md) 独立制作：定标题和开场钩子时选主体与短文案，保存本地图像及 `cover.json`，用 Pillow 排版。最后与视频成对交付；这一静态图片流程不依赖视频时间轴，也不会在每次构建时自动调用生图 API。

平台发布由 [publish/](../publish/SKILL.md) 独立承接交付：通用层绑定用户确认的视频和封面，平台层维护各自文案与设置。当前 B 站生成本地可复制的填写页面，由用户手动上传、填写和发布；小红书、视频号后续可扩展平台资料，共用成片确认。第三方 social-auto-upload 的 [评估](../publish/references/social-auto-upload.md) 仅留作参考，当前未启用自动上传。

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

- `writing/`、`cover/`、`motion/`、`math/`、`sound/`、`character/` 等保存公共代码和说明；源码按能力分工，生成物按作品归属。
- `examples/` 保存跨模块验证样例；台阶和同胚已从模块内移入这里。
- 公共命令使用根 `.venv` 与 `node_modules`。Astra 的 Manim 渲染优先使用 `envs/manim/.venv`，未安装时使用当前解释器；普通 `shuyu exec` 始终使用根环境。安装与版本归属见 [SETUP.md](SETUP.md)。
- HyperFrames 版本由项目注册表选择。旧作品保留已验证版本，新项目继承默认版本；统一入口不强行升级历史渲染器。
- 字体由 `style/fonts.json` 与 `scripts/font_assets.py` 管理，子集按内容缓存。构建包保留可搬运的离线副本及许可记录。
- 历史影片的输出实体迁到 `output/<项目>/archive/`，原位置仅保留兼容链接。研究输入与来源证据不属于构建缓存。

`shuyu layout` 检查模块是否重新出现独立产物或依赖目录。安装与迁移说明见 [SETUP.md](SETUP.md)。

## 选哪个引擎做镜头

先按 [制作选项](PRODUCTION-OPTIONS.md) 落实模式及 Omega、Manim 等选择，写入作品 `BRIEF.md`。无讲解模式关闭 Omega 讲解层；Manim 在两种模式下仍可独立选择。用户选择优先；下表用于 `manim: auto` 的逐镜头判断。

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
- **Ω 是否出镜按本片 `omega` 选择执行。** 知识讲解片未指定时默认 `on`，用户可选 `off`。启用时用 `compositions/guide.html` + `ShuyuStage`（[character/stage.js](../character/stage.js)）按口播锚点安排位置和动作，站在画面留白处，不遮挡图形、公式和字幕。片头 Logo 不算讲解员出镜。
- `manim: auto` 时，能直接表达的 2D 镜头优先用 HyperFrames；连续推导、函数图像、精确几何按上表考虑 Manim。`selected` 按指定片段执行，`off` 使用其他适合的引擎；不能用自动判断覆盖用户选择。Manim 每改一次都要重新渲染，HyperFrames 可以实时预览、逐帧拖动。
- 渲染环境离线。GSAP、KaTeX、字体都放在作品的 `assets/` 下，不引用 CDN。

公式镜头先区分“增加模型项、加约束、等价整理、简化模型”，再选显现、移动或归并动作。详细做法见 [动画与公式一起讲解](../motion/references/formula-explanation.md)。当前 TeX 适配器只负责排版，尚无公共公式语义匹配或图式联动引擎；这些动作先在作品里实现与验证。

### 什么时候走 Astra

Astra（`shuyu math`）是“模型写数学依据和 Manim 场景、再由模型审核”的流水线。引擎和 Astra 分开决定：

| 情况 | 做法 |
| --- | --- |
| 本片选择使用 Manim 的片段（连续推导、函数图像、精确几何构造等） | 可用 `shuyu math run --project <作品> --clock <anchors.resolved.json>` 生成，也可直接编写 Manim 场景；审核通过后以 `<video>` 放进合成。使用 Manim 不等于必须调用 Astra |
| 镜头用 HyperFrames，但数学不是一眼可查（新定义、证明步骤、计数、对应关系） | 画面在 HyperFrames 里做；数学写进作品的 `mathematics.md`（对象、命题、推导、画面对应、不说的内容）。需要第二意见时，可用 `shuyu math prepare` 只生成数学依据，不采用它的场景 |
| 镜头只是计数、标注、已讲过的结论复现 | 直接在 HyperFrames 里做，不需要单独的数学依据 |

模型审核不是证明。无论走哪条路，交付前都要核对数学依据和画面是否一致。一般项、有限窗口与真实拼合的要求见 [数学画面验收](VALIDATION.md#数学画面与一般项)。

## 数据流

```
登记稿件 ──► writing export ──► narration.json ──► sound/voice.py ──► 逐句音频 + 逐词时间 (voice-timings.json)
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
  BRIEF.md           模式、Omega/Manim/配音/字幕选择及逐片段安排
  SCRIPT.md          口播稿（人读）
  DIRECTION.md       讲解画面任务，或剧情动画的因果分镜、动作与声音事件
  COVER.md           封面主体、钩子、来源与看图记录
  cover.json         封面本地图像与中文排版，素材在 assets/cover/
  .writing.json      启用 writing 后的编辑入口与导出摘要
  narration.json     口播逐句、配音设置（机器读）
  voice-timings.json 配音后生成：每句与每个词的实际时间
  sound-cues.json    音效：时间、种类、增益、对应的画面事件
  index.html         根合成：场景、配音轨、音效轨
  compositions/      每个场景一个文件
  assets/            vendor（GSAP、KaTeX）、fonts、audio、clips（Manim 片段）
  REVIEW.md          检查记录
```

旧项目若使用 `SCRIPT.writing.md`，它是正文编辑源，`SCRIPT.md` 可以继续作为旧构建生成的展示稿。已登记作品在公共准备、配音与混音检查中核对文稿同步；改稿后先导出，再刷新真实时钟。状态摘要不表示数学或试听已通过。

`shuyu render` 对 `films/` 作品预检封面，成片测量通过后生成 `renders/<视频名>-cover.jpg` 和 `delivery.json`。品牌片头与技术示例不强制封面。`shuyu deliver <项目>` 为已有 MP4 补图、测量并绑定双文件，不重新渲染；`--check` 检查输入和交付哈希。文件契约见 [封面配置](../cover/references/files.md)。

## 交付前检查

先按 [安装说明](SETUP.md) 确认环境，再按 [交付核对](VALIDATION.md#交付核对) 验证数学、正文角色、声音和最终 MP4。该表是验收要求的维护入口；`REVIEW.md` 记录本片证据和保留的警告。
