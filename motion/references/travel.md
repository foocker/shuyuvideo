# 连续行走路径

`motion/runtime/travel.js` 在作品准备时复制为 `assets/lib/travel.js`，导出 `ShuyuTravel`。用于角色沿平面路径移动；不负责人物骨骼或避障求解。

用三次贝塞尔段定义 `[x,z]` 路线。相邻段必须共享端点与切线；内部按弧长取样，整条路线只在起点和终点加减速。`pose(t,start,end)` 返回位置、连续展开的朝向、累计距离、速度与距离驱动的步态相位，任意正反寻帧结果一致。

```js
const route = ShuyuTravel.path([
  [[0,2], [1,2], [2,1], [2,0]],
  [[2,0], [2,-.4], [2,-.8], [2,-1.2]]
]);
const motion = route.pose(localTime, 2, 8, {
  startHeading: Math.PI / 2,
  stepLength: .64
});
// actor is a film-owned rig; map these fields to its body and feet.
actor.pose(motion);
```

朝向沿路径切线变化，不要横坐标走完再移动纵坐标。`startHeading` / `endHeading` 可让角色先松手、转向再出发或到达后看向道具；应留出这些窗口。`walk` 由累计路程决定，不能独立使用 `t * 频率`。角色脚底接地和站立期回推仍由骨骼实现。

曲线控制点安全不代表沿途安全。用最终剪辑时钟取样，检查身体、随身物和打开的门扇/门框之间的距离，并查看连续运动片段。缩短全片时优先减少等待和重复，不把人物奔跑压成滑行。

单元验证：`node tests/travel_runtime.cjs`；公共打包验证：`python -m unittest discover -s tests -p test_motion_runtime.py`。
