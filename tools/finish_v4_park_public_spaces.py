"""Finish the existing authored parks, without rebuilding the case interiors.

Run only with the owned background Blender CLI. The user's open file is unused.
"""
import bpy,math,json,sys,random,subprocess,shutil
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import v4_rebuilt_environment_kit as K
import build_v4_rebuilt_environment as A
from v4_park_continuity import distant_tree
O=R/'art/space_v4/park_levels_v1';W=R/'Game/Saved/park-levels-20261104/public-space-finish';W.mkdir(exist_ok=True)
before=W/'parks-before.blend'
if not before.exists():shutil.copy2(O/'parks-authoring.blend',before)
bpy.ops.wm.open_mainfile(filepath=str(O/'parks-authoring.blend'))
K.setup_materials()
for key in ['cream','red','blue','violet','enamel','brick','ink','gold','teal']:
    candidates=[m for m in bpy.data.materials if m.name.startswith('park_'+key)]
    if candidates:K.M[key]=candidates[0]
    else:
        base={'cream':'plaster','red':'lacquer','blue':'lacquer','violet':'lacquer','enamel':'stone','brick':'plaster','ink':'iron','gold':'brass','teal':'lacquer'}[key]
        K.M[key]=K.M[base].copy();K.M[key].name='park_'+key
manifest=json.loads((O/'raw-manifest.json').read_text(encoding='utf8'))
plan=json.loads((O/'plan.json').read_text(encoding='utf8'));configs={d['id']:d for d in plan['districts']}
only=next((set(v.split('=',1)[1].split(','))for v in sys.argv if v.startswith('--only=')),None)
proofFile=W/'authoring.json';proof=json.loads(proofFile.read_text(encoding='utf8'))['proof']if proofFile.exists()else[]
baseCollision={a['id']:a['collision']for a in json.loads((O/'manifest.json').read_text(encoding='utf8'))['assets']}
def remove(obj):
    for o in [*reversed(obj.children_recursive),obj]:bpy.data.objects.remove(o,do_unlink=True)
def disk(parent,name,x,y,r,z,mat):
    v=[(x,y,z)]+[(x+r*math.cos(i*math.tau/64),y+r*math.sin(i*math.tau/64),z)for i in range(64)]
    return K.mesh(name,v,[(0,i+1,(i+1)%64+1)for i in range(64)],mat,parent,uv_scale=.30)
def rim(parent,name,x,y,r,z,mat='stone'):
    return K.tube(name,[(x+r*math.cos(i*math.tau/64),y+r*math.sin(i*math.tau/64),z)for i in range(65)],[.07]*65,mat,parent,6)
def plaque(parent,letters):
    # A physical backed sign with a connected frame, rather than floating text.
    points=[Vector(v.co)for v in letters.data.vertices];xmin=min(v.x for v in points)-.18;xmax=max(v.x for v in points)+.18
    zmin=min(v.y for v in points)-.13;zmax=max(v.y for v in points)+.13
    x,y,z=letters.location;w=xmax-xmin;h=zmax-zmin;cx=x+(xmin+xmax)/2;cz=z+(zmin+zmax)/2
    cut=min(.15,h*.2);outline=[(-w/2+cut,-h/2),(w/2-cut,-h/2),(w/2,-h/2+cut),(w/2,h/2-cut),(w/2-cut,h/2),(-w/2+cut,h/2),(-w/2,h/2-cut),(-w/2,-h/2+cut)]
    v=[(cx+px,y+dy,cz+pz)for dy in [.025,.11]for px,pz in outline];n=len(outline)
    K.mesh('backed_architectural_sign',v,[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)],'blue',parent,uv_scale=.5)
    line=[(cx+px,y+.008,cz+pz)for px,pz in outline+[outline[0]]];K.tube('sign_continuous_border',line,[.025]*len(line),'gold',parent,6)
    # Existing signs on towers have an actual wall behind them; park gateways
    # and canopy signs instead hang from the existing overhead structure.
    text=letters.name
    if '태엽 광장'not in text and '천체관'not in text:
        top=cz+h/2;ceiling=top+.65
        if '축제의 거리'in text and abs(x+29)<1:ceiling=9.5
        elif '가면 전망대'in text:ceiling=9.8
        elif '동화 정원'in text and abs(y+40.5)<1:ceiling=9.2
        for px in [cx-w*.35,cx+w*.35]:K.tube('attached_sign_hanger',[(px,y+.065,top),(px,y+.065,ceiling)],[.025,.025],'iron',parent,6)
    return {'textObject':letters.name,'backed':True,'width':round(w,3),'height':round(h,3)}
def bench(parent,angle,cx,cy,r=9):
    # Curved seating is one bent surface and a continuous back, no cube piles.
    a=angle-.22;b=angle+.22
    def strip(name,r0,r1,z0,z1,mat):
        verts=[]
        for rr,z in [(r0,z0),(r1,z1)]:verts +=[(cx+rr*math.cos(a+(b-a)*i/12),cy+rr*math.sin(a+(b-a)*i/12),z)for i in range(13)]
        return K.mesh(name,verts,[(i,i+1,14+i,13+i)for i in range(12)],mat,parent,uv_scale=.5)
    strip('curved_audience_bench_seat',r-.32,r+.32,.46,.46,'wood');strip('curved_audience_bench_back',r+.3,r+.4,.46,1.03,'wood')
    for t in [a+.05,b-.05]:
        for rr in [r-.24,r+.24]:K.tube('bench_shaped_metal_leg',[(cx+rr*math.cos(t),cy+rr*math.sin(t),.02),(cx+rr*math.cos(t),cy+rr*math.sin(t),.48)],[.04,.04],'iron',parent,6)
    footprint=[(cx+rr*math.cos(a+(b-a)*i/12),cy+rr*math.sin(a+(b-a)*i/12))for rr in [r-.32,r+.4]for i in range(13)]
    return [min(x for x,y in footprint),min(-y for x,y in footprint),max(x for x,y in footprint),max(-y for x,y in footprint),0,1.03]
def export(root,row):
    A.O=O;row['raw']=A.export([root,*root.children_recursive],row['id']+'.glb','Assets/Art/park_levels/'+row['id']+'.glb',{'parkDistrict':row['id'],'publicSpaceFinish':2})

for row in manifest['levels']:
    ident=row['id'];root=bpy.data.objects['park_level_'+ident]
    if ident=='perimeter'or only and ident not in only:continue
    row.setdefault('publicSpaceBaseCollision',baseCollision[ident]);row['collision']=json.loads(json.dumps(row['publicSpaceBaseCollision']))
    old=bpy.data.objects.get('public_space_finish_'+ident)
    if old:remove(old)
    finish=K.root('public_space_finish_'+ident,root)
    signs=[] # Names and decorative text are intentionally absent from the world.
    # Groves beyond the public circulation form a continuous planted backdrop.
    # They do not occupy or block routes, evidence positions or building doors.
    rng=random.Random(260110+list(configs).index(ident));trees=[]
    for grove in range(24):
        a=grove*math.tau/24+rng.uniform(-.06,.06);rad=rng.uniform(102,123)
        for k in range(4):
            x=rad*math.cos(a)+rng.uniform(-6,6);y=rad*math.sin(a)+rng.uniform(-6,6)
            tree=distant_tree(finish,x,y,940000+grove*4+k);tree.scale=(1.1,1.1,1.3);trees.append([round(x,2),round(y,2)])
    if ident=='carnival':
        # The former full-canopy collision box also fenced off its entire lawn.
        row['collision']=[c for c in row['collision']if not(all(abs(c[i]-[-41,1,-17,25][i])<.01 for i in range(4))and c[5]>=12)]
        for x,y in [(-41,-13),(-17,-13),(-29,-25),(-29,-1)]:row['collision'].append([x-.23,-y-.23,x+.23,-y+.23,0,8.5])
        disk(finish,'circus_public_boarded_apron',-29,-13,12.5,.032,'wood');rim(finish,'circus_apron_fitted_edge',-29,-13,12.5,.04,'gold')
        disk(finish,'circus_central_show_ring',-29,-13,4.8,.05,'paving');rim(finish,'show_ring_inset_border',-29,-13,4.8,.055,'gold')
        for angle in [.25,.9,1.55,2.2,2.85]:row['collision'].append(bench(finish,angle,-29,-13))
        # The visible canopy rim is 9.7m high; posts used to stop at8.4m.
        for o in root.children_recursive:
            if o.type=='MESH'and o.name.startswith('circus_canopy_load_pole'):
                for v in o.data.vertices:
                    if v.co.z>8:v.co.z=10.18
        # Keep the main doors accessible while connecting the covered public floor.
        routefile=O/('paths-'+ident+'.json');data=json.loads(routefile.read_text())
        for dest in [[-29,22],[-38,13],[-20,13]]:
            if dest not in data['destinations']:data['destinations'].append(dest)
    else:
        routefile=O/('paths-'+ident+'.json');data=json.loads(routefile.read_text())
    if ident=='mirrors':
        for o in list(root.children_recursive):
            if o.name.startswith(('illusion_arcade_fitted_roof','arcade_actual_mirror_panel')):remove(o)
        for bay in [o for o in root.children_recursive if o.name.startswith('illusion_arcade_bay')and o.type=='EMPTY']:
            v=[(-3.8,y,4.05)for y in [-1.6,1.6]]+[(0,y,5.85)for y in [-1.6,1.6]]+[(3.8,y,4.05)for y in [-1.6,1.6]]
            roof=K.mesh('illusion_arcade_fitted_roof',v,[(0,2,3,1),(2,4,5,3)],'violet',bay,uv_scale=.3);roof.modifiers.new('Real roof thickness','SOLIDIFY').thickness=.12
            for side in [-1,1]:
                panel=K.rounded_solid('arcade_actual_mirror_panel',.09,2.8,2.8,'mirror',bay,.025,(side*3.45,0,2));bpy.context.view_layer.update()
                bb=[panel.matrix_world@Vector(c)for c in panel.bound_box]
                row['collision'].append([min(v.x for v in bb),min(-v.y for v in bb),max(v.x for v in bb),max(-v.y for v in bb),min(v.z for v in bb),max(v.z for v in bb)])
    if ident=='starlight':
        # Recessed glazing makes the landmark entrance read as a closed door,
        # not an unframed hole into the surrounding field.
        for side in [-1,1]:
            K.rounded_solid('planetarium_recessed_glazed_entry',2.2,.09,2.7,'glass',finish,.03,(-34+side*1.13,-14.9,1.4))
            K.tube('planetarium_entry_handle',[(-34+side*.18,-15.03,1.0),(-34+side*.18,-15.03,1.55)],[.035,.035],'gold',finish,8)
        for angle in [i*math.pi/6 for i in range(7)]:
            x=-34+10.05*math.cos(angle);y=-5+10.05*math.sin(angle)
            K.tube('observatory_lower_wall_course',[(x,y,.65),(x,y,2.5)],[.04,.04],'enamel',finish,6)
    if ident=='clockwork':
        # Mechanical spokes support the ornamental dial; it is not a new
        # functioning timepiece, event or evidentiary clock.
        for i in range(6):
            a=i*math.tau/6;K.tube('mechanism_real_dial_spoke',[(-39,-9.23,13.6),(-39+1.65*math.cos(a),-9.23,13.6+1.65*math.sin(a))],[.09,.06],'gold',finish,8)
    # Reissue only the path meshes. Visibility-pulled centerlines and rounded
    # route joins replace grid staircases without changing semantic door IDs.
    data['obstacles']=[c for c in row['collision']if c[4]<1.6 and c[5]>.34];routefile.write_text(json.dumps(data),encoding='utf8')
    subprocess.run(['C:/python/python.exe','-X','utf8',str(R/'tools/plan_v4_park_paths.py'),str(routefile)],check=True)
    for o in list(root.children_recursive):
        if o.name.startswith(('one_connected_public_promenade','continuous_fitted_promenade_edging')):remove(o)
    paving=json.loads(routefile.with_suffix('.mesh.json').read_text());v=[(x,-z,.025)for t in paving['triangles']for x,z in t]
    K.mesh('one_connected_public_promenade',v,[(k,k+1,k+2)for k in range(0,len(v),3)],'paving',finish,uv_scale=.3)
    for polygon in paving['polygons']:
        for ring in [polygon['outer'],*polygon['holes']]:
            line=[(x,-z,.065)for x,z in ring];K.tube('continuous_fitted_promenade_edging',line,[.055]*len(line),'stone',finish,6)
    bpy.context.view_layer.update();export(root,row)
    proof=[p for p in proof if p['id']!=ident]+[{'id':ident,'physicalSigns':signs,'newBackgroundTrees':len(trees),'pathsConnected':paving['connected'],'sourceObject':finish.name}]
    (O/'raw-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'parks-authoring.blend'),compress=True)
    print('PUBLIC_SPACE_FINISHED',ident,flush=True)
(W/'authoring.json').write_text(json.dumps({'source':'art/space_v4/park_levels_v1/parks-authoring.blend','proof':proof,'runtimeVerified':False},ensure_ascii=False,indent=2),encoding='utf8')
