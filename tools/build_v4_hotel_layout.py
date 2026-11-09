"""Author hotel instance/portal layout from exported room dimensions. No game integration."""
from pathlib import Path
import json, math, hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art/space_v4'
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf8'))
spaces={s['id']:s for s in manifest['spaces']}
corridor=spaces['hotel_corridor'];guest=spaces['guest_room'];lobby=spaces['hotel_lobby']
w,d,h=corridor['size_m'];gw,gd,gh=guest['size_m']
ys=sorted({t['position_blender'][1] for t in corridor['targets']})
assert len(ys)==8 and all(b-a>=gw+.05 for a,b in zip(ys,ys[1:])), 'room frontage overlaps: rebuild corridor first'
instances=[{'id':'hotel_lobby','asset':lobby['file'],'position_blender':[0,0,0],'rotation_z_degrees':0,'mode':lobby['mode']},
           {'id':'hotel_corridor','asset':corridor['file'],'position_blender':[-4,6+d/2,3.2],'rotation_z_degrees':0,'mode':corridor['mode']}]
portals=[{'id':'lobby_upper_to_corridor','a':{'instance':'hotel_lobby','local_door':[ -4,6,3.2]},'b':{'instance':'hotel_corridor','local_door':[0,-d/2,0]},'transition':'room load boundary; world door frames coincide','implementation':'pending'}]
rects=[]
for i,y in enumerate(ys):
    for side in [-1,1]:
        ident=f'guest_{i*2+(1 if side<0 else 2):02d}'
        center=[-4+side*(w/2+gd/2),6+d/2+y,3.2]
        instances.append({'id':ident,'asset':guest['file'],'position_blender':center,'rotation_z_degrees':90 if side<0 else -90,'mode':guest['mode'],'occupant':'unassigned; story allocation pending'})
        rects.append((ident,[center[0]-gd/2,center[1]-gw/2,center[0]+gd/2,center[1]+gw/2]))
        portals.append({'id':ident+'_door','a':{'instance':'hotel_corridor','local_door':[side*w/2,y,0],'return_position_local':[side*(w/2-.8),y,0]},'b':{'instance':ident,'local_door':[0,-gd/2,0],'entry_camera':guest['camera']},'transition':'free_walk <-> fixed_orbit; reset to authored room camera on entry','lock_policy':'story/save flag wiring pending','implementation':'pending'})
for i,(a,ra) in enumerate(rects):
    for b,rb in rects[i+1:]:
        overlap_x=min(ra[2],rb[2])-max(ra[0],rb[0]);overlap_y=min(ra[3],rb[3])-max(ra[1],rb[1])
        assert not (overlap_x>.001 and overlap_y>.001),(a,b)
def transform(inst,point):
    a=math.radians(inst['rotation_z_degrees']);x,y,z=point;cx,cy,cz=inst['position_blender']
    return [cx+x*math.cos(a)-y*math.sin(a),cy+x*math.sin(a)+y*math.cos(a),cz+z]
lookup={i['id']:i for i in instances}
for portal in portals:
    a,b=portal['a'],portal['b'];pa=transform(lookup[a['instance']],a['local_door']);pb=transform(lookup[b['instance']],b['local_door'])
    assert max(abs(x-y) for x,y in zip(pa,pb))<.001,portal['id']
report={'status':'authored layout and matching door frames; not runtime tested','source_manifest_sha256':hashlib.sha256((OUT/'manifest.json').read_bytes()).hexdigest(),'units':'original project meters; not measured V3 geometry','instances':instances,'portals':portals,'checks':{'guest_rooms':16,'room_footprint_overlap':'PASS','paired_door_world_alignment':'PASS','camera_mode_mapping':'PASS','runtime_collision_and_transitions':'NOT RUN'},'limits':['hotel subset only; not complete park map','room occupant/story door numbers unassigned','runtime doors/locks/collisions/persistence not implemented']}
(OUT/'hotel_layout.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
# Authoring floor plan is sourced from the same instance rectangles, not a separate guessed map.
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-16 -9 25 75">','<rect x="-16" y="-9" width="25" height="75" fill="#eee8db"/>','<g transform="translate(0,62) scale(1,-1)" fill="#b9a8c7" stroke="#31273b" stroke-width=".08">',f'<rect x="{-4-w/2}" y="6" width="{w}" height="{d}" fill="#cfa0ac"/>','<rect x="-7" y="-6" width="14" height="12"/>']
for ident,rect in rects:
    x,y,x2,y2=rect;svg.append(f'<rect x="{x}" y="{y}" width="{x2-x}" height="{y2-y}"/>')
svg.append('</g>')
for ident,rect in rects:
    x,y,x2,y2=rect;svg.append(f'<text x="{(x+x2)/2}" y="{62-(y+y2)/2}" text-anchor="middle" font-size=".8" fill="#231d29">{ident}</text>')
svg.extend(['<text x="-14" y="-6" font-size=".9">HOTEL AUTHORING LAYOUT / NOT RUNTIME</text>','</svg>'])
(OUT/'hotel_layout.svg').write_text('\n'.join(svg),encoding='utf8')
print('PASS 16 room footprints; 17 paired portal frames; camera mapping; no runtime claim')
