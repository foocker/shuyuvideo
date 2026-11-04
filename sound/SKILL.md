---
name: sound
description: 为数语视频从 Freesound 搜索、筛选和下载音效，根据声音来源、时长、下载量、评分与许可证选择素材，并接入 sound-cues.json 和现有混音流程。
---

# 视频音效

本技能负责音效选材与下载。搜索下载脚本仅依赖 Python 3 标准库；音频测量另需 FFmpeg / ffprobe，`mix.py` 还需 `numpy`、`soundfile`，`voice.py` 还需 `edge-tts >= 7.3.1`。配音和混音的用法见 [README.md](README.md)。

以下命令在 `tools/shuyuvideo` 根目录执行；在其他工作目录使用时，按本文件位置解析脚本的绝对路径。

```powershell
# 将画面动作转成英文关键词，搜索并提供试听链接
python sound/scripts/sfx.py freesound "soft whoosh" --license cc0 --urls

# 将搜索返回的 fs:ID 下载到本地音效库；替换示例中的 ID
python sound/scripts/sfx.py get sound/library fs:<id1> fs:<id2>
```

## 选材

- 先判断声音来源、描述和时长是否符合画面，再参考下载量和评分人数；推荐时说明依据。评分人数比平均分更有参考价值，例如 380 人给出的 4.4 分比 6 人给出的 4.9 分更可靠。
- 上传者对录音设备、声源与处理方式的描述能帮助判断质感。描述显示声源不符时，即使下载量高也不选。下载量和描述不能代替试听，不要声称已经听过未经试听的音频。
- CC0 通常不要求署名；BY 需要按许可署名。商用任务排除 BY-NC，可用 `--license cc0` 或 `--license by` 筛选。不要删除音效的必要来源、许可证及署名信息。
- 热门的短促撞击音也可能带有数秒低频尾音。下载后按需要用 FFmpeg / ffprobe 检查实际时长、尾音与能量峰值；需要用户试听时提供 `--urls` 输出的链接。
- 音效对应具体画面事件，少而准。选择与动作相符的真实音效，避免用无关提示音填满时间线。

## 接入作品

1. 下载文件到 `sound/library/`。这是本地素材目录，不进入 Git。当前下载的是 MP3 预览文件，并非原始上传音频。
2. 在作品的 `sound-cues.json` 中，把 `sfx` 设为下载文件名去掉 `.mp3` 后的部分。例如下载输出为 `fs_12345_soft-click.mp3`，就使用 `"sfx": "fs_12345_soft-click"`。若改名，两处应保持一致。
3. 按实际画面填写 `time`、`gainDb` 和 `on`。也可用已有的语音锚点流程，参见 `sound/mix.py` 的输入说明。
4. 在作品中记录选用音效的来源页面、许可证、必要署名和所作修改。搜索缓存保存上传者信息，下载时会提示非 CC0 音效的作者；这些提示不能代替完整的许可记录。
5. 运行现有脚本，把用到的文件复制进作品并混音：

```powershell
python sound/sfx.py films/<作品>
python sound/mix.py films/<作品>
```

混音前需要已有 `voice-timings.json`，由 `sound/voice.py` 生成。混音输出及响度测量见作品的 `assets/audio/mix-report.json`；测量通过不等于已经完成人耳试听。

搜索参数、缓存、来源记录与网络排查见 [references/freesound.md](references/freesound.md)。
