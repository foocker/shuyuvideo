"""Package the original and rendered correction as synchronized comparison videos.

Expects output/comparison/staircase-fixed-full.mp4, rendered from the isolated
fixed-film project. Original repository footage is read only.
"""
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from workspace import output_dir, font_path
OUT = output_dir('staircase-test', 'comparison')
ORIGINAL = ROOT / 'films/staircase-sum/renders/staircase-sum.mp4'
FIXED = OUT / 'staircase-fixed-full.mp4'


def run(args):
    subprocess.run(args, check=True)


def banner(name, height, font_size, subtitle):
    image = Image.new('RGBA', (1920, height), (244, 242, 236, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(font_path('sans')), font_size)
    small = ImageFont.truetype(str(font_path('sans')), 24)
    for x, label in [(480, '原始'), (1440, '修正后')]:
        draw.text((x, 8), label, font=font, fill='#203B35', anchor='mt')
        if subtitle:
            draw.text((x, 67), subtitle, font=small, fill='#58675E', anchor='mt')
    image.save(OUT / name)


def compare(name, start, duration, focus=False):
    # Both inputs start at the same exact 30 fps frame. Only one original audio
    # stream is used, so synchronized voices never double in the comparison.
    header = 'focus-header.png' if focus else 'comparison-header.png'
    top = 120 if focus else 80
    height = 1080 if focus else 620
    picture = 'crop=960:960:400:60' if focus else 'scale=960:540:flags=lanczos'
    graph = (
        f'[0:v]setpts=PTS-STARTPTS,{picture},setsar=1[a];'
        f'[1:v]setpts=PTS-STARTPTS,{picture},setsar=1[b];'
        f'[a][b]hstack=inputs=2,pad=1920:{height}:0:{top}:color=0xF4F2EC[base];'
        '[base][2:v]overlay=0:0,drawbox=x=959:y=0:w=2:h=ih:color=0xCDD3CD:t=fill[v]'
    )
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
         '-ss', str(start), '-i', str(ORIGINAL), '-ss', str(start), '-i', str(FIXED),
         '-i', str(OUT / header), '-filter_complex', graph, '-map', '[v]', '-map', '0:a:0',
         '-t', str(duration), '-r', '30', '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '16', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
         '-movflags', '+faststart', str(OUT / name)])


def main():
    assert ORIGINAL.is_file() and FIXED.is_file(), 'Render the corrected full film first'
    OUT.mkdir(parents=True, exist_ok=True)
    banner('comparison-header.png', 80, 36, '')
    banner('focus-header.png', 120, 40, '拼合边界与矩形描边 · 同步局部放大')
    # 8.2..32.4 is exactly 726 frames, avoiding a partial frame at 32.45.
    compare('staircase-side-by-side.mp4', 8.2, 24.2)
    compare('staircase-close-up.mp4', 23.1, 7.8, focus=True)
    for label, source in [('original', ORIGINAL), ('fixed', FIXED)]:
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-ss', '8.2',
             '-i', str(source), '-t', '24.2', '-c:v', 'libx264', '-crf', '16',
             '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart',
             str(OUT / f'staircase-{label}-clip.mp4')])
    manifest_path = OUT / 'comparison-manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    outputs = []
    for name in ['staircase-fixed-full.mp4', 'staircase-side-by-side.mp4',
                 'staircase-close-up.mp4', 'staircase-original-clip.mp4', 'staircase-fixed-clip.mp4']:
        path = OUT / name
        info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
            'format=duration:stream=codec_type,width,height,r_frame_rate', '-of', 'json', str(path)]))
        assert path.stat().st_size > 0
        assert any(s['codec_type'] == 'audio' for s in info['streams']), name
        expected = 52.36 if name.endswith('full.mp4') else 7.8 if name.endswith('close-up.mp4') else 24.2
        assert abs(float(info['format']['duration']) - expected) < 1 / 30 + 0.001, (name, info)
        outputs.append({'file': name, 'bytes': path.stat().st_size, **info})
    manifest.update({'sideBySideRangeSeconds': [8.2, 32.4], 'focusRangeSeconds': [23.1, 30.9],
        'comparisonAudio': 'Single original audio stream; no double mix', 'outputs': outputs})
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'videos': [item['file'] for item in outputs]}))


if __name__ == '__main__':
    main()
