# 公开成片

这七部完整视频可从 GitHub 打开或下载；仓库首页直接展示动画片段。

| 作品 | 完整视频 | 预览片段（成片时间） |
| --- | --- | --- |
| 数学中的光滑，到底是什么意思？ | [6 分 57 秒 MP4](videos/smooth-structure-long.mp4?raw=true) · [封面 JPG](covers/smooth-structure-long-cover.jpg) | [01:40–01:48](previews/smooth-structure-long.gif) |
| 画里的人，怎么走出来了？ | [3 分 05 秒 MP4](videos/escher-encounter-explainer.mp4?raw=true) | [02:28–02:36](previews/escher-encounter-explainer.gif) |
| 莫比乌斯带 | [2 分 48 秒 MP4](videos/mobius-explainer.mp4?raw=true) | [01:56–02:04](previews/mobius-explainer.gif) |
| 台阶的一半 | [1 分钟 MP4](videos/staircase-sum.mp4?raw=true) | [00:22.5–00:30.5](previews/staircase-sum.gif) |
| 什么是相等 | [2 分 55 秒 MP4](videos/equality-explainer.mp4?raw=true) | [00:45–00:53](previews/equality-explainer.gif) |
| 人的表面，为什么能变成球面？ | [2 分 35 秒 MP4](videos/human-to-sphere-explainer.mp4?raw=true) | [00:41–00:49](previews/human-to-sphere-explainer.gif) |
| 手指相扣，能挣脱吗？ | [2 分 34 秒 MP4](videos/topology-unlock-explainer.mp4?raw=true) | [00:59–01:07](previews/topology-unlock-explainer.gif) |

`videos/` 保存从 `output/<项目>/renders/<项目>.mp4` 原样复制的定稿，1920×1080、30 fps，保留配音、字幕和音效。`previews/` 是从成片截取的 640×360、12 fps、8 秒无声 GIF，用于 README 展示。

更新时先完成作品验收，再复制指定 MP4、更新对应预览并核对首页链接。作品源码、配音缓存、研究原片和构建包继续保存在本地；仅此目录中的展示副本纳入 Git。

后续影片固定交付视频与独立封面。用户指定公开时，先运行 `shuyu deliver <项目> --check`，再将定稿 JPG 复制到 `public/covers/<片名>-cover.jpg`，与 MP4 一起更新链接。`previews/` 的动态预览继续独立维护；历史公开影片不因新增封面功能而批量重做。
