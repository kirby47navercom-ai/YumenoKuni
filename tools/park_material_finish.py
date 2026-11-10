import bpy,math,re
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
PALETTES={
 'fairytale':{'wall':(.98,.83,.60),'accent':(.84,.32,.38),'utility':(.48,.72,.66),'roof':(.64,.78,.94),'metal':(.42,.59,.66)},
 'carnival':{'wall':(.98,.83,.58),'accent':(.85,.20,.24),'utility':(.37,.55,.81),'roof':(.66,.74,.91),'metal':(.42,.55,.68)},
 'mirrors':{'wall':(.87,.83,.98),'accent':(.60,.36,.79),'utility':(.37,.70,.73),'roof':(.65,.64,.90),'metal':(.48,.63,.75)},
 'clockwork':{'wall':(.96,.83,.57),'accent':(.87,.43,.20),'utility':(.42,.64,.62),'roof':(.66,.79,.81),'metal':(.51,.65,.71)},
 'starlight':{'wall':(.86,.94,1),'accent':(.26,.58,.86),'utility':(.28,.76,.78),'roof':(.58,.75,.98),'metal':(.55,.74,.87)},
 'perimeter':{'wall':(.85,.81,.66),'accent':(.69,.49,.31),'utility':(.52,.66,.58),'roof':(.62,.72,.75),'metal':(.48,.59,.63)}}
STATS={}
def role(name):
 n=re.sub(r'\.\d+$','',name).split('__finish5_')[0]
 if any(k in n for k in ['foliage','grass','leaf','bark','paving','planting_soil','ornament_print','generated_']):return 'preserve'
 if any(k in n for k in ['glass','mirror','light','bulb']):return 'preserve'
 if n.startswith(('architecture_hotel_','architecture6_')):return 'preserve'
 if n in ['form_slate','form_copper','form_painted_steel','rebuilt_roof']:return 'roof'
 if n in ['form_ivory','form_sandstone','park_cream']:return 'wall'
 if n=='form_clinical':return 'clinical'
 if n=='form_utility':return 'utility'
 if n in ['form_terracotta','park_brick']:return 'accent'
 if 'cream_trim'in n or n in ['theme_v2_ivory','theme_v2_cream_paint']:return 'trim'
 if 'canvas'in n or n=='rebuilt_linen':return 'canvas'
 if any(k in n for k in ['gold','brass','copper']):return 'gold'
 if any(k in n for k in ['iron','steel']):return 'metal'
 if 'wood'in n:return 'wood'
 if 'cloth'in n:return 'cloth'
 return 'paint'
def texture_for(bs):
 # Follow the actual base-colour graph, not an unrelated first normal image.
 seen=set()
 def walk(node):
  if node in seen:return None
  seen.add(node)
  if node.type=='TEX_IMAGE'and node.image:return node
  for i in node.inputs:
   for l in i.links:
    q=walk(l.from_node)
    if q:return q
  return None
 return walk(bs.inputs['Base Color'].links[0].from_node)if bs.inputs['Base Color'].links else None

def configure(m,theme):
 bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)if m.node_tree else None
 if not bs:return False
 typ=role(m.name);p=PALETTES[theme];tint=list(m.get('surfaceTint',bs.inputs['Base Color'].default_value))
 tex=texture_for(bs)
 if typ in ['wall','accent','utility','roof','metal']:tint=[*p[typ],1]
 elif typ=='clinical':tint=[.78,.98,.91,1]
 elif typ=='trim':tint=[1,.94,.78,1]
 elif typ=='gold':tint=[.91,.68,.26,1]
 elif typ=='canvas':tint=[1,.97,.87,1]if 'ivory'in m.name or 'linen'in m.name else [*(p['accent']if 'coral'in m.name else(.20,.40,.80)),1]
 elif typ=='paint':
  n=m.name
  for key,col in [('coral',p['accent']),('cobalt',(.22,.43,.78)),('violet',(.57,.33,.77)),('mint',(.33,.72,.57)),('park_red',(.86,.20,.26)),('park_blue',(.22,.43,.78)),('park_violet',(.57,.33,.77)),('park_teal',(.23,.70,.68))]:
   if key in n:tint=[*col,1];break
 # Restore tint wiring even for preserved materials, without multiplying twice.
 if tex and (typ!='preserve' or m.get('surfaceTint')):
  for l in list(bs.inputs['Base Color'].links):m.node_tree.links.remove(l)
  mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.name='finish5_authored_pigment';mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=tint;m.node_tree.links.new(tex.outputs['Color'],mix.inputs[1]);m.node_tree.links.new(mix.outputs[0],bs.inputs['Base Color']);m['surfaceTint']=tint
 if typ=='preserve':return True
 rough={'wall':.82,'accent':.75,'clinical':.68,'utility':.74,'roof':.72,'metal':.46,'trim':.76,'canvas':.88,'gold':.42,'wood':.62,'cloth':.87,'paint':.48}[typ]
 metal={'gold':.45,'metal':.32,'roof':.08}.get(typ,0)
 bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
 # Recover the original spatial roughness texture discarded by the old finish.
 roughtex=next((n for n in m.node_tree.nodes if n.type=='TEX_IMAGE'and n.image and 'roughness'in n.image.name.lower()),None)
 if roughtex and not bs.inputs['Roughness'].links:
  roughtex.image.colorspace_settings.name='Non-Color';m.node_tree.links.new(roughtex.outputs['Color'],bs.inputs['Roughness'])
 for n in m.node_tree.nodes:
  if n.type=='NORMAL_MAP':
   n.inputs['Strength'].default_value={'wall':.55,'accent':.5,'clinical':.36,'utility':.50,'roof':.5,'metal':.28,'trim':.45,'canvas':.48,'gold':.26,'wood':.58,'cloth':.5,'paint':.18}[typ]
   for l in n.inputs['Color'].links:
    if l.from_node.type=='TEX_IMAGE'and l.from_node.image:l.from_node.image.colorspace_settings.name='Non-Color'
 m['surfaceMaterialRevision']=5;m['finish5Role']=typ;return True

def apply(root,theme):
 cache={};objects=[];repaired=0;meshes=0
 model=[root,*root.children_recursive]
 authored={mesh for owner in model if owner.get('architectureSourceSHA256') for mesh in owner.children_recursive}
 for o in model:
  if o.type!='MESH':continue
  # The reviewed Blender asset already owns its UVs and material assignments.
  # Unused Boolean slots are valid there and must not trigger a repaint.
  if o in authored:continue
  meshes+=1
  if o.data.users>1:o.data=o.data.copy()
  for slot in o.material_slots:
   old=slot.material
   if not old:raise AssertionError(('unassigned material',o.name))
   if role(old.name)=='preserve'and not old.get('surfaceTint'):continue
   if old not in cache:
    # Hotel and atlas materials retain identity for existing structural/UV gates.
    if old.name.startswith('architecture_hotel_')or 'ornament_print'in old.name:cache[old]=old;continue
    m=old.copy();m.name=re.sub(r'\.\d+$','',old.name).split('__finish5_')[0]+'__finish5_'+theme;configure(m,theme);cache[old]=m
   slot.material=cache[old]
  uv=o.data.uv_layers.active
  if not uv:uv=o.data.uv_layers.new(name='UVMap')
  for face in o.data.polygons:
   m=o.data.materials[face.material_index]
   if not m or any(k in m.name.split('__finish5_')[0] for k in ['ornament','foliage','identity','printed','mask','glass','mirror','light']):continue
   if len(face.loop_indices)!=3:continue
   ids=list(face.loop_indices);a,b,c=[uv.data[k].uv.copy()for k in ids];area=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))
   if area>=1e-10:continue
   axis=max(range(3),key=lambda k:abs(face.normal[k]));axes=[k for k in range(3)if k!=axis]
   for li in ids:
    v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]*.5,v[axes[1]]*.5)
   repaired+=1
  objects.append(o.name)
 return {'theme':theme,'meshObjectsChecked':meshes,'materialCopies':len(cache),'uvFacesRepaired':repaired,'geometryEdited':False,'checkedObjects':objects}
