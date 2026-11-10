"""Check actual decoded video pixels so an occasional missing prop cannot pass."""
from pathlib import Path
import subprocess,json,argparse
import numpy as np
parser=argparse.ArgumentParser();parser.add_argument('--movie',action='store_true');args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'output/character-ink';records=[]
for name in ['turnWheel','push']:
 file=OUT/'assets'/f'{name}-props-alpha.webm'
 raw=subprocess.check_output(['ffmpeg','-v','error','-c:v','libvpx-vp9','-i',str(file),'-f','rawvideo','-pix_fmt','rgba','pipe:1'])
 frames=np.frombuffer(raw,np.uint8).reshape((-1,640,640,4));counts=[]
 for im in frames:
  # This right-hand region contains the wheel / block, away from the white eyes.
  crop=im[260:540,390:620];mask=(crop[:,:,3]>128)&(crop[:,:,:3].max(axis=2)>130)
  counts.append(int(mask.sum()))
 assert min(counts)>100,(name,min(counts),[i for i,c in enumerate(counts) if c<=100])
 records.append(dict(action=name,frames=len(frames),minimumPropPixels=min(counts),maximumPropPixels=max(counts)))
movieRecords=[]
if args.movie:
 catalog=json.loads((OUT/'reports/catalog.json').read_text(encoding='utf8'))
 for name in ['turnWheel','push']:
  shot=next(s for s in catalog['shots'] if s['a']==name)
  raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(shot['start']),'-i',str(OUT/'renders/ink-actions.mp4'),'-t',str(shot['end']-shot['start']),'-vf','crop=250:650:800:190','-f','rawvideo','-pix_fmt','rgb24','pipe:1'])
  frames=np.frombuffer(raw,np.uint8).reshape((-1,650,250,3));counts=[]
  for im in frames:
   # White background and dark actor are excluded; only coloured prop surfaces remain.
   mask=(im.min(axis=2)>80)&(im.max(axis=2)<232)&(im.max(axis=2)>110)
   counts.append(int(mask.sum()))
  assert min(counts)>300,(name,'movie missing prop',min(counts))
  movieRecords.append(dict(action=name,frames=len(frames),minimumPropPixels=min(counts),maximumPropPixels=max(counts)))
(OUT/'reports/encoded-prop-check.json').write_text(json.dumps({'passed':True,'records':records,'movieRecords':movieRecords},indent=2),encoding='utf8')
print('Encoded props continuous:',records)
