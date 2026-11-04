"""Check a rendered MP4: streams, size, frame rate, audio/video sync and encoded loudness.

Usage: python scripts/validation/render_check.py <video.mp4> [--project <dir>] [--report <report.json>]

With --project, audio is required when the project has assets/audio/final-mix.wav
or an <audio> element, the canvas size comes from the root composition, and a
project mastered by sound/mix.py must keep the encoded loudness in its range.
Measures the file only; lip sync and narration timing still need a viewing.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'sound'))
from mix import loudness, validate_loudness  # noqa: E402

WIDTH, HEIGHT = 1920, 1080
# Container durations differ by up to one AAC frame (~21 ms) plus one video frame.
SYNC_TOLERANCE = 0.08


def probe(path):
    out = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                                   'stream=codec_type,width,height,avg_frame_rate,duration:format=duration',
                                   '-of', 'json', str(path)], encoding='utf-8')
    return json.loads(out)


def expects_audio(project):
    if (project / 'assets/audio/final-mix.wav').is_file():
        return True
    index = project / 'index.html'
    return index.is_file() and '<audio' in index.read_text(encoding='utf-8')


def project_size(project):
    """Canvas size of the root composition, e.g. 1440x1080 for mobius."""
    index = project / 'index.html' if project else None
    if index and index.is_file():
        found = re.search(r'data-composition-id="main"[^>]*?data-width="(\d+)"[^>]*?data-height="(\d+)"',
                          index.read_text(encoding='utf-8'))
        if found:
            return int(found[1]), int(found[2])
    return WIDTH, HEIGHT


def check(video, project=None, size=None):
    size = size or project_size(project)
    errors, data = [], probe(video)
    streams = data.get('streams', [])
    videos = [s for s in streams if s['codec_type'] == 'video']
    audios = [s for s in streams if s['codec_type'] == 'audio']
    summary = {'duration': float(data['format']['duration'])}
    if len(videos) != 1:
        return [f'expected one video stream, found {len(videos)}'], summary
    v = videos[0]
    num, den = (int(x) for x in v['avg_frame_rate'].split('/'))
    summary.update(width=v['width'], height=v['height'], fps=round(num / den, 3) if den else 0,
                   videoDuration=float(v.get('duration', summary['duration'])), audio=bool(audios))
    if (v['width'], v['height']) != tuple(size):
        errors.append(f"resolution {v['width']}x{v['height']}, expected {size[0]}x{size[1]}")
    if project is not None and expects_audio(project) and not audios:
        errors.append('project has a soundtrack but the render has no audio stream')
    if audios:
        a = float(audios[0].get('duration', summary['duration']))
        summary['audioDuration'] = a
        if abs(a - summary['videoDuration']) > SYNC_TOLERANCE:
            errors.append(f"audio {a:.3f}s and video {summary['videoDuration']:.3f}s differ by more than {SYNC_TOLERANCE}s")
        measured = loudness(video)
        summary['loudness'] = measured
        failures = [f'encoded audio: {f}' for f in validate_loudness(measured)['failures']]
        # The delivery range is for masters made by sound/mix.py; stings and
        # inserts are levelled by the film that uses them.
        mastered = project is not None and (project / 'assets/audio/mix-report.json').is_file()
        if mastered:
            errors += failures
        else:
            summary['warnings'] = failures
    return errors, summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path)
    parser.add_argument('--project', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    try:
        errors, summary = check(args.video, args.project)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        errors, summary = [str(exc)], {}
    video = args.video.resolve()
    root = Path(__file__).resolve().parents[2]
    shown = video.relative_to(root).as_posix() if video.is_relative_to(root) else video.name
    report = {'ok': not errors, 'kind': 'render', 'video': shown, 'errors': errors, **summary,
              'scope': 'File measurements only; watch the film for lip sync, timing and picture defects.'}
    content = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(content + '\n', encoding='utf-8')
    print(content)
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
