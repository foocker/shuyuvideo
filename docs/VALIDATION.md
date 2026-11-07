# 制作验证与交付

公共验证属于作品制作流程，适用于任意引擎。从仓库根目录使用 `shuyu.ps1 validate`；脚本位于 [scripts/validation/validate.py](../scripts/validation/validate.py)，仅依赖 Python 标准库。

失败返回非零退出码；报告的 `ok` 只表示所列结构、记录和文件完整性检查通过，不代表已证明授权或数学结论。动作、镜头与局部取样另见 [motion](../motion/SKILL.md)。方法来源与许可记录保留在 [SOURCE.md](../motion/SOURCE.md)。

## 素材清单

`shuyu.ps1 validate assets <清单.json> [--report <报告.json>]`。清单结构：

```json
{
  "schema": "shuyu-assets/v1",
  "intendedUse": "study",
  "assets": [{
    "id": "diagram",
    "role": "mathematical-diagram",
    "path": "assets/diagram.svg",
    "kind": "project-original",
    "source": "本作品的参数化模型生成",
    "license": "project-internal"
  }]
}
```

`path` 和可选 `licenseFile` 相对清单目录，必须指向目录内的实际文件。`kind` 可为 `project-original`、`user-provided`、`external`；外部来源必须提供 HTTP(S) 来源 URL。可选 `sha256` 是完整的 64 位文件摘要。空素材数组允许用于无需外部文件的场景。

`license` 填具体许可或明确的内部使用依据。`project-internal` 只是项目内部记录，不是向第三方授予的开源许可。来源不明不能用这个值掩盖；`unknown` / `unspecified` 会失败。校验器不访问来源网站，不能独立确认记录是否真实。

CC BY 系列需 `credit`；CC BY-SA 还需 `adaptationLicense` 和 `changes`，例如“未修改”。支持 `CC-BY-NC-4.0` 和 `CC BY-NC 4.0` 两种写法。记录完整也仍需人工核对相同方式共享义务。`intendedUse: commercial` 会拒绝识别到的 CC 非商业许可；工具不替代其他许可证的具体条款审查。外部素材不能用 `project-internal` 占位。

## 分镜覆盖

`shuyu.ps1 validate timeline <分镜.json> [--assets <素材清单.json>] [--report <报告.json>]`：

```json
{
  "schema": "shuyu-timeline/v1",
  "fps": 30,
  "durationFrames": 1800,
  "maxOverlapFrames": 15,
  "shots": [{
    "id": "operation",
    "startFrame": 0,
    "endFrame": 1800,
    "subject": "同一个几何对象",
    "action": "改变条件并比较结果",
    "readFrames": 30,
    "assets": ["diagram"]
  }]
}
```

只列主要画面顺序，不把同时出现的角色、配音和字幕混在同一覆盖检查中。区间为左闭右开，帧号为整数；不限片长，默认不允许重叠，需要转场时显式设置 `maxOverlapFrames`。`readFrames` 记录镜头内预留读取的帧数，不自动添加停顿。存在素材 ID 引用时必须提供 `--assets`，并先验证该清单。


## 屏幕文字与成片

`shuyu.ps1 validate screen <作品目录> [--report <报告.json>]` 静态扫描 `index.html` 和 `compositions/` 中的可见文字与含中文的脚本字符串，脚本位于 [screen_text.py](../scripts/validation/screen_text.py)。`shuyu check` 会自动运行它。`data-tex` 中的 TeX 不按可见文字检查，只要求中文写在 `\text{}` 里。作品尺寸、画幅这类本来就是普通文字的符号，在元素上加 `data-literal-text`，不再报 Unicode 公式符号。

`shuyu render` 渲染后运行 [render_check.py](../scripts/validation/render_check.py)，也可单独执行 `shuyu.ps1 exec scripts/validation/render_check.py <视频.mp4> --project <作品目录>`。它只测量文件，不代替看片。

## 数学画面与一般项

- 固定的 4×5 方块图只能表示具体例子。边长标为 $n$、$n+1$ 时，图中须明确表示省略的中间项：保留首尾标签，例如 $1,2,\ldots,n-1,n$，横向列和长列高度分别使用水平、竖向或斜向省略号。不能只改标签而保留完整的固定格数。
- 画面只显示有限个拼片时，用边缘省略号表示继续延伸，并在 `mathematics.md` 说明为何能推广。原理示例与原作的精确重建要区分。
- 尺寸、平移距离和接触位置来自同一份参数。检查真实网格、共享边或表面，不能靠颜色覆盖、相机缩放掩盖空隙、重叠或穿透。阶梯配对用 $k+(n+1-k)=n+1$ 解释总高。
- KaTeX 标签避免换行与相互贴靠。Manim 的横向省略号按宽度缩放，按点的高度放大会使符号过宽。公式场景交接同时核对对象位置和标签。

这些是数学与画面人工核对要求；静态文字扫描不判断它们是否成立。作品可增加针对自身几何关系的数值检查。

## 交付核对

| 项目 | 通过依据 |
| --- | --- |
| 结构和文字 | `shuyu check <项目>` 成功，HyperFrames 无错误、`reports/screen-text.json` 无问题；运行时生成的字另看抽帧。警告逐项记录判断。 |
| 口播文稿 | 已启用 writing 的作品通过 `shuyu writing check <作品目录>`，登记稿件与配音输入一致；编辑检查另记录衔接、指代、事实条件，实际听感另行试听。格式通过不代表文风通过。 |
| 数学和能力选择 | 画面与 `mathematics.md` 一致；启用 Omega 时有正文出镜帧；选用的 Manim 已实际剪入且颜色、时窗匹配。Astra 使用口播时钟时，导出时长与时钟 `end` 差不超过 0.5 秒。 |
| 声音 | 最新 `mix-report.json` 为 `passed`，文稿、配音缓存和混音输入一致。目标 -16 LUFS，接受 -17 至 -15 LUFS、真峰值不高于 -1.5 dBTP；看音效是否落在真实动作上。 |
| 节奏 | 每片有按信息密度选择语速和停顿的依据；检查少量加速段的前后衔接、真实句间静音及片尾留白，定义、推导和观察动作未被挤压。记录改前／改后时长与实际试听状态，不能以计时通过代替听感。 |
| 画面 | 查看每段中间、关键动作前后与切点；以约 360px 宽检查字幕、省略号和边长。主画面按理解作用删减与字幕重复的反问和解释，保留必要图形、公式、标签与条件。先缩短或拆分字幕再扩大字，不能覆盖数学标签。 |
| 成片 | `shuyu render <项目>` 成功，`reports/render-check.json` 通过尺寸、音轨、音画时长差 ≤0.08 秒及混音作品编码后响度检查；从最终 MP4 解码抽帧，并核对完整时长。 |
| 封面与双文件 | `shuyu cover check <项目>` 和 `shuyu deliver <项目> --check` 成功，MP4 与独立 JPG 均存在且哈希一致。实际查看 JPG 及 `reports/cover-mobile.jpg`，核对主体、短钩子、字形、边缘裁切与手机可读性，记录在 `COVER.md` 或 `REVIEW.md`。 |
| 平台发布资料 | `shuyu publish check <项目> --platform bilibili` 检查成片确认、发布资料、交付文件与定时窗口。交付本地填写页，用户手动上传、核对和发布；`--ready` 是选项确认后的可选检查，不是本地页面交付前提。 |

`films/` 作品默认接 3 秒品牌片头（可 `--no-intro`，见 [brand](../brand/README.md)）。独立 SRT 和章节时间须加上实际片头时长，正文内部时间不改。最终 MP4 的帧不能仅用网页预览截图代替。

`REVIEW.md` 分开记录自动测量、几何论证、画面审查和试听。没有实际听过声音时写明“仅测量，未试听”；响度合格不证明节奏和音色合适。

影片渲染前缺 `cover.json`、缺底图或文字越界会直接失败，避免全片渲染后才发现无法交付封面。输入图、文字、字体、构建器或输出 JPG 改变后，旧封面检查失败；`delivery.json` 还绑定当前视频。已有视频执行 `shuyu deliver <项目>` 会重新构建封面并测量视频，结果保存在 `reports/delivery-video-check.json`，无需重渲染。自动检查不判断图像审美、钩子有效性或素材授权真实性。历史作品不批量重做。

## 缺陷登记与复盘

[accumulation.py](../scripts/validation/accumulation.py) 提供四个子命令，都通过 `shuyu.ps1 validate` 运行：

| 命令 | 作用 |
| --- | --- |
| `validate defects` | 校验 [defects.json](defects.json)：编号不重复，标为 `guarded` 的缺陷写明的检查文件确实存在 |
| `validate retro <retro.json> [--duration 秒]` | 校验一部作品的复盘：方法编号见 `studies/methods.md`，缺陷编号须已登记，时间落在片长内 |
| `validate summary` | 汇总所有 `films/*/retro.json` 与 `examples/*/retro.json`，按方法统计使用次数、作品和效果，列出从未用过的方法 |
| `validate reuse` | 统计 `prepare-film.py` 分发的公共运行库被哪些作品的源码引用；两部独立作品引用才算 `proven` |

复盘中的效果（`worked` / `unclear` / `failed`）是制作者的判断，不是观众测试结果。
