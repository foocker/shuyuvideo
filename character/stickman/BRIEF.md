# 火柴人基础动作资产

- mode: story-animation
- omega: off
- manim: off（二维角色动作，无数学渲染需求）
- narration: off
- captions: off
- audio: silent（供后续影片复用的动作资产与技术展示，沿用角色库的静音约定）
- 1920×1080，30 fps，48 秒动作目录。

用户指定先复刻 `downloads/Alan_Becker/Animation_vs._Geometry.mp4` 中橙色火柴人的基本动作，新增角色到 `character/`。本次做可编辑的骨架与关键帧，不迁移或替换 Omega，也不接入现有影片。

第一批：观察、走、跑、蹲下拾取、蹲姿按压、低姿拖拽、双手悬挂、坐起站立。用户确认后补跳跃、前空翻、后空翻，扩充至 11 个。来源、归一化与补画范围见 SOURCES.md 和 motions.json。v1 的 8 动作视频、源码和素材包保存在 renders/versions/v01-basic-actions/。
