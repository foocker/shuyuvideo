# 完整作品研究

从完整作品中提炼可迁移的表达方法，并保留能回看、能反驳、能继续实现的证据。首轮研究日期：2026-10-30。

当前完成一个案例：3Blue1Brown《Backpropagation, intuitively》。研究覆盖全片组织，重点分析 04:42–09:31 的局部解释、贡献汇总与返回整体。2026-10-31 已迁入数语仓库，原视频、字幕、抽帧和所引用的研究资料均保存在本目录；复制原视频时核对了 SHA-256。

## 从这里读

| 入口 | 内容 |
|---|---|
| [用于新片的创作指引](production-guide.md) | 从观众理解障碍选择方法；Astra 新任务自动带入并保存快照 |
| [可点选片段的阅读页](cases/backpropagation/index.html) | 原片播放器、全片章节、14 个分析事件、官方口播文本、画面证据 |
| [完整作品分析](cases/backpropagation/README.md) | 观看目标、前提、全片理解过程、核心对象、重点段落及局限 |
| [04:42–09:31 细读](cases/backpropagation/close-reading.md) | 每一步的已有认识、新问题、画面操作、得到的认识与概念边界 |
| [7 种表达方法](methods.md) | 适用问题、操作、证据、失败条件、迁移建议及可能需要的实现 |
| [art-motion 可借鉴的能力](art-motion-reuse.md) | 哪些已有能力能用、哪些约束依赖题材、哪些能力还需通过新作品验证 |
| [声音与时间证据](cases/backpropagation/audio.md) | 字幕句间间隔、原混音响度包络、目前可以和不可以判断的内容 |
| [核验记录](cases/backpropagation/REVIEW.md) | 来源、时间范围、文字边界和阅读页功能的检查结果 |

双击阅读页即可加载本目录的数据和原视频，不需要联网或安装前端依赖。原片位于 `cases/backpropagation/sources/original.mp4`，随本目录一起复制。若浏览器限制本地媒体，在 `tools/shuyuvideo` 下执行：

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

然后打开 `http://127.0.0.1:8765/studies/cases/backpropagation/`。浏览器需支持原片的 AV1 视频与 Opus 音频；网页会报告媒体加载错误，也可使用本地播放器按文档时间码查看。

## 这次实际完成到哪里

- 全片每 25 秒抽帧，14 个事件另行加密；4 处转换以每秒 4 帧观察。
- 官方 73 句字幕及时间文件保存在本地，来源固定到 Git 提交并记录 SHA-256。
- 核心段落的观察、解释和迁移建议分开记录。章节边界是语义划分，部分直接采用字幕句界，不能当作精确剪辑点。
- 声音完成了原混音的 100 毫秒 RMS 包络测量和字幕句间间隔整理；未听辨音乐配器、音效、混音层次或完成全片连续视听审阅。
- 7 种方法均为**本案例支持的迁移假设**。没有新题材成片或观众测试，不能称为已验证的通用创作规律。
- 研究所引用的 art-motion 文档和源码已保存为本地文本快照；没有将片段声明为已接入的运行引擎或动画模板。

## 如何积累下一部作品

每个案例围绕四个问题组织：观众起初知道什么；作品让观众依次理解什么；哪种视听操作承担了这次理解；换题材后什么条件仍须成立。

保留三层资料：

1. **作品案例**：出处、范围、整片组织、时间码、画面和声音证据。
2. **表达方法**：从案例中抽出的操作，注明适用范围、失败例、待验证部分。
3. **实现需求**：新作品真正用到后，再判断哪些应成为通用函数、对象接口或检查工具。

同一条方法再次出现时，增加独立作品证据；新作品不支持时，缩小适用范围或修正原结论。两段连续帧不算两个独立案例。抽帧可以证明某种画面状态出现过，不能单独证明流畅性、听感或学习效果。

## 结构与复现

`cases/backpropagation/study.json` 是章节、事件、取样时间和方法编号的编辑源。阅读页使用的 `study-data.js` 由脚本生成，避免直接打开 HTML 时遇到本地 JSON 读取限制。

```powershell
# 从 studies 目录执行；依赖 ffmpeg/ffprobe、Pillow、numpy、matplotlib
python -m pip install -r requirements.txt
python scripts/build_evidence.py cases/backpropagation
```

脚本验证视频和字幕摘要、时间范围与章节覆盖，然后生成证据拼图、音频包络和页面数据。`evidence/manifest.json` 记录每幅拼图的取样时刻。画面标签是请求取样时间，误差受源帧率约束，不是逐帧剪辑表。

来源归属保留在 [provenance.json](cases/backpropagation/sources/provenance.json)。原片、字幕和所引画面仍归其原作者；这些材料作为本地研究证据保存，未将它们声明为新创作资产。

迁入记录见 [migration.json](migration.json)，实测结果见 [独立性检查](PORTABILITY.md)。其中的旧目录名仅表示来源，不参与运行。可执行 `python scripts/verify_library.py` 检查本地链接、媒体路径、来源哈希和时间范围；该检查只用 Python 标准库。
