# 文稿文件与命令

`shuyu writing` 是离线数据工具，不调用模型或语音服务。文稿由当前会话按 [写稿入口](../SKILL.md) 完成。下述路径均从 `tools/shuyuvideo` 根目录解析，参数是作品目录，不是注册表中的项目 ID。

## 新稿

先用自然段写正文，定稿时按 [可执行样例](../../examples/writing/SCRIPT.md) 的格式标出配音单元。配置与正文均以稿件为编辑入口：

````markdown
<!-- shuyu-script/v1 -->

# 标题不进入配音

```shuyu-voice
{"voice":"zh-CN-YunxiNeural","rate":"-3%","gap":0.35}
```

## 段落标题也不进入配音

<!-- shuyu-line {"id":"q1","scene":"opening","pause":0.8} -->
从一加到一百，等于多少？
<!-- /shuyu-line -->
````

每个成对标记内只有要读出的文字，可包含多句或换行；导出保留块内文字，不自动改写、拆句或添加标点。块外只允许空行、一级至三级标题、一个配音配置块及行标记。备注放另一个文件，误放在块外会报错；误写在口播块内的自然语言备注仍需编辑发现，程序不能理解其用途。

`shuyu-voice` 保存原有全部顶层配置，除 `lines`。行标记保存该行除 `text` 外的字段，包含 `id`、可选 `scene`、`pause`、`start` 和项目扩展字段。未知 JSON 配置保留，不主动丢弃。JSON 必须标准有效，不允许重复键、NaN 或 Infinity。

- `id`：稳定且大小写不重复，使用英文字母、数字、下划线或连字符，最长 80 字符；禁用 Windows 设备文件名。它会成为音频文件名。
- `pause`：本句结束到下一句的间隔秒数，**替代**默认 `gap`，不与 `gap` 相加。
- `rate`：可选的本句语速，如 `"+8%"`；覆盖全局 `rate`，不与其相加。未设置时继承全局速度。相邻句子可组成一个加速段，选段与停顿依据另写 `DIRECTION.md`。改速后重新配音并重算实际时钟。
- `pronunciations`：可放在全局配音配置或行标记，如`{"五重":"五崇"}`，以等字数的中文同音字明确TTS读音。正文不改字；字幕与动作锚点使用映射回原文的词时间。仅用于已核对的读音，不做任意语义改写；详见[术语读音](../../docs/NARRATION.md#多音字与术语读音)。
- `start`：旧项目可有绝对起点，会保留。改稿后需要人工重审它；真正的重叠由 `voice.py` 用音频长度检查。
- 口播文字遵守现有 `voice.py` 的字符限制：不含 TeX、反斜杠、斜杠、ASCII 问号、替换乱码符；中文问号可用。Markdown 结构不放进正文。

```powershell
.\shuyu.ps1 writing export films/<作品> --dry-run
.\shuyu.ps1 writing export films/<作品>
.\shuyu.ps1 writing check films/<作品>
```

首次导出要求目标 `narration.json` 不存在或内容相同，避免无来源覆盖旧稿。成功后生成 `.writing.json`，登记稿件名和最后导出的配音输入摘要。摘要不代表作者确认、数学正确或试听通过。

## 迁入已有作品

导入会逐字保留现有 `narration.json` 的文本、行顺序、ID、场景、停顿及全部配置。它不润色内容。

```powershell
.\shuyu.ps1 writing import films/<作品> --script SCRIPT.writing.md --title "作品标题"
# 编辑 SCRIPT.writing.md，导演备注写到 DIRECTION.md
.\shuyu.ps1 writing export films/<作品> --dry-run
.\shuyu.ps1 writing export films/<作品>
.\shuyu.ps1 writing check films/<作品>
```

若项目没有 `SCRIPT.md`，且构建脚本不会写入它，可以省略 `--script`。导入永远不覆盖已有稿件或已登记项目。旧 `build.py` / `clock.py` 可能从音频时钟生成 `SCRIPT.md`，所以旧作品优先采用独立的 `SCRIPT.writing.md`；它成为该作品唯一编辑入口，旧文件仅为展示副本。

已登记的项目直接编辑登记稿件，不重复导入。`.writing.json` 与稿件、`narration.json` 一起保留。若外部程序或人工改过 `narration.json`，导出会拒绝覆盖；对照两份内容，在登记稿件合并需要保留的变化，并使配音文件恢复为上次导出版本或与合并稿一致，再导出。不要删除状态文件来掩盖冲突。

## 自动检查与边界

- `check`：检查稿件格式、`anchors.json` 的行引用及目标词是否仍在正文、稿件与配音文件一致、导出状态一致。
- `export --dry-run`：执行同样的格式和引用校验，显示变更行、删除行及是否需要刷新音频，不写文件。全局配置和行顺序变化也算变更。
- `export`：先检查再原子替换 `narration.json`，登记新摘要；失败不会用半份 JSON 替换旧文件。一次导出中断于更新摘要之前，可重复相同导出恢复。
- 已登记作品的 `prepare/check/snapshot/preview/render` 在构建前检查文稿同步，公共构建完成后再次检查源稿与构建包；配音及混音的输入检查也会检查同步。

自定义构建脚本须将登记稿件、`.writing.json` 和 `narration.json` 一起复制到实际交付的构建目录；公共入口拒绝漏掉这些文件或保留旧版本的构建包。

`anchors.json` 检查只证明目标词存在；实际分词是否能匹配要在配音后由 `sound/anchors.py` 检查。作品私有 `build.py` 的硬编码行 ID、场景清单、词索引和绝对时间不被通用工具推断；拆行、合并、换场景时同步更新这些引用。

同项目的写稿导出与制作串行执行。检查能阻止不同步版本继续生产，不能拦截任意外部编辑器写文件；独立稿名和版本保存用于避免旧脚本覆盖编辑稿。

改稿后仍按 [声音定稿约定](../../sound/README.md#避免旧配音覆盖新稿) 更新配音、真实时钟、字幕、镜头与混音。文稿检查不评价语言质量、数学事实或听感，也不替代新配音生成。
