"""Editable Blender comparison of the six authored hero prop families."""
import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/lowpoly_v1'
bpy.ops.wm.read_factory_settings(use_empty=True)
families=[('dining_room','dining_room_chair'),('dining_room','dining_room_meeting_table'),('plaza','plaza_detail_fountain_dry'),('plaza','plaza_park_bench'),('plaza','plaza_detail_planter.002'),('plaza','sculpt_street_lamp')]
for label,folder in [('HIGH_reference','materials_v2'),('LOW_baked','lowpoly_v1')]:
 collection=bpy.data.collections.new(label);bpy.context.scene.collection.children.link(collection)
 for room in ['dining_room','plaza']:
  previous=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(R/'art/space_v4'/folder/'models'/('explore3d__'+room+'.glb')))
  added=set(bpy.context.scene.objects)-previous;roots=[];keep=set()
  for i,(source,name) in enumerate(families):
   if source!=room:continue
   root=next(o for o in added if o.name==name);keep.add(root);keep.update(root.children_recursive);roots.append((i,root))
  for o in added-keep:bpy.data.objects.remove(o,do_unlink=True)
  for i,root in roots:
   world=root.matrix_world.copy();root.parent=None;root.matrix_world=world;root.location=Vector(((i%3)*5,(i//3)*5,0))
  for obj in keep:
   for old in list(obj.users_collection):old.objects.unlink(obj)
   collection.objects.link(obj)
   obj.name=label+'_'+obj.name
 collection.hide_render=label.startswith('HIGH');collection.hide_viewport=label.startswith('HIGH')
bpy.data.orphans_purge(do_recursive=True)
bpy.context.scene['comparison']='Toggle HIGH_reference / LOW_baked collections. Identical authored families; low meshes contain actual high-to-low normal and material bakes.'
bpy.ops.wm.save_as_mainfile(filepath=str(O/'hero-high-low.blend'),compress=True)
print('EDITABLE_HIGH_LOW_SAVED',flush=True)
