# 封面输入与输出

作品源码目录放 `cover.json`。最小排版示例：

```json
{
  "schema": "shuyu-cover/v1",
  "title": "数学中的光滑，到底是什么意思？",
  "mode": "compose",
  "size": [1920, 1080],
  "background": "#F4F2EC",
  "image": "assets/cover/background.jpg",
  "fit": "exact",
  "provenance": {
    "kind": "external",
    "source": "图片来源页 URL；详细许可证据见 assets/cover/SOURCE.md",
    "license": "实际许可证或已获得的授权"
  },
  "texts": [{
    "text": "你好光滑",
    "box": [120, 340, 880, 280],
    "font": "sans-bold",
    "fontSize": 200,
    "color": "#183D37"
  }]
}
```

`title` 是完整视频标题，`texts` 才是封面显示文字。`box` 为像素 `[左, 上, 宽, 高]`，定位可见字形的左上角。字体引用 `style/fonts.json`，使用本机覆盖路径和 `faceIndex`。不自动缩字或截断，文字放不下会失败；应先精简钩子或重新排版。

文字支持显式 `\n` 换行、`spacing`（行间像素，默认 12）、`align`（left / center / right）。颜色接受 Pillow 支持的颜色值。底图保留 EXIF 方向，透明部分落在背景色上。`fit: exact` 只允许同长宽比缩放；`cover` 居中裁切，`contain` 居中留边，须明确选择。

`compose` 必须有文字层，图像可省略用于有意设计的纯文字封面。`ready` 必须有已经完成的本地图像，不能再提供文字层。只要引用图片就必须有 `provenance.kind/source/license`；工具检查记录存在，授权判断仍由制作人完成。图片路径必须在作品目录内。

输出：

```text
output/<项目>/
  renders/<视频名>.mp4
  renders/<视频名>-cover.jpg      独立交付图片
  reports/cover-mobile.jpg       从交付 JPG 缩小，人工看图
  reports/cover-check.json       输入/字体/构建器/成品哈希与文字边界
  reports/delivery-video-check.json  为已有视频补封面时的测量
  delivery.json                 绑定 MP4、JPG 的文件名、大小和 SHA256
```

```powershell
.\shuyu.ps1 cover build smooth-structure-long
.\shuyu.ps1 cover check smooth-structure-long
.\shuyu.ps1 deliver smooth-structure-long
.\shuyu.ps1 deliver smooth-structure-long --check
```

`deliver` 不改影片源文件、不重新配音或渲染；它重建封面并调用现有视频测量。完整画面/试听审查沿用 `REVIEW.md`。`--check` 只核对已绑定文件和封面输入，不再次跑响度测量。改视频或封面后应重新 `deliver`。输入图、文字、字体或构建器改变都会使旧封面检查失败。
