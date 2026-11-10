"""Rebuild the initial Ink motion data from the approved local stickman study.

This is an explicit import, not a runtime dependency. Further editing can be done
in motions.json and compiled with build-data.py without importing again.
"""
from pathlib import Path
import copy, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'stickman/motions.json'
source = json.loads(SOURCE.read_text(encoding='utf8'))
data = copy.deepcopy(source)
S = 44 / 96
data['schema'] = 'shuyu-ink-motions/v1'
data['rig'] = dict(color='#263640', backColor='#40515b', headRadius=12.5,
                   hipHeight=44, torsoWidth=15, footLength=13,
                   unit='Ink units; y down; foot sole at y=0')
data['retarget'] = dict(source='character/stickman/motions.json',
                       sourceSha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                       scale=S, headOffsetScale=[.65,.80],
                       interpolation='monotone cubic Hermite; contact holds preserved')
for name, a in data['actions'].items():
    a['motionSource'] = a.pop('reference', {})
    a.pop('studyNote', None)
    for k in a['keys']:
        p = k['pose']
        for j in data['joints'] + ['root']:
            p[j] = [v*S for v in p[j]]
        # Ink has a smaller solid head and a longer neck relative to head size.
        p['head'] = [p['neck'][i] + (p['head'][i]-p['neck'][i])*f
                     for i,f in enumerate((.65,.80))]
        # Resting hands reach the hip as in the original Ink design. Contact
        # poses and acrobatics keep their separately authored endpoints.
        if name in ('observe','walk') or (name in ('pick','recover','jump','frontflip','backflip')
                and abs(p['hip'][1]+44)<.01 and abs(p['neck'][0])<.01):
            for side in ('Back','Front'):
                for j,f in [('hand'+side,1.18),('elbow'+side,1.08)]:
                    p[j] = [p['neck'][i] + (p[j][i]-p['neck'][i])*f for i in range(2)]
        # Feet are wider than the stickman's stroke ends. Open the neutral
        # stance enough that both feet and both legs remain legible.
        if name in ('observe','pick','recover'):
            p['footBack'][0] -= 3
            p['kneeBack'][0] -= 1.5
        if name in ('frontflip','backflip') and .76 <= k['t'] <= 1.29:
            p['elbowFront'][0] += 5
            p['handFront'][0] += 3
            p['elbowBack'][0] -= 8
            p['handBack'][0] -= 27
        p['headScale'] = [1+(v-1)*.65 for v in p['headScale']]
        if name in ('recover','drag'):
            p['hip'][1] = min(-4.3,p['hip'][1])
            for j in ('kneeFront','kneeBack'):
                p[j][1] = min(-3.7,p[j][1])
    if a.get('gait'):
        for field in ('stride','touchdown','lift','thigh','shin'):
            a['gait'][field] *= S
        a['armDelay'] = .045 if name=='walk' else .025
    if a.get('airborne'):
        for field in ('height','distance'):
            a['airborne'][field] *= S
        a['airborne']['pivot'] = [v*S for v in a['airborne']['pivot']]
    if a.get('prop'):
        a['prop']['ground'] = [v*S for v in a['prop']['ground']]

# Attention is authored in the head's local coordinates, in eye-white units.
# It is evaluated before full-body rotation, so the face cannot float on flips.
gaze = {
 'observe': [[0,.3,0],[.28,.5,.65],[.8,.65,.8],[1.55,.65,.8],[1.9,.4,0],[2.4,.4,0]],
 'pick': [[0,.4,0],[.25,.7,.7],[2.4,.8,.8],[3.05,1,0],[4,1,0],[4.6,.8,.3],[5.2,1,0],[5.6,1,0]],
 'jump': [[0,.5,0],[.2,.5,-.5],[.6,.4,-.7],[1.15,.6,.1],[1.4,.6,.7],[2,.4,0],[2.4,.4,0]],
 'frontflip': [[0,.5,0],[.5,.7,-.4],[1,.2,0],[1.4,.6,.5],[2.6,.4,0]],
 'backflip': [[0,.4,0],[.4,0,-.7],[.8,-.2,-.4],[1.4,.5,.5],[2.6,.4,0]],
}
for name,a in data['actions'].items():
    a['gaze'] = gaze.get(name, [[0,.65,.35 if name in ('press','drag') else 0],
                              [a['duration'],.65,.35 if name in ('press','drag') else 0]])
    a['blinks'] = {'observe':[1.75], 'pick':[.12,4.15], 'recover':[1.1],
                    'jump':[1.61], 'frontflip':[1.77], 'backflip':[1.77]}.get(name,[])
    a['interpolation'] = 'pchip'
(ROOT/'motions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Imported',len(data['actions']),'actions into Ink proportions')
