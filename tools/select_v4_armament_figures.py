"""Preserve imagegen bytes; inspect alpha without editing raster pixels."""
import json, hashlib, shutil
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art/v4_production/armament_20261103'
rows=json.loads((OUT/'selected-inputs.json').read_text(encoding='utf-8'))
bank={'version':1,'symbolicArmor':True,'runtimeVerified':False,'figures':{}}
for row in rows:
    source=Path(row['file'])
    with Image.open(source) as im:
        assert im.mode=='RGBA',source
        alpha=im.getchannel('A'); lo,hi=alpha.getextrema()
        assert lo==0 and hi>200,source
        width,height=im.size
        bounds=alpha.point(lambda x:255 if x>32 else 0).getbbox()
        assert bounds and bounds[0]>0 and bounds[1]>0 and bounds[2]<width and bounds[3]<height,(source,bounds)
    name=row.get('outputFilename',f"{row['who']}-{row['phase']}.png")
    dest=OUT/name
    if dest.exists(): assert dest.read_bytes()==source.read_bytes(),dest
    else: shutil.copyfile(source,dest)
    spec=bank['figures'].setdefault(row['who'],{'states':[]})
    spec['states'].append({'phase':row['phase'],'source':dest.relative_to(ROOT).as_posix(),'texture':'Assets/Art/armament_v4/'+name,'aspect':width/height,'width':width,'height':height,'alphaRange':[lo,hi],'visibleBounds':bounds,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'generatedSource':str(source)})
for spec in bank['figures'].values():
    spec['states'].sort(key=lambda x:['full','half','core'].index(x['phase']))
    assert len(spec['states'])==3
(OUT/'runtime-bank.json').write_text(json.dumps(bank,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'opponents':len(bank['figures']),'states':len(rows),'pixelEdits':0}))
