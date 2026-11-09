"""Case-one later trial: explicit inputs, exclusive lie route and exact returns."""
import re
from pathlib import Path
import json


def compile_second_half(g, sources, tasks, next_id):
    d = {s.prefix: s for s in sources.values()}
    tm = tasks["tasks"]

    def says(p, a, b):
        return [e for e in d[p].paragraphs(a, b) if e["type"] == "say"]

    def seq(p, a, b, to):
        return g.sequence(d[p], a, b if b is not None else len(d[p].lines), to)

    def task(ident, kind, p, line, **fields):
        tm[ident] = {"id": ident, "kind": kind, "chapter": "1", "sourceKind": "BASELINE", "source": d[p].ref(line), "intro": [], "lines": [], "wrong": [], "success": [], "bindings": [], "return": {"graphNext": True}, "runtimeReady": True, "retry": {"sameTask": True, "preserveEvidence": True, "preservePublicFacts": True, "cancellationIsSuccess": False}, **fields}
        return tm[ident]

    def input_node(ident, to, **fields):
        return g.add("v4:input:" + ident, {"type": "task", "taskId": ident, "source": tm[ident]["source"], "runtimeReady": tm[ident]["runtimeReady"], "next": to, "success": to, **fields})

    def recall(ident, flag, choices, to):
        missing = g.add(ident + ":missing", {"type": "gate", "reason": "Required earlier choice missing; never replay all remembered branches."})
        return g.add(ident, {"type": "branch", "cases": [{"flag": flag, "equals": v, "to": seq(p, a, b, to)} for v, p, a, b in choices], "default": missing})

    task("T1-FA-01", "anagram", "163", 151, intro=says("163",157,157), answer="인쇄된본문", answerGlyphs=list("인쇄된본문"), distractorDescription="빈/종/이/시/각/표", mechanic={"selectGlyphCount":1,"arrivalJudgment":True,"poolSlots":20,"specialCollectibleSeparate":True}, wrongVariants=[{"cause":"빈종이","script":says("163",161,161)},{"cause":"시각표","script":says("163",167,167)},{"cause":"wrong-order","script":says("163",173,173)}],success=says("163",179,183),retryPolicy="wrongSlotOnly")
    lie = task("T1-LIE-01", "nonstop", "163",188,lines=says("163",194,200),answerEvidenceId="v4:E1-06",requiresEvidence=["v4:E1-06"],evidencePool="actually-acquired-v4-cards-only",judgment="refute-or-intentional-lie",wrongVariants=[{"cause":"wrong-card:pain","script":says("163",206,206)},{"cause":"wrong-card:number-only","script":says("163",212,212)}])
    lie["targets"]=[{"lineId":lie["lines"][-1]["id"],"word":"발견 뒤에 현장 조각을 넣었을 수도 있잖아.","verdict":"refute","actor":"yuu"}]
    lie["transformation"]={"sourceEvidenceId":"v4:E1-06","normalLabel":"발견 전 회수","lieLabel":"발견 뒤 회수","intentionalHold":True,"changesHistoricalFacts":False}
    rs=task("T1-RS-01","showdown","163",310,lines=says("163",316,330),answerEvidenceId="v4:E1-06",requiresEvidence=["v4:E1-06"],evidencePool="actually-acquired-v4-cards-only",success=says("163",360,364),wrongVariants=[{"cause":"pain","script":says("163",336,338)},{"cause":"last-reunion","script":says("163",344,346)},{"cause":"names-only","script":says("163",352,354)}])
    rs["targets"]=[{"lineId":rs["lines"][-1]["id"],"word":"아예 볼 필요 없어","verdict":"refute","actor":"taiga"}]
    questions=[]
    for a,b,answer,correct,wrong in ((374,395,"A",394,[("B",384),("C",388)]),(396,419,"B",416,[("A",406),("C",410)])):
        opts=[]
        for line in d["163"].lines[a-1:b]:
            m=re.match(r'- ([ABC]) 「(.+?)」',line)
            if m: opts.append({"id":m[1],"label":m[2]})
        questions.append({"id":f"T1-RL-01:link:{len(questions)+1}","q":next(s for s in d["163"].lines[a-1:b] if s.startswith("**시작:")).replace("**","")[3:].strip(),"options":opts,"answer":answer,"retryPolicy":"currentLinkOnly","success":says("163",correct,correct),"wrongVariants":[{"optionId":key,"script":says("163",line,line)} for key,line in wrong]})
    task("T1-RL-01","reasoning","163",368,questions=questions)
    waves=[]
    for index,(a,b) in enumerate(((428,438),(442,448),(452,458)),1):
        events=says("163",a,b)
        waves.append({"id":f"T1-AA-01:wave:{index}","pairs":[{"claim":events[i],"response":events[i+1]} for i in range(0,len(events),2)],"retryPolicy":"currentWaveLastClaim"})
    task("T1-AA-01","armament","163",420,opponent="taiga",waves=waves,lines=[e["claim"] for w in waves for e in w["pairs"]],final=["카에데의 목을","누른 손을","계속","떼지 않았다"],finalSubject="타이가는",finalDistractors=["보고서만","놓친 손을","입실 전부터","닿게 하지 않았다"],wrongVariants=[{"cause":"paper-or-missed-hand","script":says("163",464,464)},{"cause":"no-contact","script":says("163",468,468)},{"cause":"wrong-order","script":says("163",472,472)}],success=says("163",478,478),failureIsPhysicalHarm=False)
    # Candidate tables, not a generated guess, determine every slot answer.
    root=Path(__file__).resolve().parents[1]
    contract=json.loads((root/'art/v4_production/completion/comic_contracts.json').read_text(encoding='utf-8-sig'))
    slots=[]
    response_ranges=[{'A':(36,46),'C':(48,56),'B':(58,64)},{'B':(74,82),'C':(84,92),'A':(94,100)},{'A':(110,118),'B':(120,128),'C':(130,136)},{'A':(146,156),'C':(158,166),'B':(168,174)},{'B':(184,192),'C':(194,202),'A':(204,212)},{'A':(222,230),'B':(232,240),'C':(242,248)}]
    for record in (s for s in contract['slots'] if s['chapter']==1):
        options=[]
        for option in record['options']:
            raw=d['157'].lines[option['source_line']-1]
            expected=f"|{record['slot']}{option['key']}|{option['description']}|"+('정답' if option['correct'] else '오답')+'|'
            if raw!=expected: raise ValueError('Climax source candidate changed: '+expected)
            path=f"art/reconstruction_v4/candidates/C1_S{record['slot']:02}_{option['key']}.webp"
            if not (root/path).is_file(): raise ValueError('Missing actual climax candidate '+path)
            a,b=response_ranges[record['slot']-1][option['key']]
            options.append({"id":option['key'],"label":option['description'],"image":path,"source":d['157'].ref(option['source_line']),"response":says('157',a,b)})
        slots.append({"id":f"T1-MG-01:slot:{record['slot']}","options":options,"answer":record['correct_key'],"retryPolicy":"currentSlotOnly","priorCorrectSlotsRemain":True})
    task('T1-MG-01','climax','157',7,intro=says('157',8,26),slots=slots,success=says('157',253,283),sourceContractPolicy='Old whole-file hash differs; every current candidate caption/key is checked against its authored table. Candidate visual style still requires whole-scene runtime review.')
    task('T1-VOTE-01','vote','11c2',1505,answer='taiga',candidates=['mio','rei','sora','ken','nana','riku','akari','yuu','koto','satsuki','taiga','rin','sho','ai','haruka','kaede'],deadCandidatesSelectable=True,selectionRole='final-culprit-vote',finalVote=True,wrong=[],wrongPolicy='failure-and-retry-only; no correct-branch aftermath',voteCounts='not authored: majority conclusion only; never invent individual other ballots')
    g.taskDefinitions=tm
    # The player commits a real vote before the correct-result source is read.
    vote=input_node('T1-VOTE-01',seq('11c2',1507,1507,next_id))
    vote_before=seq('11c2',1321,1505,vote)
    armor=input_node('T1-AA-01',vote_before)
    final_dialogue=seq('11c2',1093,1318,armor)
    representative_tail=seq('115',117,None,final_dialogue)
    representative=recall('v4:115:1-C03:trial','1-C03',[('타이가','115',25,44),('카에데','115',47,70),('켄','115',73,92),('기권','115',95,114)],representative_tail)
    representative_intro=seq('115',5,22,representative)
    equipment_late=seq('11c2',951,1090,representative_intro)
    # PN-A03 supersedes the duplicated question at the climax return point.
    pn3=g.add('v4:input:T1-PN-A03',{'type':'task','taskId':'T1-PN-A03','source':d['11c2'].ref(949),'runtimeReady':tm['T1-PN-A03']['runtimeReady'],'next':equipment_late,'success':equipment_late})
    climax=input_node('T1-MG-01',pn3)
    last_argument=seq('11c2',689,944,climax)
    survival=seq('67',5,None,last_argument)
    last_question=seq('11c2',655,686,survival)
    reasoning=input_node('T1-RL-01',last_question)
    after_choice=seq('11c2',169,652,reasoning)
    options=[]
    for key,a,b in [('A',129,140),('B',143,154),('C',157,166)]:
        label=d['11c2'].lines[122+'ABC'.index(key)].split('「',1)[1].rsplit('」',1)[0]
        options.append({'id':key,'label':label,'to':seq('11c2',a,b,after_choice),'set':{'T1-C03':key}})
    menu=g.add('v4:11c2:T1-C03:menu',{'type':'menu','q':'조각에 대해 더 확인할 것','options':options,'source':d['11c2'].ref(121)})
    showdown=input_node('T1-RS-01',seq('11c2',107,118,menu))
    brace=seq('11c2',99,104,showdown)
    common_lie=seq('163',286,308,brace)
    normal=seq('163',216,229,common_lie)
    lying=seq('163',230,285,common_lie)
    g.nodes[lying].setdefault('set',{})['T1-LIE-B']=True
    lie['outcomes']={'A':{'judgment':'refute','transformed':False,'to':normal},'B':{'judgment':'lie','transformed':True,'to':lying,'sets':{'T1-LIE-B':True}}}
    lie_input=input_node('T1-LIE-01',normal,outcomes=lie['outcomes'])
    after_anagram=seq('11c2',79,92,lie_input)
    anagram=input_node('T1-FA-01',after_anagram)
    return seq('11c2',5,76,anagram)
