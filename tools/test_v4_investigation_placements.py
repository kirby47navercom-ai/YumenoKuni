"""Pure JSON/mesh-collision checks; does not cook or run the game."""
import copy
import hashlib
import json
import unittest
import v4_investigation_placements as p


class PlacementsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout=p.build_placements()
        cls.world=json.loads((p.ROOT/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf-8'))['spaces']

    def test_every_current_scope_has_a_visible_affordance_spec(self):
        chapters={str(i):json.loads((p.ROOT/f'data/v4_story/chapters/{i}.json').read_text(encoding='utf-8')) for i in range(1,7)}
        before=copy.deepcopy(chapters)
        report=p.apply_placements(chapters)
        self.assertEqual(report['boundSpots'],109)
        self.assertEqual(report['unmatchedSpotIds'],[])
        for c,g in chapters.items():
            for id,node in g['nodes'].items():
                old=before[c]['nodes'][id]
                if node.get('type')!='investigate':self.assertEqual(node,old);continue
                self.assertEqual({k:v for k,v in node.items() if k!='spots'},{k:v for k,v in old.items() if k!='spots'})
                for left,right in zip(node['spots'],old['spots']):
                    for field in ['entry','returnTo','completionFlag','onReturnSet','required']:
                        self.assertEqual(left.get(field),right.get(field))
                    self.assertTrue(left['visibleMarkerRequired'])
                    self.assertFalse(left['runtimeVerified'])
        once=copy.deepcopy(chapters)
        p.apply_placements(chapters)
        self.assertEqual(once,chapters)

    def test_authored_world_anchors_are_clear_and_in_bounds(self):
        for spot in self.layout['spots'].values():
            s=self.world[spot['space_id']];x,y,z=spot['world_pos']
            xmin,zmin,xmax,zmax=s['bounds']
            self.assertTrue(xmin<=x<=xmax and zmin<=z<=zmax)
            self.assertTrue(spot['target_id'])
            self.assertFalse(spot['reaGeometryRecovered'])
            if not spot['authoredTransform']:continue
            # Existing object targets intentionally sit on their object. Only
            # standing marker/NPC staging has body-clearance requirements.
            blocked=[b for b in s['collision'] if b[0]-.2<x<b[2]+.2 and b[1]-.2<z<b[3]+.2 and b[4]<1.6 and b[5]>.1]
            self.assertEqual(blocked,[],spot)

    def test_existing_target_matches_the_real_room_target(self):
        for spot in self.layout['spots'].values():
            if not spot['objectMeshMatched']:continue
            target=next(x for x in self.world[spot['space_id']]['targets'] if x['id']==spot['target_id'])
            self.assertEqual(spot['world_pos'],target['p'])

    def test_missing_rooms_are_proved_without_fake_historical_geometry(self):
        for id,line in [('v4:6:investigate:I6-03-04:spot',27),('v4:6:investigate:I6-05-08:spot',49)]:
            spot=self.layout['spots'][id]
            self.assertEqual(spot['space_id'],'lower_corridor')
            self.assertTrue(spot['productionSetReuse'])
            self.assertTrue(spot['needsDedicatedSet'])
            self.assertFalse(spot['objectMeshMatched'])
            self.assertEqual(spot['sourceProof']['line'],line)
        for id in ['I19-20','I21','I22-23','I24-25']:
            self.assertEqual(self.layout['spots'][f'v4:5:investigate:{id}:spot']['space_id'],'supply_store')

    def test_source_proof_hash_matches_story_normalized_text_identity(self):
        for spot in self.layout['spots'].values():
            ref=spot['sourceProof'];source=p.ROOT/'docs/design/rewrite_v4'/ref['file']
            text=source.read_text(encoding='utf-8-sig')
            self.assertEqual(ref['fileSha256'],hashlib.sha256(text.encode('utf-8')).hexdigest())
            self.assertEqual(ref['quote'],text.splitlines()[ref['line']-1])

    def test_neutral_labels_do_not_disclose_unacquired_answers(self):
        self.assertEqual({m['label'] for m in self.layout['markers']},{'대화하기','조사하기'})
        self.assertTrue(all(m['visibleWhenSpotActive']==m['spot_id'] for m in self.layout['markers']))


if __name__=='__main__':unittest.main()
