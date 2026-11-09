"""Pure publication-time detail adapter; original219 task files stay frozen."""
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]


@lru_cache(maxsize=4)
def _tasks(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))['tasks']


def apply_detail(bundle,task=None,root=None):
    """Return a copy with existing authored subtargets/options restored.

    Pass task for a fully in-memory transformation. If omitted, the caller's
    frozen data/v4_story/tasks.json is read once per workspace. Nothing is
    acquired, judged, retried or routed by this adapter.
    """
    out=deepcopy(bundle)
    if not out.get('ready'):return out
    ident=out['taskId']
    task=task if task is not None else _tasks(str((Path(root) if root else ROOT)/'data/v4_story/tasks.json'))[ident]
    if task['id']!=ident or task['source']!=out['source']:raise ValueError('Detail task/source does not match native bundle: '+ident)
    stage=out['stage'];changed=[]
    if task['kind'] in ('nonstop','panic','showdown'):
        source_lines={l['id']:l for l in task['lines']}
        for row in stage['lines']:
            source_id=row.get('sourceLineId',row['id'])
            if source_id not in source_lines:raise ValueError('Detail row is not an authored utterance: '+row['id'])
            # The native converter has already moved targets to their exact
            # split fragment. No target is repeated on the now-plain tail.
            agreement=next((x for x in row.get('targets',[]) if x['kind']=='agree'),None)
            if agreement:
                word=agreement['word'];cp=row['text'].index(word)
                row['agreeTarget']={'word':word,'start':len(row['text'][:cp].encode('utf-16-le'))//2,'glyphStart':cp,'answer':agreement['answer'],'source':deepcopy(row['source'])}
                changed.append('authored-agreement-substring')
            point=task.get('vpoint',{})
            if point.get('character'):
                candidates=[x for x in task.get('targets',[]) if x['lineId']==source_id and x['word'].startswith(point['character'])]
                local=next((x for x in candidates if x['word'] in row['text']),None)
                if local:
                    cp=row['text'].index(local['word']);character=point['character']
                    if len(character)!=1:raise ValueError('V-point must name one actual displayed glyph: '+ident)
                    row['vpoint']={'optional':True,'character':character,'glyphIndex':cp,'glyphIndexUtf16':len(row['text'][:cp].encode('utf-16-le'))//2,'coordinateSpace':'actual-glyph-projection','source':deepcopy(row['source']),'notSentenceCenter':True}
                    changed.append('authored-vpoint-character')
        if task.get('vpoint',{}).get('character') and not any(l.get('vpoint') for l in stage['lines']):raise ValueError('Authored V-point lost its actual target fragment: '+ident)
        if 'debate' in out:out['debate']['lines']=deepcopy(stage['lines'])
    if task['kind']=='anagram':
        for key in ('distractors','wrongText','retryPolicy'):
            if key in task:stage[key]=deepcopy(task[key]);changed.append('anagram-'+key)
        if task.get('wrongText'):
            stage['wrongTextPolicy']='Exact source candidate-word responses. Do not invent a meaning for every unrelated single glyph; use other for an unmatched attempt.'
    if task['kind']=='showdown':
        from v4_showdown_bindings import build_showdown
        stage['showdownV4']=build_showdown(task,stage)
        changed.append('authored-showdown-groups')
    if changed:out['detailBinding']={'sourceTaskId':ident,'source':deepcopy(task['source']),'restored':sorted(set(changed)),'changesAnswers':False,'changesReturn':False,'addsNoise':False}
    return out
