# 来源、改写与许可范围

本次依据本地 `tools/shuyuvideostudy/skills` 快照吸收方法。上游为 [vibe-motion/skills](https://github.com/vibe-motion/skills)，核对提交 `4c86c0d016a3ba22ee673428a494f3c44f84111f`，记录日期 2026-11-04。具体参考文件及 SHA-256 见 [source-manifest.json](source-manifest.json)。来源 URL 是出处记录，不参与渲染。

| 参考 | 吸收内容 | 本地实现 |
| --- | --- | --- |
| `disney-animation-rule-skill` | 分阶段动作、主次关系、接触点、纯时间求值 | 中文教学动作规范；数学不变量优先于表演夸张 |
| `pixel2motion` | 语义部件、SVG 曲线审查、交叉描边、固定时刻截图、最终图比较 | 本地 SVG 分析和 GSAP 采样工具；支持圆弧与平滑命令，增加倒序重访、数值断言和严格尺寸比较 |
| `brand-launch-video-star` | 素材来源记录、文件哈希、分镜覆盖检查 | 公共 [Python 校验器](../scripts/validation/validate.py)；不限语言和片长，支持原创图形与实际许可记录 |

本地文档和检查脚本按这些方法重新组织与实现，没有整包复制上游技能。清理了安装推广、联系方式、默认外部品牌文案及远程个人网站依赖。固定动作比例、强制英文、广告片长度和切换 Remotion 工程的要求没有纳入本地流程。

`runtime/camera.js`、`runtime/transitions.js` 与 `checks/continuity.js` 来自本仓库原有镜头和转场实现，不属于上述上游技能。镜头与转场现统一归入 motion；跨模块素材和分镜验证归入 `scripts/validation/`，其来源记录仍保留在本页。

该上游快照未提供覆盖以上三个技能的统一 LICENSE 文件，也未在其目录发现明确的文件级授权声明。本记录保留出处，不把“可查看源码”写成 MIT、CC0 或其他未经声明的授权。

## 特定素材的许可不能扩大到整个仓库

- **克拉尼预览 GIF**：上游 `3d-chladni-render/SKILL.md` 明确标注 `assets/3d-chladni-cosmic.gif` 为 **“3D Chladni media by Lykno, licensed under CC BY-NC 4.0.”** [许可文本](https://creativecommons.org/licenses/by-nc/4.0/)。此许可记录只对应该预览媒体，不代表外部 3D-Chladni 代码或所有生成结果都采用此许可。本次未复制 GIF 或调用其外部工程。
- **布帘引擎**：上游 `printed-curtain-render/assets/printed-curtain-template/NOTICE.txt` 标注由 Jason Labbe 的 [Dynamic ropes 2](https://openprocessing.org/sketch/533576) 改编，适用 **CC BY-SA 4.0**。[许可文本](https://creativecommons.org/licenses/by-sa/4.0/)。其中捆绑的 p5.js 1.9.4 另有 **LGPL v2.1** 声明。本次未复制引擎或 p5.js；后续若引入，应一并保存 NOTICE、代码内许可及改动说明。

## 本地案例

`../examples/staircase/` 来自本仓库 `films/staircase-sum` 的图形、样式、台阶场景和语音锚点快照。来源路径与修改情况记录在清单和案例审查中。构建使用本仓库 GSAP、KaTeX、字体子集及镜头模块；原依赖的许可文件仍由 npm 包保存，不用本页替换它们。

这些工具目前只验证下述范围：清单结构、文件完整性、主画面分镜覆盖、SVG 局部路径、独立 GSAP 场景的抽样与重访。完整影片媒体同步、数学推导及观众学习效果仍需各自证据。

其他技能的处理见 [候选清单](references/candidates.md)。
