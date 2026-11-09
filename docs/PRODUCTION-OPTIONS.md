# 制作模式与能力选择

开工先选择制作模式，再落实 Omega、Manim、配音与字幕，结果写进本片 `BRIEF.md`。这些选择决定内容与分镜，不是渲染时自动转换的特效。

| 模式 | 值 | 制作方式 |
| --- | --- | --- |
| 讲解模式 | `mode: explainer` | 口播驱动理解，Omega 可选，按真实口播时钟编排图形和演示 |
| 无讲解模式 | `mode: story-animation` | 纯动画画面，故事和动作推进；保留画外配音，可有字幕；角色参与故事，不面向观众讲课 |

无讲解模式固定 `omega: off`，保留 `narration: voiceover`，字幕默认 `captions: on`，可以关闭。它需要行动的因果关系，以及动作、音效和情绪节奏；内涵通过规则、选择和后果呈现。仅选择讲解模式的 `omega: off` 不会变成剧情动画。创作与验收见 [无讲解剧情动画](../writing/references/story-animation.md)。

| 选项 | 值 | 实际行为 |
| --- | --- | --- |
| `omega` | `on` | 正文中加入 Ω 讲解角色，按口播安排位置、视线、手势与出退场 |
| `omega` | `off` | 正文不加入讲解角色；品牌片头另按既有设置处理 |
| `manim` | `auto` | 逐段判断适合的引擎，记录采用和不采用的理由 |
| `manim` | `selected` | 用 Manim 制作指定数学片段，再剪入整片 |
| `manim` | `off` | 用 HyperFrames、SVG 或 Three.js 等完成镜头 |
| `narration` | `voiceover` | 保留画外配音，两种模式默认都启用 |
| `captions` | `on` / `off` | 显示或关闭配音字幕；必要的对象短标签单独安排 |

新片尚未指定时，用一次简短提问提供“讲解模式 / 无讲解模式”，同时收集有必要的 Omega、Manim 与字幕选择，继续材料和数学核对等独立工作。用户已说“无讲解模式”“纯动画、保留配音、不用角色讲解”时直接采用 `story-animation`，不再次确认。只有“不带 Omega”时仍可做讲解片，不擅自改为剧情动画。

已明确的部分不再询问；用户要求直接制作或合理等待后未回应时，说明普通知识讲解任务默认 `explainer`、`omega: on`、`manim: auto`、`narration: voiceover`、`captions: on`，再按此执行。无讲解模式默认 Omega 关闭，其余默认沿用。续做读取原简报；旧作品未记录 mode 时按原有流程继续，用户后续修改优先。

## 开工入口

```powershell
# 交互终端会提供两种模式供选择
.\shuyu.ps1 start geometry-adventure

# 对话中已选无讲解时，直接传入选择，不重复询问
.\shuyu.ps1 start geometry-adventure --mode story-animation --title "几何奇遇"
.\shuyu.ps1 start geometry-explainer --mode explainer --omega on --manim auto
```

`start` 创建本地 `films/<作品>/BRIEF.md`、`DIRECTION.md` 和用于项目发现的 `package.json`；无讲解模式带故事与声音分镜模板。可用 `--captions off` 关闭字幕。非交互调用必须显式传 `--mode`；`story-animation --omega on` 会报错。命令不覆盖已有目录，不生成配音或成片。

`BRIEF.md` 是逐片制作选择的记录源，续做或切换模式直接编辑该文件，并同步稿件、分镜与合成。完成 `index.html` 与场景后进入 `prepare/check/render`；这些命令不会仅凭 mode 字段自动改写镜头或移除旧讲解角色，成片仍须核对。

## 在简报中记录

将字段合入已有 frontmatter，正文写清实际段落与理由。例如：

```yaml
mode: explainer
omega: "on"
manim: selected
narration: voiceover
captions: "on"
```

```markdown
制作选择依据：用户要求带 Omega，并用 Manim 解释极限。
Omega：开场提出问题；图同构段指向对应节点；极限段指向误差；片尾收束。
Manim：极限段，显示数列项、误差区间与收敛条件；其余段落用 SVG / GSAP。
```

`auto` 的判断必须在分镜完成前写成具体决定。若全部片段都不用 Manim，也应写明原因，不能把 `auto` 解释成默认跳过。选择变化时同步更新简报、分镜和作品构建脚本，避免下一次重建恢复旧选择。

## 按选择制作

讲解片流程为：定稿与数学核对 → 生成旁白并取得实际时间 → 按段落选择数学短片或三维母版 → 剪入 HyperFrames → 按选择编排 Omega → 字幕、音效与混音 → 成片检查。

无讲解流程为：故事目标与数学规则 → 因果分镜与粗动画 → 画外配音实测、协调动作窗口 → 精修动画与镜头 → 字幕、音效、音乐和混音 → 故事可读性与成片检查。配音空白仍有动作、声音与情绪进展；当前混音长度由真实配音时钟的总长决定，纯动画片尾须计入 `tail`，详见 [时钟衔接](../writing/references/story-animation.md#与现有配音时钟衔接)。

用户要求沿用某片时，继承该片实际确认的模式和选项，不统一改成 `selected`；新主题仍须落实到具体镜头。

Omega 开启时，通过 [角色库](../character/README.md) 与 `ShuyuStage` 放在独立的 `compositions/guide.html` 角色层。按口播锚点编排动作，优先利用留白；重要数学动作可让角色暂退。不是全程固定站在角落或无目的循环挥手。片头 Ω 标志不算正文讲解员。

Manim 片段使用 [暖白主题](../style/adapters/manim_theme.py)，按最终画布和帧率导出，保存于作品 `assets/clips/`，再由 HyperFrames 的 `<video>` 剪入已确定的时间窗。由框架管理视频播放、裁切与同步，字幕、角色和混音仍在整片合成层处理。Manim 可以直接编写，也可以使用 [Astra](../math/README.md) 生成；是否调用模型与选择动画引擎是两件事。

## 交付核对

公开成片见 [作品预览](../README.md#作品预览)，本地源码入口见 [catalog.json](../catalog.json)，`films/` 不进入 Git。讲解版中的 `film.json`、`build.py`、`render_math.py` 可参考口播驱动的完整流程，参数和镜头安排须按新主题重写。《遭遇》示范 `auto` 选择两段 Manim；《台阶的一半》示范 `auto` 全部沿用 HyperFrames 精确拼图。

在 `REVIEW.md` 记录实际模式和选项的证据：Omega 开启时的正文出镜时间、抽帧和遮挡检查；Manim 选用时的源场景、导出文件、合成时间窗和成片抽帧。无讲解模式记录关闭配音与字幕后的故事可读性、关键动作与音效落点、转折及结尾的依据，确认没有讲解角色出镜；完整视听另行记录。保存了角色库不代表角色出镜，生成了 Manim 文件不代表剪进成片。验收应对照最终 MP4；能力受阻时说明原因及替代方案，不静默跳过用户选择。
