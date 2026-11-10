"""Author Ink-specific story actions. Existing action data is never regenerated.

Run explicitly to replace this named set, then build-data.py. Coordinates are
Ink units, sole y=0. Props and grip weights are editable pose channels.
"""
from pathlib import Path
from copy import deepcopy
import json, math

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'motions.json').read_text(encoding='utf8'))
base=deepcopy(data['actions']['observe']['keys'][0]['pose'])
base.update(footBack=[-16,0],footFront=[12,0],kneeBack=[-13,-23],kneeFront=[15,-24],
            elbowBack=[-18,-62],handBack=[-18,-43],elbowFront=[17,-63],handFront=[21,-43])
extra=dict(propKind=0,propX=0,propY=0,propAngle=0,propAlpha=1,propPage=0,propBend=0,
           gripFront=0,gripBack=0,pageGrip=0,footAngleFront=0,footAngleBack=0,eyeClose=0)

def pose(parent=None,**changes):
    p=deepcopy(parent or base)
    for k,v in extra.items():p.setdefault(k,v)
    p.update(changes)
    return p

def body(p,dx=0,dy=0):
    p=deepcopy(p)
    for j in ['head','neck','waist','hip','elbowBack','handBack','elbowFront','handFront']:
        p[j]=[p[j][0]+dx,p[j][1]+dy]
    return p

def item(name,label,category,keys,description,shots,**options):
    duration=keys[-1][0]
    contacts=options.pop('contacts', [dict(joint=j,start=0,end=duration) for j in ['footBack','footFront']])
    a=dict(label=label,category=category,duration=duration,loop=False,
           description=description,storyUse=shots,source='Ink-specific authored animation; no new video trace',
           keys=[dict(t=t,pose=p) for t,p in keys],contacts=contacts,
           gaze=[[0,.5,0],[duration,.5,0]],blinks=[],interpolation='pchip',
           beats=[keys[0][0],keys[len(keys)//2][0],keys[-1][0]],viewScale=1)
    a.update(options);data['actions'][name]=a

paperRig=dict(kind='paper',grips={'Front':[12.5,9],'Back':[-12.5,9]},armLengths=[26,27])
paperLow=pose(propKind=1,propX=31,propY=-26,propAngle=-9,gripFront=1,gripBack=1)
reading=pose(propKind=1,propX=30,propY=-61,propAngle=-7,gripFront=1,gripBack=1,
             head=[9,-94],headTilt=8)
paperReach=pose(propKind=1,propX=32,propY=-50,propAngle=-9,
                head=[16,-90],neck=[8,-78],waist=[0,-58],hip=[-3,-43],headTilt=14,
                handFront=[45,-43],elbowFront=[28,-58],handBack=[21,-39],elbowBack=[-5,-48])
paperCaught=pose(paperReach,gripFront=1,gripBack=1)
item('paperTake','接过论文','paper',[(0,pose(propKind=1,propX=32,propY=-50,propAngle=-9)),(.3,pose(propKind=1,propX=32,propY=-50,propAngle=-9)),(.8,paperReach),(1.02,paperCaught),(1.3,paperCaught),(2.2,reading),(2.8,reading)],
     '先看纸页，双手接住，再抬到眼前。','11、12、14、15：纸页、论文与手稿',propRig=paperRig,beats=[.8,1.3,2.4],gaze=[[0,.7,.7],[.7,.8,.8],[2.1,.8,.5],[2.8,.8,.5]])
readBreathe=pose(body(reading,dy=-.65),propY=-61.6,propAngle=-5.5)
item('paperRead','持纸阅读','paper',[(0,reading),(.8,readBreathe),(1.5,pose(reading,headTilt=12,head=[11,-92])),(2.2,readBreathe),(3,reading)],
     '双手托住纸页，目光按行移动。','12、14、15：阅读论文和书信',loop=True,propRig=paperRig,beats=[.3,1.5,2.7],
     gaze=[[0,.3,.2],[.4,.9,.2],[.55,.2,.5],[1.15,.9,.5],[1.3,.2,.8],[2,.8,.8],[2.6,.3,.2],[3,.3,.2]],blinks=[2.35])
flipReach=pose(reading,gripFront=0,pageGrip=1,handFront=[43,-75],elbowFront=[38,-54])
flipHalf=pose(reading,gripFront=0,pageGrip=1,handFront=[15,-77],elbowFront=[26,-55],propPage=.5,propBend=4,headTilt=5)
flipEnd=pose(reading,gripFront=0,pageGrip=1,handFront=[-9,-74],elbowFront=[-15,-60],propPage=1,propBend=1)
item('paperFlip','翻阅一页','paper',[(0,reading),(.35,reading),(.75,flipReach),(1,flipReach),(1.4,flipHalf),(1.85,flipEnd),(2.1,flipEnd),(2.6,pose(reading,propPage=1)),(3,pose(reading,propPage=1))],
     '一手托纸，一手捏起页角翻过去，再扶稳。','14、15、35：手稿整理与翻阅',propRig=paperRig,beats=[.85,1.4,2.7],gaze=[[0,.8,.4],[1,.6,0],[1.8,-.2,.4],[3,.7,.5]])
offer=pose(reading,propX=46,propY=-62,propAngle=2,head=[26,-95],headTilt=-2,neck=[16,-82],waist=[11,-60])
releasedPaper=pose(offer,gripFront=0,gripBack=0,handFront=[55,-55],handBack=[32,-56])
item('paperOffer','递出论文','paper',[(0,reading),(.3,reading),(1.15,offer),(1.65,offer),(1.9,releasedPaper),(2.3,pose(propKind=1,propX=70,propY=-67,propAngle=2,propAlpha=.7)),(2.7,pose(propKind=1,propX=87,propY=-71,propAngle=2,propAlpha=0)),(3.1,pose(propKind=1,propX=87,propY=-71,propAngle=2,propAlpha=0))],
     '把文稿递向前方，留出交接停顿后松手。','13、15、35：收稿与接续',propRig=paperRig,beats=[.2,1.5,2.7])
guard=pose(reading,propX=23,propY=-49,propAngle=-19,head=[19,-78],neck=[8,-65],waist=[-4,-45],hip=[-13,-29],kneeFront=[22,-20],kneeBack=[-20,-17],headTilt=22,propBend=5)
guardWind=pose(guard,propX=19,propY=-47,propAngle=-27,propBend=-4,head=[16,-76],hip=[-15,-29])
item('paperGuard','迎风护稿','paper',[(0,reading),(.4,reading),(.9,guard),(1.25,guardWind),(1.7,guard),(2,guardWind),(2.55,guard),(3.2,reading),(3.6,reading)],
     '察觉风起，抱紧纸页下蹲，压住后重新站稳。','11、13、17：风雪护纸与扑住手稿',propRig=paperRig,beats=[.3,1.25,3.2],blinks=[1.2],gaze=[[0,.8,.5],[.5,1,-.5],[1.2,.7,.6],[3.6,.7,.5]])

gunRig=dict(kind='gun',grips={'Front':[0,5]},armLengths=[26,27])
gunLow=pose(propKind=2,propX=21,propY=-43,propAngle=63,gripFront=1,
            footBack=[-18,0],footFront=[15,0],handBack=[-14,-46])
aim=pose(gunLow,propX=43,propY=-78,propAngle=0,head=[7,-96],headTilt=-3,
         neck=[1,-81],hip=[-2,-44],waist=[-2,-61],handBack=[-21,-44],elbowBack=[-27,-64])
raiseMid=pose(gunLow,propX=33,propY=-61,propAngle=24,head=[10,-96],headTilt=-4)
item('gunRaise','举枪','gun',[(0,gunLow),(.35,gunLow),(.95,raiseMid),(1.55,aim),(1.9,aim)],
     '目光先锁定，前臂抬起，身体稳住。','按用户新增：独立持枪动作；不自动改变第16镜',propRig=gunRig,beats=[.2,.95,1.75])
aimBreath=pose(aim,propY=-78.45,propAngle=-.35,head=[7,-96.35])
item('gunAim','持枪瞄准','gun',[(0,aim),(1.1,aimBreath),(2.4,aim)],
     '脚底固定，胸口和手臂只有克制的呼吸。','用户指定的持枪动作',loop=True,propRig=gunRig,beats=[0,1.1,2.3],gaze=[[0,1,0],[2.4,1,0]])
recoil=pose(aim,propX=36,propY=-81,propAngle=-13,head=[3,-96],neck=[-2,-80],waist=[-4,-60],hip=[-3,-43],handBack=[-25,-46],elbowBack=[-30,-64],eyeClose=.85)
rebound=pose(aim,propX=41,propY=-76.8,propAngle=2.5,head=[6,-94],neck=[0,-79],hip=[-3,-43])
item('gunFire','开枪与回弹','gun',[(0,aim),(.18,aim),(.25,recoil),(.36,pose(recoil,eyeClose=.25)),(.56,rebound),(.93,aim),(1.3,aim)],
     '短暂稳枪后立即击发，手腕后坐，躯干吸收，再回到瞄准。','用户指定的开枪动作；单次、无目标和伤口',propRig=gunRig,beats=[.05,.26,.93],
     events=[dict(type='muzzle',t=.18,duration=.075,anchor=[31,-2])],gaze=[[0,1,0],[1.3,1,0]])
item('gunLower','收枪放低','gun',[(0,aim),(.35,aim),(.95,raiseMid),(1.55,gunLow),(2,gunLow)],
     '停留确认后放低枪口，肩膀随后松开。','用户指定持枪动作的结束态',propRig=gunRig,beats=[.2,.95,1.75])

# Falls are authored on the ground, including the body's thickness. No
# post-hoc camera shake, blood or arbitrary rotation around the screen origin.
fallStart=pose(footBack=[-16,0],footFront=[12,0])
backHit=pose(fallStart,head=[-8,-93],neck=[-10,-79],waist=[-9,-61],hip=[-6,-43],headTilt=-22,
             handFront=[29,-61],elbowFront=[16,-61],handBack=[-31,-64],elbowBack=[-26,-64])
backUnbalanced=pose(backHit,head=[-34,-76],neck=[-27,-64],waist=[-20,-48],hip=[-20,-28],headTilt=-38,
                   kneeBack=[-10,-17],footFront=[19,-7],kneeFront=[13,-27],handBack=[-44,-42],elbowBack=[-38,-57],handFront=[19,-65],elbowFront=[1,-63],footAngleFront=-18)
backSeat=pose(backUnbalanced,head=[-47,-53],neck=[-38,-42],waist=[-30,-24],hip=[-24,-8],headTilt=-48,
              handBack=[-58,-10],elbowBack=[-51,-30],handFront=[-5,-39],elbowFront=[-15,-46],kneeFront=[10,-22],footFront=[32,-4],kneeBack=[-1,-16],footBack=[16,0],footAngleFront=0)
backDown=pose(head=[-63,-13],neck=[-47,-9],waist=[-30,-8],hip=[-12,-5],headTilt=-86,
              elbowBack=[-45,-5],handBack=[-33,0],elbowFront=[-27,-27],handFront=[-12,-22],
              kneeBack=[10,-7],footBack=[31,-3],kneeFront=[9,-21],footFront=[35,0],eyeClose=.85)
backBounce=pose(backDown,head=[-62,-17],neck=[-46,-11],kneeFront=[10,-25],footFront=[35,-3],eyeClose=.5)
item('fallBack','失衡后倒','fall',[(0,fallStart),(.35,fallStart),(.52,backHit),(.83,backUnbalanced),(1.18,backSeat),(1.48,backDown),(1.62,backBounce),(1.9,backDown),(2.6,backDown)],
     '胸口先失衡，脚离地，臀部再到肩背依次落下。','07、25：甩落、失手；亦可接外力反应',contacts=[dict(joint='footBack',start=0,end=.83),dict(joint='footFront',start=0,end=.52)],beats=[.52,1.18,2.2],viewScale=.96)
forwardHit=pose(head=[24,-88],neck=[14,-76],waist=[5,-58],hip=[-1,-42],headTilt=20,
                handFront=[37,-57],elbowFront=[24,-59],handBack=[-8,-42],elbowBack=[-17,-60])
trip=pose(forwardHit,head=[42,-67],neck=[30,-58],waist=[12,-48],hip=[-5,-36],headTilt=40,
           kneeFront=[14,-18],footFront=[12,0],kneeBack=[-20,-30],footBack=[-34,-11],
           elbowFront=[40,-39],handFront=[54,-18],elbowBack=[6,-32],handBack=[30,-11],footAngleBack=-15)
brace=pose(trip,head=[56,-37],neck=[43,-28],waist=[20,-23],hip=[-2,-18],headTilt=57,
            elbowFront=[58,-18],handFront=[64,0],elbowBack=[29,-13],handBack=[42,0],
            kneeFront=[15,-7],footFront=[12,0],kneeBack=[-20,-14],footBack=[-39,-4],footAngleBack=0)
faceDown=pose(head=[64,-13],neck=[49,-9],waist=[25,-8],hip=[1,-5],headTilt=88,
               elbowFront=[81,-24],handFront=[99,0],elbowBack=[42,-5],handBack=[55,0],
               kneeFront=[-19,-4],footFront=[-43,0],kneeBack=[-17,-20],footBack=[-35,-3],eyeClose=.9)
item('fallForward','绊倒与撑地','fall',[(0,pose()),(.3,pose()),(.57,forwardHit),(.85,trip),(1.14,brace),(1.42,faceDown),(1.57,pose(faceDown,head=[64,-16],eyeClose=.3)),(1.85,faceDown),(2.6,faceDown)],
     '重心冲到脚前，双手先撑地，再伏下停稳。','07、17、20：扑空、摔落与压住纸缝',contacts=[dict(joint='footFront',start=0,end=1.14),dict(joint='footBack',start=0,end=.57)],beats=[.57,1.14,2.2],viewScale=.9)

starRig=dict(kind='star',grips={'Front':[0,3]},armLengths=[27,29])
catchReady=pose(handFront=[26,-100],elbowFront=[30,-76],head=[12,-99],headTilt=-12,
                propKind=3,propX=43,propY=-140,propAngle=-25)
catchTouch=pose(catchReady,propX=37,propY=-96,handFront=[37,-93],propAngle=0,gripFront=1)
catchGive=pose(catchTouch,head=[15,-90],neck=[7,-77],hip=[-5,-39],propX=34,propY=-78,propAngle=9,handBack=[4,-56],elbowBack=[-17,-60])
starHold=pose(propKind=3,propX=30,propY=-67,gripFront=1,headTilt=7,handBack=[10,-49])
item('catchStar','接住落星','star',[(0,catchReady),(.3,catchReady),(.7,pose(catchReady,propY=-119)),(.98,catchTouch),(1.25,catchGive),(1.8,starHold),(2.4,starHold)],
     '先追视落点，接触后手臂向下卸力，再护到身前。','01、18、32：接住朱红星',propRig=starRig,beats=[.3,1.02,2],viewScale=.93,
     gaze=[[0,.6,-1],[.8,.7,-.6],[1.3,.8,.3],[2.4,.8,.5]])
starOffer=pose(starHold,propX=49,propY=-71,propAngle=-5,neck=[4,-82],head=[13,-96],headTilt=1)
starLetGo=pose(starOffer,gripFront=0,handFront=[49,-68])
item('placeStar','送回星轨','star',[(0,starHold),(.3,starHold),(1.1,starOffer),(1.45,starOffer),(1.65,starLetGo),(2.05,pose(starLetGo,propX=65,propY=-80)),(2.45,pose(propKind=3,propX=83,propY=-91,propAlpha=.3)),(2.8,pose(propKind=3,propX=90,propY=-98,propAlpha=0)),(3.1,pose(propKind=3,propX=90,propY=-98,propAlpha=0))],
     '伸手送出，轻轻松掌，让星继续沿轨迹前行。','32、35：把星送回运行的队列',propRig=starRig,beats=[.2,1.4,2.5],viewScale=.9)

leverRig=dict(kind='lever',grips={'Front':[0,-40],'Back':[0,-34]},armLengths=[28,29])
lever=pose(propKind=4,propX=34,propY=-8,propAngle=19,handFront=[35,-36],handBack=[23,-38])
leverTouch=pose(lever,gripFront=1,gripBack=1,head=[17,-91],neck=[8,-78],hip=[-4,-42],headTilt=9)
leverLoad=pose(leverTouch,head=[9,-89],neck=[0,-75],hip=[-13,-37],waist=[-7,-55],kneeFront=[18,-21],kneeBack=[-22,-20])
leverPulled=pose(leverLoad,propAngle=-24,head=[-5,-86],neck=[-11,-72],waist=[-16,-54],hip=[-19,-36],headTilt=-7)
item('pullLever','双手拉杆','machine',[(0,lever),(.4,lever),(.85,leverTouch),(1.1,leverLoad),(1.65,leverPulled),(2,leverPulled),(2.4,pose(leverPulled,gripFront=0,gripBack=0)),(2.9,pose(propKind=4,propX=34,propY=-8,propAngle=-24)),(3.3,pose(propKind=4,propX=34,propY=-8,propAngle=-24))],
     '先握住，再沉下重心拉动，最后松手站回。','06、22、23：连杆与升降机构',propRig=leverRig,beats=[.85,1.65,3],viewScale=.93)
wheelRig=dict(kind='wheel',grips={'Front':[18,0],'Back':[-18,0]},armLengths=[28,29])
wheel=pose(propKind=5,propX=31,propY=-62,propAngle=-24,gripFront=1,gripBack=1,
           head=[10,-96],neck=[3,-82],hip=[-4,-44])
wheelTop=pose(body(wheel,dx=2,dy=2),propAngle=0)
wheelTurn=pose(body(wheel,dx=5,dy=5),propAngle=30,headTilt=9)
item('turnWheel','双手转轮','machine',[(0,wheel),(.5,wheelTop),(1.15,wheelTurn),(1.6,wheelTurn),(2.25,wheelTop),(3,wheel)],
     '双手跟住轮缘，用肩背带动来回推转。','10、22、29、30、31：星环变成舵',loop=True,propRig=wheelRig,beats=[0,1.3,2.25])
pushRig=dict(kind='block',grips={'Front':[-14,-9],'Back':[-14,8]},armLengths=[27,29])
block=pose(propKind=6,propX=57,propY=-34,handFront=[31,-47],handBack=[19,-37])
pushTouch=pose(block,gripFront=1,gripBack=1,head=[23,-85],neck=[14,-72],waist=[1,-58],hip=[-9,-42],headTilt=11)
pushLoad=pose(pushTouch,head=[25,-80],neck=[15,-67],waist=[0,-51],hip=[-16,-31],kneeBack=[-20,-16],kneeFront=[23,-20])
pushMove=pose(pushLoad,propX=65,head=[31,-83],neck=[21,-70],hip=[-9,-34],waist=[8,-54])
item('push','抵住并推开','machine',[(0,block),(.35,block),(.85,pushTouch),(1.2,pushLoad),(1.9,pushMove),(2.25,pushMove),(2.6,pose(pushMove,gripFront=0,gripBack=0)),(3.1,pose(propKind=6,propX=65,propY=-34)),(3.5,pose(propKind=6,propX=65,propY=-34))],
     '双掌贴住，压低身体蓄力，推移后收手。','13、24、30：扶纸、锁具与推动星环',propRig=pushRig,beats=[.85,1.9,3.2],viewScale=.93)

# Match the approved walk rig: neither thigh nor shin changes length.
# Both knees bend toward the same side of the screen, as a side-view person.
legRig=dict(thigh=data['actions']['walk']['gait']['thigh'],shin=data['actions']['walk']['gait']['shin'],bend=1)
oneHang=pose(head=[7,-101],neck=[-2,-87],waist=[-3,-69],hip=[-4,-50],
              elbowFront=[20,-113],handFront=[10,-136],elbowBack=[-21,-69],handBack=[-13,-56],
              footFront=[4,0],footBack=[-9,-2])
oneSwing=pose(oneHang,head=[9,-101],neck=[0,-87],waist=[2,-69],hip=[3,-50],
               elbowFront=[22,-113],handBack=[-10,-55],footFront=[14,-1],footBack=[1,-3])
oneReturn=pose(oneHang,head=[4,-101],neck=[-5,-87],waist=[-7,-69],hip=[-10,-50],
               handBack=[-18,-56],footFront=[-3,-1],footBack=[-15,-3])
item('hangOne','单手悬挂','contact',[(0,oneHang),(.65,oneSwing),(1.3,oneHang),(1.95,oneReturn),(2.6,oneHang)],
     '单手承重，腿自然垂下，双脚小幅错开随重心摆动。','20、25：抓边与按住最后一个卡扣',loop=True,legRig=legRig,contacts=[dict(joint='handFront',start=0,end=2.6)],beats=[0,.65,1.95],viewScale=.95,guide=dict(kind='bar',anchor=[10,-136]))
# Release drops 28 units; landing narrows the stance and bends both knees forward.
releaseStart=pose(oneHang,root=[0,-28])
letGo=pose(releaseStart,handFront=[18,-119],elbowFront=[29,-100],handBack=[-21,-63])
releaseEnd=pose(head=[8,-101],neck=[0,-87],waist=[-2,-69],hip=[-4,-50],
                footFront=[6,0],footBack=[-8,0],elbowFront=[20,-70],handFront=[24,-49],elbowBack=[-18,-68],handBack=[-12,-48])
fallAir=pose(releaseEnd,root=[0,-12],footFront=[6,0],footBack=[-8,-1],
              elbowFront=[25,-80],handFront=[31,-92],elbowBack=[-23,-81],handBack=[-27,-92])
land=pose(releaseEnd,elbowFront=[26,-72],handFront=[35,-73],elbowBack=[-24,-72],handBack=[-30,-73])
compress=pose(body(land,dx=3,dy=9),headTilt=9)
releaseKeys=[(0,releaseStart),(.35,releaseStart),(.5,letGo),(.72,fallAir),(1.02,land),(1.16,compress),(1.32,compress),(1.95,releaseEnd),(2.4,releaseEnd)]
item('release','松手落地','contact',releaseKeys,'松开抓点，双腿自然落下；脚掌踩稳后向前屈膝，再站直。','25、33：主动放手',legRig=legRig,contacts=[dict(joint='handFront',start=0,end=.35),dict(joint='footFront',start=1.02,end=2.4),dict(joint='footBack',start=1.02,end=2.4)],beats=[.35,1.16,1.95],viewScale=.84,guide=dict(kind='bar',anchor=[10,-164]))

climb0=pose(head=[5,-100],neck=[-1,-86],waist=[-3,-67],hip=[-4,-49],
            handFront=[32,-120],elbowFront=[31,-94],handBack=[18,-100],elbowBack=[24,-77],
            footFront=[10,0],footBack=[-7,0])
climbFoot=pose(climb0,footFront=[11,-22])
climbReach=pose(climbFoot,handBack=[18,-142],elbowBack=[-11,-116])
climbLift=pose(climbReach,head=[11,-111],neck=[5,-97],waist=[3,-78],hip=[1,-60],
               footBack=[-6,-10],elbowFront=[37,-99],elbowBack=[-8,-120])
climbHigh=pose(climbLift,head=[12,-121],neck=[6,-107],waist=[4,-88],hip=[2,-70],
               footBack=[-3,-22],elbowFront=[37,-98],elbowBack=[-5,-124])
item('climbUp','抓握攀上一级','contact',[(0,climb0),(.3,climb0),(.85,climbFoot),(1.05,climbFoot),(1.45,climbReach),(1.75,climbLift),(2.55,climbHigh),(3.1,climbHigh)],
     '一脚抬膝踩上一级，换高抓点；支撑腿蹬起，后脚跟上。','22、23：机器台阶与爬梯',legRig=legRig,contacts=[dict(joint='handFront',start=0,end=3.1),dict(joint='handBack',start=0,end=1.05),dict(joint='handBack',start=1.45,end=3.1),dict(joint='footBack',start=0,end=1.05),dict(joint='footBack',start=2.55,end=3.1),dict(joint='footFront',start=0,end=.3),dict(joint='footFront',start=.85,end=3.1)],beats=[.85,1.75,2.7],guide=dict(kind='ladder',x=20,rungs=[-142,-120,-100,-66,-44,-22,0]),viewScale=.95)

data['version']='2.1.0'
for name,a in data['actions'].items():
    a.setdefault('category','basic')
    a.setdefault('description',a.get('label',name))
    a.setdefault('beats',[0,a['duration']*.5,a['duration']])
    a.setdefault('viewScale',1)
(ROOT/'motions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Ink actions:',len(data['actions']))
