"""Synchronize the HyperFrames duration with the shared action catalogue."""
from pathlib import Path
import json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
catalog=json.loads(subprocess.check_output(['node','-p',"JSON.stringify(require('./lib/catalog.js'))"],cwd=ROOT))
duration=catalog['duration']
for name in ['index.html','compositions/showcase.html']:
 p=ROOT/name;s=p.read_text(encoding='utf8');s=re.sub(r'data-duration="[\d.]+"',f'data-duration="{duration}"',s)
 if name=='index.html' and 'lib/catalog.js' not in s:s=s.replace('<script src="reference/motions.js">','<script src="lib/catalog.js"></script><script src="lib/guides.js"></script><script src="reference/motions.js">')
 s=s.replace('墨影基础动作','墨影动作库');p.write_text(s,encoding='utf8')
report=ROOT.parents[1]/'output/character-ink/reports/catalog.json';report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf8')
print('Catalogue:',len(catalog['shots']),'actions,',duration,'seconds')
