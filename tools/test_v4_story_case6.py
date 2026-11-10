"""Pure final-chapter route/source checks; never runs a game or generator."""
from __future__ import annotations
import copy
import itertools
import json
import random
from pathlib import Path
from build_v4_story import Source, compile_tasks
from v4_native_tasks import convert_task
from v4_story_case6 import compile_chapter_six, REVIEWED_HASHES

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {p.name: Source(p) for p in (ROOT / "docs/design/rewrite_v4").glob("*.md")}
LIBRARY = compile_tasks(SOURCES, json.loads((ROOT / "docs/design/rewrite_v4/qa_2026-10-29/trial_input_reedit.json").read_text(encoding="utf-8-sig")))
TASKS = copy.deepcopy(LIBRARY)
GRAPH = compile_chapter_six(SOURCES, {}, TASKS)
NODES = GRAPH["nodes"]
DEFINITIONS = TASKS["tasks"]


def walk(choices=None, initial=None, outcome="A", respect_bindings=False):
    choices, flags = choices or {}, dict(initial or {})
    node_id, seen, stack, cards = GRAPH["entry"], [], [], {}
    for _ in range(6000):
        n = NODES[node_id]
        seen.append(n)
        flags.update(n.get("set", {}))
        kind = n["type"]
        if kind in ("gate", "end"):
            return n, seen, flags, cards
        if kind == "menu":
            key = next(iter(n["options"][0]["set"]))
            option = next(o for o in n["options"] if o["id"] == choices.get(key, "A"))
            flags.update(option["set"])
            node_id = option["to"]
        elif kind == "branch":
            node_id = next((c["to"] for c in n["cases"] if flags.get(c["flag"], False if isinstance(c["equals"], bool) else None) == c["equals"]), n["default"])
        elif kind == "investigate":
            remaining = [o for o in n["spots"] if not flags.get(o["completionFlag"], False)]
            if remaining:
                spot = remaining[0]
                stack.append((spot["returnTo"], spot["onReturnSet"]))
                node_id = spot["entry"]
            else:
                assert all(c in cards for c in n["requiredCards"])
                node_id = n["next"]
        elif kind == "return":
            node_id, update = stack.pop()
            flags.update(update)
        elif kind == "task":
            task = DEFINITIONS[n["taskId"]]
            assert all(c in cards for c in task.get("requiresEvidence", [])), (n["taskId"], set(cards))
            assert not flags.get("public:game:control-ended", False)
            assert not flags.get("public:outside:actual-response", False)
            if respect_bindings and not task["runtimeReady"]:
                return n, seen, flags, cards
            # Explicit static success model. No question/geometry is actually
            # solved here and no tested data readiness field is changed.
            selected = n.get("outcomes", {}).get(outcome)
            if selected:
                flags.update(selected.get("sets", {}))
                node_id = selected["to"]
            else:
                node_id = n["success"]
        else:
            if kind == "evidence":
                cards[n["evidenceId"]] = n
            node_id = n["next"]
    raise AssertionError("route did not terminate")


def by_source(seen):
    result = {}
    for n in seen:
        source = n.get("source", {})
        if source:
            result.setdefault(source["file"].split("_", 1)[0], set()).add(source["line"])
    return result


def check_path(choices, initial=None, outcome="A"):
    end, seen, flags, cards = walk(choices, initial, outcome)
    support = choices.get("E6-C01", "A")
    voice = choices.get("E6-C02", "A")
    papers = choices.get("T6-C01", "A")
    location = by_source(seen)
    assert end["id"] == "v4:6:end:" + support
    assert end["humanSurvivors"] == ["mio", "rin", "nana", "sho", "satsuki"]
    assert end["nanaLocation"] == ("outside" if support == "A" else "inside-current-reception")
    assert end["supportActive"] == (support == "B")
    assert flags["public:lappy:support-active"] == (support == "B")
    assert flags["public:lappy:responsive"] == (support == "B")
    assert flags["public:nana:old-vow-ended"]
    assert flags["public:game:control-ended"] and flags["public:outside:actual-response"] and flags["public:loading-gate:opened"]
    assert flags.get("public:records:reception-first-page-sent", False) == (papers == "C")
    assert sum(n["type"] == "task" for n in seen) == 35
    tasks_in_order = [n['taskId'] for n in seen if n['type']=='task']
    assert tasks_in_order.index('T6-VOTE-01') < tasks_in_order.index('T6-RL-FINAL')
    assert tasks_in_order[-1] == GRAPH['resultTaskId'] == 'T6-RL-FINAL'
    hearing_at = next(i for i,n in enumerate(seen) if n.get('taskId')=='T6-RL-FINAL')
    control_at = next(i for i,n in enumerate(seen) if n.get('set',{}).get('public:game:control-ended'))
    assert hearing_at < control_at
    assert len(cards) == 15 and "v4:E6-05" in cards and cards["v4:E6-05"]["revision"]
    assert len([n for n in seen if n["type"] == "investigate"]) == 26
    d = location["16d2"]
    assert bool(d & set(range(284, 339))) == (support == "A")
    assert bool(d & set(range(342, 391))) == (support == "B")
    assert bool(d & set(range(540, 569))) == (support == "A")
    assert bool(d & set(range(572, 621))) == (support == "B")
    assert bool(location["122"] & set(range(121, 146))) == (support == "A")
    assert bool(location["122"] & set(range(149, 160))) == (support == "B")
    for key, a, z in (("A", 83, 105), ("B", 109, 135), ("C", 139, 159)):
        assert bool(location["73"] & set(range(a, z + 1))) == (voice == key)
    for key, a, z in (("A", 95, 101), ("B", 107, 113), ("C", 119, 131)):
        assert bool(location["16d1"] & set(range(a, z + 1))) == (papers == key)
    assert bool(location["169"] & set(range(362, 391))) == (outcome == "B")
    assert bool(location["169"] & set(range(400, 407))) == (outcome == "B")
    assert bool(location["169"] & set(range(444, 449))) == (outcome == "B")
    assert bool(location["169"] & {452}) == (outcome == "B" and support == "A")
    assert bool(location["169"] & {456}) == (outcome == "B" and support == "B")
    for number, a, z, prefix in ((1, 688, 700, "16d2"), (2, 414, 420, "169"), (4, 424, 430, "169"), (5, 434, 440, "169")):
        assert bool(location.get(prefix, set()) & set(range(a, z + 1))) == bool((initial or {}).get(f"T{number}-LIE-B", False))
    complete_rin = bool((initial or {}).get("fte:20:complete", False))
    assert (309 in location["16a2"]) == complete_rin and (313 in location["16a2"]) != complete_rin
    assert bool(location["16a"] & set(range(253, 262))) == (choices.get("6-C01", "A") != "A")
    return len(seen)


def main():
    # Reception includes Nana; her thirteen targets exclude herself and Koto.
    memory_scope=DEFINITIONS['T6-NS-A08']['answerScope']
    assert '접수14명 중 나나 자신을 제외한13명' in memory_scope
    assert '첫14명 대상 망각' not in memory_scope
    for n in NODES.values():
        links = [n.get(k) for k in ("next", "success", "target", "returnTo", "default")]
        links += [c["to"] for c in n.get("cases", [])] + [c["to"] for c in n.get("options", [])]
        links += [x["entry"] for x in n.get("spots", [])] + [o["to"] for o in n.get("outcomes", {}).values()]
        assert all(x in NODES for x in links if x)
        if n.get("source"):
            assert SOURCES[n["source"]["file"]].hash == n["source"]["fileSha256"]
    task_nodes = [n for n in NODES.values() if n["type"] == "task"]
    actual_tasks = {n["taskId"]: DEFINITIONS[n["taskId"]] for n in task_nodes}
    unbound = {k for k, t in actual_tasks.items() if not t["runtimeReady"]}
    assert unbound == {"T6-MM-01", "T6-MM-A02", "T6-MM-A03", "T6-SPOT-A01", "T6-PERSON-A02"}
    for n in task_nodes:
        assert len(set(n["seats"])) == 16 and len(n["trialDead"]) == 11
        assert not set(n["trialDead"]) & {"mio", "rin", "nana", "sho", "satsuki"}
        t = actual_tasks[n["taskId"]]
        assert convert_task(t, GRAPH["evidenceCatalog"])["ready"] == t["runtimeReady"]
        for wrong in t.get("wrongVariants", []):
            assert all(e["id"] not in NODES for e in wrong.get("script", []))
    assert [x["answer"] for x in DEFINITIONS["T6-MG-01"]["slots"]] == list("CABCABCA")
    assert len(DEFINITIONS["T6-SD-01"]["pairs"]) == 6
    assert DEFINITIONS["T6-SD-01"]["teams"] == {"us": ["mio", "nana", "rin"], "them": ["sho", "satsuki"]}
    assert [x["source"]["line"] for x in DEFINITIONS["T6-SD-01"]["pairs"][2]["afterSuccess"]] == [101, 103, 105, 107]
    assert DEFINITIONS["T6-VOTE-01"]["voteCounts"] == {"koto": 5}
    assert DEFINITIONS["T6-VOTE-01"]["majorityRequired"] == 3
    roles = {"외부접수원": "external_receptionist", "현장확인자": "site_checker", "어린 하루카·복원 음성": "restored_child_haruka_voice", "상대·복원 음성": "restored_other_voice"}
    source_lines = {(n.get("source", {}).get("file"), n.get("source", {}).get("line")): n for n in NODES.values() if n.get("source")}
    for source in SOURCES.values():
        if source.prefix not in {"16b2", "16d1", "16d2", "73", "122", "169"}:
            continue
        for number, raw in enumerate(source.lines, 1):
            label = raw[1:].split("]", 1)[0] if raw.startswith("[") else ""
            if label not in roles or (source.prefix == "169" and number < 400):
                continue
            n = source_lines[(source.name, number)]
            assert n["type"] == "say" and n["speaker"] == label and n["actor"] == roles[label]
            assert n["text"] == raw.split("]", 1)[1].strip() and not n["participantSeat"]
    actual_picture = DEFINITIONS["T6-PERSON-A02"]
    assert "image" not in actual_picture["candidateOverrides"]["haruka"]
    assert actual_picture["candidateOverrides"]["haruka"]["identityScope"] == "actual-past-victim-not-current-created-body"
    first, _, _, _ = walk(respect_bindings=True)
    assert first["taskId"] == "T6-MM-A02"
    # Every independent ending choice combination, with both current lie
    # outcomes. Early query order varies without changing the ending options.
    keys = ("6-C02", "6-C03", "T6-C03", "T6-C02", "T6-C01", "E6-C02", "E6-C01")
    rng = random.Random(20261030)
    paths = total = 0
    for values in itertools.product(*(["ABC"] * 6 + ["AB"])):
        choices = dict(zip(keys, values))
        choices.update({"6-C01": rng.choice("ABC"), "I6-C01": rng.choice("ABC")})
        for outcome in "AB":
            total += check_path(choices, {"fte:20:complete": bool(paths % 2)}, outcome)
            paths += 1
    for prior in itertools.product((False, True), repeat=4):
        flags = dict(zip(("T1-LIE-B", "T2-LIE-B", "T4-LIE-B", "T5-LIE-B"), prior))
        for support, voice, outcome in itertools.product("AB", "ABC", "AB"):
            total += check_path({"E6-C01": support, "E6-C02": voice}, flags, outcome)
            paths += 1
    for p in REVIEWED_HASHES:
        source = next(x for x in SOURCES.values() if x.prefix == p)
        original = source.hash
        source.hash = "altered"
        try:
            try:
                compile_chapter_six(SOURCES, {}, {"tasks": {}})
            except ValueError as exc:
                assert "re-read" in str(exc)
            else:
                raise AssertionError("Altered reviewed source accepted: " + p)
        finally:
            source.hash = original
    assert unbound == {k for k, t in actual_tasks.items() if not t["runtimeReady"]}
    assert not GRAPH["campaignReady"]
    print(f"PASS: {paths} static paths through both actual open endings; {total} visited nodes; {len(REVIEWED_HASHES)} source hashes; 35 task boundaries, final seven-link hearing before control release. Game/executable/build/generator runs:0.")


if __name__ == "__main__":
    main()
