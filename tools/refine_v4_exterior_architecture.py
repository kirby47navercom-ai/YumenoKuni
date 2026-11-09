"""Low-frequency architectural relief on existing park facades.

Called by build_v4_exterior_context.py in an isolated Blender process. Original
meshes, transforms, doors, target objects and collision data are untouched.
The existing material palette is reused so joining the context adds no materials.
"""
import math
import bpy


def refine(world, layout, specs):
    mats = {key: bpy.data.materials['yk_' + key]
            for key in ('ink', 'ivory', 'gold', 'purple', 'paper')}
    additions = []

    def mesh(name, vertices, faces, parent, material):
        data = bpy.data.meshes.new(name)
        data.from_pydata(vertices, [], faces)
        data.update()
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = parent
        obj.data.materials.append(mats[material])
        additions.append(obj)
        return obj

    def box(name, center, size, parent, material):
        x, y, z = (value / 2 for value in size)
        obj = mesh(name, [(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),
                          (-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)],
                   [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),
                    (2,3,7,6),(3,0,4,7)], parent, material)
        obj.location = center
        # Broad silhouette bevels survive a distant gameplay camera. No tiny
        # stamped textures or additional independent runtime actors.
        bevel = obj.modifiers.new('soft_stone_edge', 'BEVEL')
        bevel.width = min(.025, min(size) / 4)
        bevel.segments = 2
        return obj

    def arch(name, x, y, z, radius, rise, parent):
        # A real extruded elliptical moulding: front/back strips and inner/outer
        # returns. The opening and original window stay visible under the arch.
        vertices = []
        n, thickness, depth = 16, .085, .095
        for back in (0, 1):
            for outer in (0, 1):
                for i in range(n + 1):
                    a = math.pi * i / n
                    vertices.append((x + (radius + outer*thickness)*math.cos(a),
                                     y + back*depth,
                                     z + (rise + outer*thickness)*math.sin(a)))
        faces = []
        stride = n + 1
        for i in range(n):
            a, b, c, d = i, stride+i, 2*stride+i, 3*stride+i
            faces.extend([(a,a+1,b+1,b),(c,d,d+1,c+1),
                          (a,c,c+1,a+1),(b,b+1,d+1,d)])
        faces.extend([(0,stride,3*stride,2*stride),
                      (n,2*stride+n,3*stride+n,stride+n)])
        return mesh(name, vertices, faces, parent, 'ivory')

    facades = []
    for instance in layout['instances']:
        parent = bpy.data.objects.get('facade_' + instance['id'])
        if parent is None:
            continue
        width, depth, height = specs[instance['asset_id']]['size_m']
        front = -depth/2 - .19
        # Stepped fascia and deep shadow returns give the roof a supported edge.
        for side in (-1, 1):
            box('finish_eave_return', (side*(width/2+.15),0,height+.12),
                (.24,depth+.48,.20), parent, 'ivory')
            box('finish_eave_ink', (side*(width/2+.17),0,height+.015),
                (.27,depth+.52,.045), parent, 'ink')
        for z, projection, tall, material in (
                (height+.12,.28,.20,'ivory'),
                (height+.015,.31,.045,'ink'),
                (height-.075,.19,.08,'gold')):
            box('finish_front_cornice', (0,front-.035,z),
                (width+.42,projection,tall), parent, material)
        for side in (-1, 1):
            x, window_width = side*width*.3, min(2,width*.22)
            for edge in (-1, 1):
                box('finish_window_jamb',
                    (x+edge*(window_width/2+.075),front-.075,1.65),
                    (.105,.14,1.47), parent, 'ivory')
            arch('finish_window_arch',x,front-.15,2.34,
                 window_width/2+.035,.25,parent)
            box('finish_window_keystone',(x,front-.16,2.62),
                (.16,.18,.23),parent,'gold')
            box('finish_window_sill',(x,front-.13,.9),
                (window_width+.42,.43,.105),parent,'ivory')
            for dx in (-window_width*.32,window_width*.32):
                # Tapered rather than cuboid sill corbels.
                verts=[(x+dx-.075,front-.04,.82),(x+dx+.075,front-.04,.82),
                       (x+dx-.075,front-.27,.82),(x+dx+.075,front-.27,.82),
                       (x+dx-.055,front-.04,.58),(x+dx+.055,front-.04,.58)]
                mesh('finish_sill_corbel',verts,
                     [(0,2,3,1),(0,1,5,4),(0,4,2),(1,3,5),(2,4,5,3)],
                     parent,'ivory')
            # A shallow recessed-look panel remains inside the existing solid
            # window bay. The central doorway is never covered.
            box('finish_base_panel',(x,front-.025,.43),
                (window_width+.18,.06,.5),parent,'purple')
            for dz in (-.265,.265):
                box('finish_panel_rail',(x,front-.065,.43+dz),
                    (window_width+.3,.075,.045),parent,'ivory')
        facades.append(instance['id'])
    # object.join only keeps the active object's modifier stack. Bake our small
    # bevels before the common context compiler joins all material-compatible parts.
    graph = bpy.context.evaluated_depsgraph_get()
    bevelled = 0
    for obj in additions:
        if obj.modifiers:
            original = obj.data
            obj.data = bpy.data.meshes.new_from_object(obj.evaluated_get(graph))
            obj.modifiers.clear()
            if original.users == 0:
                bpy.data.meshes.remove(original)
            bevelled += 1
    return {'facades':facades,'addedMeshParts':len(additions),'bakedBevelParts':bevelled,
            'policy':'Existing facade-local architectural relief only; original geometry, portals, target positions and collision untouched; existing materials reused; joined context export.'}
