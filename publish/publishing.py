"""Shared approved-video packets and platform metadata. No network or publish calls."""
import argparse
from datetime import datetime, timezone
import hashlib
from html import escape
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'cover'))
from workspace import inside, output_dir, project_config
import production as cover
from platforms import bilibili

PLATFORMS = {'bilibili': bilibili}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, data):
    cover.write_json(path, data)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def paths(project, platform):
    if platform not in PLATFORMS:
        raise ValueError(f'{platform} 尚未完成发布适配；当前支持 bilibili')
    source = inside(project_config(project)['source'])
    target = output_dir(project, 'publish', platform)
    return {'source': source, 'shared': source / 'publish/video.json',
            'metadata': source / f'publish/{platform}.json', 'output': target,
            'manifest': target / 'packet.json'}


def init(project, platform):
    files = paths(project, platform)
    if files['metadata'].exists():
        raise ValueError(f'发布配置已存在，直接编辑：{files["metadata"]}')
    title_file = files['source'] / 'cover.json'
    title = read(title_file).get('title', project) if title_file.exists() else project
    profile_file = ROOT / 'publish/profiles.local.json'
    account = read(profile_file).get(platform) if profile_file.exists() else None
    if not files['shared'].exists():
        write(files['shared'], {'schema': 'shuyu-publish-video/v1', 'project': project,
                                'approval': None, 'final_action': 'user'})
    write(files['metadata'], PLATFORMS[platform].template(title, account))
    return {'metadata': str(files['metadata']), 'shared': str(files['shared'])}


def approve(project, platform, note):
    """Record an existing explicit user acceptance of these exact delivered assets."""
    files = paths(project, platform)
    if not note.strip():
        raise ValueError('请记录用户确认的依据')
    data = read(files['shared'])
    check_shared(data, project)
    delivery = cover.check_delivery(project)
    data['approval'] = {'video': delivery['video']['sha256'], 'cover': delivery['cover']['sha256'],
                        'note': note, 'recorded_at': datetime.now(timezone.utc).isoformat()}
    write(files['shared'], data)
    return {'shared': str(files['shared']), 'approval': data['approval']}


def check_shared(data, project):
    if (not isinstance(data, dict) or data.get('schema') != 'shuyu-publish-video/v1'
            or data.get('project') != project or data.get('final_action') != 'user'):
        raise ValueError('成片发布配置无效；最终发布须由用户执行')


def inspect(project, platform, now=None):
    files = paths(project, platform)
    data, shared = read(files['metadata']), read(files['shared'])
    check_shared(shared, project)
    report = PLATFORMS[platform].validate(data, now)
    if report['errors']:
        raise ValueError('；'.join(report['errors']))
    delivery = cover.check_delivery(project)
    approval = shared.get('approval')
    if not isinstance(approval, dict) or not approval.get('note'):
        raise ValueError('尚未记录用户对成片的确认；不能准备上传包')
    if any(approval.get(key) != delivery[key]['sha256'] for key in ('video', 'cover')):
        raise ValueError('视频或封面已改变，旧的成片确认失效')
    media = cover.paths(project)
    return files, data, shared, delivery, media, report


def render_html(title, rows, review):
    cards = []
    for index, (label, value) in enumerate(rows):
        cards.append(f'<section><label for="v{index}">{escape(label)}</label>'
                     f'<button data-copy="v{index}">复制</button>'
                     f'<textarea id="v{index}" readonly rows="{min(10, max(1, str(value).count(chr(10)) + 1))}">{escape(str(value))}</textarea></section>')
    pending = ''.join(f'<li>{escape(x)}</li>' for x in review)
    return '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>数语 · 发布资料</title><style>
body{margin:0;background:#f4f2ec;color:#183d37;font:17px/1.65 system-ui,sans-serif}
main{max-width:920px;margin:48px auto;padding:0 24px}h1{font-size:30px;line-height:1.3}
.intro{color:#58675f}.top{display:grid;grid-template-columns:1.2fr 1fr;gap:28px;align-items:start}
img{width:100%;border-radius:12px}a{color:#176454}section{background:#fffefb;padding:20px;margin:16px 0;border-radius:12px}
label{font-weight:650}textarea{display:block;box-sizing:border-box;width:100%;margin-top:12px;padding:12px;border:1px solid #dce2dc;border-radius:7px;resize:vertical;font:inherit;color:inherit;background:#fafbf8}
button{float:right;border:0;background:#e5ede6;color:#183d37;border-radius:6px;padding:7px 18px;cursor:pointer}
@media(max-width:650px){.top{grid-template-columns:1fr}main{margin:24px auto}}
</style><main><p>数语 / B 站投稿资料</p><h1>''' + escape(title) + '''</h1>
<p class="intro">手动上传视频和封面，复制下方资料填写投稿页，检查后发布。</p>
<div class="top"><img src="cover.jpg" alt="本片封面"><div><a href="''' + bilibili.UPLOAD_URL + '''" target="_blank" rel="noopener noreferrer">打开 B 站投稿页 ↗</a>
<p>网页仍需核对</p><ul>''' + pending + '''</ul></div></div>''' + ''.join(cards) + '''
<p role="status" id="status"></p></main><script>
document.querySelectorAll('[data-copy]').forEach(button=>button.addEventListener('click',async()=>{
const field=document.getElementById(button.dataset.copy);field.focus();field.select();
try{if(navigator.clipboard){await navigator.clipboard.writeText(field.value)}else if(!document.execCommand('copy')){throw Error()}
document.getElementById('status').textContent='已复制';}catch{document.getElementById('status').textContent='已选中文字，请按 Ctrl+C 复制';}
}));</script></html>'''


def build(project, platform):
    files, data, shared, delivery, media, report = inspect(project, platform)
    target = files['output']
    target.mkdir(parents=True, exist_ok=True)
    rows = [('视频文件', str(media['movie'])), ('封面文件', str(media['cover'])), *PLATFORMS[platform].fields(data)]
    content = '# B 站发布资料\n\n手动上传视频和封面，复制下方资料填写投稿页，检查后发布。\n\n'
    content += '\n\n'.join(f'## {label}\n\n{value}' for label, value in rows)
    content += '\n\n## 网页待核对\n\n' + '\n'.join('- ' + x for x in report['review']) + '\n'
    generated = {'POST.md': content, 'title.txt': data['title'], 'description.txt': data['description'],
                 'tags.txt': '\n'.join(data['tags']), 'index.html': render_html(data['title'], rows, report['review'])}
    for name, value in generated.items():
        (target / name).write_text(value, encoding='utf-8')
    shutil.copy2(media['cover'], target / 'cover.jpg')
    outputs = {name: digest(target / name) for name in [*generated, 'cover.jpg']}
    packet = {'schema': 'shuyu-publish-packet/v1', 'project': project, 'platform': platform,
              'state': 'local_prepared', 'final_action': 'user',
              'metadata_sha256': digest(files['metadata']), 'approval_sha256': digest(files['shared']),
              'video': {'path': str(media['movie']), 'sha256': delivery['video']['sha256']},
              'cover': {'path': str(media['cover']), 'sha256': delivery['cover']['sha256']},
              'fields': dict(rows[2:]), 'review': report['review'], 'outputs': outputs,
              'upload_url': PLATFORMS[platform].UPLOAD_URL}
    write(files['manifest'], packet)
    return {'packet': str(files['manifest']), 'page': str(target / 'index.html'), **report}


def check(project, platform, ready=False, now=None):
    files, data, shared, delivery, media, report = inspect(project, platform, now)
    packet = read(files['manifest'])
    if (packet.get('schema') != 'shuyu-publish-packet/v1' or packet.get('project') != project
            or packet.get('platform') != platform or packet.get('final_action') != 'user'
            or packet.get('state') != 'local_prepared'):
        raise ValueError('发布包身份或状态不正确，请重新 build')
    for key, path in [('metadata_sha256', files['metadata']), ('approval_sha256', files['shared'])]:
        if packet.get(key) != digest(path):
            raise ValueError('发布资料或成片确认已改变，请重新 build')
    for key in ('video', 'cover'):
        path = media['movie' if key == 'video' else key]
        if packet.get(key) != {'path': str(path), 'sha256': delivery[key]['sha256']}:
            raise ValueError('发布包引用的交付文件已改变，请重新 build')
    if (packet.get('fields') != dict(PLATFORMS[platform].fields(data))
            or packet.get('upload_url') != PLATFORMS[platform].UPLOAD_URL
            or packet.get('review') != report['review']):
        raise ValueError('发布包字段与配置不同，请重新 build')
    expected = {'POST.md', 'title.txt', 'description.txt', 'tags.txt', 'index.html', 'cover.jpg'}
    if not isinstance(packet.get('outputs'), dict) or set(packet['outputs']) != expected:
        raise ValueError('发布包缺少文件记录，请重新 build')
    for name in expected:
        path = files['output'] / name
        if not path.is_file() or digest(path) != packet['outputs'][name]:
            raise ValueError(f'发布包文件缺失或已改变：{name}；请重新 build')
    if ready and report['review']:
        raise ValueError('仍需网页核对：' + '；'.join(report['review']))
    return {'ok': True, 'ready_for_handoff': not report['review'], 'page': str(files['output'] / 'index.html'), **report}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'approve', 'build', 'check', 'assist', 'backend'])
    parser.add_argument('project', nargs='?')
    parser.add_argument('--platform', choices=['bilibili', 'xiaohongshu', 'tencent'], default='bilibili')
    parser.add_argument('--note', default='')
    parser.add_argument('--ready', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.action == 'backend':
            result = read(ROOT / 'publish/backends/social-auto-upload.json')
        else:
            if not args.project:
                parser.error('请提供项目 ID')
            if args.action == 'init':
                result = init(args.project, args.platform)
            elif args.action == 'approve':
                result = approve(args.project, args.platform, args.note)
            elif args.action in ('build', 'assist'):
                result = build(args.project, args.platform)
                if args.action == 'assist':
                    result['next'] = '打开本地 index.html，复制资料；由用户手动上传、填写和发布。'
            else:
                result = check(args.project, args.platform, args.ready)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
