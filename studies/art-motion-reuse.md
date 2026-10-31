# 从 huashu-art-motion 借鉴什么

比较对象是本仓库保存的 [art-motion 研究资料快照](references/art-motion/README.md)。所引用文档和源码按原内容保存，保留 MIT 许可与来源哈希，阅读不依赖外部目录。这里记录能力关系，不把源码片段当作可运行引擎，也不自动采用其作者的审美偏好。

## 可以保留的生产方法

| 能力 | 本地证据 | 在作品研究中的用法 |
|---|---|---|
| 可追溯拆解 | [01-拆解](references/art-motion/references/01-拆解.md.txt) | 保存时间码、关键状态与局部连续帧；为解释寻找可验证证据 |
| 确定性画面 | [engine.js](references/art-motion/scripts/engine/engine.js.txt) | 同一时间生成同一帧，便于回看、修改和对照 |
| 按节拍或秒数组织场景 | 同文件的 `eighths` / `dur` | 按作品实际主导关系选择时间组织方式 |
| 口播关键词定位 | [tm.js](references/art-motion/scripts/engine/reference_films/spacex/spacex/tm.js.txt) | 将强调动作关联到语义提示点；本实现匹配首次出现的子串，重复词需更明确的定位 |
| 动作与视觉表达工具 | [motion.js](references/art-motion/scripts/engine/lib/motion.js.txt)、[diagram.js](references/art-motion/scripts/engine/lib/diagram.js.txt)、[camera.js](references/art-motion/scripts/engine/lib/camera.js.txt) | 为已明确用途的强调、对应、图形变化和取景提供底层实现 |
| 声画事件对位 | [05-节奏与配乐](references/art-motion/references/05-节奏与配乐.md.txt) | 借鉴共享时间事件和动作音效对位；节拍网格按题材决定 |
| 经验回流 | [12-口播整片与经验回流](references/art-motion/references/12-口播整片与经验回流.md.txt) | 将观察、根因、改法和验证结果归到适当层次 |
| 迁移边界 | [15-跨场景风格提炼](references/art-motion/references/15-跨场景风格提炼.md.txt) | 区分单场景实现、跨场景验证与尚未实现的研究假设 |

## 当前案例补出的需求

现有 [t1 语法卡](references/art-motion/references/动画语法/t1_3b1b.md.txt) 已说明颜色含义、形变、语义运镜和有意静止。其示范是 8 秒、3 个镜头；[参数化片段](references/art-motion/scripts/engine/clips/t1_3b1b.js.txt) 提供标题、公式、要点、曲线和强调。完整反向传播案例还需要处理更长范围内的对象与含义。

| 新作品可能需要 | 当前可借鉴部分 | 还须明确的部分 |
|---|---|---|
| 同一网络跨多段保持身份 | 确定性时间、绘图函数、场景组织 | 节点和连接 ID、数值与视觉状态的共同来源、子图恢复 |
| 图、公式和表格表达同一个量 | 公式 token、图形与高亮能力 | 语义对应关系，避免只按外形匹配 |
| 多路贡献汇总 | 绘图、位移、强调与布局 | 贡献来源、单位、符号、求和或平均等运算类型 |
| 口播与视觉解释协同 | 关键词定位、段落时间 | 动作起点、完成点、结果读取、句间视觉操作的独立时间事件 |
| 全片认识逐步加深 | 场景模块与经验记录 | 当前已知、这一段的新认识、下一段依赖、何时恢复此前省略的复杂度 |
| 配音、音乐、音效的职责划分 | 节奏方法、合成示例、音轨封装 | 声部素材与来源、进入退出、相对电平和语音清晰度的实际审听 |

这些是候选能力需求；没有完成新题材实现前，不宜设计成包揽所有科普片的统一引擎接口。

## 需要按题材重新判断的规则

**所有动作上节拍。** 艺术速通片可以由音乐网格驱动；这部讲解片还要容纳解释条件、对照和读取结果。两者可以共享时间事件机制，段落时长的依据不同。

**每镜都必须写出“谁变成谁”。** 这有助于制止空泛动效，但本片也大量依靠选择性保留、并排对照和稳定图形上的强调。判断标准应是动作承担哪一步解释，而不是每段必须使用形变。

**同屏最多两条要点。** 本片三条影响途径在 05:14 已全部出现，之后长期承担当前讨论位置的提示。应检查文字的用途、可读性和注意焦点，不能仅按数量判断它是否像演示文稿。

**静止与运动比例。** [film_gate.py](references/art-motion/scripts/film_gate.py.txt) 自述快速运动门槛来自作者表态的 13 支片，并明确样本限制。它可提供定位线索；迁移到长篇数学讲解前，需重新选样验证，不能把提高运动占比当成提高理解质量。本轮没有运行它来给原片打分。

**“完整工程”的范围。** [SpaceX 参考代码说明](references/art-motion/scripts/engine/reference_films/spacex/README.md.txt) 明确部分角色、口播等素材不随包提供。[render.py](references/art-motion/scripts/engine/render.py.txt) 将已有音轨封装进视频；[配乐脚本](references/art-motion/scripts/audio/synth_艺术史速通.py.txt) 是具体作品的合成示例。借鉴时应分别确认能力、示例和所需素材。

## 先验证哪一块最有价值

推荐下一次原创试作只验证“同一对象 → 局部因果 → 多项汇总 → 回到整体”中的一个小链条。题材按实际需要选；例如线性组合、合力或概率加权，必须保留各自的数学含义。

先写观众已有认识与希望获得的新认识，再选对象和解释操作；完成短段并正常速度审阅后，记录哪些实现重复出现。对象身份、语义映射或带来源的汇总若多次需要，再收入共享代码。当前第一阶段的研究成果已经可用于这个选择，尚未将试作列为已完成。
