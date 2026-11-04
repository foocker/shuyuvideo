# Freesound 搜索与下载

搜索与下载入口为 `sound/scripts/sfx.py`，仅使用 Python 3 标准库，无需配置 Freesound 账号或 API 密钥。命令示例以 `tools/shuyuvideo` 为工作目录。

```powershell
python sound/scripts/sfx.py freesound "paper slide" --license by -n 5 --urls
python sound/scripts/sfx.py get sound/library fs:<id1> fs:<id2>
```

| 搜索参数 | 作用 |
| --- | --- |
| `--license cc0` | 仅搜索 CC0 |
| `--license by` | 搜索 CC0 和 Attribution |
| `--license any` | 不过滤许可证，默认值；可能包含非商用许可 |
| `--urls` | 显示 MP3 试听链接 |
| `-n 5` | 最多显示 5 条结果，默认 8 条 |
| `--sort relevance` | 获取相关结果后按下载量重新排序，默认方式 |
| `--sort downloads` / `rating` / `short` | 按下载量、评分或时长排序 |
| `--pages 3` | 从起始页抓取的页数，默认 3 页 |
| `-p 2` | 从第 2 页开始搜索，默认第 1 页 |

查询、页码、页数与条数应填写合理值。搜索依赖 Freesound 网页结构；网页变化可能导致没有结果，不能据此断言网站没有对应音效。

## 缓存与来源记录

搜索结果以 UTF-8 保存到用户主目录下的 `.cache/sfx-sources/index.json`。`get` 依赖其中的标题、下载地址、作者和许可证，所以应先搜索，再使用返回的 `fs:ID` 下载。不要把其他机器的个人缓存打包到仓库。

下载命令输出实际文件名；已有同名文件会复用。一次传入多个 ID 可并发下载。任一条目失败时，命令返回非零退出码，应检查失败项后重试。

下载的是 Freesound 的高质量 MP3 预览，不是原始上传文件。需要无损或其他原始格式时，按对应音效页面的下载要求另行获取。

可由缓存中的 `author` 和 ID 找到来源页面：`https://freesound.org/people/<author>/sounds/<id>/`。在作品中保存页面地址、实际许可证、需要的署名以及修改说明。不要将“非 CC0 时打印作者”误当作已经满足全部署名要求；商用时排除 BY-NC，未知许可应先核实。

## 网络排查

脚本使用 Python `urllib`，遵循当前环境中的 `HTTP_PROXY` / `HTTPS_PROXY` 等代理设置。发生超时时，检查 Freesound 是否可访问，以及当前终端的代理设置是否有效，再重试搜索。

此技能不依赖特定代理软件、节点、端口或订阅，也不会修改本机代理配置。
