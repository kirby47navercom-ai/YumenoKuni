"""Full-HD 16:9 still plates from actual authored 3D geometry, never walkable substitutes."""
import bpy,json,math,os,shutil,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];FINISH=os.environ.get('V4_BG_FINISH')=='1';STYLE=os.environ.get('V4_BG_STYLE')=='1' or FINISH;OUT=ROOT/('art/bg_v4/plates_r4' if FINISH else 'art/bg_v4/plates_r3' if STYLE else 'art/bg_v4/plates');OUT.mkdir(parents=True,exist_ok=True)
if os.environ.get('V4_BG_OUT'):
    OUT=ROOT/os.environ['V4_BG_OUT'];OUT.mkdir(parents=True,exist_ok=True)
SPACE=ROOT/'art/space_v4/full_v2'
manifest=json.loads((SPACE/'manifest.json').read_text(encoding='utf8'));specs={s['id']:s for s in manifest['spaces']}
jobs=[('park_day','exterior','day'),('park_night','exterior','night'),('hotel_lobby_day','hotel_lobby','day'),('hotel_lobby_night','hotel_lobby','night'),('hotel_corridor_day','hotel_corridor','day'),('hotel_corridor_night','hotel_corridor','night'),('dining_day','dining_room','day'),('dining_night','dining_room','night'),('service_lounge_day','service_lounge','day'),('service_lounge_night','service_lounge','night'),('shelter_reception','shelter_reception','interior'),('operating_archive','operating_archive','interior')]
records=json.loads((OUT/'manifest.json').read_text(encoding='utf8'))['assets'] if (OUT/'manifest.json').exists() else []
only=os.environ.get('V4_BG_ONLY')
for ident,space,tod in jobs:
    if only and space!=only:continue
    if STYLE and not FINISH and space=='exterior' and only!='exterior':continue
    source=SPACE/('park_exterior_r2_source.blend' if space=='exterior' else ('space_finish_source.blend' if FINISH else 'space_art_source.blend' if STYLE else 'space_kit_source.blend'))
    if os.environ.get('V4_BG_SOURCE_OVERRIDE'):source=ROOT/os.environ['V4_BG_SOURCE_OVERRIDE']
    bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
    for o in scene.objects:o.hide_render=True
    root=bpy.data.objects['park_exterior_level' if space=='exterior' else space]
    for o in [root]+list(root.children_recursive):o.hide_render=False
    # Keep actual built geometry and one shared camera projection with the 3D contract.
    cam=scene.camera;cam.hide_render=False;cam.data.type='PERSP';cam.data.angle=math.radians(70)
    if space=='exterior':eye=(0,-12,1.65);target=(0,20,3)
    else:
        s=specs[space];c=s['camera']
        if 'eye_blender' in c:eye=c['eye_blender']
        else:
            spawn=c.get('spawn_blender',[0,-s['size_m'][1]/2+1.4,0]);eye=(spawn[0],spawn[1],1.6)
        target=(eye[0],eye[1]+5,1.5)
    cam.location=eye;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background')
    bg.inputs[0].default_value=(.04,.06,.13,1) if tod=='night' else (.43,.55,.66,1)
    bg.inputs[1].default_value=.13 if tod=='night' else .65
    for o in scene.objects:
        if o.type!='LIGHT':continue
        if o.data.type=='SUN':
            o.hide_render=space!='exterior';o.data.energy=.12 if tod=='night' else 2
        elif o.name.startswith('preview_'):o.hide_render=True
    if space!='exterior':
        # Root-local fixtures: lamps from other room collections must stay hidden.
        for o in root.children_recursive:
            if o.type=='LIGHT':
                o.data.energy*=.34 if tod=='night' else .7
                o.data.color=(1,.67,.38) if tod=='night' else (1,.88,.70)
        bpy.ops.object.light_add(type='AREA',location=(eye[0],eye[1]+2,3));light=bpy.context.object;light.data.energy=65 if tod=='night' else 220;light.data.size=5;light.data.color=(1,.66,.4) if tod=='night' else (.80,.88,1)
        # Side daylight washes the room rather than flattening it from the camera.
        if tod=='day':
            bpy.ops.object.light_add(type='AREA',location=(-specs[space]['size_m'][0]*.43,0,2.6));fill=bpy.context.object;fill.data.energy=270;fill.data.size=3;fill.rotation_euler=(Vector((0,0,1))-fill.location).to_track_quat('-Z','Y').to_euler();fill.data.color=(.73,.84,1)
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard';scene.view_settings.look='Medium High Contrast';scene.view_settings.exposure=-.6
    scene.render.use_freestyle=True
    for view in scene.view_layers:
        if view.freestyle_settings.linesets:
            lineset=view.freestyle_settings.linesets[0]
            if lineset.linestyle is None:lineset.linestyle=bpy.data.linestyles.new('yk_plate_ink')
            style=lineset.linestyle;style.color=(.025,.018,.035);style.thickness=.8
    native=OUT/(ident+'.png')
    if native.exists():
        history=ROOT/'Game/Saved/v4-native-render-history';history.mkdir(parents=True,exist_ok=True)
        backup=history/(OUT.name+'_'+ident+'_'+hashlib.sha256(native.read_bytes()).hexdigest()[:16]+'.png')
        if not backup.exists():shutil.copy2(native,backup)
    scene.render.filepath=str(native);bpy.ops.render.render(write_still=True)
    rec={'id':ident,'source':(OUT/(ident+'.png')).relative_to(ROOT).as_posix(),'source_blend':source.relative_to(ROOT).as_posix(),'space':space,'time':tod,'camera_eye_blender':list(eye),'camera_target_blender':list(target),'size':[1920,1080],'tool':'Blender Cycles + Freestyle','intended_use':'static narrative/background plate and CG environment reference only; actual exploration uses 3D meshes','hd_file':f'art/hd_v4/bg/{OUT.name}/{ident}.png','runtime_integrated':False,'visual_status':'not yet accepted'}
    (OUT/(ident+'.json')).write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n',encoding='utf8');records=[r for r in records if r['id']!=ident];records.append(rec)
(OUT/'manifest.json').write_text(json.dumps({'source':'actual authored original 3D scenes, not extracted assets','assets':records},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('BACKGROUND_PLATES_COMPLETE',len(records),flush=True)
