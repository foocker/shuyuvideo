# 数语工作区约定

先看 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)；项目配置以 `workspace.json` 为准。

## 制作与验收

- 先读本轮要求和作品 `BRIEF.md`，按 [制作选项](docs/PRODUCTION-OPTIONS.md) 落实独立的 `omega: on | off` 与 `manim: auto | selected | off`。已确认的选择直接沿用；未指定时只问一次，同时继续独立工作。用户要求直接做或合理等待后未答复时，说明知识讲解片默认 `omega: on`、`manim: auto`，不反复确认。
- 在简报中记录选择依据和具体镜头。启用 Omega 时必须实际参与正文讲解；选用的 Manim 必须渲染并剪入，不能以片头 Logo 或存在库文件代替。能力受阻时说明原因，不静默省略。用户要求沿用上一部时，继承该片实际选择。
- 先定稿与数学核对，再取真实口播时钟，最后编排画面、角色、字幕和音效。三维几何可沿用验证母版，不为统一工具重做。
- 画面遵循内容简单原则：底部字幕承担完整口播；主画面优先使用图形、变化、公式和必要的短标签。删除仅复述字幕的反问、解释句和章节副标题；定义、对象标识、关键条件及必要对照可保留，不按重复字数机械删字。详见 [文字与画面分工](docs/NARRATION.md#文字与画面分工)。
- 写稿、从文章改编或修改口播时，使用 [writing/](writing/SKILL.md)。先写连贯段落，再分配音单元；正文与制作说明分开。已登记的作品编辑 `.writing.json` 指定稿件，导出并检查同步后再配音；旧脚本会生成 `SCRIPT.md` 时用独立的 `SCRIPT.writing.md`。
- 每部新制作或修改的影片使用 [cover/](cover/SKILL.md)，固定交付 MP4 和独立 JPG。封面默认一个视觉主体、一句短钩子，简洁且手机可读；完整标题不必挤上封面。按各片内容设计，不将单片题材当通用模板。作品保存 `COVER.md`、`cover.json` 与本地素材；已有视频用 `shuyu deliver <项目>` 补封面，不重渲染。历史作品不批量回填。
- [验收约定](docs/VALIDATION.md#交付核对) 包括一般项与省略号、拼合几何、手机可读性、声音输入一致性和最终 MP4 抽帧。自动检查、数学论证和实际视听分别记录。

## 工作区与交付

- 在根目录通过 `shuyu.ps1` 或 `python scripts/shuyu.py` 工作；入口自动使用根 `.venv`。
- 能力源码按模块维护；可复用案例放 `examples/`，实际作品源码放 `films/`。
- 动作、镜头和转场统一归入 `motion/`：规范在 `references/`，运行时在 `runtime/`，动作检查在 `checks/`。素材与分镜契约验证归 `scripts/validation/`，使用 `shuyu validate`；作品资源由公共准备脚本生成。
- 新产物放 `output/<项目>/`。渲染用 `renders/`，检查用 `reports/`，数学任务用 `math/`；不要在模块里新建 `output`、`runs` 或依赖环境。
- 视频与 `<视频名>-cover.jpg` 同放 `renders/`；`delivery.json` 绑定两个交付文件的哈希。交付前运行 `shuyu deliver <项目> --check` 并实际查看封面及手机缩略图。照片/插画生成是素材准备步骤，离线重建封面不重复调用模型。
- 用户指定公开的定稿复制到 `public/videos/`，README 动图放 `public/previews/`；按 `public/README.md` 更新展示副本，源码与构建包继续留在本地。
- Node 依赖只改根 `package.json` / `package-lock.json`。公共 Python 范围维护在根 `requirements*.txt`；另有 `envs/manim/` 的 uv 渲染环境与锁文件，具体选择见 [安装说明](docs/SETUP.md)。不新增模块私有环境。
- 字体来源与许可用 `style/fonts.json`，本机路径用忽略的 `workspace.local.json`；生成子集用 `scripts/font_assets.py`。作品包中的字体是离线构建副本，不是新的权威来源。
- 新项目的 HyperFrames 版本由注册表选择。历史作品保留已验证版本，升级时单独验证。
- 历史输出目录链接仅用于兼容原影片脚本；新功能使用根输出。不要递归删除这些链接所指向的归档产物。
- 同一项目的 `prepare/check/snapshot/preview/render` 会同步构建包，必须串行执行。源码中的同名音频会覆盖包内音频；按 [音频定稿约定](sound/README.md#避免旧配音覆盖新稿) 保存完整版本。不同项目可并行。
- 研究原片、来源、许可和版本化证据保留；清理推广链接、联系方式与默认外部品牌文案时不要删掉必要署名和许可。
- 成片画面、字幕和片尾不显示素材曲名、作者署名、CC BY 等许可证字样、来源网址或第三方工具宣传文案。选材时使用无需署名的素材、原创素材或已获得相应授权的素材；不能满足这一要求的素材应替换或移除，不得只删署名却继续使用。来源和许可证保留在内部素材记录中，不制作成片尾字幕。此规则适用于后续所有新片和修改。

修改公共构建入口后运行 `shuyu layout`、相关测试及一条真实构建／渲染验证。修改 Astra 时加 `shuyu test --math`；离线验证不要调用模型。
