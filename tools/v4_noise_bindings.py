"""Publish explicitly authored interruptions without changing main testimony."""
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

@lru_cache(maxsize=1)
def _inputs():
    return (json.loads((ROOT/'data/presentation/v4_trial_noise.json').read_text(encoding='utf-8')),
            json.loads((ROOT/'data/v4_story/tasks.json').read_text(encoding='utf-8'))['tasks'])

def apply_noise(bundle):
    # Nonstop now has a single owner: trial_direction.noise plus host staging.
    # The old inline supplement bypassed its introduction gate and duplicated rows.
    if bundle['stage']['kind']=='nonstop':return bundle
    bank,tasks=_inputs()
    ident=bundle['taskId']
    if ident not in bank['tasks']:return bundle
    if not bundle.get('ready') or bundle['stage']['kind'] not in ('nonstop','panic'):
        raise ValueError('Noise needs an actual live debate: '+ident)
    task=tasks[ident];events={row['id']:row for row in task['lines']}
    protected={row['lineId'] for row in task.get('targets',[])}
    out=deepcopy(bundle);before=deepcopy(out['stage']['lines']);added=[]
    for row in bank['tasks'][ident]['noiseSources']:
        event=events.get(row['sourceEventId'])
        if not event or event['actor']!=row['actor'] or event['id'] in protected:
            raise ValueError('Noise participant/context changed: '+row['id'])
        if any(k in row for k in ('targets','weak','lieWeak','vpoint','agreeTarget','answer','answerEvidenceId')):
            raise ValueError('Noise must not add a judgment: '+row['id'])
        ref=row['sourceRef']
        if any(event['source'].get(k)!=ref[k] for k in ('file','line','fileSha256')):
            raise ValueError('Noise source reference changed: '+row['id'])
        if row['origin']!='own-authored-additional-manuscript' or not row['text'] or len(row['text'].encode('utf-16-le'))//2>26:
            raise ValueError('Noise authorship/text bounds: '+row['id'])
        reward=row['rewardSeconds']
        if type(reward) is not int or not 0<=reward<=60:raise ValueError('Noise reward bounds')
        role=row.get('noiseRole','ordinary')
        if role not in ('ordinary','loud') or role=='loud' and (bundle['stage']['kind']!='panic' or reward!=0):
            raise ValueError('Loud role requires a Panic row with zero reward')
        added.append({'id':row['id'],'actor':row['actor'],'speaker':row['speaker'],'text':row['text'],
                      'kind':'noise','source':deepcopy(ref),'sourceRefMeaning':'context-reference-not-verbatim-source',
                      'origin':row['origin'],'noiseGroup':row['id'],'contextSourceEventId':row['sourceEventId'],'noiseRewardSeconds':reward,'noiseRole':role,'motion':'wave'})
    if len({row['id'] for row in before+added})!=len(before)+len(added):raise ValueError('Duplicate noise row ID')
    out['stage']['lines']=before+added
    out['debate']['lines']=deepcopy(out['stage']['lines'])
    out['noiseLayer']={'origin':bank['origin'],'originalLineCount':len(before),'addedNoiseIds':[r['id'] for r in added],
                       'nativeExact':False,'preservesMainTestimony':True,'rewardPolicy':'own-authored-seconds-capped-at-initial-timer'}
    return out
