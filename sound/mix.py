"""Mix voice takes and sound cues into stems and a loudness-matched master.

Usage: python sound/mix.py <film-dir>

Inputs: <film>/voice-timings.json (from voice.py), <film>/sound-cues.json:
  [{"id": "flip", "time": 9.40, "sfx": "whoosh-short", "gainDb": -24, "on": "台阶翻转"}]
Instead of `time`, a cue may give `"anchor": "<name>"` (and `offset`) from
anchors.resolved.json (sound/anchors.py), so it follows the narration when
lines are re-voiced.
`time` is when the picture event happens; the cue is shifted so its loudest
point lands one frame later. `gainDb` is the cue's peak level before mastering.
Optional <film>/assets/audio/bed.wav is laid under everything at `bedGain`.

Outputs in <film>/assets/audio: narration.wav, sound-effects.wav, final-mix.wav
(48 kHz, -16 LUFS integrated, true peak <= -1.5 dBTP) and mix-report.json.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000
TARGET_LUFS = -16.0
CEILING_DBTP = -1.5
FRAME = 1 / 30


def decode(path, channels):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le',
                                   '-ar', str(SR), '-ac', str(channels), 'pipe:1'])
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, channels).copy()


def loudness(path):
    run = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(path), '-af',
                          'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                         capture_output=True, text=True, encoding='utf-8', errors='replace')
    stats = json.loads(re.findall(r'\{[^{}]+\}', run.stderr)[-1])
    return {'integratedLufs': float(stats['input_i']), 'truePeakDbtp': float(stats['input_tp']),
            'lra': float(stats['input_lra'])}


def place(track, data, start):
    a = max(0, round(start * SR))
    b = min(len(track), a + len(data))
    if b > a:
        track[a:b] += data[:b - a]


def main(film):
    timings = json.loads((film / 'voice-timings.json').read_text(encoding='utf-8'))
    cues_path = film / 'sound-cues.json'
    cues = json.loads(cues_path.read_text(encoding='utf-8')) if cues_path.exists() else []
    count = round(timings['duration'] * SR)
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
        place(bed, data * float(json.loads((film / 'narration.json').read_text(encoding='utf-8')).get('bedGain', 0.14)), 0)

    out = film / 'assets/audio'
    out.mkdir(parents=True, exist_ok=True)
    raw = voice + effects + bed
    sf.write(out / 'final-mix.wav', raw, SR, subtype='FLOAT')
    before = loudness(out / 'final-mix.wav')
    gain_db = min(TARGET_LUFS - before['integratedLufs'], CEILING_DBTP - 0.3 - before['truePeakDbtp'])
    gain = 10 ** (gain_db / 20)
    sf.write(out / 'narration.wav', voice * gain, SR, subtype='PCM_16')
    sf.write(out / 'sound-effects.wav', (effects + bed) * gain, SR, subtype='PCM_16')
    sf.write(out / 'final-mix.wav', raw * gain, SR, subtype='PCM_16')
    after = loudness(out / 'final-mix.wav')
    report = {'sampleRate': SR, 'duration': timings['duration'], 'lines': len(timings['lines']),
              'cues': placed, 'bed': bed_path.exists(), 'gainDb': round(gain_db, 2),
              'before': before, 'measured': after,
              'note': 'Measured with ffmpeg loudnorm; not a listening test.'}
    (out / 'mix-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'gainDb': report['gainDb'], **after}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(Path(sys.argv[1]).resolve())
