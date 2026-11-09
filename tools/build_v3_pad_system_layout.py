"""Project retained SFL leaves; no archives, original process or extraction."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/analysis/v3_rebuild'
reference=json.loads((DOC/'pad_subpage_reference.json').read_text(encoding='utf-8'))
cache=Path(reference['evidence_cache'])
assert hashlib.sha256(cache.read_bytes()).hexdigest()==reference['evidence_cache_sha256']
source=next(x for x in reference['existing_common_carriers'] if x['ancestry']==['flash/techou/techou_system_US.spc'])
leaves=[]
for row in source['hierarchy_first_local_frame']:
    key=row.get('definition_ref')
    if not key:continue
    definition=source['leaf_definitions'][key]
    if key.startswith('4:'):
        b=definition['text_header']['bounds_xywh'];bounds=[b[0],b[0]+b[2],b[1],b[1]+b[3]]
    else:
        records=definition.get('shape_rect_records',[])
        if not records:continue
        bounds=[min(r['four_ints'][0] for r in records),max(r['four_ints'][1] for r in records),min(r['four_ints'][2] for r in records),max(r['four_ints'][3] for r in records)]
    m=row['composed_affine_row_major'];points=[[(x*m[0]+y*m[3]+m[6])*2/3,(x*m[1]+y*m[4]+m[7])*2/3] for x in bounds[:2] for y in bounds[2:]]
    x=min(p[0] for p in points);y=min(p[1] for p in points)
    leaves.append({'path':row['path'],'definition_ref':key,'local_bounds':bounds,'affine':m,'rect_1280':[round(x,5),round(y,5),round(max(p[0] for p in points)-x,5),round(max(p[1] for p in points)-y,5)]})
result={'scope':'Retained SFL geometry only; fl_backlog root and child first local frames. All local canvas bounds are not opaque ink. No original runtime/pixel/material/child-animation equality.',
 'target_sha256':reference['target_sha256'],'cache_sha256':reference['evidence_cache_sha256'],'source':source['source'],'sfl_sha256':source['sfl_sha256'],'label':source['snapshot_label'],'leaves':leaves,
 'entries':['backlog','save','load','option','kisekae','mainmenu'],
 'selection_lift_design':44,'selection_lift_1280':44*2/3,
 'limits':['Original per-entry root label sets are not all replayed here. The observed fl_backlog lift is not proof of all in/out animation frames.',
 'Original title/icon raster resources are absent from the supplied bank; typography and own vector ink must be identified as adaptations.']}
(DOC/'pad_system_ui_contract.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'ok':True,'leaves':len(leaves),'roots':sorted({x['path'].split('/')[0] for x in leaves})}))
