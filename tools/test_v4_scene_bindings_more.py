"""Pure source/art contract checks. Does not cook, write data, or run the game."""
import unittest
from pathlib import Path
import v4_scene_bindings_more as scenes


class SceneBindingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=scenes.build_more()

    def test_actual_existing_spaces_only(self):
        import json
        world=json.loads((scenes.ROOT/'art/space_v4/runtime_v1/world.json').read_text(encoding='utf-8'))['spaces']
        self.assertGreater(len(self.result['sections']),800)
        for value in self.result['sections'].values():
            self.assertIn(value['space'],world)
            self.assertFalse(value['knowledgeGrant'])
            self.assertFalse(value['actorPositionsAssigned'])
            self.assertGreater(value['sourceSpan']['endLineExclusive'],value['sourceSpan']['startLine'])

    def test_section_context_is_not_teleport_or_knowledge(self):
        lookup={(Path(x['source']['file']).stem.split('_')[0],x['source']['location']):x for x in self.result['sections'].values()}
        self.assertEqual(lookup['13a4','3-35']['space'],'screening_room')
        self.assertEqual(lookup['13a4','3-35']['perspective'],'viewed-recording')
        self.assertEqual(lookup['15a6','5-90']['space'],'operating_archive')
        self.assertEqual(lookup['15a6','5-90']['perspective'],'reported-memory-nana')
        self.assertEqual(lookup['15a10','5-168']['perspective'],'objective-unheard-by-mio')
        self.assertEqual(lookup['14a12','4-173']['space'],'dining_room')
        self.assertNotIn(('14a12','4-174'),lookup)
        self.assertEqual(lookup['13d','R3-11']['space'],'hotel_corridor')

    def test_bounded_current_shots_and_all_catalog_audited(self):
        self.assertEqual(len(self.result['cgAudit']),72)
        self.assertGreaterEqual(len(self.result['cgRanges']),40)
        ranges={}
        for shot in self.result['cgRanges']:
            self.assertTrue(shot['clearOnExit'])
            self.assertTrue(shot['clearOnInteractive'])
            self.assertFalse(shot['knowledgeGrant'])
            self.assertGreater(shot['endLineExclusive'],shot['startLine'])
            self.assertTrue((scenes.ROOT/shot['image']).is_file())
            ranges.setdefault(shot['source']['file'],[]).append(shot)
        for rows in ranges.values():
            rows=sorted(rows,key=lambda x:x['startLine'])
            for left,right in zip(rows,rows[1:]):
                self.assertLessEqual(left['endLineExclusive'],right['startLine'])

    def test_known_wrong_pixels_cannot_become_source_facts(self):
        bound={x['logical_id'] for x in self.result['cgRanges']}
        statuses={x['logical_id']:x['status'] for x in self.result['cgAudit']}
        for id in ['c2_props_normal','c6_descending_order','execution_c4_02']:
            self.assertNotIn(id,bound)
            self.assertEqual(statuses[id],'pixel-story-conflict')
        self.assertNotIn('c2_unshared_table',bound)
        self.assertNotIn('c3_after_two_absences',bound)

    def test_trial_and_ending_shots_do_not_predate_outcome(self):
        shots={x['logical_id']:x for x in self.result['cgRanges']}
        self.assertEqual(shots['c3_trial_contradiction']['startLine'],123)
        self.assertEqual(shots['c3_blindfold_test']['endLineExclusive'],56)
        self.assertEqual(shots['c3_information_custody']['source']['file'].split('_')[0],'13a12')
        self.assertFalse(shots['c3_information_custody']['catalogSourceMatchesCurrentBinding'])
        self.assertEqual(shots['c6_support_keep']['startLine'],380)
        self.assertEqual(shots['c6_support_stop']['startLine'],326)
        self.assertLessEqual(shots['c6_outside_not_resolution']['endLineExclusive'],518)
        for id,line in [('execution_c1_05',146),('execution_c2_05',82),('execution_c3_05',119),('execution_c4_05',85),('execution_c5_05',63)]:
            self.assertEqual(shots[id]['startLine'],line)

    def test_source_changes_require_review(self):
        old=scenes.REVIEWED_SOURCE_HASHES['16d2']
        try:
            scenes.REVIEWED_SOURCE_HASHES['16d2']='0'*64
            with self.assertRaisesRegex(ValueError,'manuscript changed'):
                scenes.build_more()
        finally:
            scenes.REVIEWED_SOURCE_HASHES['16d2']=old

    def test_all_current_freetime_node_sources_have_a_reviewed_place(self):
        import json
        index=json.loads((scenes.ROOT/'data/v4_story/freetime/index.json').read_text(encoding='utf-8'))['meetings']
        self.assertGreaterEqual(len(index),73)
        for key,entry in index.items():
            graph=json.loads((scenes.ROOT/'data/v4_story'/entry['path']).read_text(encoding='utf-8'))
            for node in graph['nodes'].values():
                ref=node.get('source')
                if not ref or node.get('type') not in ['say','stage']:continue
                matches=[r for r in self.result['sceneRanges'] if r['source']['file']==ref['file'] and r['startLine']<=ref['line']<r['endLineExclusive']]
                self.assertEqual(len(matches),1,(key,node['id'],ref))
                self.assertEqual(matches[0]['source']['fileSha256'],ref['fileSha256'])

    def test_freetime_choices_keep_actual_mio_location(self):
        def space(prefix,line):
            return next(x['space'] for x in self.result['sceneRanges'] if x['source']['file'].startswith(prefix+'_') and x['startLine']<=line<x['endLineExclusive'])
        self.assertEqual(space('26',419),'hotel_lobby')
        self.assertEqual(space('26',507),'laundry_room')
        self.assertEqual(space('39',9),'guest_room')
        self.assertEqual(space('39',13),'laundry_room')
        self.assertEqual(space('39',27),'hotel_lobby')
        self.assertEqual(space('57',144),'hotel_corridor')
        self.assertEqual(space('57',174),'hotel_lobby') # Nana/Haruka leave; Mio stays.
        self.assertEqual(space('63',359),'plaza')
        self.assertEqual(space('63',459),'guest_room')
        self.assertEqual(space('52',257),'hotel_corridor')
        self.assertEqual(space('52',263),'kitchen')
        for line in [278,306,338,390,402]:self.assertEqual(space('59',line),'park_garden')
        for line in [256,282,326,342,376]:self.assertEqual(space('59',line),'ticket_booth')
        self.assertEqual(space('42',363),'park_garden')
        self.assertEqual(next(x for x in self.result['sceneRanges'] if x['source']['file'].startswith('45_') and x['startLine']==369)['perspective'],'objective-unseen-by-mio')


if __name__=='__main__':
    unittest.main()
