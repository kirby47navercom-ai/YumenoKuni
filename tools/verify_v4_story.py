#!/usr/bin/env python3
"""Verify source-faithful V4 control flow, not play time or visual quality."""
from __future__ import annotations

from copy import deepcopy
import itertools
import hashlib
import json
from pathlib import Path
import tempfile
import sys

import build_v4_story as v4


def walk(graph, choices, flags=None, stop_at=None, task_success=False):
    flags = dict(flags or {})
    node_id = graph["entry"]
    events = []
    seen = set()
    stack = []
    for _ in range(len(graph["nodes"]) * 3 + 10):
        state = (node_id, tuple(sorted(flags.items())), tuple(f["returnTo"] for f in stack))
        if state in seen:
            raise AssertionError(f"unintended cycle {node_id}")
        seen.add(state)
        node = graph["nodes"][node_id]
        events.append(node)
        flags.update(node.get("set", {}))
        if node_id == stop_at:
            return events, flags
        kind = node["type"]
        if kind == "return" and stack:
            frame = stack.pop()
            flags.update(frame.get("onReturnSet", {}))
            node_id = frame["returnTo"]
            continue
        if kind in ("end", "return", "gate"):
            return events, flags
        if kind == "menu":
            selected = next(o for o in node["options"] if o["id"] == choices[node_id])
            flags.update(selected.get("set", {}))
            node_id = selected["to"]
        elif kind == "branch":
            node_id = next((c["to"] for c in node["cases"] if flags.get(c["flag"]) == c["equals"]), node["default"])
        elif kind == "call":
            stack.append(node)
            node_id = node["target"]
        elif kind == "investigate":
            pending = [s for s in node["spots"] if not flags.get(s["completionFlag"])]
            if pending:
                spot = pending[0]
                stack.append({"returnTo": spot.get("returnTo", node["id"]), "onReturnSet": spot.get("onReturnSet", {})})
                node_id = spot["entry"]
            else:
                assert all(flags.get("card:" + c) for c in node.get("requiredCards", [])), "unacquired required evidence"
                node_id = node["next"]
        elif kind == "evidence":
            if node.get("revision"):
                assert flags.get("card:" + node["evidenceId"]), "evidence revised before acquisition"
            flags["card:" + node["evidenceId"]] = True
            node_id = node["next"]
        elif kind == "task":
            if not task_success:
                return events, flags
            # Explicit structural success model only. This does not perform
            # player input or certify an unresolved image/region binding.
            if node.get("outcomes"):
                selected = node["outcomes"][choices.get(node["id"], "A")]
                flags.update(selected.get("sets", {}))
                node_id = selected["to"]
            else:
                node_id = node["success"]
        else:
            node_id = node["next"]
    raise AssertionError("route exceeded acyclic bound")


def references(graph):
    for node in graph["nodes"].values():
        yield from (node[k] for k in ("next", "default", "target", "returnTo") if k in node)
        yield from (o["to"] for o in node.get("options", []))
        yield from (o["to"] for o in node.get("cases", []))
        yield from (o["entry"] for o in node.get("spots", []))
        yield from (o["returnTo"] for o in node.get("spots", []) if "returnTo" in o)
        yield from (o["to"] for o in node.get("outcomes", {}).values())


def verify(directory: Path):
    checks = []

    def check(name, truth):
        if not truth:
            raise AssertionError(name)
        checks.append(name)

    manifest = v4.load(directory / "manifest.json")
    check("Unfinished campaign is explicitly blocked; no legacy fallback", not manifest["campaignReady"] and len(manifest["remaining"]) == 6)
    for entry in manifest["sourceFiles"]:
        actual = (v4.SRC / entry["file"]).read_text(encoding="utf-8-sig")
        check(f"Source hash {entry['file']}", v4.sha(actual) == entry["sha256"])
    for chapter,next_chapter in zip(('P','1','2','3','4','5'),('1','2','3','4','5','6')):
        graph=v4.load(directory/f'chapters/{chapter}.json')
        ends=[n for n in graph['nodes'].values() if n['type']=='end']
        check(f"Actual chapter {chapter} end exists",bool(ends))
        check(f"Native chapter {chapter} transition is explicit",all(n.get('chapterComplete') is True and n.get('nextChapter')==next_chapter for n in ends))
    graphs = [v4.load(directory / "chapters/P.json")]
    graphs.extend(v4.load(p) for p in sorted((directory / "freetime").glob("*.json")) if p.name!='index.json')
    check("All reviewed meetings are generated", len(graphs) == 1+len(manifest['authoredFreetimeMeetings']))
    paths = 0
    for graph in graphs:
        nodes = graph["nodes"]
        check(f"Graph entry exists {graph.get('sourceFile', graph['chapter'])}", graph["entry"] in nodes)
        check(f"Graph has no dangling edge {graph.get('sourceFile', graph['chapter'])}", all(target in nodes for target in references(graph)))
        check(f"Only actors speak {graph.get('sourceFile', graph['chapter'])}", all((n["speaker"] in v4.SPEAKERS or graph.get('chapter')=='P' and n['speaker']=='???' and n['actor'] in v4.SPEAKERS.values() and not n.get('mono')) and "direction" not in n and not n["text"].startswith(">") for n in nodes.values() if n["type"] == "say"))
        check(f"Author directions never dialogue {graph.get('sourceFile', graph['chapter'])}", all("text" not in n and "speaker" not in n for n in nodes.values() if n["type"] == "stage"))
        menus = [n for n in nodes.values() if n["type"] == "menu"]
        check(f"Distinct authored choices remain {graph.get('sourceFile', graph['chapter'])}", len(menus) == graph.get('authoredMenuCount',3 if graph.get('sourceFile','').startswith('26_') else 2))
        seen_paths=set()
        for combination in itertools.product(*(m["options"] for m in menus)):
            selected = {m["id"]: o["id"] for m, o in zip(menus, combination)}
            history={key:values[0] for key,values in graph.get('requiresPriorFlags',{}).items()}
            for key,rule in graph.get('conditionalPriorFlags',{}).items():
                if all(history.get(k) in v if isinstance(v,list) else history.get(k)==v for k,v in rule['when'].items()):history[key]=rule['values'][0]
            events, flags = walk(graph, selected, history)
            route=tuple(e['id'] for e in events)
            if route in seen_paths:continue
            seen_paths.add(route)
            check(f"Path ends without gate {graph.get('sourceFile', graph['chapter'])} {tuple(selected.values())}", events[-1]["type"] in ("end", "return"))
            for menu, chosen in zip(menus, combination):
                for other in menu["options"]:
                    if other["id"] != chosen["id"] and other["to"] != chosen["to"]:
                        check(f"No other option entered {menu['id']}:{chosen['id']}->{other['id']} path {paths}", other["to"] not in {e["id"] for e in events})
                # Accepted choices may share physical work before their own
                # responses. Verify the flag dispatch, rather than calling
                # entry into that common work an entry into the other choice.
                shared=[o for o in menu['options'] if o['id']!=chosen['id'] and o['to']==chosen['to']]
                if shared and menu['id'] in {e['id'] for e in events}:
                    choice_flags=[k for k,v in chosen.get('set',{}).items() if v==chosen['id'] and all(o.get('set',{}).get(k)==o['id'] for o in shared)]
                    check(f"Shared work retains choice flag {menu['id']}",bool(choice_flags))
                    dispatch=next((e for e in events if e['type']=='branch' and any(all(any(c['flag']==k and c['equals']==o['id'] for c in e['cases']) for o in [chosen,*shared]) for k in choice_flags)),None)
                    check(f"Shared work dispatches distinct responses {menu['id']}",dispatch is not None)
                    flag=next(k for k in choice_flags if all(any(c['flag']==k and c['equals']==o['id'] for c in dispatch['cases']) for o in [chosen,*shared]))
                    destinations={c['equals']:c['to'] for c in dispatch['cases'] if c['flag']==flag}
                    visited={e['id'] for e in events}
                    check(f"Chosen response after shared work {menu['id']}:{chosen['id']}",destinations[chosen['id']] in visited)
                    for other in shared:
                        check(f"Other response excluded after shared work {menu['id']}:{other['id']}",destinations[other['id']] not in visited)
            if graph["chapter"] == "P":
                check(f"Both real readable documents appear path {paths}", len([e for e in events if e["type"] == "document"]) == 2)
                # Delayed callback must not put Haruka inside the office in B.
                a_call = any(e["type"] == "say" and e.get("text") == "응.그 말을 하면 되지." for e in events)
                b_call = any(e["type"] == "say" and e.get("text") == "관리실 말고 어디 갔어?" for e in events)
                check(f"Office companion callback matches selection path {paths}", a_call == (flags["P-C01"] == "A") and b_call == (flags["P-C01"] == "B"))
            paths += 1
    first_day = v4.load(directory / "chapters/1.json")
    first_day = deepcopy(first_day)
    first_day["nodes"]["v4:1:11c1:pending"] = {"id": "v4:1:11c1:pending", "type": "gate", "reason": "Daily-life verification boundary; trial is tested separately below."}
    check("First day call edges resolve locally", all(target in first_day["nodes"] for target in references(first_day)))
    first_day_paths = 0
    menus = {n["id"]: n for n in first_day["nodes"].values() if n["type"] == "menu"}
    base_choices = {ident: "REST" if menu.get("selectionRole") == "freetime" else menu["options"][0]["id"] for ident, menu in menus.items()}
    base_choices.update({"v4:1:F1-A": "REST", "v4:1:F1-B": "REST"})
    main_choice_ids = ("v4:11a:1-C01:menu", "v4:101:1-C06:menu", "v4:65:1-C05:menu", "v4:120:1-C08:menu")
    for prior in ("A", "B"):
        for values in itertools.product("ABC", repeat=4):
            selected = {**base_choices, **dict(zip(main_choice_ids, values))}
            events, flags = walk(first_day, selected, {"P-C02": prior})
            check(f"Daily life and investigation {prior} {values} stop before uncompiled trial", events[-1]["id"] == "v4:1:11c1:pending")
            check(f"First day {prior} {values} preserves actual main decisions", all(flags[k] == v for k, v in zip(("1-C01", "1-C06", "1-C05", "1-C08"), values)))
            files = {e.get("source", {}).get("file", "").split("_", 1)[0] for e in events}
            check(f"First day all mandatory insertions {prior} {values}", {"11a", "91", "101", "135", "65", "120", "86"} <= files)
            check(f"No unplayed AI meeting callback {prior} {values}", not any(e["id"].startswith("v4:65:") and e.get("source", {}).get("line", 0) in range(69, 106) for e in events))
            check(f"Later 101 callback stays on actual map choice {prior} {values}", sum(e.get("type") == "say" and e.get("source", {}).get("file", "").startswith("101_") and e.get("source", {}).get("line", 0) in (427, 437, 447) for e in events) <= 1)
            first_day_paths += 1
    for a, b in itertools.product(("A1", "A2", "A3"), ("B1", "B2", "B3")):
        selected = {**base_choices, "v4:1:F1-A": "25", "v4:25:F-AI01-A:menu": a, "v4:25:F-AI01-B:menu": b}
        events, flags = walk(first_day, selected, {"P-C02": "A"})
        check(f"AI call correctly returns {a} {b}", events[-1]["id"] == "v4:1:11c1:pending" and flags["fte:25:complete"] and flags["window:F1-A:completed"])
        callback_lines = [e.get("source", {}).get("line", 0) for e in events if e.get("source", {}).get("file", "").startswith("65_")]
        ranges = {"A1": range(70, 81), "A2": range(82, 91), "A3": range(92, 105)}
        check(f"AI only actual earlier choice is remembered {a} {b}", any(n in ranges[a] for n in callback_lines) and not any(n in ranges[other] for other in ranges if other != a for n in callback_lines))
        first_day_paths += 1
    # An unsupported meeting is an explicit boundary, not a fake completed
    # optional scene that later creates false memory or material possession.
    missing_events, missing_flags = walk(first_day, {**base_choices, "v4:1:F1-B": "46"}, {"P-C02": "A"})
    check("Missing actual first meeting fails closed without followup completion", missing_events[-1]["type"] == "gate" and "fte:46:complete" not in missing_flags)
    second_day_paths = 0
    second_day_choices = ("v4:154:1-C14:menu", "v4:11a2:1-C02:menu", "v4:123:1-C09:menu", "v4:176:W1-C02:menu", "v4:108:1-C07:menu")
    for combinations in itertools.product(*(menus[k]["options"] for k in second_day_choices)):
        selected = {**base_choices, **{k: o["id"] for k, o in zip(second_day_choices, combinations)}}
        events, flags = walk(first_day, selected, {"P-C02": "B"})
        check(f"Second-day distinct decisions complete {second_day_paths}", events[-1]["id"] == "v4:1:11c1:pending")
        files = {e.get("source", {}).get("file", "").split("_", 1)[0] for e in events}
        check(f"Second-day all required insertions {second_day_paths}", {"154", "92", "123", "78", "176", "108", "170"} <= files)
        # Current room exchange and its actual participant-specific dialogue
        # follow the selected branch, rather than both sets of moving boxes.
        current = {e.get("source", {}).get("line", 0) for e in events if e.get("source", {}).get("file", "").startswith("11a2_")}
        expected = range(403, 418) if flags["1-C02"] == "A" else range(419, 434)
        excluded = range(419, 434) if flags["1-C02"] == "A" else range(403, 418)
        check(f"Room state branch exclusive {second_day_paths}", any(i in expected for i in current) and not any(i in excluded for i in current))
        second_day_paths += 1
    third_day_paths = 0
    for representative, copy, search in itertools.product(menus["v4:11a3:1-C03:representative"]["options"], "ABC", "AB"):
        selected = {**base_choices, "v4:11a3:1-C03:representative": representative["id"], "v4:11a3:1-C04:menu": copy, "v4:11b:I-C01": search}
        events, flags = walk(first_day, selected, {"P-C02": "A"})
        check(f"Discovery/investigation path completes {third_day_paths}", events[-1]["id"] == "v4:1:11c1:pending")
        check(f"Representative ballot stays distinct {third_day_paths}", flags["1-C03"] == representative["label"] and menus["v4:11a3:1-C03:representative"]["fixedResult"] == "kaede" and not menus["v4:11a3:1-C03:representative"]["finalVote"])
        check(f"All actual evidence acquired {third_day_paths}", all(flags.get("card:" + c) for c in first_day["evidenceCatalog"]))
        visited = [e.get("source", {}).get("line", 0) for e in events if e.get("source", {}).get("file", "").startswith("11b_")]
        check(f"Room search does not occur on refusal {third_day_paths}", (711 in visited) == (search == "A") and (763 in visited) == (search == "B"))
        card_events = [e for e in events if e["type"] == "evidence"]
        check(f"Revisions not duplicate acquisition {third_day_paths}", sum(e["evidenceId"] == "v4:E1-10" and not e.get("revision") for e in card_events) == 1 and sum(e["evidenceId"] == "v4:E1-10" and e.get("revision") for e in card_events) == 1)
        third_day_paths += 1
    tasks = v4.load(directory / "tasks.json")["tasks"]
    ledger = v4.load(v4.SRC / "qa_2026-10-29/trial_input_reedit.json")
    check("Only approved and explicitly compiled baseline task IDs imported", set(tasks) == {e["id"] for e in ledger["entries"]} | set(manifest["tasks"]["compiledBaseline"]))
    for task in tasks.values():
        name = task["id"]
        check(f"Wrong branch isolated {name}", not ({e["id"] for e in task["wrong"]} & {e["id"] for e in task["intro"] + task["success"] + task.get("lines", [])}))
        check(f"Cancellation cannot solve {name}", task["retry"]["cancellationIsSuccess"] is False)
        if task["return"].get("taskId"):
            check(f"Success next exists {name}", task["return"]["taskId"] in tasks)
        if "targets" in task:
            check(f"Explicit marked targets preserved {name}", len(task["targets"]) == (2 if name in ("T2-LIE-01","T4-LIE-01","T5-LIE-01","T6-LIE-01") else 1))
            check(f"Debate not duplicated as intro {name}", not ({e["id"] for e in task["intro"]} & {e["id"] for e in task["lines"]}))
        if task["kind"] == "person":
            check(f"Person selection is separate from vote {name}", not task["finalVote"] and task["answer"] in task["candidates"] and task["deadCandidatesSelectable"])
        if task["kind"] == "choice":
            check(f"Answer really exists {name}", task["answer"] in {o["id"] for o in task["options"]})
        if task["kind"] == "reasoning":
            check(f"All authored links preserved {name}", (len(task["questions"]) >= 1 if task.get("sourceKind") == "BASELINE" else len(task["questions"]) == 3) and all(q["answer"] in {o["id"] for o in q["options"]} for q in task["questions"]))
        if task["kind"] == "anagram":
            check(f"Single-glyph arrival native rule {name}", task["mechanic"]["selectGlyphCount"] == 1 and "pairSequence" not in task)
        if task["kind"] in ("spot", "mindmine"):
            if task["runtimeReady"]:
                proof=task.get('pictureProvenance',{})
                source_diagram=(proof.get('sourceBound') is True and proof.get('contract') and (v4.ROOT/proof['contract']).is_file() and proof.get('imageSha256')==hashlib.sha256((v4.ROOT/task['image']).read_bytes()).hexdigest())
                reviewed=name in ("T1-MM-01","T1-SPOT-A01","T1-MM-A03") or (proof.get('newEvidence') is False and (source_diagram or (proof.get('sourceProof') and proof.get('visualReview'))))
                check(f"Actual pictured clue binding {name}", reviewed and task["answerRegionId"] in {r["id"] for r in task["regions"] if r["correct"]} and (v4.ROOT/task["image"]).is_file())
            else:
                check(f"No fabricated clue coordinates {name}", any(b["kind"] == "forensicImageRegions" for b in task["bindings"]))
        check(f"Readiness agrees with required binding {name}", task["runtimeReady"] == (not task["bindings"]))
    trial_graph = v4.load(directory / "chapters/1.json")
    trial_graph["entry"] = "v4:1:11c1:pending"
    complete_graph = deepcopy(trial_graph)
    trial_graph["nodes"]["v4:1:11c2:pending"] = {"id": "v4:1:11c2:pending", "type": "gate", "reason": "First-half verification boundary."}
    trial_choice_ids = ("v4:66:T1-C04:menu", "v4:93:T1-C05:menu", "v4:11c1:T1-C02:menu")
    trial_paths = 0
    for choices in itertools.product("ABC", repeat=3):
        for recalled in "ABC":
            selected = dict(zip(trial_choice_ids, choices))
            events, flags = walk(trial_graph, selected, {"1-C05": recalled, "1-C09": recalled}, task_success=True)
            check(f"First-half trial structural success route {choices} {recalled}", events[-1]["id"] == "v4:1:11c2:pending")
            task_ids = [e["taskId"] for e in events if e["type"] == "task"]
            check(f"Four exact baseline inputs retained {choices} {recalled}", {"T1-NS-T05e", "T1-MM-01", "T1-SD-01", "T1-PD-01"} <= set(task_ids))
            check(f"No wrong reaction in success path {choices} {recalled}", not ({e["id"] for e in events} & {e["id"] for t in tasks.values() for e in t["wrong"]}))
            trial_paths += 1
    boundary, _ = walk(trial_graph, dict(zip(trial_choice_ids, "ABC")), {"1-C05": "A", "1-C09": "A"})
    check("Ordinary static walk never auto-solves an input task", boundary[-1]["type"] == "task")
    late_paths = 0
    for rep, privacy, paper, lie in itertools.product(("카에데", "타이가", "켄", "기권"), "ABC", "ABC", "AB"):
        selected={**dict(zip(trial_choice_ids, ("A", "B", privacy))), "v4:11c2:T1-C03:menu":paper,"v4:input:T1-LIE-01":lie}
        events, flags=walk(complete_graph,selected,{"1-C03":rep,"1-C05":"A","1-C07":"B","1-C09":"C","I-C01":"B","W1-C02":"A"},task_success=True)
        check(f"Full case structural correct-input path {late_paths}",events[-1]["id"]=="v4:1:end")
        locations={(e.get('source',{}).get('file','').split('_',1)[0],e.get('source',{}).get('line',0)) for e in events}
        check(f"Lie history exists only after intentional route {late_paths}",bool(flags.get('T1-LIE-B'))==(lie=='B') and (('11d',454) in locations)==(lie=='B'))
        check(f"Absent optional store memory is never created {late_paths}",('11d',641) not in locations)
        check(f"Death state changes after actual announcement {late_paths}",flags.get('public:taiga:death-confirmed') is True)
        check(f"Real final vote distinct from representative {late_paths}",sum(e.get('taskId')=='T1-VOTE-01' for e in events)==1 and tasks['T1-VOTE-01']['finalVote'])
        late_paths+=1
    check("Actual reconstruction has six separately answered slots",len(tasks['T1-MG-01']['slots'])==6 and ''.join(s['answer'] for s in tasks['T1-MG-01']['slots'])=='BACBAC')
    check("Lie changes utterance, not source evidence",not tasks['T1-LIE-01']['transformation']['changesHistoricalFacts'])
    index = v4.load(directory / "blocks.json")
    check("Source index cannot be mistaken for linear executable scenes", all(not b["executable"] for b in index["blocks"].values()))
    return {"schemaVersion": 1, "passed": True, "checks": len(checks), "paths": paths, "firstDayChoicePaths": first_day_paths, "secondDayChoicePaths": second_day_paths, "discoveryInvestigationPaths": third_day_paths, "trialFirstHalfStructuralPaths": trial_paths, "trialThroughAftermathStructuralPaths":late_paths, "taskCount": len(tasks), "runtimeTested": False, "campaignReady": False, "note": "Static semantic routing only. Trial paths explicitly model task success, including unresolved regions; ordinary walks stop at the first input. Not gameplay, timing certification, or art acceptance."}


if __name__ == "__main__":
    result = verify(v4.OUT)
    v4.dump(v4.OUT / "verification.json", result)
    print(json.dumps(result, ensure_ascii=False))
