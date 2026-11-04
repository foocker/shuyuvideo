# 源码来源与本地适配

来源：[HarleyCoops/Math-To-Manim](https://github.com/HarleyCoops/Math-To-Manim)，本地 `tools/Math-To-Manim`。

复制提交：`be5e680d64c1f3070e8a34c8510ae94a2600dcc9`。复制日期：2026-10-31。

最初复制范围：`astra/` Python 与 JS 源码、锁定 Node 清单、MIT LICENSE、流程文档、核心离线测试。2026-10-31 按用户要求移除本接入中的 Jev。其余 provider、archive、legacy、旧展示素材、依赖目录和登录凭据均不属于接入包。

上游此前仅作为参考查阅；本次已经复制成本仓库可运行的独立入口。上游模块保留自己的导入名称 `astra`，由本地启动器优先加载本目录，避免误用已安装的另一个源码副本。

局部改动：

1. `astra/client.py` 向桥接脚本传递登录模式；`astra/bridge.mjs` 支持显式 `api` 或 `chatgpt`，原模块未指定时仍为 ChatGPT。数语入口按照用户在本会话的授权默认使用已有 API 登录，密钥仍由 Codex 缓存提供。
2. `astra/render_worker.py` 的高画质改为数语的 1920×1080 / 30fps；低、中画质保持原规格。
3. 新增 `shuyu_astra.py`、`astra.ps1` 和 `shuyu-guidance.md`，提供主题准备、固定风格快照、运行、继续、明确场景修复、无模型重渲染与片段信息导出。
4. 新增数语集成测试；流水线直接保存 Astra 的真实审核结果。审核缺陷不自动触发额外模型重试，数语导出标注 `needs_revision`；源码检查与渲染错误仍按预算修复。
5. `astra/pipeline.py` 恢复任务时将已有试渲染/渲染目录计入尝试编号，避免进程中断后复用相同目录导致失败，旧证据保留。

6. 删除 Jev 客户端、专用设计评估与调查调度、文本证据整理、Jev 文档、依赖声明及 CLI/MCP 开关。旧任务文件中的审核设置仅在读取时忽略，不改写原请求或历史证据。
7. 新任务带入本仓库的作品研究创作指引，保存快照和哈希，便于把研究方法落实到简报和分镜。
8. 2026-11-04 统一工作区：Astra 使用根 `.venv` 和 npm 锁定运行时；默认任务进入 `output/<项目>/math/`。同胚示例移至根 `examples/homeomorphism/`，原 Node 清单移入 `docs/archive/dependency-manifests/` 留作出处，不参与运行。

`source-manifest.json` 记录当前保留文件的上下游哈希，以及已移除文件的上游来源。流程文档已更新为本地实际流程，使用入口以本目录 README 为准。

同胚例子来自真实请求 `runs/astra/20261031-homeomorphism-api`，由请求模型 `gpt-6-astra` 的作者及独立审阅会话产出。复制示例保留深色原设计与数学说明，它是几何和流程案例，不是已完成暖白适配的数语资产。
