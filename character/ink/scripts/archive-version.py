"""Freeze a finished version without overwriting any existing archive."""
from pathlib import Path
import hashlib,json,shutil,argparse
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'output/character-ink'
parser=argparse.ArgumentParser();parser.add_argument('--version',default='v03-contact-and-props');parser.add_argument('--zip',default='ink-motion-assets-v3.zip');args=parser.parse_args()
assert args.version.replace('-','').replace('_','').isalnum()
versions=OUT/'renders/versions';dest=versions/args.version
assert not dest.exists(),'Archive already exists; create a new version instead'
dest.mkdir(parents=True)
shutil.copytree(ROOT,dest/'source',ignore=shutil.ignore_patterns('__pycache__','.hyperframes'))
shutil.copytree(OUT/'reports',dest/'reports',ignore=shutil.ignore_patterns('*.log'))
records=[]
for file in [OUT/'renders/ink-actions.mp4',OUT/'renders/ink-actions-cover.jpg',OUT/args.zip,OUT/'delivery.json']:
 shutil.copy2(file,dest/file.name)
 records.append(dict(file=file.name,bytes=file.stat().st_size,sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
data=json.loads((ROOT/'motions.json').read_text(encoding='utf8'));catalog=json.loads((OUT/'reports/catalog.json').read_text(encoding='utf8'))
record=dict(version=args.version,date='2026-11-10',duration=catalog['duration'],actions=len(data['actions']),files=records,source='source/',review='source/REVIEW.md')
(dest/'version.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
previous=json.loads((versions/'versions.json').read_text(encoding='utf8'))['versions'] if (versions/'versions.json').exists() else []
allVersions=previous+[record]
(versions/'versions.json').write_text(json.dumps({'project':'character-ink','current':record['version'],'versions':allVersions},ensure_ascii=False,indent=2),encoding='utf8')
(versions/'INDEX.md').write_text('# 墨影动作版本\n\n'+''.join(f'- [{v["version"]}]({v["version"]}/ink-actions.mp4)：{v["actions"]} 动作，{v["duration"]} 秒，{v["date"]}。含完整源码、素材包、封面和检查报告。\n' for v in allVersions),encoding='utf8')
for r in records:
 assert hashlib.sha256((dest/r['file']).read_bytes()).hexdigest()==r['sha256']
print('Archived',dest)
