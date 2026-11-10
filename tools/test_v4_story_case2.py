"""Pure graph verification: no generator output, build or game process."""
from __future__ import annotations

import itertools
import json
import copy
import random
from pathlib import Path
from build_v4_story import Source, compile_tasks
from v4_story_case2 import compile_chapter_two, REVIEWED_HASHES

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {p.name: Source(p) for p in (ROOT / "docs/design/rewrite_v4").glob("*.md")}
GRAPH = compile_chapter_two(SOURCES, {}, {"tasks": {}})
NODES = GRAPH["nodes"]


def run(choices=None, start=None, flags=None, graph=None, task_map=None, outcome="A", respect_bindings=False):
    flags = dict(flags or {})
    choices = choices or {}
    graph = graph or GRAPH
    nodes = graph["nodes"]
    node_id = start or graph["entry"]
    stack = []
    seen = []
    cards = {}
    for _ in range(10000):
        n = nodes[node_id]
        seen.append(n)
        flags.update(n.get("set", {}))
        kind = n["type"]
        if kind in ("gate", "end"):
            return n, seen, flags, cards
        if kind == "menu":
            key = next(iter(n.get("options", [{}])[0].get("set", {})), "")
            wanted = choices.get(key, "REST" if n.get("selectionRole") == "freetime" else n["options"][0]["id"])
            option = next(o for o in n["options"] if o["id"] == wanted)
            assert all(flags.get(k, False if isinstance(v, bool) else None) == v for k, v in option.get("requires", {}).items())
            flags.update(option.get("set", {}))
            node_id = option["to"]
        elif kind == "branch":
            node_id = next((c["to"] for c in n["cases"] if flags.get(c["flag"], False if isinstance(c["equals"], bool) else None) == c["equals"]), n["default"])
        elif kind == "call":
            stack.append((n["returnTo"], n.get("onReturnSet", {})))
            node_id = n["target"]
        elif kind == "return":
            node_id, updates = stack.pop()
            flags.update(updates)
        elif kind == "investigate":
            remaining = [o for o in n["spots"] if not flags.get(o["completionFlag"], False)]
            if remaining:
                spot = remaining[0]
                stack.append((spot["returnTo"], spot.get("onReturnSet", {})))
                node_id = spot["entry"]
            else:
                assert all(x in cards for x in n.get("requiredCards", []))
                node_id = n["next"]
        elif kind == "task":
            assert task_map is not None
            task = task_map[n["taskId"]]
            assert all(x in cards for x in task.get("requiresEvidence", []))
            assert not flags.get("public:yuu:executed", False), "Culprit portrait was killed before the actual result"
            if respect_bindings and not task["runtimeReady"]:
                return n, seen, flags, cards
            # This is explicitly a static success model, not an input/runtime
            # result. Unbound tasks remain unbound in both tested data objects.
            outcomes = n.get("outcomes", {})
            selected = outcomes.get(outcome)
            if selected:
                flags.update(selected.get("sets", {}))
                node_id = selected["to"]
            else:
                node_id = n["success"]
        else:
            if kind == "evidence":
                cards[n["evidenceId"]] = n
            node_id = n["next"]
    raise AssertionError("cycle or missing route termination")


def lines(seen, prefix):
    return {n.get("source", {}).get("line") for n in seen if n.get("source", {}).get("file", "").startswith(prefix + "_")}


def verify_route(choices):
    stop, seen, flags, cards = run(choices)
    assert stop["id"] == "v4:2:pending:trial", stop
    assert not any(n["type"] == "end" for n in seen)
    assert set(cards) == {"v4:E2-%02d" % i for i in range(1, 11)} | {"v4:E2-BAND"}
    assert flags["public:ai:body-discovered"] is True
    assert all(flags["window:F2-" + k + ":completed"] is True for k in "ABCD")
    assert sum(n["type"] == "investigate" for n in seen) == 66
    c = {key: choices.get(key, value) for key, value in DEFAULTS.items()}
    a, a2, a3, a4, a5, a6, wash, play, notice = [lines(seen, p) for p in ("12a", "12a2", "12a3", "12a4", "12a5", "12a6", "84", "105", "111")]
    assert (bool(a & set(range(210, 224)))) == (c["2-C01"] != "C")
    assert (bool(a & set(range(224, 232)))) == (c["2-C01"] == "C")
    assert bool(a & set(range(362, 419))) == (c["2-C02"] == "A")
    assert bool(a & set(range(420, 441))) == (c["2-C02"] == "B")
    assert bool(a2 & set(range(98, 128))) == (c["2-C03"] == "A")
    assert bool(a2 & set(range(128, 154))) == (c["2-C03"] == "B")
    assert bool(wash & set(range(165, 182))) == (c["2-C03"] == "A")
    assert bool(wash & set(range(185, 196))) == (c["2-C03"] == "B")
    assert bool(wash & set(range(129, 143))) == (c["2-C10"] != "C")
    assert bool(wash & set(range(143, 157))) == (c["2-C10"] == "C")
    assert bool(a3 & set(range(492, 561))) == (c["2-C05"] == "A")
    assert bool(a3 & set(range(572, 767))) == (c["2-C05"] == "B")
    assert bool(a3 & set(range(784, 823))) == (c["2-C05"] == "B")
    assert bool(a6 & {551}) == (c["2-C05"] == "A")
    assert bool(a6 & {555}) == (c["2-C05"] == "B")
    assert bool(a4 & set(range(462, 535))) == (c["2-C06"] == "A")
    assert bool(a4 & set(range(538, 587))) == (c["2-C06"] == "B")
    assert bool(a5 & set(range(523, 594))) == (c["2-C06"] == "A")
    assert bool(a5 & set(range(597, 612))) == (c["2-C06"] == "B")
    assert any(n["id"] == "v4:2:document:mio-role-request" for n in seen) == (c["2-C06"] == "A")
    assert bool(notice & set(range(319, 326))) == (c["2-C12"] == "B")
    for value, first, last in (("A", 287, 301), ("B", 305, 317), ("C", 321, 335)):
        assert bool(play & set(range(first, last + 1))) == (c["2-C11"] == value)
    # No private free-time memory is granted on a rest route.
    assert not any(k.startswith("fte:") for k in flags)
    assert not (lines(seen, "12a3") & set(range(58, 103)))
    assert not (lines(seen, "12a3") & set(range(151, 210)))
    assert not (lines(seen, "12a3") & set(range(844, 877)))
    assert not (lines(seen, "12a4") & set(range(370, 397)))
    return len(seen)


DEFAULTS = {"2-C01": "A", "2-C02": "A", "2-C03": "A", "2-C04": "A", "2-C05": "A", "2-C06": "A", "2-C07": "A", "2-C08": "A", "2-C09": "A", "2-C10": "A", "2-C11": "A", "2-C12": "A", "W2-C14": "A", "W2-C03": "A", "I2-C01": "A"}
DOMAINS = {key: "AB" if key in ("2-C02", "2-C03", "2-C04", "2-C05", "2-C06", "I2-C01") else "ABC" for key in DEFAULTS}


def main():
    checks = 0
    for n in NODES.values():
        links = [n.get(k) for k in ("next", "success", "target", "returnTo", "default")]
        links += [c["to"] for c in n.get("cases", [])] + [c["to"] for c in n.get("options", [])]
        links += [s["entry"] for s in n.get("spots", [])]
        assert all(x in NODES for x in links if x)
        ref = n.get("source")
        if ref:
            assert SOURCES[ref["file"]].hash == ref["fileSha256"]
        checks += 1
    routes = [dict(DEFAULTS)]
    for key, domain in DOMAINS.items():
        routes.extend({**DEFAULTS, key: value} for value in domain)
    rng = random.Random(20261029)
    routes += [{key: rng.choice(domain) for key, domain in DOMAINS.items()} for _ in range(384)]
    total = sum(verify_route(route) for route in routes)
    # Every still-uncompiled meeting actually stops and grants no completion.
    for node in NODES.values():
        if node.get("selectionRole") != "freetime":
            continue
        for option in node["options"]:
            if option["id"] == "REST":
                continue
            stop, seen, flags, cards = run(start=option["to"], flags=option.get("requires", {}))
            assert stop["type"] == "gate"
            assert not cards
            assert not flags.get("window:" + node["id"].split(":")[-1] + ":completed", False)
            checks += 1
    # Revision mismatch must fail before any source-range compilation.
    source = next(s for s in SOURCES.values() if s.prefix == "12a")
    digest = source.hash
    source.hash = "changed"
    try:
        try:
            compile_chapter_two(SOURCES, {}, {"tasks": {}})
        except ValueError as exc:
            assert "re-read" in str(exc)
        else:
            raise AssertionError("altered source accepted")
    finally:
        source.hash = digest
    print(f"PASS: {len(routes)} complete-to-trial-gate paths, {total} visited nodes, {checks} graph/gate checks, {len(REVIEWED_HASHES)} locked source revisions")
    verify_trial_and_result()


def verify_trial_and_result():
    from v4_native_tasks import convert_task
    library = compile_tasks(SOURCES, json.loads((ROOT / "docs/design/rewrite_v4/qa_2026-10-29/trial_input_reedit.json").read_text(encoding="utf-8-sig")))
    task_map = copy.deepcopy(library)
    graph = compile_chapter_two(SOURCES, {}, task_map)
    nodes = graph["nodes"]
    definitions = task_map["tasks"]
    task_nodes = [n for n in nodes.values() if n["type"] == "task"]
    assert len(task_nodes) == 36
    actual_tasks = {n["taskId"]: definitions[n["taskId"]] for n in task_nodes}
    assert set(x["kind"] for x in actual_tasks.values()) == {"nonstop", "panic", "person", "vote", "choice", "bullet", "showdown", "scrum", "anagram", "mindmine", "spot", "reasoning", "climax", "armament"}
    assert sum(t["kind"] == "nonstop" for t in actual_tasks.values()) == 12
    for n in nodes.values():
        links = [n.get(k) for k in ("next", "success", "target", "returnTo", "default")]
        links += [c["to"] for c in n.get("cases", [])] + [c["to"] for c in n.get("options", [])]
        links += [s["entry"] for s in n.get("spots", [])]
        links += [o["to"] for o in n.get("outcomes", {}).values()]
        assert all(x in nodes for x in links if x)
    assert not any(n.get("source", {}).get("file", "").startswith("12c3_") and n["source"]["line"] == 835 for n in nodes.values())
    assert len(definitions["T2-SD-01"]["pairs"]) == 6
    assert len(definitions["T2-SD-01"]["teams"]["us"]) == 7
    assert len(definitions["T2-SD-01"]["teams"]["them"]) == 6
    assert [x["answer"] for x in definitions["T2-MG-01"]["slots"]] == list("CBACBA")
    assert definitions["T2-VOTE-01"]["voteCounts"] == {"yuu": 11, "mio": 2}
    unbound = {k for k, t in actual_tasks.items() if not t["runtimeReady"]}
    assert unbound == {"T2-SPOT-A01", "T2-MM-A02", "T2-MM-01", "T2-MM-A03"}
    for n in task_nodes:
        assert n["trialDead"] == ["kaede", "taiga", "ai"] and len(set(n["seats"])) == 16
        task = actual_tasks[n["taskId"]]
        native = convert_task(task, graph["evidenceCatalog"])
        assert native["ready"] == task["runtimeReady"]
        for wrong in task.get("wrongVariants", []):
            assert all(e["id"] not in nodes for e in wrong.get("script", []))
    baseline = {**DEFAULTS, "T2-C03": "A", "T2-C02": "A", "T2-C01": "A", "T2-C04": "A", "R2-C01": "A"}
    initial = {"1-C08": "A"}
    stop, _, _, _ = run(baseline, flags=initial, graph=graph, task_map=definitions, respect_bindings=True)
    assert stop["taskId"] == "T2-SPOT-A01", "Unbound actual picture was bypassed"
    variants = [{**baseline, key: value} for key in ("T2-C03", "T2-C02", "T2-C01", "T2-C04", "R2-C01", "2-C09", "2-C12") for value in "ABC"]
    rng = random.Random(20261030)
    variants += [{**baseline, **{key: rng.choice(domain) for key, domain in DOMAINS.items()}, **{key: rng.choice("ABC") for key in ("T2-C03", "T2-C02", "T2-C01", "T2-C04", "R2-C01")}} for _ in range(96)]
    walked = 0
    for choices in variants:
        for outcome, old_promise, prior_lie, prior_tin in itertools.product("AB", "ABC", (False, True), (False, True)):
            flags0 = {"1-C08": old_promise, "T1-LIE-B": prior_lie, "fte:25:complete": prior_tin}
            stop, seen, flags, cards = run(choices, flags=flags0, graph=graph, task_map=definitions, outcome=outcome)
            assert stop["id"] == "v4:2:end" and flags["public:yuu:executed"]
            assert sum(n["type"] == "task" for n in seen) == 36
            assert "v4:T2-RS-A03:unobserved-life-check" not in cards
            assert bool(lines(seen, "169") & set(range(44, 93))) == (outcome == "B")
            assert bool(lines(seen, "169") & set(range(102, 123))) == (outcome == "B")
            assert bool(lines(seen, "164") & set(range(168, 187))) == prior_lie
            assert bool(lines(seen, "155") & set(range(19, 38))) == prior_tin
            assert bool(lines(seen, "155") & set(range(41, 52))) != prior_tin
            for key, first, last in (("A", 83, 107), ("B", 111, 123), ("C", 127, 141)):
                assert bool(lines(seen, "113") & set(range(first, last + 1))) == (old_promise == key)
            for key, first, last, echo in (("A", 145, 167, 241), ("B", 171, 199, 245), ("C", 203, 227, 249)):
                selected = choices["R2-C01"] == key
                assert bool(lines(seen, "155") & set(range(first, last + 1))) == selected
                assert (echo in lines(seen, "155")) == selected
            walked += 1
    assert not graph["campaignReady"]
    assert unbound == {k for k, t in actual_tasks.items() if not t["runtimeReady"]}, "Static simulation altered runtime readiness"
    print(f"PASS: {walked} static success paths through chapter end; 36 task boundaries, 32 typed native conversions, four real picture gates preserved. No game or original executable ran.")


if __name__ == "__main__":
    main()
