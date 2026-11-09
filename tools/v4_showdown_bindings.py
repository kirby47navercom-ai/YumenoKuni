"""Reviewed source groups/interludes; no stage-array-last-row weak inference."""
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

# Actual start/end and explicit progression/interlude boundaries, one-based.
# Normal tuning below is our game tuning, not a claim that these numbers came
# from a V3 DAT which never contained the fan-game's authored statements.
PLANS={
 'T1-RS-A02':[(638,640,642,642),(644,646,None,None)],
 'T1-RS-A03':[(677,679,681,681),(683,683,None,None)],
 'T2-RS-A02':[(679,681,683,683),(685,687,None,None)],
 'T2-RS-A03':[(718,720,722,722),(724,726,None,None)],
 'T3-RS-A02':[(679,681,683,683),(685,685,None,None)],
 'T3-RS-A03':[(716,718,720,720),(722,722,None,None)],
 'T4-RS-A02':[(650,652,654,654),(656,656,None,None)],
 'T4-RS-A03':[(687,689,691,691),(693,693,None,None)],
 'T5-RS-A02':[(679,681,683,683),(685,685,None,None)],
 'T5-RS-A03':[(716,720,722,722),(724,724,None,None)],
 'T6-RS-A02':[(611,613,615,615),(617,617,None,None)],
 'T6-RS-A03':[(648,650,652,652),(654,654,None,None)],
 'T1-RS-01':[(316,326,328,328),(330,330,None,None)],
 'T2-RS-01':[(12,22,24,44),(46,46,None,None)],
 'T3-RS-01':[(154,164,166,166),(168,168,None,None)],
 'T4-RS-01':[(186,194,196,196),(198,198,None,None)],
 'T5-RS-01':[(199,209,211,217),(221,231,233,239),(243,243,None,None)],
 'T6-RS-01':[(140,150,152,152),(154,154,None,None)],
}


def build_showdown(task,stage,root=None):
    from build_v4_story import Source
    from v4_native_tasks import scripts
    if task['id'] not in PLANS or task['kind']!='showdown':raise ValueError('Showdown source plan not reviewed: '+task['id'])
    source=Source((Path(root) if root else ROOT)/'docs/design/rewrite_v4'/task['source']['file'])
    if source.hash!=task['source']['fileSha256']:raise ValueError('Showdown source changed; re-read group/interlude boundaries: '+source.name)
    if len(task['targets'])!=1 or task['targets'][0]['verdict']!='refute':raise ValueError('Only the actual authored single blade verdict is reviewed: '+task['id'])
    target=task['targets'][0];opponent=target['actor'];original={l['id']:l for l in task['lines']}
    fragments={key:[] for key in original}
    for row in stage['lines']:fragments[row.get('sourceLineId',row['id'])].append(row)
    def events(a,b):
        raw=[deepcopy(original.get(e['id'],e)) for e in source.paragraphs(a,b) if e['type'] in ('say','stage')]
        return scripts(raw)
    groups=[];statements={};covered=[]
    for number,(a,b,after_a,after_b) in enumerate(PLANS[task['id']]):
        chosen=[l for l in task['lines'] if a<=l['source']['line']<=b]
        entries=[];normal_count=0
        for line in chosen:
            covered.append(line['id'])
            if line['actor']!=opponent:
                entries.append({'type':'dialogue','sourceLineId':line['id'],'events':scripts([line])})
                continue
            ids=[]
            for row in fragments[line['id']]:
                current=deepcopy(row);weak=next((x['weak'] for x in row.get('targets',[]) if x.get('outcome')=='A'),None)
                is_blade=bool(weak) and line['id']==target['lineId']
                current.update(role='blade' if is_blade else 'ordinary',requiredHits=1 if is_blade else 2,gaugeGain=5,gaugeLoss=-5,durationFrames=360 if is_blade else 216)
                if is_blade:
                    if weak['word']!=target['word'] or weak['answer']!=task['answerEvidenceId']:raise ValueError('Actual showdown blade was rebound: '+task['id'])
                    current['bladeTarget']=deepcopy(weak)
                statements[row['id']]=current;ids.append(row['id'])
                if not is_blade:normal_count+=1
            entries.extend({'type':'statement','lineId':ident} for ident in ids)
        after=events(after_a,after_b) if after_a is not None else []
        for line in task['lines']:
            if after_a is not None and after_a<=line['source']['line']<=after_b:covered.append(line['id'])
        final=any(statements[e['lineId']]['role']=='blade' for e in entries if e['type']=='statement')
        groups.append({'id':task['id']+':group:'+str(number+1),'entries':entries,'afterAdvance':after,
                       'advanceThreshold':255 if final else min(100,50+normal_count*5),'initialGauge':50,
                       'gaugeSettleFrames':15,'endDwellFrames':10,'tugRequired':8,'tugLimitFrames':180,
                       'finalBladeGroup':final,'sourceRange':{'file':source.name,'firstLine':a,'lastLine':b,'fileSha256':source.hash},
                       'onGaugeRepeat':{'replay':'same-group','authoredReaction':None},'onWrongBlade':{'queue':'existing-wrong','resume':'same-group-start'}})
    if sorted(covered)!=sorted(original):raise ValueError('Showdown grouping lost or duplicated actual dialogue: '+task['id'])
    blade_rows=[l for l in statements.values() if l['role']=='blade']
    if len(blade_rows)!=1:raise ValueError('Showdown must retain its actual single weak row: '+task['id'])
    order=list(statements)
    for group in groups:
        for item in group['entries']:
            if item['type']=='statement':item['statementIndex']=order.index(item['lineId'])
    return {'schemaVersion':1,'taskId':task['id'],'opponent':opponent,'statements':statements,'statementOrder':order,'groups':groups,
            'answerEvidenceId':task['answerEvidenceId'],'weakSourceLineId':target['lineId'],'weakRuntimeLineId':blade_rows[0]['id'],
            'timeFrames':10800,'wrongBladeDamage':2000,'groupFailureDamage':1000,'normalSlashDoesNotJudgeTruth':True,
            'wrongResponsePolicy':'Use existing queues.wrong or an explicitly matched existing wrongVariant only for an actual wrong blade. A missed/gauge repeat is not an asserted false theory; do not dispatch unrelated source reactions.',
            'hitGeometry':'finite-segment-versus-visible-glyph-circles-inclusive-boundary','weakGlyphsProtectedFromPartialErasure':True,
            'tuningProvenance':'Own V4 play tuning: ordinary requiredHits2,durations216/360, initialGauge50, threshold50+ordinaryCount*5. REA supplies mechanism/ranges, not these source-specific values.',
            'angleContract':{'input':'normalized-axis-deadzone0.125 or mouse-vector-radius75','rangeProvider':'host-supplied-gauge-range','nativeRangeTableRestored':False},
            'source':deepcopy(task['source']),'reaReferences':['docs/spec/18_V3_분석/05_미니게임.md:533-578'],
            'runtimeVerified':False,'changesGraphReturn':False,'changesOriginalLines':False}
