"""Hand-reviewed visible source regions; no option-index clue coordinates."""
import json,hashlib
from pathlib import Path


def bind_pictures(g,sources,tasks):
    root=Path(__file__).resolve().parents[1]
    path=root/'ui/v4/documents_v4_runtime/manifest.json'
    contract=json.loads(path.read_text(encoding='utf-8'))
    for proof in contract['comparison']['source']:
        s=sources[proof['file']]
        if s.hash!=proof['sha256'] or proof['quote'] not in s.lines[proof['line']-1]:
            raise ValueError('Source comparison picture stale: '+proof['file'])
    world=root/contract['accessPlan']['sourceWorld']
    if hashlib.sha256(world.read_bytes()).hexdigest()!=contract['accessPlan']['worldSha256']:
        raise ValueError('Source room plan changed; rebuild and re-inspect exact projection')
    mapping={'T1-SPOT-A01':'accessPlan','T1-MM-A03':'comparison'}
    for ident,key in mapping.items():
        task=tasks['tasks'][ident];picture=contract[key]
        task.update({k:picture[k] for k in ('image','coordinateSystem','answerRegionId','regions')})
        task['bindings']=[b for b in task['bindings'] if b['kind']!='forensicImageRegions']
        task['runtimeReady']=not task['bindings']
        task['pictureProvenance']={'contract':path.relative_to(root).as_posix(),'entry':key,'sourceBound':True,'newEvidence':False,'visualReview':'Directly viewed generated full document at 3200x2000; readable fields, unopened private appendix and existing-room target projection.'}
        if ident=='T1-MM-A03':
            task['wrongVariants']=[{'cause':'appendix','script':task['wrong']}]
            task['wrong']=[]
            task['wrongPolicy']='A region-specific reaction is used only for the actual selected appendix. Other misses retry without falsely calling them a private question.'
        for node in g.nodes.values():
            if node.get('taskId')==ident:node['runtimeReady']=task['runtimeReady']
    # The player examines the same aid during investigation first. The card
    # commits after this document returns, rather than revealing a trial image
    # for the first time or auto-granting its evidence on loading the picture.
    targets=[('v4:E1-09','comparison','작동 확인과 점검표 대조'),('v4:E1-02','accessPlan','직원 휴게실 출입구 확인')]
    for evidence_id,key,title in targets:
        hit=[n for n in g.nodes.values() if n.get('type')=='evidence' and n.get('evidenceId')==evidence_id and not n.get('revision')]
        if len(hit)!=1:raise ValueError('Exact investigation picture acquisition point missing: '+evidence_id)
        evidence=hit[0];docid=evidence['id']+':inspection-document'
        predecessors=[n for n in g.nodes.values() if n.get('next')==evidence['id']]
        if len(predecessors)!=1:raise ValueError('Ambiguous inspection picture predecessor '+evidence_id)
        predecessors[0]['next']=docid
        p=contract[key]
        g.add(docid,{'type':'document','title':title,'rows':[],'image':p['image'],'source':evidence['source'],'private':False,'next':evidence['id'],'inspectionOnly':True,'grantsEvidence':False})
