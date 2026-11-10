"""Retain exact HDR emitter bodies in completed early bake outputs."""
from pathlib import Path
import sys,json
from v4_lowpoly_glb import read,write,Copier
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/lowpoly_v1';catalog=json.loads((R/'art/space_v4/materials_v2/manifest.json').read_text())['assets']
for stem in sys.argv[1:]:
 row=next(r for r in catalog if Path(r['runtime']).stem==stem);source=R/row['file'];dest=O/'models'/Path(row['file']).name
 h,hb=read(source);l,lb=read(dest);emitters={n['name']:n for n in h['nodes'] if 'mesh'in n and all('light'in h['materials'][p['material']].get('name','').lower() for p in h['meshes'][n['mesh']]['primitives'])}
 copier=Copier(l)
 for node in copier.j['nodes']:
  if 'mesh'not in node:continue
  if node['name']in emitters:node['mesh']=copier.copy(h,hb,'meshes',emitters[node['name']]['mesh'],'high')
  else:node['mesh']=copier.copy(l,lb,'meshes',node['mesh'],'low')
 write(dest,copier.j,bytes(copier.b));print('Exact emitters retained',stem,len(emitters))
