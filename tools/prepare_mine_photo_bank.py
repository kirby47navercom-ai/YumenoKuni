"""Use the already examined entry photograph as one movable recollection unit.

Native SVG composition only: original compressed WebP bytes are embedded
unchanged. No raster crop, retouch, new photograph or invented distractor.
"""
import base64,hashlib,json
from prepare_mine_object_bank import ROOT,BANK,rotated_footprints

def main():
    task='T6-MM-01';number=12;name='historical_entry_photo'
    stage=json.loads((ROOT/'data/v4_story/native_tasks.json').read_text(encoding='utf-8'))['tasks'][task]['stage']
    assert len(stage['regions'])==1 and stage['regions'][0]['correct']
    source=ROOT/stage['image'];raw=source.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==stage['pictureProvenance']['sha256']
    width,height,pad=504,294,12
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="504" height="294" viewBox="0 0 504 294"><image x="12" y="12" width="480" height="270" preserveAspectRatio="none" href="data:image/webp;base64,{base64.b64encode(raw).decode()}"/></svg>\n'
    target=BANK/(name+'.svg');target.write_text(svg,encoding='utf-8');digest=hashlib.sha256(target.read_bytes()).hexdigest()
    rows=['' if y<pad or y>=height-pad else f'{pad}:{width-pad}' for y in range(height)]
    size=8.8;rw=size/20;rh=size*height/width/11;rect=[.25,.15,rw,rh]
    rects={str(c):[.5-rw*20/c/2,.15,rw*20/c,rh] for c in (18,20,22)}
    cells={}
    for c,r in rects.items():
        cells[c]=sorted({int((r[1]+(y+.5)/height*r[3])*11)*int(c)+int((r[0]+(x+.5)/width*r[2])*int(c)) for y in range(pad,height-pad) for x in range(pad,width-pad)})
        assert all(0<=i<int(c)*11 for i in cells[c])
    mask={'objects':{name:{'width':width,'height':height,'rows':rows,'alphaThreshold':127,'rotations':rotated_footprints(rows,width,height,size)}}}
    maskname=f'mask_{number}.json';(BANK/maskname).write_text(json.dumps(mask,separators=(',',':')),encoding='utf-8')
    obj={'id':name,'regionId':stage['regions'][0]['id'],'texture':f'Assets/Art/mine_objects/{name}.svg','maskKey':name,'maskAsset':f'Assets/Data/mine_objects/{number}.json','rect':rect,'rectByWidth':rects,'rotation':0,'sizeCells':size,'cellsByWidth':cells,'original':target.relative_to(ROOT).as_posix(),'runtime':target.relative_to(ROOT).as_posix(),'sourceSHA256':digest,'runtimeSHA256':digest}
    selection=f'selection_{task}.json';(BANK/selection).write_text(json.dumps({'taskId':task,'objects':[obj],'reference':stage['image'],'embeddedOriginalSHA256':hashlib.sha256(raw).hexdigest(),'sourceProof':stage['pictureProvenance']['sourceProof'],'method':'Native SVG places the unchanged already-examined photograph in one movable picture unit; analytic opaque image rectangle and transparent margin. No bitmap pixels edited.','visualReview':{'sourceFullImageDirectViewed':True,'runtime':False},'limits':['Only the existing one qualifying entry picture is selectable. Selection accepts the fully uncovered picture unit, not the prior exact face contour. No unseen interior, timestamp, duplicate witness, continuous movement or additional photograph is supplied. Original8-angle pixel masks are not reconstructed.']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    entries=json.loads((BANK/'banks.json').read_text(encoding='utf-8'));entry={'selection':selection,'mask':maskname,'target':f'Assets/Data/mine_objects/{number}.json'}
    if entry not in entries:entries.append(entry)
    (BANK/'banks.json').write_text(json.dumps(entries,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'task':task,'objects':1,'rasterPixelsEdited':False,'newPhoto':False}))

if __name__=='__main__':main()
