"""Expand reviewed choice synopses into their performed dialogue."""

import json
from pathlib import Path

from build_v4_story import SPEAKERS


SOURCE = Path(__file__).resolve().parents[1] / 'data/revised_choice_dialogue.json'


def apply_choice_dialogue(chapters, document=None, *, introductions=None):
    if document is None:
        document = json.loads(SOURCE.read_text(encoding='utf-8'))
    if document.get('schemaVersion') != 1:
        raise ValueError('Unsupported V5 choice dialogue version')
    seen = set()
    for response in document['responses']:
        ident = response['id']
        if ident in seen:
            raise ValueError(f'Duplicate V5 choice dialogue: {ident}')
        seen.add(ident)
        nodes = chapters[response['chapter']]['nodes']
        original = nodes[ident]
        if (original['type'] != 'say' or original.get('actor') != 'mio'
                or not original.get('mono') or original['text'] != response['expected']):
            raise ValueError(f'Changed V5 choice synopsis: {ident}')
        if original.keys() - {'id', 'type', 'actor', 'speaker', 'mono', 'text', 'next', 'source'}:
            raise ValueError(f'Choice dialogue would discard authored behavior: {ident}')
        script = response['script']
        if not script:
            raise ValueError(f'Empty V5 choice dialogue: {ident}')
        addresses = [ident, *(f'{ident}:dialogue:{index}' for index in range(1, len(script)))]
        if any(address in nodes for address in addresses[1:]):
            raise ValueError(f'Choice dialogue address collision: {ident}')
        for index, speech in enumerate(script):
            if (speech.keys() - {'actor', 'speaker', 'text', 'mono'}
                    or SPEAKERS.get(speech['speaker']) != speech['actor']
                    or not isinstance(speech['text'], str) or not speech['text'].strip()
                    or ('mono' in speech and speech['mono'] is not True)
                    or (speech.get('mono') and speech['actor'] != 'mio')):
                raise ValueError(f'Invalid V5 choice speech: {ident}, {index}')
            # Preserve the response entry address used by existing saves and choices.
            address = addresses[index]
            performed = dict(speech)
            reveal = (introductions or {}).get(speech['actor'])
            if response['chapter'] == 'P' and reveal is not None and original['source']['line'] < reveal:
                performed['speaker'] = '???'
            nodes[address] = {'id': address, 'type': 'say', **performed,
                              'next': addresses[index + 1] if index + 1 < len(script) else original['next'],
                              'source': dict(original['source'])}
