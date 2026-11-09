"""Original playable-space props for the authored minigame art kit; not game logic."""
from pathlib import Path
import os,json,math
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/minigames_v4';O.mkdir(parents=True,exist_ok=True)
os.environ['V4_SPACE_OUT']='art/space_v4/minigames_v4';os.environ['V4_SPACE_PREVIEW']='Game/Saved/v4-minigame-art';os.environ['V4_SPACE_TEXTURED']='0'
source=(R/'tools/build_v4_space_assets.py').read_text(encoding='utf8');exec(source[:source.index('\ndef floor():')],globals())
records=[]
def export(r,role,ports=None,animation=None):
 bpy.ops.object.select_all(action='DESELECT')
 for o in [r]+list(r.children_recursive):o.select_set(True)
 bpy.context.view_layer.objects.active=r;p=O/(r.name+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(p),export_format='GLB',use_selection=True,export_extras=True,export_apply=True,export_animations=True)
 records.append({'id':r.name,'file':p.relative_to(R).as_posix(),'role':role,'ports':ports or [],'animation':animation,'axes':'source BlenderZ-up -> glTFY-up','unit':'meters','pivot':'root origin','runtime_integrated':False})
 return r

r=root('drive_taxi');cube('lower_body',(0,0,.55),(1.82,3.65,.48),'purple',r,.16);cube('upper_body',(0,-.02,.87),(1.76,3.48,.39),'ivory',r,.14)
cube('cabin_frame',(0,.03,1.29),(1.50,1.72,.64),'ink',r,.16);cube('roof',(0,.03,1.68),(1.48,1.68,.11),'ivory',r,.08)
for x in [-.756,.756]:
 cube('side_window',(x,.05,1.39),(.024,1.31,.39),'glass',r,.025);cube('door_divider',(x,0,1.28),(.036,.045,.70),'gold',r,.005)
 cube('door_handle',(x*1.18,.43,.98),(.03,.19,.045),'ink',r,.01)
cube('windscreen',(0,-.85,1.36),(1.29,.04,.41),'glass',r,.04);cube('rear_screen',(0,.91,1.36),(1.28,.04,.41),'glass',r,.04)
for y in [-1.77,1.77]:
 cube('bumper',(0,y,.55),(1.78,.14,.18),'ink',r,.04)
 for x in [-.58,.58]:cube('lamp',(x,y*1.014,.84),(.37,.035,.18),'light' if y<0 else 'rose',r,.035)
for x in [-.89,.89]:
 for y in [-1.13,1.13]:
  wheel=empty('wheel',r,(x,y,.40));t=cyl('tire',(0,0,0),.37,.20,'ink',wheel,32);t.rotation_euler.y=math.pi/2;t=cyl('hub',(math.copysign(.105,x),0,0),.19,.035,'gold',wheel,24);t.rotation_euler.y=math.pi/2
  wheel.rotation_euler.x=0;wheel.keyframe_insert('rotation_euler',frame=1);wheel.rotation_euler.x=math.tau;wheel.keyframe_insert('rotation_euler',frame=25)
for x in [-.40,.40]:cube('seat',(x,.23,1.01),(.60,.62,.15),'rose',r,.10)
cube('blank_roof_sign',(0,0,1.85),(.66,.24,.25),'ivory',r,.045)
export(r,'original stylized four-wheel taxi; labels/question text separate',animation={'name':'wheel_cycle','frames':[1,25],'loop':True,'fps':24,'visual_only':True})

def road(ident,turn=0):
 r=root(ident);length=12;w=6
 if turn==0:
  cube('asphalt',(0,6,-.10),(w,length,.20),'ink',r,.02)
  for x in [-2.83,2.83]:cube('edge_stripe',(x,6,.012),(.10,length,.024),'ivory',r,.002)
  for y in [1,4,7,10]:cube('lane_dash',(0,y,.016),(.10,1.4,.026),'gold',r,.002)
  ports=[{'position':[0,0,0],'heading':0},{'position':[0,12,0],'heading':0}]
 else:
  radius=10;steps=24
  for i in range(steps):
   a=i*math.pi/2/steps;b=(i+1)*math.pi/2/steps
   v=[(turn*(radius+q)*math.cos(t)-turn*radius,(radius+q)*math.sin(t),z) for z in [-.2,0] for q,t in [(-w/2,a),(w/2,a),(w/2,b),(-w/2,b)]]
   mesh=bpy.data.meshes.new('curve_tile');mesh.from_pydata(v,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update();o=bpy.data.objects.new('curve_tile',mesh);scene.collection.objects.link(o);o.parent=r;o.data.materials.append(M['ink'])
   for off in [-w/2+.15,w/2-.15]:bar('curve_edge',(turn*(radius+off)*math.cos(a)-turn*radius,(radius+off)*math.sin(a),.015),(turn*(radius+off)*math.cos(b)-turn*radius,(radius+off)*math.sin(b),.015),.045,'ivory',r)
  ports=[{'position':[0,0,0],'heading':0},{'position':[-turn*10,10,0],'heading':turn*90}]
 return export(r,'road art module; connect with declared root ports, no collision/score rules',ports)
road('road_straight');road('road_curve_left',1);road('road_curve_right',-1)
r=root('road_split')
# One continuous concave slab eliminates the coplanar intersections of three boxes.
outline=[(-3,-2),(3,-2),(3,1),(7.8,8.5),(2.6,11.5),(0,7),(-2.6,11.5),(-7.8,8.5),(-3,1)]
n=len(outline);verts=[(x,y,z) for z in [-.2,0] for x,y in outline]
faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
mesh=bpy.data.meshes.new('continuous_fork');mesh.from_pydata(verts,[],faces);mesh.update();ob=bpy.data.objects.new('continuous_fork',mesh);scene.collection.objects.link(ob);ob.parent=r;mesh.materials.append(M['ink'])
for i,(a,b) in enumerate(zip(outline,outline[1:]+outline[:1])):
 if i not in [0,3,6]:bar('edge_stripe',(*a,.02),(*b,.02),.045,'ivory',r)
for sign in [-1,1]:
 for y in [3,5,7,9]:
  o=cube('guide_dash',(sign*(y-1)*.578,y,.025),(.11,.8,.024),'gold',r,.002);o.rotation_euler.z=-sign*math.radians(30)
export(r,'single connected branching road slab; no coplanar overlap',[{'position':[0,-2,0],'heading':0},{'position':[-5.2,10,0],'heading':30},{'position':[5.2,10,0],'heading':-30}])
r=root('road_barrier');
for x in [-1.5,1.5]:cube('foot',(x,0,.12),(.45,.65,.24),'ink',r);cube('post',(x,0,.75),(.15,.16,1.3),'steel',r)
cube('beam',(0,0,1.05),(3.6,.16,.45),'ivory',r,.04)
for x in [-1.3,-.65,0,.65,1.3]:o=cube('stripe',(x,-.09,1.05),(.24,.015,.40),'purple',r,.001);o.rotation_euler.y=-.3
export(r,'visible road obstacle silhouette; physics delegated to game')
for ident,mat in [('question_cube','ivory'),('mindmine_violet','purple'),('mindmine_ivory','paper'),('mindmine_wine','rose')]:
 r=root(ident);cube('core',(0,0,.5),(.94,.94,.94),mat,r,.055)
 for x in [-.47,.47]:
  for y in [-.47,.47]:bar('ink_edge',(x,y,.04),(x,y,.96),.016,'ink',r)
 for z in [.04,.96]:
  for y in [-.47,.47]:bar('ink_edge',(-.47,y,z),(.47,y,z),.016,'ink',r)
  for x in [-.47,.47]:bar('ink_edge',(x,-.47,z),(x,.47,z),.016,'ink',r)
 export(r,'independent selectable cube; text/hidden picture and answer remain separate')
r=root('drive_answer_gate')
for x in [-2.4,2.4]:cube('post',(x,0,1.55),(.16,.20,3.1),'ink',r)
cube('blank_sign',(0,0,2.8),(5.15,.18,.82),'ivory',r,.04);cube('sign_inset',(0,-.105,2.8),(4.70,.025,.57),'purple',r,.01);export(r,'answer lane gate; literal option text rendered by engine')
r=root('drive_passenger_token');cyl('base',(0,0,.06),.43,.12,'ink',r,32);cyl('body',(0,0,.69),.23,.85,'purple',r,24)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=.27,location=(0,0,1.32));o=bpy.context.object;o.name='blank_sculpted_head';o.parent=r;o.data.materials.append(M['ivory'])
for x in [-.30,.30]:bar('arm',(x*.7,0,1.04),(x,0,.58),.08,'ivory',r)
export(r,'original abstract question passenger sculpture, not a story character or human model')
r=root('anagram_orb');bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=.48,location=(0,0,0));o=bpy.context.object;o.parent=r;o.name='orb';o.data.materials.append(M['glass'])
for axis in [0,1]:
 for i in range(32):
  a=i*math.tau/32;b=(i+1)*math.tau/32
  x=(.50*math.cos(a),.50*math.sin(a),0);y=(.50*math.cos(b),.50*math.sin(b),0)
  if axis:x=(x[0],0,x[1]);y=(y[0],0,y[1])
  bar('orb_band',x,y,.012,'gold',r)
export(r,'3D letter orb; billboard glyph and selection collider authored separately')
r=root('comic_page_stand');cube('back',(0,0,.85),(2.2,.13,1.6),'wood',r,.04);cube('blank_page',(0,-.08,.85),(2.04,.025,1.45),'paper',r,.01);export(r,'comic page physical display, texture atlas can be supplied at runtime')
scene.frame_set(1);scene.render.fps=24
bpy.ops.wm.save_as_mainfile(filepath=str(O/'minigame_art_source.blend'))
(O/'manifest.json').write_text(json.dumps({'source':'original authored geometry; no V3 meshes','assets':records,'runtime_integrated':False,'material_policy':'own ivory/violet/wine/gold PBR palette, no borrowed textures','claims_excluded':['driving physics','question timing','collision/route correctness','game performance acceptance']},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
# Contact render has real depth/occlusion rather than a debug wireframe.
from mathutils import Vector
pre=R/'Game/Saved/v4-minigame-art';pre.mkdir(parents=True,exist_ok=True)
bpy.ops.object.camera_add(location=(7,-9,6));cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=8;cam.rotation_euler=(Vector((0,0,.6))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES';scene.cycles.samples=20;scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
if scene.world is None:scene.world=bpy.data.worlds.new('minigame_preview_world')
scene.world.color=(.25,.25,.25);bpy.ops.object.light_add(type='AREA',location=(2,-4,7));lamp=bpy.context.object;lamp.data.energy=1100;lamp.data.size=7
for a in records:
 for o in scene.objects:o.hide_render=True
 obj=bpy.data.objects[a['id']]
 for o in [obj]+list(obj.children_recursive):o.hide_render=False
 cam.hide_render=False;lamp.hide_render=False
 if a['id'].startswith('road_') and a['id']!='road_barrier':cam.data.ortho_scale=25;cam.location=(13,-10,17);target=(0,5,0)
 elif a['id']=='drive_answer_gate':cam.data.ortho_scale=9;cam.location=(7,-9,6);target=(0,0,1.5)
 else:cam.data.ortho_scale=6;cam.location=(6,-8,5);target=(0,0,.7)
 cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(pre/(a['id']+'.png'));bpy.ops.render.render(write_still=True)
print('MINIGAME_ART_COMPLETE',len(records),flush=True)
