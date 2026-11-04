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
| 测试依赖 | [requirements-dev.txt](../requirements-dev.txt) |
| Node 依赖及锁 | 根目录 `package.json` / `package-lock.json` |
| 项目、输出根目录、HyperFrames 版本 | [workspace.json](../workspace.json) |
| 字体来源与许可 | [style/fonts.json](../style/fonts.json) |
| 本机字体覆盖 | `workspace.local.json`，不进入 Git |

旧模块的 `requirements.txt` 只转引根文件，没有各自的版本范围。Astra 不再安装 `math/node_modules`。旧 Node 清单保存在 `docs/archive/dependency-manifests/`，仅作来源追溯，不参与安装。

## 按项目工作

```powershell
.\shuyu.ps1 list
.\shuyu.ps1 prepare staircase-test
.\shuyu.ps1 check staircase-test
.\shuyu.ps1 snapshot staircase-test --at 15,19.924
.\shuyu.ps1 render staircase-test
.\shuyu.ps1 preview brand

# prepare 仅生成请求，不调用模型
.\shuyu.ps1 math prepare --project staircase-sum --prompt-file examples/homeomorphism/prompt.txt
.\shuyu.ps1 math resume output/staircase-sum/math/<任务目录>
```

`prepare` 从模块或作品源码构建独立离线项目。编辑源码，再重新准备；不要把 `output/` 中的副本当作唯一源码。新视频进入 `output/<项目>/renders/`，检查报告进入 `reports/`，数学过程和片段进入同一项目的 `math/`。台阶检查页及迁入的旧视频保留原文件名。

声音脚本以作品包为输入；先准备，再在生成包中做配音、音效和混音。直接传入已有作品路径的旧用法仍有效。

```powershell
.\shuyu.ps1 exec sound/voice.py output/<项目>/project
.\shuyu.ps1 exec sound/anchors.py output/<项目>/project
.\shuyu.ps1 exec sound/sfx.py output/<项目>/project
.\shuyu.ps1 exec sound/mix.py output/<项目>/project
```

`anchors.py` 仅在使用 `anchors.json` 时运行。重新准备会复制源码中的同名文件；定稿素材回存作品源码。新增的生成音频不会因重新准备而清空。

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

`doctor` 检查解释器、包、工具、字体和固定版本渲染器；`layout` 检查模块是否重新出现独立输出或依赖目录。`check` 读取 HyperFrames 的 `ok` 字段并扫描屏幕文字，任一失败返回非零状态，两份报告都写入 `reports/`。`render` 渲染后核对 MP4，结果写入 `reports/render-check.json`。`prepare` 会删除构建包中源码已删除或改名的文件，构建包里生成的配音和混音不受影响。测试临时文件也写入 `output/verification/`。

研究原片和版本化 `evidence/` 是资料与证据，不按临时产物迁移。历史影片的 `output/renders` 实体目录已迁入根输出，旧位置只留目录链接，映射见 `workspace.json`。这让原剪辑清单和脚本继续可重建；新工作使用统一入口。
