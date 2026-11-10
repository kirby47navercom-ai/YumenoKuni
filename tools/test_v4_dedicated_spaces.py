"""Pure GLB/source/geometry integration checks, never the game executable."""
from collections import deque
from copy import deepcopy
import json
from pathlib import Path
import struct
import unittest
import v4_dedicated_spaces as dedicated
from v4_scene_bindings_more import build_more
from v4_investigation_placements import build_placements,apply_placements


def solid(s,x,z,r=.27):
    a,b,c,d=s['bounds']
    if not(a+r<=x<=c-r and b+r<=z<=d-r):return True
    return any(lo<1.6 and hi>.34 and ax-r<x<bx+r and az-r<z<bz+r
               for ax,az,bx,bz,lo,hi in s['collision'])


def reachable(s):
    step=.2;sx,_,sz=s['spawn'];points={(0,0)};q=deque(points)
    while q:
        i,j=q.popleft()
        for ii,jj in [(i+1,j),(i-1,j),(i,j+1),(i,j-1)]:
            if (ii,jj) in points or solid(s,sx+ii*step,sz+jj*step):continue
            points.add((ii,jj));q.append((ii,jj))
    return [(sx+i*step,sz+j*step) for i,j in points]


def gltf(path):
    raw=path.read_bytes();n,kind=struct.unpack_from('<II',raw,12)
    assert raw[:4]==b'glTF' and kind==0x4e4f534a
    return json.loads(raw[20:20+n])


def occluded(s,x,z,target):
    # Same obstruction semantics as the existing native ExploreWorld module.
    tx,ty,tz=target;dx,dz=tx-x,tz-z
    for ax,az,bx,bz,lo,hi in s['collision']:
        if lo>max(1.6,ty) or hi<min(1.6,ty):continue
        if ax-.01<=tx<=bx+.01 and az-.01<=tz<=bz+.01:continue
        low,high=0,1;hit=True
        for start,delta,left,right in [(x,dx,ax,bx),(z,dz,az,bz)]:
            if abs(delta)<.0001:
                if start<left or start>right:hit=False;break
            else:
                a,b=sorted(((left-start)/delta,(right-start)/delta));low=max(low,a);high=min(high,b)
                if low>high:hit=False;break
        if hit and low>.0001 and low<.99:return True
    return False


class DedicatedSpacesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle=dedicated.build();cls.spaces=cls.bundle['spaces']
        cls.scenes=build_more();dedicated.apply_scene_bindings(cls.scenes)

    def test_original_model_artifacts_and_copy_contract(self):
        self.assertEqual(len(self.bundle['manifest']['spaces']),6)
        self.assertGreater((dedicated.ROOT/dedicated.OUTPUT/'dedicated_spaces_source.blend').stat().st_size,100000)
        self.assertEqual(len(self.bundle['copies']),12)
        self.assertLess(sum((dedicated.ROOT/r['file']).stat().st_size for r in self.bundle['manifest']['spaces']),70*2**20)
        for s in self.spaces.values():
            self.assertEqual(s['coordinateSystem'],'runtime-world-xyz')
            self.assertFalse(s['reaGeometryRecovered']);self.assertFalse(s['runtime_tested'])
            self.assertTrue(s['productionLayout'])
        for r in self.bundle['manifest']['spaces']:
            document=gltf(dedicated.ROOT/r['file'])
            self.assertGreater(len(document['meshes']),20)
            raw=(dedicated.ROOT/r['file']).read_bytes();header_length=struct.unpack_from('<I',raw,12)[0]
            for image in document.get('images',[]):
                view=document['bufferViews'][image['bufferView']];offset=28+header_length+view.get('byteOffset',0)
                self.assertEqual(raw[offset:offset+8],b'\x89PNG\r\n\x1a\n')
                self.assertLessEqual(max(struct.unpack_from('>II',raw,offset+16)),2048)
            self.assertTrue((dedicated.ROOT/dedicated.OUTPUT/'maps'/('map_'+r['id']+'.svg')).is_file())

    def test_world_adds_real_instances_without_unlocks_or_overwrite(self):
        w={'spaces':{'sentinel':{'id':'unchanged'}},'instances':{},'connections':[]}
        base=json.loads((dedicated.ROOT/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf-8'))
        for id in ('lower_stairway','mirror_maze'):w['spaces'][id]=deepcopy(base['spaces'][id])
        dedicated.apply_world(w);self.assertEqual(len(w['spaces']),11)
        self.assertEqual(w['spaces']['sentinel'],{'id':'unchanged'})
        self.assertEqual(set(w['instances']),set(self.spaces));self.assertEqual(w['connections'],[])
        old=deepcopy(w);dedicated.apply_world(w);self.assertEqual(w,old)
        for id,spec in self.spaces.items():
            expected=deepcopy(spec)
            if id=='garden_rest_area':expected['entry_yaw']=50
            self.assertEqual(w['spaces'][id],expected)

    def test_collision_free_spawn_and_reachable_targets(self):
        for id,s in self.spaces.items():
            self.assertFalse(solid(s,s['spawn'][0],s['spawn'][2]),id)
            route=reachable(s);self.assertGreater(len(route),30,id)
            for t in s['targets']:
                x,y,z=t['p']
                self.assertLess(min((xx-x)**2+(zz-z)**2 for xx,zz in route),3.8**2,(id,t['id']))

    def test_core_real_separate_portals_and_protected_current_well(self):
        r=next(x for x in self.bundle['manifest']['spaces'] if x['id']=='core_external_inspection')
        self.assertEqual({p['id'] for p in r['portals']},{'main_inspection','side_management'})
        s=self.spaces[r['id']];route=reachable(s)
        self.assertTrue(any(x>3.3 and z<-.3 for x,z in route),'Side lane is unreachable')
        self.assertFalse(any(-4.9<x<2.3 and -5.1<z<-2.3 for x,z in route),'Player can walk into current guarded well')
        self.assertFalse(r['historicalSightVerified'])
        for target_id in dedicated.CORE_TARGETS.values():
            t=next(t for t in s['targets'] if t['id']==target_id)['p']
            self.assertTrue(any((x-t[0])**2+(z-t[2])**2<4.1**2 and not occluded(s,x,z,t) for x,z in route),target_id)

    def test_shop_front_is_outside_real_facade_and_booth_colours_are_three_each(self):
        shop=self.spaces['souvenir_shop'];front=self.spaces['souvenir_forecourt']
        self.assertLess(shop['spawn'][2],3.5);self.assertGreater(front['spawn'][2],3.5)
        self.assertEqual(shop['mesh'],front['mesh']);self.assertGreaterEqual(front['bounds'][3],7)
        doc=gltf(dedicated.ROOT/dedicated.OUTPUT/'can_toss_booth.glb');materials=doc['materials'];meshes=doc['meshes']
        counts={'dedicated_red':0,'dedicated_blue':0}
        for node in doc['nodes']:
            if node.get('name','').startswith(('can_0_','can_1_','can_2_')):
                p=meshes[node['mesh']]['primitives'][0];counts[materials[p['material']]['name']]+=1
        self.assertEqual(counts,{'dedicated_red':3,'dedicated_blue':3})

    def test_toy_display_mounts_and_car_wheels_contact_actual_shelves(self):
        nodes=self.spaces['souvenir_shop']['nodes']
        mounts=[n for n in nodes if n['id'].startswith('toy_display_mount')]
        wheels=[n for n in nodes if n['id'].startswith('toy_car_wheel')]
        self.assertEqual(len(mounts),12);self.assertEqual(len(wheels),16)
        for n in mounts:self.assertAlmostEqual(n['box'][0][1],.58,places=3)
        for n in wheels:self.assertAlmostEqual(n['box'][0][1],1.52,places=3)

    def test_exact_source_changes_keep_real_branches_and_lobbies(self):
        def at(prefix,line):
            rows=[r for r in self.scenes['sceneRanges'] if r['source']['file'].startswith(prefix+'_') and r['startLine']<=line<r['endLineExclusive']]
            self.assertEqual(len(rows),1,(prefix,line));return rows[0]['space']
        for prefix,line,space in [('55',9,'hotel_lobby'),('55',24,'hotel_rest_lounge'),
          ('55',510,'hotel_corridor'),('147',9,'hotel_indoor_garden'),('147',111,'garden_rest_area'),
          ('26',419,'hotel_rest_lounge'),('26',507,'laundry_room'),('49',381,'hotel_lobby'),
          ('57',174,'hotel_rest_lounge'),('57',144,'hotel_corridor'),('143',91,'hotel_lobby'),
          ('41',9,'souvenir_forecourt'),('34',325,'souvenir_shop'),('34',494,'souvenir_forecourt'),
          ('59',9,'can_toss_booth'),('59',278,'park_garden'),('59',306,'park_garden'),
          ('59',326,'can_toss_booth'),('59',338,'park_garden'),('59',394,'park_garden'),('37',9,'hotel_washroom'),
          ('52',257,'hotel_corridor'),('52',263,'kitchen'),('16b1',199,'operating_archive')]:
            if prefix=='16b1':continue # Ordinary investigation source routing owns I6-09.
            self.assertEqual(at(prefix,line),space)
        before=build_more();self.assertEqual(before['cgRanges'],self.scenes['cgRanges'])
        self.assertEqual(before['sections'],self.scenes['sections'])
        # All final73 execution graphs still have exactly one reviewed source set.
        base=dedicated.ROOT/'data/v4_story';index=json.loads((base/'freetime/index.json').read_text(encoding='utf-8'))['meetings']
        self.assertGreaterEqual(len(index),73)
        for key,entry in index.items():
            graph=json.loads((base/entry['path']).read_text(encoding='utf-8'))
            for node in graph['nodes'].values():
                ref=node.get('source')
                if node.get('type') not in ['say','stage'] or not ref:continue
                rows=[r for r in self.scenes['sceneRanges'] if r['source']['file']==ref['file'] and r['startLine']<=ref['line']<r['endLineExclusive']]
                self.assertEqual(len(rows),1,(key,ref));self.assertEqual(rows[0]['source']['fileSha256'],ref['fileSha256'])

    def test_only_two_core_spots_move_preserving_story_flow(self):
        graph=json.loads((dedicated.ROOT/'data/v4_story/chapters/6.json').read_text(encoding='utf-8'))
        chapters={'6':graph};report=apply_placements(chapters);before=deepcopy(graph)
        result=dedicated.apply_placements(chapters,report)
        self.assertEqual(len(result['updatedCoreSpots']),2)
        for id,node in graph['nodes'].items():
            original=before['nodes'][id]
            if node.get('type')!='investigate':self.assertEqual(node,original);continue
            for spot,old in zip(node['spots'],original['spots']):
                if spot['id'] not in dedicated.CORE_TARGETS:self.assertEqual(spot,old);continue
                self.assertEqual(spot['space_id'],'core_external_inspection')
                for key in ['entry','returnTo','required','completionFlag','onReturnSet']:
                    self.assertEqual(spot.get(key),old.get(key))
                self.assertFalse(spot['needsDedicatedSet']);self.assertFalse(spot['runtimeVerified'])
        self.assertEqual(report['dedicatedSetsStillNeeded'],[])


if __name__=='__main__':unittest.main()
