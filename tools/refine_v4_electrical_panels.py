"""Refine the reviewed electrical cabinets without changing their placement/state."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import build_v4_rebuilt_environment as A
import v4_rebuilt_environment_kit as K
O=A.O;p=O/'room-assembly.json';manifest=json.loads(p.read_text());row=next(a for a in manifest['assets']if a['runtime'].endswith('/electrical_room.glb'))
A.clean();bpy.ops.import_scene.gltf(filepath=str(R/row['file']))
A.erase([o for o in bpy.data.objects if o.name.startswith('readable_breaker_face')])
material=K.M['iron'].copy();material.name='rebuilt_readable_breaker_panel';bs=material.node_tree.nodes.get('Principled BSDF');tex=material.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(R/'art/space_v4/rebuilt_dedicated_v2/masters/electrical-panel.png'),check_existing=False);tex.image.pack();material.node_tree.links.new(tex.outputs[0],bs.inputs['Base Color']);K.M['breaker_panel']=material
panels=[o for o in bpy.data.objects if o.name.startswith('breaker_cabinet')and o.type=='MESH']
for cabinet in panels:
    points=[cabinet.matrix_world@Vector(p)for p in cabinet.bound_box];lo=[min(p[i]for p in points)for i in range(3)];hi=[max(p[i]for p in points)for i in range(3)];x=(lo[0]+hi[0])/2;y=lo[1]-.004;w=hi[0]-lo[0]
    levels=[lo[2]+.035,.70,1.,1.3,1.6,1.9,2.2,hi[2]-.035];vs=[0,.29,.38,.47,.56,.65,.74,1]
    v=[(xx,y,z)for z in levels for xx in [lo[0]+.035,hi[0]-.035]];o=K.mesh('readable_breaker_face',v,[(i*2,i*2+1,i*2+3,i*2+2)for i in range(len(levels)-1)],'breaker_panel')
    for face in o.data.polygons:
        if face.normal.y>0:face.flip()
        for li in face.loop_indices:
            index=o.data.loops[li].vertex_index;o.data.uv_layers[0].data[li].uv=(index%2,vs[index//2])
    K.frame_ring('readable_breaker_face_seam',w-.025,hi[2]-lo[2]-.025,.024,.025,'iron',None,(x,y+.008,(lo[2]+hi[2])/2))
# The back-wall title was behind the tall equipment. Put it on the clear entry
# wall; the permanent HUD continues to identify the room from the initial view.
sign=next(o for o in bpy.data.objects if o.name.startswith('facility_electrical_room')and o.type=='EMPTY');d=A.SPECS['electrical_room']['size_m'][1];sign.location=(0,-d/2+.18,2.75);sign.rotation_euler.z=3.141592653589793
A.freeze(list(bpy.data.objects));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'sources/electrical_room.blend'),compress=True)
new=A.export(list(bpy.data.objects),Path(row['file']).name,row['runtime'],{k:v for k,v in row.items()if k not in ['file','runtime','triangles','meshParts','rawBytes']});manifest['assets']=[new if a['runtime']==new['runtime']else a for a in manifest['assets']];p.write_text(json.dumps(manifest,indent=2)+'\n');print('ELECTRICAL_PANELS_REFINED',len(panels))
