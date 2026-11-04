# 数语 Astra 制作流程

入口为 [astra.ps1](astra.ps1)，转发到根目录 `shuyu.ps1 math`，使用统一 `.venv`。
安装与命令见 [README.md](README.md)。

主题 → 教学简报 → 数学/科学依据 → 分镜 → Manim 场景 → 本地渲染。
每个阶段由独立的 Astra 会话审核；创作与审核均使用 `gpt-6-astra`，
通过 Codex SDK/CLI 0.156.1 调用。数语入口默认使用已授权的 API 登录。
新任务保存数语风格与作品研究创作指引的快照和哈希。

审核记录定义、推导、实际画面、缺陷和限制。输入绑定文件哈希，引用不得
超出给定材料，成片审核必须引用实际图片。模型评分不等于数学证明。

Jev 代码、依赖声明与开关已移除。审核缺陷不自动触发重复生成或额外调查；
数语导出会标记 `needs_revision`，通过 `resume --feedback-file` 明确修复。
源码检查和渲染错误仍在 `max_revisions` 预算内修复。

清单的 `completed` 表示流程完成，`review_status: astra_only` 表示执行了
Astra 审核；最终状态看 `shuyu-fragment.json`。旧请求中的已停用审核配置
可兼容读取，不会重新启用额外服务，也不会改写历史请求和证据。

完整渲染前先生成最终静帧，检查执行与 LaTeX；随后输出 MP4、元数据和抽帧。
静帧不等于连续运动检查，源码筛查不是操作系统沙箱。低清为 854×480 / 15fps，
中清为 1280×720 / 30fps，高画质为 1920×1080 / 30fps。

`resume` 按请求与上游哈希复用阶段；变更画质会重新审核场景和渲染。
`render-existing` 仅渲染保存的代码，不调用模型，标记 `not_reviewed`，
不把旧审核当作新视频已通过的依据。

可选 MCP 入口为 `python -m astra.cli serve-mcp`，需另装 MCP SDK。
它使用同一流水线；数语制作优先用 PowerShell 入口，以应用风格、研究指引与导出约定。
