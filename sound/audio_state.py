"""Check narration caches and bind an accepted mix to its actual local inputs."""
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'writing'))
from manuscript import check_if_managed
from voice_config import voice_fingerprint


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def file_hash(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_voice(film, timings):
    check_if_managed(film)
    config = read_json(film / 'narration.json') if (film / 'narration.json').exists() else {}
    lines = timings['lines']
    if 'lines' in config:
        expected = [(r['id'], r['text']) for r in config['lines']]
        if expected != [(r['id'], r['text']) for r in lines]:
            raise ValueError('Narration and voice-timings disagree; regenerate voice and timing anchors')
    # Manually supplied recordings without voice.py metadata remain supported.
    if not lines or not timings.get('voice'):
        return
    source_lines = {row['id']: row for row in config.get('lines', [])}
    for row in lines:
        path = film / row['file']
        take = read_json(path.with_suffix('.json'))
        profile = timings.get('voiceProfile')
        fingerprint = voice_fingerprint(source_lines.get(row['id'], row), config, profile)
        if profile and take.get('voiceProfile') != profile:
            raise ValueError(f"Voice role changed for {row['id']}; regenerate voice and timing anchors")
        if take.get('text') != row['text'] or take.get('fingerprint') != fingerprint:
            raise ValueError(f"Stale voice cache for {row['id']}; regenerate voice before mixing")
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"Missing or empty voice take: {row['file']}")
        if take.get('audioSha256') and file_hash(path) != take['audioSha256']:
            raise ValueError(f"Voice audio changed for {row['id']}; regenerate the take before mixing")
        if abs((row['end'] - row['start']) - take['duration']) > .002:
            raise ValueError(f"Voice duration changed for {row['id']}; regenerate the timing anchors")


def input_state(film):
    """Hashes include only named inputs, never unrelated cached takes or output stems."""
    timings = read_json(film / 'voice-timings.json')
    validate_voice(film, timings)
    result = {}
    for name in ('narration.json', 'voice-timings.json', 'sound-cues.json', 'anchors.resolved.json'):
        path = film / name
        if path.exists():
            encoded = json.dumps(read_json(path), sort_keys=True, ensure_ascii=False).encode('utf-8')
            result[name] = hashlib.sha256(encoded).hexdigest()
    files = {row['file'] for row in timings['lines']}
    cues = read_json(film / 'sound-cues.json') if (film / 'sound-cues.json').exists() else []
    files.update(f"assets/sfx/{cue['sfx']}.mp3" for cue in cues)
    if (film / 'assets/audio/bed.wav').exists():
        files.add('assets/audio/bed.wav')
    for name in sorted(files):
        result[name] = file_hash(film / name)
    return result


def validate_mix_state(film):
    """Raise on failed/stale mixes. Legacy passed reports retain their supported checks."""
    report_path = film / 'assets/audio/mix-report.json'
    if not report_path.exists():
        return
    report = read_json(report_path)
    if not isinstance(report, dict):
        raise ValueError('Invalid mix report; rerun sound/mix.py')
    if report.get('status') != 'passed' or report.get('outputsPublished') is not True:
        raise ValueError('Latest mix did not pass; rerun sound/mix.py before rendering')
    if 'inputs' in report or 'outputSha256' in report:
        if (not isinstance(report.get('inputs'), dict)
                or not isinstance(report.get('outputSha256'), dict)
                or not report['outputSha256'].get('final-mix.wav')):
            raise ValueError('Incomplete mix fingerprints; rerun sound/mix.py')
    timing_path = film / 'voice-timings.json'
    if timing_path.exists():
        timings = read_json(timing_path)
        validate_voice(film, timings)
        try:
            duration = float(report.get('duration', float('nan')))
        except (TypeError, ValueError) as exc:
            raise ValueError('Invalid mix duration; remix required') from exc
        if not math.isfinite(duration) or not math.isclose(duration, timings['duration'], abs_tol=.04):
            raise ValueError('Mix duration differs from the current film clock; remix required')
    if 'inputs' in report and report['inputs'] != input_state(film):
        raise ValueError('Mix inputs changed since mastering; rerun sound/mix.py')
    for name, expected in report.get('outputSha256', {}).items():
        if file_hash(film / 'assets/audio' / name) != expected:
            raise ValueError(f'Mastered audio changed: {name}; rerun sound/mix.py')
