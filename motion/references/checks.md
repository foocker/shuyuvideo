# 动作检查的输入与验证范围

从仓库根目录通过 `shuyu.ps1 exec motion/checks/<工具>.py` 运行；依赖统一由 `shuyu.ps1 setup` 安装。SVG 分析使用 fonttools，浏览器探针使用 Pillow 和 Playwright。

浏览器探针默认调用已安装的 Chrome，不自动下载浏览器。没有 Chrome 时可将已有 Chromium 路径传给 `--browser`。失败返回非零退出码；报告的 `ok` 只覆盖所列检查。素材来源与分镜覆盖见公共 [制作验证](../../docs/VALIDATION.md)。

## 对象衔接

[continuity.js](../checks/continuity.js) 提供 `ShuyuMotionChecks.continuity(a, b)`。输入 `{x, y, size}` 使用相同屏幕坐标空间，`size` 为正数。输出 `offsetPx`、`sizeChange`、`ok`；位置差小于 2 像素且大小变化小于 1% 才通过。检查不涉及形状、颜色或数学含义。

作品中的 `assets/lib/transitions.js` 由准备脚本自动包含此检查器，加载后即可调用。旧 `ShuyuTransitions.check(a, b)` 转调同一实现。若直接加载源码，可单独加载检查器；使用旧接口时须同时加载检查器与转场运行时。

## SVG 路径

`shuyu.ps1 exec motion/checks/svg_audit.py <图.svg> [--angle 8] [--strict] [--report <报告.json>]`。

支持标准 SVG 路径命令，包括圆弧与平滑曲线，由 fonttools 展开后分析切线、退化段和大量微小线段。默认只有无法解析的几何使检查失败；切线转角和细碎线段是人工审看提示。`--strict` 将这些提示也作为失败，只适用于预期连续光滑的轮廓。

角度和长度按路径局部坐标计算。外层变换、字体、遮罩、自交拓扑和最终像素不在此工具的正确性范围；没有 path 的文件会明确报告未检查，不能当作通过。不要把有意的矩形拐角判成坏曲线。

## 时间取样与截图

`shuyu.ps1 exec motion/checks/probe_motion.py <配置.json> --out <证据目录> [--browser <浏览器路径>]`。配置中的 HTML 和参考图片相对配置目录，所有资源应在此目录内：

```json
{
  "html": "index.html",
  "timeline": "main",
  "root": "#root",
  "width": 1920,
  "height": 1080,
  "times": [0, 0.5, 1],
  "assertions": [{
    "time": 1,
    "selector": "#curve",
    "source": "attribute",
    "property": "stroke-dashoffset",
    "equals": 0,
    "tolerance": 0.01
  }]
}
```

页面必须已注册 `window.__timelines.main` 暂停 GSAP 时间轴；`times` 使用秒，升序且不重复，不超出时间轴长度。属性断言支持 `attribute` 和 `style`，只比较完整数值，不把矩阵或带单位字符串强行转成进度。运行时错误、找不到元素、外部请求、断言失败或倒序重访像素差异会使任务失败。

输出 `report.json`、逐时刻 PNG 和 `contact-sheet.png`。可选 `reference` 指向同一渲染环境下的静态终态 PNG，与最后取样帧逐像素比较；尺寸不符直接失败，不缩放掩盖误差。没有参考图时报告 `finalComparison: null`，不宣称已验证最终姿态。

该探针用于独立场景；发现 template、子合成或音视频元素时要求改用 HyperFrames 的正式检查。像素变化本身不判断动作是否自然；阶段交接和交叉处应额外加密取样，随后人工查看。
