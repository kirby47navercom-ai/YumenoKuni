"""Build the six park enclosures in Blender metres."""
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import v4_rebuilt_environment_kit as K
import theme_park_v2_kit as T

PARK = ROOT / 'art/space_v4/park_levels_v1'
OUTPUT = PARK / 'background'
PLINTH = .72
TOP = 7.2
SETBACK = .24


def material(key, color, emission=0):
    mat = bpy.data.materials.new(key)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = .72
    if emission:
        shader.inputs['Emission Color'].default_value = (*color, 1)
        shader.inputs['Emission Strength'].default_value = emission
    K.M[key] = mat


class SolidBatch:
    def __init__(self):
        self.vertices = []
        self.faces = []

    def box(self, x, y, z, width, depth, height):
        first = len(self.vertices)
        self.vertices.extend((x+dx*width/2,y+dy*depth/2,z+dz*height/2) for dx,dy,dz in
                             [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                              (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
        self.faces.extend(tuple(first+i for i in face) for face in
                          [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])

    def mesh(self, name, mat, parent):
        K.mesh(name,self.vertices,self.faces,mat,parent)


def surveillance_mount(parent, x):
    mount = T.root('CCTV mount',parent,(x,-.55,TOP+.8))
    T.tube('Camera support arm',[(0,.55,-.63),(0,0,-.08)],.11,'steel',mount,8)
    yaw = parent.rotation_euler.z
    xx = parent.location.x+x*math.cos(yaw)+.55*math.sin(yaw)
    yy = parent.location.y+x*math.sin(yaw)-.55*math.cos(yaw)
    return {'position':[xx,TOP+.8,-yy],'yaw':math.degrees(yaw)}


def surveillance_head(parent):
    camera = T.root('CCTV head',parent)
    # The front of the camera is local -Y, toward the playable side of the fence.
    camera.rotation_euler.x = math.radians(14)
    K.rounded_solid('Weatherproof CCTV body',.74,1.35,.56,'housing',camera,.08)
    K.rounded_solid('CCTV rain shield',.88,1.55,.10,'steel',camera,.04,(0,-.12,.30))
    T.tube('Black lens surround',[(0,-.66,0),(0,-.81,0)],.243,'steel',camera,12)
    T.tube('Visible optical lens',[(0,-.82,0),(0,-.85,0)],.174,'lens',camera,12)
    T.ball('Recording indicator',camera,(.27,-.74,.10),.065,'indicator')


def fence_run(root, x, y, yaw, length):
    parent = T.root('Locked perimeter run',root,(x,y,0),yaw)
    steel = SolidBatch()
    foot = SolidBatch()
    columns = math.ceil(length/7.8)
    span = length/columns
    cameras = []
    for bay in range(columns):
        left = -length/2+bay*span
        foot.box(left+span/2,0,PLINTH/2,span,.46,PLINTH)
        divisions = math.ceil(span/.62)
        for i in range(1,divisions):
            bx = left+span*i/divisions
            steel.box(bx,0,(PLINTH+TOP)/2,.115,.115,TOP-PLINTH)
            # Angled tips face the enclosure and break up the top silhouette.
            T.tube('Angled security tip',[(bx,0,TOP-.13),(bx,-.35,TOP+.55)],
                   .058,'steel',parent,4)
        steel.box(left,0,TOP/2,.29,.32,TOP)
        if bay%3==1:
            steel.box(left,0,TOP/2,.34,.38,TOP+1.16)
            cameras.append(surveillance_mount(parent,left))
    for height in (PLINTH+.14,3.68,TOP-.18):
        steel.box(0,0,height,length,.22,.19)
    foot.mesh('Continuous concrete footing','footing',parent)
    steel.mesh('Continuous steel bars and rails','steel',parent)
    return cameras


def ground(parent, rect, name):
    left, front, right, back = rect
    return K.mesh(name,[(left,front,-.025),(right,front,-.025),
                        (right,back,-.025),(left,back,-.025)],
                  [(0,1,2,3)],'court',parent,uv_scale=.21)


def build(district, bounds):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    K.setup_materials()
    K.M['court'] = K.M['paving'].copy()
    K.M['court'].name = 'enclosure_concrete'
    material('steel',(.068,.081,.095))
    material('footing',(.20,.22,.24))
    material('housing',(.60,.62,.64))
    material('lens',(.041,.11,.15))
    material('indicator',(.92,.026,.014),2)
    root = T.root('Steel enclosure and surveillance',None)
    west,south,east,north = bounds[0],-bounds[3],bounds[2],-bounds[1]
    outline = (west-1,south-1,east+1,north+1)
    if district == 'carnival':
        # Preserve the existing pool opening in the ground surface.
        left,front,right,back = 7.99,4.99,20.01,11.01
        x0,y0,x1,y1 = outline
        zones = [(x0,y0,x1,front),(x0,back,x1,y1),(x0,front,left,back),(right,front,x1,back)]
    else:
        zones = [outline]
    for zone in zones:
        ground(root,zone,'Utility paving')
    # The current movement limits already stop the player. Place the steel
    # immediately outside them so its footprint does not add invisible obstacles.
    width = east-west+2*SETBACK
    depth = north-south+2*SETBACK
    cameras = []
    for x,y,yaw,length in [
        ((west+east)/2,north+SETBACK,0,width),
        (east+SETBACK,(south+north)/2,-math.pi/2,depth),
        ((west+east)/2,south-SETBACK,math.pi,width),
        (west-SETBACK,(south+north)/2,math.pi/2,depth),
    ]:
        cameras.extend(fence_run(root,x,y,yaw,length))
    return root,cameras


def export_mesh(root, file):
    by_material = {}
    bpy.context.view_layer.update()
    for obj in root.children_recursive:
        if obj.type != 'MESH':
            continue
        matrix = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = matrix
        by_material.setdefault(obj.data.materials[0].name,[]).append(obj)
    selected = []
    for objects in by_material.values():
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()
        selected.append(objects[0])
    bpy.ops.object.select_all(action='DESELECT')
    for obj in selected:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = selected[0]
    temporary = file.with_name(file.stem+'.pending.glb')
    bpy.ops.export_scene.gltf(filepath=str(temporary),export_format='GLB',use_selection=True,export_tangents=True)
    return temporary,len(selected)


def export(district, root, cameras, bounds):
    file = OUTPUT/(district+'.glb')
    temporary,draw_groups = export_mesh(root,file)
    data = temporary.read_bytes()
    length = struct.unpack_from('<I',data,12)[0]
    document = json.loads(data[20:20+length])
    court = next(mat for mat in document['materials'] if mat['name']=='enclosure_concrete')
    court.setdefault('pbrMetallicRoughness',{})['baseColorFactor'] = [.36,.38,.41,1]
    chunk = json.dumps(document,separators=(',',':')).encode()
    chunk += b' '*(-len(chunk)%4)
    tail = data[20+length:]
    data = struct.pack('<IIIII',0x46546c67,2,20+len(chunk)+len(tail),len(chunk),0x4E4F534A)+chunk+tail
    temporary.write_bytes(data)
    temporary.replace(file)
    return dict(id=district,file=file.relative_to(ROOT).as_posix(),runtime='Assets/Art/park_levels/background/'+file.name,
                sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),drawGroups=draw_groups,
                cameras=cameras,bounds=bounds,fenceHeight=TOP,placementSetback=SETBACK)


OUTPUT.mkdir(exist_ok=True)
bank = json.loads((PARK/'manifest.json').read_text(encoding='utf8'))
rows = []
for row in bank['assets']:
    root,cameras = build(row['id'],row['bounds'])
    rows.append(export(row['id'],root,cameras,row['bounds']))
head = T.root('Shared CCTV head',None)
surveillance_head(head)
head_file = OUTPUT/'cctv-head.glb'
head_temporary,_ = export_mesh(head,head_file)
head_temporary.replace(head_file)
head_data = head_file.read_bytes()
head_manifest = OUTPUT/'cctv-head.json'
head_manifest.write_text(json.dumps({
    'file':head_file.relative_to(ROOT).as_posix(),
    'sha256':hashlib.sha256(head_data).hexdigest()
},indent=2)+'\n',encoding='utf8')
manifest = OUTPUT/'manifest.json'
temporary = manifest.with_suffix('.tmp')
temporary.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
temporary.replace(manifest)
