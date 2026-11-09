"""Chapter-five trial routes, bound to authored source and acquired evidence.

In-memory helper only. The campaign compiler owns output. Image/rhythm
bindings remain actual gates; structural traversal is not gameplay approval.
"""
from __future__ import annotations
import hashlib
import json
import re
from v4_story_case3 import S, C, M, T, V

SOURCE_PREFIXES = ("15c1", "15c2", "15c3", "167", "185", "169", "161", "100", "76", "109", "119", "81", "193")
LEDGER_NAME = "10_5장_정보와행위_원장_스포주의.md"
TRIAL_DEAD = ["kaede", "taiga", "ai", "yuu", "riku", "sora", "ken", "haruka", "rei", "koto"]


def route_source_hashes(sources):
    current = {s.name:s.hash for s in sources.values() if s.prefix in SOURCE_PREFIXES or s.name == LEDGER_NAME}
    if current != REVIEWED_SOURCE_HASHES:
        raise ValueError("Chapter5 trial source changed; re-read exact routes before updating ranges")
    return dict(REVIEWED_SOURCE_HASHES)


def compile_trial_five(g, sources, tasks, next_id):
    from build_v4_story import SPEAKERS
    route_source_hashes(sources)
    docs = {s.prefix:s for s in sources.values() if s.prefix in SOURCE_PREFIXES}
    tm = tasks["tasks"]
    g.taskDefinitions = tm
    _baseline_tasks(tm, docs)
    _bind_additional(tm)
    cache, spans = {}, []
    before = set(g.nodes)

    def uid(label, to=""):
        return "v4:5:trial:" + label + (":" + hashlib.sha256(to.encode()).hexdigest()[:12] if to else "")

    def seq(p,a,b,to):
        source = docs[p]
        b = len(source.lines) if b is None else b
        key = (p,a,b,to)
        if key in cache: return cache[key]
        spans.append({"file":source.name,"first":a,"last":b,"sha256":source.hash})
        result = g.sequence(source,a,b,to)
        cache[key] = result
        return result

    def route(ops,to):
        for op in reversed(ops):
            kind = op[0]
            if kind == "span": to = seq(*op[1:],to)
            elif kind == "case":
                _,flag,rows,required = op
                default = to
                if required:
                    default = g.add(uid("missing:"+flag,to),{"type":"gate","reason":"Required earlier authored choice absent: "+flag})
                cases = []
                for values,body in rows:
                    target = route(body,to)
                    for value in values if isinstance(values,tuple) else (values,):
                        cases.append({"flag":flag,"equals":value,"to":target})
                to = g.add(uid("branch:"+flag,to),{"type":"branch","cases":cases,"default":default})
            elif kind == "menu":
                _,p,line,flag,labels,bodies = op
                options = [{"id":"ABC"[ix],"label":label,"to":route(body,to),"set":{flag:"ABC"[ix]}} for ix,(label,body) in enumerate(zip(labels,bodies))]
                to = g.add(uid("choice:"+flag),{"type":"menu","q":docs[p].lines[line-1].lstrip("# "),"source":docs[p].ref(line),"options":options})
            elif kind == "set":
                to = g.add(uid("state",json.dumps(op[1],sort_keys=True)+to),{"type":"stage","direction":"","set":op[1],"next":to})
            elif kind == "task":
                task = tm[op[1]]
                to = g.add("v4:input:"+op[1],{"type":"task","taskId":op[1],"runtimeReady":task["runtimeReady"],"source":task["source"],"next":to,"success":to})
            elif kind == "lie":
                _,tid,normal,inverted = op
                a = route(normal,to)
                b = route(inverted,to)
                outcomes = {"A":{"judgment":"refute","transformed":False,"to":a,"sets":{"T5-LIE-B":False}},"B":{"judgment":"lie","transformed":True,"transformedJudgment":"agree","requireAgreement":True,"to":b,"sets":{"T5-LIE-B":True}}}
                tm[tid]["outcomes"] = outcomes
                to = g.add("v4:input:"+tid,{"type":"task","taskId":tid,"runtimeReady":tm[tid]["runtimeReady"],"source":tm[tid]["source"],"outcomes":outcomes,"next":a,"success":a})
            elif kind == "document":
                _,p,a,b,title = op
                rows = [l.removeprefix("- ") for l in docs[p].lines[a-1:b] if l.strip()]
                to = g.add(uid("document:"+p+":"+str(a)),{"type":"document","title":title,"rows":rows,"source":docs[p].ref(a),"next":to,"private":False})
            else: raise ValueError("Unknown chapter5 trial operation "+kind)
        return to

    entry = route(_trial_ops(),next_id)
    for nid in set(g.nodes)-before:
        n = g.nodes[nid]
        if n["type"] == "task":
            n.update(trialDead=list(TRIAL_DEAD),seats=[a for a in SPEAKERS.values() if a != "lappy"],rosterSource=docs["15c1"].ref(3))
            t = tm[n["taskId"]]
            for key in ("scrumSession","roundIndex","roundCount","sessionEndAfterParentConfrontation"):
                if key in t: n[key] = t[key]
    # Keep metadata on the graph; the central compiler merges this into export.
    g.trialFiveRanges = spans
    g.trialFiveGuards = {"fixedCulprit":"akari","currentAlive":6,"trialDead":list(TRIAL_DEAD),"threeScrumRoundsInterleaved":True,"finalVoteOwnersPublicOnlyAfterResult":True,"physicalRewindNotMemoryRecovery":True,"noHypotheticalBottleAcquired":True,"executionOwnedByCaller":True}
    return entry


def _trial_ops():
    return [
        V({"T5-LIE-B":False}), S("15c1",5,16), T("T5-NS-01"), S("15c1",21,84),
        M("15c1",87,"T5-C01",["되감긴 뒤 현재의 접촉을 짚는다","다 마신 뒤 빈잔을 회수한 시점을 짚는다","글을 읽기 전후 달라진 말을 묻는다"],[[S("15c1",93,122)],[S("15c1",123,158)],[S("15c1",159,188)]]),
        S("15c1",191,196), T("T5-RS-01"), S("15c1",301,312),
        S("100",5,108), M("100",109,"T5-C03",["회수와 음용의 행위를 나눈다","남은 기록과 돌아간 물건을 나눈다","되감기 뒤에도 남은 앞부분을 묻는다"],[[S("100",113,126)],[S("100",127,140)],[S("100",141,158)]]), S("100",161,278),
        S("15c1",315,344), T("T5-FA-01"), S("15c1",377,404),
        C("5-C05",[("A",[S("15c1",405,410)]),("B",[S("15c1",411,418)]),("C",[S("15c1",419,426)])]), S("15c1",429,464),
        C("5-C05",[("A",[S("15c1",467,469)]),("B",[S("15c1",470,472)]),("C",[S("15c1",473,475)])]), S("15c1",477,494),
        C("5-C05",[(("A","B"),[S("15c1",495,498)]),("C",[S("15c1",499,502)])]), S("15c1",505,676),
        S("15c2",5,16), T("T5-PN-01"), S("15c2",21,124), S("76",5,68),
        C("5-C06",[("A",[S("76",71,82)]),("B",[S("76",83,92)]),("C",[S("76",93,106)])]), S("76",107,None),
        S("15c2",127,192), T("T5-MM-01"), S("15c2",195,310), S("167",132,137),
        ("lie","T5-LIE-01",[S("169",252,257)],[S("169",258,302)]),
        S("15c2",315,328), S("109",5,240), T("T5-SD-02"), S("15c2",335,352), T("T5-SD-03"), S("15c2",355,404), S("167",196,215),
        S("193",5,None), S("15c2",407,822), T("T5-RL-01"), S("15c2",825,1066),
        S("15c3",5,213), S("119",5,128), S("15c3",216,239), S("161",7,20), T("T5-MG-01"), S("161",229,256), S("15c3",242,247),
        C("5-C04",[("A",[S("15c3",248,251)]),("B",[S("15c3",252,255)]),("C",[S("15c3",256,259)])]), S("15c3",260,343),
        S("81",5,166), S("15c3",346,427),
        M("15c3",430,"T5-C02",["자신의 표가 가져올 죽음을 안다고 답한다","다른 사람에게 대신 책임지라고 하지 말라고 답한다","대답하지 않고 투표를 준비한다"],[[S("15c3",436,489)],[S("15c3",490,545)],[S("15c3",546,569)]]),
        S("15c3",572,581), T("T5-AA-01"), T("T5-VOTE-01"), S("15c3",584,588),
        ("document","15c3",590,592,"투표 결과"), S("15c3",594,972),
    ]


def _bind_additional(tm):
    bind={"T5-NS-A01":("01",),"T5-NS-A02":("15",),"T5-NS-A03":("05",),"T5-NS-A04":("05","20"),"T5-NS-A05":("18",),"T5-NS-A06":("19",),"T5-NS-A07":("13","19"),"T5-NS-A08":("19",),"T5-NS-A09":("13",),"T5-NS-A10":("02","01","14"),"T5-NS-A11":("20",),"T5-EVIDENCE-A01":("03",),"T5-PN-A02":("08",),"T5-PN-A03":("02",),"T5-RS-A02":("16","17"),"T5-RS-A03":("18","20")}
    for tid,codes in bind.items():
        t=tm[tid]
        t.update(answerEvidenceId="v4:E5-"+codes[0],requiresEvidence=["v4:E5-"+c for c in codes],evidencePool="actually-acquired-v4-cards-only")
        t["bindings"]=[b for b in t["bindings"] if b["kind"] != "evidenceAcquisition"]
        t["runtimeReady"]=not any(b.get("required") for b in t["bindings"])


def _baseline_tasks(tm,docs):
    def events(p,a,b): return [e for e in docs[p].paragraphs(a,b) if e["type"] in ("say","stage")]
    def says(p,a,b): return [e for e in events(p,a,b) if e["type"] == "say"]
    def make(tid,kind,p,line,**fields):
        ref=docs[p].ref(line)
        title=ref["heading"].split(" ",1)[-1].split(" — ",1)[0]
        tm[tid]={"id":tid,"kind":kind,"chapter":"5","sourceKind":"BASELINE","source":ref,"title":title,"prompt":title,"intro":[],"lines":[],"wrong":[],"success":[],"bindings":[],"return":{"graphNext":True},"runtimeReady":True,"retry":{"sameTask":True,"preserveEvidence":True,"preservePublicFacts":True,"cancellationIsSuccess":False},**fields}
        return tm[tid]
    for tid,kind,p,a,b,weak,codes,wrongs,success in (
        ("T5-NS-01","nonstop","167",5,30,"더 안 맞춰도 돼",["01","02","20"],[(31,36),(37,44)],(45,54)),
        ("T5-PN-01","panic","167",55,70,"얼굴만 바꾸면 되니까",["13"],[(71,76),(77,86)],(87,98)),
        ("T5-RS-01","showdown","15c1",197,247,"다 마신 뒤 빈잔을 가져온 게,코토에게 넣은 거야",["05","20","01"],[(249,258),(259,268),(269,278)],(279,300)),
    ):
        lines=says(p,a,b); target=next(e for e in lines if weak in e["text"])
        make(tid,kind,p,a,lines=lines,intro=[e for e in events(p,a,b) if e["type"]=="stage"],targets=[{"lineId":target["id"],"word":weak,"actor":target["actor"],"verdict":"refute"}],answerEvidenceId="v4:E5-"+codes[0],requiresEvidence=["v4:E5-"+c for c in codes],evidencePool="actually-acquired-v4-cards-only",judgment="refute",wrongVariants=[{"cause":"source-wrong-"+str(i),"script":events(p,x,y)} for i,(x,y) in enumerate(wrongs,1)],success=events(p,*success))
    tm["T5-PN-01"]["lanes"]=[{"id":pos,"actor":actor,"lines":[e["id"] for e in tm["T5-PN-01"]["lines"] if e["actor"]==actor]} for pos,actor in (("왼쪽","satsuki"),("가운데","rin"),("오른쪽","sho"))]
    tm["T5-PN-01"]["laneLayoutPolicy"]="authored first-speaker layout; no added witness facts"
    make("T5-MM-01","mindmine","167",99,intro=events("167",103,103),regionDescription="가방 포장과 D칸 조각의 이어지는 인쇄·찢긴 경계 및 회수D 마개의 끊긴 띠 끝",imageDescription="이미 수사에서 확인한 실물 포장과 마개 띠 비교 도식",wrongVariants=[{"cause":"wrong-region:"+c,"script":events("167",a,b)} for c,a,b in (("A",112,115),("C",116,119),("D",120,125))],success=events("167",126,131),bindings=[{"kind":"forensicImageRegions","required":True,"description":"Bind the two actually inspected joining boundaries; never use answer-option index as a region."}],runtimeReady=False)
    lie=make("T5-LIE-01","nonstop","169",228,lines=says("169",232,240),answerEvidenceId="v4:E5-17",requiresEvidence=["v4:E5-08","v4:E5-09","v4:E5-17"],evidencePool="actually-acquired-v4-cards-only",judgment="refute-or-intentional-lie-agreement",wrong=events("169",244,250),wrongVariants=[{"cause":"character-not-physical-state","script":events("167",144,150)}],scrumSession="T5-SD-01",roundIndex=1,roundCount=3,sessionEndAfterParentConfrontation=True)
    claim=re.search(r"「(.+)」",docs["167"].lines[139])[1].replace("**","")
    lie["intro"]=[{"id":"v4:167:T5-SD-02:spoken-claim","type":"say","speaker":"아카리","actor":"akari","text":claim,"mono":False,"source":docs["167"].ref(140)}]
    tm["T5-RS-01"]["phases"]=[{"id":"first","source":docs["15c1"].ref(197),"startLine":199,"endLine":217},{"id":"development","source":docs["15c1"].ref(219),"startLine":221,"endLine":239},{"id":"final","source":docs["15c1"].ref(241),"startLine":243,"endLine":247}]
    last=lie["lines"][-1]
    lie["targets"]=[{"lineId":last["id"],"word":"D는 여기서 빼도","actor":"akari","verdict":"refute"},{"lineId":last["id"],"word":"다른 병이 있으면","actor":"akari","verdict":"lie","transformedJudgment":"agree","requireAgreement":True}]
    lie["transformation"]={"sourceEvidenceId":"v4:E5-17","sourceEvidenceIds":["v4:E5-08","v4:E5-09","v4:E5-17"],"normalLabel":"D 외 다섯 용기 미개봉/마지막 준비까지 D 띠 연결","lieLabel":"D 외 다른 용기도 열려 있었음","intentionalHold":True,"changesHistoricalFacts":False,"createsBottle":False,"transformedJudgment":"agree","requireAgreement":True}
    teams={"us":["mio","rin","sho"],"them":["akari","nana","satsuki"]}
    lie["teams"]=teams
    for tid,index,a,b,them,us,reply,wrong,keyword,response in (
        ("T5-SD-02",2,152,173,"nana","rin",160,166,"제가 어느 잔을 드리려고 했는지","미리 지정하지 않은 새 잔 여섯/그 뒤 아카리의 선택/개인 잔만 양성"),
        ("T5-SD-03",3,174,195,"satsuki","sho",182,188,"자기가 마셨잖아.그러면 자기가 한 거 아니야?","손으로 마신 행동과 R-7을 알고 선택한 행동의 구별"),
    ):
        raw=docs["167"].lines[a+3];quote=re.search(r"「(.+)」",raw)[1].replace("**","")
        first=says("167",reply,wrong-1)[0]
        pair={"id":tid+":round:"+str(index),"them":them,"themText":quote,"keyword":keyword,"us":us,"usText":first["text"],"responseKeyword":response,"success":events("167",reply,wrong-1),"wrong":events("167",wrong+1,b),"source":docs["167"].ref(a)}
        make(tid,"scrum","167",a,pairs=[pair],teams=teams,scrumSession="T5-SD-01",roundIndex=index,roundCount=3,sessionEndAfterParentConfrontation=True,teamMeaning="current question alignment, not final vote ownership")
    questions=[]
    for no,(a,b,answer,prompt) in enumerate(((220,241,"B","16:52의 10초로 돌아가지 않은 것은?"),(242,263,"B","원래 구간의 설명은 누구의 기억에서 왔을까?")),1):
        opts=[{"id":m[1],"label":m[2]} for l in docs["167"].lines[a-1:b] if (m:=re.match(r"^- ([ABC]) (.+)$",l))]
        heads=[(i,m[1]) for i in range(a,b+1) if (m:=re.match(r"^\*\*([ABC]) — (?:정답|오답)",docs["167"].lines[i-1]))]
        scripts={k:events("167",line+1,heads[ix+1][0]-1 if ix+1<len(heads) else b) for ix,(line,k) in enumerate(heads)}
        questions.append({"id":"T5-RL-01:link:"+str(no),"q":prompt,"options":opts,"answer":answer,"success":scripts[answer],"wrongVariants":[{"optionId":k,"script":v} for k,v in scripts.items() if k!=answer],"retryPolicy":"currentLinkOnly","source":docs["167"].ref(a)})
    make("T5-RL-01","reasoning","167",216,questions=questions)
    make("T5-FA-01","anagram","15c1",345,intro=events("15c1",347,349),answer="사용횟수",answerGlyphs=list("사용횟수"),distractorDescription="기/억/시/각",mechanic={"selectGlyphCount":1,"arrivalJudgment":True,"poolSlots":20,"specialCollectibleSeparate":True},wrongVariants=[{"cause":c,"script":events("15c1",a,b)} for c,a,b in (("memory",353,357),("clock",359,363),("order",365,369))],success=events("15c1",371,375),retryPolicy="wrongSlotOnly",editorialMechanicCorrection="REA V3 uses one selected glyph and arrival judgment; manuscript identical-pair instruction is not executable")
    make("T5-AA-01","armament","167",264,intro=events("167",268,268),waves=[{"id":"T5-AA-01:wave:"+str(i),"script":events("167",a,b),"retryPolicy":"sameWave"} for i,(a,b) in enumerate(((272,275),(278,285),(288,295)),1)],answerParts=["다른 이름을 눌러","우리가 틀리게 하고","네가 살아나갈","표를 요구하고 있어."],distractors=["아무 이름도 안 눌러","모두가 맞게 하고","아무도 죽지 않을","허락을 받은 거야"],wrongVariants=[{"cause":c,"text":text,"source":docs["167"].ref(line)} for c,text,line in (("no-death","그 방법은 확인하지 못했어.그랬으면 좋겠다는 말을 규칙으로 고르면 안 돼.",300),("permission","아카리는 살고 싶다고 했어.네가 고르는 표를 좋다고 해 줬다고 바꾸지 마.",301),("order","우리 오답의 뒤에 아카리가 남는 조건이야.누가 그 비용을 지는지 빠뜨리지 말고.",302))],success=events("167",304,318),bindings=[{"kind":"rhythmWaveTiming","required":True,"description":"Bind all three authored changing beat patterns and exact input windows."}],runtimeReady=False)
    slots=[]
    for no,(a,b,answer) in enumerate(((21,56,"1B"),(57,92,"2C"),(93,126,"3A"),(127,158,"4B"),(159,192,"5C"),(193,228,"6A")),1):
        candidates=[{"id":m[1],"imageDescription":m[2]} for l in docs["161"].lines[a-1:b] if (m:=re.match(r"^\|([1-6][ABC])\|([^|]+)\|(?:정답|오답)\|",l))]
        heads=[(i,m[1]) for i in range(a,b+1) if (m:=re.match(r"^### ([1-6][ABC])를 놓았다",docs["161"].lines[i-1]))]
        responses={k:events("161",line+1,heads[ix+1][0]-1 if ix+1<len(heads) else b) for ix,(line,k) in enumerate(heads)}
        slots.append({"id":"T5-MG-01:slot:"+str(no),"candidates":candidates,"answer":answer,"wrong":{k:v for k,v in responses.items() if k!=answer},"success":responses[answer],"retryPolicy":"currentSlotOnly","source":docs["161"].ref(a)})
    make("T5-MG-01","climax","161",21,slots=slots,bindings=[{"kind":"authoredComicPanels","required":True,"description":"Bind all18 exact candidate comic panels; textual answers do not complete the comic mechanic."}],runtimeReady=False)
    make("T5-VOTE-01","vote","15c3",584,answer="akari",candidates=["mio","rei","sora","ken","nana","riku","akari","yuu","koto","satsuki","taiga","rin","sho","ai","haruka","kaede"],deadCandidatesSelectable=True,finalVote=True,authoredResult={"total":6,"akari":4,"satsuki":1,"nana":1,"otherVoteOwnerRevealedOnlyAfterResult":True})


REVIEWED_SOURCE_HASHES = {
    "100_5장_돌아온_잔_남아_있는_글_보강.md": "e5f99c08c355ccb6062b30604605ff10855c6bea87331044e1412ec8928466db",
    "109_5장_네가_버려_주겠다고_했잖아_보강.md": "c4b8ea242c24a87d4f269c6741cf3d41cd85afdd53eaffe8f45daf111b1efe96",
    "10_5장_정보와행위_원장_스포주의.md": "1703eda8d03c0ae83feb66491f99e1ed5dcd7920b8264ac6c75203423a0c7296",
    "119_5장_상처가_없다는_말을_믿었던_사람_보강.md": "e3af5cacfca2f8359f8f33b78b83cf9b50a15ee31860825c23ef8c6c1ef8bfd1",
    "15c1_5장_재판_빈잔의_자백_초고.md": "0755f2cfe8906330a6c58c35243dd85720923ea7bb07594d68969b1975298d95",
    "15c2_5장_재판_열었던_손_초고.md": "d3766924530f626788a2632c088d3bd9432f257298561574f96e699b81cd46d0",
    "15c3_5장_재판_남겨_두려던_사람_초고.md": "c3a1b845cb9c702dab7a0520e17c68ed5babbecc37c246464985e3e7592efb55",
    "161_5장_재구성만화_슬롯과_실제문답.md": "8bfbd495838bf97a3c1207be5be171275371674c83658ca0ae1517a51e1dedc4",
    "167_5장_재판_형식별_연속대본.md": "0bd5da3ec11b1fddc5ac5b6a2a91096f7152a42a91a0cc0dd6d5a5980f116c3a",
    "169_2_4_5_6장_우소다마와_후과_연속대본.md": "954fbe7b6d6f59c6f2dedd9c564654f08a20f15f378fdc284c27ec66d7428964",
    "185_5장_재판_반복논의와_지목_연속대본.md": "c0d5728b2ac6884a5c0a65e17d58ad69ee5ad28d166f2f7027833262c74df075",
    "76_5장_믿지_않는_사람의_증언_보강.md": "37be6b767c101061e478542b4dcb598c489af175888d6c095acfe6e9dd8ec09d",
    "81_5장_네가_미안하다면_보강.md": "a3f4228011aa0abdd5078067d4f520c31d3c8dc6cb80bff990c88c174abb05b7",
    "193_5장_재판_죽어서_좋았다는_말_연속대본.md": "968cc8c2c6e03596cc076fc47c56a54f3bf14c749489701806a9b4d23871b813"
}
