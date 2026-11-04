"""One deterministic font-subsetting implementation and content-addressed cache."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import tempfile

from fontTools import subset
from fontTools.ttLib import TTFont

from workspace import ROOT, config, font_path, font_record, inside


def build_subset(font_id, text, destination):
    source = font_path(font_id)
    record = font_record(font_id)
    chars = ''.join(sorted(set(text)))
    inputs = {'font': hashlib.sha256(source.read_bytes()).hexdigest(),
              'faceIndex': record.get('faceIndex', 0), 'text': chars,
              'fonttools': importlib.metadata.version('fonttools'), 'format': 'woff2-v1'}
    key = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    cache = inside(config()['cacheRoot']) / 'fonts'
    cache.mkdir(parents=True, exist_ok=True)
    cached = cache / f'{key}.woff2'
    if not cached.exists():
        with TTFont(source, fontNumber=inputs['faceIndex'], recalcTimestamp=False) as font:
            options = subset.Options()
            options.recalc_timestamp = False
            sub = subset.Subsetter(options=options)
            sub.populate(text=chars)
            sub.subset(font)
            font.flavor = 'woff2'
            with tempfile.NamedTemporaryFile(dir=cache, suffix='.woff2', delete=False) as handle:
                temp = Path(handle.name)
            try:
                font.save(temp)
                temp.replace(cached)
            finally:
                temp.unlink(missing_ok=True)
        (cache / f'{key}.json').write_text(json.dumps({
            # The file name and hash identify the source without recording a machine path.
            'fontId': font_id, 'source': source.name, 'sourceSha256': inputs['font'],
            'faceIndex': inputs['faceIndex'], 'characters': len(chars),
            'license': record['license'], 'sha256': hashlib.sha256(cached.read_bytes()).hexdigest()
        }, ensure_ascii=False, indent=2), encoding='utf-8')
    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Copies keep exported projects portable and prevent editing one bundle
    # from mutating the central cache or another work through a hard link.
    shutil.copy2(cached, dest)
    return {'fontId': font_id, 'cacheKey': key,
            'path': dest.relative_to(ROOT).as_posix() if dest.is_relative_to(ROOT) else dest.name,
            'sha256': hashlib.sha256(dest.read_bytes()).hexdigest(), 'characters': len(chars), 'license': record['license']}
