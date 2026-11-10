"""Select latest planned original-art versions, without counting revisions as extra story CGs."""
from pathlib import Path
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[1];F=ROOT/'art/v4_production/full';J=F/'builtin_jobs'
jobs=[json.loads(p.read_text(encoding='utf8')) for p in J.glob('*.json')]
canonical=lambda s:re.sub(r'_builtin_r\d+$','',s)
bases={canonical(j['id']):j for j in jobs if j.get('kind')!='targeted_revision'}
assert len(bases)>=75,('Unexpected logical cohort',len(bases))
selected=[];pending=[]
for key,base in sorted(bases.items()):
 versions=[j for j in jobs if canonical(j['id'])==key]
 latest=max(versions,key=lambda j:int(re.search(r'_r(\d+)$',j['id']).group(1)))
 mp=ROOT/'art/cg_v4/builtin'/(latest['id']+'.json')
 if not mp.exists():pending.append(latest['id']);continue
 meta=json.loads(mp.read_text(encoding='utf8'))
 for field in ['source_file','hd_file','delivery_file']:assert (ROOT/meta[field]).exists(),(latest['id'],field)
 assert (ROOT/meta['delivery_file']).with_suffix('.webp').exists()
 selected.append({'logical_id':key,'kind':base.get('kind','event'),'selected_id':latest['id'],'metadata':mp.relative_to(ROOT).as_posix(),'source':meta['source_file'],'raw_4x':meta['hd_file'],'delivery':meta['delivery_file'],'webp':Path(meta['delivery_file']).with_suffix('.webp').as_posix(),'size':meta['delivery_size'],'manuscript':meta['source'],'manuscript_sha256':meta.get('manuscript_sha256'),'source_review':'see builtin_visual_review.json; source inspection is distinct from runtime import','panel_grid':meta.get('panel_grid'),'panel_uv_rectangles':meta.get('panel_uv_rectangles'),'runtime_integrated':False})
spaces=json.loads((ROOT/'art/space_v4/full_v2/manifest.json').read_text(encoding='utf8'))
qa=json.loads((ROOT/'art/space_v4/full_v2/qa.json').read_text(encoding='utf8'))
backgrounds=[]
for name in [v for v in ['plates','plates_r3','plates_r4'] if (ROOT/f'art/bg_v4/{v}/manifest.json').exists()]:
 m=json.loads((ROOT/f'art/bg_v4/{name}/manifest.json').read_text(encoding='utf8'))
 for row in m['assets']:
  old=next((i for i,r in enumerate(backgrounds) if r['id']==row['id']),None)
  record={'id':row['id'],'source':row['source'],'delivery':row['hd_file'],'size':row.get('delivery_size'),'source_blend':row['source_blend'],'runtime_integrated':False}
  if not (ROOT/row['hd_file']).with_suffix('.webp').exists():pending.append('background:'+row['id'])
  if old is None:backgrounds.append(record)
  else:backgrounds[old]=record
assert len(backgrounds)==12
result={'status':'production files selected; source/HD and runtime acceptance recorded separately','logical_cg_required':len(bases),'logical_cg_files_ready':len(selected),'retained_cg_versions':len(list((ROOT/'art/cg_v4/builtin').glob('*.json'))),'pending_files':pending,'tool_policy':'built-in image_gen + local4x, Blender; NAI prohibited','cg':selected,'backgrounds':backgrounds,'space_models':spaces['spaces'],'prop_models':spaces['models'],'park_assembly':'art/space_v4/full_v2/park_exterior_r2.glb','interior_visual_overrides':'art/space_v4/full_v2/interior_art_r4/manifest.json','world_layout':'art/space_v4/full_v2/world_layout.json','geometry_qa_counts':{k:qa[k] for k in ['model_count','space_count','assembly_versions_checked','interior_visual_variants_checked']},'source_inspection_record':'art/v4_production/full/builtin_visual_review.json','import_contracts':['read camera and portal contracts, never flatten free-walk maps into a single background','stream interiors separately; exterior contains actual outdoor geometry and facades','do not load every duplicated embedded 5k texture simultaneously','honor glTF Y-up conversion and explicit source Blender coordinates','global exterior lighting is in exterior_lighting.json; room doors/locks/collision/interaction need runtime integration','CGs are fullbleed16:9; dialogue overlay visibility and hotspot positions must match each image in engine'],'world_map_art':'ui/v4/world_maps/manifest.json','runtime_integration':'NOT RUN'}
(F/'production_catalog.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Catalog:',len(selected),f'/{len(bases)} logical CG files,',len(backgrounds),'backgrounds,',len(spaces['spaces']),'space/state models; pending',pending)
