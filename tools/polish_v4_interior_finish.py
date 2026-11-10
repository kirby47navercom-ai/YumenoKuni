"""Original wall-mounted finish pass; preserves canonical floor/portal/case geometry."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];SPACE=ROOT/'art/space_v4/full_v2';OUT=SPACE/'interior_art_r4';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SPACE/'space_art_source.blend'));scene=bpy.context.scene
manifest=json.loads((SPACE/'interior_art_r3/manifest.json').read_text(encoding='utf8'))
specs={s['id']:s for s in json.loads((SPACE/'manifest.json').read_text(encoding='utf8'))['spaces']}
M={k:bpy.data.materials['yk_'+k] for k in ['ink','wood','gold','paper','rose','ivory','light','purple']}
def box(name,loc,size,mat,parent):
 x,y,z=[v/2 for v in size];mesh=bpy.data.meshes.new(name)
 mesh.from_pydata([(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)],[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update()
 uv=mesh.uv_layers.new(name='UVMap')
 for p in mesh.polygons:
  axes=[i for i in range(3) if i!=max(range(3),key=lambda k:abs(p.normal[k]))]
  for li in p.loop_indices:
   v=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]/2,v[axes[1]]/2)
 o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);o.parent=parent;o.location=loc;o.data.materials.append(M[mat]);o.hide_render=True;return o
def group(name,parent,loc,angle=0):
 o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);o.parent=parent;o.location=loc;o.rotation_euler.z=angle;return o
def frame(parent,w,h,z,mat='gold'):
 for x in [-w/2,w/2]:box('finish_frame_vertical',(x,0,z),(.035,.035,h),mat,parent)
 for zz in [z-h/2,z+h/2]:box('finish_frame_horizontal',(0,0,zz),(w,.035,.035),mat,parent)
public={'hotel_lobby','hotel_corridor','dining_room','reading_room','dream_lobby','exhibition_room'}
records=[]
for old in manifest['spaces']:
 s=specs[old['id']];root=bpy.data.objects[s['id']];w,d,h=s['size_m'];rich=s['id'] in public
 before=len(root.children_recursive)
 bpy.context.view_layer.update();occupied=[];inv=root.matrix_world.inverted()
 for child in root.children:
  if child.name.split('.')[0] in {'back','front','left','right','north','south','east','west','ceiling','floor'} or child.name.startswith(('art_','finish_')):continue
  pts=[inv@o.matrix_world@Vector(v) for o in [child]+list(child.children_recursive) if o.type=='MESH' for v in o.bound_box]
  if pts:occupied.append(([min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]))
 # Double wooden base moulding, flush against the wall, no freestanding obstacle.
 for side,length,loc,angle in [('north',w,(0,d/2-.15,0),0),('south',w,(0,-d/2+.15,0),math.pi),('east',d,(w/2-.15,0,0),-math.pi/2),('west',d,(-w/2+.15,0,0),math.pi/2)]:
  axis=0 if side in ('north','south') else 1
  portals=[p['position_blender'][axis] for p in s.get('portals',[]) if p.get('side')==side]
  wall=group('finish_wall_'+side,root,loc,angle)
  count=max(1,int(length/1.5))
  for i in range(count):
   off=-length/2+(i+.5)*length/count
   if any(abs(off-q)<1.1 for q in portals):continue
   if s['id']=='dining_room' and side=='north' and abs(off)<1.55:continue  # original framed central wall light
   # Existing windows, clock, key rack and tall cabinets own their wall areas.
   # Do not install sconces or inset frames over those original meshes.
   worldoff=off if side in ('north','east') else -off
   wallcoord=loc[1-axis];blocked=False
   for lo,hi in occupied:
    if lo[axis]-.22<worldoff<hi[axis]+.22 and lo[1-axis]-.32<wallcoord<hi[1-axis]+.32 and hi[2]>1.35 and lo[2]<2.75:blocked=True;break
   if blocked:continue
   # Upper-wall detail stays above standard doors/windows; never paints a new clue.
   p=group('finish_panel',wall,(off,0,0));pw=length/count-.20
   if rich:
    box('finish_walnut_inset',(0,-.01,.57),(pw,.045,.92),'wood',p)
    frame(p,pw-.12,.72,.57)
    frame(p,pw-.18,min(.58,h-2.55),h-.66)
    box('finish_rosette',(0,-.025,h-.66),(.10,.04,.10),'gold',p).rotation_euler.y=math.pi/4
   for z,thick,mat in [(.10,.10,'wood'),(.19,.022,'gold'),(1.14,.065,'wood'),(1.20,.025,'gold')]:
    box('finish_moulding',(0,-.02,z),(pw+.13,.055,thick),mat,p)
   if rich and i%2==0:
    # High sconces do not introduce floor collision or interactive evidence.
    box('finish_sconce_back',(0,-.06,2.28),(.13,.06,.33),'gold',p)
    box('finish_sconce_arm',(0,-.16,2.20),(.045,.22,.04),'ink',p)
    box('finish_sconce_shade',(0,-.25,2.37),(.20,.15,.23),'light',p)
 # Lamps/ornament at ceiling height, with unobstructed 2.6m head clearance.
 if rich:
  for y in [-d*.22,d*.22]:
   c=group('finish_ceiling_fixture',root,(0,y,h-.15))
   box('finish_ceiling_mount',(0,0,0),(.32,.32,.07),'wood',c)
   for x in [-.45,.45]:
    box('finish_chandelier_arm',(x/2,0,-.14),(.50,.04,.04),'gold',c)
    box('finish_chandelier_shade',(x,0,-.22),(.22,.22,.16),'light',c)
 for o in [root]+list(root.children_recursive):o.hide_render=True
 bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
 for o in [root]+list(root.children_recursive):o.select_set(True)
 bpy.context.view_layer.objects.active=root;dest=OUT/(s['id']+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,export_extras=True,export_apply=True)
 records.append({**old,'file':dest.relative_to(ROOT).as_posix(),'finish_parts_added':len(root.children_recursive)-before,'source_blend':'art/space_v4/full_v2/space_finish_source.blend','runtime_integrated':False})
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(SPACE/'space_finish_source.blend'))
(OUT/'manifest.json').write_text(json.dumps({'status':'33 authored visual finish variants, not additional rooms','base_manifest':'art/space_v4/full_v2/manifest.json','spaces':records,'runtime_integrated':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('INTERIOR_FINISH_COMPLETE',len(records),flush=True)
