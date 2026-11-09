"""Explicit case-one trial control flow. Never replay source wrong branches linearly."""
from __future__ import annotations

import re


def compile_first_half(g, sources, tasks, next_id):
    docs = {s.prefix: s for s in sources.values()}
    task_map = tasks["tasks"]

    def says(prefix, a, b):
        return [e for e in docs[prefix].paragraphs(a, b) if e["type"] == "say"]

    def span(prefix, a, b, target):
        source = docs[prefix]
        start = source.at(a) if isinstance(a, str) else a
        stop = source.at(b) - 1 if isinstance(b, str) else b if b is not None else len(source.lines)
        return g.sequence(source, start, stop, target)

    def new_task(ident, kind, prefix, start, **fields):
        value = {"id": ident, "kind": kind, "chapter": "1", "sourceKind": "BASELINE", "source": docs[prefix].ref(start), "intro": [], "lines": [], "wrong": [], "success": [], "bindings": [], "return": {"graphNext": True}, "runtimeReady": True, "retry": {"sameTask": True, "preserveEvidence": True, "preservePublicFacts": True, "cancellationIsSuccess": False}, **fields}
        task_map[ident] = value
        return value

    def task_node(ident, target):
        return g.add("v4:input:" + ident, {"type": "task", "taskId": ident, "runtimeReady": task_map[ident]["runtimeReady"], "source": task_map[ident]["source"], "next": target, "success": target})

    def branch(ident, flag, options, default, target):
        return g.add(ident, {"type": "branch", "cases": [{"flag": flag, "equals": value, "to": span(prefix, a, b, target)} for value, prefix, a, b in options], "default": default})

    def menu(prefix, ident, heading_line, rows, finish, target, labels):
        options = []
        for i, first in enumerate(rows):
            end = rows[i + 1] - 1 if i + 1 < len(rows) else finish - 1
            options.append({"id": "ABC"[i], "label": labels[i], "to": span(prefix, first + 1, end, target), "set": {ident: "ABC"[i]}})
        return g.add(f"v4:{prefix}:{ident}:menu", {"type": "menu", "q": docs[prefix].lines[heading_line - 1].split("—")[-1].strip(), "options": options, "source": docs[prefix].ref(heading_line)})

    ns = new_task("T1-NS-T05e", "nonstop", "11c1", 452, lines=says("11c1", 464, 476), wrong=says("11c1", 520, 524), wrongVariants=[{"cause": "wrong-evidence-B", "script": says("11c1", 488, 494)}, {"cause": "true-statement-name", "script": says("11c1", 498, 506)}, {"cause": "wrong-evidence-observer", "script": says("11c1", 510, 516)}], answerEvidenceId="v4:E1-02", requiresEvidence=["v4:E1-02"], judgment="refute", prompt="문이 기록한 것과 사람 수")
    target_line = next(e for e in ns["lines"] if e["source"]["line"] == 472)
    ns["targets"] = [{"lineId": target_line["id"], "word": "한 번 열릴 때마다 한 사람", "verdict": "refute", "actor": "haruka"}]
    ns["vpoint"] = {"optional": True, "character": "한"}

    new_task("T1-MM-01", "mindmine", "163", 5, intro=says("163", 10, 14), wrongVariants=[{"cause": "wrong-region:seal", "script": says("163", 16, 20)}, {"cause": "wrong-region:door", "script": says("163", 22, 26)}, {"cause": "wrong-region:window", "script": says("163", 28, 32)}], success=says("163", 34, 38), prompt="B를 열어도 사람이 통과하려면 먼저 건드려야 하는 것은?", regionDescription="바깥 보강판", imageDescription="수사에서 확인한 B의 바깥 구조", bindings=[{"kind": "forensicImageRegions", "required": True, "description": "The actual inspected B drawing, with external reinforcing plate distinguishable from seal/door/window."}], runtimeReady=False)
    # Direct visual inspection: the existing image really shows the exterior
    # reinforcing plate and fixed window. It does not show a selectable seal;
    # that unused wrong variant must not be painted onto an unrelated pixel.
    mine = task_map["T1-MM-01"]
    mine.update(image="art/inspection_v4/delivery/door_B_fixed_window.webp", coordinateSystem="normalized-image-uv", regions=[{"id":"reinforcing-plate","label":"바깥 보강판","polygon":[[.230,.195],[.474,.195],[.474,.887],[.230,.887]],"correct":True},{"id":"fixed-window","label":"고정 창","polygon":[[.621,.208],[.892,.208],[.892,.622],[.621,.622]],"correct":False,"wrongVariant":"wrong-region:window"}], answerRegionId="reinforcing-plate", mechanic={"colors":["white","pink","yellow","blue"],"colorCountByDifficulty":True,"removeAdjacentSameColor":True,"adjacency":"orthogonal-four","gravity":False,"boundaryColorCycleOnce":True,"isolatedHits":3,"isolatedPenaltyTicks":600,"thenSelectRegion":True}, bindings=[], runtimeReady=True, bindingSource="Directly viewed 3840x2160 delivery image; plate/window UVs follow visible artwork, never option index. Outside/unmapped regions retry without inventing a pictured seal.")
    pairs = []
    for no, a in enumerate((55, 69, 83, 97, 111, 125), 1):
        before = says("163", a + 1, a + 7)
        actor = before[0]
        response = before[1]
        raw = docs["163"].lines[actor["source"]["line"] - 1]
        keyword = re.search(r"\*\*(.+?)\*\*", raw)[1]
        spec = docs["163"].lines[a + 3]
        response_key = spec.split("/", 1)[1].strip("* .")
        pairs.append({"id": f"T1-SD-01:round:{no}", "them": actor["actor"], "themText": actor["text"], "keyword": keyword, "us": response["actor"], "usText": response["text"], "responseKeyword": response_key, "wrong": says("163", a + 8, a + 12), "source": docs["163"].ref(a)})
    new_task("T1-SD-01", "scrum", "163", 41, intro=says("163", 48, 52), success=says("163", 140, 148), pairs=pairs, teams={"us": ["mio", "rin", "nana", "riku", "rei", "haruka", "sho"], "them": ["taiga", "sora", "yuu", "koto", "akari", "satsuki", "ai", "ken"]}, teamMeaning="positions in the current explanation; neither team implies blanket trust/culprit status")
    panic = new_task("T1-PD-01", "panic", "130", 133, lines=says("130", 138, 152), wrong=says("130", 188, 190), success=says("130", 194, 215), answerEvidenceId="v4:130:T-08d:unobserved-gaps", evidenceOptions=[{"id": "v4:130:T-08d:unobserved-gaps", "name": "두 사람 외에도 미확인 시간이 있다", "source": [docs["130"].ref(141), docs["130"].ref(143)]}, {"id": "v4:E1-12", "name": "미오가23:14에 합류를 보았다"}, {"id": "v4:E1-07", "name": "원본 순찰표의 숫자가 고쳐졌다"}], scopeOnlyEvidence=True, requiresEvidence=[], judgment="refute")
    panic_target = next(e for e in panic["lines"] if e["source"]["line"] == 147)
    panic["targets"] = [{"lineId": panic_target["id"], "word": "타이가 아니면 소라", "verdict": "refute", "actor": "yuu"}]
    panic["scopePolicy"] = {"lifetime":"current-input-only","source":"heard current debate premises, not a physical evidence acquisition","inventoryGrant":False,"persistAfterReturn":False,"requiresOwnedEvidence":False}
    panic["lanes"] = [{"id": pos, "actor": actor, "lines": [e["id"] for e in panic["lines"] if e["actor"] == actor]} for pos, actor in (("왼쪽", "yuu"), ("가운데", "rin"), ("오른쪽", "ai"))]
    # No guessed global card is awarded for an utterance heard only in this
    # live debate. The premise offered by the source stays local to this task.
    g.taskDefinitions = task_map

    after_panic = span("130", 217, None, span("11c1", 957, None, next_id))
    panic_entry = task_node("T1-PD-01", after_panic)
    panic_prelude = span("130", 5, 130, panic_entry)
    after_patrol = span("11c1", 909, 954, panic_prelude)
    notebook_source = docs['189']
    if notebook_source.hash != '0fd981312aadc758866f346c041f1bb25f997586035d8d841b6a737643ef4342':
        raise ValueError('Re-read the current notebook confrontation before changing its trial placement.')
    notebook_confrontation = g.sequence(notebook_source, 1, len(notebook_source.lines), after_patrol)
    taiga_join = span("11c1", 880, 902, span("11c1", 904, 908, notebook_confrontation))
    taiga_choice = branch("v4:11c1:TAIGA03:callback", "F-TA03-B", [("B1", "11c1", 844, 854), ("B2", "11c1", 856, 866), ("B3", "11c1", 868, 878)], "v4:11c1:TAIGA03:skip", taiga_join)
    g.add("v4:11c1:TAIGA03:skip", {"type": "stage", "direction": "타이가03을 실제로 만나지 않은 경로는 회상을 건너뛴다.", "next": next(n["id"] for n in g.nodes.values() if n.get("source", {}).get("file") == docs["11c1"].name and n.get("source", {}).get("line") == 905)})
    scrum_entry = task_node("T1-SD-01", taiga_choice)
    before_scrum = span("11c1", 555, 836, scrum_entry)
    ns_success = span("11c1", 528, 554, before_scrum)
    ns_entry = task_node("T1-NS-T05e", ns_success)
    ns_intro = span("11c1", 452, 463, ns_entry)
    personal_choice_after = span("11c1", 424, 451, ns_intro)
    personal_choice = menu("11c1", "T1-C02", 380, [386, 396, 410], 424, personal_choice_after, ["개인 질문 공개 요구를 막는다", "미오도 공개를 요구한다", "목적 판단을 보류하고 시야를 비교한다"])
    witnesses = span("11c1", 240, 379, personal_choice)
    # The source's three question labels precede the A/B/C bodies; no unrelated
    # person is spoken into existence and no hidden question sheet is opened.
    wrong_map_after = span("93", 163, 376, span("11c1", 238, 239, witnesses))
    wrong_map_choice = menu("93", "T1-C05", 117, [121, 133, 149], 161, wrong_map_after, ["미오가 고친 문장을 읽는다", "코토에게 직접 다시 읽어 달라고 한다", "린에게 본인의 구간을 다시 읽어 달라고 한다"])
    wrong_map_start = span("93", 5, 116, wrong_map_choice)
    rear_explanation = span("11c1", 208, 235, wrong_map_start)
    mine = task_node("T1-MM-01", rear_explanation)
    pre_mine = span("11c1", 54, 205, mine)
    dinner_echo_tail = span("66", 262, None, pre_mine)
    dinner_echo = branch("v4:66:1-C05:callback", "1-C05", [("A", "66", 250, 252), ("B", "66", 254, 256), ("C", "66", 258, 260)], "v4:66:missing-dinner-choice", dinner_echo_tail)
    g.add("v4:66:missing-dinner-choice", {"type": "gate", "reason": "Compulsory 1-C05 choice is missing; do not play all three dinner memories."})
    after_first_question = span("66", 205, 248, dinner_echo)
    first_question = menu("66", "T1-C04", 115, [119, 149, 177], 203, after_first_question, ["리쿠의 은폐를 먼저 의심한다", "코토의 공용 물건 관리 영향력이 두렵다고 말한다", "래피 파일의 미확정 범위를 묻는다"])
    first_question_intro = span("66", 5, 114, first_question)
    silence = span("137", 5, None, first_question_intro)
    opening_after_memory = span("11c1", 20, 49, silence)
    memory = branch("v4:123:1-C09:trial", "1-C09", [("A", "123", 230, 232), ("B", "123", 234, 236), ("C", "123", 238, 240)], "v4:123:missing-play-choice", opening_after_memory)
    g.add("v4:123:missing-play-choice", {"type": "gate", "reason": "Required 1-C09 rhythm-play choice is missing; no unplayed memory is granted."})
    return span("11c1", 6, 17, memory)
