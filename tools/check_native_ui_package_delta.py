"""Prove UI-only package changes before inheriting completed native logic tests."""
import hashlib,json,uuid
from pathlib import Path
root=Path(__file__).resolve().parents[1];saved=root/'Game/Saved';read=lambda p:json.loads(p.read_text(encoding='utf8'))
new=read(root/'Game/build-result.json');old_id='2026-11-01T13-56-29-441Z-0fce033a';old=root/'Game/Builds/windows'/old_id;current=Path(new['output'])
if not old.exists():old=saved/'native-ui-baseline-0fce033a'
a=read(old/'game.hbpack.json');b=read(current/'game.hbpack.json');left={r['path']:r for r in a['files']};right={r['path']:r for r in b['files']}
added=sorted(right.keys()-left.keys());removed=sorted(left.keys()-right.keys());changed=sorted(k for k in left.keys()&right.keys() if left[k]['sha256']!=right[k]['sha256'])
assert not removed
assert set(added)=={'tools/native-ui-frame.mjs','licenses/native-ui-zstd-LICENSE.txt'},added
generated={'Content/Assets/Blueprints/BP_Yumeno.hbblueprint.json','Content/Assets/Scenes/Main.hbscene.json'}
runtime={'tools/native-widget-layer.mjs','prototype/ui-runtime.js',b['windowsApplication']['executable']}
assert set(changed)-generated==runtime,changed
def replace(value,mapping):
 if isinstance(value,str):return mapping.get(value,value)
 if isinstance(value,list):return [replace(x,mapping) for x in value]
 if isinstance(value,dict):return {k:replace(v,mapping) for k,v in value.items()}
 return value
normalised=[]
for name in sorted(generated):
 before=read(old/name);after=read(current/name);maps=[]
 for data in (before,after):
  ids=[]
  if name.endswith('.hbblueprint.json'):ids=[n['id'] for n in data['nodes']]
  else:ids=[c['id'] for o in data['objects'] for c in o.get('components',[]) if not c['id'].startswith('component_')]
  assert len(ids)==len(set(ids));[uuid.UUID(key.removeprefix('node_')) for key in ids];maps.append({key:'@generated-id-'+str(i) for i,key in enumerate(ids)})
 assert len(maps[0])==len(maps[1]);assert replace(before,maps[0])==replace(after,maps[1]),name
 normalised.append({'path':name,'privateIDs':len(maps[0]),'allOtherFieldsExact':True})
for p in sorted(left.keys()&right.keys()-set(changed)):
 assert hashlib.sha256((current/p).read_bytes()).hexdigest()==left[p]['sha256'],p
identity=read(saved/('source-identity-'+new['id'].rsplit('-',1)[1]+'.json'));assert identity['status']=='PASS' and identity['allSourceFilesExact']==56 and identity['allGeneratedDataJSONExact']==345
result={'ok':True,'build':new['id'],'baselineBuild':old_id,'newFiles':added,'changedFiles':changed,'removedFiles':removed,'exactPaths':len(left)-len(changed),'generatedPrivateIDChecks':normalised,'gameCppDataArtAudioAllUnchanged':True,'sourceIdentity':str((saved/('source-identity-'+new['id'].rsplit('-',1)[1]+'.json')).relative_to(root)),'functionalEvidenceMayBeInherited':True,'scope':'All authored C++ logic, data, text, assets, models, audio and native gameplay module bytes are identical. Only native UI transport/raster/state bookkeeping and its player/license changed. Prior219/779/five outcomes and2hour records retain their original build IDs. Current UI, input, resize and performance need focused actual regressions.'}
out=saved/('native-ui-package-delta-'+new['id'].rsplit('-',1)[1]+'.json');out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'ok':True,'build':new['id'],'changed':changed,'added':added}))
