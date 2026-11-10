"""Source/UV/inspection-return checks. No native visual/run acceptance."""
import copy,hashlib,json,xml.etree.ElementTree as ET
from PIL import Image
from build_v4_story import ROOT,Source,Graph,compile_tasks
from v4_remaining_picture_bindings import bind_remaining_pictures,load_and_validate,MAPPING


def inside(poly,x,y):
    hit=False
    for i,a in enumerate(poly):
        b=poly[i-1]
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:hit=not hit
    return hit


def main():
    sources={p.name:Source(p) for p in (ROOT/'docs/design/rewrite_v4').glob('*.md')}
    m=load_and_validate(sources)
    assert len(m['entries'])==12 and len(MAPPING)==13
    centers=0
    for key,p in m['entries'].items():
        with Image.open(ROOT/p['image']) as im:
            assert list(im.size)==p['rasterSize']
            # Keep selected built-in illustration pixels at their actual native
            # resolution rather than fabricating detail by scaling them up.
            if p.get('authoredIllustration'):
                assert p.get('nativeResolutionPreserved') and im.width>=1500 and im.height>=900
            else:assert im.width>=3200 and im.height>=2000
        if p['svg']:
            svg=ET.parse(ROOT/p['svg']).getroot();assert svg.attrib['viewBox']=='0 0 1600 1000'
            assert len(list(svg))>8
        assert p['newEvidence'] is False
        assert all(0<=v<=1 for r in p['regions'] for point in r['polygon'] for v in point)
        correct=[r for r in p['regions'] if r['correct']];assert correct
        for r in correct:
            # Concave boundary masks must have a reachable interior, including
            # the center used by root's static native input fixture.
            u=sum(q[0] for q in r['polygon'])/len(r['polygon']);v=sum(q[1] for q in r['polygon'])/len(r['polygon'])
            assert inside(r['polygon'],u,v),(key,r['id'],'centroid outside real polygon')
            centers+=1
    from v4_story_case1 import compile_investigation
    from v4_story_case3 import compile_chapter_three
    from v4_story_case4 import compile_chapter_four
    from v4_story_case5 import compile_chapter_five
    count=docs=0;metadata=[]
    for chapter,compile in ((1,None),(3,compile_chapter_three),(4,compile_chapter_four),(5,compile_chapter_five)):
        tasks=compile_tasks(sources,json.loads((ROOT/'docs/design/rewrite_v4/qa_2026-10-29/trial_input_reedit.json').read_text(encoding='utf-8-sig')))
        if chapter==1:
            g=Graph('1');end=g.add('test:1:end',{'type':'end'})
            task=g.add('test:1:input',{'type':'task','taskId':'T1-MM-A02','runtimeReady':False,'next':end,'success':end})
            entry,catalogue=compile_investigation(g,sources,task);g=g.export(entry,evidenceCatalog=catalogue)
        else:g=compile(sources,{},tasks)
        original=copy.deepcopy(g);before_cards={n['id']:n['evidenceId'] for n in g['nodes'].values() if n.get('type')=='evidence'}
        result=bind_remaining_pictures(g,sources,tasks);snapshot=copy.deepcopy(g)
        assert bind_remaining_pictures(g,sources,tasks)==result
        assert snapshot==g,'Non-idempotent picture insertion'
        after_cards={n['id']:n['evidenceId'] for n in g['nodes'].values() if n.get('type')=='evidence'}
        assert before_cards==after_cards
        for key in result['inspectionDocuments']:
            p=m['entries'][key];docid='v4:inspection-diagram:'+key;n=g['nodes'][docid]
            assert n['type']=='document' and n['image']==p['image'] and n['grantsEvidence'] is False
            # Return through any other inspection aid sharing this scope and
            # finally reach the same original evidence node exactly once.
            dest=n['next'];seen={docid}
            while g['nodes'][dest]['type']=='document':
                assert dest not in seen;seen.add(dest);dest=g['nodes'][dest]['next']
            assert g['nodes'][dest]['evidenceId']==p['inspectionScope']
            preds=[v for v in g['nodes'].values() if v.get('next')==docid]
            assert len(preds)==1
        for tid in result['boundTaskIds']:
            t=tasks['tasks'][tid];assert t['runtimeReady'] is True
            assert not any(b.get('kind')=='forensicImageRegions' for b in t['bindings'])
            assert t['answerRegionId'] in {r['id'] for r in t['regions'] if r['correct']}
            assert not t['wrong'],'Unselected source-specific reaction leaked into generic miss'
            for region in t['regions']:
                if 'wrongVariant' in region:assert region['wrongVariant'] in {v['cause'] for v in t['wrongVariants']}
            for n in g['nodes'].values():
                if n.get('taskId')==tid:assert n['runtimeReady'] is True
            from v4_native_tasks import convert_task
            converted=convert_task(t,g.get('evidenceCatalog',{}));assert converted['ready'],tid
        for tid in result['unresolvedTaskIds']:assert tasks['tasks'][tid]['runtimeReady'] is False
        count+=len(result['boundTaskIds']);docs+=len(result['inspectionDocuments']);metadata.append(result)
    assert count==13 and docs==12
    print(json.dumps({'status':'PASS','sourceBoundTasks':count,'actualInspectedImages':len(m['entries']),'exactUvInteriorTargets':centers,'investigationDocumentsBeforeEvidence':docs,'newEvidenceGranted':False,'sameReturnAndIdempotence':True,'remainingExactPictureGate':[],'nativeExecuted':False,'centralOutputsWritten':False},ensure_ascii=False))


if __name__=='__main__':main()
