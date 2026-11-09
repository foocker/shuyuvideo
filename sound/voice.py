"""Generate cached narrator takes; API roles are configured in tools/shuyuvideo/.env.

python sound/voice.py <film-dir> [line-id ...] [--role ROLE] [--sample]
python sound/voice.py --list-roles
"""
import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import edge_tts
from voice_config import effective_rate, effective_speech_text, restore_word_texts, voice_fingerprint
from voice_roles import ROLES, read_env, resolve_role, credentials, credential_ready
from voice_api import synthesize_api, rate_percent, VoiceAPIError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'writing'))
from manuscript import check_if_managed

TICK = 1e7


def probe_duration(path):
    out = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                   '-of', 'default=noprint_wrappers=1:nokey=1', str(path)], encoding='utf-8')
    return float(out.strip())


def take_path(line, config, folder, profile=None):
    if not profile or profile['provider'] == 'edge':
        return folder / f"{line['id']}.mp3"
    # API trials and edits cannot overwrite audio referenced by the current clock.
    key = voice_fingerprint(line, config, profile)
    return folder / 'roles' / profile['role'] / key / f"{line['id']}.wav"


def cached_take(line, config, folder, profile=None):
    dest = take_path(line, config, folder, profile)
    stamp = dest.with_suffix('.json')
    if dest.is_file() and dest.stat().st_size and stamp.is_file():
        try:
            cached = json.loads(stamp.read_text(encoding='utf-8'))
            if not isinstance(cached, dict):
                return None
            if cached.get('fingerprint') != voice_fingerprint(line, config, profile):
                return None
            if cached.get('audioSha256') and hashlib.sha256(dest.read_bytes()).hexdigest() != cached['audioSha256']:
                return None
            return cached
        except (ValueError, OSError):
            pass
    return None


async def synthesize(line, config, folder, profile=None, env=None):
    cached = cached_take(line, config, folder, profile)
    if cached:
        return cached
    dest = take_path(line, config, folder, profile)
    dest.parent.mkdir(parents=True, exist_ok=True)
    rate = effective_rate(line, config)
    spoken = effective_speech_text(line, config)
    api = profile and profile['provider'] != 'edge'
    # A lost API reply may already be billed, so API requests are not retried.
    for attempt in range(1 if api else 3):
        try:
            with tempfile.TemporaryDirectory(prefix='.voice-', dir=dest.parent) as tmp:
                staged = Path(tmp) / dest.name
                if api:
                    words = await asyncio.to_thread(synthesize_api, spoken, rate, profile, env, staged)
                else:
                    words = []
                    request = edge_tts.Communicate(spoken, config['voice'], rate=rate,
                                                   boundary='WordBoundary', connect_timeout=20, receive_timeout=60)
                    with staged.open('wb') as fp:
                        async for chunk in request.stream():
                            if chunk['type'] == 'audio':
                                fp.write(chunk['data'])
                            elif chunk['type'] == 'WordBoundary':
                                words.append({'text': chunk['text'], 'start': round(chunk['offset'] / TICK, 3),
                                              'end': round((chunk['offset'] + chunk['duration']) / TICK, 3)})
                words = restore_word_texts(words, spoken, line['text'])
                duration = round(probe_duration(staged), 3)
                if not words or duration <= 0 or not staged.stat().st_size:
                    raise ValueError('Empty voice take or missing word timestamps')
                record = {'id': line['id'], 'text': line['text'], 'rate': rate,
                          'fingerprint': voice_fingerprint(line, config, profile),
                          'duration': duration, 'words': words,
                          'audioSha256': hashlib.sha256(staged.read_bytes()).hexdigest()}
                if api:
                    record['voiceProfile'] = profile
                if spoken != line['text']:
                    record['spokenText'] = spoken
                meta = staged.with_suffix('.json')
                meta.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
                staged.replace(dest)
                meta.replace(dest.with_suffix('.json'))
                return record
        except Exception:
            if api or attempt == 2:
                raise
            await asyncio.sleep(2 + attempt)


async def main(film, only, role=None, dry_run=False, sample=False):
    check_if_managed(film)
    config = json.loads((film / 'narration.json').read_text(encoding='utf-8'))
    env = read_env()
    profile = resolve_role(config, role, env)
    api = profile['provider'] != 'edge'
    folder = film / 'assets/voice'
    lines = config['lines']
    unknown = only - {line['id'] for line in lines}
    if unknown:
        raise ValueError('Unknown line IDs: ' + ', '.join(sorted(unknown)))
    if sample and not only:
        raise ValueError('--sample requires one or more line IDs')
    for line in lines:
        if not isinstance(line['id'], str) or not line['id'] or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in line['id']):
            raise ValueError('Line IDs must use letters, digits, underscores or hyphens')
        rate = effective_rate(line, config)
        effective_speech_text(line, config)
        if api:
            rate_percent(rate)
        for bad in ('$', '\\', '/', '?', '�'):
            if bad in line['text']:
                raise ValueError(f"{line['id']}: narration text must not contain {bad!r}")
    selected = [line for line in lines if not only or line['id'] in only]
    cached = {line['id']: cached_take(line, config, folder, profile) for line in lines}
    if dry_run:
        print(json.dumps({'profile': profile, 'credentialsReady': credential_ready(profile, env),
                          'sampleOnly': sample, 'selectedLines': len(selected),
                          'cachedLines': sum(cached[line['id']] is not None for line in selected),
                          'requestsNeeded': sum(cached[line['id']] is None for line in selected)},
                         ensure_ascii=False, indent=2))
        return
    if only and not sample:
        missing = [line['id'] for line in lines if line['id'] not in only and not cached[line['id']]]
        if missing:
            raise ValueError('Other lines need this role/settings too; run the whole film, or use --sample: ' + ', '.join(missing))
    if any(not cached[line['id']] for line in selected):
        credentials(profile, env)
    gate = asyncio.Semaphore(1 if api else 2)

    async def one(line):
        async with gate:
            return await synthesize(line, config, folder, profile, env)

    if api:
        # Stop on the first failed paid request, without queued requests starting.
        takes = [await one(line) for line in selected]
    else:
        takes = await asyncio.gather(*(one(line) for line in selected))
    if sample:
        for line, take in zip(selected, takes):
            print(f"{line['id']}: {take['duration']:.3f}s  {take_path(line, config, folder, profile)}")
        print('Sample takes saved; the film clock was not changed.')
        return
    takes = {**cached, **{take['id']: take for take in takes}}
    clock = float(config.get('lead', 0.5))
    timeline = []
    for line in lines:
        take = takes[line['id']]
        start = round(float(line.get('start', clock)), 3)
        if start < clock - 1e-3:
            raise ValueError(f"{line['id']} overlaps the previous line")
        end = round(start + take['duration'], 3)
        timeline.append({'id': line['id'], 'text': line['text'], 'rate': effective_rate(line, config),
                         'file': take_path(line, config, folder, profile).relative_to(film).as_posix(),
                         'start': start, 'end': end,
                         'words': [{**w, 'start': round(start + w['start'], 3), 'end': round(start + w['end'], 3)}
                                   for w in take['words']]})
        clock = end + float(line.get('pause', config.get('gap', 0.35)))
    duration = round(clock + float(config.get('tail', 1.0)), 3)
    result = {'voice': profile['voice'], 'rate': config.get('rate', '+0%'), 'duration': duration, 'lines': timeline}
    if api:
        result['voiceProfile'] = profile
    with tempfile.TemporaryDirectory(prefix='.voice-clock-', dir=film) as tmp:
        staged = Path(tmp) / 'voice-timings.json'
        staged.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        staged.replace(film / 'voice-timings.json')
    for item in timeline:
        print(f"{item['id']}: {item['start']:7.3f} - {item['end']:7.3f}  {item['text']}")
    print(f'duration {duration}')


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('film', nargs='?', type=Path)
    parser.add_argument('lines', nargs='*')
    parser.add_argument('--role', choices=list(ROLES), help='override SHUYU_VOICE_ROLE for this run')
    parser.add_argument('--list-roles', action='store_true')
    parser.add_argument('--dry-run', action='store_true', help='show settings/cache status without network calls')
    parser.add_argument('--sample', action='store_true', help='synthesize selected lines without replacing the film clock')
    args = parser.parse_intermixed_args()
    if args.list_roles:
        for role, (label, _, _) in ROLES.items():
            print(f'{role:20s} {label}')
        return
    if not args.film:
        parser.error('film directory is required unless --list-roles is used')
    try:
        asyncio.run(main(args.film.resolve(), set(args.lines), args.role, args.dry_run, args.sample))
    except (ValueError, VoiceAPIError) as exc:
        parser.exit(1, f'{exc}\n')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cli()
