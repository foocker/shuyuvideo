"""Start a local film with a production-mode brief, before writing or animation."""
import argparse
import json
import re
import sys

from workspace import ROOT, projects


MODES = {'explainer': '讲解模式', 'story-animation': '无讲解模式（剧情动画）'}
RESERVED = {'con', 'prn', 'aux', 'nul', *(f'com{i}' for i in range(1, 10)),
            *(f'lpt{i}' for i in range(1, 10))}


def start_film(project, mode, *, title=None, omega=None, manim='auto', captions='on'):
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', project) or project in RESERVED:
        raise ValueError('Project ID must use lowercase letters, digits, hyphens or underscores; not a reserved filename')
    if mode not in MODES or manim not in ('auto', 'selected', 'off') or captions not in ('on', 'off'):
        raise ValueError('Invalid production mode, manim or captions choice')
    omega = omega if omega is not None else ('off' if mode == 'story-animation' else 'on')
    if omega not in ('on', 'off'):
        raise ValueError('omega must be on or off')
    if mode == 'story-animation' and omega != 'off':
        raise ValueError('无讲解模式 requires omega: off; story characters may act, but must not present to the audience')
    title = project if title is None else title.strip()
    if not title or '\n' in title or '\r' in title:
        raise ValueError('Title must be a nonempty single line')
    if project in projects():
        raise ValueError(f'Project already registered: {project}; edit its BRIEF.md to change choices')
    film = ROOT / 'films' / project
    if not film.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('Film path escapes repository')

    # Read everything before creating the directory; never replace existing work.
    template = ROOT / 'scripts/templates' / mode
    body = (template / 'BRIEF.md').read_text(encoding='utf-8')
    direction = (template / 'DIRECTION.md').read_text(encoding='utf-8')
    brief = (f'---\nmode: {mode}\nomega: "{omega}"\nmanim: {manim}\n'
             f'narration: voiceover\ncaptions: "{captions}"\n---\n\n# {title}\n\n'
             f'制作模式：{MODES[mode]}。配音保留为画外音；字幕按 captions 选择制作。\n\n' + body)
    film.parent.mkdir(parents=True, exist_ok=True)
    film.mkdir(exist_ok=False)
    (film / 'BRIEF.md').write_text(brief, encoding='utf-8')
    (film / 'DIRECTION.md').write_text(direction, encoding='utf-8')
    (film / 'package.json').write_text(json.dumps(
        {'name': project, 'private': True},
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'project': project, 'source': film.relative_to(ROOT).as_posix(), 'mode': mode,
            'omega': omega, 'manim': manim, 'narration': 'voiceover', 'captions': captions,
            'next': '完善 BRIEF.md 与 DIRECTION.md，完成分镜、配音及 index.html 后再 prepare/check/render；此命令仅创建制作起点。'}


def main(argv=None):
    parser = argparse.ArgumentParser(description='创建本地影片的简报与导演稿，选择讲解或无讲解模式。')
    parser.add_argument('project', help='new film ID, e.g. geometry-adventure')
    parser.add_argument('--mode', choices=MODES, help='explainer = 讲解；story-animation = 无讲解剧情动画')
    parser.add_argument('--title')
    parser.add_argument('--omega', choices=('on', 'off'))
    parser.add_argument('--manim', choices=('auto', 'selected', 'off'), default='auto')
    parser.add_argument('--captions', choices=('on', 'off'), default='on')
    args = parser.parse_args(argv)
    if args.mode is None:
        if not sys.stdin.isatty():
            parser.error('非交互调用请指定 --mode explainer 或 --mode story-animation')
        print('1. 讲解模式：口播驱动，可使用 Omega 讲解员\n'
              '2. 无讲解模式：故事与动作驱动，保留画外配音，可配字幕')
        try:
            choice = input('选择制作模式 [1/2]：').strip()
        except EOFError:
            parser.error('未选择模式；可使用 --mode 指定')
        args.mode = {'1': 'explainer', '2': 'story-animation'}.get(choice, choice)
        if args.mode not in MODES:
            parser.error('请选择 1 或 2，或使用 --mode 指定')
    try:
        result = start_film(args.project, args.mode, title=args.title, omega=args.omega,
                            manim=args.manim, captions=args.captions)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
