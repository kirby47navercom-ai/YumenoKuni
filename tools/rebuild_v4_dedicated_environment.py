"""Bring six later-added sets into the same low-mesh/PBR bank, preserving state IDs."""
from pathlib import Path
import bpy,sys,json,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import build_v4_rebuilt_environment as A
import v4_rebuilt_environment_kit as K
O=R/'art/space_v4/rebuilt_dedicated_v2';(O/'raw').mkdir(parents=True,exist_ok=True)
only=next((set(s.split('=',1)[1].split(','))for s in sys.argv if s.startswith('--only=')),None)
source=O/'dedicated-rebuilt.blend'if only and (O/'dedicated-rebuilt.blend').exists()else R/'art/space_v4/dedicated_v1/dedicated_spaces_source.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));K.setup_materials()
manifest=json.loads((R/'art/space_v4/dedicated_v1/manifest.json').read_text(encoding='utf8'));rows=[]
paint={}
def tinted(key,color):
    signature=(key,tuple(color))
    if signature in paint:return paint[signature]
    m=K.M[key].copy();m.name='rebuilt_dedicated_paint_'+str(len(paint));m['surfaceTint']=list(color)
    b=m.node_tree.nodes.get('Principled BSDF');link=b.inputs['Base Color'].links
    if link:
        source=link[0].from_socket;mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=color;m.node_tree.links.new(source,mix.inputs[1]);m.node_tree.links.new(mix.outputs[0],b.inputs['Base Color'])
    paint[signature]=m;return m
for rec in manifest['spaces']:
    if only and rec['id']not in only:continue
    root=bpy.data.objects[rec['id']];objects=list(root.children_recursive);originalNames={o.name for o in objects};changes=A.replace_props(objects)
    if rec['id']=='souvenir_shop':
        # The source deliberately omitted books: these are toy display shelves.
        # A generic bookshelf replacement must not obscure the actual toy stock.
        A.erase([o for o in root.children_recursive if o.name.startswith('book_row_with_varied_heights')])
    # Keep explicit can/ball/box/towel names: authored prop-state ranges refer to them.
    for o in root.children_recursive:
        if o.type!='MESH':continue
        if any(k in o.name for k in ['vanity_wall_mirror','vanity_mirror_surface','mirror_surface','fixed_mirror']):
            o.data.materials.clear();o.data.materials.append(K.M['mirror']);continue
        for i,m in enumerate(o.data.materials):
            if not m or m.name.startswith('rebuilt_'):continue
            name=m.name.split('.')[0];role=name.removeprefix('dedicated_');node=o.name.lower()
            if role=='glass':key='glass'
            elif role=='mirror':key='mirror'
            elif 'floor' in node or 'threshold'in node:key='paving'
            elif role in ['wood']:key='wood'
            elif role in ['wine']:key='cloth'
            elif role=='purple':key='lacquer'
            elif role=='gold':key='brass'
            elif role in ['steel','ink','rubber']:key='iron'
            elif role=='leaf':key='leaf'
            elif role=='light':key='light'
            elif role=='white':key='linen'
            else:key='plaster'
            if role in ['red','blue','green']:
                color=m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value[:];o.data.materials[i]=tinted('linen',color)
            else:o.data.materials[i]=K.M[key]
    # Box sofas become a continuous upholstered shell, while retaining their original
    # collider envelope and the authored table/board/box positions in world data.
    if rec['id']=='hotel_rest_lounge':
        sofaParts=[o for o in root.children_recursive if o.name.startswith(('sofa_plinth','sofa_seat','sofa_back','sofa_arm'))];A.erase(sofaParts)
        for x in [-3.5,3.5]:
            sofa=K.root('upholstered_shared_sofa',root);sofa.location=(x,2,0)
            K.soft_body('continuous_upholstered_seat',2.65,.95,.24,'cloth',sofa,(0,-.1,.48))
            K.soft_body('rounded_upholstered_back',2.8,.24,.96,'cloth',sofa,(0,.45,.92))
            for side in [-1,1]:
                K.soft_body('rounded_upholstered_arm',.22,1.08,.48,'cloth',sofa,(side*1.32,-.1,.72))
                for yy in [-.4,.4]:K.tube('turned_sofa_foot',[(side*1.14,yy,.03),(side*1.14,yy,.35)],[.035,.045],'wood',sofa,8)
        shelf=bpy.data.objects.get('play_materials_shelf')
        if shelf:
            pos=shelf.location.copy();A.erase([shelf]);case=K.casework('open_play_materials_case',2.3,.55,1.2,root);case.location=pos-(type(pos)((0,0,.6)))
            for z in [.20,.52,.84]:K.rounded_solid('play_box_support_shelf',2.2,.50,.035,'wood',case,.005,(0,0,z))
    # The chair's back is local +Y. Orient all reused chairs toward their nearest
    # actual table, including both sides of indoor and front-apron seating.
    tables=[o for o in root.children_recursive if o.type=='EMPTY'and o.name.startswith('set_meeting_table')]
    for o in root.children_recursive:
        if o.type!='EMPTY'or not o.name.startswith('set_chair')or not tables:continue
        table=min(tables,key=lambda t:(t.location-o.location).length);delta=table.location-o.location
        if .3<delta.length<4:o.rotation_euler.z=math.atan2(delta.x,-delta.y)
    objects=[root,*root.children_recursive];A.freeze(objects)
    # Preserve the same holes, the collision-only guard and authored object states.
    shown=[o for o in objects if not o.get('metadata_collision_only')and o.type not in ['LIGHT','CAMERA']]
    previous=A.O;A.O=O
    try:row=A.export(shown,rec['id']+'.glb','Assets/Art/explore3d/dedicated/'+rec['id']+'.glb')
    finally:A.O=previous
    row['prefabReplacements']=changes;row['originalSource']=rec['file'];rows.append(row)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'dedicated-rebuilt.blend'),compress=True)
if only and (O/'assembly.json').exists():rows=[a for a in json.loads((O/'assembly.json').read_text())['assets']if Path(a['runtime']).stem not in only]+rows
(O/'assembly.json').write_text(json.dumps({'assets':rows,'worldMetadataChanged':False,'stateObjectNamesPreserved':True},indent=2)+'\n')
print('DEDICATED_REBUILT',len(rows),flush=True)
