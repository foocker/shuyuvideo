# 迁入数语后的独立性检查

2026-10-31，将本研究目录复制到另一个位置，使用该副本进行检查。

- 原片、73 句字幕、14 个章节、14 个事件、20 张证据拼图与声音分析均位于研究目录内。
- 15 份被引用的 art-motion 文档与源码以文本快照保存，保留来源哈希和 MIT 许可。
- 阅读页在断网 Chromium 中直接打开，原片解码、事件跳转、取样跳转、播放、区间停止和章节导航均通过；页面请求均位于副本内部。
- 桌面与手机截图已检查，手机无横向溢出，JavaScript 错误为零。
- 在副本中实际运行 `build_evidence.py`，重建 20 张拼图、声音包络、18 个字幕间隔候选及页面数据，再次通过来源和链接检查。
- Astra 新任务已实测保存创作指引快照与哈希，32 项离线流程测试通过。

证据：[阅读页检查记录](evidence/reader-portability.json) ·
[独立性检查](evidence/independence.json) ·
[桌面截图](evidence/reader-local-desktop.png) · [手机截图](evidence/reader-local-mobile.png)。

这些检查证明本研究库的文件依赖完整、阅读页可使用、证据可重建，不代表完成了
原片的连续视听分析、方法的跨题材验证或观众理解测试。工具依赖按
[requirements.txt](requirements.txt) 安装，重建另外需要本机 FFmpeg/ffprobe。
