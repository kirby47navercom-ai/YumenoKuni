"""Source-preserving production adapters; the publisher owns all cooked writes."""
import json
import sys
from v4_acting_bindings import build_acting, bind_node
from v4_dedicated_spaces import apply_world, apply_placements
from v4_task_detail_bindings import apply_detail
from v4_noise_bindings import apply_noise
from v4_comic_presentation import build_comic, bind_task
from v4_dialogue_presence import apply as apply_dialogue_presence
from v4_dialogue_presence import continue_live_replies,ROOT
from v4_sound_direction import apply as apply_sound_direction

payload = json.load(sys.stdin)
from v4_inspection_illustrations import bind_runtime as bind_inspection_illustrations
payload = bind_inspection_illustrations(payload)
world = apply_world(payload['world'])
from v4_freetime_paths import apply as apply_freetime_paths
apply_freetime_paths(payload['world'])
from pathlib import Path
park_manifest=ROOT/'art/space_v4/park_levels_v1/manifest.json'
if park_manifest.exists()and json.loads(park_manifest.read_text(encoding='utf8')).get('geometryComplete'):
    from v4_park_levels import apply as apply_park_levels
    world['copies']+=apply_park_levels(payload['world'])['copies']
    from v4_park_story import adapt as adapt_park_story
    for graph in payload['graphs'].values():
        for node in graph['nodes'].values():adapt_park_story(node)
apply_placements(payload['graphs'])
comic = build_comic()
payload['native']['tasks'] = {key:bind_task(apply_noise(apply_detail(bundle)),comic) for key,bundle in payload['native']['tasks'].items()}
acting = build_acting()
for name in ('graphs', 'native', 'gifts'):
    payload[name] = bind_node(payload[name], acting)
apply_dialogue_presence(payload['graphs'])
continue_live_replies(payload['graphs'],json.loads((ROOT/'data/presentation/v4_scenes.json').read_text(encoding='utf-8')),acting['assets'])
apply_sound_direction(payload['graphs'], payload['native']['tasks'])
payload['copies'] = world['copies']
json.dump(payload, sys.stdout, ensure_ascii=False, separators=(',', ':'))
