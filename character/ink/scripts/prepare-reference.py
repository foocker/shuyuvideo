"""Freeze the approved reference runtime for the offline comparison page."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
(ROOT/'reference').mkdir(exist_ok=True)
for name in ['motions.js','stickman.js']:
    shutil.copy2(ROOT.parent/'stickman/lib'/name,ROOT/'reference'/name)
shutil.copy2(ROOT.parent/'stickman/SOURCES.md',ROOT/'reference/SOURCES.md')
print('Copied local reference runtime')
