# 数语视频与动画

数学科普视频的制作仓库：研究好的视频，积累风格、角色和镜头，用 Astra 保证数学讲解正确，再合成成片。

## 目录

| 目录 | 作用 | 入口 |
| --- | --- | --- |
| [style/](style/README.md) | 数语暖白视觉风格：颜色、字体、各引擎的主题适配 | [风格页](style/preview.html) |
| [brand/](brand/README.md) | Ω 品牌片头：3 秒常用版、7 秒文字动画版 | [双版本预览](brand/preview.html) |
| [character/](character/README.md) | Ω 角色：表情、手势、15 个动作，可按时间取样、任意位置渲染 | [交互动作库](character/study.html) |
| [studies/](studies/README.md) | 好视频的拆解：原片、字幕、抽帧、表达方法 | [创作指引](studies/production-guide.md) |
| [math/](math/README.md) | Astra 数学讲解片段：简报 → 数学依据 → 分镜 → Manim → 审核 | `.\shuyu.ps1 math doctor` |
| [sound/](sound/README.md) | 配音、Freesound 音效选材与下载、混音和响度测量 | [音效 skill](sound/SKILL.md) |
| [motion/](motion/SKILL.md) | 动作设计、镜头与转场运行时、路径与连续性检查 | [台阶镜头验证](examples/staircase/README.md) |
| [films/](films/) | 已完成的作品，每部可独立重建 | 见下表 |

[积累方向](docs/REPOSITORY.md) · [索引](catalog.json) · [公共素材与分镜验证](docs/VALIDATION.md)

`films/` 和 `studies/cases/`（自己的作品、复刻对象的原片与抽帧）只保存在本地，不进入 Git，远程仓库中下面的成片链接不可用。

## 成片

| 作品 | 内容 | 成片 |
| --- | --- | --- |
| [human-to-sphere](films/human-to-sphere/README.md) | 人的表面为什么与球面同胚，带配音整片 | [185 秒](films/human-to-sphere/film/output/human-to-sphere-story-final.mp4) · [60 秒动画](films/human-to-sphere/renders/human-to-sphere-revised.mp4) |
| [mobius](films/mobius/README.md) | 莫比乌斯带绕行、剪切、相扣 | [120 秒](films/mobius/renders/mobius.mp4) |
| [topology-mistakes](films/topology-mistakes/README.md) | 字形拓扑 | [58 秒](films/topology-mistakes/output/topology-mistakes-final.mp4) |
| [topology-unlock](films/topology-unlock/README.md) | 八状态连续解环 | [60 秒](films/topology-unlock/output/topology-unlock-final.mp4) |
| [escher-encounter](films/escher-encounter/README.md) | Escher《遭遇》三维演绎 | [36 秒](films/escher-encounter/renders/encounter.mp4) |
| [character](character/README.md) | Ω 动作总览 | [36 秒](output/character/shuyu-omega-showcase.mp4) |

## 统一工作区

模块提供能力，作品与示例组织内容，生成物集中到根目录。约定见 [技术架构](docs/ARCHITECTURE.md) 和 [安装说明](docs/SETUP.md)。

```text
workspace.json         项目、引擎版本与输出约定
requirements*.txt      Python 依赖，统一安装到 .venv
package*.json          Node 依赖，统一安装到 node_modules
style/fonts.json       字体来源；.cache/fonts 保存可复用子集
examples/              可重建验证示例：staircase、homeomorphism
films/                 实际作品源码和定稿输入
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

台阶对比视频已迁到 [output/staircase-test/comparison/](output/staircase-test/comparison/)。历史影片的旧输出位置只保留指向根目录的兼容链接；新命令统一写入 `output/`。研究资料和版本化证据仍按出处归档。
