"""Blender facility architecture and physical printed signs, no gameplay edits."""
import bpy, math, json
from pathlib import Path
import v4_rebuilt_environment_kit as K
from build_v4_facility_identity import family,PALETTE
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/facility_identity_v1'
IDENTITY=json.loads((O/'manifest.json').read_text(encoding='utf8'))
def setup():
    for key,path,pixel in [('facility_sign','facility-signs.png',False),('room_face','room-faces.png',True)]:
        file=O/path
        if not file.exists():continue
        m=bpy.data.materials.new('identity_'+key);m.use_nodes=True;m.use_backface_culling=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Roughness'].default_value=.74;b.inputs['Specular IOR Level'].default_value=.12
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(file),check_existing=False);tex.image.pack();tex.interpolation='Closest'if pixel else 'Linear';tex.extension='EXTEND';m.node_tree.links.new(tex.outputs['Color'],b.inputs['Base Color']);K.M[key]=m
        m.node_tree.links.new(tex.outputs['Color'],b.inputs['Emission Color']);b.inputs['Emission Strength'].default_value=.35 if pixel else .20
    for kind,c in PALETTE.items():
        rgb=[int(c[i:i+2],16)/255 for i in [1,3,5]];m=K.M['plaster'].copy();m.name='identity_wall_'+kind;m['surfaceTint']=[*rgb,1];K.M['identity_'+kind]=m
        bs=m.node_tree.nodes.get('Principled BSDF');source=bs.inputs['Base Color'].links[0].from_socket;tint=m.node_tree.nodes.new('ShaderNodeMixRGB');tint.name='source_identity_tint';tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=(*rgb,1);m.node_tree.links.new(source,tint.inputs[1]);m.node_tree.links.new(tint.outputs[0],bs.inputs['Base Color'])
def plate(ident,parent,loc,rotation=0,width=2.4):
    # Superseded by user direction: no facility names on the 3D structures.
    return None

def panel(name,rect,size,w,h,material,parent,loc,rotation):
    r=K.root(name,parent);r.location=loc;r.rotation_euler.z=rotation
    K.rounded_solid('formed_sign_backing',w+.065,.035,h+.065,'iron',r,.012)
    obj=K.mesh('printed_'+name,[(-w/2,-.024,-h/2),(w/2,-.024,-h/2),(w/2,-.024,h/2),(-w/2,-.024,h/2)],[(0,1,2,3)],material,r)
    # BMesh's outward-normal inference is ambiguous for an isolated open sheet.
    # The printed side is authored -Y, matching the physical backing's front.
    for face in obj.data.polygons:
        if face.normal.y>0:face.flip()
    obj.data.update()
    x,y,ww,hh=rect;u0=x/size[0];u1=(x+ww)/size[0];v0=1-(y+hh)/size[1];v1=1-y/size[1]
    for f in obj.data.polygons:
        for li in f.loop_indices:
            co=obj.data.vertices[obj.data.loops[li].vertex_index].co;obj.data.uv_layers[0].data[li].uv=(u0 if co.x<0 else u1,v0 if co.z<0 else v1)
    return r
def guest_badges(parent=None):
    assert 'faceRects'in IDENTITY,'Generate and inspect the 16 pixel heads first'
    result=[]
    for room,slug in IDENTITY['roomOwners'].items():
        i=int(room[-2:])-1;y=-24.5+7*(i//2);side=-1 if i%2==0 else 1
        # Corridor door face is at +/-2m; put the badge on the leaf, facing inward.
        obj=panel('door_badge_'+room,IDENTITY['faceRects'][slug],IDENTITY['faceAtlasSize'],.38,.38,'room_face',parent,(side*1.94,y,1.80),-side*math.pi/2)
        obj['guestRoom']=room;obj['character']=slug;obj['pixelDimensions']=[64,64];result.append({'room':room,'character':slug,'positionBlender':list(obj.location),'widthMetres':.38})
    return result
def front_wall(parent,w,d,h,windows,material):
    c=bpy.data.curves.new('functional_front_openings','CURVE');c.dimensions='2D';c.fill_mode='BOTH';c.extrude=.1;c.resolution_u=1
    def loop(points):
        s=c.splines.new('POLY');s.points.add(len(points)-1)
        for p,(x,z)in zip(s.points,points):p.co=(x,z,0,1)
        s.use_cyclic_u=True
    loop([(-w/2,0),(-.7,0),(-.7,2.5),(.7,2.5),(.7,0),(w/2,0),(w/2,h),(-w/2,h)])
    for x,ww,b,t in windows:
        loop([(x-ww/2,b),(x-ww/2,t),(x+ww/2,t),(x+ww/2,b)])
        K.frame_ring('structural_window_reveal',ww+.10,t-b+.10,.05,.24,'iron',parent,(x,-d/2+.02,(b+t)/2))
        K.mesh('recessed_window_glass',[(x-ww/2,-d/2+.14,b),(x+ww/2,-d/2+.14,b),(x+ww/2,-d/2+.14,t),(x-ww/2,-d/2+.14,t)],[(0,1,2,3)],'glass',parent)
    obj=bpy.data.objects.new('functional_front_openings',c);bpy.context.scene.collection.objects.link(obj);graph=bpy.context.evaluated_depsgraph_get();data=bpy.data.meshes.new_from_object(obj.evaluated_get(graph));bpy.data.objects.remove(obj,do_unlink=True)
    for v in data.vertices:x,z,depth=v.co;v.co=(x,-d/2+.1+depth,z)
    obj=bpy.data.objects.new('pierced_facility_front',data);bpy.context.scene.collection.objects.link(obj);obj.parent=parent;data.materials.append(K.M[material])
    K.frame_ring('accessible_entrance_reveal',1.6,2.7,.1,.24,'stone',parent,(0,-d/2+.02,1.25),inner_size=(1.4,2.5))
def building(ident,w,d,h):
    import v4_facility_architecture as architecture,sys
    if ident in architecture.PLANS:return architecture.build(ident,w,d,h,sys.modules[__name__])
    kind=family(ident);r=K.house(w,d,h,'mansard'if kind=='hotel'else 'gable')
    # Preserve the original continuous U wall; replace front openings and roof.
    for o in list(r.children):
        if o.name.startswith(('pierced_facade','recessed_window_reveal','inset_glazing','continuous_entrance_reveal','coherent_')):bpy.data.objects.remove(o,do_unlink=True)
    mat='identity_'+kind
    for o in r.children:
        if o.type=='MESH':o.data.materials.clear();o.data.materials.append(K.M[mat])
    if kind in ['medical','utility']:windows=[(x,min(w*.20,1.8),1.65,min(2.65,h-.35))for x in [-w*.30,w*.30]]
    elif kind in ['dining','mirror']:windows=[(x,min(w*.26,3),.45,min(2.65,h-.3))for x in [-w*.29,w*.29]]
    elif kind=='theatre':windows=[(x,min(w*.16,2),.9,min(3.35,h-.30))for x in [-w*.33,w*.33]]
    elif kind=='archive':windows=[(x,.70,.75,min(2.65,h-.3))for x in [-w*.36,-w*.22,w*.22,w*.36]]
    else:windows=[(x,min(w*.21,2.2),.8,min(2.65,h-.3))for x in [-w*.30,w*.30]]
    if h>5.8:windows +=[(x,1.5,4.05,h-.55)for x in [-w*.3,0,w*.3]]
    front_wall(r,w,d,h,windows,mat)
    e=h+.08;xx=w/2+.28
    if kind in ['medical','civic','archive']:
        roof=[(-xx,e),(-xx,e+.25),(xx,e+.25),(xx,e)];style='flat_parapet'
        # Single continuous folded parapet, rather than stacks of trim cubes.
        for side in [-1,1]:K.tube('parapet_coping',[(side*xx,-d/2-.28,e+.32),(side*xx,d/2+.28,e+.32)],[.065]*2,'stone',r,4)
    elif kind=='utility':roof=[(-xx,e),(-xx,e+.16),(xx,e+.85),(xx,e+.69)];style='mono_pitch_service'
    elif kind=='theatre':roof=[(-xx*math.cos(i*math.pi/16),e+2.2*math.sin(i*math.pi/16))for i in range(17)]+[(xx,e-.12),(-xx,e-.12)];style='vaulted_auditorium'
    elif kind=='mirror':roof=[(-xx,e),(-xx*.45,e+1.15),(0,e+.55),(xx*.45,e+1.15),(xx,e),(xx,e-.12),(-xx,e-.12)];style='faceted_glass_gallery'
    elif kind=='hotel':roof=[(-xx,e),(-xx+.65,e+1.1),(-xx+1.1,e+1.4),(xx-1.1,e+1.4),(xx-.65,e+1.1),(xx,e),(xx,e-.12),(-xx,e-.12)];style='mansard_hotel'
    else:roof=[(-xx,e),(0,e+1.1),(xx,e),(xx,e-.12),(0,e+.98),(-xx,e-.12)];style='pitched_dining'
    roofObj=K.section('purpose_'+style,roof,d+.56,'glass'if kind=='mirror'else'iron'if kind in ['utility','medical']else'roof',r);roofObj.rotation_euler.z=math.pi/2
    if kind in ['medical','dining','hotel','civic']:
        canopy=K.section('entrance_weather_canopy',[(-.22,0),(.85,0),(.85,.09),(-.22,.20)],min(4.4,w*.66),'iron',r);canopy.location=(0,-d/2-.60,2.72)
        for side in [-1,1]:K.tube('canopy_structural_post',[(side*min(2,w*.30),-d/2-.82,.03),(side*min(2,w*.30),-d/2-.82,2.72)],[.045]*2,'iron',r,8)
    if kind=='theatre':
        aw=K.section('continuous_theatre_marquee',[(-.2,0),(1.4,0),(1.4,.25),(-.2,.45)],w*.64,'lacquer',r);aw.location=(0,-d/2-.9,2.75)
        for x in [-w*.28,w*.28]:K.tube('proscenium_column',[(x,-d/2-.15,0),(x,-d/2-.15,h-.15)],[.14]*2,'stone',r,8)
    if kind=='utility':
        # Connected bent service stack; small louvers remain surface detail.
        K.tube('extraction_duct',[(w*.30,d*.15,h-.4),(w*.30,d*.15,h+1.35),(w*.30,d*.15-.4,h+1.55)],[.24]*3,'iron',r,10)
        vent=K.frame_ring('service_louver_surround',1.4,.7,.07,.14,'iron',r,(-w*.30,-d/2-.04,h-.43))
    if kind=='archive':
        for x in [-w*.40,w*.40]:K.tube('archive_stone_pier',[(x,-d/2-.15,.05),(x,-d/2-.15,h)],[.15]*2,'stone',r,6)
    plate(ident,r,(0,-d/2-(1.125 if kind=='theatre'else .16),min(h-.22,3.05)),width=min(3.4,w*.56))
    r.name='purpose_building_'+ident;r['facilityIdentity']=ident;r['architectureFamily']=kind;r['roofStyle']=style;r['door_clear_width']=1.4;r['door_clear_height']=2.5
    return r
