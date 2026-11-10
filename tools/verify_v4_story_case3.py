"""Read-only chapter-three graph checks; never a claim of native gameplay.

The control-flow simulator assumes successful task input solely to inspect its
authored continuation. It does not waive runtime bindings or count play time.
Freetime fixtures below are synthetic return frames used only in these checks.
"""
from __future__ import annotations

import copy
import itertools
import json
from collections import Counter
from pathlib import Path

from build_v4_story import ROOT, Source
from v4_story_case3 import compile_chapter_three, route_source_hashes


CHOICES = ("3-C01", "3-C03", "3-C04", "W3-C15", "3-C02", "I3-C02", "I3-C01", "T3-C01")


def compile_fixture():
    sources = {p.name: Source(p) for p in (ROOT / "docs/design/rewrite_v4").glob("*.md")}
    tasks = json.loads((ROOT / "data/v4_story/tasks.json").read_text(encoding="utf-8-sig"))
    fixtures = {p: {"entry": "test:fte:" + p, "nodes": {"test:fte:" + p: {"id": "test:fte:" + p, "type": "return"}}} for p in ("55", "58", "60", "61")}
    return sources, tasks, compile_chapter_three(sources, fixtures, tasks)


def walk(graph, tasks, choices, history=None, stop_at=None):
    flags = {"fte:" + p + ":complete": True for p in ("21", "36", "27", "45", "28", "47", "30", "48")}
    flags.update({"KOTO-03A": "A1", "KOTO-03B": "B1", "F-KE03-A": "A1", "F-KE03-B": "B1", "F-RI03-A": "A2", "F-RI03-B": "B1"})
    flags.update(history or {})
    node = graph["entry"]
    stack, seen, acquired, taskids, trace = [], set(), set(), [], []
    while True:
        n = graph["nodes"][node]
        key = (node, tuple((q[0], tuple(sorted(q[1].items()))) for q in stack))
        if key in seen:
            raise AssertionError("Control-flow loop " + node)
        seen.add(key)
        trace.append(n)
        if stop_at and stop_at(n):
            return trace, flags, acquired, taskids
        flags.update(n.get("set", {}))
        kind = n["type"]
        if kind == "branch":
            node = next((c["to"] for c in n["cases"] if flags.get(c["flag"]) == c["equals"]), n["default"])
        elif kind == "menu":
            eligible = [o for o in n["options"] if all(flags.get(k, False) == v for k, v in o.get("requires", {}).items())]
            selection = next((choices.get(flag) for flag in CHOICES if any(flag in o.get("set", {}) for o in eligible)), None)
            if n.get("window") == "F3":
                selection = choices.get("F3", "55")
            elif n.get('selectionRole')=='freetime':
                selection=choices.get(n['window'],'REST')
            selected = next((o for o in eligible if o["id"] == selection), None)
            assert selected, (node, selection, flags)
            flags.update(selected.get("set", {}))
            node = selected["to"]
        elif kind == "call":
            stack.append((n["returnTo"], n.get("onReturnSet", {})))
            node = n["target"]
        elif kind == "return":
            node, after = stack.pop()
            flags.update(after)
        elif kind == "investigate":
            pending = [s for s in n["spots"] if not flags.get(s["completionFlag"], False)]
            if pending:
                spot = pending[0]
                # Re-entering a completed hub is intentional, not a loop.
                seen.remove(key)
                stack.append((spot["returnTo"], spot["onReturnSet"]))
                node = spot["entry"]
            else:
                node = n["next"]
        elif kind == "task":
            task = tasks["tasks"][n["taskId"]]
            assert set(task.get("requiresEvidence", [])) <= acquired, n["taskId"] + " precedes evidence"
            taskids.append(n["taskId"])
            # Structural edge inspection only: no native input/ready assertion.
            node = n["success"]
        elif kind == "evidence":
            acquired.add(n["evidenceId"])
            node = n["next"]
        elif kind == "gate":
            raise AssertionError("Unexpected structural gate: " + n["reason"])
        elif kind == "end":
            assert not stack
            return trace, flags, acquired, taskids
        else:
            node = n["next"]


def check_history(trace, choices):
    # Every alternative in the source is checked at its precise line range.
    alternatives = {
        "83": [(5, 106, "3-C01", "A"), (109, 206, "3-C01", "B"), (209, 314, "3-C01", "C")],
        "98": [(90, 142, "3-C03", "A"), (144, 198, "3-C03", "B"), (200, 246, "3-C03", "C"), (254, 260, "3-C03", "A"), (262, 268, "3-C03", "B"), (270, 286, "3-C03", "C"), (472, 490, "3-C03", "A"), (492, 510, "3-C03", "B"), (512, 528, "3-C03", "C")],
        "156": [(108, 172, "3-C04", "A"), (174, 240, "3-C04", "B"), (242, 286, "3-C04", "C"), (290, 292, "3-C04", "AB"), (294, 296, "3-C04", "C"), (306, 320, "3-C04", "A"), (322, 334, "3-C04", "B"), (336, 358, "3-C04", "C")],
        "180": [(170, 218, "W3-C15", "A"), (220, 258, "W3-C15", "B"), (260, 306, "W3-C15", "C"), (311, 311, "W3-C15", "A"), (313, 313, "W3-C15", "B"), (315, 315, "W3-C15", "C"), (330, 336, "W3-C15", "B"), (338, 342, "W3-C15", "AC"), (352, 356, "W3-C15", "A"), (358, 362, "W3-C15", "B"), (364, 368, "W3-C15", "C")],
        "70": [(78, 112, "I3-C02", "A"), (114, 158, "I3-C02", "B"), (160, 196, "I3-C02", "C")],
        "13b3": [(246, 256, "I3-C01", "A"), (258, 266, "I3-C01", "B"), (268, 280, "I3-C01", "C")],
        "102": [(104, 116, "T3-C01", "A"), (118, 134, "T3-C01", "B"), (136, 150, "T3-C01", "C"), (276, 284, "T3-C01", "A"), (286, 294, "T3-C01", "B"), (296, 304, "T3-C01", "C")],
        "13d": [(226, 234, "I3-C02", "B"), (270, 280, "I3-C02", "A"), (564, 576, "I3-C02", "C")],
    }
    for n in trace:
        ref = n.get("source", {})
        prefix, line = ref.get("file", "").split("_", 1)[0], ref.get("line", 0)
        for first, last, flag, allowed in alternatives.get(prefix, []):
            if first <= line <= last:
                assert choices[flag] in allowed, (prefix, line, flag, choices[flag], allowed)


def main():
    sources, tasks, graph = compile_fixture()
    nodes = graph["nodes"]
    for n in nodes.values():
        for field in ("next", "success", "default", "target", "returnTo"):
            if field in n:
                assert n[field] in nodes, (n["id"], field, n[field])
        for child in n.get("cases", []) + n.get("options", []):
            assert child["to"] in nodes
        if n["type"] == "task":
            assert n["taskId"] in tasks["tasks"]
            assert len(n["seats"]) == 16 and len(n["trialDead"]) == 6 and "ken" not in n["trialDead"]
        if n.get("type") == "say" and "켄의몸" in n.get("delivery", ""):
            assert n["actor"] == "ken" and n["speaker"] in ("켄의 몸", "소라(켄의 몸)")
        for spot in n.get("spots", []):
            assert not spot["geometryReady"] and spot["target_id"] is None
    normal = {k: "A" for k in CHOICES}
    # This is ordinary paper inside an envelope, not Mio's protected record.
    # Task metadata must not contradict the evidence players actually acquire.
    phrase_task=tasks['tasks']['T3-EVIDENCE-A01']
    assert phrase_task['answerEvidenceId']=='v4:3:knowledge:private-phrase'
    assert '비공개 시험 문장 원본' in phrase_task['candidatesDescription']
    for field in ('answerScope','selectedEvidenceLabel'):
        assert '보통 종이' in phrase_task[field] and '보호 마법 기록이 아니' in phrase_task[field], field
    base, flags, owned, taskids = walk(graph, tasks, normal, {"2-C05": "A"})
    assert len(taskids) == len(set(taskids)) == 39
    assert len(owned) == len(graph["evidenceCatalog"]) == 22
    assert flags["3:first-discovery"] and flags["3:second-discovery"] and not flags["3:second-body-alive"]
    assert flags["3:identity:confirmed"]
    assert flags["3:livingBodies"] == 9
    assert flags["fte:55:complete"] and not flags.get("fte:60:complete", False)
    assert taskids.index("T3-LIE-01") < taskids.index("T3-PERSON-A02") < taskids.index("T3-CULPRIT-A01") < taskids.index("T3-VOTE-01")
    personal=[n for n in nodes.values() if n.get('selectionRole')=='freetime']
    assert {n['window'] for n in personal}=={'F3','F3-after-lunch'}
    later=next(n for n in personal if n['window']=='F3-after-lunch')
    assert next(o for o in later['options'] if o['id']=='56')['requires']=={'fte:23:complete':True,'fte:41:complete':True}
    assert next(o for o in later['options'] if o['id']=='59')['requires']=={'fte:24:complete':True,'fte:42:complete':True}
    no_personal={**normal,'F3':'REST','F3-after-lunch':'REST'}
    trace,no_flags,_,_=walk(graph,tasks,no_personal,{'2-C05':'A',**{'fte:'+p+':complete':False for p in ('21','36','27','45','28','47','30','48')}})
    assert not any(no_flags.get('fte:'+p+':complete') for p in ('55','58','60','61','56','59'))
    assert trace[-1]['type']=='end'
    assert not any(n.get("source", {}).get("file", "").startswith("13c2_") and n.get("source", {}).get("line") == 41 for n in base)
    # Baseline plus every pair of mandatory choices, all three alternatives.
    # This is 253 branch interactions, not an exhaustive narrative playthrough.
    scenarios = [normal]
    for a, b in itertools.combinations(CHOICES, 2):
        for x, y in itertools.product("ABC", repeat=2):
            scenarios.append({**normal, a: x, b: y})
    for choices in scenarios:
        trace, _, _, tids = walk(graph, tasks, choices, {"2-C05": "B"})
        check_history(trace, choices)
        assert tids == taskids
    # Earned personal-history callbacks: each actual ending, not all at once.
    histories = []
    for p, aflag, bflag in (("55", "KOTO-03A", "KOTO-03B"), ("60", "F-KE03-A", "F-KE03-B"), ("61", "F-RI03-A", "F-RI03-B")):
        for a, b in itertools.product(("A1", "A2", "A3"), ("B1", "B2", "B3")):
            history = {"2-C05": "A", aflag: a, bflag: b}
            trace, state, _, _ = walk(graph, tasks, {**normal, "F3": p}, history)
            assert state[f"fte:{p}:complete"]
            histories.append(trace)
    for a in ("A1", "A2", "A3"):
        for b in ("B1", "B2", "B3") if a != "A3" else (None,):
            history = {"2-C05": "A", "fte:59:complete": True, "SORA-03A": a}
            if b:
                history["SORA-03B-A" if a == "A1" else "SORA-03B-B"] = b
            histories.append(walk(graph, tasks, normal, history)[0])
    for b in ("B1", "B2", "B3"):
        histories.append(walk(graph, tasks, normal, {"2-C05": "A", "fte:63:complete": True, "F-SA03-B": b})[0])
    for first, second in itertools.product((False, True), repeat=2):
        trace = walk(graph, tasks, normal, {"2-C05": "A", "T1-LIE-B": first, "T2-LIE-B": second})[0]
        assert any(n.get("source", {}).get("file", "").startswith("169_") for n in trace) == second
        assert any(n.get("source", {}).get("file", "").startswith("13c2_") and 28 <= n["source"]["line"] <= 32 for n in trace) == first
        histories.append(trace)
    for intro in (None, "24", "89"):
        history = {"2-C05": "A", **({f"fte:{intro}:complete": True} if intro else {})}
        trace = walk(graph, tasks, normal, history)[0]
        assert any(n.get("source", {}).get("file", "").startswith("13c3_") and 320 <= n["source"]["line"] <= 354 for n in trace) == (intro is not None)
        histories.append(trace)
    # Uncompiled meeting must actually stop, not silently award completion.
    blocked = compile_chapter_three(sources, {}, copy.deepcopy(tasks))
    trace, state, _, _ = walk(blocked, tasks, normal, {"2-C05": "A"}, lambda n: n["type"] == "gate")
    assert trace[-1]["type"] == "gate" and not state.get("fte:55:complete", False)
    # All main spoken lines survive either in graph or conditional task script.
    present = set()
    def collect(value):
        if isinstance(value, dict):
            if value.get("type") == "say" and "source" in value:
                present.add((value["source"]["file"], value["source"]["line"]))
            for q in value.values(): collect(q)
        elif isinstance(value, list):
            for q in value: collect(q)
    collect(nodes)
    collect([t for t in tasks["tasks"].values() if t.get("chapter") == "3"])
    for s in sources.values():
        if s.prefix in {"13a", "13a2", "13a3", "13a4", "13a5", "13a6", "13a7", "13a8", "13a9", "13a10", "13a11", "13a12", "13b1", "13b2", "13b3", "13b4", "13c1", "13c2", "13c3", "13d"}:
            for event in s.paragraphs():
                if event["type"] == "say":
                    assert (s.name, event["source"]["line"]) in present, (s.name, event["source"]["line"])
    remaining = [t["id"] for t in tasks["tasks"].values() if t.get("chapter") == "3" and not t["runtimeReady"]]
    print(json.dumps({"staticChecks": "passed", "mainGraphNodesWithSyntheticFreetimeFixture": len(nodes), "mandatoryChoicePairScenarios": len(scenarios), "personalHistoryScenarios": len(histories), "authoredTaskContracts": len(taskids), "acquiredKnowledgeCards": len(owned), "pinnedSourceFiles": len(route_source_hashes(sources)), "taskBindingGates": remaining, "uncompiledSelectedFreetimeGateVerified": True, "nativeExecuted": False, "tasksAssumedSuccessfulOnlyForStructuralReturnInspection": True, "storyOrGameOutputsWritten": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
