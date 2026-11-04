# 制作时可选择的能力

Omega 讲解员与 Manim 数学动画是两个独立选项，在执行制作时由用户选择，制作代理将结果写进本片 `BRIEF.md`。它们是内容与分镜选择，不是给 `shuyu render` 加一个参数就能自动补齐的后期特效。

| 选项 | 值 | 实际行为 |
| --- | --- | --- |
| `omega` | `on` | 正文中加入 Ω 讲解角色，按口播安排位置、视线、手势与出退场 |
| `omega` | `off` | 正文不加入讲解角色；品牌片头另按既有设置处理 |
| `manim` | `auto` | 逐段判断适合的引擎，记录采用和不采用的理由 |
| `manim` | `selected` | 用 Manim 制作指定数学片段，再剪入整片 |
| `manim` | `off` | 用 HyperFrames、SVG 或 Three.js 等完成镜头 |

新片尚未指定时，用一次简短提问提供这两项选择。可以直接说“带 Omega，极限那一段用 Manim”，或“不带 Omega，Manim 按需要”。已明确的部分不再询问；用户要求直接制作或暂未回应时，说明知识讲解片默认 `omega: on`、`manim: auto`，再按此执行。续做时读取已记录的选择，用户后续修改优先。

## 在简报中记录

将字段合入已有 frontmatter，正文写清实际段落与理由。例如：

```yaml
omega: on
manim: selected
```

```markdown
制作选择依据：用户要求带 Omega，并用 Manim 解释极限。
Omega：开场提出问题；图同构段指向对应节点；极限段指向误差；片尾收束。
Manim：极限段，显示数列项、误差区间与收敛条件；其余段落用 SVG / GSAP。
```

`auto` 的判断必须在分镜完成前写成具体决定。若全部片段都不用 Manim，也应写明原因，不能把 `auto` 解释成默认跳过。选择变化时同步更新简报、分镜和作品构建脚本，避免下一次重建恢复旧选择。

## 按选择制作

已验证的讲解片流程为：定稿与数学核对 → 生成旁白并取得实际时间 → 按段落选择 Manim 数学短片或原有三维母版 → 导出并剪入 HyperFrames → 按关键语句安排 Omega → 合成字幕、音效与混音 → 检查与成片抽帧。用户要求沿用这套流程时，直接继承 `omega: on`、`manim: selected` 并为新主题选择具体数学段落；不再重复询问是否需要这两项能力。

Omega 通过 [角色库](../character/README.md) 与 `ShuyuStage` 放在独立的 `compositions/guide.html` 角色层。按口播锚点编排动作，优先利用留白；重要数学动作可让角色暂退。不是全程固定站在角落或无目的循环挥手。片头 Ω 标志不算正文讲解员。

Manim 片段使用 [暖白主题](../style/adapters/manim_theme.py)，按最终画布和帧率导出，保存于作品 `assets/clips/`，再由 HyperFrames 的 `<video>` 剪入已确定的时间窗。由框架管理视频播放、裁切与同步，字幕、角色和混音仍在整片合成层处理。Manim 可以直接编写，也可以使用 [Astra](../math/README.md) 生成；是否调用模型与选择动画引擎是两件事。

## 交付核对

当前流程的具体作品入口：

- [什么是相等](../films/equality-explainer/README.md)：代数同构、极限使用 Manim，合入多主题讲解。
- [人，能变成球？](../films/human-to-sphere/explainer/README.md)：保留人体三维母版，加入同胚映射和亏格的 Manim 块。
- [莫比乌斯带](../films/mobius/explainer/README.md)：保留剪切、相扣及绕行母版，加入接缝配对和剪切分类的 Manim 块。
- [手指相扣，能挣脱吗？](../films/topology-unlock/explainer/README.md)：保留八状态解环母版，借指环挑战与橡胶人想象串起四步动作；Manim 讲清变形规则和固定闭环的约束。

这些作品均为 `omega: on`、`manim: selected`。三个拓扑讲解版的 `film.json`、`build.py`、`render_math.py` 展示了“旁白时钟 → 素材重定时 → 数学短片 → 角色与字幕 → 混音与成片检查”的可续做实现。解环版另用 `cutCues` 对齐动作阶段、`wordCues` 对齐概念文字，长句字幕按真实逐词时间拆分。它们是作品实例，具体镜头安排按新主题重写。

在 `REVIEW.md` 记录实际采用的选项及证据：Omega 的正文出镜时间、抽帧和遮挡检查；Manim 的源场景、导出文件、合成时间窗和成片抽帧。保存了角色库不代表角色出镜，生成了 Manim 文件不代表剪进成片。验收应对照最终 MP4；能力受阻时说明原因及替代方案，不静默跳过用户选择。
