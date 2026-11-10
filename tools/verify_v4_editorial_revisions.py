"""Check revised manuscript words without accepting a changed route or identity."""
import hashlib
import json
from pathlib import Path
from build_v4_story import Source, speaker_line
from v4_editorial_ids import validate_delivery

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'Game/Saved/editorial-before-20261101'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
rows = read(ROOT/'tools/v4_editorial_revisions.json')['revisions']
sources, original, allowed, allowed_delivery = {}, {}, {}, {}
for prefix in {r['prefix'] for r in rows}:
    file, = (ROOT/'docs/design/rewrite_v4').glob(prefix+'_*.md')
    sources[prefix] = Source(file)
    original[prefix] = Source(BASE/file.name)
current_hash = {s.name:s.hash for s in sources.values()}
original_hash = {s.name:s.hash for s in original.values()}
current_raw_hash = {s.name:hashlib.sha256(s.path.read_bytes()).hexdigest() for s in sources.values()}
original_raw_hash = {s.name:hashlib.sha256(s.path.read_bytes()).hexdigest() for s in original.values()}
ids = set()
for row in rows:
    source, before = sources[row['prefix']], original[row['prefix']]
    def find(s, raw):
        indices = [i+1 for i,line in enumerate(s.lines) if line.strip()==raw and s.ref(i+1)['location']==row['location']]
        assert len(indices)==1, (s.name,raw,indices)
        line = indices[0]
        return next(e for e in s.paragraphs(line,line) if e['type']=='say')
    old, new = find(before,row['before']), find(source,row['after'])
    assert old['id']==new['id'] and old['id'] not in ids
    ids.add(old['id'])
    validate_delivery(row)
    for key in ('actor','speaker','mono'):
        assert old[key]==new[key], (old['id'],key)
    if old['delivery'] != new['delivery']:
        assert row.get('authoredDelivery')
        allowed_delivery[old['id']] = (old['delivery'], new['delivery'])
    allowed[(source.name,row['location'],old['text'])] = new['text']

changed = []
compiled_revisions = set()
def compare(a,b,path='root'):
    if a==b:return
    if isinstance(a,dict) and isinstance(b,dict):
        assert a.keys()==b.keys(), (path,'different keys')
        for key in a:
            if key=='reviewedSourceHashes' and a[key]!=b[key]:
                assert a[key].keys()==b[key].keys(),path
                for file in a[key]:
                    if a[key][file]!=b[key][file]:
                        assert a[key][file]==original_hash[file] and b[key][file]==current_hash[file],(path,file)
            elif (key=='fileSha256' or (key=='sha256' and 'first' in a and 'last' in a)) and a[key]!=b[key]:
                file=a['file'];assert b['file']==file
                assert a[key] in (original_hash[file],original_raw_hash[file]) and b[key] in (current_hash[file],current_raw_hash[file]),path
            elif key in ('exactLine','ledgerPrefix') and a[key]!=b[key] and path.startswith('tasks/tasks/') and path.endswith('/return'):
                assert any(r['before'].startswith(a[key]) and r['after']==b[key] for r in rows),(path,key)
            elif key=='text' and a[key]!=b[key]:
                source=a.get('source',{})
                token=(source.get('file'),source.get('location'),a[key])
                assert allowed.get(token)==b[key], (path,'unreviewed text change')
                compiled_revisions.add(token)
                changed.append({'path':path,'id':a.get('id'),'file':token[0]})
            elif key=='delivery' and a[key]!=b[key]:
                assert allowed_delivery.get(a.get('id')) == (a[key], b[key]), (path,'unreviewed delivery')
            else:compare(a[key],b[key],path+'/'+key)
    elif isinstance(a,list) and isinstance(b,list):
        assert len(a)==len(b),path
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i))
    else:assert False,(path,a,b)

chapters=[]
for file in sorted(BASE.glob('[1-6].json')):
    before,after=read(file),read(ROOT/'data/v4_story/chapters'/file.name)
    assert before['nodes'].keys()==after['nodes'].keys()
    compare(before,after,'chapter/'+file.stem)
    chapters.append({'chapter':file.stem,'preservedNodeIds':len(before['nodes'])})
compare(read(BASE/'tasks.json'),read(ROOT/'data/v4_story/tasks.json'),'tasks')
fte_base=ROOT/'Game/Saved/editorial-fte-before-2026110116'
fte_checked=[]
if any(row['prefix'] in ('44','45') for row in rows):
    before_files={p.name:p for p in fte_base.glob('*.json')}
    after_files={p.name:p for p in (ROOT/'data/v4_story/freetime').glob('*.json')}
    assert before_files.keys()==after_files.keys()
    for name in sorted(before_files):
        before,after=read(before_files[name]),read(after_files[name])
        assert before.get('nodes',{}).keys()==after.get('nodes',{}).keys()
        compare(before,after,'freetime/'+name)
        fte_checked.append(name)
if (BASE/'v4_scenes.json').exists():
    from v4_editorial_scene_review import verify_and_normalize
    compare(read(BASE/'v4_scenes.json'),verify_and_normalize(read(ROOT/'data/presentation/v4_scenes.json')),'scenes')
if (BASE/'v4_trial_noise.json').exists():
    compare(read(BASE/'v4_trial_noise.json'),read(ROOT/'data/presentation/v4_trial_noise.json'),'noise')
assert compiled_revisions == set(allowed), ('uncompiled editorial revisions', set(allowed)-compiled_revisions)
checkpoint=ROOT/'Game/Saved/ui-checkpoints/normal-ch3-latest/savegames.json'
assert hashlib.sha256(checkpoint.read_bytes()).hexdigest()=='d43c126c6df61cb9f96b312cb65fdcf9992605368617f23c572fc5c6e9850fe7'
report={'ok':True,'reviewedSourceRevisions':len(rows),'existingEventIdsPreserved':len(ids),
        'explicitAuthoredDeliveryChanges':len(allowed_delivery),
        'freetimeFilesComparedWithSameNodesAndRouting':fte_checked,
        'chapters':chapters,'compiledTextOccurrences':len(changed),'sameRoutesChoicesTasksAnswersIdentityAndEvidence':True,
        'sameCgAndPublicRecordBoundaries':(BASE/'v4_scenes.json').exists(),
        'sceneAndTimeRepairSeparatelyChecked':'Game/Saved/editorial-scene-repair-proof-20261101.json',
        'sameNoiseWordsAndSourceEventIds':(BASE/'v4_trial_noise.json').exists(),
        'normalThreeCheckpointUnchanged':True,'runtimeOverlay':False,'nativePlayed':False,
        'scope':'Reviewed source words and explicitly declared delivery tags; stable IDs and all other graph semantics preserved. Not a literary-quality or duration certificate.'}
(ROOT/'Game/Saved/editorial-revision-proof-20261101.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
