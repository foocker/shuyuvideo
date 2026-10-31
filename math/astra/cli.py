"""Math-To-Manim command: Astra specialists and independent evidence audits."""
import argparse
import json
from pathlib import Path
import subprocess
from astra import __version__
from astra.client import clean_environment
from astra.models import Request
from astra.pipeline import Pipeline, ROOT
from astra.runtime import setup_runtime, codex_command

def main(argv=None):
    p=argparse.ArgumentParser(prog='math-to-manim',description='Astra films with independent Astra evidence audits.')
    p.add_argument('--version',action='version',version=f'math-to-manim Astra {__version__}')
    commands=p.add_subparsers(dest='command',required=True)
    commands.add_parser('setup',help='Install the pinned Astra Codex runtime')
    commands.add_parser('login',help='Sign in to Codex with ChatGPT')
    run=commands.add_parser('run');run.add_argument('prompt');run.add_argument('-q','--quality',choices=['l','m','h'],default='h')
    run.add_argument('--effort',choices=['high','xhigh','max'],default='high')
    run.add_argument('--max-revisions',type=int,default=6);run.add_argument('--no-render',action='store_true')
    local=commands.add_parser('render-existing',help='Render saved scene code with zero model/API calls')
    local.add_argument('run_dir',type=Path)
    local.add_argument('--candidate',type=Path,required=True,help='Saved candidate JSON or scene Python file')
    local.add_argument('-q','--quality',choices=['l','m','h'],default='m')
    resume=commands.add_parser('resume');resume.add_argument('run_dir',type=Path)
    resume.add_argument('-q','--quality',choices=['l','m','h'],help='Override delivery quality while preserving cached mathematical planning')
    commands.add_parser('doctor')
    commands.add_parser('runs')
    server=commands.add_parser('serve-mcp',help='Serve the Astra SDK MCP connection')
    server.add_argument('--transport',choices=['stdio','streamable-http'],default='stdio')
    server.add_argument('--port',type=int,default=8644)
    args=p.parse_args(argv)
    if args.command=='setup':
        print(f'Codex runtime installed: {setup_runtime()}')
        print('Authenticate with: math-to-manim login')
        return 0
    if args.command=='login':
        return subprocess.run(codex_command('login'),env=clean_environment()).returncode
    if args.command=='serve-mcp':
        from astra.mcp_server import main as serve
        serve(args.transport,args.port)
        return 0
    if args.command=='render-existing':
        from astra.local_render import render_existing
        print(json.dumps(render_existing(args.run_dir,args.candidate,args.quality),indent=2))
        return 0
    if args.command=='doctor':
        try:
            result=subprocess.run(codex_command('login','status'),env=clean_environment())
        except RuntimeError as exc:
            print(str(exc))
            return 1
        for tool in ['ffmpeg','latex']:
            import shutil
            print(f'{tool}: {shutil.which(tool) or "missing"}')
        return result.returncode
    if args.command=='runs':
        for path in sorted((ROOT/'runs/astra').glob('*/manifest.json')):
            data=json.loads(path.read_text(encoding='utf-8'));print(path.parent.name,data['status'])
        return 0
    if args.command=='resume':
        result=Pipeline().run(None,folder=args.run_dir,render_quality=args.quality)
    else:
        result=Pipeline().run(Request(prompt=args.prompt,quality=args.quality,effort=args.effort,
                                      max_revisions=args.max_revisions,render=not args.no_render))
    print(json.dumps(result,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
