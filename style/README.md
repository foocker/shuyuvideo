# 数语暖白 · 视觉基线 v1

[打开风格页](preview.html) · [机器参数](tokens.json) · [视觉审查与验证](AUDIT.md) · [Math-To-Manim 接入约定](../math/README.md)

2026-10-30，依据用户指定的 `tools/shuyuvideo` 现有案例提炼。新素材和新作品以这套视觉身份为基础，来源于其他引擎的数学片段也按此适配。已有作品的源文件和成片保持原样。

## 1. 共同风格

暖白背景、深灰绿文字、低饱和青绿几何、陶红关系强调、赭金局部焦点。三维主体圆润、哑光，用柔和明暗说明表面；构图围绕当前讲解对象保留空间。二维图形和公式延续同样的颜色关系。

这里固定的是颜色的职责和视觉基调，具体布局随问题变化。字形片有标题与说明，莫比乌斯片几乎全屏展示几何，两者都属于这套风格。

art-motion 的笔刷、材质和动画方法是可选能力。水墨、宣纸纹理、光晕和不断运动的背景不属于当前默认外观。Math-To-Manim 提供数学讲解片段；其示例的深底、饱和色和镜头节奏由具体片段适配。

## 2. 默认颜色与职责

色值来自源码，不是截图吸色。三维材质经过灯光和色调映射后，显示像素会变化。

| Token | 色值 | 用途 | 来源 |
|---|---|---|---|
| `background` | `#F4F2EC` | 全片基础背景 | 人体片、同胚定义片 |
| `ink` | `#203B35` | 正文、公式、轴线、关键轮廓 | 同胚定义片 |
| `muted` | `#536359` | 注释、次级说明 | 同胚定义片 |
| `line` | `#C8CEC5` | 非语义分隔线、辅助网格 | 同胚定义片 |
| `subject` | `#548D80` | 主几何、曲线、较大主体 | 字形拓扑片 |
| `subjectLight` | `#8BBAAA` | 大面填充、带面正面 | 莫比乌斯片 |
| `emphasis` | `#B64D35` | 当前映射、关键符号和关系 | 同胚定义片 |
| `focus` | `#D2AA58` | 关注位置、小球、局部面积 | 莫比乌斯片 |
| `backface` | `#63533F` | 带面背侧、朝向区分 | 莫比乌斯片 |
| `neutralBody` | `#D1CCC0` | 中性人体与实体基色 | 人体片 |

`surface` 与 `neutralCool` 保留解环片的偏冷浅色。完整颜色及源文件行号见 `tokens.json`。

历史背景分别还有 `#F7F4E8`（莫比乌斯）、`#F5F3EC`（字形）、`#F7F7F3`（解环）与 Ω 原展示底色。它们作为来源变体记录；新片跨引擎拼接时先选定一个背景，默认 `#F4F2EC`，避免接缝跳色。

### 文字色与物体色

对默认背景的平涂对比度：`ink` 10.79:1、`muted` 5.69:1、`emphasis` 4.57:1。三者可作为普通文字起点。

`subjectLight` 1.93:1、`focus` 1.95:1，适合大面和局部色块；小字使用 `ink`，关键轮廓另加深色线。`subject` 3.41:1 可用于清楚的图形线条；细小公式仍优先使用 `ink`。对比度不替代最终尺寸、压缩后画面及动态观看检查。

## 3. 语义色先服务数学

**对象区分：** 字形片的五色 `#548D80 / #718BAF / #C38460 / #9B849F / #9A9E70` 按对象身份绑定。O/N/E 变形、换位后保持对应颜色。可以配编号、形状或文字，不只依靠颜色。

**表面追踪：** 人体七色保持原有开口与原始材料坐标的身份，不为了风格统一改成全部青绿。七色是特定教学任务的编码，不是全片装饰色板。

**关系强调：** 陶红可以表示正在解释的映射或关注关系；只有本片明确约定后才表示负值、错误或另一种含义。同色不应无说明地承担冲突含义。

迁移外部数学场景时，先写出“变量/对象/正负/状态 → 颜色及辅助标识”的映射，再改源码。全局 RGB 替换可能破坏原有数学编码。

## 4. 材质、字和空间

- 主要实体的实际粗糙度为 0.64–0.82，金属度为 0–0.03；新物体可从 `roughness=0.76, metalness=0` 开始。针等金属道具和追踪小球有独立材质。
- 主光通常在左上前方；根据物体、尺度和渲染器校准。色调映射与曝光决定最终颜色，不能只比材质十六进制。
- 中文使用清楚的无衬线。现有片使用本地字体子集；新片需包含自己的文案字形。默认字体名为 `Microsoft YaHei`，可替换为具备目标字形的固定字体，最终工程保存实际字体来源。
- 1920×1080 下，标题 68 px、说明 34 px、注释 28 px 是从现有片提取的起点。公式字号按内容密度调整，默认建议 52 px。Manim 的字号需在实际渲染中校准，不把 CSS px 当成相同单位。
- 数学片段新接入使用 Manim MathTex 的 Computer Modern 作为起点。这是新增约定，尚未声称全部历史作品已有同一数学字体。
- 默认横屏 1920×1080、30 fps；左边距参考 108 px、上边距 72 px。这些是创作起点；原 4:3 莫比乌斯片保留比例。
- 背景分隔线可以淡；需要看清的边、连接、切口、公式和坐标轴不能为了“柔和”失去辨识度。

## 5. 怎样使用

`tokens.json` 是编辑源；`tokens.css` 和 `tokens.js` 由脚本生成。

浏览器 / SVG：

```html
<link rel="stylesheet" href="path/to/style/tokens.css">
<style>
  .scene { background: var(--shuyu-background); color: var(--shuyu-ink); }
  .math-curve { stroke: var(--shuyu-subject); }
</style>
```

Canvas / Three.js：

```html
<script src="path/to/style/tokens.js"></script>
<script>
  const colors = window.ShuyuStyle.colors;
  // ctx.fillStyle = colors.background;
  // material.color.set(colors.subjectLight);
</script>
```

Manim：使用 [manim_theme.py](adapters/manim_theme.py) 的显式函数，或直接读 JSON。函数只设置当前场景背景和新建的文字/公式，不在导入时覆盖全局类默认值。旧场景中显式设置的颜色仍需要按语义改写。

已实际用本机 Manim CE 0.21.0 渲染 [静态样张](evidence/manim-style.png)，验证中文、MathTex、曲线和颜色能够共同呈现。它是本地原创风格验证，没有导入 Math-To-Manim 场景，也没有验证其完整流水线兼容性。

```powershell
# 在 tools/shuyuvideo 执行
python style/scripts/build-style.py
python -m manim -s --disable_caching -r 1920,1080 --media_dir style/evidence/manim style/adapters/manim_style_proof.py ShuyuStyleProof
```

加 `--references` 可重新提取六部本地参考成片的静帧；时间和源文件 SHA-256 写入 `evidence/references.json`。生成脚本也核对每个核心色是否确实出现在对应源码中。

## 6. 如何继续积累

先以 v1 制作新片。确需新颜色时，记录对象、职责、与现有颜色冲突的原因及实际帧；通用于多部作品后再更新基线。个别场景需要的颜色放在该作品中，避免每次制作都扩大公共色板。

视觉身份、数学语义、表达方法和渲染工具分别维护。风格统一到每部作品的实际画面上，能力和方法通过作品逐步验证。
