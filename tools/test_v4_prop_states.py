"""Pure source/metadata checks; no cook, engine or game execution."""
from copy import deepcopy
import hashlib
import unittest
from pathlib import Path
import v4_prop_states as props


class PropStatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.bundle=props.build()

    def state(self,prefix,line,flags=None,space=None,shown=True):
        ref=next(r['source'] for r in self.bundle['ranges'] if r['source']['file'].startswith(prefix+'_'))
        return props.resolve(self.bundle,dict(ref,line=line),flags,space,shown)

    def test_exact_existing_nodes_and_absent_props_are_distinct(self):
        from v4_dedicated_spaces import build
        spaces=build()['spaces']
        self.assertGreaterEqual(len(self.bundle['ranges']),200)
        self.assertGreaterEqual(len(self.bundle['unbound']),25)
        for prop in self.bundle['catalog'].values():
            nodes={n['id'] for n in spaces[prop['space_id']]['nodes']}
            self.assertTrue(set(prop['meshNodes'])<=nodes)
            self.assertEqual(prop['assetReady'],bool(prop['meshNodes']))
        for row in self.bundle['ranges']:
            self.assertTrue(set(row['nodeVisibility'])<=set(row['meshNodes']))
            self.assertFalse(row['inventoryGrant']);self.assertFalse(row['knowledgeGrant'])
            self.assertFalse(row['animationBound']);self.assertFalse(row['runtimeVerified'])
            path=props.ROOT/'docs/design/rewrite_v4'/row['source']['file']
            self.assertEqual(hashlib.sha256(path.read_text(encoding='utf-8-sig').encode()).hexdigest(),row['source']['fileSha256'])
        self.assertFalse(self.bundle['catalog']['rei.originalDrawing']['assetReady'])
        self.assertFalse(self.bundle['catalog']['sho.bentCar']['assetReady'])
        self.assertTrue(self.bundle['catalog']['shop.neutralCarStock']['assetReady'])

    def test_top_can_and_its_two_rims_hide_together(self):
        state=self.state('42',7)
        visible=state['nodeVisibility']
        for node in ['can_2_0','can_metal_rim.010','can_metal_rim.011']:self.assertFalse(visible[node])
        self.assertTrue(visible['can_0_0'])
        self.assertEqual(state['states']['booth.cans']['upright'],5)
        for node in ['soft_throw_ball','soft_throw_ball.001','soft_throw_ball.002']:self.assertFalse(visible[node])

    def test_three_different_first_games_never_merge(self):
        a=self.state('42',207,{'SORA-02A':'A'})['states']['booth.cans']
        b=self.state('42',207,{'SORA-02A':'B'})['states']['booth.cans']
        c=self.state('42',207,{'SORA-02A':'C'})['states']['booth.cans']
        self.assertEqual((a['upright'],a['outside']),(0,5))
        self.assertEqual(b['upright'],0);self.assertTrue(b['lastOneLoweredByHand'])
        self.assertEqual((c['upright'],c['fallen']),(2,4))
        # Six upright after the miss is factual, but their changed gaps have no
        # reviewed matching pose. Do not restore the ordinary triangle.
        current=self.state('42',171,{'SORA-02A':'C'})
        self.assertEqual(current['states']['booth.cans']['upright'],6)
        self.assertFalse(current['nodeVisibility']['can_2_0'])
        self.assertTrue(current['unresolved'])

    def test_later_game_resets_and_unobserved_cleanup_is_not_done(self):
        current=self.state('59',176)
        self.assertEqual(current['states']['booth.cans']['scores'],{'mio':5,'sora':4})
        self.assertTrue(current['nodeVisibility']['can_2_0'])
        self.assertIsNone(current['states']['booth.balls']['physicalTotal'])
        self.assertEqual(current['states']['booth.balls']['throwsPerPlayer'],3)
        first=self.state('59',256,{'SORA-03A':'A2'})['states']['booth.cans']
        self.assertEqual(first['outside'],3);self.assertTrue(first['firstGameUnchanged'])
        self.assertNotIn('booth.cans',self.state('59',256,{'SORA-03A':'A1'})['states'])
        cleaned=self.state('59',326,{'SORA-03A':'A1','SORA-03B-A':'B2'})['states']['booth.cans']
        self.assertEqual(cleaned['location'],'original box; actual joint cleanup')
        left=self.state('59',338,{'SORA-03A':'A1','SORA-03B-A':'B3'})['states']['booth.cans']
        self.assertFalse(left['laterCleanupObserved']);self.assertFalse(left['laterGameObserved'])

    def test_original_draft_and_mio_paper_do_not_become_one_gift(self):
        one=self.state('58',554,{'F-RE03-B':'B1','F-RE02-B':'B1','F-RE02-A':'A1'})['states']
        self.assertEqual(one['rei.originalDrawing']['owner'],'rei')
        self.assertEqual(one['rei.originalDrawing']['placement'],'notice board')
        self.assertEqual(one['mio.ownDrawing']['owner'],'mio')
        self.assertIsNone(one['rei.titleLabel']['text'])
        two=self.state('58',554,{'F-RE03-B':'B2','F-RE02-B':'B2','F-RE02-A':'A2'})['states']
        self.assertNotIn('mio.ownDrawing',two);self.assertNotIn('pillarWidth',two['rei.originalDrawing'])
        self.assertEqual(two['rei.originalDrawing']['owner'],'rei')
        self.assertFalse(two['rei.originalDrawing']['visible'])
        unseen=[r for r in self.bundle['ranges'] if r['source']['file'].startswith('45_') and r['startLine']==369]
        self.assertTrue(unseen);self.assertEqual(unseen[0]['perspective'],'objective-unseen-by-mio')

    def test_mirror_custody_and_towel_shape_are_path_specific(self):
        for flag,who in [('A1','mio'),('A2','haruka'),('A3','haruka')]:
            result=self.state('37',207,{'F-HA02-A':flag})
            self.assertEqual(result['states']['haruka.handMirror']['custodian'],who)
            self.assertFalse(result['nodeVisibility']['folded_shared_towel'])
            self.assertFalse(self.bundle['catalog']['haruka.haircutTowel']['assetReady'])
        self.assertEqual(self.state('37',349)['states']['haruka.scissors']['returnStatus'],'intended-not-observed')

    def test_actual_late_intro_and_borrowed_item_conditions(self):
        self.assertFalse(self.state('143',17)['states']['rin.rabbitToy']['visible'])
        self.assertFalse(self.state('147',49)['states']['rei.cloth']['mioHasSpareCloth'])
        self.assertFalse(self.state('88',59)['states']['nana.goStones']['earlierGameGranted'])
        borrowed=self.state('56',48,{'SHO-02B':'A'})['states']
        self.assertTrue(borrowed['sho.busToy']['visible']);self.assertNotIn('sho.bentCar',borrowed)
        not_borrowed=self.state('56',48,{'SHO-02B':'B'})['states']
        self.assertFalse(not_borrowed['sho.busToy']['visible']);self.assertFalse(not_borrowed['sho.bentCar']['visible'])

    def test_missed_path_and_unknown_source_never_create_side_effects(self):
        before=deepcopy(self.bundle);flags={'F-RE03-B':'B1'}
        deferred=self.state('58',208,flags,shown=False)
        self.assertTrue(deferred['deferred']);self.assertEqual(deferred['nodeVisibility'],{})
        props.resolve(self.bundle,{'file':'unrelated.md','line':1},flags)
        self.assertEqual(flags,{'F-RE03-B':'B1'});self.assertEqual(self.bundle,before)
        ref=next(r['source'] for r in self.bundle['ranges'] if r['source']['file'].startswith('58_'))
        with self.assertRaisesRegex(ValueError,'hash differs'):props.resolve(self.bundle,dict(ref,line=208,fileSha256='0'*64),flags)

    def test_adapter_only_adds_metadata_and_scene_departures_have_exact_coverage(self):
        scene={'sections':{'sentinel':{'space':'plaza'}},'cgRanges':[{'id':'unchanged'}]}
        original=deepcopy(scene);report=props.apply_scene_bindings(scene)
        self.assertEqual(scene['sections'],original['sections']);self.assertEqual(scene['cgRanges'],original['cgRanges'])
        self.assertEqual(report['logicalProps'],34)
        from v4_scene_bindings_more import build_more
        from v4_dedicated_spaces import apply_scene_bindings
        result=build_more();apply_scene_bindings(result)
        def at(prefix,line):
            matches=[r for r in result['sceneRanges'] if r['source']['file'].startswith(prefix+'_') and r['startLine']<=line<r['endLineExclusive']]
            self.assertEqual(len(matches),1);return matches[0]
        self.assertEqual(at('35',410)['space'],'souvenir_shop')
        self.assertEqual(at('43',333)['space'],'kitchen');self.assertEqual(at('43',345)['space'],'hotel_rest_lounge')
        self.assertEqual(at('57',380)['space'],'hotel_corridor');self.assertEqual(at('57',386)['space'],'hotel_rest_lounge')
        for line in [278,306,338,390]:self.assertEqual(at('59',line)['space'],'park_garden')
        self.assertEqual(at('58',568)['space'],'hotel_corridor')

    def test_shared_exit_dialogue_requires_the_actual_current_choice(self):
        row=self.bundle['conditionalSceneRanges'][0];ref=dict(row['source'],line=411)
        for value,place in [('B1','kitchen'),('B2','hotel_corridor'),('B3','hotel_rest_lounge')]:
            self.assertEqual(props.resolve_scene(self.bundle,ref,{'F-AI02-B':value})['space'],place)
        self.assertIsNone(props.resolve_scene(self.bundle,ref,{})['space'])


if __name__=='__main__':unittest.main()
