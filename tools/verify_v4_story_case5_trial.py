"""Static/synthetic traversal of authored chapter5 trial; no runtime or timing claim."""
import copy
import itertools
import json
from build_v4_story import ROOT, Source, Graph, compile_tasks
from v4_story_case5_trial import compile_trial_five, route_source_hashes, TRIAL_DEAD

CHOICES=("5-C04","5-C05","5-C06","T5-C01","T5-C03","T5-C02")


def fixture():
    sources={p.name:Source(p) for p in (ROOT/"docs/design/rewrite_v4").glob("*.md")}
    tasks=compile_tasks(sources,json.loads((ROOT/"docs/design/rewrite_v4/qa_2026-10-29/trial_input_reedit.json").read_text(encoding="utf-8-sig")))
    g=Graph("5");end=g.add("test:5:result",{"type":"end"})
    entry=compile_trial_five(g,sources,tasks,end)
    return sources,tasks,g.export(entry)


def _events(obj):
    if isinstance(obj,dict):
        if obj.get("type") in ("say","stage"):yield obj
        else:
            for value in obj.values():yield from _events(value)
    elif isinstance(obj,list):
        for value in obj:yield from _events(value)


def walk(graph,tasks,choices,missing=None):
    flags={c:choices.get(c,"A") for c in CHOICES if c!=missing}
    trace=[];inputs=[];nid=graph["entry"];seen=set();owned={"v4:E5-"+f"{i:02}" for i in range(1,21)}
    def add(events):trace.extend(events)
    while True:
        assert nid not in seen,"Control loop "+nid
        seen.add(nid);n=graph["nodes"][nid];flags.update(n.get("set",{}))
        if n["type"]=="branch":nid=next((c["to"] for c in n["cases"] if flags.get(c["flag"],False)==c["equals"]),n["default"])
        elif n["type"]=="menu":
            flag=next(iter(n["options"][0]["set"]));key=choices.get(flag,"A")
            opt=next(o for o in n["options"] if o["id"]==key);flags.update(opt["set"]);nid=opt["to"]
        elif n["type"]=="task":
            t=tasks["tasks"][n["taskId"]];inputs.append(n["taskId"])
            assert set(t.get("requiresEvidence",[]))<=owned,n["taskId"]
            assert n["trialDead"]==TRIAL_DEAD
            assert len(n["seats"])==16 and "akari" not in n["trialDead"]
            trace.append({"type":"test-input","taskId":n["taskId"]})
            add(t.get("intro",[]));add(t.get("lines",[]))
            for q in t.get("questions",[]):add(q.get("success",[]))
            for pair in t.get("pairs",[]):add(pair.get("success",[]))
            for slot in t.get("slots",[]):add(slot.get("success",[]))
            for wave in t.get("waves",[]):add(wave.get("script",[]))
            if "outcomes" in n:
                result=n["outcomes"][choices.get("lie","A")];flags.update(result.get("sets",{}));nid=result["to"]
            else:add(t.get("success",[]));nid=n["success"]
        elif n["type"]=="end":return trace,flags,inputs,None
        elif n["type"]=="gate":return trace,flags,inputs,n
        else:trace.append(n);nid=n["next"]


def main():
    sources,tasks,g=fixture();docs={s.prefix:s for s in sources.values()}
    task_ids={n["taskId"] for n in g["nodes"].values() if n["type"]=="task"}
    assert len(task_ids)==39
    all_events={e["id"] for e in _events(g["nodes"])}|{e["id"] for tid in task_ids for e in _events(tasks["tasks"][tid])}
    for p in ("15c1","15c2","15c3"):
        expected=[e for e in docs[p].paragraphs() if e["type"]=="say"]
        assert not [e["source"]["line"] for e in expected if e["id"] not in all_events],p
    source_tasks={"T5-LIE-01","T5-SD-02","T5-SD-03"}
    assert {tasks["tasks"][x]["roundIndex"] for x in source_tasks}=={1,2,3}
    assert all(tasks["tasks"][x]["scrumSession"]=="T5-SD-01" for x in source_tasks)
    assert tasks["tasks"]["T5-LIE-01"]["transformation"]["createsBottle"] is False
    assert tasks["tasks"]["T5-LIE-01"]["outcomes"]["B"]["requireAgreement"]
    assert tasks["tasks"]["T5-FA-01"]["mechanic"]["selectGlyphCount"]==1
    assert tasks["tasks"]["T5-MG-01"]["runtimeReady"] is False
    assert [s["answer"] for s in tasks["tasks"]["T5-MG-01"]["slots"]]==["1B","2C","3A","4B","5C","6A"]
    assert len([c for s in tasks["tasks"]["T5-MG-01"]["slots"] for c in s["candidates"]])==18
    # Full Cartesian choices: no unrealized conversation or false timeline becomes memory.
    count=0
    for values in itertools.product("ABC",repeat=len(CHOICES)):
        choices=dict(zip(CHOICES,values))
        for lie in "AB":
            choices["lie"]=lie
            trace,flags,inputs,gate=walk(g,tasks,choices)
            assert gate is None,gate
            assert len(inputs)==len(set(inputs))==39
            assert flags["T5-LIE-B"]==(lie=="B")
            source_lines=[(e["source"]["file"],e["source"]["line"]) for e in trace if "source" in e]
            for p,flag,spans in (("15c1","5-C05",[(405,410),(411,418),(419,426)]),("76","5-C06",[(71,82),(83,92),(93,106)]),("15c3","5-C04",[(248,251),(252,255),(256,259)]),("15c1","T5-C01",[(93,122),(123,158),(159,188)]),("100","T5-C03",[(113,126),(127,140),(141,158)]),("15c3","T5-C02",[(436,489),(490,545),(546,569)])):
                chosen="ABC".index(choices[flag]);name=docs[p].name
                for ix,(a,b) in enumerate(spans):
                    got=[line for file,line in source_lines if file==name and a<=line<=b]
                    assert bool(got)==(ix==chosen),(flag,choices[flag],ix)
            ids=[e.get("taskId") for e in trace]
            ix1=ids.index("T5-LIE-01");ix2=ids.index("T5-SD-02");ix3=ids.index("T5-SD-03")
            between=lambda a,b,p,x,y:any(e.get("source",{}).get("file")==docs[p].name and x<=e["source"]["line"]<=y for e in trace[a:b])
            assert ix1<ix2<ix3
            assert between(ix1,ix2,"109",5,240)
            assert between(ix2,ix3,"15c2",335,352)
            assert between(ix3,ids.index("T5-RL-01"),"167",196,215)
            vote=ids.index("T5-VOTE-01")
            assert ids.index("T5-AA-01")<vote
            assert all(i>vote for i,e in enumerate(trace) if e.get("source",{}).get("file")==docs["15c3"].name and e["source"]["line"]>=590)
            assert not any(e.get("source",{}).get("file")==docs["15c3"].name and e["source"]["line"]>=974 for e in trace)
            lie_lines=[line for file,line in source_lines if file==docs["169"].name]
            assert any(258<=line<=302 for line in lie_lines)==(lie=="B")
            count+=1
    for flag in ("5-C04","5-C05","5-C06"):
        assert walk(g,tasks,{},missing=flag)[3] is not None
    # Every explicit continuation exists and no card is granted inside a hypothesis.
    for n in g["nodes"].values():
        assert n["type"] != "evidence"
        tos=[n[k] for k in ("next","success","default") if k in n]
        tos += [o["to"] for key in ("cases","options","outcomes") for o in (n.get(key,{}).values() if key=="outcomes" else n.get(key,[]))]
        assert all(to in g["nodes"] for to in tos),n["id"]
    expected_returns={"T5-NS-A01":("15c1",43),"T5-NS-A02":("15c1",55),"T5-NS-A03":("15c1",69),"T5-NS-A04":("15c1",81),"T5-NS-A05":("15c1",307),"T5-NS-A06":("15c1",319),"T5-NS-A07":("15c1",331),"T5-NS-A08":("15c2",9),"T5-NS-A09":("15c2",117),"T5-NS-A10":("15c2",325),"T5-NS-A11":("15c2",363),"T5-PERSON-A01":("15c2",143),"T5-PERSON-A02":("15c3",272),"T5-CULPRIT-A01":("15c2",733),"T5-EVIDENCE-A01":("15c2",949),"T5-PN-A02":("15c2",135),"T5-PN-A03":("15c1",655),"T5-RS-A02":("15c2",263),"T5-RS-A03":("15c2",631),"T5-MM-A02":("15c2",257),"T5-MM-A03":("15c2",321),"T5-FA-A02":("15c2",129),"T5-FA-A03":("15c2",409),"T5-RL-A02":("15c1",341),"T5-RL-A03":("15c2",943)}
    for tid,(p,line) in expected_returns.items():
        target=g["nodes"][g["nodes"]["v4:input:"+tid]["success"]]
        # A heading has no player event; compare its first actual event.
        expected=next(e for e in docs[p].paragraphs(line) if e["type"] in ("say","stage"))
        assert target["id"]==expected["id"],(tid,target["id"],expected["id"])
    assert g["nodes"][g["nodes"]["v4:input:T5-SPOT-A01"]["success"]]["taskId"]=="T5-MM-A02"
    assert g["nodes"][g["nodes"]["v4:input:T5-ANSWER-A01"]["success"]]["taskId"]=="T5-RL-01"
    from v4_native_tasks import convert_task
    catalogue={"v4:E5-"+f"{i:02}":{"id":"v4:E5-"+f"{i:02}","name":"acquired-test-card"} for i in range(1,21)}
    converted=[convert_task(tasks["tasks"][tid],catalogue) for tid in sorted(task_ids)]
    ready=sum(bool(x.get("ready")) for x in converted)
    assert ready==33
    lie=next(x for x in converted if x["taskId"]=="T5-LIE-01")
    assert lie["transformation"]["requireAgreement"] is True
    changed=copy.copy(next(s for s in sources.values() if s.prefix=="15c1"));changed.hash="changed"
    altered=dict(sources);altered[changed.name]=changed
    try:route_source_hashes(altered)
    except ValueError:pass
    else:raise AssertionError("Source guard accepted changed source")
    print(json.dumps({"status":"PASS","scope":"static and synthetic only; no native execution or playtime approval","nodes":len(g["nodes"]),"tasks":len(task_ids),"choiceRoutes":count,"sourceGuardFiles":len(route_source_hashes(sources)),"adapterReady":ready,"bindingGates":[tid for tid in sorted(task_ids) if not tasks["tasks"][tid]["runtimeReady"]]},ensure_ascii=False))


if __name__=="__main__":main()
