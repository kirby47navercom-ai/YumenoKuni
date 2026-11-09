"""Original scene-scale investigation objects, independent from their 2D inspection pictures."""
from pathlib import Path
import os,json,math
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/inspection_props_v4';O.mkdir(parents=True,exist_ok=True)
os.environ['V4_SPACE_OUT']='art/space_v4/inspection_props_v4';os.environ['V4_SPACE_PREVIEW']='Game/Saved/v4-inspection-props';os.environ['V4_SPACE_TEXTURED']='0'
s=(R/'tools/build_v4_space_assets.py').read_text(encoding='utf8');exec(s[:s.index('\ndef floor():')],globals());records=[]
mat=bpy.data.materials.new('own_clear_glass');mat.use_nodes=True;bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.68,.78,.80,.28);bs.inputs['Alpha'].default_value=.28;bs.inputs['Roughness'].default_value=.12;bs.inputs['Transmission Weight'].default_value=.75;bs.inputs['IOR'].default_value=1.46;mat.surface_render_method='DITHERED';M['clear_glass']=mat
def ring(name,center,radius,tube,material,parent,plane='XY',arc=math.tau,start=0):
 for i in range(32):
  a=start+i*arc/32;b=start+(i+1)*arc/32
  def pos(t):
   c=(radius*math.cos(t),radius*math.sin(t),0)
   if plane=='XZ':c=(c[0],0,c[1])
   return tuple(center[k]+c[k] for k in range(3))
  bar(name,pos(a),pos(b),tube,material,parent)
def export(r,role,notes=None):
 bpy.ops.object.select_all(action='DESELECT')
 for x in [r]+list(r.children_recursive):x.select_set(True)
 bpy.context.view_layer.objects.active=r;p=O/(r.name+'.glb');bpy.ops.export_scene.gltf(filepath=str(p),export_format='GLB',use_selection=True,export_extras=True,export_apply=True)
 records.append({'id':r.name,'file':p.relative_to(R).as_posix(),'role':role,'unit':'meters','source_axes':'BlenderZ-up -> glTFY-up','pivot':'root ground center unless documented','notes':notes or {},'runtime_integrated':False});return r
r=root('new_clear_glass');N=48;profile=[(.032,0),(.034,.004),(.038,.104),(.036,.109),(.033,.104),(.030,.012)]
verts=[(rad*math.cos(i*math.tau/N),rad*math.sin(i*math.tau/N),z) for rad,z in profile for i in range(N)]
faces=[]
for k in range(len(profile)-1):
 for i in range(N):faces.append((k*N+i,k*N+(i+1)%N,(k+1)*N+(i+1)%N,(k+1)*N+i))
faces.append(tuple(reversed(range(N))));mesh=bpy.data.meshes.new('hollow_glass_mesh');mesh.from_pydata(verts,[],faces);mesh.update();ob=bpy.data.objects.new('hollow_glass',mesh);scene.collection.objects.link(ob);ob.parent=r;mesh.materials.append(M['clear_glass']);ring('rim',(0,0,.108),.035,.0009,'clear_glass',r)
export(r,'one plain hollow NEW glass tumbler; duplicate exactly6 for unpacked set',{'material':'alpha blend +KHR_materials_transmission; HB transparency support must be checked during integration','story':'15a9 six-piece NEW glass pack; personal cup means selected serving, not seventh heirloom mug'})
r=root('ordinary_teapot');cyl('body',(0,0,.095),.085,.16,'steel',r,48);cyl('lid',(0,0,.184),.088,.014,'steel',r,48);cyl('knob',(0,0,.205),.021,.03,'ink',r,24);bar('spout',(.06,0,.10),(.15,0,.16),.018,'steel',r);ring('handle',(-.10,0,.10),.065,.009,'ink',r,'XZ',math.pi*1.55,math.pi*.225);export(r,'ordinary communal teapot, no ingredient/dosing inference')
def tube(parent,loc=(0,0,0)):
 x,y,z=loc;cyl('closed_tube',(x,y,z+.055),.012,.10,'ivory',parent,24);cyl('sealed_cap',(x,y,z+.112),.014,.018,'ink',parent,24)
r=root('sealed_fictional_sample');tube(r);export(r,'closed fictional sample, label rendered separately',{'no_real_chemical_recipe_or_quantity':True})
for count in [6,5]:
 r=root('sample_rack_'+str(count));cube('tray',(0,0,.012),(.17,.13,.024),'steel',r,.008)
 for i in range(count):tube(r,((i%3-1)*.05,(i//3-.5)*.05,.025))
 export(r,'sealed fictional sample rack, exact count variant '+str(count),{'count':count,'no_invented_labels':True})
r=root('right_wrist_brace');N=30;L=12;verts=[]
for row in range(L+1):
 y=-.15+row*.30/L
 for i in range(N+1):
  a=-math.pi*.82+i*math.pi*1.64/N;rad=.044+row/L*.009;verts.append((rad*math.sin(a),y,.06+rad*math.cos(a)))
faces=[]
for row in range(L):
 for i in range(N):
  a=-math.pi*.82+(i+.5)*math.pi*1.64/N
  if row>=9 and 1.0<a<1.9:continue # actual thumb opening, local+X at wrist end
  n=row*(N+1)+i;faces.append((n,n+1,n+N+2,n+N+1))
mesh=bpy.data.meshes.new('brace_surface');mesh.from_pydata(verts,[],faces);mesh.update();ob=bpy.data.objects.new('brace_fabric',mesh);scene.collection.objects.link(ob);ob.parent=r;mesh.materials.append(M['ivory']);mod=ob.modifiers.new('fabric_thickness','SOLIDIFY');mod.thickness=.002
for y in [-.09,.02]:
 for i in range(24):
  a=i*math.tau/24;b=(i+1)*math.tau/24;bar('velcro_band',(.055*math.cos(a),y,.06+.055*math.sin(a)),(.055*math.cos(b),y,.06+.055*math.sin(b)),.004,'ink',r)
export(r,'right-wrist clinical brace with thumb opening and2straps',{'forearm_axis':'localY','thumb_port':'local+X,localY>0.075; scene binds RIGHT hand only','no_hand_mesh':True})
r=root('opaque_sealed_envelope');cube('paper_body',(0,0,.002),(.20,.125,.004),'paper',r,.001);mesh=bpy.data.meshes.new('flap_mesh');mesh.from_pydata([(-.10,.0625,.004),(.10,.0625,.004),(0,-.018,.0045)],[],[(0,1,2)]);mesh.update();ob=bpy.data.objects.new('closed_flat_flap',mesh);scene.collection.objects.link(ob);ob.parent=r;mesh.materials.append(M['ivory']);export(r,'opaque envelope with CLOSED flat flap; no text visibility through it')
r=root('black_blindfold');cube('opaque_cloth',(0,0,.004),(.25,.075,.008),'ink',r,.012)
for side in [-1,1]:bar('tie',(side*.10,0,.009),(side*.22,.045,.009),.006,'ink',r)
export(r,'opaque black eye-cover cloth, no magical glow')
r=root('pink_protected_notebook');cube('pages',(0,0,.018),(.16,.225,.025),'paper',r,.003)
for z in [.003,.033]:cube('cover',(0,0,z),(.172,.237,.009),'rose',r,.003)
cube('spine',(-.082,0,.018),(.012,.237,.036),'rose',r,.003);export(r,'single worn pink notebook; protects recorded state, not observer truth',{'text_on_page':'engine/verified document layer, no fabricated magical proof'})
for count in [1,3]:
 r=root('loose_document_'+str(count))
 for i in range(count):ob=cube('sheet',(i*.004,i*.004,.001+i*.0015),(.21,.297,.001),'paper',r,0);ob.rotation_euler.z=i*.025
 export(r,'independent loose document pages, count'+str(count),{'page_text':'editable verified text layer, not invented full prose'})
r=root('memory_card');cube('black_body',(0,0,.001),(.024,.032,.002),'ink',r,.001)
for i in range(8):cube('contact',(-.009+i*.0026,.010,.0022),(.0016,.008,.0005),'gold',r,.0001)
export(r,'small black memory card; never a playing card')
r=root('closed_camera_bag');cube('fabric_case',(0,0,.10),(.29,.16,.20),'ink',r,.025);cube('closed_flap',(0,-.086,.16),(.30,.025,.10),'wood',r,.015)
for x in [-.085,.085]:cube('buckle',(x,-.105,.12),(.026,.012,.035),'steel',r,.003)
ring('top_handle',(0,0,.215),.055,.009,'ink',r,'XZ',math.pi,0);export(r,'CLOSED wet-camera-bag exterior; camera/card stay inside',{'wetness':'material variant, no open bag/card outside generated'})
r=root('microphone_weighted_base');cyl('heavy_base',(0,0,.022),.155,.044,'ink',r,64);cyl('collar',(0,0,.055),.028,.04,'steel',r,32);export(r,'independent heavy microphone base, separate from pole',{'trace':'localized purple decal supplied separately; ownership never proves actor'})
r=root('broken_connector_loop');ring('broken_arc',(0,0,.008),.024,.004,'ink',r,'XY',math.tau*.78,math.pi*.12);bar('detached_fragment',(.035,.025,.008),(.046,.034,.008),.004,'ink',r);export(r,'broken small black connector and separate fragment, not a whole belt')
r=root('work_marker_scraps')
for i in range(3):ob=cube('marker_piece',((i-1)*.05,0,.002),(.035,.055,.004),'ivory' if i!=1 else 'wood',r,.001);ob.rotation_euler.z=(i-1)*.35
export(r,'ordinary removable route marker scraps; no new code/text')
r=root('retracted_utility_knife');cube('black_core',(0,0,.012),(.036,.145,.024),'ink',r,.008);cube('yellow_shell',(0,0,.018),(.039,.137,.023),'gold',r,.008);cube('slider',(0,.014,.033),(.018,.036,.008),'ink',r,.003);cube('retracted_tip',(0,.071,.018),(.021,.006,.005),'steel',r,.001);export(r,'ordinary utility work knife in RETRACTED inspection pose; no attack mechanics')
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(O/'inspection_props_source.blend'));(O/'manifest.json').write_text(json.dumps({'source':'original authored inspection props','assets':records,'runtime_integrated':False,'no_original_game_meshes':True},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
pre=R/'Game/Saved/v4-inspection-props';pre.mkdir(parents=True,exist_ok=True)
if scene.world is None:scene.world=bpy.data.worlds.new('inspection_preview_world')
scene.world.color=(.4,.4,.4);bpy.ops.object.camera_add(location=(.5,-.7,.65));cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.55;cam.rotation_euler=(Vector((0,0,.065))-cam.location).to_track_quat('-Z','Y').to_euler();bpy.ops.object.light_add(type='AREA',location=(.25,-.4,.9));lamp=bpy.context.object;lamp.data.energy=80;lamp.data.size=.6;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=1000;scene.render.resolution_y=750;scene.render.resolution_percentage=100
for a in records:
 for ob in scene.objects:ob.hide_render=True
 r=bpy.data.objects[a['id']]
 for ob in [r]+list(r.children_recursive):ob.hide_render=False
 cam.hide_render=False;lamp.hide_render=False;scene.render.filepath=str(pre/(a['id']+'.png'));bpy.ops.render.render(write_still=True)
print('INSPECTION_PROPS_COMPLETE',len(records),flush=True)
