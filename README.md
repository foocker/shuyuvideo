# 数语视频与动画

数学科普视频的制作仓库：研究好的视频，积累风格、角色和镜头，用 Astra 保证数学讲解正确，再合成成片。

## 目录

| 目录 | 作用 | 入口 |
| --- | --- | --- |
| [style/](style/README.md) | 数语暖白视觉风格：颜色、字体、各引擎的主题适配 | [风格页](style/preview.html) |
| [character/](character/README.md) | Ω 角色：表情、手势、15 个动作，可按时间取样、任意位置渲染 | [交互动作库](character/study.html) |
| [studies/](studies/README.md) | 好视频的拆解：原片、字幕、抽帧、表达方法 | [创作指引](studies/production-guide.md) |
| [math/](math/README.md) | Astra 数学讲解片段：简报 → 数学依据 → 分镜 → Manim → 审核 | `.\math\astra.ps1 doctor` |
| [films/](films/) | 已完成的作品，每部可独立重建 | 见下表 |

[积累方向](docs/REPOSITORY.md) · [索引](catalog.json)

`films/` 和 `studies/cases/`（自己的作品、复刻对象的原片与抽帧）只保存在本地，不进入 Git，远程仓库中下面的成片链接不可用。

## 成片

| 作品 | 内容 | 成片 |
| --- | --- | --- |
| [human-to-sphere](films/human-to-sphere/README.md) | 人的表面为什么与球面同胚，带配音整片 | [185 秒](films/human-to-sphere/film/output/human-to-sphere-story-final.mp4) · [60 秒动画](films/human-to-sphere/renders/human-to-sphere-revised.mp4) |
| [mobius](films/mobius/README.md) | 莫比乌斯带绕行、剪切、相扣 | [120 秒](films/mobius/renders/mobius.mp4) |
| [topology-mistakes](films/topology-mistakes/README.md) | 字形拓扑 | [58 秒](films/topology-mistakes/output/topology-mistakes-final.mp4) |
| [topology-unlock](films/topology-unlock/README.md) | 八状态连续解环 | [60 秒](films/topology-unlock/output/topology-unlock-final.mp4) |
| [escher-encounter](films/escher-encounter/README.md) | Escher《遭遇》三维演绎 | [36 秒](films/escher-encounter/renders/encounter.mp4) |
| [character](character/README.md) | Ω 动作总览 | [36 秒](character/output/shuyu-omega-showcase.mp4) |

## 重建

各作品目录先运行 `npm ci`（依赖未随仓库保存），Python 依赖见 `scripts/requirements.txt`，成片验证为 `npm run verify:render`（需 FFmpeg/ffprobe）。渲染环境离线，第三方 JS/CSS/字体放在各项目 `assets/` 下。`math/` 首次使用前运行 `.\math\astra.ps1 setup`，它会安装自己的 Node 依赖。
