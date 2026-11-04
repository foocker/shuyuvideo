# 数语工作区约定

先看 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)；项目配置以 `workspace.json` 为准。

- 在根目录通过 `shuyu.ps1` 或 `python scripts/shuyu.py` 工作；入口自动使用根 `.venv`。
- 能力源码按模块维护；可复用案例放 `examples/`，实际作品源码放 `films/`。
- 动作、镜头和转场统一归入 `motion/`：规范在 `references/`，运行时在 `runtime/`，动作检查在 `checks/`。素材与分镜契约验证归 `scripts/validation/`，使用 `shuyu validate`；作品资源由公共准备脚本生成。
- 新产物放 `output/<项目>/`。渲染用 `renders/`，检查用 `reports/`，数学任务用 `math/`；不要在模块里新建 `output`、`runs` 或依赖环境。
- Node 依赖只改根 `package.json` / `package-lock.json`。Python 版本范围只改根 `requirements*.txt`；旧模块清单只是兼容转引。
- 字体来源与许可用 `style/fonts.json`，本机路径用忽略的 `workspace.local.json`；生成子集用 `scripts/font_assets.py`。作品包中的字体是离线构建副本，不是新的权威来源。
- 新项目的 HyperFrames 版本由注册表选择。历史作品保留已验证版本，升级时单独验证。
- 历史输出目录链接仅用于兼容原影片脚本；新功能使用根输出。不要递归删除这些链接所指向的归档产物。
- 研究原片、来源、许可和版本化证据保留；清理推广链接、联系方式与默认外部品牌文案时不要删掉必要署名和许可。

修改公共构建入口后运行 `shuyu layout`、相关测试及一条真实构建／渲染验证。修改 Astra 时加 `shuyu test --math`；离线验证不要调用模型。
