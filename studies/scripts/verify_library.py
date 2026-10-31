"""Verify archived research without importing any sibling project or extra package."""
from __future__ import annotations

import hashlib
from html import unescape
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


def local_path(base: Path, relative: str) -> Path:
    path = (base / unquote(relative)).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(f'Missing or external research file: {base}: {relative}')
    return path


def digest(path: Path) -> str:
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main() -> None:
    checked_links = 0
    for document in [*ROOT.rglob('*.md'), *ROOT.rglob('*.html')]:
        text = document.read_text(encoding='utf-8')
        if document.suffix == '.md':
            links = re.findall(r'\]\(([^)]+)\)', text)
        else:
            links = re.findall(r'(?:src|href)="([^"$]+)"', text)
        for link in links:
            url = urlsplit(unescape(link))
            if url.scheme or url.netloc or not url.path:
                continue
            local_path(document.parent, url.path)
            checked_links += 1

    cases = []
    for study_path in ROOT.glob('cases/*/study.json'):
        case = study_path.parent
        study = json.loads(study_path.read_text(encoding='utf-8'))
        provenance = json.loads((case / 'sources/provenance.json').read_text(encoding='utf-8'))
        video = local_path(case, study['video'])
        assert video == local_path(case, provenance['video']['relative_path'])
        assert digest(video) == provenance['video']['sha256']
        assert video.stat().st_size == provenance['video']['bytes']
        for record in provenance['sources']:
            assert digest(local_path(case, record['file'])) == record['sha256']
        chapters = study['chapters']
        assert chapters[0]['start'] == 0 and chapters[-1]['end'] == study['duration']
        for index, chapter in enumerate(chapters):
            assert chapter['start'] < chapter['end']
            if index:
                assert chapter['start'] == chapters[index - 1]['end']
        for event in study['events']:
            assert 0 <= event['start'] < event['end'] <= study['duration']
            assert all(event['start'] <= t <= event['end'] for t in event['samples'])
            local_path(case, f'evidence/{event["id"]}.jpg')
        evidence = json.loads((case / 'evidence/manifest.json').read_text(encoding='utf-8'))
        assert evidence['video_sha256'] == provenance['video']['sha256']
        for sheet in evidence['sheets']:
            local_path(case, sheet['file'])
            assert all(0 <= t <= study['duration'] for t in sheet['times'])
        script = (case / 'study-data.js').read_text(encoding='utf-8')
        study_json, sentences_json = script.split('window.STUDY = ', 1)[1].split(';\nwindow.SENTENCES = ', 1)
        assert json.loads(study_json) == study
        sentences = json.loads((case / 'sources/sentence_timings.json').read_text(encoding='utf-8'))
        assert json.loads(sentences_json.rstrip().removesuffix(';')) == sentences
        cases.append({'id': study['id'], 'video': video.relative_to(ROOT).as_posix(),
                      'chapters': len(chapters), 'events': len(study['events']),
                      'sentences': len(sentences), 'sheets': len(evidence['sheets'])})

    snapshots = ROOT / 'references/art-motion'
    sources = json.loads((snapshots / 'sources.json').read_text(encoding='utf-8'))
    for record in sources['files']:
        assert digest(local_path(snapshots, record['path'])) == record['sha256']
    print(json.dumps({'status': 'passed', 'local_links_checked': checked_links,
                      'reference_snapshots': len(sources['files']), 'cases': cases},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
