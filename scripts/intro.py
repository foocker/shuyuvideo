"""Put the ShuYu brand intro (3 s v1) in front of a rendered film.

`shuyu render <project>` calls this after HyperFrames renders the body. Films
under films/ get the intro by default; turn it off for one render with
`--no-intro`, or for a project with `"brandIntro": false` in workspace.json.
Other projects (brand, character, examples) can opt in with `"brandIntro": true`.

The intro is re-encoded together with the body, so the result has one set of
stream parameters. An intro of another size is fitted inside the film's canvas
on the warm-white background. The intro itself is rendered with `shuyu render brand`.
"""
import json
from pathlib import Path
import subprocess

from workspace import ROOT, config, output_dir, project_config

BACKGROUND = '0xF4F2EC'


def wanted(project, override=None):
    """override: True (--intro), False (--no-intro) or None (project setting)."""
    if override is not None:
        return override
    record = project_config(project)
    if 'brandIntro' in record:
        return bool(record['brandIntro'])
    settings = config().get('brandIntro', {})
    return settings.get('default', True) and record.get('source', '').startswith('films/')


def intro_file():
    settings = config().get('brandIntro', {})
    project = settings.get('project', 'brand')
    path = output_dir(project, 'renders') / settings.get('video', project_config(project)['video'])
    if not path.is_file():
        raise ValueError(f'Brand intro not rendered: {path.relative_to(ROOT).as_posix()}; run shuyu render {project}')
    return path


def probe(path):
    data = json.loads(subprocess.check_output(
        ['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height,avg_frame_rate:format=duration',
         '-of', 'json', str(path)], encoding='utf-8'))
    video = next(s for s in data['streams'] if s['codec_type'] == 'video')
    num, den = (int(x) for x in video['avg_frame_rate'].split('/'))
    return {'width': video['width'], 'height': video['height'], 'fps': num / den,
            'duration': float(data['format']['duration']),
            'audio': any(s['codec_type'] == 'audio' for s in data['streams'])}


def join(intro, body, destination):
    """Write intro + body to destination; returns the intro duration in seconds."""
    a, b = probe(intro), probe(body)
    w, h, fps = b['width'], b['height'], b['fps']
    video = (f'scale={w}:{h}:force_original_aspect_ratio=decrease,'
             f'pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={BACKGROUND},setsar=1,fps={fps},format=yuv420p')
    inputs, chains = ['-i', str(intro), '-i', str(body)], []
    audio = []
    for index, info in enumerate((a, b)):
        chains.append(f'[{index}:v]{video}[v{index}]')
        if info['audio']:
            chains.append(f'[{index}:a]aformat=sample_rates=48000:channel_layouts=stereo[a{index}]')
        else:
            chains.append(f'anullsrc=r=48000:cl=stereo,atrim=duration={info["duration"]}[a{index}]')
        audio.append(f'[v{index}][a{index}]')
    chains.append(''.join(audio) + 'concat=n=2:v=1:a=1[v][a]')
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', ';'.join(chains),
                    '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16',
                    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(destination)], check=True)
    return a['duration']
