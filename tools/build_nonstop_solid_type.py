"""Run with Blender --background --python. Own licensed font, real closed meshes.

Front and rear caps plus extruded contour walls are geometry, not offset copies
of a glyph bitmap. The three palettes retain different face/side materials.
"""
import bpy
import json
from pathlib import Path
import sys
from mathutils import Matrix

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
ROOT = Path(__file__).resolve().parents[1]
revision = '--revision-labels' in sys.argv
OUT = ROOT / ('art/revision_kotodama' if revision else 'art/nonstop_solid_type')
OUT.mkdir(parents=True, exist_ok=True)
if revision:
    labels_path = Path(sys.argv[sys.argv.index('--revision-labels') + 1])
    texts = json.loads(labels_path.read_text(encoding='utf-8'))
else:
    direction = json.loads((ROOT / 'data/v4_story/trial_direction.json').read_text(encoding='utf-8'))
    tasks = json.loads((ROOT / 'data/v4_story/native_tasks.json').read_text(encoding='utf-8'))['tasks']
    texts = ['거짓 · ']
    for tid, task in tasks.items():
        if (task.get('debate') or {}).get('kind') != 'nonstop':
            continue
        for row in task['debate']['lines'] + direction.get('extra', {}).get(tid, []):
            entry = direction['debate'].get(row['id'], {})
            if entry.get('acting', '').startswith('assertive|'):
                texts.append(row['text'])
    for task in tasks.values():
        if task['stage']['kind'] == 'nonstop':
            texts.extend(o.get('name', '') for o in task['stage'].get('options', []))
            texts.extend(task.get('transformation', {}).get(k, '') for k in ['lieLabel', 'normalLabel'])
chars = sorted(set(''.join(texts)) - set(' \n\r\t'))
if revision:
    chars = [c for c in chars if not (ROOT / 'art/nonstop_solid_type' / f'u_{ord(c):x}_w.glb').is_file()]
font = bpy.data.fonts.load(str(ROOT / 'fonts/blackhansans/BlackHanSans-Regular.ttf'))


def material(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*rgb, 1)
    bs.inputs['Emission Color'].default_value = (*rgb, 1)
    bs.inputs['Emission Strength'].default_value = 1
    bs.inputs['Roughness'].default_value = 1
    return m


palettes = {'w': (1, 1, 1), 'y': (1, .74, .035), 'b': (.06, .6, 1)}
if revision:
    palettes = {'w': palettes['w']}
materials = {k: (material(k + '_face', c), material(k + '_wall', tuple(v * .24 for v in c))) for k, c in palettes.items()}
records = json.loads((OUT / 'manifest.json').read_text(encoding='utf8'))['glyphs'] if (OUT / 'manifest.json').exists() else []
existing = {r['codepoint'] for r in records}
for char in chars:
    if ord(char) in existing and all((OUT / f'u_{ord(char):x}_{c}.glb').exists() for c in palettes):
        continue
    curve = bpy.data.curves.new('letter', 'FONT')
    curve.body, curve.font, curve.size = char, font, 1
    curve.extrude, curve.bevel_depth, curve.bevel_resolution = .075, .006, 0
    curve.resolution_u = 4
    obj = bpy.data.objects.new('glyph', curve)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    # Text's front is +Z. Keep the front at z=0 and the walls behind it.
    bounds = [v.co for v in obj.data.vertices]
    lo = [min(v[i] for v in bounds) for i in range(3)]
    hi = [max(v[i] for v in bounds) for i in range(3)]
    for v in obj.data.vertices:
        v.co.x = (v.co.x - (lo[0] + hi[0]) / 2) / 10.0
        v.co.y = (v.co.y - (lo[1] + hi[1]) / 2) / 10.0
        v.co.z = (v.co.z - hi[2]) / 10.0
    obj.data.update()
    faces = [0 if abs(polygon.normal.z) > .9 else 1 for polygon in obj.data.polygons]
    # Blender's exporter converts Z-up to Y-up. Precompensate that basis.
    obj.data.transform(Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
    for palette, slots in materials.items():
        obj.data.materials.clear()
        for slot in slots:
            obj.data.materials.append(slot)
        for polygon, index in zip(obj.data.polygons, faces):
            polygon.material_index = index
        file = OUT / f'u_{ord(char):x}_{palette}.glb'
        bpy.ops.export_scene.gltf(filepath=str(file), export_format='GLB', use_selection=True, export_cameras=False, export_lights=False, export_extras=False)
    records.append({'codepoint': ord(char), 'vertices': len(obj.data.vertices), 'faces': len(obj.data.polygons), 'depth': (hi[2] - lo[2]) / 10.0})
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.curves.remove(curve) if curve.users == 0 else None
(OUT / 'manifest.json').write_text(json.dumps({'font': 'fonts/blackhansans/BlackHanSans-Regular.ttf', 'glyphs': records}, indent=2), encoding='utf-8')
print('SOLID_GLYPHS', len(records), flush=True)
