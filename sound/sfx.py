"""Copy the sound effects a film's cues name into <film>/assets/sfx.

Usage: python sound/sfx.py <film-dir>

Sources, in order: sound/library/ (your own local files, git-ignored), then the
HyperFrames media-use bundled library (Pixabay Content License). The Pixabay
license forbids redistributing the files on their own, so they are copied into
each film (films/ is git-ignored) and never committed to this public repository.
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = [HERE / 'library', Path.home() / '.claude/skills/media-use/audio/assets/sfx']


def main(film):
    cues = json.loads((film / 'sound-cues.json').read_text(encoding='utf-8'))
    dest = film / 'assets/sfx'
    dest.mkdir(parents=True, exist_ok=True)
    for name in sorted({c['sfx'] for c in cues}):
        source = next((d / f'{name}.mp3' for d in SOURCES if (d / f'{name}.mp3').is_file()), None)
        if source is None:
            raise SystemExit(f'No sound named {name!r} in {[str(d) for d in SOURCES]}')
        shutil.copy2(source, dest / source.name)
        print(f'{name}: {source}')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(Path(sys.argv[1]).resolve())
