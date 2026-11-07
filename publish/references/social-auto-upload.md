# social-auto-upload 适配评估

检查日期：2026-11-07。仓库：[dreammis/social-auto-upload](https://github.com/dreammis/social-auto-upload)。固定检查版本：[3847fff](https://github.com/dreammis/social-auto-upload/tree/3847fff01f5434a8a32829833163cd6723cabc59)，提交于 2026-10-22。许可证 MIT；如果以后复制或修改其源码，保留原版权与许可证。

当前决定：用户已选择保留本地填写页面、手动上传。以下仅为来源评估，不作为后续自动化实施计划；不需要安装该工具或配置命令行账号。

## 与本项目模式的对应

| 平台 | 上游实现 | 当前选择 |
| --- | --- | --- |
| B 站 | `sau bilibili upload-video` 调用 `biliup upload`，支持视频、标题、简介、tid、标签、封面、定时；成功返回表示已提交 | 没有草稿或 prepare-only 参数。当前使用数语本地填写页，由用户手动上传 |
| 小红书 | `sau xiaohongshu upload-video` 支持文案、标签、封面、定时，直接进入发布流程 | 当前未见草稿或 prepare-only 参数；后续接入需先补手动确认模式 |
| 视频号 | `sau tencent upload-video --draft` 将最终按钮改为“保存草稿”，还支持双比例封面、短标题、分类、合集 | 可以复用草稿能力；先完成视频号字段与封面适配、结果核验后再接入，不在本次冒充已支持 |

证据文件：[`sau_commands/bilibili.py`](https://github.com/dreammis/social-auto-upload/blob/3847fff01f5434a8a32829833163cd6723cabc59/sau_commands/bilibili.py)、[`xiaohongshu.py`](https://github.com/dreammis/social-auto-upload/blob/3847fff01f5434a8a32829833163cd6723cabc59/sau_commands/xiaohongshu.py)、[`tencent.py`](https://github.com/dreammis/social-auto-upload/blob/3847fff01f5434a8a32829833163cd6723cabc59/sau_commands/tencent.py)、[`uploader/tencent_uploader/main.py`](https://github.com/dreammis/social-auto-upload/blob/3847fff01f5434a8a32829833163cd6723cabc59/uploader/tencent_uploader/main.py)。

B 站 CLI 没有公开创作声明、合集、商业推广、互动管理等参数；不能把缺少的字段静默丢弃后直接提交。它的 `check` 会调用 `biliup renew`，不是纯本地检查；`login` 需要本机交互终端。第一次调用还可能自动下载或更新 biliup。

## 复用边界

数语负责：确认哪版视频可发布、封面绑定、平台文案、选项记录、上传前检查和用户最终确认。上游可负责：后续兼容模式中的登录、上传与保存草稿。不复制整套账号管理和浏览器代码。

本轮仅将源码下载到忽略的 `.cache/integrations/social-auto-upload` 并阅读，没有安装其 Python/浏览器依赖，没有登录或执行上传。`publish backend` 返回固定版本的评估结果，不能当成已安装、已连接账号或可直接发布。

升级后重新检查实际 CLI 参数和提交路径，再改变能力记录。若未来采用视频号草稿模式，参数始终显式保留 `--draft`，保存后按标题、账号和稿件标识核对；不要只凭返回码推断草稿完整。B 站在当前用户模式下不生成可误执行的自动投稿脚本。
