"""Incremental corrections from actual source/native review, retaining the rest."""
import bpy,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import build_v4_rebuilt_environment as A
import v4_rebuilt_environment_kit as K
import v4_rebuilt_landmarks as L
bpy.ops.wm.open_mainfile(filepath=str(A.O/'sources/park-rebuilt.blend'));K.setup_materials();world=bpy.data.objects['park_exterior_level'];p=bpy.data.objects['exterior_coaster_platform'];A.erase(p.children_recursive);new=L.coaster(K);new.parent=p;A.rematerial(world.children_recursive);A.freeze(list(world.children_recursive));bpy.context.preferences.filepaths.save_version=0
A.terrain_aperture(world)
bpy.ops.wm.save_as_mainfile(filepath=str(A.O/'sources/park-rebuilt.blend'),compress=True)
groups=[bpy.data.objects['exterior_'+n]for n in ['plaza','park_garden','pool_edge','ferris_platform','coaster_platform','park_main_gate']];landmarks=set(o for g in groups for o in A.descendants(g));common=[o for o in world.children_recursive if o not in landmarks]
manifest=json.loads((A.O/'exterior-assembly.json').read_text());newrows=[A.export(common,'finish_context.glb','Assets/Art/explore3d/finish_context.glb',{'facadesRebuilt':31,'treesRebuilt':22}),A.export(A.descendants(p),'finish_coaster_platform.glb','Assets/Art/explore3d/finish_coaster_platform.glb')];replace={a['runtime']:a for a in newrows};manifest['assets']=[replace.get(a['runtime'],a)for a in manifest['assets']];(A.O/'exterior-assembly.json').write_text(json.dumps(manifest,indent=2)+'\n');print('REBUILT_INCREMENTAL_POLISH_READY',flush=True)
