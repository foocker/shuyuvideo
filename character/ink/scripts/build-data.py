from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'motions.json').read_text(encoding='utf8'))
(ROOT/'lib').mkdir(exist_ok=True)
(ROOT/'lib/motions.js').write_text('/* Generated from motions.json. */\n(function(g){const data='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';if(typeof module!=="undefined"&&module.exports)module.exports=data;else g.InkMotionData=data;})(globalThis);\n',encoding='utf8')
print('Built Ink motion data')
