"""Themed outdoor levels with stable interior IDs and source-local evidence poses."""
from pathlib import Path
from copy import deepcopy
import json,math,hashlib
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/park_levels_v1'
def plan():return json.loads((O/'plan.json').read_text(encoding='utf8'))
def membership(p):
    out={room:district for district,rooms in p['rooms'].items()for room in rooms}
    out.update({room:'residence'for room in p['residence']});return out
def hedge_collision(boxes, centerlines):
    """Attach the centerline to the existing bounds of diagonal hedges."""
    segments={}
    for x,z,xx,zz,height in centerlines:
        bounds=(min(x,xx)-.36,min(z,zz)-.36,max(x,xx)+.36,max(z,zz)+.36,0,height)
        segments[tuple(round(n,5) for n in bounds)]=[x,z,xx,zz]
    return [box+segments.get(tuple(round(n,5) for n in box),[]) for box in boxes]

def district_collision(asset, world):
    boxes=deepcopy(asset['collision'])
    if asset['id']=='clockwork':
        # park_architecture_v6.loading_gate is an open loading canopy with four
        # piers and a central barred gate, not a solid 12 x 12 m building.
        i=world['instances']['loading_gate'];x,y,z=i['p'];b=[-6,-6,6,6]
        old=[x+b[0],z+b[1],x+b[2],z+b[3]]
        matches=[c for c in boxes if c[:4]==old]
        assert len(matches)==1,('Loading canopy footprint changed',matches)
        boxes.remove(matches[0])
        for px in [-4.85,4.85]:
            for pz in [-4.4,4.4]:boxes.append([x+px-.35,z+pz-.33,x+px+.35,z+pz+.33,y,y+4.9])
        boxes.append([x-3.95,z-.34,x+3.95,z+.34,y+.13,y+3.91])
    return boxes

def apply(world,require_art=True):
    p=plan();groups=membership(p);districts={d['id']:d for d in p['districts']};before=deepcopy(world['instances']);specs=world['spaces'];local_specs=deepcopy(specs);assets={};hedges={}
    if require_art:
        m=json.loads((O/'manifest.json').read_text(encoding='utf8'));assert m['geometryComplete'];assets={a['id']:a for a in m['assets']}
        hedges=json.loads((R/'data/park_hedge_centerlines.json').read_text(encoding='utf8'))['districts']
    header={'version':1,'districts':{},'minimumChapter':{'residence':0,'depths':6},'stableInteriorSaveCoordinates':True}
    for d in p['districts']:
        row={k:d[k]for k in ['name','scene','chapter','hub']};row['mesh']=f"Assets/Art/park_levels/{d['id']}.glb";header['districts'][d['id']]=row;header['minimumChapter'][d['id']]=d['chapter']
    for ident,i in world['instances'].items():
        group=groups.get(ident,'residence'if ident.startswith('guest_')else None);assert group,(ident,'Unassigned current room')
        i['district']=group
        if group in districts:
            d=districts[group];ox,oy=d['originBlender'];i['p']=[i['p'][0]-ox,i['p'][1],i['p'][2]+oy]
            if ident in p['placementsBlender']:
                x,y=p['placementsBlender'][ident];i['p']=[x,i['p'][1],-y]
        if ident in p.get('placementsEngine',{}):i['p']=p['placementsEngine'][ident]
        s=specs[i['space']];s['district']=group
        if s.get('outdoor'):s['levelScene']=districts[group]['scene']
        else:s['levelScene']='Explore'
    for d in p['districts']:
        hub=d['hub']
        if hub not in world['instances']:
            s=deepcopy(specs['plaza']);s.update(id=hub,mesh=header['districts'][d['id']]['mesh'],map='Assets/Art/park_levels/map_'+d['id']+'.svg',mode='free_walk',outdoor=True,spawn=d['spawn'],eye_height=1.6,bounds=d['bounds'],floor=0,walk_surfaces=[[*d['bounds'],0]],collision=[],targets=[],nodes=[],district=d['id'],levelScene=d['scene'])
            specs[hub]=s;world['instances'][hub]={'space':hub,'p':[0,0,0],'label':d['name'],'rotation':0,'occupant':'','district':d['id']}
        else:
            # Keep original plaza/exit local poses, but let the public plaza be a
            # genuine whole outdoor level instead of a tiny cell in a backdrop.
            s=specs[world['instances'][hub]['space']]
            s.update(bounds=d['bounds'],walk_surfaces=[[*d['bounds'],0]])
            if hub=='plaza':s['spawn']=d['spawn']
            world['instances'][hub]['p']=[0,0,0];world['instances'][hub]['label']=d['name']
        if require_art:
            a=assets[d['id']];s['collision']=hedge_collision(district_collision(a,world),hedges.get(d['id'],[]));s['walk_surfaces']=deepcopy(a['walkSurfaces'])
        s.update(district=d['id'],levelScene=d['scene'],outdoor=True)
    # Every free-walk exterior renders the scene-owned district, not its retired
    # small local mesh. Use that same district's physical space in local saved
    # coordinates. Keeping old garden/platform bounds made visible pavement
    # impassable; keeping their old boxes also blocked objects no longer drawn.
    # Fixed-eye sets retain their own visible mesh and original collision.
    for ident,i in world['instances'].items():
        s=specs[i['space']]
        if not s.get('outdoor') or s.get('mode')=='fixed_pan':continue
        d=districts[i['district']];hub=world['instances'][d['hub']]
        source=specs[hub['space']];ox,oy,oz=i['p']
        if ident!=d['hub']:
            original=deepcopy(s)
            # Never mutate another instance that happens to share a local set.
            if sum(v['space']==i['space'] for v in world['instances'].values())>1:
                i['space']=ident;s=deepcopy(original);specs[ident]=s;s['id']=ident
            s['footprintBounds']=deepcopy(original['bounds'])
            s['bounds']=[source['bounds'][0]-ox,source['bounds'][1]-oz,source['bounds'][2]-ox,source['bounds'][3]-oz]
            s['floor']=source.get('floor',0)-oy
            s['walk_surfaces']=[[a-ox,b-oz,c-ox,d-oz,h-oy] for a,b,c,d,h in source['walk_surfaces']]
            s['collision']=[]
            for box in source['collision']:
                c=box[:];c[:4]=[c[0]-ox,c[1]-oz,c[2]-ox,c[3]-oz]
                if len(c)>=6:c[4:6]=[c[4]-oy,c[5]-oy]
                if len(c)==10:c[6:]=[c[6]-ox,c[7]-oz,c[8]-ox,c[9]-oz]
                s['collision'].append(c)
        s['walkingOrigin']=[ox,oy,oz]
    # Existing room-to-room door anchors remain intact, including case-critical
    # paired boundaries. Chapter gates apply to traversal, not historical shots.
    kept=[]
    for edge in world['connections']:
        ga=world['instances'][edge['a']]['district'];gb=world['instances'][edge['b']]['district'];edge['minimumChapter']=max(header['minimumChapter'][ga],header['minimumChapter'][gb])
        # The enlarged plaza is the whole park level. Its old 14m cell exits
        # are replaced below by doors at the actual authored facility fronts.
        replaced={*p['rooms']['fairytale'],'hotel_lobby'}-{'plaza','staff_passage'}
        if (edge['a']=='plaza'and edge['b']in replaced)or(edge['b']=='plaza'and edge['a']in replaced):continue
        # Public travel between themed parks goes through their actual gate.
        # Retain authored restricted service/depth links and the common hotel.
        if ga!=gb and edge.get('kind')!='paired_boundary' and 'depths'not in [ga,gb]and 'perimeter'not in [ga,gb]and set([ga,gb])!={'fairytale','residence'}:continue
        kept.append(edge)
    world['connections']=kept
    links=[]
    for d in p['districts']:
        if d['id']=='perimeter':continue
        hub=d['hub'];rooms=list(p['rooms'][d['id']])
        if d['id']=='fairytale':rooms+=['hotel_lobby']
        for ident in rooms:
            if ident==hub:continue
            if ident in ['theatre_preparation','mirror_workbay','screening_room','inspection_hall_changed','ferris_cabin']:continue
            i=world['instances'][ident];s=local_specs[before[ident]['space']];x,y,z=i['p'];front=s['bounds'][3]
            links.append({'id':'park_entry:'+hub+':'+ident,'a':hub,'b':ident,'a_p':[x,1.2,z+front+1.1],'b_p':[0,1.2,front-.15],'kind':'park_door','minimumChapter':d['chapter']})
    gates=[('carnival',[59,1.2,1]),('mirrors',[64,1.2,-42]),('clockwork',[-64,1.2,-24]),('starlight',[24,1.2,64])]
    for ident,anchor in gates:
        d=districts[ident];spawn=d['spawn'];links.append({'id':'park_gate:'+ident,'a':'plaza','b':d['hub'],'a_p':anchor,'b_p':[spawn[0],1.2,spawn[2]+1.5],'kind':'park_gate','minimumChapter':d['chapter'],'label':d['name']})
    existing={e['id']for e in world['connections']}
    for row in links:
        assert row['id']not in existing;world['connections'].append(row)
    # The original exterior catalog is replaced by scene-owned park assets.
    world.pop('worldContext',None);world['parkLevels']=header
    for group in p['lockedGeometryGroups']:
        for a,b in zip(group,group[1:]):
            assert all(abs((before[a]['p'][k]-before[b]['p'][k])-(world['instances'][a]['p'][k]-world['instances'][b]['p'][k]))<1e-5 for k in range(3)),('Critical relative layout changed',a,b)
    copies=[]
    if require_art:
        copies=[{'from':a['file'],'to':a['runtime']}for a in assets.values()];(O/'maps').mkdir(exist_ok=True)
        local_names=O/'theme_park_v2/local-names-manifest.json'
        if local_names.exists():
            for a in json.loads(local_names.read_text(encoding='utf8'))['assets']:
                assert hashlib.sha256((R/a['source']).read_bytes()).hexdigest()==a['sourceSHA256'],('Refresh text-free local mesh',a['source'])
                copies.append({'from':a['file'],'to':a['runtime']})
        gate=json.loads((O/'gate-manifest.json').read_text(encoding='utf8'));copies.append({'from':gate['file'],'to':gate['runtime']})
        for ident,d in header['districts'].items():
            hubspec=specs[world['instances'][d['hub']]['space']];b=hubspec['bounds'];parts=[]
            for i in world['instances'].values():
                if i['district']!=ident:continue
                room=specs[i['space']];q=room.get('footprintBounds',room['bounds']);parts.append(f'<rect x="{i["p"][0]+q[0]}" y="{i["p"][2]+q[1]}" width="{q[2]-q[0]}" height="{q[3]-q[1]}" fill="#282330" stroke="#ffda24" stroke-width=".35"/>')
            file=O/'maps'/('map_'+ident+'.svg');file.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{b[0]} {b[1]} {b[2]-b[0]} {b[3]-b[1]}">'+''.join(parts)+'</svg>',encoding='utf8');copies.append({'from':file.relative_to(R).as_posix(),'to':'Assets/Art/park_levels/'+file.name})
    return {'copies':copies,'world':world}
if __name__=='__main__':
    from v4_dedicated_spaces import apply_world
    from v4_freetime_paths import apply as freetime
    w=json.loads((R/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf8'));apply_world(w);freetime(w);apply(w,require_art='--metadata-only'not in __import__('sys').argv);json.dump(w,__import__('sys').stdout,ensure_ascii=False,separators=(',',':'))
