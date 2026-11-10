# 安装与统一入口

在 `tools/shuyuvideo` 执行。Windows 使用 `shuyu.ps1`；其他平台使用 `python scripts/shuyu.py`。入口自动选择根目录 `.venv`，不依赖当前激活的 Python。

```powershell
.\shuyu.ps1 setup               # 公共依赖
.\shuyu.ps1 setup --math --dev  # 同一环境增加 Manim/Astra 与测试依赖
.\shuyu.ps1 doctor
.\shuyu.ps1 math doctor
.\shuyu.ps1 layout
```

需要 Python 3.11+、Node.js 22+、FFmpeg/ffprobe、Chrome。`setup` 安装 Python 包及根目录 npm 锁定依赖，不调用模型、不修改登录。

Manim 及其系统依赖（LaTeX、dvisvgm 等）按 [Manim 官方安装说明](https://docs.manim.community/en/stable/installation/uv.html) 准备，版本范围见 [requirements-math.txt](../requirements-math.txt)。本仓库的 Manim 渲染环境放在 `envs/manim/`，是一个 uv 项目，`pyproject.toml` 和 `uv.lock` 纳入版本管理，`.venv` 被忽略：

```powershell
cd envs/manim
uv sync
```

`workspace.json` 的 `manimEnvironment` 指向这个目录，Astra 渲染 Manim 场景时用它的 Python；目录不存在时退回运行 Astra 的解释器。Astra 自身（pydantic 等）仍装在根目录 `.venv`（`setup --math`）。

## 配置归属

| 配置 | 唯一维护位置 |
| --- | --- |
| 公共 Python 版本范围 | [requirements.txt](../requirements.txt) |
| 可选数学依赖 | [requirements-math.txt](../requirements-math.txt)，仍装进同一 `.venv` |
| Astra 的独立 Manim 渲染环境 | `envs/manim/pyproject.toml` / `uv.lock`；用 `uv sync` 安装 |
| 测试依赖 | [requirements-dev.txt](../requirements-dev.txt) |
| Node 依赖及锁 | 根目录 `package.json` / `package-lock.json` |
| 项目、输出根目录、HyperFrames 版本 | [workspace.json](../workspace.json) |
| 字体来源与许可 | [style/fonts.json](../style/fonts.json) |
| 本机字体覆盖 | `workspace.local.json`，不进入 Git |

旧模块的 `requirements.txt` 只转引根文件，没有各自的版本范围。Astra 不再安装 `math/node_modules`。旧 Node 清单保存在 `docs/archive/dependency-manifests/`，仅作来源追溯，不参与安装。

## 按项目工作

新片先选制作模式，生成本地简报和导演稿（随后完成内容与合成源码）：

```powershell
.\shuyu.ps1 start geometry-adventure --mode story-animation --title "几何奇遇"
.\shuyu.ps1 start geometry-explainer --mode explainer --omega on --manim auto
```

`story-animation` 是无讲解模式：默认 `narration: off`、`captions: off`、关闭讲解角色，零人声、零台词，镜头时钟无需 TTS。仅用户明确要求画外音时使用 `--narration voiceover`；该剧情变体的配音字幕需另用 `--captions on` 启用。交互终端省略 `--mode` 时提供模式选择；非交互调用必须指定。旧作品不批量转换；明确切换时修改 BRIEF.md 并同步分镜与合成，详见 [制作选项](PRODUCTION-OPTIONS.md)。

成片确认后使用独立 [发布模块](../publish/SKILL.md)：

```powershell
.\shuyu.ps1 publish init <项目> --platform bilibili
# 编辑 films/<作品>/publish/bilibili.json
.\shuyu.ps1 publish approve <项目> --note "用户已确认当前成片的依据"
.\shuyu.ps1 publish build <项目> --platform bilibili
.\shuyu.ps1 publish check <项目> --platform bilibili
.\shuyu.ps1 publish backend
```

发布包位于 `output/<项目>/publish/bilibili/`，包括可复制的 `index.html`、纯文本及文件摘要。`approve` 只记录真实已有确认；修改视频或封面后会失效。用户打开资料页后手动上传、填写和发布，无需安装上传工具或配置命令行登录。`assist` 保留为生成同一页面的兼容入口。

写稿与改稿使用 [writing 模块](../writing/SKILL.md)。数据工具只用 Python 标准库，参数为作品源码目录：

```powershell
.\shuyu.ps1 writing import films/<作品> --script SCRIPT.writing.md
.\shuyu.ps1 writing export films/<作品> --dry-run
.\shuyu.ps1 writing export films/<作品>
.\shuyu.ps1 writing check films/<作品>
```

新稿格式、配置保留、旧作品迁入与检查边界见 [文件契约](../writing/references/files.md)。已导入作品直接编辑登记稿件，无需重复导入。

每部影片先按 [封面模块](../cover/SKILL.md) 准备 `COVER.md`、`cover.json` 和本地图像。使用已有 Pillow 依赖与字体注册表，无需额外安装。封面只放一个视觉主体与一句短钩子。

```powershell
.\shuyu.ps1 cover build <项目>      # 单独制作封面 JPG 与手机缩略图
.\shuyu.ps1 cover check <项目>      # 检查素材/排版/文件同步
.\shuyu.ps1 deliver <项目>          # 已有视频补封面，测量并生成双文件清单
.\shuyu.ps1 deliver <项目> --check  # 检查本次交付完整且未过期
```

`render` 对影片自动执行封面预检和双文件交付；品牌片头与技术示例保持独立。输出为 `renders/<视频名>.mp4`、`renders/<视频名>-cover.jpg`，绑定清单为 `output/<项目>/delivery.json`。重建不重复生图，素材与配置见 [封面文件契约](../cover/references/files.md)。

```powershell
.\shuyu.ps1 list
.\shuyu.ps1 prepare staircase-test
.\shuyu.ps1 check staircase-test
.\shuyu.ps1 snapshot staircase-test --at 15,19.924
.\shuyu.ps1 render staircase-test
.\shuyu.ps1 preview brand

# math prepare 仅生成请求，不调用模型；resume 会按任务配置继续执行
.\shuyu.ps1 math prepare --project homeomorphism --prompt-file examples/homeomorphism/prompt.txt
.\shuyu.ps1 math resume output/homeomorphism/math/<任务目录>
```

`prepare` 从模块或作品源码构建独立离线项目。`check/snapshot/preview/render` 也会先同步源码，所以同一项目的这些命令须串行执行；不同项目可并行。编辑源码，再重新准备；不要把 `output/` 中的副本当作唯一源码。新视频进入 `output/<项目>/renders/`，检查报告进入 `reports/`，数学过程和片段进入同一项目的 `math/`。

声音脚本以作品包为输入；先准备，再在生成包中做配音、音效和混音。直接传入已有作品路径的旧用法仍有效。

```powershell
.\shuyu.ps1 exec sound/voice.py output/<项目>/project
.\shuyu.ps1 exec sound/anchors.py output/<项目>/project
.\shuyu.ps1 exec sound/sfx.py output/<项目>/project
.\shuyu.ps1 exec sound/mix.py output/<项目>/project
```

`anchors.py` 仅在使用 `anchors.json` 时运行。作品的 `build.py`/`render_math.py` 按该片 README 执行，它们不是公共命令。`shuyu exec` 使用根 `.venv`；需要独立 Manim 环境时在 `envs/manim` 中使用 `uv run python <脚本路径>`。

重新准备会覆盖源码中存在的同名音频。请按 [音频定稿约定](../sound/README.md#避免旧配音覆盖新稿) 保存配音、时钟和混音的完整版本；仅在构建包生成且未登记为源码副本的文件会保留。不要并行执行同步与混音。

## 字体与离线包

统一用 [scripts/font_assets.py](../scripts/font_assets.py) 按“源字体哈希、字符集、构建版本”缓存到 `.cache/fonts/`。字体源和许可只在一个注册表维护。`style/fonts.json` 只记字体文件名，运行时在本机的系统字体目录中查找，仓库里不保存本机路径。字体装在别处时，在本机覆盖文件里写 `path`，可以是相对仓库根目录的路径，示例：

```json
{"fonts":{"sans":{"path":"fonts/NotoSansCJKsc-Regular.otf","faceIndex":0,"license":"OFL-1.1; preserve the accompanying license"}}}
```

将其写入 `workspace.local.json`；粗体对应 `sans-bold`。作品 `assets/fonts/` 是自动生成的离线副本，便于单独移动和渲染，不使用硬链接。KaTeX 字体来自唯一 npm 包。默认 Windows 字体子集仅本机使用，不提交；替换字体时同时保存对应许可。

## 验证与历史兼容

素材与分镜检查统一从根入口调用，输入格式见 [公共验证](VALIDATION.md)：

```powershell
.\shuyu.ps1 validate assets output/staircase-test/asset-manifest.json
.\shuyu.ps1 validate timeline output/staircase-test/timeline.json --assets output/staircase-test/asset-manifest.json
```

```powershell
.\shuyu.ps1 test
.\shuyu.ps1 test --math
.\shuyu.ps1 doctor --audio-only --json
```

`doctor` 检查解释器、包、工具、字体和固定版本渲染器；`layout` 检查输出和依赖目录。`check` 与 `render` 的检查范围见 [验收约定](VALIDATION.md#交付核对)。`prepare` 会删除上次从源码复制、这次已删除或改名的文件；只在构建包中生成的文件会保留。工作区测试与验证报告写入 `output/verification/`。

研究原片和版本化 `evidence/` 是资料与证据，不按临时产物迁移。历史影片的 `output/renders` 实体目录已迁入根输出，旧位置只留目录链接，映射见 `workspace.json`。这让原剪辑清单和脚本继续可重建；新工作使用统一入口。
