"""Original circular court shell for real runtime orbital shots; Blender background only."""
import bpy
import math
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art/space_v4/court_intro_v1'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
M = {}
for name, color, metal, emission in [
    ('ink', (.025, .033, .065, 1), .2, 0),
    ('floor', (.035, .055, .11, 1), .45, 0),
    ('blue', (.045, .11, .22, 1), .35, 0),
    ('violet', (.13, .055, .19, 1), .3, 0),
    ('gold', (.42, .29, .12, 1), .7, 0),
    ('cyan', (.05, .65, .82, 1), .2, .8),
    ('window', (.22, .15, .45, 1), .1, .45),
    ('rose', (.3, .05, .15, 1), .3, 0),
]:
    mat = bpy.data.materials.new('court_' + name)
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = color
    bs.inputs['Metallic'].default_value = metal
    bs.inputs['Roughness'].default_value = .48
    bs.inputs['Emission Color'].default_value = color
    bs.inputs['Emission Strength'].default_value = emission
    M[name] = mat


def cube(name, loc, size, mat, angle=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    obj.rotation_euler.z = angle
    obj.data.materials.append(M[mat])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new('edge light', 'BEVEL')
    bevel.width = .025
    bevel.segments = 2
    return obj


def disc(name, radius, depth, z, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=radius, depth=depth, location=(0, 0, z))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(M[mat])
    return obj


def ring(name, radius, z, thickness, mat):
    bpy.ops.mesh.primitive_torus_add(major_segments=96, minor_segments=6, location=(0, 0, z), major_radius=radius, minor_radius=thickness)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(M[mat])


disc('outer floor', 13, .22, -.14, 'ink')
disc('raised central stage', 6.9, .18, -.01, 'blue')
disc('inlaid center', 4.65, .025, .095, 'floor')
for r in [1.5, 3.1, 4.6, 6.7, 7.4, 8.4, 9.4, 12.5]:
    ring('concentric stage rim', r, .115 if r < 6.9 else .005, .026 if r < 7 else .045, 'cyan' if r in [3.1, 6.7, 8.4, 12.5] else 'gold')
for i in range(32):
    a = i * math.tau / 32
    cube('radial floor inlay', (5.6 * math.sin(a), 5.6 * math.cos(a), .096), (.025, 2.6, .008), 'gold', -a)

# Tangent wall bays have actual depth, recessed glazing, mullions and projecting columns.
for i in range(16):
    a = i * math.tau / 16
    sx, sy = math.sin(a), math.cos(a)
    def bay(name, radius, z, size, mat):
        return cube(name, (radius * sx, radius * sy, z), size, mat, -a)
    bay('wall bay', 12.85, 5.2, (5.15, .35, 10.4), 'ink')
    bay('wall lower panel', 12.58, 1.2, (4.8, .15, 2.3), 'blue')
    bay('recessed window', 12.62, 6.3, (3.5, .08, 6.5), 'window')
    for x in [-1.85, 1.85]:
        o = bay('window jamb', 12.45, 6.3, (.15, .18, 6.8), 'gold')
        o.location.x += x * math.cos(a)
        o.location.y -= x * math.sin(a)
    for z in [3.0, 4.6, 6.3, 8.0, 9.6]:
        bay('window transom', 12.42, z, (3.8, .18, .1), 'blue')
    for x in [-.9, 0, .9]:
        o = bay('window mullion', 12.4, 6.3, (.065, .2, 6.5), 'ink')
        o.location.x += x * math.cos(a)
        o.location.y -= x * math.sin(a)
    b = a + math.pi / 16
    cube('projecting pillar', (12.3 * math.sin(b), 12.3 * math.cos(b), 5.3), (.44, .6, 10.6), 'violet', -b)
for z, r, mat in [(.2, 12.4, 'gold'), (2.5, 12.4, 'cyan'), (10.0, 12.3, 'gold'), (10.5, 12.4, 'cyan')]:
    ring('architectural cornice', r, z, .09, mat)

cube('host dais', (0, 8.8, 1.4), (3.6, 2.1, 2.8), 'ink')
cube('host chair seat', (0, 8.9, 3.1), (1.65, 1.3, .35), 'rose')
cube('host chair back', (0, 9.45, 4.2), (1.8, .28, 2.7), 'violet')
for x in [-.96, .96]:
    cube('host gold frame', (x, 9.4, 4.2), (.1, .35, 2.9), 'gold')

# Combine by material to keep draw calls bounded without flattening any geometry.
for obj in list(bpy.context.scene.objects):
    if obj.type == 'MESH':
        bpy.context.view_layer.objects.active = obj
        for mod in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
for mat in M.values():
    group = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.data.materials and o.data.materials[0] == mat]
    if not group:
        continue
    bpy.ops.object.select_all(action='DESELECT')
    for o in group:
        o.select_set(True)
    bpy.context.view_layer.objects.active = group[0]
    bpy.ops.object.join()
    group[0].name = 'architecture_' + mat.name

bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'courtroom_stage.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT / 'courtroom_stage.glb'), export_format='GLB', export_apply=True)
(OUT / 'manifest.json').write_text(json.dumps({
    'source': 'tools/build_nonstop_courtroom.py',
    'original_geometry': True,
    'mesh': 'courtroom_stage.glb',
    'podium_mesh': 'debate_podium.glb',
    'podium_source': 'tools/build_debate_podium.py',
    'podium_radius': 3.95,
    'actor_foot_radius': 4.08,
    'wall_radius': 12.85,
    'wall_height': 10.4,
    'axes': 'Blender Z-up exported to standard glTF Y-up',
    'scope': '3D architecture and individual 3D podiums, 2D characters remain separate runtime billboards',
}, indent=2) + '\n', encoding='utf-8')
print('Original 3D court shell exported; podiums stay independent runtime meshes.')
