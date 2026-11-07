"""Generate one Mandarin take per narration line and lay them out on one clock.

Usage: python sound/voice.py <film-dir> [line-id ...]

Reads <film>/narration.json (format: docs/NARRATION.md). Writes
<film>/assets/voice/<id>.mp3 and <film>/voice-timings.json, which holds each
line's start/end on the film clock plus per-word times. Takes are cached by
text, voice and rate, so editing one line regenerates only that line.

Needs edge-tts >= 7.3.1 (older versions get HTTP 403); `shuyu setup` installs
it into the root .venv. Run it with `shuyu exec sound/voice.py <film-dir>`.
"""
import asyncio
import json
import subprocess
import sys
from pathlib import Path

import edge_tts
from voice_config import effective_rate, voice_fingerprint

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'writing'))
from manuscript import check_if_managed

TICK = 1e7  # edge-tts offsets are in 100 ns units


def probe_duration(path):
    out = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                   '-of', 'default=noprint_wrappers=1:nokey=1', str(path)], encoding='utf-8')
    return float(out.strip())


async def synthesize(line, config, folder):
    dest = folder / f"{line['id']}.mp3"
    stamp = folder / f"{line['id']}.json"
    rate = effective_rate(line, config)
    fingerprint = voice_fingerprint(line, config)
    if dest.exists() and stamp.exists():
        cached = json.loads(stamp.read_text(encoding='utf-8'))
        if cached.get('fingerprint') == fingerprint:
            return cached
    for attempt in range(3):
        try:
            words = []
            request = edge_tts.Communicate(line['text'], config['voice'], rate=rate,
                                           boundary='WordBoundary', connect_timeout=20, receive_timeout=60)
            with dest.open('wb') as fp:
                async for chunk in request.stream():
                    if chunk['type'] == 'audio':
                        fp.write(chunk['data'])
                    elif chunk['type'] == 'WordBoundary':
                        words.append({'text': chunk['text'], 'start': round(chunk['offset'] / TICK, 3),
                                      'end': round((chunk['offset'] + chunk['duration']) / TICK, 3)})
            record = {'id': line['id'], 'text': line['text'], 'rate': rate, 'fingerprint': fingerprint,
                      'duration': round(probe_duration(dest), 3), 'words': words}
            stamp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
            return record
        except Exception:
            if attempt == 2:
                raise
            await asyncio.sleep(2 + attempt)


async def main(film, only):
    check_if_managed(film)
    config = json.loads((film / 'narration.json').read_text(encoding='utf-8'))
    folder = film / 'assets/voice'
    folder.mkdir(parents=True, exist_ok=True)
    lines = config['lines']
    for line in lines:
        effective_rate(line, config)
        for bad in ('$', '\\', '/', '?', '�'):
            assert bad not in line['text'], f"{line['id']}: narration text must not contain {bad!r}"
    gate = asyncio.Semaphore(2)

    async def one(line):
        async with gate:
            return await synthesize(line, config, folder)

    takes = await asyncio.gather(*(one(l) for l in lines if not only or l['id'] in only))
    takes = {t['id']: t for t in takes}
    for line in lines:
        if line['id'] not in takes:
            takes[line['id']] = json.loads((folder / f"{line['id']}.json").read_text(encoding='utf-8'))
        if takes[line['id']].get('fingerprint') != voice_fingerprint(line, config):
            raise ValueError(f"Stale voice cache for {line['id']}; include it in this voice run")

    clock = float(config.get('lead', 0.5))
    timeline = []
    for line in lines:
        take = takes[line['id']]
        start = round(float(line.get('start', clock)), 3)
        assert start >= clock - 1e-3, f"{line['id']} overlaps the previous line"
        end = round(start + take['duration'], 3)
        timeline.append({'id': line['id'], 'text': line['text'], 'rate': effective_rate(line, config),
                         'file': f"assets/voice/{line['id']}.mp3",
                         'start': start, 'end': end,
                         'words': [{**w, 'start': round(start + w['start'], 3), 'end': round(start + w['end'], 3)}
                                   for w in take['words']]})
        clock = end + float(line.get('pause', config.get('gap', 0.35)))
    duration = round(clock + float(config.get('tail', 1.0)), 3)
    result = {'voice': config['voice'], 'rate': config.get('rate', '+0%'), 'duration': duration, 'lines': timeline}
    (film / 'voice-timings.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    for item in timeline:
        print(f"{item['id']}: {item['start']:7.3f} - {item['end']:7.3f}  {item['text']}")
    print(f'duration {duration}')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    asyncio.run(main(Path(sys.argv[1]).resolve(), set(sys.argv[2:])))
