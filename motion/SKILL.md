---
name: motion
description: 设计数语教学动画的对象动作、镜头运动与场景转场，使用统一运行时并检查路径、衔接和时间定位。用于聚焦局部、场景切换，以及改善僵硬、突跳和接触点漂移。
---

# 数语动作、镜头与转场

从当前作品的理解障碍出发：观众需要看清哪个对象、哪个变化和哪个结果。保留数语配色和现有数学模型。先读 `BRIEF.md` 的模式：讲解片沿用口播时钟；`story-animation` 按 [无讲解剧情动画](../writing/references/story-animation.md) 先设计行动因果和粗动画，再协调真实配音时间。无配音的动作与声音事件不强行绑定某个词。

## 选择能力

| 需求 | 入口 |
| --- | --- |
| 对象动作的准备、运动、接触、停稳与读取时间 | [动作规范](references/principles.md) |
| 公式逐项揭示、分组归并、物体与曲线联动，以及引擎选择 | [动画与公式一起讲解](references/formula-explanation.md)（制作指引，非新增运行时） |
| 推近、拉远、平移、局部聚焦再回到全景 | [镜头 API](references/camera.md)，源码 `runtime/camera.js` |
| 硬切、交叉淡化、对象延续、推入切换 | [转场 API](references/transitions.md)，源码 `runtime/transitions.js` |
| 路径、对象衔接和倒序取样检查 | [动作检查](references/checks.md)，实现位于 `checks/` |

`shuyu.ps1 prepare <项目>` 将运行时打包到作品的 `assets/lib/camera.js`、`assets/lib/transitions.js`。前者提供 `ShuyuCamera`；后者提供 `ShuyuTransitions` 和 `ShuyuMotionChecks`。作品使用包内资源，源码只在本模块维护。

## 设计动作

阅读 [动作规范](references/principles.md)。先明确主动作、接触点和必须保持的数学关系，再决定准备、运动、接触、停稳及读取时间。只选能解决当前问题的动画原则，不固定阶段比例，不强制每个对象弹跳或变形。

- Ω、装饰和相机可以适度夸张；表示长度、面积、角度、连接关系的对象应保持所讲关系。
- 画面由绝对时间和显式输入决定；随机拖动、倒序取帧应得到相同状态。
- 修改口播后先更新语音锚点。镜头取景与场景衔接使用本模块 API；Ω 姿态和动作继续由 [角色模块](../character/README.md) 负责。

## 按问题选择检查

所有命令在 `tools/shuyuvideo` 执行，使用仓库 `.venv`。

能力源码留在本目录；示例统一位于根目录 `examples/`，生成物统一位于 `output/<项目>/`。使用 `shuyu.ps1 prepare/check/render <项目>` 进入同一工作区，不在 skill 目录建立独立输出或安装环境。

| 问题 | 工具与边界 |
| --- | --- |
| SVG 曲线有折角、冗余节点或像素阶梯 | `motion/checks/svg_audit.py` 分析局部路径，给出切线和细碎线段证据；设计中的角点不自动视为错误 |
| 倒拖后姿态变化、缓动似乎未生效、最终图形不一致 | `motion/checks/probe_motion.py` 对独立 HTML 的暂停 GSAP 时间轴采样、倒序重访和截图，支持数值断言与最终图比较 |
| 硬切前后同一对象的位置或大小突跳 | `ShuyuMotionChecks.continuity(a, b)` 比较屏幕位置和大小 |

参数和输入契约见 [检查工具](references/checks.md)。真实台阶镜头的验证入口见 [examples/staircase/README.md](../examples/staircase/README.md)。

素材来源、文件哈希、许可记录及主画面分镜覆盖属于公共 [制作验证](../docs/VALIDATION.md)，通过 `shuyu.ps1 validate assets/timeline` 调用，不在 motion 内维护第二套实现。

完整 HyperFrames 作品继续使用作品固定版本的 `check`、`snapshot` 和现有混音验收。独立 HTML 探针不挂载子合成，不代替 HyperFrames 的媒体同步和整片验证；检测到子合成时会明确失败。

## 交付依据

区分自动检查、目视检查和数学论证。像素变化或路径切线告警只是定位线索，不能据此认定动画不美观或数学错误。最终图比较要求相同尺寸与渲染环境，不缩放参考图掩盖误差。

来源及许可范围见 [SOURCE.md](SOURCE.md)。克拉尼和布帘仅保留候选说明，未导入素材或引擎；需要专题时再按其来源许可接入。
