"""Static and synthetic policy checks. Never launches a player or original game."""
from __future__ import annotations
import copy
import json
from pathlib import Path
from v4_presentation import (ROOT, SCRIPT_ACTIONS, PresentationState, build_contract,
                             score_v4, score_graph_v4, score_trials_v4, score_tasks_v4, scene_music, validate_contract)


def verify():
    contract = build_contract()
    cues = json.loads((ROOT / "audio/cues.json").read_text(encoding="utf-8"))
    report = validate_contract(contract, cues)
    checks = []

    def check(label, result):
        checks.append({"case": label, "pass": bool(result)})
        if not result:
            report["errors"].append(label)

    for ch, prefix in enumerate(('189','190','191','192','193','186'), 1):
        block = {'source': {'file': prefix+'_trial.md', 'location': f'T{ch}-Q01'}}
        check('numbered trial insert keeps court bed '+str(ch), scene_music(ch, block)==f'bgm_trial_main_{ch}')
        block['source']['location']='T-'+str(ch)
        check('unnumbered trial section keeps court bed '+str(ch), scene_music(ch, block)==f'bgm_trial_main_{ch}')
        block['kind']='freetime'
        check('explicit freetime keeps priority over source location '+str(ch),scene_music(ch,block)=='bgm_freetime')
    check('non-trial T prefix does not override daily music', scene_music('1',{'source':{'file':'189_any.md','location':'TICKET'}})=='bgm_daily_pastel')

    # Genuine non-sound cases: negation, intention, retrospective dialogue and
    # C4 rescue are all present in the manuscripts and must not reveal a death.
    quiet = {"chapter": "4", "beats": [{"id": "v4:14a13:4-185", "source": {"file": "14a13_a.md", "location": "4-185"}, "events": [
        {"id": "a", "type": "stage", "direction": "대답이 없다. 물속의 몸을 아직 온전히 보지 못한 상태다. 명확한 사망 CG나 발견 방송으로 앞당기지 않는다."},
        {"id": "b", "type": "say", "speaker": "미오", "text": "시체가 발견되었다고 생각했어?!", "emo": "놀람"},
        {"id": "c", "type": "stage", "direction": "미오가 노크하려다 멈춘다."},
        {"id": "d", "type": "gate", "direction": "방송/회상/처형 미해석"},
    ]}]}
    before = copy.deepcopy(quiet["beats"][0]["events"][-1])
    score_v4(quiet)
    check("living rescue / dialogue punctuation / declined knock emit no sound",
          all(not e.get("sfx") and not e.get("presentation", {}).get("actions") for e in quiet["beats"][0]["events"]))
    check("unresolved gate is not converted to presentation", quiet["beats"][0]["events"][-1] == before)
    after = copy.deepcopy(quiet)
    score_v4(quiet)
    check("score is idempotent", quiet == after)
    evidence_graph={"chapter":"1","nodes":{
        "new":{"id":"new","type":"evidence","evidenceId":"v4:E1-01","revision":False},
        "revision":{"id":"revision","type":"evidence","evidenceId":"v4:E1-01","revision":True}}}
    score_graph_v4(evidence_graph)
    check("explicit evidence nodes distinguish acquisition and revision",
          evidence_graph["nodes"]["new"]["presentation"]["actions"] == ["evidence_acquired"]
          and evidence_graph["nodes"]["revision"]["presentation"]["actions"] == ["evidence_revised"])

    state = PresentationState()
    state.music("bgm_daily_pastel")
    state.music("bgm_daily_pastel")
    check("same cue never restarts", state.output == [("music", "bgm_daily_pastel")])
    state.music("jingle_body_1>bgm_tense", {"jingle_body_1": 5})
    state.tick(1)
    state.music("bgm_investigation")
    state.tick(10)
    check("interrupted reveal chain cannot overwrite later investigation", state.cue == "bgm_investigation" and not state.pending)
    state.music("jingle_vote>bgm_trial_truth", {"jingle_vote": 3})
    state.music("@silence")
    state.tick(10)
    check("silence cancels pending jingle and does not resurrect BGM", not state.cue and not state.pending)
    snapshot = state.save()
    state.music("bgm_title")
    state.restore(snapshot)
    check("save/restore preserves explicit silence", not state.cue and state.output == [])

    e = {"id": "real-reveal", "music": "jingle_body_3>bgm_tense", "sfx": ["sfx_shock"],
         "presentation": {"once": "c3-first", "actions": ["body_reveal"]}}
    state.event(e, contract)
    state.event(e, contract)
    snapshot = state.save()
    check("compatibility sfx and action do not double fire", state.output.count(("sfx", "sfx_shock")) == 1)
    state.restore(snapshot)
    check("reload during a jingle restores its bed without false old timer", state.cue == "bgm_tense" and not state.pending and state.remaining == 0)
    state.event(e, contract)
    check("return/reload cannot replay a completed reveal", state.output == [])
    second = copy.deepcopy(e)
    second["id"], second["presentation"]["once"] = "second-reveal", "c3-second"
    state.event(second, contract)
    check("C3 second death is a distinct event after first", state.output.count(("sfx", "sfx_shock")) == 1)
    state.mode_exit()
    check("mode exit removes transient effect", not state.sequence)

    trial = {"stages": [{"kind": k} for k in ("nonstop", "panic", "showdown", "mindmine", "anagram", "reasoning", "scrum", "armament", "climax", "vote", "talk")]}
    score_trials_v4(trial, 2)
    check("all trial modes select mode music and post-vote truth persists",
          all(s.get("music") for s in trial["stages"]) and trial["stages"][-1]["music"] == "bgm_trial_truth")

    index_file = ROOT / "data/v4_story/blocks.json"
    if index_file.is_file():
        blocks = json.loads(index_file.read_text(encoding="utf-8"))["blocks"]
        seen, matched, semantic_before = set(), {}, {}
        action_events = {}
        # The index includes nested copies. Store/source IDs establish unique
        # occurrences; this count must never be presented as runtime frequency.
        for b in blocks.values():
            original = [(e.get("id"), e.get("text"), e.get("direction"), e.get("next"), e.get("options")) for e in b["events"]]
            ch = b.get("chapter") or (b["id"].split(":")[1][1:2] if b["id"].split(":")[1].startswith("1") and len(b["id"].split(":")[1]) > 1 else "P")
            if ch not in "123456":
                ch = "P"
            score_v4({"chapter": ch, "beats": [b]})
            check_equal = original == [(e.get("id"), e.get("text"), e.get("direction"), e.get("next"), e.get("options")) for e in b["events"]]
            if not check_equal:
                report["errors"].append("story semantics modified: " + b["id"])
            for e in b["events"]:
                if e.get("id") in seen:
                    continue
                seen.add(e.get("id"))
                p, src = e.get("presentation", {}), e.get("source", {})
                for action in p.get("actions", []):
                    key = (Path(src.get("file", "")).name.split("_")[0], src.get("location", ""), action)
                    matched[key] = matched.get(key, 0) + 1
                    action_events[e["id"]] = {"source": src, "action": action, "once": p.get("once"), "music": e.get("music")}
        for f, loc, prefix, action, music in SCRIPT_ACTIONS:
            check("authored source action matches exactly once: " + f + ":" + loc + ":" + action,
                  matched.get((f, loc, action)) == 1)
        check("original text/route fields remain unchanged", not any("story semantics modified" in e for e in report["errors"]))
        report["index_coverage"] = {"blocks_including_nested_duplicates": len(blocks), "unique_event_ids": len(seen),
                                    "unique_action_events": len(action_events), "runtime_frequency_claim": False}
        report["authored_event_bindings"] = action_events
    else:
        report["errors"].append("missing actual V4 compiler index; source binding not tested")

    task_file = ROOT / "data/v4_story/tasks.json"
    if task_file.exists():
        tasks = json.loads(task_file.read_text(encoding="utf-8"))
        original_routes = {k: (t.get("return"), t.get("retry"), t.get("answer"), t.get("targets")) for k, t in tasks["tasks"].items()}
        score_tasks_v4(tasks)
        check("task retry/return/answer/targets conserved", original_routes == {k: (t.get("return"), t.get("retry"), t.get("answer"), t.get("targets")) for k, t in tasks["tasks"].items()})
        check("empty spoken success still has accepted-input feedback", all(t["presentation"]["outcomes"]["success"]["action"] for t in tasks["tasks"].values()))
        check("all wrong returns keep music and exact caller return is restored", all(t["presentation"]["outcomes"]["wrong"]["music"] == "keep" and t["presentation"]["outcomes"]["return"]["music"] == "restore-callsite-bed" for t in tasks["tasks"].values()))

    graph_files = list((ROOT / "data/v4_story/chapters").glob("*.json")) + list((ROOT / "data/v4_story/freetime").glob("*.json"))
    for f in graph_files:
        g = json.loads(f.read_text(encoding="utf-8"))
        if "nodes" not in g:
            continue
        old_routes = {k: (e.get("next"), e.get("options")) for k, e in g["nodes"].items()}
        score_graph_v4(g)
        if g.get("kind") == "freetime":
            check("freetime keeps its own bed: " + f.stem, g["presentation"]["entryMusic"] == "bgm_freetime" and all(v["music"] == "bgm_freetime" for v in g["presentation"]["sectionBeds"].values()))
        check("compiled graph route conserved: " + f.stem,
              old_routes == {k: (e.get("next"), e.get("options")) for k, e in g["nodes"].items()})
        check("compiled graph does not issue BGM on every dialogue: " + f.stem,
              all(not e.get("music") for e in g["nodes"].values() if e.get("type") == "say" and not e.get("presentation", {}).get("actions")))

    report["checks"] = checks
    report["status"] = "pass" if not report["errors"] else "fail"
    out = ROOT / "data/presentation/v4_verification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"checks", "authored_event_bindings"}}, ensure_ascii=False))
    print("checks", sum(x["pass"] for x in checks), "/", len(checks))
    return not report["errors"]


if __name__ == "__main__":
    raise SystemExit(0 if verify() else 1)
