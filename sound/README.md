# 声音

配音、音效、混音三步，每步一个脚本，都以作品目录为参数。口播稿的写法见 [docs/NARRATION.md](../docs/NARRATION.md)。

音效选材的技能入口见 [SKILL.md](SKILL.md)：从 Freesound 搜索与下载音效，再接入下述作品流程。

```powershell
# 在 tools/shuyuvideo 执行，先按 docs/SETUP.md 安装依赖
.\shuyu.ps1 doctor --audio-only
.\shuyu.ps1 prepare <项目>
.\shuyu.ps1 exec sound/voice.py output/<项目>/project  # 生成配音和 voice-timings.json
# 按作品 README 重算画面、字幕与音效锚点，再执行下两步
.\shuyu.ps1 exec sound/sfx.py output/<项目>/project    # 复制清单用到的音效
.\shuyu.ps1 exec sound/mix.py output/<项目>/project    # 混音并验收；失败返回非零退出码
```

## 时间从哪里来

`voice.py` 逐句合成，记录每个词的开始和结束时间，再按 `gap`/`pause` 把句子排到全片时间线上，写进 `voice-timings.json`。画面上的关键动作按词的时间来排。例如"倒过来"这个词在 9.4 秒开始，翻转动画就从 9.4 秒开始。

改一句口播只会重新生成这一句，其他句子使用缓存。但后面句子的开始时间会整体移动，所以改稿后要重新核对画面时间。

使用 `anchors.json` 的作品在配音后运行 `sound/anchors.py`，再复制音效、混音。环境安装与统一命令见 [安装说明](../docs/SETUP.md)。

## 避免旧配音覆盖新稿

`shuyu check/snapshot/preview/render` 都会先从源码同步构建包。若源码仍存旧 `assets/voice` 或 `assets/audio`，同名新文件就会被覆盖。按以下顺序定稿：

1. 修改源码中的 `narration.json`，运行 `prepare`，在构建包中生成配音。
2. 作品构建脚本读取新 `voice-timings.json` 编排画面、字幕和音效；若源码已有配音缓存，将当前 `assets/voice/` 与时钟一并回存。先回存再 `prepare`。
3. 生成音效与混音。源码若保留音频，只有报告为 `passed` 时才一起保存三个 WAV 和 `mix-report.json`；项目自有 `--freeze-audio` 之类命令按其 README 执行，不是公共参数。
4. 串行完成检查、抽帧与渲染。不要以文件存在或旧报告通过代替本次验收。

混音前会核对文稿、时钟和 `voice.py` 缓存指纹；成功后记录输入与主音轨的摘要。带新摘要的项目在渲染前和成片检查时会拒绝过期输入、失败报告或被替换的音轨；旧报告仍核对状态、时长与配音缓存，重新混音后获得完整摘要。该检查不识别音频的实际语义，仍需试听。

## 音效

`sound-cues.json` 中每条音效都对应一个画面事件：

```json
[
  {"id": "flip",  "time": 9.40,  "sfx": "whoosh-short", "gainDb": -24, "on": "第二道台阶翻转"},
  {"id": "lock",  "time": 11.20, "sfx": "click-soft",   "gainDb": -22, "on": "两道台阶拼合"}
]
```

- `time` 填画面事件发生的时间。`mix.py` 会把音效最响的位置对齐到这一时刻之后一帧，因为声音比画面早到会显得不对。
- 为对齐峰值而落在片头之前的采样会被裁掉，后面的声音仍保持原定时间；超出片尾的部分同样裁掉。
- 音效要少而准，每个都要有画面上的原因。可用的对应关系：转场或物体快速移动用 `whoosh-short`，物体落定或拼合用 `click-soft`，数字或公式出现用 `pop`。
- 同一种音效重复出现时，相邻两次换不同的文件，或把增益差开 2–3 dB。
- `time` 对应物体真正落定或接触的时刻，不直接拿台词起点代替。优先保留复制、翻转、拼合、结果落定等有意义的声音，避免每个文字显现都配提示声。
- 不用合成的提示音，避免叮咚声。

`sfx.py` 优先读取 `sound/library/` 中的本地音效，再查找 HyperFrames media-use 自带的音效库。后者使用 Pixabay Content License，不允许把文件单独再分发，所以本仓库只保存脚本：音效文件复制进作品目录，而 `films/` 和 `sound/library/` 不进 Git。自行下载的音效按各自许可证使用。

### 搜索和下载新音效

在 `tools/shuyuvideo` 运行；下载脚本仅依赖 Python 3 标准库：

```powershell
python sound/scripts/sfx.py freesound "soft whoosh" --license cc0 --urls
# 把下列 ID 替换为搜索结果中的 fs:ID，可一次下载多个
python sound/scripts/sfx.py get sound/library fs:<id1> fs:<id2>
```

`sound/scripts/sfx.py` 负责搜索与下载，`sound/sfx.py` 负责按作品清单复制音效。下载的是 MP3 预览，文件名类似 `fs_12345_soft-whoosh.mp3`；把不含扩展名的文件名填入 `sound-cues.json` 的 `sfx` 字段，再运行原有复制和混音命令。

搜索结果保存在用户主目录的 `.cache/sfx-sources/index.json`，下载前需先搜索。默认许可筛选为 `any`；需要商用时使用 `cc0` 或 `by`，并在作品中保留来源、许可证及必要署名。完整参数与排查方法见 [Freesound 使用说明](references/freesound.md)。

## 响度

`mix.py` 先在临时目录生成三条轨道：`narration.wav`、`sound-effects.wav`、`final-mix.wav`，再用 FFmpeg loudnorm 测量最终 PCM 文件。目标 -16 LUFS，验收范围 **-17 至 -15 LUFS（含边界）**，真峰值不高于 **-1.5 dBTP**。

通过后才替换正式音轨，退出码为 0，`mix-report.json` 中的 `status` 为 `passed`、`outputsPublished` 为 `true`。静音、无效测量或响度未达标时退出码为 1，报告记录失败原因，不用本次结果覆盖旧音轨。旧文件仍可能存在，交付前必须确认本次报告通过。测量通过不代表已经完成人耳试听。

当前母带处理通过统一增益保持各轨平衡。如果瞬时峰值限制了整体增益，导致响度仍低于 -17 LUFS，程序会拒绝输出；应降低过强的瞬态音效或调整轨道平衡后重试。

背景音乐可选：放在 `assets/audio/bed.wav`，音量由 `narration.json` 的 `bedGain` 控制，默认 0.14。
