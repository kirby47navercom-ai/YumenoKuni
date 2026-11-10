"""All219 publication-time transformations; no original/native game run."""
from copy import deepcopy
from collections import Counter
import json
from build_v4_story import OUT,load
from v4_task_detail_bindings import apply_detail


def main():
    tasks=load(OUT/'tasks.json')['tasks'];native=load(OUT/'native_tasks.json')['tasks'];checks=points=agree=groups=0
    for ident,bundle in native.items():
        before=deepcopy(bundle);task=deepcopy(tasks[ident]);out=apply_detail(bundle,task)
        assert bundle==before and task==tasks[ident]
        assert apply_detail(out,task)==out,'Publication transform must be idempotent'
        for key in ('taskId','ready','queues','requiresEvidence','scopeOnlyEvidence','outcomes','transformation','source'):
            assert out.get(key)==bundle.get(key),(ident,key)
        for key in ('id','kind','answer','script','candidates','options'):
            assert out['stage'].get(key)==bundle['stage'].get(key),(ident,key)
        old_lines=[l for l in bundle['stage'].get('lines',[]) if isinstance(l,dict)]
        rows=[l for l in out['stage'].get('lines',[]) if isinstance(l,dict)]
        assert len(rows)==len(old_lines)
        for row,old in zip(rows,old_lines):
            for key,value in old.items():assert row[key]==value,(ident,row['id'],key)
            if row.get('vpoint'):
                point=row['vpoint'];cp=point['glyphIndex'];assert row['text'][cp]==point['character']==task['vpoint']['character']
                assert point['glyphIndexUtf16']==len(row['text'][:cp].encode('utf-16-le'))//2;points+=1
            if row.get('agreeTarget'):
                target=row['agreeTarget'];assert row['text'][target['glyphStart']:].startswith(target['word'])
                assert target['word'] in [t['word'] for t in task['targets'] if t['verdict']=='agree'];agree+=1
            assert row.get('kind')!='noise'
        if 'debate' in out:assert out['debate']['lines']==out['stage']['lines']
        if task['kind']=='showdown':
            detail=out['stage']['showdownV4'];groups+=len(detail['groups']);assert detail['answerEvidenceId']==task['answerEvidenceId']
            target=task['targets'][0];actual=detail['statements'][detail['weakRuntimeLineId']]
            assert actual.get('sourceLineId',actual['id'])==target['lineId'] and actual['bladeTarget']['word']==target['word']
            assert actual['actor']==target['actor']
            assert len([l for l in detail['statements'].values() if l['role']=='blade'])==1
            expected={l['id'] for l in task['lines']};seen=[]
            for group in detail['groups']:
                for entry in group['entries']:
                    if entry['type']=='statement':
                        line=detail['statements'][entry['lineId']];assert line['actor']==detail['opponent']
                        seen.append(line.get('sourceLineId',line['id']))
                    else:seen.extend(e['eventId'] for e in entry['events'] if e['type']=='say')
                seen.extend(e['eventId'] for e in group['afterAdvance'] if e['type']=='say')
            assert set(seen)==expected,(ident,set(seen)-expected,expected-set(seen))
            cut_counts=Counter(l.get('sourceLineId',l['id']) for l in detail['statements'].values())
            assert Counter(seen)==Counter({key:cut_counts.get(key,1) for key in expected}),ident
            if ident in ('T1-RS-A02','T2-RS-A02','T2-RS-A03'):
                assert actual['id']!=rows[-1]['id'] and detail['statements'][rows[-1]['id']]['role']=='ordinary'
            if ident in ('T2-RS-01','T5-RS-01'):
                assert any(e.get('actor')=='mio' for g in detail['groups'] for e in g['afterAdvance'])
        checks+=16+len(rows)
    fa=apply_detail(native['T3-FA-01'],tasks['T3-FA-01'])['stage']
    assert fa['distractors']==['귀','환','소','생'] and fa['wrongText']==tasks['T3-FA-01']['wrongText']
    assert points==63 and agree==6 and groups==37
    print(json.dumps({'passed':True,'tasks':len(tasks),'checks':checks+3,'sourceVpoints':points,'narrowAgreeTargets':agree,'showdownGroups':groups,'newNoise':0,'sourceMutation':False,'runtimeExecuted':False}))


if __name__=='__main__':main()
