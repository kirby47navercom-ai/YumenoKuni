"""Pure conversion regression; no original game or runtime is executed."""
from copy import deepcopy
import json
import build_v4_story as v4
from v4_native_tasks import convert_tasks,convert_task


def verify():
    tasks=v4.load(v4.OUT/'tasks.json');original=deepcopy(tasks)
    catalogue={}
    for p in (v4.OUT/'chapters').glob('*.json'):catalogue.update(v4.load(p).get('evidenceCatalog',{}))
    native=convert_tasks(tasks,catalogue);checks=0
    def check(condition):
        nonlocal checks
        if not condition:raise AssertionError('native task conversion check '+str(checks))
        checks+=1
    check(tasks==original)
    for ident,task in tasks['tasks'].items():
        out=native['tasks'][ident]
        if not task['runtimeReady']:
            check(not out['ready'] and 'stage' not in out)
            continue
        check(out['ready'] and out['stage']['script']==[])
        check(all(e.get('text') if e['type']=='say' else 'text' not in e for e in out['queues']['intro']))
        check(len(out['queues']['success'])==len([e for e in task['success'] if e['type'] in ('say','stage')]))
        if 'debate' in out:
            grouped={event['id']:[] for event in task['lines']}
            for line in out['debate']['lines']:grouped[line.get('sourceLineId',line['id'])].append(line)
            check(all(''.join(row['text'] for row in grouped[event['id']])==event['text'].replace('【','').replace('】','').replace('〔','').replace('〕','') for event in task['lines']))
            for line in out['debate']['lines']:
                check('【' not in line['text'] and '〔' not in line['text'])
                check(len(line['text'].encode('utf-16-le'))//2<=48)
                if line.get('weak'):
                    w=line['weak'];check(line['text'][w['start']:w['start']+len(w['word'])]==w['word'])
        if task['kind']=='choice':check(out['stage']['optionIds'][out['stage']['answer']]==task['answer'])
        if task['kind']=='person':check(out['stage']['candidates']==task['candidates'] and task['answer'] in out['stage']['candidates'])
        if task['kind']=='reasoning':check(all(q['answer'] in q['options'] for q in out['stage']['questions']))
        if task['kind']=='anagram':check(out['stage']['mechanic']['selectGlyphCount']==1)
    lie=native['tasks']['T1-LIE-01']
    check(set(lie['outcomes'])=={'A','B'} and lie['outcomes']['A']['to']!=lie['outcomes']['B']['to'])
    check(lie['transformation']['changesHistoricalFacts'] is False and lie['queues']['success']==[])
    check(native['tasks']['T1-PD-01']['scopeOnlyEvidence'] and native['tasks']['T1-PD-01']['requiresEvidence']==[])
    check(native['tasks']['T1-MM-01']['stage']['answerRegionId']=='reinforcing-plate')
    check(native['tasks']['T1-MM-01']['stage']['mechanic']['gravity'] is False and native['tasks']['T1-MM-01']['stage']['mechanic']['adjacency']==4 and native['tasks']['T1-MM-01']['stage']['mechanic']['recolorBoundaryOnce'])
    check(native['tasks']['T1-SPOT-A01']['stage']['answerRegionId']=='door_A')
    check(native['tasks']['T1-MM-A03']['queues']['wrong']==[] and native['tasks']['T1-MM-A03']['queues']['wrongVariants'][0]['cause']=='appendix')
    check(native['tasks']['T1-MM-A02']['ready'] and native['tasks']['T1-MM-A02']['stage']['image']=='art/inspection_v4/delivery/floor_ice_builtin_r1.webp')
    for ident in ('T3-PERSON-A01','T3-PERSON-A02'):
        check(native['tasks'][ident]['stage']['candidateOverrides']['ken']['label']=='켄의 몸')
        check('조종자 미확인' in native['tasks'][ident]['stage']['candidateOverrides']['ken']['caption'])
    for ident in ('T3-CULPRIT-A01','T3-VOTE-01'):
        stage=native['tasks'][ident]['stage']
        check(stage['answer']=='sora' and stage['candidateOverrides']['sora']['label']=='소라(현재 켄의 몸)')
        check(stage['candidateOverrides']['ken']['label']=='켄(몸의 원래 주인)')
    broken=deepcopy(tasks['tasks']['T1-NS-T05e']);broken['targets'][0]['word']='UNAUTHORED TARGET'
    try:convert_task(broken,catalogue)
    except ValueError:check(True)
    else:check(False)
    result={'passed':True,'checks':checks,'ready':sum(t['ready'] for t in native['tasks'].values()),'total':len(native['tasks']),'runtimeTested':False,'sourceMutation':False}
    v4.dump(v4.OUT/'native_verification.json',result)
    return result


if __name__=='__main__':print(json.dumps(verify()))
