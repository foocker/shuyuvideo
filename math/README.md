# Astra 数学与科学讲解片段

已将 Math-To-Manim 的 Astra 源码复制到本目录，使用 `gpt-6-astra`，继续复用 `tools/manimations/.venv`。这是数语的数学/科学片段制作入口：主题 → 教学简报 → 数学依据 → 分镜 → Manim 场景 → 渲染与独立 Astra 审核。

新任务会读取 [数语暖白风格](../style/README.md)，把颜色职责和字体参数随任务冻结。数学、视觉表达、Ω 角色、声音和后期各自保留可独立改进的入口，先从严谨的讲解片段积累。模型审核不是数学证明，`completed` 只表示流水线运行完成。

同时读取本仓库的 [作品研究创作指引](../studies/production-guide.md)，将七种候选表达方法带入简报与分镜，按主题选用，并保存 `expression-guidance.md` 和来源哈希。

## 直接使用

在 `tools/shuyuvideo` 执行：

```powershell
# 环境和本地登录方式检查，不输出密钥
.\math\astra.ps1 doctor

# 仅准备主题、风格快照与请求，不调用模型
.\math\astra.ps1 prepare --prompt-file math\examples\homeomorphism\prompt.txt

# 真正运行 Astra，生成并渲染预览
.\math\astra.ps1 run --prompt-file math\examples\homeomorphism\prompt.txt -q l

# 另一个科学主题
.\math\astra.ps1 run '解释理想单摆的周期：小角近似、单位、能量与近似失效的条件。约90秒。' -q l

# 复用已完成阶段，继续任务
.\math\astra.ps1 resume math\runs\astra\<任务目录>
```

`-q l` 为 854×480 / 15fps 预览，`-q m` 为 1280×720 / 30fps，`-q h` 为 **1920×1080 / 30fps** 数语交付规格。先预览、核验后再提高画质。`prepare` 返回目录后，可直接 `resume` 运行。

沿用本次用户明确允许的现有 API 登录及 Codex provider 配置，默认 `--auth api`；需要 ChatGPT 登录时显式使用 `--auth chatgpt`。入口不复制密钥、不修改全局配置。创作和独立审核均使用 Astra；Jev 代码、依赖声明和开关已移除。

## 初始化与检查

当前机器已初始化。迁移机器后先创建 `tools/manimations/.venv`，安装本目录 Python 依赖、Node.js、FFmpeg/ffprobe 与 LaTeX/dvisvgm，再执行：

```powershell
uv pip install --python ..\manimations\.venv\Scripts\python.exe -r math\requirements.txt
.\math\astra.ps1 setup
.\math\astra.ps1 doctor
```

启动器始终选择相邻的 `manimations` Python，加载本目录的 `astra/`，不依赖相邻 `Math-To-Manim` 源码目录。`setup` 安装本目录锁定的 Codex SDK/CLI 0.156.1。

## 片段怎样进入数语

每次任务位于 `runs/astra/<任务>/`：

| 文件 | 用途 |
| --- | --- |
| `input.txt`、`prompt.txt`、`request.json` | 原始主题、数语要求、实际生成请求 |
| `style-tokens.json`、`shuyu-context.json` | 本次风格与环境快照、交付规格和来源 |
| `expression-guidance.md` | 本次选用表达方法的参考指引快照；哈希记录在任务上下文中 |
| `brief.md`、`mathematics.md` | 观众、定义、假设、推导、来源和模型边界 |
| `storyboard.md` | 镜头、公式、动作时间、口播与角色提示的建议 |
| `scene.py` | 可继续修改与重建的 Manim 源码 |
| `attempts/`、`probes/`、`renders/` | 真实模型过程、审核、试渲染、MP4与抽帧 |
| `shuyu-fragment.json` | 给后续选片与剪辑使用的入口、规格、审核状态和限制 |

`shuyu-fragment.json` 区分 `needs_revision`、`astra_reviewed_preview`、`rendered_not_reviewed` 与 `incomplete`。发现阻断缺陷的片段不会因 MP4 已生成就标为可用。暖白配色已进入创作与审核要求，是否真正匹配风格仍以实际画面为准。

数学命题保存条件、推导和反例；科学内容保存来源、单位、参数、近似与不确定性。把可复查的模型和有趣的表达分开记录，方便以后优化故事、编导和艺术表现，而不破坏数学对象。

[Ω 角色](../character/README.md) 继续使用现有库。分镜可建议思考、看向、指示、讲解等动作，现阶段不自动嵌入角色或制作口型。片段默认静音，声音和整片剪辑后续按统一时间轴组织。

## 修改与复用

审核指出场景缺陷时，把具体修改要求写入 UTF-8 文本：

```powershell
.\math\astra.ps1 resume <任务目录> --feedback-file <修改要求.txt>
```

该命令保留原记录、复用数学和分镜，只重新生成场景。若改变数学对象或前提，应发起新主题，避免沿用不适用的数学说明。

已有场景只需重渲染时：

```powershell
.\math\astra.ps1 render-existing <任务目录> --candidate <场景.py> -q m
```

此路径不调用模型，并标为 `rendered_not_reviewed`。历史审核保留，但不把旧审核当成新视频已通过。

## 当前验证范围

已验证复制后的模块独立加载、锁定 SDK 安装与桥接加载、环境检查、数语主题准备以及 32 项离线测试。真实 Astra API 作者/审核和 Manim 0.22.1 的同胚案例已在源项目运行；[复制的案例](examples/homeomorphism/README.md) 保留源码、数学说明和几何检查，原示例为深色，不能当作数语暖白成片。尚未以新数语提示词重新调用模型生成完整新片，也未完成科学专题评测。

测试（在本目录）：

```powershell
New-Item -ItemType Directory -Force output | Out-Null
& ..\..\..\manimations\.venv\Scripts\python.exe -X utf8 -m pytest --basetemp output\pytest-temp
```

复制来源、上游提交、文件哈希和局部改动见 [SOURCE.md](SOURCE.md) 与 `source-manifest.json`。上游 MIT 许可保存在 [LICENSE](LICENSE)。
