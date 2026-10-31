# 同胚：杯子与环面

2026-10-31 使用真实 Astra 链路制作的案例源码。完整边界模型、同胚定义、可逆参数化与球面反例见 [mathematics.md](mathematics.md)；修正版时间安排见 [timeline.md](timeline.md)。

- `scene.py`：修正版 108 秒场景，保留原深色外观；仅作数学模型与实现参考。
- `geometry-verification.json`：核心23秒、346个时间采样的固定网格检查，不包含全局碰撞证明。
- `prompt.txt`：在数语入口使用的主题，可重新按暖白风格生成。
- `evidence/`：从源项目复制的数学、场景与成片审核、抽帧及来源说明。

108 秒参考视频已生成并通过完整解码检查，规格为 854×480、15fps、1620 帧。但最终 Astra 审核**未通过**：逆函数镜头仍显示正向箭头，内底高亮被遮挡，原审核收到的运动证据不足。保留为 `needs_revision` 案例，不能作为已验收教学成片。

- [本机参考视频（待修订）](../../output/homeomorphism/homeomorphism-reference-needs-revision.mp4) · [23 秒形变片段](../../output/homeomorphism/cup-to-torus-23s.mp4)。视频位于忽略的 `output/`，不随源码提交。
- [成片审核](evidence/render-astra-audit.json) · [编码核验](evidence/video-verification.json) · [人工抽帧观察](evidence/visual-review.json)。
- [教学镜头](evidence/lesson-contact-sheet.png) · [形变逐秒抽帧](evidence/core-contact-sheet.png)。后补抽帧不等于连续运动验收，也不覆盖或改写原审核结果。

复制的审核报告内路径相对源运行目录解析；当前视频来源与哈希见 [provenance.json](evidence/provenance.json)。

单独渲染参考代码（在 `tools/shuyuvideo`）：

```powershell
& ..\manimations\.venv\Scripts\python.exe -m manim -ql --media_dir math\output\homeomorphism math\examples\homeomorphism\scene.py AstraFilm
```

该网格包含约1.9万个三角面，Cairo 渲染可能需要较长时间。学习模型和构造可先读数学说明；请勿把已审核的模型直接等同于任意修改后视频的数学或视觉质量。
