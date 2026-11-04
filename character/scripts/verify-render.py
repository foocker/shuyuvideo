"""Check the encoded showcase against the actual HyperFrames review frames."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from workspace import output_dir, font_path
import json,subprocess,hashlib
from PIL import Image,ImageChops,ImageStat,ImageDraw
ROOT=Path(__file__).resolve().parents[1];movie=output_dir('character','renders')/'shuyu-omega-showcase.mp4'
if not movie.exists(): movie=output_dir('character')/'shuyu-omega-showcase.mp4'
review=output_dir('character','reports','snapshots')
if not list(review.glob('frame-*.png')): review=output_dir('character','review')
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
v=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(1920,1080,'30/1',1080)
assert abs(float(probe['format']['duration'])-36)<.04
assert not any(s['codec_type']=='audio' for s in probe['streams'])
subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-f','null','-'],check=True,capture_output=True)
comparisons=[];frames=[]
for source in sorted(review.glob('frame-*.png')):
    t=float(source.stem.split('-at-')[-1][:-1]);target=review/('encoded-'+source.name)
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(movie),'-frames:v','1',str(target)],check=True,capture_output=True)
    stat=ImageStat.Stat(ImageChops.difference(Image.open(source).convert('RGB'),Image.open(target).convert('RGB')))
    mae=sum(stat.mean)/3;assert mae<4,(t,mae);comparisons.append({'time':t,'mae':mae});frames.append(target)
assert len(frames)>=9
sheet=Image.new('RGB',(1440,((len(frames)+2)//3)*296),'#eaeae2');draw=ImageDraw.Draw(sheet)
for i,path in enumerate(frames):
    x=i%3*480;y=i//3*296;sheet.paste(Image.open(path).convert('RGB').resize((480,270)),(x,y));draw.text((x+12,y+276),path.stem.replace('encoded-frame-',''),fill='#141413')
sheet.save(output_dir('character')/'export-contact.jpg',quality=93)
report={'duration':36,'frames':1080,'dimensions':[1920,1080],'fps':30,'audio':'none by design','fullDecode':'passed','frameComparisons':comparisons,'sha256':hashlib.sha256(movie.read_bytes()).hexdigest()}
(output_dir('character')/'render-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
