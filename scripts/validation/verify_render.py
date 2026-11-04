"""Validate a silent film MP4 without depending on old renders or cached snapshots.

Shared by films/<name>/scripts/verify-render.py, which supply the film's
expected size, length and sample times. Requires FFmpeg/ffprobe on PATH and
Pillow. Writes render-verification.json and contact-sheet.jpg to <film>/output.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageStat
import argparse
import hashlib
import io
import json
import subprocess


def verify(root, video, bundle, duration, width, height, fps, times, output=None):
    root = Path(root)
    output = Path(output) if output else root / 'output'
    output.mkdir(parents=True, exist_ok=True)
    probe = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_format', '-show_streams',
        '-of', 'json', str(video),
    ]))
    streams = probe['streams']
    v = next(s for s in streams if s['codec_type'] == 'video')
    assert (int(v['width']), int(v['height'])) == (width, height)
    assert v['r_frame_rate'] == f'{fps}/1'
    assert int(v['nb_frames']) == duration * fps
    assert v['codec_name'] == 'h264' and v['pix_fmt'] == 'yuv420p'
    assert abs(float(probe['format']['duration']) - duration) < .05
    assert not any(s['codec_type'] == 'audio' for s in streams)
    decode = subprocess.run([
        'ffmpeg', '-v', 'error', '-xerror', '-i', str(video), '-f', 'null', '-',
    ], capture_output=True, text=True)
    assert decode.returncode == 0 and not decode.stderr.strip(), decode.stderr

    tile_w = 400
    tile_h = round(tile_w * height / width)
    row_h = tile_h + 26
    sheet = Image.new('RGB', (tile_w * 4, row_h * ((len(times) + 3) // 4)), '#eeeee8')
    draw = ImageDraw.Draw(sheet)
    for i, time in enumerate(times):
        data = subprocess.check_output([
            'ffmpeg', '-v', 'error', '-ss', str(time), '-i', str(video),
            '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'ppm', '-',
        ])
        with Image.open(io.BytesIO(data)) as frame:
            assert frame.size == (width, height)
            assert max(ImageStat.Stat(frame).stddev) > 1, f'Blank frame at {time}s'
            pic = frame.convert('RGB').resize((tile_w, tile_h), Image.Resampling.LANCZOS)
        x, y = (i % 4) * tile_w, (i // 4) * row_h
        sheet.paste(pic, (x, y))
        draw.text((x + 8, y + tile_h + 6), f'{time:g} s', fill='#273f3a')
    sheet.save(output / 'contact-sheet.jpg', quality=94)

    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    report = {
        'video': video.relative_to(root).as_posix() if video.is_relative_to(root) else video.name,
        'duration': float(probe['format']['duration']),
        'width': width, 'height': height, 'fps': fps, 'frames': int(v['nb_frames']),
        'hasAudio': False, 'bytes': video.stat().st_size, 'decodeErrors': [],
        'videoSha256': digest(video), 'bundleSha256': digest(root / 'assets/geometry' / bundle),
        'sampleTimes': times,
        'scope': 'Full decode, encoding specifications and sampled nonblank frames. '
                 'Does not establish visual parity with source or geometry correctness.',
    }
    (output / 'render-verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
    return report


def main(root, *, video, bundle, duration, size, fps, times, doc=__doc__):
    """Command line for one film: optional video path, relative to the film."""
    parser = argparse.ArgumentParser(description=doc)
    parser.add_argument('video', nargs='?', default=video)
    parser.add_argument('--output', type=Path, help='Report folder (default: <film>/output)')
    args = parser.parse_args()
    root = Path(root)
    return verify(root, (root / args.video).resolve(), bundle, duration, *size, fps, times, args.output)
