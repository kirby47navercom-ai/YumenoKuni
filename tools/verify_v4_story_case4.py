"""Read-only chapter4 routing checks; structural task success is assumed only
to inspect authored continuation. This is not native play or time measurement.
"""
import copy
import itertools
import json

from build_v4_story import ROOT, Source
from v4_story_case4 import compile_chapter_four, route_source_hashes, _daily_ops, _investigation_ops, _trial_ops, _result_ops

CHOICES = tuple(["4-C" + f"{i:02}" for i in range(1, 12)] + ["W4-C01", "W4-C12", "I4-C01", "I4-C02", "T4-C01", "T4-C02"])


def fixture():
    sources = {p.name: Source(p) for p in (ROOT / "docs/design/rewrite_v4").glob("*.md")}
    tasks = json.loads((ROOT / "data/v4_story/tasks.json").read_text(encoding="utf-8-sig"))
    ft = {p: {"entry": "test:fte:" + p, "nodes": {"test:fte:" + p: {"id": "test:fte:" + p, "type": "return"}}} for p in ("38", "37", "62", "88", "38-late", "57", "64")}
    return sources, tasks, compile_chapter_four(sources, ft, tasks)


def walk(g, tasks, choices, history=None, until_gate=False):
    flags = {"fte:" + p + ":complete": True for p in ("29", "38", "34", "37", "31", "39")}
    flags.update({"F-AK03-A": "A1", "F-AK03-B": "B1", "F-HA03-A": "A1", "F-HA03-B": "B1", "F-HA01-A": "A1", "F-HA01-B": "B1", "F-NA03-A": "A1", "F-NA03-B": "B1", "F-RE03-A": "A1", "F-RE03-B": "B1", "SHO-03A": "A1", "SHO-03B": "B1"})
    flags.update(history or {})
    nid, stack, trace, owned, inputs, seen = g["entry"], [], [], set(), [], set()
    while True:
        n = g["nodes"][nid]
        trace.append(n)
        state = (nid, tuple((frame[0], tuple(sorted(frame[1].items()))) for frame in stack))
        assert state not in seen, "Unexpected control loop " + nid
        seen.add(state)
        flags.update(n.get("set", {}))
        kind = n["type"]
        if kind == "branch":
            nid = next((c["to"] for c in n["cases"] if flags.get(c["flag"], False) == c["equals"]), n["default"])
        elif kind == "menu":
            options = [o for o in n["options"] if all(flags.get(k, False) == v for k, v in o.get("requires", {}).items())]
            flag = next((f for f in CHOICES if any(f in o.get("set", {}) for o in options)), None)
            selected = choices.get(flag) if flag else choices.get(n.get("window"), {"4-morning12": "62", "4-early13": "continue", "4-afternoon13": "64"}.get(n.get("window")))
            option = next((o for o in options if o["id"] == selected), None)
            assert option is not None, (n["id"], selected)
            flags.update(option.get("set", {})); nid = option["to"]
        elif kind == "call":
            stack.append((n["returnTo"], n.get("onReturnSet", {}))); nid = n["target"]
        elif kind == "return":
            nid, after = stack.pop(); flags.update(after)
        elif kind == "investigate":
            pending = [s for s in n["spots"] if not flags.get(s["completionFlag"], False)]
            if pending:
                s = pending[0];seen.remove(state)
                stack.append((s["returnTo"], s["onReturnSet"]));nid = s["entry"]
            else: nid = n["next"]
        elif kind == "task":
            t = tasks["tasks"][n["taskId"]]
            assert set(t.get("requiresEvidence", [])) <= owned, n["taskId"]
            inputs.append(n["taskId"])
            if n.get("outcomes"):
                chosen = n["outcomes"][choices.get("lie", "A")]
                flags.update(chosen.get("sets", {}));nid = chosen["to"]
            else: nid = n["success"]
        elif kind == "evidence":
            owned.add(n["evidenceId"]);nid = n["next"]
        elif kind == "gate":
            if until_gate:return trace, flags, owned, inputs
            raise AssertionError(n["reason"])
        elif kind == "end":
            assert not stack
            return trace, flags, owned, inputs
        else: nid = n["next"]


def main():
    sources, tasks, g = fixture()
    nodes = g["nodes"]
    for n in nodes.values():
        for field in ("next", "success", "default", "target", "returnTo"):
            if field in n:assert n[field] in nodes, (n["id"],field)
        for child in n.get("cases", []) + n.get("options", []):assert child["to"] in nodes
        for outcome in n.get("outcomes", {}).values():assert outcome["to"] in nodes
        if n["type"] == "task":
            assert n["taskId"] in tasks["tasks"]
            assert len(n["seats"]) == 16 and len(n["trialDead"]) == 8
        for spot in n.get("spots", []):assert not spot["geometryReady"] and spot["target_id"] is None
    base = {f: "A" for f in CHOICES}
    trace, state, owned, input_ids = walk(g, tasks, base)
    assert len(input_ids) == len(set(input_ids)) == 36
    assert len(owned) == len(g["evidenceCatalog"]) == 20
    assert state["4:livingBodies"] == 7 and state["4:biologically-dead"] and not state["4:form-remains"]
    assert state["4:origin-belief-restored"] and not state["4:independent-erasure-restored"]
    assert input_ids[-1] == "T4-VOTE-01"

    # Build constraints only from explicitly authored menu alternatives. Later
    # callbacks have independent assertions below; no source text is changed.
    constraints = []
    def inspect(ops):
        for op in ops:
            if op[0] == "menu":
                for letter, body in zip("ABC", op[5]):
                    for row in body:
                        if row[0] == "span":constraints.append((row[1], row[2], row[3], op[3], letter))
                    inspect(body)
            elif op[0] == "case":
                for _, body in op[2]:inspect(body)
            elif op[0] == "investigate":inspect(op[4])
            elif op[0] == "lie":inspect(op[2]);inspect(op[3])
            elif op[0] == "ifelse":inspect(op[2]);inspect(op[3])
    inspect(_daily_ops() + _investigation_ops() + _trial_ops() + _result_ops())
    scenarios = [base]
    for a,b in itertools.combinations(CHOICES, 2):
        for x,y in itertools.product("ABC", repeat=2):scenarios.append({**base,a:x,b:y})
    for selected in scenarios:
        for lie in ("A", "B"):
            trace, flags, cards, inputs = walk(g, tasks, {**selected,"lie":lie})
            assert cards == owned and inputs == input_ids
            assert flags["T4-LIE-B"] == (lie == "B")
            for n in trace:
                ref = n.get("source",{});p = ref.get("file","").split("_",1)[0];line = ref.get("line",0)
                for prefix,a,b,flag,letter in constraints:
                    if prefix == p and isinstance(a,int) and isinstance(b,int) and a <= line <= b:
                        assert selected[flag] == letter,(p,line,flag,letter)
    # Late 01 and the next day's separate late02: two earned calls, no double
    # meeting in one window, with actual completion applied only on return.
    late = {"fte:29:complete": False,"fte:38:complete": False,"fte:88:complete":False}
    _, late_flags, _, _ = walk(g,tasks,{**base,"4-morning12":"88","4-early13":"38-late","4-afternoon13":"57"},late)
    assert late_flags["fte:88:complete"] and late_flags["fte:29:complete"] and late_flags["fte:38:complete"] and late_flags["fte:57:complete"]

    histories = []
    for p,af,bf in (("62","F-AK03-A","F-AK03-B"),("64","F-HA03-A","F-HA03-B"),("57","F-NA03-A","F-NA03-B"),("58","F-RE03-A","F-RE03-B"),("56","SHO-03A","SHO-03B")):
        for a,b in itertools.product(("A1","A2","A3"),("B1","B2","B3")):
            history={f"fte:{p}:complete":True,af:a,bf:b}
            histories.append(walk(g,tasks,base,history)[0])
    for met in (False,True):
        for a,b in itertools.product(("A1","A2","A3"),("B1","B2","B3")):
            history={"fte:34:complete":met,"fte:87:complete":False,"F-HA01-A":a,"F-HA01-B":b}
            # If no first meeting exists, avoid a synthetic repeat02/03; route
            # the independent Nana afternoon fixture in this structural test.
            choices={**base,"I4-C01":"B","4-afternoon13":"57"}
            histories.append(walk(g,tasks,choices,history)[0])
    blocked=compile_chapter_four(sources,{},copy.deepcopy(tasks))
    btrace,bflags,_,_=walk(blocked,tasks,base,until_gate=True)
    assert btrace[-1]["type"] == "gate" and not bflags.get("fte:62:complete",False)

    present=set()
    def collect(v):
        if isinstance(v,dict):
            if v.get("type")=="say" and "source"in v:present.add((v['source']['file'],v['source']['line']))
            for x in v.values():collect(x)
        elif isinstance(v,list):
            for x in v:collect(x)
    collect(nodes);collect([t for t in tasks['tasks'].values() if t.get('chapter')=='4'])
    for s in sources.values():
        if re_main(s.prefix):
            for event in s.paragraphs():
                if event['type']=='say':assert (s.name,event['source']['line']) in present,(s.name,event['source']['line'])
    remaining=[t['id'] for t in tasks['tasks'].values() if t.get('chapter')=='4' and not t['runtimeReady']]
    print(json.dumps({'staticChecks':'passed','graphNodesWithSyntheticMeetingFixtures':len(nodes),'mandatoryChoicePairScenariosIncludingBothLieOutcomes':2*len(scenarios),'personalHistoryScenarios':len(histories),'taskContracts':len(input_ids),'knowledgeCards':len(owned),'pinnedSources':len(route_source_hashes(sources)),'taskBindingGates':remaining,'nativeExecuted':False,'structuralTaskSuccessAssumedOnlyForReturnInspection':True,'storyOrGameOutputsWritten':False},ensure_ascii=False))


def re_main(prefix):
    return prefix in {"14a"} | {"14a"+str(i) for i in range(2,14)} | {"14b"+str(i) for i in range(1,5)} | {"14c"+str(i) for i in range(1,4)} | {"14d"}


if __name__=='__main__':main()
