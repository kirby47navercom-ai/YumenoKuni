import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
O=R/'art/space_v4/park_levels_v1'
bpy.ops.wm.open_mainfile(filepath=str(O/'parks-authoring.blend'))
data={}
for ident in ['fairytale','carnival','mirrors','clockwork','starlight','perimeter']:
    root=bpy.data.objects['park_level_'+ident]
    data[ident]={'children':[[o.name,o.type,len(o.children_recursive)] for o in root.children],
      'labels':[[o.name,str(o.get('facilityLabel',''))] for o in root.children_recursive if o.type=='FONT' or o.get('facilityLabel') or o.name.startswith(('physical_wayfinding','backed_architectural','sign_continuous','attached_sign'))],
      'signMaterials':[[o.name,[m.name for m in o.data.materials if m and ('identity_facility_sign' in m.name or 'identity_room_face' in m.name)]] for o in root.children_recursive if o.type=='MESH' and any(m and ('identity_facility_sign' in m.name or 'identity_room_face' in m.name)for m in o.data.materials)]}
(O/'theme_park_v2/source-inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
print('INVENTORY_WRITTEN',flush=True)
