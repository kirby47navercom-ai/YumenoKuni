"""Choice expansion keeps saved addresses, effects, and each branch's continuation."""

from copy import deepcopy
import unittest

from revised_choice_dialogue import apply_choice_dialogue


class ChoiceDialogueTest(unittest.TestCase):
    def setUp(self):
        self.chapters = {'P': {'nodes': {
            'menu': {'id': 'menu', 'type': 'menu', 'options': [
                {'id': 'A', 'to': 'response', 'set': {'choice': 'A'}},
                {'id': 'B', 'to': 'other', 'set': {'choice': 'B'}}]},
            'response': {'id': 'response', 'type': 'say', 'actor': 'mio', 'speaker': '미오',
                         'mono': True, 'text': '설명', 'next': 'tail',
                         'source': {'location': 'P02', 'line': 135}},
            'other': {'id': 'other', 'type': 'end'},
            'tail': {'id': 'tail', 'type': 'end'}}}}
        self.document = {'schemaVersion': 1, 'responses': [
            {'chapter': 'P', 'id': 'response', 'expected': '설명', 'script': [
                {'actor': 'rin', 'speaker': '린', 'text': '내 이름은 빼.'},
                {'actor': 'mio', 'speaker': '미오', 'text': '문만 적었어.'}]}]}

    def test_saved_entry_and_branch_effects(self):
        prior = deepcopy(self.chapters['P']['nodes'])
        apply_choice_dialogue(self.chapters, self.document)
        nodes = self.chapters['P']['nodes']
        self.assertEqual(nodes['menu'], prior['menu'])
        self.assertEqual(nodes['other'], prior['other'])
        self.assertEqual(nodes['tail'], prior['tail'])
        first = nodes[nodes['menu']['options'][0]['to']]
        second = nodes[first['next']]
        self.assertEqual((first['actor'], second['actor'], second['next']), ('rin', 'mio', 'tail'))
        self.assertNotIn('mono', first)
        self.assertEqual(first['source'], prior['response']['source'])

    def test_changed_source_and_unsafe_scripts_fail(self):
        for mutate in (
                lambda d: d['responses'][0].update(expected='이전 설명'),
                lambda d: d['responses'][0].update(script=[]),
                lambda d: d['responses'][0]['script'][0].update(actor='ken'),
                lambda d: d['responses'][0]['script'][0].update(set={'unearned': True}),
                lambda d: d['responses'].append(deepcopy(d['responses'][0]))):
            with self.subTest(mutate=mutate):
                document = deepcopy(self.document)
                mutate(document)
                with self.assertRaises(ValueError):
                    apply_choice_dialogue(deepcopy(self.chapters), document)

    def test_choice_does_not_reveal_an_unknown_speaker(self):
        apply_choice_dialogue(self.chapters, self.document, introductions={'rin': 200})
        first = self.chapters['P']['nodes']['response']
        self.assertEqual(first['actor'], 'rin')
        self.assertEqual(first['speaker'], '???')


if __name__ == '__main__':
    unittest.main()
