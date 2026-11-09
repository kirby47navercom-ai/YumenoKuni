"""Bind new exact source inspection diagrams and their real visible UV regions.

Source facts/regions are fixed in the diagram manifest; no clue is granted by
loading an image. The central compiler owns generated story data writes.
"""
import copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'ui/v4/investigation_diagrams_v4/manifest.json'
MAPPING={
 'T1-MM-A02':'c1_floor_ice',
 'T3-SPOT-A01':'c3_observation_plan','T3-MM-01':'c3_observation_plan',
 'T3-MM-A02':'c3_waiting_position','T3-MM-A03':'c3_knife_custody',
 'T4-SPOT-A01':'c4_hatch_hand_observation','T4-MM-A02':'c4_external_fastening','T4-MM-A03':'c4_closed_hatch_photo','T4-MM-01':'c4_storage_boundary',
 'T5-SPOT-A01':'c5_inventory_fragment','T5-MM-A02':'c5_packaging_warning','T5-MM-A03':'c5_cap_strip','T5-MM-01':'c5_two_joining_boundaries',
}
# Only exact selected-region responses play. A miss elsewhere never fabricates
# that the player selected e.g. the appendix, a neck or another cell.
WRONG_MAP={
 'T1-MM-A02':{},
 'T3-SPOT-A01':{'work-inside':'original'},
 'T3-MM-01':{},
 'T3-MM-A02':{'right-empty':'original'},
 'T3-MM-A03':{},
 'T4-SPOT-A01':{'front-door':'original'},
 'T4-MM-A02':{'water':'original'},
 'T4-MM-A03':{},
 'T4-MM-01':{'hatch':'wrong-region:C'},
 'T5-SPOT-A01':{'cell-A':'original','cell-B':'original','cell-C':'original','cell-E':'original','cell-F':'original'},
 'T5-MM-A02':{'fold':'original'},
 'T5-MM-A03':{'bottle-bottom':'original'},
 'T5-MM-01':{},
}


def load_and_validate(sources):
    m=json.loads(MANIFEST.read_text(encoding='utf-8'))
    if hashlib.sha256((ROOT/m['worldSource']).read_bytes()).hexdigest()!=m['worldSha256']:
        raise ValueError('Diagram world anchors changed; re-inspect exact room nodes')
    for name,expected in m['sourceHashes'].items():
        if sources[name].hash!=expected:raise ValueError('Diagram source changed: '+name)
    for picture in m['entries'].values():
        if hashlib.sha256((ROOT/picture['image']).read_bytes()).hexdigest()!=picture['sha256']:raise ValueError('Diagram pixels changed: '+picture['image'])
        if picture['visualReview'].startswith('pending'):raise ValueError('Actual diagram still awaits visual review')
        for p in picture['source']:
            s=sources[p['file']]
            if s.hash!=p['fileSha256'] or s.lines[p['line']-1]!=p['quote']:raise ValueError('Diagram source reference stale')
    return m


def bind_remaining_pictures(graph,sources,tasks):
    m=load_and_validate(sources)
    nodes=graph.nodes if hasattr(graph,'nodes') else graph['nodes']
    chapter=str(graph.chapter) if hasattr(graph,'chapter') else str(graph['chapter'])
    relevant={tid:key for tid,key in MAPPING.items() if tid.startswith('T'+chapter+'-')}
    attached=set()
    for tid,key in relevant.items():
        task=tasks['tasks'][tid];picture=m['entries'][key]
        task.update(image=picture['image'],coordinateSystem=picture['coordinateSystem'],regions=copy.deepcopy(picture['regions']))
        # The back wall is a real visible feature of the H box, not the whole room.
        if tid=='T3-MM-01':
            task['regions'].append({'id':'H-back-wall','label':'작업 홈 뒤 벽','polygon':[[.53125,.83],[.75,.83],[.75,.86],[.53125,.86]],'correct':False,'wrongVariant':'wrong-region:B'})
        task['answerRegionId']=next(r['id'] for r in task['regions'] if r['correct'])
        task.setdefault('originalPictureWrong',copy.deepcopy(task.get('wrong',[])))
        task.setdefault('originalPictureWrongVariants',copy.deepcopy(task.get('wrongVariants',[])))
        variants=copy.deepcopy(task['originalPictureWrongVariants'])
        if task['originalPictureWrong']:
            variants.append({'cause':'original','script':copy.deepcopy(task['originalPictureWrong'])})
        for region in task['regions']:
            cause=WRONG_MAP[tid].get(region['id'])
            if cause:region['wrongVariant']=cause
        task['wrong']=[];task['wrongVariants']=variants
        task['wrongPolicy']='Only a source-exact selected-region response is queued. Other misses retry with ordinary UI failure feedback, no invented character speech.'
        task['bindings']=[b for b in task['bindings'] if b.get('kind')!='forensicImageRegions']
        task['runtimeReady']=not any(b.get('required') for b in task['bindings'])
        task['pictureProvenance']={'contract':MANIFEST.relative_to(ROOT).as_posix(),'entry':key,'sourceBound':True,'imageSha256':picture['sha256'],'newEvidence':False,'worldMetricAcceptance':False,'runtimeVisualAcceptance':False,'limitations':picture['limitations']}
        if tid=='T5-MM-01':task['selectionPolicy']='Both already-confirmed pair comparisons are visible together; only an actual torn boundary is selectable as correct. No two-simultaneous-input rule is invented.'
        for node in nodes.values():
            if node.get('taskId')==tid:node['runtimeReady']=task['runtimeReady']
        attached.add(key)
    for key in sorted(attached):
        picture=m['entries'][key];cid=picture['inspectionScope'];docid='v4:inspection-diagram:'+key
        if docid in nodes:continue
        hits=[n for n in nodes.values() if n.get('type')=='evidence' and n.get('evidenceId')==cid and not n.get('revision')]
        if len(hits)!=1:raise ValueError('Diagram needs one exact authored acquisition scope: '+cid)
        evidence=hits[0];pred=[n for n in nodes.values() if n.get('next')==evidence['id']]
        if len(pred)!=1:raise ValueError('Ambiguous exact diagram predecessor: '+cid)
        pred[0]['next']=docid
        nodes[docid]={'id':docid,'type':'document','title':picture['title'],'rows':[],'image':picture['image'],'source':evidence['source'],'private':False,'next':evidence['id'],'inspectionOnly':True,'grantsEvidence':False,'authoredReference':copy.deepcopy(picture['source'])}
    return {'boundTaskIds':sorted(relevant),'inspectionDocuments':sorted(attached),'unresolvedTaskIds':[k for k in m['unresolved'] if k.startswith('T'+chapter+'-')]}
