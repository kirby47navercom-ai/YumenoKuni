"""Prepare a reversible quarantine move and maintain asset references. Does not move/delete."""
from pathlib import Path
import json,os,re,hashlib
R=Path(__file__).resolve().parents[1];Q='_삭제대기_2026-10-29';O=R/Q;O.mkdir(exist_ok=True)
if (O/'move-receipt.json').is_file():
    raise SystemExit('Move already completed; preserve move-plan/receipt. Add new candidates explicitly instead of rebuilding the original plan.')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
audit=read(R/'docs/analysis/storage_cleanup_2026-10-29/files.json')
rows={x['path']:x for x in audit['rows']}
current=Path(read(R/'Game/build-result.json')['executable']).parent.resolve()
def add_tree(path,category):
    for p in path.rglob('*'):
        if p.is_file():rows[p.relative_to(R).as_posix()]={'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'category':category}
for platform in (R/'Game/Builds').iterdir():
    if platform.is_dir():
        for build in platform.iterdir():
            if build.is_dir() and build.resolve()!=current:add_tree(build,'D_previous_build')
# Canonical inputs stay available; retired source candidates can still be opened from quarantine.
chars=read(R/'art/character_delivery_v4/manifest.json')
protected=set()
for a in chars['actors']:
    for key in ['master_source','master_hd']:
        if a.get(key):protected.add(a[key].replace('\\','/'))
for a in chars['selected_poses']:
    for key in ['source','hd']:
        if a.get(key):protected.add(a[key].replace('\\','/'))
for a in read(R/'art/v4_production/completion/final_catalog.json')['story_cg']:
    for key in ['source','webp']:protected.add(a[key].replace('\\','/'))
protected|={str(Path(x).with_suffix('.webp')).replace('\\','/') for x in list(protected) if x.endswith('.png')}
plan=[];skipped=[]
for rel,row in rows.items():
    p=R/rel;category=row['category']
    bucket='제작참조확인필요' if category[0] in 'EGI' else '바로삭제가능'
    dest=f'{Q}/{bucket}/{rel}'
    if not p.exists() and not (R/dest).exists():continue
    if rel in protected and category!='A_pixel_identical_png':skipped.append(rel);continue
    if category=='A_pixel_identical_png' and not p.with_suffix('.webp').is_file():skipped.append(rel);continue
    if rel.startswith('Game/Builds/') and p.resolve().is_relative_to(current):continue
    plan.append({'source':rel,'destination':dest,'bytes':p.stat().st_size if p.exists() else (R/dest).stat().st_size,'category':category})
mapping={x['source']:x['destination'] for x in plan if not x['source'].startswith(('Game/Builds/','Game/Saved/','.git/'))}
pngs={x['source']:str(Path(x['source']).with_suffix('.webp')).replace('\\','/') for x in plan if x['category']=='A_pixel_identical_png'}
for p,w in pngs.items():mapping[p]=mapping.get(w,w)
canonical={}
for a in read(R/'art/space_v4/full_v2/interior_art_r4/manifest.json')['spaces']:
    for prefix in ['art/space_v4/full_v2/','art/space_v4/full_v2/interior_art_r3/']:canonical[prefix+Path(a['file']).name]=a['file']
canonical['art/space_v4/full_v2/park_exterior.glb']='art/space_v4/full_v2/park_exterior_r2.glb'
active={'art/v4_production/completion/final_catalog.json','art/v4_production/full/production_catalog.json','art/space_v4/full_v2/manifest.json','art/space_v4/full_v2/world_layout.json','art/space_v4/full_v2/hotel_layout.json','art/space_v4/hotel_layout.json'}
changed=[];hash_changes=[];sha_cache={}
def sha(p):
    p=str(p)
    if p not in sha_cache:sha_cache[p]=hashlib.sha256(Path(p).read_bytes()).hexdigest()
    return sha_cache[p]
def replace_value(s,file):
    normalized=s.replace('\\','/');absolute=normalized.startswith(R.as_posix()+'/')
    key=normalized[len(R.as_posix())+1:] if absolute else normalized
    table={**mapping,**canonical} if file.relative_to(R).as_posix() in active else mapping
    target=table.get(key)
    if target is None and not absolute:
        candidate=(file.parent/key).resolve()
        if candidate.is_relative_to(R):
            match=table.get(candidate.relative_to(R).as_posix())
            if match:target=os.path.relpath(R/match,file.parent).replace('\\','/')
    if target is None:return s
    value=(R/target).as_posix() if absolute else target
    return value.replace('/','\\') if '\\' in s else value
def walk(value,file):
    if isinstance(value,list):return [walk(x,file) for x in value]
    if not isinstance(value,dict):return replace_value(value,file) if isinstance(value,str) else value
    old=dict(value);out={k:walk(v,file) for k,v in value.items()}
    for field,src in old.items():
        if not isinstance(src,str) or out[field]==src:continue
        key=src.replace('\\','/');key=key[len(R.as_posix())+1:] if key.startswith(R.as_posix()+'/') else key
        if key not in pngs:continue
        oldfile=R/key;newfile=(R/pngs[key])
        if not newfile.exists():continue
        for h in [field+'_sha256',field.removesuffix('_file')+'_sha256','source_image_sha256' if field=='source_file' else '', 'sha256']:
            if h and h in out and isinstance(out[h],str) and re.fullmatch('[a-fA-F0-9]{64}',out[h]):
                if oldfile.exists() and out[h]==sha(oldfile):
                    out[h]=sha(newfile);hash_changes.append({'file':file.relative_to(R).as_posix(),'field':h,'old':old[h],'new':out[h]})
    return out
for base in ['art','ui','bg','tools']:
    for p in (R/base).rglob('*.json'):
        rel=p.relative_to(R).as_posix()
        if rel in rows or p.stat().st_size>10_000_000:continue
        try:before=read(p)
        except (OSError,ValueError):continue
        after=walk(before,p)
        if before!=after:p.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');changed.append(rel)
# Literal asset paths in maintained tools/galleries; history in docs and Saved stays intact.
pattern=re.compile('|'.join(re.escape(x) for x in sorted(mapping,key=len,reverse=True)))
for base in ['tools','art/v4_production']:
    for p in (R/base).rglob('*'):
        if p.suffix not in {'.py','.mjs','.js','.html'} or p.name==Path(__file__).name:continue
        try:s=p.read_text(encoding='utf-8-sig')
        except (ValueError,OSError):continue
        t=pattern.sub(lambda m:mapping[m[0]],s)
        if s!=t:p.write_text(t,encoding='utf-8');changed.append(p.relative_to(R).as_posix())
p=R/'tools/build_v4_space_assets.py';s=p.read_text(encoding='utf-8');s=s.replace("f'{identifier}.png'","f'{identifier}.webp'");p.write_text(s,encoding='utf-8')
# Move whole old build/cache directories instead of tens of thousands of child operations.
units={}
for x in plan:
    rel=x['source'];cat=x['category'];unit=rel
    if cat=='D_previous_build':unit='/'.join(rel.split('/')[:4])
    elif cat=='C_test_browser_cache':unit=rel.split('/WebView2/')[0]+'/WebView2'
    if unit not in units:
        destination=f'{Q}/'+('제작참조확인필요' if cat[0] in 'EGI' else '바로삭제가능')+'/'+unit
        units[unit]={'source':unit,'destination':destination,'category':cat,'directory':unit!=rel,'bytes':0}
    units[unit]['bytes']+=x['bytes']
record={'authorization':'User explicitly requested moving cleanup candidates into a folder under this workspace; no deletion','current_build_preserved':current.relative_to(R).as_posix(),'files':plan,'units':list(units.values()),'changed_reference_files':sorted(set(changed)),'image_hash_migrations':hash_changes,'protected_current_sources':skipped,'planned_bytes':sum(x['bytes'] for x in plan),'deleted_bytes':0}
(O/'move-plan.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
ignore=R/'.gitignore';s=ignore.read_text(encoding='utf-8');line='/'+Q+'/'
if line not in s:ignore.write_text(s+'\n# User requested reversible cleanup quarantine\n'+line+'\n',encoding='utf-8')
print(json.dumps({'files':len(plan),'units':len(units),'bytes':record['planned_bytes'],'reference_files_changed':len(set(changed)),'protected':len(skipped)}))
