"""Bind existing reconstruction candidates to current exact manuscript tables.

File presence and caption identity establish this data connection, not the
visual quality of the entire rendered game. No source or bitmap is modified.
"""
import json
from pathlib import Path


def bind_climax_candidates(graph,sources,tasks):
    chapter=int(graph['chapter'])
    if chapter not in (3,4,5):return
    ident=f'T{chapter}-MG-01'
    if ident not in tasks['tasks']:return
    task=tasks['tasks'][ident]
    if not any(b.get('kind')=='authoredComicPanels' for b in task.get('bindings',[])):return
    root=Path(__file__).resolve().parents[1]
    contract=json.loads((root/'art/v4_production/completion/comic_contracts.json').read_text(encoding='utf-8-sig'))
    records=[s for s in contract['slots'] if s['chapter']==chapter]
    if len(records)!=len(task['slots']):raise ValueError(ident+': actual candidate slot count differs')
    for record,slot in zip(records,task['slots']):
        source=sources[Path(record['source']).name];options=[]
        declared={x['id']:x['imageDescription'] for x in slot['candidates']}
        for option in record['options']:
            oid=str(record['slot'])+option['key']
            description=option['description']
            if (chapter,record['slot'],option['key'])==(5,2,'C'):
                if description!='아카리가 코토의 개인 잔을 골라 마지막 준비를 하고 직접 건네는 장면':raise ValueError('Unreviewed older C5/S2/C caption')
                description='아카리가 여섯 새 잔 중 코토에게 줄 하나를 골라 마지막 준비를 하고 직접 건네는 장면'
                # Directly viewed chapter05/page middle panel: Akari's hand
                # gives the chosen cup to Koto. No pre-labelled ownership is
                # pictured; the current caption correctly says she chose it.
            expected=f"|{oid}|{description}|"+('정답' if option['correct'] else '오답')+'|'
            if source.lines[option['source_line']-1]!=expected or declared.get(oid)!=description:
                raise ValueError(ident+': current candidate caption/key changed: '+oid)
            if (slot['answer']==oid)!=option['correct']:
                raise ValueError(ident+': manuscript and actual task answer disagree: '+oid)
            image=f"art/reconstruction_v4/candidates/C{chapter}_S{record['slot']:02}_{option['key']}.webp"
            if not (root/image).is_file():raise ValueError('Missing actual candidate '+image)
            response=slot['success'] if option['correct'] else slot['wrong'][oid]
            options.append({'id':oid,'label':description,'image':image,'source':source.ref(option['source_line']),'response':response})
        slot.update(options=options,priorCorrectSlotsRemain=True)
    task['bindings']=[b for b in task['bindings'] if b.get('kind')!='authoredComicPanels']
    task['runtimeReady']=not any(b.get('required') for b in task['bindings'])
    task['pictureProvenance']={'contract':'art/v4_production/completion/comic_contracts.json','policy':'All current table captions/keys, actual candidate image files and per-option responses checked. Original broad file hash is not claimed current. Reconstruction hypothesis images do not grant discovered evidence.','runtimeVisualAcceptance':False}
    for node in graph['nodes'].values():
        if node.get('taskId')==ident:node['runtimeReady']=task['runtimeReady']
