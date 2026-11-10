from copy import deepcopy
import hashlib,json
from pathlib import Path
import v4_noise_bindings as noise
from v4_task_detail_bindings import apply_detail

root=Path(__file__).resolve().parents[1]
native=json.loads((root/'data/v4_story/native_tasks.json').read_text(encoding='utf-8'))['tasks']
bank,tasks=noise._inputs();count=rows=loud=0;texts=set();hashes={}
for ident,bundle in native.items():
    before=apply_detail(bundle);out=noise.apply_noise(before)
    if before['stage']['kind']=='nonstop':assert out==before and 'noiseLayer' not in out
    if 'noiseLayer' not in out:assert out==before;continue
    count+=1;n=out['noiseLayer']['originalLineCount'];added=out['stage']['lines'][n:];rows+=len(added)
    assert out['stage']['lines'][:n]==before['stage']['lines'] and out['debate']['lines']==out['stage']['lines']
    for key in ['answer','options','kind']:assert out['stage'].get(key)==before['stage'].get(key)
    for key in ['return','queues','transformation']:assert out.get(key)==before.get(key)
    events={e['id']:e for e in tasks[ident]['lines']}
    for row in bank['tasks'][ident]['noiseSources']:
        ref=row['sourceRef'];file=ref['file']
        if file not in hashes:hashes[file]=hashlib.sha256((root/'docs/design/rewrite_v4'/file).read_text(encoding='utf-8').encode('utf-8')).hexdigest()
        assert hashes[file]==ref['fileSha256']
        assert row['text']!=events[row['sourceEventId']]['text'] and row['text'] not in texts;texts.add(row['text'])
    assert all(r['noiseGroup']==r['id'] and r['contextSourceEventId'] in events for r in added)
    for r in added:
        if r['noiseRole']=='loud':assert out['stage']['kind']=='panic' and r['noiseRewardSeconds']==0;loud+=1
        else:assert r['noiseRole']=='ordinary' and r['noiseRewardSeconds']==2
    assert not any(r['id'] in ids for lane in out['debate'].get('lanes',[]) for ids in [lane['lines']] for r in added)
expected=[v for k,v in bank['tasks'].items() if native[k]['stage']['kind']=='panic']
assert count==len(expected) and rows==sum(len(v['noiseSources']) for v in expected) and len(texts)==rows
assert loud==6

ident=next(k for k,v in bank['tasks'].items() if native[k]['stage']['kind']=='panic' and v['noiseSources'][0].get('noiseRole','ordinary')=='ordinary');original=noise._inputs
for key,value in [('weak',{}),('actor','not-a-participant'),('text','x'*27),('rewardSeconds',-1),('noiseRole','loud'),('noiseRole','unrecognized')]:
    changed=deepcopy(bank);changed['tasks'][ident]['noiseSources'][0][key]=value
    noise._inputs=lambda:(changed,tasks)
    try:noise.apply_noise(apply_detail(native[ident]))
    except ValueError:pass
    else:raise AssertionError('Invalid noise metadata admitted: '+key)
noise._inputs=original
print(json.dumps({'status':'PASS','noiseTasks':count,'noiseRows':rows,'loudZeroReward':loud,'ordinaryTwoSeconds':rows-loud,'uniqueText':len(texts),'mainTargetsLanesAnswersRoutesPreserved':True,'LFSourceHashesExact':True,'noPermanentReferenceSuppression':True,'invalidMetadataRejected':6,'playerLaunch':False},ensure_ascii=False))
