"""Distinguish actual mirrors from the dark tinted window/monitor material."""
import bpy,sys,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import build_v4_rebuilt_environment as A
import v4_rebuilt_environment_kit as K
p=A.O/'room-assembly.json';m=json.loads(p.read_text());changed=[]
for row in m['assets']:
    raw=(R/row['file']).read_bytes();size=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+size]);names=[n.get('name','')for n in j['nodes']]
    wanted=lambda n:any(k in n for k in ['vanity_mirror_surface','mirror_surface','fixed_mirror'])or n.startswith('mirror_panel')
    if not any(wanted(n)for n in names):continue
    A.clean();bpy.ops.import_scene.gltf(filepath=str(R/row['file']));count=0
    for o in bpy.data.objects:
        if o.type=='MESH'and wanted(o.name):o.data.materials.clear();o.data.materials.append(K.M['mirror']);count+=1
    new=A.export(list(bpy.data.objects),Path(row['file']).name,row['runtime'],{k:v for k,v in row.items()if k not in ['file','runtime','triangles','meshParts','rawBytes']});row.update(new);changed.append((Path(row['runtime']).stem,count))
p.write_text(json.dumps(m,indent=2)+'\n');print('ACTUAL_MIRROR_MATERIALS',changed)
