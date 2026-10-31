"""Bake the brand's actual Georgia Omega outline, plus local UI fonts."""
from pathlib import Path
import json
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools import subset
ROOT=Path(__file__).resolve().parents[1]
font=TTFont('C:/Windows/Fonts/georgia.ttf');glyphs=font.getGlyphSet();name=font.getBestCmap()[937]
bounds=BoundsPen(glyphs);glyphs[name].draw(bounds);x0,y0,x1,y1=bounds.bounds
record=RecordingPen();pen=Qu2CuPen(record,max_err=.3,all_cubic=True);glyphs[name].draw(pen)
scale=300/(y1-y0);center=(x0+x1)/2
commands=[]
for op,points in record.value:
    commands.append([{'moveTo':'M','lineTo':'L','curveTo':'C','closePath':'Z'}[op],*[[round((x-center)*scale,5),round(-(y-y0)*scale,5)] for x,y in points]])
data={'source':'ShuYu2 icon.svg: Georgia capital Omega; C:/Windows/Fonts/georgia.ttf','height':300,'commands':commands}
(ROOT/'lib/omega-shape.js').write_text('(function(r){const shape='+json.dumps(data,separators=(',',':'))+';if(typeof module!=="undefined"&&module.exports)module.exports=shape;else r.ShuyuOmegaShape=shape;})(globalThis);\n',encoding='utf-8')
text=''.join(p.read_text(encoding='utf-8') for suffix in ['*.html','*.js'] for p in ROOT.rglob(suffix) if 'vendor' not in p.parts and 'output' not in p.parts)+''.join(chr(i) for i in range(32,127))
for target,source in [('ui','msyh.ttc'),('ui-bold','msyhbd.ttc')]:
    font=TTFont(Path('C:/Windows/Fonts')/source,fontNumber=0);sub=subset.Subsetter(options=subset.Options());sub.populate(text=text);sub.subset(font);font.flavor='woff2';font.save(ROOT/f'assets/fonts/{target}.woff2')
print(json.dumps({'outlineCommands':len(commands),'height':300,'fonts':'local'}))
