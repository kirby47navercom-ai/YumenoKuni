"""Decoded runtime proof for facility signs, head badges and aligned sunlight."""
from pathlib import Path
import sys,json,math,hashlib,io
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from v4_lowpoly_glb import read,array,digest
O=R/'art/space_v4/facility_identity_v1';identity=json.loads((O/'manifest.json').read_text(encoding='utf8'));placements=json.loads((O/'placement-proof.json').read_text());bank=json.loads((R/'art/space_v4/rebuild_v1/manifest.json').read_text(encoding='utf8'))
assert len(identity['roomOwners'])==len(set(identity['roomOwners'].values()))==16
assert len(placements['roomBadges'])==16
for slug in identity['roomOwners'].values():
    im=Image.open(O/'faces'/(slug+'.png')).convert('RGBA');assert im.size==(64,64);alpha=np.array(im)[:,:,3];assert alpha.min()==0 and alpha.max()>=250;assert (alpha>0).sum()>700
badge_proof=[];sign_proof=[];facades=[]
for row in bank['assets']:
    name=Path(row['runtime']).stem
    if name not in placements['facilityInteriors']and name!='finish_context':continue
    j,b=read(R/row['file']);meta=j['nodes'][0]['extras']['sourcePivots']
    for material in j['materials']:
        if not material['name'].startswith(('identity_facility_sign','identity_room_face')):continue
        t=j['textures'][material['pbrMetallicRoughness']['baseColorTexture']['index']];ii=t.get('source',t.get('extensions',{}).get('EXT_texture_webp',{}).get('source'));image=j['images'][ii];v=j['bufferViews'][image['bufferView']];off=v.get('byteOffset',0);actual=Image.open(io.BytesIO(b[off:off+v['byteLength']])).convert('RGBA');expected=Image.open(O/('facility-signs.png'if material['name'].startswith('identity_facility_sign')else'room-faces.png')).convert('RGBA')
        assert actual.size==expected.size and actual.tobytes()==expected.tobytes(),(name,'stale packed identity atlas')
    if name=='finish_context':
        facades=[m for m in meta if 'architectureFamily'in m];assert len(facades)==30;assert len(set(m['architectureFamily']for m in facades))>=8
    else:assert any(m.get('facilityIdentity')==name for m in meta),(name,'no physical nameplate')
    if name=='clinic':
        signs=[p for p in j['meshes'][0]['primitives']if j['materials'][p['material']]['name'].startswith('identity_facility_sign')]
        assert signs and all((array(j,b,p['attributes']['NORMAL'])[:,2]>.99).all()for p in signs),'The printed back-wall sign must face into the room (+Z), not the wall'
    if name=='hotel_corridor':
        badges=[m for m in meta if 'guestRoom'in m];assert{m['guestRoom']:m['character']for m in badges}==identity['roomOwners'];badge_proof=badges
        mat=next(m for m in j['materials']if m['name'].startswith('identity_room_face'));tex=j['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']];sampler=j['samplers'][tex['sampler']];assert sampler['magFilter']==sampler['minFilter']==9728
        emit=j['textures'][mat['emissiveTexture']['index']];assert j['samplers'][emit['sampler']]['magFilter']==j['samplers'][emit['sampler']]['minFilter']==9728
        # Face geometry must still be 16 independent visible printed quads.
        prim=[p for p in j['meshes'][0]['primitives']if j['materials'][p['material']]['name'].startswith('identity_room_face')];assert sum(len(array(j,b,p['indices']).reshape(-1))//3 for p in prim)==32
    sign_proof.append(name)
alignment=json.loads((R/'art/environment_v4/celestial-alignment.json').read_text());scene=json.loads((R/'Game/Assets/Scenes/Explore.hbscene.json').read_text(encoding='utf8'))
for i,phase in enumerate(['day','night','evening']):
    light=next(o for o in scene['objects']if o['id']==f'Outdoor{i}_sun');assert np.allclose(light['rotation'],alignment[phase]['rotationDegrees']);p=next(c['properties']for c in light['components']if c['type']=='DirectionalLight');assert p['castShadow']and p['shadowMapWidth']==2048
    x,y,z=np.radians(light['rotation']);d=np.array([math.sin(y),-math.sin(x)*math.cos(y),math.cos(x)*math.cos(y)]);assert np.dot(d,alignment[phase]['direction'])>.999999
result={'ok':True,'facilityManifestSHA256':digest((O/'manifest.json').read_bytes()),'environmentManifestSHA256':digest((R/'art/space_v4/rebuild_v1/manifest.json').read_bytes()),'physicalFacilitySigns':len(sign_proof)-1,'purposeFacades':len(facades),'architectureFamilies':sorted(set(m['architectureFamily']for m in facades)),'pixelHeads':len(badge_proof),'pixelFaceSampler':'NEAREST without mipmaps','sunMoonAlignment':True,'runtimeVisualAcceptance':False,'scope':'Independent decoded geometry, material sampler, physical marker metadata and actual generated scene light vector checks. Actual native visual QA separate.'}
(O/'static-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
