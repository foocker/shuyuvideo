# 镜头运动

[camera.js](../runtime/camera.js) 提供 `ShuyuCamera`，以时间计算 1920×1080 世界图层的位置与缩放。脚本没有外部依赖；从仓库根运行 `shuyu.ps1 prepare <项目>`，会复制到作品的 `assets/lib/camera.js`。

世界图层应绝对定位在 `(0, 0)`，宽高为 1920×1080。相机的 `{x, y}` 表示屏幕中心所对准的世界坐标，`z` 是缩放倍率。

```js
const cameraAt = ShuyuCamera.track(ShuyuCamera.HOME, [
  { at: 2, dur: 1.2, box: [600, 250, 400, 300], pad: 0.15 },
  { at: 5, dur: 1.2, to: ShuyuCamera.HOME }
]);
// 在场景时间轴的更新回调中调用，t 是场景内的绝对时间。
ShuyuCamera.apply(worldElement, cameraAt(t));
```

`box` 为 `[x, y, width, height]`；也可直接使用 `to: {x, y, z}`。关键段按 `at` 升序排列，`dur` 为正数，各运动段不重叠。`ease` 支持 `linear`、`smooth`（默认）、`in`、`out`。

`frame(box, pad)` 计算取景相机；`toScreen` / `toWorld` 转换坐标。对象标注若位于固定屏幕图层，应使用 `toScreen` 跟随主体。不要在同一个世界图层上叠加其他独立的 CSS transform。

镜头只改变观看方式，数学对象的坐标和关系应继续由同一模型决定。接入场景后检查正向播放、倒拖及关键时刻的对象位置。

准备、启动、停稳与读取时间的设计见 [教学动作规范](principles.md)，可重复取样的检查见 [动作检查](checks.md)。返回 [motion 入口](../SKILL.md)。
