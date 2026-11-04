# 数语品牌片头

[双版本预览](preview.html) · [3 秒 MP4](../output/brand/shuyu-intro-3s.mp4) · [7 秒 MP4](../output/brand/shuyu-brand-7s.mp4)

沿用数语网站与角色库的 Georgia Ω 字形，暖白底、深绿主体。参考 3Blue1Brown 指定视频开头的形成与定格节奏；画面与声音均未使用参考片素材。

| 版本 | 用途 | 动画 |
| --- | --- | --- |
| 3 秒常用版 | 日常数学视频开头 | Ω 描线填实、睁眼、显出“数语”、轻眨眼，最后 0.75 秒定格 |
| 7 秒文字动画版 | 宣传片、系列首集、品牌介绍 | 保留前 3 秒，Ω 和数语上移，“探索理性与想象的边界”以文字自身的动作展开，最后定格 |

两版均为 1920×1080、30 fps、H.264/AAC。声音为本地原创的短音色，无旁白；结尾 0.3 秒留静音。`../output/brand/` 另有 `-silent.mp4`，用于自行配乐。

## 接在新片前

`shuyu render <作品>` 默认把 3 秒常用版接在 `films/` 下作品的正片前，作品源码和时间线不用改。HyperFrames 先渲染正片到 `<视频名>-body.mp4`，再与片头一起重新编码为交付文件，并对交付文件做渲染检查。

| 需要 | 做法 |
| --- | --- |
| 本次不加片头 | `.\shuyu.ps1 render <作品> --no-intro` |
| 某部作品始终不加 | 在 `workspace.json` 的该项目里写 `"brandIntro": false` |
| `films/` 以外的项目也加 | 该项目写 `"brandIntro": true`，或本次用 `--intro` |
| 换用其他片头 | 改 `workspace.json` 顶层 `brandIntro` 的 `project` 与 `video` |

片头文件取自 `output/brand/renders/shuyu-intro-3s.mp4`，缺失时先 `.\shuyu.ps1 render brand`。已在合成里自带片头的作品要写 `"brandIntro": false`，避免重复。用剪辑软件时，直接把 3 秒 MP4 放在正片前即可；片头最后一帧定格，接暖白正片可直接切换。

## 三连图标

`lib/sanlian.js` 提供点赞、收藏、投币三个原创 SVG 图标（`window.ShuyuSanlian`），颜色取自数语风格，图标内不含文字。`scripts/prepare-film.py` 会把它复制到每部作品的 `assets/lib/sanlian.js`，根合成引入后即可使用：

```js
const icons = ShuyuSanlian.row(svgGroup, { x: 960, y: 470, size: 170 });   // 点赞、收藏、投币一排
ShuyuSanlian.light(tl, icons.like, 1.2);   // 1.2 秒处亮起：描边变色、填满、弹一下、放射短线
ShuyuSanlian.create(svgGroup, 'coin', { x, y, size: 40, on: true });   // 单个、已亮
```

位置写在外层 `<g>` 的 SVG 属性上，GSAP 只动画内层 `.sl-pop`，两者不冲突。用法示例见 `films/what-is-equal/compositions/sanlian.html`。

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
