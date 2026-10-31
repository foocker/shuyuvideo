"""Local ShuYu entry point for the copied Astra authoring and rendering chain."""
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
# Prefer the copied code even when math-to-manim is installed from another checkout.
sys.path.insert(0, str(HERE))

from astra.client import CodexSDK, MODEL, clean_environment
from astra.models import Request
from astra.pipeline import Pipeline, save
from astra.render_worker import PROFILES
from astra import runtime


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(topic, *, quality='l', auth='api', output=None):
    if not topic or len(topic.strip()) < 10:
        raise ValueError('请提供至少10个字符的讲解主题、对象或具体要求。')
    tokens_path = PROJECT / 'style/tokens.json'
    tokens = json.loads(tokens_path.read_text(encoding='utf-8'))
    guidance = (HERE / 'shuyu-guidance.md').read_text(encoding='utf-8')
    expression_path = PROJECT / 'studies/production-guide.md'
    expression_guidance = expression_path.read_text(encoding='utf-8')
    folder = (Path(output) if output else HERE / 'runs/astra' /
              (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6])).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    if any(folder.iterdir()):
        raise ValueError('输出目录必须为空；已有任务请使用 resume。')
    width, height, fps = PROFILES[quality]
    context = {
        'model': MODEL, 'auth_mode': auth,
        'style_id': f"{tokens['id']}@{tokens['version']}",
        'style_source': 'style/tokens.json', 'style_sha256': sha(tokens_path),
        'expression_guidance': {
            'source': 'studies/production-guide.md',
            'sha256': sha(expression_path),
            'snapshot': 'expression-guidance.md',
            'evidence': 'studies/methods.md',
        },
        'python': sys.executable, 'manim': version('manim'),
        'delivery': {'width': width, 'height': height, 'fps': fps},
        'pipeline_source': 'math/astra',
        'character_reference': 'character/README.md',
        'authentication_note': 'Explicit API mode uses the existing Codex login/provider; no credential is copied into this run.',
    }
    palette = {key: {'value': value, 'use': tokens['roles'].get(key, {}).get('use', '')}
               for key, value in tokens['colors'].items()}
    prompt = (f'{topic.strip()}\n\n{guidance}\n\n'
              f'本次表达参考（按主题选用）：\n{expression_guidance}\n\n'
              f'完整研究证据位于本仓库：{PROJECT / "studies"}\n'
              f'本次 Python：{sys.executable}\n'
              f'本次交付：{width}×{height}，{fps} fps。未指定时长时采用70–100秒。\n'
              f'数语主题：{context["style_id"]}\n'
              f'中文字体：{tokens["typography"]["sans"]}\n'
              '本次语义颜色（使用具体值，不能假定全局主题覆盖显式颜色）：\n'
              + json.dumps(palette, ensure_ascii=False, indent=2))
    request = Request(prompt=prompt, quality=quality, effort='high',
                      max_revisions=4, render=True)
    (folder / 'input.txt').write_text(topic.strip() + '\n', encoding='utf-8')
    (folder / 'prompt.txt').write_text(prompt, encoding='utf-8')
    (folder / 'expression-guidance.md').write_bytes(expression_path.read_bytes())
    save(folder / 'style-tokens.json', tokens)
    save(folder / 'shuyu-context.json', context)
    save(folder / 'request.json', request.model_dump())
    return folder


def use_auth(folder):
    context = json.loads((folder / 'shuyu-context.json').read_text(encoding='utf-8'))
    mode = context['auth_mode']
    if mode not in ('api', 'chatgpt'):
        raise ValueError('Unsupported saved authentication mode')
    os.environ['SHUYU_ASTRA_LOGIN_METHOD'] = mode


class ShuYuClient(CodexSDK):
    def call(self, prompt, **kwargs):
        note = ('\nWindows: Read UTF-8 explicitly (Get-Content -Raw -Encoding UTF8 or Python -X utf8). '
                'Do not repeatedly reread successful complete file outputs. Return the required structured result.')
        return super().call(prompt + note, **kwargs)


def export_handoff(folder):
    folder = Path(folder).resolve()
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    context = json.loads((folder / 'shuyu-context.json').read_text(encoding='utf-8'))
    video = folder / manifest['video'] if manifest.get('video') else None
    completed = manifest.get('status') == 'completed' and video is not None and video.is_file()
    if completed and sha(video) != manifest.get('video_sha256'):
        raise ValueError('Video hash differs from the pipeline manifest')
    audit_paths = sorted((folder / 'attempts').glob('*-astra-audit.json'))
    audits = {}
    for path in audit_paths:
        stage = path.name.split('-')[1]
        report = json.loads(path.read_text(encoding='utf-8'))
        audits[stage] = {'file': path.relative_to(folder).as_posix(),
                         'verified': report['verified'], 'defects': report['defects']}
    # Local re-render evidence does not inherit approval from a previous movie.
    current_review = manifest.get('review_status') == 'astra_only'
    inspected = current_review and 'render' in audits and audits['render']['verified']
    blocked = any(not a['verified'] or a['defects'] for a in audits.values())
    status = ('needs_revision' if completed and current_review and blocked else
              'astra_reviewed_preview' if completed and inspected else
              'rendered_not_reviewed' if completed else 'incomplete')
    for stage in ('brief', 'mathematics', 'storyboard'):
        path = folder / f'{stage}.json'
        if path.is_file():
            artifact = json.loads(path.read_text(encoding='utf-8'))
            (folder / f'{stage}.md').write_text(
                artifact['summary'] + '\n\n' + artifact['content'] + '\n', encoding='utf-8')
    result = {
        'schema': 'shuyu/astra-fragment-v1', 'status': status,
        'pipeline_status': manifest.get('status'), 'model': MODEL,
        'style': context['style_id'], 'style_sha256': context['style_sha256'],
        'expression_guidance': context.get('expression_guidance'),
        'style_validation': 'requested_in_authoring_and_audits; inspect actual frames',
        'video': manifest.get('video'), 'video_sha256': manifest.get('video_sha256'),
        'contact_sheet': manifest.get('contact_sheet'), 'source': 'scene.py',
        'mathematics': 'mathematics.md', 'storyboard': 'storyboard.md',
        'audits': audits, 'review_status': manifest.get('review_status'),
        'voiceover': {'status': 'not_produced'},
        'character': {'reference': 'character/README.md', 'status': 'not_composited'},
        'notes': ['Astra review is model judgment, not formal proof or a guarantee of scientific correctness.',
                  'A pipeline status of completed alone is not approval for final editing.'],
    }
    if completed:
        probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                                'format=duration:stream=codec_type,width,height,r_frame_rate',
                                '-of', 'json', str(video)], capture_output=True, text=True,
                               encoding='utf-8', check=True)
        result['media'] = json.loads(probe.stdout)
    save(folder / 'shuyu-fragment.json', result)
    return result


def doctor():
    result = {'python': sys.executable, 'astra_source': str(HERE / 'astra'), 'model': MODEL}
    for package in ('manim', 'pydantic'):
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = None
    result['tools'] = {name: shutil.which(name) for name in ('node', 'npm', 'ffmpeg', 'ffprobe', 'latex', 'dvisvgm')}
    try:
        result['codex_runtime'] = str(runtime.runtime_directory())
    except RuntimeError:
        result['codex_runtime'] = None
    # Report credential presence only, never login-status text that can expose a key prefix.
    auth_path = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')) / 'auth.json'
    auth = json.loads(auth_path.read_text(encoding='utf-8')) if auth_path.exists() else {}
    result['cached_auth'] = {'api': bool(auth.get('OPENAI_API_KEY')), 'chatgpt': bool(auth.get('tokens'))}
    result['profiles'] = PROFILES
    result['style'] = str(PROJECT / 'style/tokens.json')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description='数语 Astra 数学/科学片段入口')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('doctor')
    commands.add_parser('setup', help='Install this copied integration’s locked Node runtime')
    for name in ('prepare', 'run'):
        sub = commands.add_parser(name)
        sub.add_argument('prompt', nargs='?')
        sub.add_argument('--prompt-file', type=Path)
        sub.add_argument('-q', '--quality', choices=PROFILES, default='l')
        sub.add_argument('--auth', choices=['api', 'chatgpt'], default='api')
        sub.add_argument('--out', type=Path)
    resume = commands.add_parser('resume')
    resume.add_argument('run_dir', type=Path)
    resume.add_argument('-q', '--quality', choices=PROFILES)
    resume.add_argument('--feedback-file', type=Path, help='Repair the scene using explicit feedback')
    local = commands.add_parser('render-existing')
    local.add_argument('run_dir', type=Path)
    local.add_argument('--candidate', required=True, type=Path)
    local.add_argument('-q', '--quality', choices=PROFILES, default='l')
    handoff = commands.add_parser('export')
    handoff.add_argument('run_dir', type=Path)
    args = parser.parse_args(argv)
    if args.command == 'doctor':
        print(json.dumps(doctor(), ensure_ascii=False, indent=2))
        return 0
    if args.command == 'setup':
        subprocess.run([shutil.which('npm') or 'npm', 'ci', '--no-audit', '--no-fund'],
                       cwd=HERE, env=clean_environment(), check=True, timeout=600)
        print(runtime.runtime_directory())
        return 0
    if args.command in ('prepare', 'run'):
        if bool(args.prompt) == bool(args.prompt_file):
            parser.error('请提供 prompt 或 --prompt-file 中的一项。')
        topic = args.prompt_file.read_text(encoding='utf-8') if args.prompt_file else args.prompt
        folder = prepare(topic, quality=args.quality, auth=args.auth, output=args.out)
        print(folder, flush=True)
        if args.command == 'prepare':
            return 0
    else:
        folder = args.run_dir.resolve()
    if args.command == 'export':
        print(json.dumps(export_handoff(folder), ensure_ascii=False, indent=2))
        return 0
    if args.command == 'render-existing':
        from astra.local_render import render_existing
        render_existing(folder, args.candidate, args.quality)
    else:
        use_auth(folder)
        feedback = ''
        if args.command == 'resume' and args.feedback_file:
            feedback = args.feedback_file.read_text(encoding='utf-8')
            ledger_path = folder / 'manifest.json'
            ledger = json.loads(ledger_path.read_text(encoding='utf-8'))
            if ledger['status'] == 'running':
                raise RuntimeError('任务仍在运行，不能同时修改它的阶段记录。')
            history = folder / 'history'
            history.mkdir(exist_ok=True)
            shutil.copyfile(ledger_path, history / f'manifest-{uuid.uuid4().hex[:8]}.json')
            ledger['stages'].pop('scene', None)
            save(ledger_path, ledger)
        Pipeline(client=ShuYuClient()).run(None, folder=folder, feedback=feedback,
                                         render_quality=args.quality if args.command == 'resume' else None)
    print(json.dumps(export_handoff(folder), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
