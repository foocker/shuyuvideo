# 场景转场

[transitions.js](../runtime/transitions.js) 提供 `ShuyuTransitions`，将转场加入场景自己的暂停 GSAP 时间轴。从仓库根运行 `shuyu.ps1 prepare <项目>`，将它与 [对象衔接检查器](../checks/continuity.js) 打包为作品的 `assets/lib/transitions.js`，在本地 GSAP 之后加载。既有作品的资源路径和接口保持兼容。

| 接口 | 用途 |
| --- | --- |
| `crossIn(tl, el, dur=0.5, at=0)` | 新场景内容淡入；根合成需让前后场景重叠，且新场景在上层 |
| `fadeOut(tl, el, end, dur=0.4)` | 在 `end - dur` 开始淡出到背景 |
| `pushArrive(tl, el, dur=0.35, at=0)` | 新场景轻微缩放并淡入，配合前一个场景的相机推近 |

```js
const timeline = gsap.timeline({ paused: true });
ShuyuTransitions.crossIn(timeline, sceneContent, 0.5);
ShuyuTransitions.fadeOut(timeline, sceneContent, 8, 0.4);

const continuity = ShuyuMotionChecks.continuity(
  { x: 960, y: 540, size: 300 },
  { x: 960, y: 540, size: 300 }
);
```

硬切由根合成安排；对象延续要求两侧画面使用同一对象位置与大小，不需要额外 tween。`ShuyuMotionChecks.continuity` 的输入、容差与边界见 [对象衔接检查](checks.md#对象衔接)。旧 `ShuyuTransitions.check(a, b)` 保留为同一检查器的兼容入口。

时间参数使用场景内部的秒数，持续时间为正；根合成的场景开始时间另行安排。这些函数不自动调整场景时长、音效或配音。跨场景对象延续可配合 [镜头 API](camera.md) 使用。返回 [motion 入口](../SKILL.md)。
