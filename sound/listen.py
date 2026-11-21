"""Build a local, narration-only review with neighboring takes and their real gaps."""
import argparse
from html import escape
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import soundfile as sf

from audio_state import file_hash, read_json, validate_voice
from mix import SR, decode, place


def review_sources(film, validate=True):
    timings = read_json(film / 'voice-timings.json')
    if validate:
        validate_voice(film, timings)
    rows = timings['lines']
    if not rows:
        raise ValueError(f'{film.name} has no narration takes')
    return rows, {row['id']: index for index, row in enumerate(rows)}


def make_clip(film, rows, index, neighbors, destination, cache):
    excerpt = rows[max(0, index - neighbors):index + neighbors + 1]
    start, end = excerpt[0]['start'], excerpt[-1]['end']
    track = np.zeros((round((end - start) * SR), 1), dtype=np.float32)
    details = []
    previous = None
    for row in excerpt:
        path = (film / row['file']).resolve()
        if not path.is_relative_to(film.resolve()) or not path.is_file():
            raise ValueError(f"Missing local take for {row['id']}: {row['file']}")
        if path not in cache:
            cache[path] = decode(path, 1)
        max_samples = round((row['end'] - row['start']) * SR)
        place(track, cache[path][:max_samples], row['start'] - start)
        words = row.get('words', [])
        gap = round(row['start'] - previous['end'], 3) if previous else None
        word_gap = (round(words[0]['start'] - previous['words'][-1]['end'], 3)
                    if words and previous and previous.get('words') else None)
        details.append({'id': row['id'], 'text': row['text'], 'start': row['start'],
                        'fileGap': gap, 'wordGap': word_gap,
                        'words': [{'text': word['text'], 'start': round(word['start'] - start, 3),
                                   'end': round(word['end'] - start, 3)} for word in words]})
        previous = row
    sf.write(destination, track, SR, subtype='PCM_16')
    return details


def review_page(cards):
    sections = []
    for line_id, tracks in cards.items():
        bodies = []
        for track in tracks:
            items = []
            word_buttons = []
            for row in track['lines']:
                text = escape(row['text'])
                if row['id'] == line_id:
                    text = f'<strong>{text}</strong>'
                    previous_end = None
                    for word in row['words']:
                        gap = word['start'] - previous_end if previous_end is not None else None
                        timing = f'{word["start"]:.2f} 秒'
                        if gap is not None:
                            timing += f'，距上一词 {gap:.2f} 秒'
                        word_buttons.append(f'<button type="button" data-seek="{word["start"]}" '
                                            f'title="{timing}">{escape(word["text"])}</button>')
                        previous_end = word['end']
                gap = row['wordGap']
                detail = f' · 距上一句末词 {gap:.2f} 秒' if gap is not None else ''
                items.append(f'<li><small>{row["start"]:.2f} 秒{detail}</small><p>{text}</p></li>')
            words = (f'<details><summary>逐词定位</summary>'
                     f'<div class="words">{"".join(word_buttons)}</div></details>' if word_buttons else '')
            bodies.append(f'<div class="take"><h3>{track["label"]}</h3><audio controls preload="metadata" '
                          f'src="{track["audio"]}"></audio><ul>{"".join(items)}</ul>{words}</div>')
        sections.append(f'<section><h2>{escape(line_id)}</h2><div class="takes">{"".join(bodies)}</div></section>')
    return """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>配音试听</title><style>
*{box-sizing:border-box}
body{margin:2rem auto;padding:0 1rem;max-width:66rem;background:#f4f2ec;color:#202927;
font:1rem/1.6 system-ui,sans-serif}
h2{font-size:1.15rem;margin:0} h3{font-size:1rem;margin:.5rem 0}
section{padding:1.15rem;margin:1rem 0;border:1px solid #d9ded8;border-radius:.6rem;background:#fffefa}
.takes{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,24rem),1fr));gap:1rem}
audio{width:100%} ul{padding:0;list-style:none} li{margin:.5rem 0}
small{color:#52635d} p{margin:.1rem 0 .65rem} strong{color:#175c52}
.words{display:flex;flex-wrap:wrap;gap:.35rem;margin-top:.5rem}
summary{cursor:pointer} button{font:inherit;color:inherit;background:#f4f2ec;border:1px solid #d9ded8;
border-radius:.25rem;padding:.15rem .4rem;cursor:pointer}
</style><h1>配音试听</h1>
<p>加粗为待复听的句子。间隔按词时间计算。</p>
""" + '\n'.join(sections) + """
<script>
document.addEventListener('click', event => {
  const button = event.target.closest('button[data-seek]');
  if (!button) return;
  const audio = button.closest('.take').querySelector('audio');
  document.querySelectorAll('audio').forEach(clip => { if (clip !== audio) clip.pause(); });
  audio.currentTime = Math.max(0, Number(button.dataset.seek) - 0.2);
  audio.play().catch(() => {});
});
</script>
</html>
"""


def build_review(film, output, ids, neighbors=1, before=None):
    if neighbors < 0:
        raise ValueError('Context must be zero or a positive number of takes')
    film = film.resolve()
    rows, indices = review_sources(film)
    requested = set(ids)
    if unknown := requested - indices.keys():
        raise ValueError('Unknown narration IDs: ' + ', '.join(sorted(unknown)))
    selected = [row['id'] for row in rows if not requested or row['id'] in requested]
    versions = [('当前', film, rows, indices)]
    if before:
        before = before.resolve()
        old_rows, old_indices = review_sources(before, validate=False)
        versions.insert(0, ('上一版', before, old_rows, old_indices))
    output.mkdir(parents=True, exist_ok=True)
    cards, cache = {}, {}
    with TemporaryDirectory(prefix='.listen-', dir=output) as temporary:
        staged = Path(temporary)
        for number, line_id in enumerate(selected, 1):
            cards[line_id] = []
            for version, (label, source, takes, lookup) in enumerate(versions, 1):
                if line_id in lookup:
                    temporary_audio = staged / 'clip.wav'
                    lines = make_clip(source, takes, lookup[line_id], neighbors, temporary_audio, cache)
                    audio = f'{number:03d}-{version}-{file_hash(temporary_audio)[:16]}.wav'
                    temporary_audio.replace(staged / audio)
                    cards[line_id].append({'label': label, 'audio': audio, 'lines': lines})
        (staged / 'review.json').write_text(json.dumps(cards, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (staged / 'index.html').write_text(review_page(cards), encoding='utf-8')
        for file in staged.glob('*.wav'):
            file.replace(output / file.name)
        for name in ('review.json', 'index.html'):
            (staged / name).replace(output / name)
    return output / 'index.html'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('film', type=Path)
    parser.add_argument('ids', nargs='*', help='Review all takes when no IDs are provided')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--context', type=int, default=1, help='Neighboring takes on each side')
    parser.add_argument('--before', type=Path, help='Earlier film directory with its clock and audio')
    args = parser.parse_intermixed_args(argv)
    try:
        print(build_review(args.film, args.output, args.ids, args.context, args.before))
    except (ValueError, OSError) as exc:
        parser.exit(1, str(exc) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
