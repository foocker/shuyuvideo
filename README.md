# 数语视频与动画

数学科普视频的制作仓库：研究好的视频，积累风格、角色和镜头，核对数学依据，再合成成片。按内容选择 Manim 数学块与已有三维素材，Omega 在关键讲解处出场；两项可独立配置。

首次使用看 [安装与命令](docs/SETUP.md)；制作前看 [能力选择](docs/PRODUCTION-OPTIONS.md) 和 [口播稿](docs/NARRATION.md)；引擎分工看 [架构](docs/ARCHITECTURE.md)，交付要求统一在 [验证](docs/VALIDATION.md#交付核对)。

## 作品预览

下方动图为 8 秒无声片段；点击预览图打开或下载完整成片，均为 1920×1080、30 fps，含中文配音和字幕。

| 作品 | 动画预览 · 点击查看完整 MP4 |
| --- | --- |
| **画里的人，怎么走出来了？**<br>《遭遇》：图底关系、镶嵌与三维相遇<br>3 分 05 秒 | [![《遭遇》：人物绕环相遇的动画预览](public/previews/escher-encounter-explainer.gif)](public/videos/escher-encounter-explainer.mp4?raw=true) |
| **莫比乌斯带**<br>反向接缝、剪切与相扣<br>2 分 48 秒 | [![莫比乌斯带剪切与相扣的动画预览](public/previews/mobius-explainer.gif)](public/videos/mobius-explainer.mp4?raw=true) |
| **台阶的一半**<br>一般项、省略号与翻转拼合<br>1 分钟 | [![一般项阶梯翻转拼合的动画预览](public/previews/staircase-sum.gif)](public/videos/staircase-sum.mp4?raw=true) |
| **什么是相等**<br>从数值相等到结构相同<br>2 分 55 秒 | [![图的连接关系与结构相同的动画预览](public/previews/equality-explainer.gif)](public/videos/equality-explainer.mp4?raw=true) |
| **人的表面，为什么能变成球面？**<br>理想外表面、同胚与亏格<br>2 分 35 秒 | [![人体理想外表面连续变形的动画预览](public/previews/human-to-sphere-explainer.gif)](public/videos/human-to-sphere-explainer.mp4?raw=true) |
| **手指相扣，能挣脱吗？**<br>橡胶人体模型与连续解环<br>2 分 34 秒 | [![橡胶人体收缩并保留连接关系的动画预览](public/previews/topology-unlock-explainer.gif)](public/videos/topology-unlock-explainer.mp4?raw=true) |

公开副本及更新说明见 [public/](public/README.md)。

## 目录

| 目录 | 作用 | 入口 |
| --- | --- | --- |
| [style/](style/README.md) | 数语暖白视觉风格：颜色、字体、各引擎的主题适配 | [风格页](style/preview.html) |
| [brand/](brand/README.md) | Ω 品牌片头：3 秒常用版、7 秒文字动画版 | [双版本预览](brand/preview.html) |
| [character/](character/README.md) | Ω 角色：表情、手势、15 个动作，可按时间取样、任意位置渲染 | [交互动作库](character/study.html) |
| `studies/`（本地） | 好视频的拆解：原片、字幕、抽帧、表达方法 | 本地 `studies/production-guide.md` |
| [math/](math/README.md) | Astra 数学讲解片段：简报 → 数学依据 → 分镜 → Manim → 审核 | `.\shuyu.ps1 math doctor` |
| [sound/](sound/README.md) | 配音、Freesound 音效选材与下载、混音和响度测量 | [音效 skill](sound/SKILL.md) |
| [motion/](motion/SKILL.md) | 动作设计、镜头与转场运行时、路径与连续性检查 | [台阶镜头验证](examples/staircase/README.md) |
| [public/](public/README.md) | 公开成片与 README 动图预览 | [作品预览](#作品预览) |
| `films/`（本地） | 作品源码与定稿输入，每部可独立重建 | [公开作品预览](#作品预览) |

[制作选项：Omega / Manim](docs/PRODUCTION-OPTIONS.md) · [积累方向](docs/REPOSITORY.md) · [索引](catalog.json) · [公共素材与分镜验证](docs/VALIDATION.md)

`films/`、`studies/` 和 `output/` 只保存在本地，不进入 Git；经选择公开的成片复制到 `public/`。其余本地作品与研究资料链接在远程仓库中不可用。全新克隆可先运行已纳入 Git 的 `examples/staircase` 验证环境。

## 统一工作区

模块提供能力，作品与示例组织内容，生成物集中到根目录。约定见 [技术架构](docs/ARCHITECTURE.md) 和 [安装说明](docs/SETUP.md)。

```text
workspace.json         项目、引擎版本与输出约定
requirements*.txt      Python 依赖，统一安装到 .venv
package*.json          Node 依赖，统一安装到 node_modules
style/fonts.json       字体来源；.cache/fonts 保存可复用子集
examples/              可重建验证示例：staircase、homeomorphism
films/                 实际作品源码和定稿输入
public/                公开成片副本与 README 动图
motion/ math/ …         公共能力源码、技能与说明
output/<项目>/          构建包、视频、报告和数学片段任务
```

```powershell
.\shuyu.ps1 setup --math --dev
.\shuyu.ps1 list
.\shuyu.ps1 prepare staircase-test
.\shuyu.ps1 check staircase-test
.\shuyu.ps1 render staircase-test
.\shuyu.ps1 math prepare --project <作品> --prompt-file <主题文件>
.\shuyu.ps1 test --math
```

台阶对比视频保存在本地 `output/staircase-test/comparison/`。历史影片的旧输出位置只保留指向根目录的兼容链接；新命令统一写入 `output/`。研究资料和版本化证据仍按出处归档。
