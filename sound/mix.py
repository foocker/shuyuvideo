"""Mix voice takes and sound cues into stems and a loudness-matched master.

Usage: python sound/mix.py <film-dir>

Inputs: <film>/voice-timings.json (from voice.py, or a shot clock with
"lines": [] and a positive "duration" for a film without voices), <film>/sound-cues.json:
  [{"id": "flip", "time": 9.40, "sfx": "whoosh-short", "gainDb": -24, "on": "台阶翻转"}]
Instead of `time`, a cue may give `"anchor": "<name>"` (and `offset`) from
anchors.resolved.json (sound/anchors.py), so it follows the narration when
lines are re-voiced.
`time` is when the picture event happens; the cue is shifted so its loudest
point lands one frame later. `gainDb` is the cue's peak level before mastering.
Optional <film>/assets/audio/bed.wav is laid under everything at `bedGain`.

Outputs in <film>/assets/audio: narration.wav, sound-effects.wav, final-mix.wav
(48 kHz, -16 LUFS target, accepted range [-17, -15], true peak <= -1.5 dBTP)
and mix-report.json. Failed checks return exit code 1 and do not replace stems.
"""
import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import soundfile as sf
from audio_state import file_hash, input_state

SR = 48000
TARGET_LUFS = -16.0
CEILING_DBTP = -1.5
LOUDNESS_RANGE = (-17.0, -15.0)
FRAME = 1 / 30


def decode(path, channels):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le',
                                   '-ar', str(SR), '-ac', str(channels), 'pipe:1'])
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, channels).copy()


def loudness(path):
    run = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(path), '-af',
                          'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                         capture_output=True, text=True, encoding='utf-8', errors='replace')
    if run.returncode:
        raise RuntimeError(f'FFmpeg loudness measurement failed: {run.stderr[-2000:]}')
    blocks = re.findall(r'\{[^{}]+\}', run.stderr)
    if not blocks:
        raise RuntimeError('FFmpeg returned no loudness measurements')
    stats = json.loads(blocks[-1])
    return {'integratedLufs': float(stats['input_i']), 'truePeakDbtp': float(stats['input_tp']),
            'lra': float(stats['input_lra'])}


def place(track, data, start):
    """Place on the film clock, trimming source samples outside either boundary."""
    offset = round(start * SR)
    source_start = max(0, -offset)
    dest_start = max(0, offset)
    count = min(len(data) - source_start, len(track) - dest_start)
    if count > 0:
        track[dest_start:dest_start + count] += data[source_start:source_start + count]


def validate_loudness(measured):
    failures = []
    for key in ('integratedLufs', 'truePeakDbtp', 'lra'):
        if not math.isfinite(measured[key]):
            failures.append(f'{key} is not finite; check for silence or invalid audio')
    if math.isfinite(measured['integratedLufs']) and not LOUDNESS_RANGE[0] <= measured['integratedLufs'] <= LOUDNESS_RANGE[1]:
        failures.append(f"Integrated loudness {measured['integratedLufs']} LUFS is outside {LOUDNESS_RANGE}")
    if math.isfinite(measured['truePeakDbtp']) and measured['truePeakDbtp'] > CEILING_DBTP:
        failures.append(f"True peak {measured['truePeakDbtp']} dBTP exceeds {CEILING_DBTP}")
    return {'passed': not failures, 'failures': failures,
            'integratedLufsRange': list(LOUDNESS_RANGE), 'maxTruePeakDbtp': CEILING_DBTP}


def write_report(out, report):
    # JSON has no infinity or NaN; silence is reported as null plus a failure.
    def clean(value):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value
    pending = out / 'mix-report.json.tmp'
    pending.write_text(json.dumps(clean(report), ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    pending.replace(out / 'mix-report.json')


def build_mix(film, out, report):
    inputs = input_state(film)
    timings = json.loads((film / 'voice-timings.json').read_text(encoding='utf-8'))
    cues_path = film / 'sound-cues.json'
    cues = json.loads(cues_path.read_text(encoding='utf-8')) if cues_path.exists() else []
    count = round(timings['duration'] * SR)
    if count <= 0:
        raise ValueError('Film duration must be positive')
    voice = np.zeros((count, 2), dtype=np.float32)
    effects = np.zeros((count, 2), dtype=np.float32)

    for line in timings['lines']:
        # TTS takes are peaky; level each take first, as the human-to-sphere film did,
        # so the master can reach -16 LUFS without hitting the peak ceiling.
        raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(film / line['file']), '-af',
                                       'highpass=f=75,loudnorm=I=-18:TP=-3:LRA=7', '-ar', str(SR), '-ac', '1',
                                       '-f', 'f32le', 'pipe:1'])
        take = np.frombuffer(raw, dtype=np.float32).reshape(-1, 1).copy()
        place(voice, np.repeat(take, 2, axis=1), line['start'])

    anchors_path = film / 'anchors.resolved.json'
    anchors = json.loads(anchors_path.read_text(encoding='utf-8')) if anchors_path.exists() else {}
    placed = []
    for cue in cues:
        if 'anchor' in cue:
            cue = {**cue, 'time': anchors[cue['anchor']] + cue.get('offset', 0)}
        data = decode(film / 'assets/sfx' / f"{cue['sfx']}.mp3", 2)
        if not len(data):
            raise ValueError(f"Sound effect {cue['sfx']!r} is empty")
        peak_index = int(np.argmax(np.abs(data).max(axis=1)))
        data *= 10 ** (cue['gainDb'] / 20) / max(float(np.abs(data).max()), 1e-8)
        tail = min(len(data), round(0.08 * SR))
        data[-tail:] *= np.linspace(1, 0, tail)[:, None]
        start = cue['time'] + FRAME - peak_index / SR
        place(effects, data, start)
        placed.append({**cue, 'fileStart': round(start, 3), 'peakAt': round(cue['time'] + FRAME, 3)})

    bed = np.zeros_like(voice)
    bed_path = film / 'assets/audio/bed.wav'
    if bed_path.exists():
        data = decode(bed_path, 2)[:count]
        config_path = film / 'narration.json'
        config = json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}
        place(bed, data * float(config.get('bedGain', 0.14)), 0)

    raw = voice + effects + bed
    if not np.isfinite(raw).all():
        raise ValueError('Mix contains invalid audio samples')
    report.update({'sampleRate': SR, 'duration': timings['duration'], 'lines': len(timings['lines']),
                   'cues': placed, 'bed': bed_path.exists(),
                   'note': 'Measured with ffmpeg loudnorm; not a listening test.'})
    with TemporaryDirectory(prefix='.mix-', dir=out) as temporary:
        staged = Path(temporary)
        sf.write(staged / 'raw.wav', raw, SR, subtype='FLOAT')
        before = loudness(staged / 'raw.wav')
        report['before'] = before
        if not all(math.isfinite(v) for v in before.values()):
            report.update({'measured': before, 'validation': validate_loudness(before)})
            raise ValueError('Mix is silent or its loudness cannot be measured')
        gain_db = min(TARGET_LUFS - before['integratedLufs'], CEILING_DBTP - 0.3 - before['truePeakDbtp'])
        gain = 10 ** (gain_db / 20)
        sf.write(staged / 'narration.wav', voice * gain, SR, subtype='PCM_16')
        sf.write(staged / 'sound-effects.wav', (effects + bed) * gain, SR, subtype='PCM_16')
        sf.write(staged / 'final-mix.wav', raw * gain, SR, subtype='PCM_16')
        after = loudness(staged / 'final-mix.wav')
        validation = validate_loudness(after)
        report.update({'gainDb': round(gain_db, 2), 'measured': after, 'validation': validation})
        if not validation['passed']:
            raise ValueError('; '.join(validation['failures']) + '. Adjust transient peaks or track balance and retry.')
        for name in ('narration.wav', 'sound-effects.wav', 'final-mix.wav'):
            (staged / name).replace(out / name)
    report.update({'status': 'passed', 'outputsPublished': True, 'inputs': inputs,
                   'outputSha256': {name: file_hash(out / name)
                                    for name in ('narration.wav', 'sound-effects.wav', 'final-mix.wav')}})


def main(film):
    out = film / 'assets/audio'
    out.mkdir(parents=True, exist_ok=True)
    report = {'status': 'failed', 'outputsPublished': False}
    try:
        build_mix(film, out, report)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        report['error'] = str(exc)
        write_report(out, report)
        print(f'Mix failed: {exc}\nSee {out / "mix-report.json"}', file=sys.stderr)
        return 1
    write_report(out, report)
    print(json.dumps({'status': report['status'], 'gainDb': report['gainDb'], **report['measured']}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('film', type=Path)
    sys.exit(main(parser.parse_args().film.resolve()))
