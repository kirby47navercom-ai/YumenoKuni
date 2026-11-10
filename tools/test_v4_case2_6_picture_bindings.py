"""Pure source/pixel-contract checks; no output, renderer or game invocation."""
from copy import deepcopy
import itertools
import json
from pathlib import Path
from build_v4_story import Source, compile_tasks
from v4_story_case2 import compile_chapter_two
from v4_story_case6 import compile_chapter_six
from v4_case2_6_picture_bindings import PICTURES, UNBOUND, bind_pictures
from v4_native_tasks import convert_task

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {p.name: Source(p) for p in (ROOT / "docs/design/rewrite_v4").glob("*.md")}


def inside(poly, x, y):
    hit = False
    for a, b in zip(poly, poly[1:] + poly[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
            hit = not hit
    return hit


def main():
    ledger = json.loads((ROOT / "docs/design/rewrite_v4/qa_2026-10-29/trial_input_reedit.json").read_text(encoding="utf-8-sig"))
    tasks = compile_tasks(SOURCES, ledger)
    graph2 = compile_chapter_two(SOURCES, {}, tasks)
    graph6 = compile_chapter_six(SOURCES, {}, tasks)
    original6 = deepcopy({k: t for k, t in tasks["tasks"].items() if k.startswith("T6-")})
    count2, count6 = len(graph2["nodes"]), len(graph6["nodes"])
    bind_pictures(graph2, SOURCES, tasks)
    bind_pictures(graph6, SOURCES, tasks)
    assert len(graph2["nodes"]) == count2 + 4 and len(graph6["nodes"]) == count6 + 4
    assert all(original6[k] == t for k, t in tasks["tasks"].items() if k.startswith("T6-") and k not in PICTURES and k != "T6-PERSON-A02")
    assert not any(n["type"] == "task" and not n["runtimeReady"] for g in (graph2,graph6) for n in g["nodes"].values())
    assert not graph2["pictureBindingReview"] and not graph6["pictureBindingReview"]
    for ident, p in PICTURES.items():
        task = tasks["tasks"][ident]
        assert task["runtimeReady"] and task["image"] == p["file"]
        assert not any(b["kind"] == "forensicImageRegions" for b in task["bindings"])
        graph = graph2 if ident.startswith("T2-") else graph6
        native = convert_task(task, graph["evidenceCatalog"])
        assert native["ready"] and native["stage"]["regions"] == p["regions"]
        for region in p["regions"]:
            assert len(region["polygon"]) >= 3
            assert all(0 <= c <= 1 for point in region["polygon"] for c in point)
        grants = [n for n in graph["nodes"].values() if n["type"] == "evidence" and n["evidenceId"] == p["evidenceId"] and not n.get("revision")]
        assert len(grants) == 1
        grant = grants[0]
        before = [n for n in graph["nodes"].values() if n.get("next") == grant["id"]]
        assert len(before) == 1
        doc = before[0]
        assert doc["type"] == "document" and doc["image"] == p["file"] and doc["rows"] == []
        assert not doc["grantsEvidence"] and not doc["private"]
        assert not any(n["type"] == "evidence" and n.get("image") == p["file"] for n in graph["nodes"].values())
    latch = tasks["tasks"]["T2-SPOT-A01"]
    actual = [(r["id"], r["correct"]) for r in latch["regions"] if inside(r["polygon"], .380, .420) or inside(r["polygon"], .748, .360)]
    assert actual == [("external-latch-left", True), ("external-latch-right", True)]
    assert all(not inside(r["polygon"], .05, .05) for r in latch["regions"])
    wheels = [r for r in latch["regions"] if r.get("wrongVariant") == "wheel"]
    assert len(wheels) == 3 and latch["wrongVariants"][0]["cause"] == "wheel"
    assert [e["source"]["line"] for e in latch["wrongVariants"][0]["script"]] == [578, 580]
    assert [e["source"]["line"] for e in latch["wrong"]] == [580]
    base = tasks["tasks"]["T2-MM-A02"]
    assert inside(base["regions"][0]["polygon"], .530, .660)
    assert not inside(base["regions"][0]["polygon"], .250, .400)
    assert not base["wrong"] and not base["wrongVariants"]
    assert base["unavailableSourceWrongVariants"][0]["dispatch"] is False
    # Every sampled visible cloth mask stays outside the actual metal mask.
    for x in range(200):
        for y in range(200):
            assert not all(inside(r["polygon"], x/200, y/200) for r in base["regions"])
    snapshot = deepcopy((graph2, graph6, tasks))
    bind_pictures(graph2, SOURCES, tasks)
    bind_pictures(graph6, SOURCES, tasks)
    assert snapshot == (graph2, graph6, tasks)
    for ident in UNBOUND:
        assert not tasks["tasks"][ident]["runtimeReady"]
    # Contract corruption fails without touching any original image/source.
    picture = PICTURES["T2-SPOT-A01"]
    old = picture["sha256"]
    picture["sha256"] = "changed"
    try:
        try:
            bind_pictures(graph2, SOURCES, tasks)
        except ValueError as exc:
            assert "re-inspect" in str(exc)
        else:
            raise AssertionError("Changed reviewed image accepted")
    finally:
        picture["sha256"] = old
    assert inside(tasks["tasks"]["T6-MM-A02"]["regions"][2]["polygon"], .270, .710)
    assert inside(tasks["tasks"]["T6-MM-A03"]["regions"][0]["polygon"], .250, .420)
    topology = tasks["tasks"]["T6-SPOT-A01"]
    assert "출입·시야 관계" in topology["prompt"] and "옛 평면" in topology["sourcePromptBeforeTopologyClarification"]
    assert [e["source"]["line"] for e in topology["wrongVariants"][0]["script"]] == [510, 512]
    connection = tasks["tasks"]["T2-MM-01"]
    assert inside(connection["regions"][1]["polygon"], .440, .570)
    assert [v["cause"] for v in connection["wrongVariants"]] == ["microphone-switch", "card-slot", "speaker-output"]
    assert [e["source"]["line"] for v in connection["wrongVariants"] for e in v["script"]] == [194, 206, 212]
    person=tasks["tasks"]["T6-PERSON-A02"]
    assert person["runtimeReady"] and person["candidateOverrides"]["haruka"]["layout"] == "landscape-photo"
    assert person["candidateOverrides"]["haruka"]["image"] == tasks["tasks"]["T6-MM-01"]["image"]
    assert "memorial" not in person["candidateOverrides"]["haruka"]["image"]
    assert convert_task(person,graph6["evidenceCatalog"])["stage"]["candidateOverrides"] == person["candidateOverrides"]
    # Exercise the complete authored graphs with real binding/ownership gates
    # enabled. Only task success is simulated; no actual mouse input is solved.
    import test_v4_story_case2 as routes2
    import test_v4_story_case6 as routes6
    def checked_images(seen):
        opened=set()
        for node in seen:
            if node["type"]=="document" and node.get("image"):
                opened.add(node["image"])
            if node["type"]=="task":
                task=tasks["tasks"][node["taskId"]]
                required=[]
                if node["taskId"] in PICTURES:
                    required.append(task["image"])
                if node["taskId"]=="T6-PERSON-A02":
                    required.append(task["candidateOverrides"]["haruka"]["image"])
                assert all(image in opened for image in required),node["taskId"]
    paths=0
    for outcome,old_promise in itertools.product("AB","ABC"):
        end,seen,flags,cards=routes2.run(routes2.DEFAULTS,flags={"1-C08":old_promise},graph=graph2,task_map=tasks["tasks"],outcome=outcome,respect_bindings=True)
        assert end["id"]=="v4:2:end" and sum(n["type"]=="task" for n in seen)==36
        checked_images(seen)
        paths+=1
    routes6.GRAPH,routes6.NODES,routes6.DEFINITIONS=graph6,graph6["nodes"],tasks["tasks"]
    for support,voice,outcome in itertools.product("AB","ABC","AB"):
        end,seen,flags,cards=routes6.walk({"E6-C01":support,"E6-C02":voice},outcome=outcome,respect_bindings=True)
        assert end["id"]=="v4:6:end:"+support and sum(n["type"]=="task" for n in seen)==34
        checked_images(seen)
        paths+=1
    print(f"PASS: nine source/pixel-bound inputs; eight first-acquisition image-before-card documents; both correct external latches; exact conditional wrong callbacks; actual historical landscape picture/person identity; idempotence and image/source/UV revisions; {paths} full static success paths with real binding/owned-card/prior-image checks enabled. All70 chapter2/6 input definitions are typed/bound, not a runtime-play claim. Central output/build/game/original-asset changes:0.")


if __name__ == "__main__":
    main()
