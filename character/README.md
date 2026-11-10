# 数语角色基础库

每个角色在独立子目录中维护造型、动作数据、运行时、预览和导出脚本。

| 角色 | 内容 | 预览与接入 |
| --- | --- | --- |
| Ω | 品牌符号角色，15 个讲解动作，表情与手势可组合 | [动作预览](omega/study.html) · [接入说明](omega/README.md) |
| 橙色火柴人 | 11 个动作，含跳跃和前后空翻，可编辑关节与透明素材 | [动作预览](stickman/study.html) · [接入说明](stickman/README.md) |
| 墨影 | 《置换之梦》角色，30 个动作，含论文、持枪、倒下与机关互动 | [动作预览](ink/study.html) · [接入说明](ink/README.md) |

```text
character/
  omega/      Ω 角色
  stickman/   橙色火柴人
  ink/        墨影
```

在工作区根目录使用统一命令：

```powershell
.\shuyu.ps1 preview character
.\shuyu.ps1 preview character-stickman
.\shuyu.ps1 preview character-ink
```

Ω 沿用项目 ID `character`、已验证的 HyperFrames 版本与 `output/character/`，其源码位置为 `character/omega/`。火柴人和墨影分别输出到 `output/character-stickman/`、`output/character-ink/`。历史成片与素材版本保留在原输出目录。

影片的公共准备脚本从 `omega/` 拷贝 Ω 运行时及 `stage.js`，成片内仍通过 `assets/lib/omega.js`、`assets/lib/omega-shape.js` 和 `assets/lib/stage.js` 引用。动作编排约定见 [motion](../motion/SKILL.md)。
