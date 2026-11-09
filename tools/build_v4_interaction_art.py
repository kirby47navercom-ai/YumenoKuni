"""Animated original doors/chest/hatch; no gameplay, source-game assets or processes."""
from pathlib import Path
import os,math,json,ast
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/interactions_v4';O.mkdir(parents=True,exist_ok=True)
os.environ['V4_SPACE_OUT']='art/space_v4/interactions_v4';os.environ['V4_SPACE_PREVIEW']='Game/Saved/v4-interaction-art';os.environ['V4_SPACE_TEXTURED']='0'
s=(R/'tools/build_v4_space_assets.py').read_text(encoding='utf8');exec(s[:s.index('\ndef floor():')],globals())
for node in ast.parse(s).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['door','chest']:exec(compile(ast.Module(body=[node],type_ignores=[]),str(R/'tools/build_v4_space_assets.py'),'exec'),globals())
scene.render.fps=24;scene.frame_end=96;records=[]

def linear(o):
 if o.animation_data and o.animation_data.action:
  act=o.animation_data.action
  for layer in act.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for curve in bag.fcurves:
      for key in curve.keyframe_points:key.interpolation='LINEAR'

def animated_angle(o,axis,states):
 for f,deg in states:o.rotation_euler[axis]=math.radians(deg);o.keyframe_insert('rotation_euler',frame=f)
 linear(o)

def save(r,meaning,events):
 bpy.ops.object.select_all(action='DESELECT')
 for o in [r]+list(r.children_recursive):o.select_set(True);linear(o)
 bpy.context.view_layer.objects.active=r;p=O/(r.name+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(p),export_format='GLB',use_selection=True,export_extras=True,export_apply=True,export_animations=True,export_frame_range=True)
 records.append({'id':r.name,'file':p.relative_to(R).as_posix(),'role':meaning,'clip':{'frames':[1,96],'fps':24,'events':events,'loop':False,'runtime_trigger':'door/chest/hatch interaction controller, animation itself never unlocks a route'},'source_coordinate':'BlenderZ-up -> glTFY-up; meters','runtime_integrated':False})

r=door();r.name='door_hinged_1m_animated';p=next(x for x in r.children if x.name.startswith('hinge'));animated_angle(p,2,[(1,0),(31,95),(60,95),(90,0),(96,0)]);save(r,'same original hinged-door leaf/pivot; open-hold-close',{'closed':[1,90,96],'open':31,'hold_end':60})
r=chest();r.name='blue_props_chest_animated';lid=next(x for x in r.children if x.name.startswith('lid_hinge'));animated_angle(lid,0,[(1,0),(9,0),(37,-105),(60,-105),(88,0),(96,0)])
for latch in [x for x in r.children if x.name.startswith('outside_latch')]:animated_angle(latch,0,[(1,0),(8,65),(88,65),(96,0)])
# Two articulated stays, each constructed as two rigid bars; sample TRS exports real motion.
for sign in [-1,1]:
 rods=[cyl('lid_stay_link',(0,0,0),.014,1,'steel',r,12) for _ in range(2)]
 for f in range(1,97):
  scene.frame_set(f);a=Vector((sign*.79,.28,.65));b=lid.matrix_local@Vector((sign*.79,-.31,0));d=b-a;mid=(a+b)/2;perp=Vector((0,-d.z,d.y)).normalized();knee=mid+perp*math.sqrt(max(0,.55**2-d.length_squared/4))
  for rod,start,end in zip(rods,[a,knee],[knee,b]):
   delta=end-start;rod.location=(start+end)/2;rod.rotation_mode='QUATERNION';rod.rotation_quaternion=delta.to_track_quat('Z','Y');rod.scale.z=delta.length
   for path in ['location','rotation_quaternion','scale']:rod.keyframe_insert(path,frame=f)
save(r,'same blue chest:2outside latches,2moving lid stays, no inner lock',{'latches_released':8,'lid_open':37,'hold_end':60,'lid_closed':88,'latched':96})
r=root('maintenance_hatch_animated');
for x in [-.78,.78]:cube('fixed_frame',(x,0,.035),(.08,1.02,.07),'steel',r,.008)
for y in [-.5,.5]:cube('fixed_frame',(0,y,.035),(1.64,.08,.07),'steel',r,.008)
hinge=empty('hatch_hinge',r,(0,.44,.07));cube('hatch_leaf',(0,-.44,.025),(1.45,.88,.05),'steel',hinge,.012)
for x in [-.55,.55]:bar('grip',(x,-.48,.1),(x,-.63,.1),.025,'ink',hinge)
latch=empty('external_latch_pivot',r,(.69,-.45,.12));cube('latch_arm',(-.1,0,0),(.30,.055,.055),'gold',latch,.006)
animated_angle(latch,2,[(1,0),(9,95),(88,95),(96,0)]);animated_angle(hinge,0,[(1,0),(10,0),(37,-100),(60,-100),(88,0),(96,0)]);save(r,'normal existing maintenance hatch with externally operated latch; no self-lock inside',{'external_latch_released':9,'open':37,'closed':88,'latched':96})
r=root('elevator_doors_animated')
for x in [-1.45,1.45]:cube('jamb',(x,0,1.5),(.15,.32,3),'ink',r)
cube('header',(0,0,2.95),(3.05,.32,.15),'ink',r)
for sign in [-1,1]:
 leaf=empty('sliding_leaf',r,(sign*.66,0,0));cube('metal_panel',(0,0,1.43),(1.3,.10,2.85),'steel',leaf,.018);cube('gold_edge',(-sign*.62,-.065,1.43),(.035,.025,2.85),'gold',leaf,.003)
 for f,x in [(1,sign*.66),(31,sign*1.96),(60,sign*1.96),(90,sign*.66),(96,sign*.66)]:leaf.location.x=x;leaf.keyframe_insert('location',frame=f)
save(r,'two independent sliding panels, local-horizontal translation only',{'open':31,'hold_end':60,'closed':90})
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(O/'interaction_source.blend'))
(O/'manifest.json').write_text(json.dumps({'source':'authored original mesh/pivots, no original-game extraction','assets':records,'runtime_integrated':False,'claims_excluded':['door collision','route unlock','latch interlock controller','gameplay event timing']},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
pre=R/'Game/Saved/v4-interaction-art';pre.mkdir(parents=True,exist_ok=True)
if scene.world is None:scene.world=bpy.data.worlds.new('interaction_preview_world')
scene.world.color=(.3,.3,.3);bpy.ops.object.camera_add(location=(4,-5,4));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=5.4;cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
bpy.ops.object.light_add(type='AREA',location=(2,-4,7));lamp=bpy.context.object;lamp.data.energy=1500;lamp.data.size=5;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
for a in records:
 obj=bpy.data.objects[a['id']]
 for ob in scene.objects:ob.hide_render=True
 for ob in [obj]+list(obj.children_recursive):ob.hide_render=False
 lamp.hide_render=False;cam.hide_render=False
 for frame in [1,37,60,96]:scene.frame_set(frame);scene.render.filepath=str(pre/f'{a["id"]}_{frame:03d}.png');bpy.ops.render.render(write_still=True)
print('INTERACTION_ART_COMPLETE',len(records),flush=True)
