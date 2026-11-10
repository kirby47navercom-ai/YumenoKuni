"""논의 스크럼 「열쇠·원판」 장면(Claude 2026-11-06, 주인님 지시 「비슷하게든 뭐든 만들어라」, 사양서 27a).
근거 : 영상 HWGF48cBGF0 10.75~13.25초 — 푸른 강철 둥근 자물쇠(바깥 고리 + 받침 12개 + 청록 테) / 흰 손이 열쇠를 꽂아 돌림 /
안쪽 타일 원판이 청록 선(빈칸) → 노랑·초록 바람개비(3갈래) → 파랑 바탕 붉은 바람개비 + 초록. V3 는 모노쿠마 흰 장갑, 우리는 래피(흰 털 앞발).
실행 : blender -b --python tools/blender_scrum_lock.py -- <출력 폴더>   → 0001.png ~ 0078.png (1280x720, 30fps)
"""
import bpy, math, sys, os
out = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else os.path.abspath('scrum_lock')
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try: sc.render.engine = eng; break
    except TypeError: pass
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.fps = 30; sc.frame_start, sc.frame_end = 1, 78
if "--test" in sys.argv: sc.frame_set(1)
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = -0.6  # V3 : 어둡고 진한 색
sc.render.filepath = os.path.join(out, '')
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.01, 0.015, 0.03, 1)


def mat(name, color, metal=0.0, rough=0.5, emit=None, strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    if emit is not None:
        b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = strength
    return m


def tile_mat():  # 타일 색은 오브젝트 색(키프레임)으로
    m = bpy.data.materials.new('tile'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes.get('Principled BSDF')
    info = nt.nodes.new('ShaderNodeObjectInfo'); nt.links.new(info.outputs['Color'], b.inputs['Base Color'])
    nt.links.new(info.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 1.1; b.inputs['Roughness'].default_value = 0.3
    return m


steel = mat('steel', (0.06, 0.13, 0.26), 0.85, 0.35)
steel_d = mat('steel_d', (0.05, 0.08, 0.13), 0.8, 0.45)
cyan = mat('cyan', (0, 0.6, 0.8), emit=(0.1, 0.9, 1.0), strength=6)
silver = mat('silver', (0.8, 0.82, 0.86), 1.0, 0.15)
dark = mat('dark', (0.01, 0.01, 0.015), 0, 0.8)
fur = mat('fur', (0.95, 0.93, 0.95), 0, 0.9)
pink = mat('pink', (0.95, 0.6, 0.72), 0, 0.85)
tmat = tile_mat()
under = mat('under', (0.0, 0.3, 0.4), emit=(0.1, 0.9, 1.0), strength=0.0)


def add(obj, m): obj.data.materials.append(m); return obj


# 원판은 XZ 면, 앞(+Y)을 본다
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1.32, depth=0.3, location=(0, -0.05, 0), rotation=(math.pi / 2, 0, 0)); add(bpy.context.object, steel)
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.99, depth=0.32, location=(0, -0.04, 0), rotation=(math.pi / 2, 0, 0)); add(bpy.context.object, under)  # 타일 틈으로 보이는 바닥
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.018, location=(0, 0.12, 0), rotation=(math.pi / 2, 0, 0)); add(bpy.context.object, cyan)
bpy.ops.mesh.primitive_torus_add(major_radius=1.33, minor_radius=0.03, location=(0, 0.1, 0), rotation=(math.pi / 2, 0, 0)); add(bpy.context.object, steel_d)
for i in range(12):  # 바깥 받침(10.75·12.25초)
    a = i * math.tau / 12 + math.tau / 24
    bpy.ops.mesh.primitive_cube_add(size=1, location=(1.38 * math.cos(a), 0.06, 1.38 * math.sin(a)), rotation=(0, -a, 0)); o = bpy.context.object
    o.scale = (0.34, 0.26, 0.16); add(o, steel_d)
# 타일(일곱 겹, 바람개비 3갈래)
tiles = []
for ring in range(7):
    r0 = 0.26 + ring * 0.1; n = 14 + ring * 6
    for k in range(n):
        a = (k + 0.5) * math.tau / n; r = r0 + 0.045
        bpy.ops.mesh.primitive_cube_add(size=1, location=(r * math.cos(a), 0.13, r * math.sin(a)), rotation=(0, -a, 0)); o = bpy.context.object
        o.scale = (0.082, 0.03, r * math.tau / n * 0.86); add(o, tmat); tiles.append((o, r, a))
# 가운데 은빛 덮개 + T자 열쇠 구멍
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.24, location=(0, 0.14, 0)); cap = bpy.context.object; cap.scale = (1, 0.45, 0.55); add(cap, silver)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.25, 0.04)); o = bpy.context.object; o.scale = (0.22, 0.02, 0.05); add(o, dark)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.25, -0.06)); o = bpy.context.object; o.scale = (0.05, 0.02, 0.16); add(o, dark)
# 뒤 벽(푸른 기계)
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, -0.6, 0), rotation=(math.pi / 2, 0, 0)); add(bpy.context.object, steel_d)
# 오른쪽 손잡이 막대(10.75초)
bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=1.6, location=(2.1, 0.1, 0.55), rotation=(0, math.pi / 2, 0)); add(bpy.context.object, steel)
# 열쇠 + 래피 앞발(흰 털, 분홍 발바닥)
key = bpy.data.objects.new('key', None); sc.collection.objects.link(key)
parts = []
bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.5, location=(0, 0, 0), rotation=(math.pi / 2, 0, 0)); parts.append(add(bpy.context.object, silver))
bpy.ops.mesh.primitive_torus_add(major_radius=0.11, minor_radius=0.03, location=(0, 0.32, 0), rotation=(0, 0, 0)); parts.append(add(bpy.context.object, silver))
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.2, -0.05)); o = bpy.context.object; o.scale = (0.03, 0.06, 0.1); parts.append(add(o, silver))
for p in parts: p.parent = key
paw = bpy.data.objects.new('paw', None); sc.collection.objects.link(paw)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0.12, 0.38, 0)); h = bpy.context.object; h.scale = (1.1, 0.9, 0.9); add(h, fur); h.parent = paw
bpy.ops.mesh.primitive_cylinder_add(radius=0.17, depth=2.2, location=(1.2, 0.5, -0.25), rotation=(0, math.radians(72), math.radians(-10))); add(bpy.context.object, fur).parent = paw
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, location=(0.0, 0.42, 0.05)); add(bpy.context.object, pink).parent = paw
paw.parent = key
# 움직임 : 1~18 옆 근접(빈 원판), 19~34 열쇠를 꽂음, 34~42 돌림, 43~60 노랑·초록, 61~78 파랑·빨강
def kf(o, f, loc=None, rot=None):
    if loc: o.location = loc; o.keyframe_insert('location', frame=f)
    if rot is not None: o.rotation_euler = rot; o.keyframe_insert('rotation_euler', frame=f)
kf(key, 1, (3.5, 1.6, -0.6), (0, 0, 0)); kf(key, 19, (2.2, 1.2, -0.3), (0, 0, 0)); kf(key, 34, (0, 0.3, 0), (0, 0, 0)); kf(key, 42, (0, 0.3, 0), (0, math.pi / 2, 0)); kf(key, 52, (0, 0.3, 0), (0, math.pi / 2, 0)); kf(key, 60, (2.5, 1.5, -1.0), (0, math.pi / 2, 0))
def phase_color(r, a, phase):
    u = (3 * a / math.tau + r * 0.95) % 1.0
    if phase == 0: return (0.004, 0.008, 0.014)
    if phase == 1: return (1.0, 0.75, 0.0) if u < 0.5 else (0.02, 0.55, 0.04)
    return (0.95, 0.05, 0.02) if u < 0.32 else ((0.02, 0.55, 0.06) if u < 0.4 and r > 0.7 else (0.03, 0.3, 0.85))
for o, r, a in tiles:
    for f, ph in ((1, 0), (42 + int(r * 10), 0), (44 + int(r * 10), 1), (60 + int(r * 8), 1), (62 + int(r * 8), 2)):
        o.color = (*phase_color(r, a, ph), 1); o.keyframe_insert('color', frame=f)
b = under.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength']
for f, v in ((1, 0.0), (18, 0.0), (22, 6.0), (42, 6.0), (48, 0.0)):
    b.default_value = v; b.keyframe_insert('default_value', frame=f)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 35
tgt = bpy.data.objects.new('tgt', None); sc.collection.objects.link(tgt)
c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
kf(cam, 1, (2.2, 1.6, 0.3)); kf(tgt, 1, (0.2, 0, 0.1)); kf(cam, 18, (2.0, 1.9, 0.25)); kf(tgt, 18, (0.25, 0, 0.1))
kf(cam, 19, (0.25, 3.3, 0.0)); kf(tgt, 19, (0.1, 0, 0)); kf(cam, 60, (0.1, 3.0, 0.0)); kf(tgt, 60, (0, 0, 0))
kf(cam, 61, (0.0, 3.0, 0.0)); kf(cam, 78, (0.0, 3.6, 0.15)); kf(tgt, 78, (0, 0, 0))
for o in (cam,):
    if o.animation_data:
        for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action, 'fcurves') else []:
            for p in fc.keyframe_points: p.interpolation = 'BEZIER'
for loc, e, s in (((1.5, 3.5, 2.0), 260, 2.0), ((-2.5, 2.0, -1.0), 140, 2.0), ((0, 1.0, 3.0), 90, 1.5)):
    L = bpy.data.lights.new('l', 'AREA'); L.energy = e; L.size = s; lo = bpy.data.objects.new('l', L); sc.collection.objects.link(lo); lo.location = loc
    t = lo.constraints.new('TRACK_TO'); t.target = tgt; t.track_axis = 'TRACK_NEGATIVE_Z'; t.up_axis = 'UP_Y'
bpy.ops.render.render(animation=True)
print('rendered to', out)
