"""Apply reviewed V5 performances to stable dialogue addresses."""

import json
from pathlib import Path
import re

from build_v4_story import SPEAKERS
from v4_acting_bindings import BLOCKED, direction_choice, speech_choice
from v4_dialogue_presence import continue_live_replies


SOURCE = Path(__file__).resolve().parents[1] / 'data/revised_dialogue_direction.json'


def source_performances(scenes):
    selected = json.loads((SOURCE.parent.parent / 'art/character_delivery_v4/manifest.json').read_text(encoding='utf-8'))
    assets = {row['character'] + '_' + row['pose'] for row in selected['selected_poses']}
    bindings = {}
    for scene in scenes.values():
        for offset, raw in enumerate(scene.body):
            match = re.match(r'^\s*\*\*([^*]+)\*\*　(\S.*)$', raw)
            if not match:
                continue
            name, text = match.groups()
            actor = SPEAKERS.get(name)
            if not actor:
                continue
            if actor == 'mio' and not re.match(r'^0[1-6]-[TR]', scene.id):
                continue
            chosen = speech_choice(text, name)
            previous = offset - 1
            while previous >= 0 and not scene.body[previous].strip():
                previous -= 1
            quote, proof_line = raw, scene.line + offset + 1
            if previous >= 0 and scene.body[previous].strip().startswith(('(', '（')):
                direction = scene.body[previous].strip()
                direct = direction_choice(direction, name, actor)
                if direct:
                    chosen, quote, proof_line = direct, direction, scene.line + previous + 1
            if not chosen:
                continue
            suffix, reason, clause = chosen
            key = actor + '_' + suffix
            if key not in assets or (actor, suffix) in BLOCKED:
                continue
            bindings[(scene.id, scene.line + offset + 1)] = {
                'actor': actor, 'text': text.replace('**', ''), 'pose': key,
                'file': scene.file, 'line': proof_line, 'quote': quote,
                'basis': reason, 'clause': clause,
            }
    return bindings


def apply_dialogue_direction(chapters, tasks, scenes):
    bindings = source_performances(scenes)
    document = json.loads(SOURCE.read_text(encoding='utf-8'))
    selected = json.loads((SOURCE.parent.parent / 'art/character_delivery_v4/manifest.json').read_text(encoding='utf-8'))
    assets = {row['character'] for row in selected['actors']}
    assets.update(row['character'] + '_' + row['pose'] for row in selected['selected_poses'])
    stances = document.get('sceneStances', {})
    for scene, actors in stances.items():
        if scene not in scenes:
            raise ValueError(f'Missing V5 performance scene: {scene}')
        for actor, pose in actors.items():
            if pose not in assets or not pose.startswith(actor + '_') or (actor, pose.removeprefix(actor + '_')) in BLOCKED:
                raise ValueError(f'Invalid V5 scene performance: {scene}, {pose}')

    def bind(value):
        if isinstance(value, list):
            for item in value:
                bind(item)
        elif isinstance(value, dict):
            source = value.get('source', {})
            record = bindings.get((source.get('location'), source.get('line')))
            if (record and not value.get('mono') and not value.get('pose')
                    and value.get('actor') == record['actor'] and value.get('text') == record['text']):
                value['pose'] = record['pose']
            elif value.get('type') == 'say' and not value.get('mono') and not value.get('pose'):
                pose = stances.get(source.get('location'), {}).get(value.get('actor'))
                if pose:
                    value['pose'] = pose
            for item in value.values():
                if isinstance(item, (dict, list)):
                    bind(item)

    bind(chapters)
    bind(tasks)
    allowed = {'pose', 'delivery', 'dialogueShot'}
    for cue in document['cues']:
        if 'task' in cue:
            if 'path' in cue:
                node = tasks[cue['task']]
                for part in cue['path']:
                    node = node[part]
                candidates = [node]
            else:
                candidates = [tasks[cue['task']]['queues'][cue['queue']][cue['index']]]
        else:
            candidates = [node for node in chapters[cue['chapter']]['nodes'].values()
                          if node['type'] == 'say'
                          and node.get('source', {}).get('location') == cue['scene']
                          and node.get('actor') == cue['actor']
                          and node['text'] == cue['text']]
        if not candidates:
            raise ValueError(f'Missing reviewed V5 performance: {cue}')
        performance = cue['performance']
        if not performance or not performance.keys() <= allowed:
            raise ValueError(f'Invalid V5 performance: {cue}')
        if 'delivery' in performance and performance['delivery'] not in {
                'interrupt', 'challenge', 'resolve', 'quiet'}:
            raise ValueError(f'Unknown V5 dialogue delivery: {cue}')
        if 'dialogueShot' in performance and not 0 <= performance['dialogueShot'] <= 5:
            raise ValueError(f'Invalid V5 dialogue camera: {cue}')
        for node in candidates:
            if node.get('actor') != cue['actor'] or node['text'] != cue['text']:
                raise ValueError(f'Changed reviewed V5 speech: {cue}')
            if 'pose' in performance and not performance['pose'].startswith(node['actor'] + '_'):
                raise ValueError(f'Performance changes the displayed body: {cue}')
            if (node['actor'], performance.get('pose', '').removeprefix(node['actor'] + '_')) in BLOCKED:
                raise ValueError(f'Performance adds an unconfirmed prop or action: {cue}')
            node.update(performance)
    continue_live_replies(chapters, {}, assets)
