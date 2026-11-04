# 工作区整理与验证

日期：2026-11-04。

## 已落实

- 公共入口 `shuyu.ps1` / `scripts/shuyu.py`，项目与引擎注册表 `workspace.json`。
- 台阶、同胚案例集中到 `examples/`。motion、math、brand、character 的已有输出迁到根 `output/<项目>/`。
- 历史影片输出迁到 `output/<项目>/archive/`，16 处旧路径保留目录链接。原始视频内容不变；新命令直接使用根输出。
- Python 统一根 `.venv`；Manim/Astra 是可选依赖组。Node 的 GSAP、KaTeX、Three.js、esbuild、Codex SDK/CLI 使用根锁文件。旧依赖清单归档保留出处。
- 三套字体子集逻辑合并为一个生成器与内容缓存；字体源、字重、许可统一配置。独立作品包仍保留可移动的字体副本。
- `AGENTS.md` 和 `shuyu layout` 记录并检查这些约定。

## 验证依据

- 迁移执行后逐项验证 816 个记录中的文件哈希，覆盖 23 项目录迁移；包含父子记录的重复校验。明细位于本地 `output/workspace-migration/`。
- 公共回归 35 项、数学离线回归 32 项通过。根环境 `pip check` 没有依赖冲突。
- 根入口 `doctor` 通过；Astra 能从根环境准备真实主题、冻结风格与研究指引，任务进入对应项目输出，未调用模型。
- 台阶独立场景构建、几何测量与 HyperFrames 检查通过。
- 角色 15 个动作的倒序取样、控件、SVG/PNG 透明导出检查通过，使用根输出中的构建包。
- 品牌构建、关键帧、检查与实际 MP4 渲染通过：1920×1080、30 fps、3 秒、含音轨，文件位于 `output/brand/renders/`。
- Manim 0.22.1 用根 `.venv` 渲染中文与 TeX 静态样张成功；已目视检查。
- 研究库 153 个本地链接、15 个引用快照及两个案例校验通过。

## 边界

本次验证工作区接线和已有样例；没有重新生成所有数学内容或重渲染全部历史长片。历史审核证据保持原结论。Windows 目录链接用于本机旧影片兼容，新环境以根入口和项目注册表为准。旧媒体链接若只在本地有对应作品，远程仓库中仍不可播放。

构建目录是可重建副本；源码是维护入口。公共依赖集中管理不意味着升级所有作品的渲染器，也不意味着移除成片离线运行所必需的字体和脚本副本。

## 动作能力归并（2026-11-04）

- 顶层 `camera/`、`transitions/` 收入 `motion/runtime/`，API 文档收入 `motion/references/`；`motion/SKILL.md` 成为统一入口。
- 动作检查集中在 `motion/checks/`。对象衔接算法单独维护；准备脚本将它随转场打包，既有 `assets/lib/*.js` 路径和 `ShuyuTransitions.check` 继续可用。
- 素材及分镜检查移到 `scripts/validation/validate.py`，通过 `shuyu validate assets/timeline` 调用；输入契约集中在 `docs/VALIDATION.md`。来源与许可记录保留。
- 删除旧 motion 依赖转引清单；工具使用根环境。旧脚本缓存归入根 `.cache/`，旧能力目录已清空移除。
- 归并后公共测试 37 项通过，其中运行时集成测试覆盖 4 组 Node 断言：相机正反向取样、旧检查接口与容差、独立检查器、三类转场的端点与倒序取样。公共验证命令的成功和失败退出状态均已检查。
- `shuyu layout`、skill 结构检查、99 个文档本地链接及 catalog 入口检查通过。台阶真实构建、素材／分镜校验与 HyperFrames 检查通过。
- 台阶 10 个采样帧与归并前逐像素一致，倒序重访也一致；证据在 `output/verification/motion-consolidation/`。此次未重渲染全部历史作品。
