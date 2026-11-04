# 台阶求和：真实镜头验证

使用仓库既有 `films/staircase-sum` 的台阶镜头快照：10 个方块组成一份台阶，复制后翻转 180°，拼成 4×5 的长方形。本目录保留样式、场景及语音锚点，图形副本修正了拼合位移，详情见 [REVIEW.md](REVIEW.md)，原始来源哈希见 [source-manifest.json](../../motion/source-manifest.json)。

这是已存在镜头的独立测试页，保留原来的 24.25 秒时间和暖白样式；完整电影的子合成、声音与字幕仍在原作品中。构建仅写根目录 `output/staircase-test/`。

在仓库根目录运行：

```powershell
.\shuyu.ps1 setup
.\shuyu.ps1 prepare staircase-test
.\shuyu.ps1 validate assets output/staircase-test/asset-manifest.json
.\shuyu.ps1 validate timeline output/staircase-test/timeline.json --assets output/staircase-test/asset-manifest.json
.\shuyu.ps1 exec motion/checks/svg_audit.py output/staircase-test/brace.svg --report output/staircase-test/svg-report.json
.\shuyu.ps1 exec motion/checks/probe_motion.py output/staircase-test/probe.json --out output/staircase-test/qa
.\shuyu.ps1 exec examples/staircase/check_geometry.py
```

探针默认使用本机 Chrome，可用 `--browser <已有浏览器可执行文件>` 指定其他 Chromium。图片中没有外部品牌文案、联系方式或推广链接。

核对重点：复制体保持身份；翻转围绕自身中心；拼合后没有方块重叠或缺口；矩形描边使用设计的非线性缓动；同一时刻倒序重访截图一致。

`check_geometry.py` 测量最终 20 个方块的浏览器矩形，检查容纳关系、两两不重叠与总面积相等。它只适用于本例最终轴对齐的方块，不检查任意旋转多边形；方块的边框与圆角留白不计入几何空缺。

分镜契约使用 60 fps、1455 帧，准确表示原镜头的 24.25 秒，不把它悄悄四舍五入成 30 fps 整数帧。素材清单只声明本次检查的数学图形，页面的公共 JS、字体及它们的原许可仍随构建资源保留。

本次验证结果与边界见 [REVIEW.md](REVIEW.md)。检查通过仅覆盖该镜头、当前浏览器和已取样时刻。

## 视频对比

本地 `output/staircase-test/comparison/` 已生成带原声的对比文件：

- `staircase-side-by-side.mp4`：左原始、右修正，同步比较原片 8.2–32.4 秒，共 24.2 秒。
- `staircase-close-up.mp4`：原片 23.1–30.9 秒的同区域放大，观察拼合缝隙与矩形边界，共 7.8 秒。
- `staircase-original-clip.mp4` / `staircase-fixed-clip.mp4`：分别播放的 1080p 镜头片段。
- `staircase-fixed-full.mp4`：52.37 秒完整修正版，保留原配音、音效、角色和时间轴。

原版来自 `films/staircase-sum/renders/staircase-sum.mp4`。修正版在 `output/staircase-test/comparison/fixed-film/` 隔离副本中，仅替换 `assets/figure.js`，使用原固定版本 `hyperframes@0.8.220`、30 fps、delivery 质量重渲染。原作品文件未覆盖。24.2 秒裁切对应完整的 726 帧，结束在公式场景切换前。

完整修正版渲染完成后，可运行 `python examples/staircase/compare_videos.py` 重新打包对比视频。该脚本需要 FFmpeg 与 Pillow，标签使用本机微软雅黑；两侧共用一条原声，避免重叠混音。来源哈希、输出规格和检查记录保存在 `output/staircase-test/comparison/comparison-manifest.json`。
