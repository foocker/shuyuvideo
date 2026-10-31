# 声音

配音、音效、混音三步，每步一个脚本，都以作品目录为参数。口播稿的写法见 [docs/NARRATION.md](../docs/NARRATION.md)。

```powershell
# 在 tools/shuyuvideo 执行；edge-tts 需 7.3.1 以上（旧版会被服务端拒绝，返回 403）
$env:PYTHONPATH = "..\.deps"     # edge-tts 装在仓库外：python -m pip install --target ..\.deps edge-tts==7.3.1
python sound/voice.py films/<作品>        # 生成配音和 voice-timings.json
python sound/sfx.py   films/<作品>        # 把 sound-cues.json 用到的音效复制进作品
python sound/mix.py   films/<作品>        # 混音、响度统一，写 mix-report.json
```

## 时间从哪里来

`voice.py` 逐句合成，记录每个词的开始和结束时间，再按 `gap`/`pause` 把句子排到全片时间线上，写进 `voice-timings.json`。画面上的关键动作按词的时间来排。例如"倒过来"这个词在 9.4 秒开始，翻转动画就从 9.4 秒开始。

改一句口播只会重新生成这一句，其他句子使用缓存。但后面句子的开始时间会整体移动，所以改稿后要重新核对画面时间。

## 音效

`sound-cues.json` 中每条音效都对应一个画面事件：

```json
[
  {"id": "flip",  "time": 9.40,  "sfx": "whoosh-short", "gainDb": -24, "on": "第二道台阶翻转"},
  {"id": "lock",  "time": 11.20, "sfx": "click-soft",   "gainDb": -22, "on": "两道台阶拼合"}
]
```

- `time` 填画面事件发生的时间。`mix.py` 会把音效最响的位置对齐到这一时刻之后一帧，因为声音比画面早到会显得不对。
- 音效要少而准，每个都要有画面上的原因。可用的对应关系：转场或物体快速移动用 `whoosh-short`，物体落定或拼合用 `click-soft`，数字或公式出现用 `pop`。
- 同一种音效重复出现时，相邻两次换不同的文件，或把增益差开 2–3 dB。
- 不用合成的提示音，避免叮咚声。

音效文件来自 HyperFrames media-use 自带的音效库。该库使用 Pixabay Content License，不允许把文件单独再分发，所以本仓库只保存脚本：`sfx.py` 把文件复制进作品目录，而 `films/` 不进 Git。自己的音效放在 `sound/library/`，同样不进 Git。

## 响度

`mix.py` 输出三条轨道：`narration.wav`、`sound-effects.wav`、`final-mix.wav`。整体响度 -16 LUFS，真峰值不高于 -1.5 dBTP。用 ffmpeg loudnorm 测量，结果写进 `mix-report.json`。这是测量值，没有人耳试听。

背景音乐可选：放在 `assets/audio/bed.wav`，音量由 `narration.json` 的 `bedGain` 控制，默认 0.14。
