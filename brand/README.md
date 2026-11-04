# 数语品牌片头

[双版本预览](preview.html) · [3 秒 MP4](../output/brand/shuyu-intro-3s.mp4) · [7 秒 MP4](../output/brand/shuyu-brand-7s.mp4)

沿用数语网站与角色库的 Georgia Ω 字形，暖白底、深绿主体。参考 3Blue1Brown 指定视频开头的形成与定格节奏；画面与声音均未使用参考片素材。

| 版本 | 用途 | 动画 |
| --- | --- | --- |
| 3 秒常用版 | 日常数学视频开头 | Ω 描线填实、睁眼、显出“数语”、轻眨眼，最后 0.75 秒定格 |
| 7 秒文字动画版 | 宣传片、系列首集、品牌介绍 | 保留前 3 秒，Ω 和数语上移，“探索理性与想象的边界”以文字自身的动作展开，最后定格 |

两版均为 1920×1080、30 fps、H.264/AAC。声音为本地原创的短音色，无旁白；结尾 0.3 秒留静音。`../output/brand/` 另有 `-silent.mp4`，用于自行配乐。

## 接在新片前

剪辑软件直接把 3 秒 MP4 放在正片前，再整体移动正片及配音。片头最终画面保持到最后一帧，接入暖白正片时可直接切换。

在 HyperFrames 整片中，把 MP4 复制到作品的 `assets/video/shuyu-intro-3s.mp4`，并在根合成插入：

```html
<video id="brand-intro" class="clip"
  src="assets/video/shuyu-intro-3s.mp4"
  data-start="0" data-duration="3" data-has-audio="true"
  data-track-index="0" data-track-kind="graphics"
  style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain"></video>
```

把正片场景和配音、字幕、音效的根时间统一后移 3 秒，根 `data-duration` 增加 3 秒；各子场景内部局部时间保持原值。已有片头的作品不重复插入。7 秒版同理。需要重新编排品牌动画时，复用 `compositions/intro.html` 与它依赖的本地字体、GSAP，而不是修改视频帧。

## 修改与重建

依赖和字体由根工作区统一管理，见 [安装说明](../docs/SETUP.md)。字体来源在 `style/fonts.json`，本机覆盖写入 `workspace.local.json`。

```powershell
# 在 tools/shuyuvideo 执行
.\shuyu.ps1 exec brand/scripts/build-assets.py
.\shuyu.ps1 check brand
.\shuyu.ps1 preview brand
.\shuyu.ps1 render brand
.\shuyu.ps1 check brand-full
.\shuyu.ps1 render brand-full
```

短版源码为 `index.html`、`compositions/intro.html`；长版延续部分为 `full/continuation.html`、`full/continuation.js`。构建会将短版和延续部分合并到同一时间线，并生成字体、音频和素材清单；不要直接修改长版生成的 `full/compositions/intro.html`。`SPEC.md` 与 `full/SPEC.md` 记录节奏，`REVIEW.md` 记录验证范围。

渲染与预览不依赖网络素材；CLI 通过固定版本 `0.8.223` 运行。成片、抽帧、缓存与本机字体子集不进入 Git。标志轮廓来源记录在 `assets/manifest.json`。

也可用 [HyperFrames desktop app](https://hyperframes.studio/studio/download?os=windows&src=cli) 继续编辑这些工程。
