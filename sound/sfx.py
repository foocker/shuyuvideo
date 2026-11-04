"""Copy the sound effects a film's cues name into <film>/assets/sfx.

Usage: python sound/sfx.py <film-dir>

Sources, in order: sound/library/ (your own local files, git-ignored), then the
HyperFrames media-use bundled library (Pixabay Content License), looked up in the
installed agent skills, and any folders in workspace.local.json soundLibraries. The Pixabay
license forbids redistributing the files on their own, so they are copied into
each film (films/ is git-ignored) and never committed to this public repository.
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'scripts'))
from workspace import ROOT, config  # noqa: E402

# Relative to the user's home; resolved on this machine, never stored as an absolute path.
SKILL_LIBRARY = Path('.claude/skills/media-use/audio/assets/sfx')
SOURCES = [HERE / 'library',
           *[ROOT / p for p in config().get('soundLibraries', [])],
           Path.home() / SKILL_LIBRARY]


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
