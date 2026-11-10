"""Compile editable motion JSON into an offline, dependency-free JS bundle."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'motions.json').read_text(encoding='utf-8'))
assert data['schema'] == 'shuyu-stickman-motions/v1'
for name, action in data['actions'].items():
    times = [key['t'] for key in action['keys']]
    assert times[0] == 0 and all(a < b for a, b in zip(times, times[1:])), name
    assert times[-1] == action['duration'], name
(ROOT / 'lib/motions.js').write_text(
    '// Generated from motions.json. Run scripts/build-data.py after editing.\n'
    '(function(g){const data=' + json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    + ';if(typeof module!=="undefined"&&module.exports)module.exports=data;'
    + 'else g.StickmanMotionData=data;})(globalThis);\n', encoding='utf-8')
print('Compiled', len(data['actions']), 'actions')
