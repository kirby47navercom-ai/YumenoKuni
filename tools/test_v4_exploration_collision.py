"""Regression coverage for district geometry/local save coordinate ownership."""
import json
import unittest
from copy import deepcopy
from verify_v4_walkability import ROOT,authored_world,solid


class DistrictWalking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world=authored_world()

    def test_every_rendered_free_exterior_uses_district_physics(self):
        w=self.world
        for ident,i in w['instances'].items():
            s=w['spaces'][i['space']]
            if not s.get('outdoor') or s['mode']=='fixed_pan':continue
            with self.subTest(instance=ident):
                d=w['parkLevels']['districts'][i['district']];hub=w['spaces'][w['instances'][d['hub']]['space']]
                ox,oy,oz=i['p']
                self.assertEqual(s['walkingOrigin'],i['p'])
                self.assertEqual(s['bounds'],[hub['bounds'][0]-ox,hub['bounds'][1]-oz,hub['bounds'][2]-ox,hub['bounds'][3]-oz])
                self.assertEqual(len(s['collision']),len(hub['collision']))
                for ix in range(19):
                    for iz in range(17):
                        x=hub['bounds'][0]+(ix+.5)/19*(hub['bounds'][2]-hub['bounds'][0])
                        z=hub['bounds'][1]+(iz+.5)/17*(hub['bounds'][3]-hub['bounds'][1])
                        self.assertEqual(solid(s,x-ox,z-oz,1.6-oy),solid(hub,x,z,1.6))

    def test_video_open_pavement_crosses_retired_garden_edge(self):
        s=self.world['spaces']['park_garden']
        self.assertTrue(all(not solid(s,0,z) for z in [9,9.74,10,11,12,13]))

    def test_loading_canopy_has_clear_floor_and_real_obstructions(self):
        s=self.world['spaces']['loading_gate']
        self.assertFalse(solid(s,0,5))
        self.assertFalse(solid(s,0,4))
        self.assertTrue(solid(s,0,0))  # visibly closed gate
        self.assertTrue(solid(s,4.85,4.4))  # structural pier

    def test_entry_anchors_do_not_use_expanded_alias_bounds(self):
        w=self.world
        for e in w['connections']:
            if e['kind']!='park_door':continue
            with self.subTest(door=e['id']):
                i=w['instances'][e['b']]
                self.assertAlmostEqual(e['a_p'][0],i['p'][0])
                self.assertAlmostEqual(e['a_p'][2]-i['p'][2]-e['b_p'][2],1.25)

    def test_all_authored_places_have_walking_connections(self):
        w=self.world;seen={'plaza'}
        while True:
            before=len(seen)
            for edge in w['connections']:
                if edge['a'] in seen:seen.add(edge['b'])
                if edge['b'] in seen:seen.add(edge['a'])
            if len(seen)==before:break
        self.assertEqual(seen,set(w['instances']))
        edges={e['id'] for e in w['connections']}
        self.assertIn('theatre_preparation__staff_passage',edges)
        self.assertIn('staff_passage__cold_store',edges)
        self.assertIn('fte_path:lower_corridor:core_external_inspection',edges)

    def test_restored_links_preserve_chapter_locks(self):
        w=self.world
        for chapter in range(1,7):
            seen={'plaza'}
            while True:
                before=len(seen)
                for e in w['connections']:
                    if e.get('minimumChapter',0)>chapter:continue
                    if e['a'] in seen:seen.add(e['b'])
                    if e['b'] in seen:seen.add(e['a'])
                if len(seen)==before:break
            self.assertEqual('core_external_inspection' in seen,chapter>=6)
            self.assertEqual('staff_passage' in seen,chapter>=2)
            for d in w['parkLevels']['districts'].values():
                self.assertEqual(d['hub'] in seen,chapter>=d['chapter'])

    def test_interior_and_fixed_eye_geometry_remains_local(self):
        from v4_dedicated_spaces import apply_world
        from v4_freetime_paths import apply as freetime
        base=json.loads((ROOT/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf8'));apply_world(base);freetime(base)
        for name,s in base['spaces'].items():
            if s.get('outdoor') and s['mode']!='fixed_pan':continue
            current=self.world['spaces'][name]
            for key in ['bounds','spawn','collision','walk_surfaces','targets','mode']:
                self.assertEqual(current.get(key),s.get(key),(name,key))


if __name__=='__main__':unittest.main()
