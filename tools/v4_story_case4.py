"""Explicit V4 chapter-four source routes; no legacy plot or branch autoplay.

Only the central story compiler writes output. Unbound image/rhythm/meeting
contracts stay actual gates. Scene chronology is distinct from causal proof.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re

from v4_story_case3 import S, C, I, M, T, E, H, V


SOURCE_PREFIXES = tuple(["14a"] + ["14a" + str(i) for i in range(2, 14)] + ["14b" + str(i) for i in range(1, 5)] + ["14c" + str(i) for i in range(1, 4)] + ["14d", "08", "09", "80", "106", "124", "127", "134", "174", "178", "142", "71", "85", "99", "77", "131", "114", "166", "160", "169", "184", "192"])


def route_source_hashes(sources):
    current = {s.name: s.hash for s in sources.values() if s.prefix in SOURCE_PREFIXES}
    if current != REVIEWED_SOURCE_HASHES:
        raise ValueError("Chapter4 source hashes changed; re-read exact routes before updating line ranges")
    return dict(REVIEWED_SOURCE_HASHES)


def compile_chapter_four(sources, freetime_graphs, tasks):
    from build_v4_story import Graph, SPEAKERS
    route_source_hashes(sources)
    docs = {s.prefix: s for s in sources.values()}
    if set(SOURCE_PREFIXES) - set(docs):
        raise ValueError("Chapter4 required source missing")
    g = Graph("4")
    tm = tasks["tasks"]
    g.taskDefinitions = tm
    spans, scopes, cache = [], [], {}
    cards = _evidence(docs)
    _baseline_tasks(tm, docs)
    _bind_additional(tm, cards)

    def uid(label, target=""):
        return "v4:4:" + label + (":" + hashlib.sha256(target.encode()).hexdigest()[:12] if target else "")

    def gate(label, reason, target="", source=None):
        return g.add(uid("gate:" + label, target), {"type": "gate", "reason": reason, **({"source": source} if source else {})})

    def seq(p, a, b, target):
        s = docs[p]
        a = s.at(a) if isinstance(a, str) else a
        b = s.at(b) - 1 if isinstance(b, str) else len(s.lines) if b is None else b
        if a > b:
            return target
        key = (p, a, b, target)
        if key in cache:
            return cache[key]
        spans.append({"file": s.name, "first": a, "last": b, "sha256": s.hash})
        # Only specifically authored readable quotes; comments/rule ledgers
        # never become dialogue merely because they were indexed.
        quote_spans = _quote_ranges().get(p, [])
        for x, y, title, private in reversed([(x, y, title, private) for x, y, title, private in quote_spans if a <= x and y <= b]):
            tail = g.sequence(s, y + 1, b, target) if y < b else target
            rows = [re.sub(r"^>\s*", "", l).replace("**", "") for l in s.lines[x - 1:y] if l.strip() not in ("", ">")]
            target = g.add(uid("document:" + p + ":" + hashlib.sha256("\n".join(rows).encode()).hexdigest()[:12]), {"type": "document", "title": title, "rows": rows, "private": private, "source": s.ref(x), "next": tail})
            b = x - 1
        result = g.sequence(s, a, b, target) if a <= b else target
        cache[key] = result
        return result

    def route(ops, target):
        for op in reversed(ops):
            kind = op[0]
            if kind == "span":
                target = seq(*op[1:], target)
            elif kind == "set":
                target = g.add(uid("state", json.dumps(op[1], sort_keys=True) + target), {"type": "stage", "direction": "", "set": op[1], "next": target})
            elif kind == "case":
                _, flag, rows, required = op
                default = gate("missing:" + flag, "Required authored choice missing: " + flag, target) if required else target
                cases = []
                for values, body in rows:
                    dest = route(body, target)
                    for value in values if isinstance(values, tuple) else (values,):
                        cases.append({"flag": flag, "equals": value, "to": dest})
                target = g.add(uid("branch:" + flag, target), {"type": "branch", "cases": cases, "default": default})
            elif kind == "any":
                dest = route(op[2], target)
                target = g.add(uid("earned-callback", target), {"type": "branch", "cases": [{"flag": f, "equals": v, "to": dest} for f, v in op[1]], "default": target})
            elif kind == "ifelse":
                _, flag, yes, no = op
                target = g.add(uid("viewed:" + flag, target), {"type": "branch", "cases": [{"flag": flag, "equals": True, "to": route(yes, target)}], "default": route(no, target)})
            elif kind == "photo-history":
                viewed = route(op[1], target)
                unseen = seq("14b3", 136, 146, target)
                target = g.add(uid("retained-first-photo"), {"type": "branch", "cases": [{"flag": "fte:" + p + ":complete", "equals": True, "to": viewed} for p in ("34", "87")], "default": unseen})
            elif kind == "menu":
                _, p, line, flag, labels, bodies = op
                title = docs[p].lines[line - 1].split("—")[-1].lstrip("# ")
                if title.startswith("선택 "):
                    title = {"4-C01": "미오가 고르는 첫 길", "4-C02": "열차를 돌려놓는 선택", "4-C03": "함께 듣는 사람이 되는 선택", "4-C04": "보여 주는 범위", "4-C05": "더 확인하고 싶은 것", "4-C06": "지도를 함께 보는 거래", "I4-C01": "지금 열어 볼 사진", "I4-C02": "수사를 마치기 전에 고르는 말", "T4-C01": "해 주지 못한 일을 보는 말"}.get(flag, "지금 할 말")
                opts = [{"id": "ABC"[i], "label": label, "to": route(body, target), "set": {flag: "ABC"[i]}} for i, (label, body) in enumerate(zip(labels, bodies))]
                target = g.add(uid("choice:" + flag), {"type": "menu", "q": title, "options": opts, "source": docs[p].ref(line)})
            elif kind == "task":
                task = tm[op[1]]
                target = g.add("v4:input:" + op[1], {"type": "task", "taskId": op[1], "runtimeReady": task["runtimeReady"], "source": task["source"], "next": target, "success": target})
            elif kind == "lie":
                _, tid, ordinary, inverted = op
                a = route(ordinary, target)
                b = route([V({"T4-LIE-B": True})] + inverted, target)
                outcomes = {"A": {"judgment": "refute", "transformed": False, "to": a, "sets": {"T4-LIE-B": False}}, "B": {"judgment": "lie", "transformed": True, "to": b, "sets": {"T4-LIE-B": True}}}
                tm[tid]["outcomes"] = outcomes
                target = g.add("v4:input:" + tid, {"type": "task", "taskId": tid, "runtimeReady": tm[tid]["runtimeReady"], "source": tm[tid]["source"], "outcomes": outcomes, "next": a, "success": a})
            elif kind == "evidence":
                target = g.add(uid("acquire:" + op[1]), {"type": "evidence", **cards[op[1]], "next": target})
            elif kind == "investigate":
                _, key, title, space, body = op
                hub = uid("investigate:" + key)
                returned = g.add(hub + ":return", {"type": "return"})
                entry = route(body, returned)
                flag = "investigation:4:" + key + ":complete"
                spot = {"id": key, "label": title, "space_id": space, "target_id": None, "geometryReady": False, "entry": entry, "returnTo": hub, "completionFlag": flag, "onReturnSet": {flag: True}, "required": True, "interactionPolicy": "authored source scope; exact source-specific geometry awaiting binding"}
                scopes.append(spot)
                target = g.add(hub, {"type": "investigate", "title": title, "spots": [spot], "requiredSpotIds": [key], "requiredCards": [], "next": target})
            elif kind == "window":
                _, name, p, line, candidates, optional = op
                opts = []
                for prefix, actor, conditions in candidates:
                    if prefix in freetime_graphs:
                        ft = freetime_graphs[prefix]
                        for nid, node in ft["nodes"].items():
                            if nid not in g.nodes:
                                g.add(nid, copy.deepcopy(node))
                        returned = {f"fte:{prefix}:complete": True, "window:" + name + ":complete": True}
                        if prefix == "88": returned["fte:29:complete"] = True
                        if prefix == "38-late": returned["fte:38:complete"] = True
                        dest = g.add(uid("call:" + name + ":" + prefix), {"type": "call", "target": ft["entry"], "returnTo": target, "onReturnSet": returned})
                    else:
                        dest = gate("meeting:" + name + ":" + prefix, "Selected exact meeting/late variant is not routed; no substitute or automatic completion.", source=docs[p].ref(line))
                    opts.append({"id": prefix, "label": actor, "requires": conditions, "to": dest})
                opts.append({"id": "continue", "label": "정해진 모임으로 간다" if optional else "각자 시간을 보낸다", "to": target, "set":{"window:"+name+":complete":True}})
                target = g.add(uid("window:" + name), {"type": "menu", "selectionRole":"freetime", "q": "개인시간 — 함께 있을 사람", "options": opts, "window": name, "oneMeetingOnly": True, "noEligibleOptions": "continue", "source": docs[p].ref(line)})
            else:
                raise ValueError("Unknown chapter4 operation " + kind)
        return target

    end = g.add("v4:4:chapter-end", {"type": "end", "chapterComplete": True, "nextChapter": "5"})
    entry = route(_daily_ops() + _investigation_ops() + _trial_ops() + _result_ops(), end)
    for n in g.nodes.values():
        if n["type"] == "task":
            n.update(trialDead=["kaede", "taiga", "ai", "yuu", "riku", "sora", "ken", "haruka"], seats=[a for a in SPEAKERS.values() if a != "lappy"], rosterSource=docs["14c1"].ref(3))
    return g.export(entry, routingStatus="authored-routes-with-explicit-binding-gates", evidenceCatalog={c["evidenceId"]: {"id": c["evidenceId"], **c} for c in cards.values()}, investigationScopes=scopes, routeRanges=spans, sourceFiles=[docs[p].name for p in SOURCE_PREFIXES], campaignReady=False, runtimeIntegrationTested=False, canonicalGuard={"fixedCulprit": "rei", "biologicalDeathBeforeFormDisappearance": True, "recordsRemainAfterDisappearance": True})


def _daily_ops():
    return [
        V({"4:livingBodies": 9, "T4-LIE-B": False}),
        ("window", "4-morning12", "14a", 5, [("38", "나나", {"fte:29:complete": True, "fte:38:complete": False}), ("37", "하루카", {"fte:34:complete": True, "fte:37:complete": False}), ("62", "아카리", {"fte:31:complete": True, "fte:39:complete": True}), ("88", "나나 — 늦은 첫 만남", {"fte:29:complete": False})], False),
        S("14a", 15, 74),
        I("fte:62:complete", True, [C("F-AK03-A", [("A1", [S("14a", 80, 96)]), ("A2", [S("14a", 98, 102)]), ("A3", [S("14a", 104, 108)])]), C("F-AK03-B", [("B1", [S("14a", 112, 116)]), ("B2", [S("14a", 118, 124)]), ("B3", [S("14a", 126, 134)])])]),
        S("14a", 135, 144), M("14a", 139, "4-C01", ["하루카와 기록 보관 쪽으로 간다", "린·레이와 승강장 쪽으로 간다", "나나가 식기를 놓는 동안 함께 있어도 되는지 묻는다"], [[S("14a", 146, 166)], [S("14a", 168, 186)], [S("14a", 188, 206)]]), S("14a", 209, 426),
        S("14a2", 5, 186), M("14a2", 181, "4-C02", ["린에게 손잡이를 직접 만져 봐도 되는지 묻는다", "다른 사람들이 움직이는 모습을 본다", "실제 장소와 다른 부분을 찾는다"], [[S("14a2", 188, 200)], [S("14a2", 202, 212)], [S("14a2", 214, 226)]]),
        S("14a2", 229, 416), S("80", 5, 358), S("14a2", 419, 450), S("14a3", 5, 278),
        S("14a4", 5, 194), M("14a4", 189, "4-C03", ["로비에서 린·레이·쇼와 도면을 본다", "하루카와 열람실로 걷는다", "코토에게 답을 대신 닫은 이유를 묻는다"], [[S("14a4", 196, 214)], [S("14a4", 216, 230)], [S("14a4", 232, 250)]]),
        S("14a4", 253, 266), S("106", 5, 134), M("106", 135, "4-C08", ["린의 낮은 탑이 더 좋아 보인다고 편든다", "두 장으로 경쟁에 들어간다", "높이 승부를 끝내고 바꿔 세워 보자고 한다"], [[S("106", 138, 170)], [S("106", 172, 212)], [S("106", 214, 250)]]),
        S("106", 253, 320), S("14a4", 269, 374), S("106", 323, 328), C("4-C08", [("A", [S("106", 330, 342)]), ("B", [S("106", 344, 358)]), ("C", [S("106", 360, 374)])]), S("106", 375, None), S("14a4", 377, 436),
        S("14a5", 5, 54), M("14a5", 49, "4-C04", ["낡은 기록을 앞뒤까지 보여 준다", "해당 문장만 먼저 읽어 준다", "지금은 옛 기록을 보여 주고 싶지 않다고 말한다"], [[S("14a5", 56, 68)], [S("14a5", 70, 82)], [S("14a5", 84, 102)]]),
        S("14a5", 105, 242),
        ("window", "4-early13", "14a5", 243, [("38-late", "나나 — 늦은 두 번째 만남", {"fte:88:complete": True, "fte:38:complete": False})], True), S("14a5", 247, 262),
        S("14a6", 5, 192), C("4-C04", [("C", [S("14a6", 194, 196)]), (("A", "B"), [S("14a6", 198, 200)])]), S("14a6", 202, 362),
        C("4-C04", [("C", [S("14a6", 364, 370)]), (("A", "B"), [S("14a6", 372, 378)])]), S("14a6", 379, 392),
        S("14a7", 5, 60), C("4-C04", [("C", [S("14a7", 62, 70)]), (("A", "B"), [S("14a7", 72, 76)])]), S("14a7", 77, 338),
        S("124", 5, 108), M("124", 103, "4-C09", ["하루카가 살아 있기를 원한다고 말한다", "자신도 하루카가 무섭다고 인정한다", "레이를 감싸는 일까지 부탁하지는 말라고 한다"], [[S("124", 110, 128)], [S("124", 130, 144)], [S("124", 146, 166)]]), S("14a7", 341, 536),
        S("127", 5, 36), M("127", 31, "4-C10", ["오늘 아침 기억을 흐려 달라고 부탁한다", "힘든 기억을 지워 달라고 하면 해 주는지 묻는다", "그 부탁은 하지 않고 함께 걸어 달라고 한다"], [[S("127", 37, 68)], [S("127", 69, 96)], [S("127", 97, 118)]]),
        S("127", 121, 124), C("4-C10", [("A", [S("127", 126, 128)]), ("B", [S("127", 130, 132)]), ("C", [S("127", 134, 136)])]), S("127", 138, 140),
        S("14a8", 5, 105), M("14a8", 100, "4-C05", ["어디까지 들리는지 더 확인하고 싶다", "직접 확인하고 싶어졌다고 인정한다", "오늘은 설명해 준 범위만 듣는다"], [[S("14a8", 107, 117)], [S("14a8", 119, 127)], [S("14a8", 129, 135)]]),
        S("14a8", 138, 251), S("134", 5, 188), S("14a8", 254, 269), S("174", 5, 78), M("174", 77, "W4-C01", ["천을 집어 마저 닦으려 한다", "어느 쪽 얼룩인지 다시 맞혀 보자고 한다", "더 손대지 않고 앉는다"], [[S("174", 80, 108)], [S("174", 110, 158)], [S("174", 160, 186)]]), S("174", 187, None), S("14a8", 272, 325),
        ("window", "4-afternoon13", "14a8", 326, [("57", "나나", {"fte:29:complete": True, "fte:38:complete": True}), ("64", "하루카", {"fte:34:complete": True, "fte:37:complete": True})], False),
        *_late_daily_ops(),
    ]


def _late_daily_ops():
    return [
        S("14a9", 5, 50), M("14a9", 45, "4-C06", ["인쇄 도면과 주석을 나눠 공용 사본을 만든다", "물품 정리를 돕고 원본을 빌린다", "그 거래에는 참여하지 않는다"], [[S("14a9", 52, 114)], [S("14a9", 116, 192)], [S("14a9", 194, 234)]]),
        S("14a9", 237, 252), I("fte:64:complete", True, [C("F-HA03-A", [("A1", [S("14a9", 258, 262)]), ("A2", [S("14a9", 264, 268)]), ("A3", [S("14a9", 270, 274)])]), C("F-HA03-B", [("B1", [S("14a9", 278, 282)]), ("B2", [S("14a9", 284, 288)]), ("B3", [S("14a9", 290, 296)])])]),
        S("14a9", 297, 326), S("178", 6, 165), M("178", 164, "W4-C12", ["하루카가 말한 위치를 직접 되묻는다", "자기가 받치겠다고 한다", "가까운 레이가 계속 받치면 된다고 한다"], [[S("178", 167, 189)], [S("178", 191, 215)], [S("178", 217, 249)]]), S("178", 250, 329),
        S("14a9", 329, 356), I("fte:56:complete", True, [C("SHO-03B", [("B1", [S("14a9", 362, 374)]), ("B2", [S("14a9", 376, 388)]), ("B3", [S("14a9", 390, 398)])]), C("SHO-03A", [("A1", [S("14a9", 402, 404)]), ("A2", [S("14a9", 406, 408)]), ("A3", [S("14a9", 410, 412)])]), S("14a9", 414, 416)]),
        S("14a9", 417, 470), S("142", 5, 60), M("142", 59, "4-C11", ["레이를 적는다", "코토를 적는다", "빈 종이로 낸다"], [[S("142", 62, 68)], [S("142", 70, 76)], [S("142", 78, 84)]]), S("142", 87, 90),
        C("4-C11", [("A", [S("142", 92, 94)]), ("B", [S("142", 96, 98)]), ("C", [S("142", 100, 102)])]), S("142", 104, 228), S("14a9", 473, 746),
        I("fte:57:complete", True, [C("F-NA03-A", [("A1", [S("14a9", 752, 762)]), ("A2", [S("14a9", 764, 776)]), ("A3", [S("14a9", 778, 788)])]), C("F-NA03-B", [("B1", [S("14a9", 792, 794)]), ("B2", [S("14a9", 796, 798)]), ("B3", [S("14a9", 800, 802)])]), S("14a9", 804, 806)]),
        S("14a9", 807, 818), S("14a10", 5, 52), I("fte:58:complete", True, [C("F-RE03-A", [("A1", [S("14a10", 58, 66)]), ("A2", [S("14a10", 68, 76)]), ("A3", [S("14a10", 78, 88)])]), C("F-RE03-B", [("B1", [S("14a10", 92, 94)]), ("B2", [S("14a10", 96, 98)]), ("B3", [S("14a10", 100, 102)])]), S("14a10", 104, 106)]), S("14a10", 107, 294),
        S("14a11", 5, 158), S("71", 5, 76), M("71", 75, "4-C07", ["서명한 사람의 요청이라는 제목으로 바꾼다", "다 같이 고칠 초안이라는 말에 동의하고 서명한다", "이름은 쓰지 않고 초안으로 둔다"], [[S("71", 78, 92)], [S("71", 94, 108)], [S("71", 110, 124)]]), S("71", 125, 138),
        V({"viewpoint": "objective"}), S("14a11", 161, 330), V({"viewpoint": "mio"}), S("14a11", 331, 396),
        S("71", 141, 150), C("4-C07", [("A", [S("71", 152, 164)]), ("B", [S("71", 166, 182)]), ("C", [S("71", 184, 202)])]), S("71", 203, 244), C("4-C07", [("A", [S("71", 246, 248)]), ("B", [S("71", 250, 260)]), ("C", [S("71", 262, 268)])]),
        S("14a11", 399, 674), S("14a12", 5, 382), S("14a13", 5, 88), V({"4:rewind-used": True}), S("14a13", 89, 178), V({"4:livingBodies": 8, "4:biologically-dead": True, "4:form-remains": True}), S("85", 5, 154), S("14a13", 181, 218),
    ]


def _photo_history_ops():
    # The ordinary first meeting (34) and its late variant (87) share the same
    # source choices. B3 never restores the deleted image. No first meeting
    # means the actual common performance photo, not a fabricated portrait.
    selected = [C("F-HA01-B", [("B2", [S("14b3", 100, 110)]), ("B1", [C("F-HA01-A", [("A1", [S("14b3", 100, 110)]), ("A2", [S("14b3", 112, 122)]), ("A3", [S("14b3", 124, 134)])])]), ("B3", [S("14b3", 136, 146)])])]
    return [("photo-history", selected)]


def _investigation_ops():
    return [
        S("14b1", 5, 18),
        H("I4-02-file", "사망 파일과 남아 있는 형체", "inspection_hall_changed", [S("14b1", 19, 44), E("death-file"), E("life-vs-form")]),
        H("I4-04-fastening", "외부 고정과 개방 전 손", "inspection_hall_changed", [S("14b1", 45, 68), E("external-fastening"), E("first-hand")]),
        H("I4-06-rewind", "아카리만 기억하는 마지막 접근", "inspection_hall_changed", [S("14b1", 69, 104), E("rewind-scope"), E("injury-order")]),
        H("I4-09-rear", "안쪽 문과 실제 외벽", "inspection_hall_changed", [S("14b1", 105, 138), E("no-rear-exit")]),
        S("14b1", 139, 162), E("old-record"),
        H("I4-14-observers", "컵을 받은 생존과 입구 관찰", "inspection_hall_changed", [S("14b1", 163, 268), E("last-alive"), E("late-company"), E("entry-observers")]),
        H("I4-19-locations", "다른 사람들의 실제 위치", "inspection_hall_changed", [S("14b2", 5, 58)]),
        H("I4-23-light", "그림자와 햇빛 아래 본체", "inspection_hall_normal", [S("14b2", 59, 124), E("shadow-light")]),
        H("I4-28-routes", "물길과 남아 있을 수 있었던 구간", "inspection_hall_changed", [S("14b2", 125, 166), E("pipe-boundary"), E("creation-rule")]),
        H("I4-31-testimony", "닫고 고정한 사람의 현재 진술", "inspection_hall_changed", [S("14b2", 167, 200), S("14b3", 5, 68), E("rei-close"), E("rear-answer")]),
        S("14b3", 69, 86), M("14b3", 81, "I4-C01", ["장소 사진부터 함께 확인한다", "남아 있는 평소 사진도 잠깐 본다", "린에게 장소 사진을 먼저 봐 달라고 한다"], [[S("14b3", 88, 94)], [S("14b3", 96, 98), *_photo_history_ops(), S("14b3", 148, 154)], [S("14b3", 156, 190)]]),
        H("I4-40-photos", "실제로 읽힌 두 장소 사진", "inspection_hall_changed", [S("14b3", 193, 222), E("photo-comparison"), E("closed-photo")]),
        H("I4-43-meeting", "기다릴 조건과 실제 면담 선택", "inspection_hall_changed", [S("14b3", 223, 308), E("waiting-request")]),
        H("I4-49-capability", "외부 고정과 감각 강화의 한계", "inspection_hall_changed", [S("14b4", 5, 106), E("sense-range")]),
        S("14b4", 107, 114), M("14b4", 109, "I4-C02", ["하루카가 요청했던 조건부터 말한다", "레이의 인정과 주장도 공유한다", "나나에게 관찰 정리를 부탁한다"], [[S("14b4", 116, 120)], [S("14b4", 122, 126)], [S("14b4", 128, 168)]]), S("14b4", 171, 260),
    ]


def _trial_ops():
    return [
        S("14c1", 5, 248), T("T4-NS-01"), S("14c1", 250, 346),
        ("lie", "T4-LIE-01", [S("169", 162, 166)], [S("169", 168, 213)]), S("14c1", 349, 384), T("T4-PN-01"), S("14c1", 387, 498), T("T4-MM-01"), S("14c1", 500, 510),
        S("99", 5, 108), M("99", 105, "T4-C02", ["사진과 직접 열어 본 장소를 나눈다", "보호 기록을 진실 보증에서 뺀다", "퇴실 판단을 무엇으로 확인했는지 묻는다"], [[S("99", 110, 124)], [S("99", 126, 144)], [S("99", 146, 164)]]), S("99", 167, 272),
        S("14c1", 513, 534), S("77", 5, 162), S("14c1", 537, 550), T("T4-RL-01"), S("14c1", 552, 560),
        S("14c2", 5, 14), S("131", 5, 20), C("T4-LIE-B", [(False, [S("131", 22, 28)]), (True, [S("131", 30, 36)])]), S("131", 38, 234), C("T4-LIE-B", [(False, [S("131", 236, 238)]), (True, [S("131", 240, 242)])]), S("131", 244, 262),
        S("14c2", 17, 22), T("T4-RS-01"), S("14c2", 25, 46), M("14c2", 41, "T4-C01", ["구조 접근과 그전 갇힌 시간을 나눈다", "대응 가능성을 인정하며 원인 행위를 묻는다", "구조자에게 책임 돌리는 말을 취소하라고 요구한다"], [[S("14c2", 48, 100)], [S("14c2", 102, 154)], [S("14c2", 156, 186)]]),
        T("T4-SD-01"), S("14c2", 193, 304), T("T4-FA-01"), S("14c2", 306, 330),
        S("114", 5, 130), ("ifelse", "fte:64:complete", [S("114", 132, 140)], [S("114", 142, 148)]), S("114", 151, 226), S("192", 5, None), S("14c2", 333, 516),
        S("14c3", 5, 494), T("T4-AA-01"), S("14c3", 583, 694), S("160", 7, 20), T("T4-MG-01"), S("160", 231, 260), T("T4-VOTE-01"), S("14c3", 697, 874),
    ]


def _result_ops():
    return [
        S("14d", 5, 94), V({"4:livingBodies": 7, "4:form-remains": False, "4:origin-belief-restored": True, "4:independent-erasure-restored": False}), S("14d", 95, 150),
        C("T4-C02", [("A", [S("99", 280, 288)]), ("B", [S("99", 290, 302)]), ("C", [S("99", 304, 316)])]), S("14d", 153, 476), I("T4-LIE-B", True, [S("169", 218, 227)]),
        I("fte:58:complete", True, [C("F-RE03-B", [("B1", [S("14d", 484, 512)]), ("B2", [S("14d", 514, 520)]), ("B3", [S("14d", 522, 528)])]), I("F-RE02-B", "B1", [S("14d", 530, 536)]), S("14d", 538, 540)]),
        S("178", 332, 343), C("W4-C12", [("A", [S("178", 345, 347)]), ("B", [S("178", 349, 351)]), ("C", [S("178", 353, 355)])]), S("178", 357, 381),
        S("14d", 543, 630), C("4-C09", [("A", [S("124", 174, 176)]), ("B", [S("124", 178, 180)]), ("C", [S("124", 182, 184)])]), S("14d", 633, 650),
        C("4-C07", [("A", [S("14d", 652, 656)]), ("B", [S("14d", 658, 664)]), ("C", [S("14d", 666, 672)])]),
        C("4-C11", [("A", [S("142", 238, 248)]), ("B", [S("142", 250, 262)]), ("C", [S("142", 264, 274)])]), S("142", 276, 288), S("14d", 677, 692),
    ]


def _quote_ranges():
    return {}


def _evidence(docs):
    rows = [
        ("death-file", "익사 사인과 별도 손상", "사건 파일의 피해자는 하루카이며 주사인은 익사다. 머리·손 손상과 구조 뒤 생존 징후 및 이후 사망 경과는 별도다. 사망 확인 순간은 최초 가해 순간이 아니다.", "14b1", 31),
        ("life-vs-form", "생물학적 사망과 형체 유지", "생명 정지와 생성 형체 소멸은 다르다. 지금 시신은 남아 있고 생성자는 살아 있다. 생성자 사망 때 잔여 생성 단위는 소멸하지만 현재의 사진과 별도 물건은 함께 지워지지 않는다.", "14b1", 43),
        ("external-fastening", "점검구 외부 고정 구조", "덮개를 내리는 것과 밖에서 고정하는 것은 다른 동작이다. 정상 점검에서 안쪽 손으로 외부 고정에 닿지 못함을 확인했고 구조 때 풀어야 열렸다.", "14b1", 55),
        ("first-hand", "개방 전 손 관찰", "최초 미오·나나가 닫힌 덮개 가장자리의 손을 봤다. 쇼·아카리는 뒤에 불려 와 개방 전에 확인했다. 처음 상태를 찍은 사진은 없고 뒤의 열린 사진이 이를 대신하지 않는다.", "14b1", 67),
        ("rewind-scope", "구조 때 실제10초 범위", "아카리가 합류한 뒤의 마지막 접근10초를 되감았다. 최초 고정과 물속에 갇힌 상태는 그전이다. 첫 접근의 나나 팔 손상은 최종 시간선에 없고 그 구간은 아카리만 기억한다.", "14b1", 91),
        ("injury-order", "손상 발생 순서의 한계", "이마의 손상은 실제다. 물에 빠질 때 충돌인지 다른 충격인지 쇼는 정확한 동작을 못 골랐다. 머리 상처 하나가 파일의 익사를 지우거나 공격 순서를 확정하지 않는다.", "14b1", 103),
        ("no-rear-exit", "안쪽 문과 실제 외벽", "안쪽 문 뒤는 막힌 수납 구획이다. 원래 높은 설비창과 외벽, 실제 하나의 출입구는 새 방과 구별된다. 이 단계에서 미확인 배관 전체를 완료로 단정하지 않았다.", "14b1", 137),
        ("old-record", "원래 도면과14일차 보호 기록", "공용 원도면과 미오의14일차 보호 손글씨는 정상 홀을 기록한다. 보호 글은 믿고 쓴 내용을 보존하며 혼자 진실을 판정하지 않는다. 젖은 카메라 사진은 아직 읽지 않은 단계와 구별한다.", "14b1", 161),
        ("last-alive", "마지막 직접 생존과 응답", "컵을 받는 모습을 미오·나나·아카리가 각각 봤다. 뒤의 실제 생존 음성은 미오·나나가 들었고 아카리는 그때 햇빛 아래 벤치에 있었다. 한 사람의 전 구간 관찰이 아니다.", "14b1", 235),
        ("late-company", "린의 사망 순간 동행", "레이 퇴실 뒤 린과 동행한 것은 실제다. 구조 뒤 사망 순간 함께 있었다는 관찰이 앞선 방 안에서의 행위를 직접 본 알리바이는 아니다.", "14b1", 267),
        ("entry-observers", "진입 뒤 앞쪽 관찰", "면담 중 미오·나나의 입구 관찰과 두 사람이 들어간 뒤 아카리·사츠키의 앞쪽 관찰은 순서와 범위가 다르다. 린이 대기 전체를 본 것으로 늘리지 않는다.", "14b1", 235),
        ("shadow-light", "사츠키 본체의 광조건", "기본 그림자는 물건을 못 잡고100%는 잡을 수 있으나 본체가 빛 아래면 유지 불가다. 래피의 기능 확인과 아카리의 햇빛 아래 벤치 목격을 구별한다.", "14b2", 123),
        ("pipe-boundary", "실제로 맞춘 물길과 개구부", "표시된 배관·망·외벽 연결과 현재 보이는 부속을 대조했다. 지금 본 연결은 사람 통로가 아니며 설비 전체를 새로 분해했다고 보고하지 않는다.", "14b2", 150),
        ("creation-rule", "생성의 친숙함과 기록 보존", "생성은 비어 있던 부피에 새 구조를 놓고 원래부터라는 믿음을 일으킨다. 원래 외벽을 지우거나 물리 사진·도면을 소급 수정하지 않는다. 현재 눈앞의 막힌 벽을 통과하게 하지 않는다.", "14b2", 165),
        ("rei-close", "레이의 개폐·고정 진술", "레이는 덮개를 닫고 밖에서 고정했다고 직접 말했다. 아직 손을 알고 봤다는 인정은 아니며 나갔다고 생각했다는 설명을 검토해야 한다.", "14b3", 68),
        ("rear-answer", "안쪽 문 재확인 문답", "미오가 그 안쪽 문으로 나갔다는 뜻이냐고 직접 재확인했고 레이는 그렇다고 답했다. 단순히 뒤쪽이라는 애매한 말만 있었던 것으로 바꾸지 않는다.", "14b3", 54),
        ("photo-comparison", "원도면과 두 장소 사진의 출구 대조", "장치에서 실제 읽힌13일차 정상 홀 사진과15일차 새 공간 사진을 미오도 공통 비교에서 직접 봤다. 안쪽 구획 내부는 사진에 없다. 공용 도면·보호 글·직접 개방은 다른 출처다.", "14b3", 222),
        ("closed-photo", "면담 전 닫힌 덮개 사진", "면담 전 사진에는 닫힌 덮개면이 실제로 찍혀 있다. 최초 손 발견 사진이나 공격 사진이 아니며 안쪽 수납 구획 내부까지 찍히지 않았다.", "14b3", 212),
        ("waiting-request", "응답 없을 때의 진입 요청", "하루카는 나왔다는 말만 믿지 말고 응답이 없으면 확인해 달라고 요청했다. 스스로 면담에 들어갔다는 사실이 외부 고정이나 살해의 포괄 동의가 되지 않는다.", "14b3", 308),
        ("sense-range", "하루카 감각 강화 범위", "기본은 고른 감각 하나,100%는 두 감각 강화다. 물체를 원격 조작하거나 신체를 늘이는 기능이 붙지 않는다. 감각으로 안다고 외부 고정을 움직이지는 못한다.", "14b4", 106),
    ]
    return {key: {"evidenceId": "v4:4:knowledge:" + key, "name": name, "text": text, "knowledgeOnly": True, "revision": False, "source": docs[p].ref(line)} for key, name, text, p, line in rows}


def _bind_additional(tm, cards):
    bind = {"T4-NS-A01": "late-company", "T4-NS-A02": "death-file", "T4-NS-A03": "death-file", "T4-NS-A04": "external-fastening", "T4-NS-A05": "sense-range", "T4-NS-A06": "first-hand", "T4-NS-A07": "rear-answer", "T4-NS-A08": "creation-rule", "T4-NS-A09": "shadow-light", "T4-NS-A10": "rewind-scope", "T4-EVIDENCE-A01": "photo-comparison", "T4-PN-A02": "injury-order", "T4-PN-A03": "entry-observers", "T4-RS-A02": "photo-comparison", "T4-RS-A03": "waiting-request"}
    for tid, key in bind.items():
        task = tm[tid]
        task.update(answerEvidenceId=cards[key]["evidenceId"], requiresEvidence=[cards[key]["evidenceId"]], evidencePool="actually-acquired-v4-cards-only")
        task["bindings"] = [b for b in task["bindings"] if b["kind"] != "evidenceAcquisition"]
        task["runtimeReady"] = not any(b.get("required") for b in task["bindings"])


def _baseline_tasks(tm, docs):
    def events(p, a, b): return [e for e in docs[p].paragraphs(a, b) if e["type"] in ("say", "stage")]
    def says(p, a, b): return [e for e in events(p, a, b) if e["type"] == "say"]
    def make(tid, kind, p, line, **fields):
        ref = docs[p].ref(line)
        title = ref["heading"].split(" ", 1)[-1].split(" — ", 1)[0]
        tm[tid] = {"id": tid, "kind": kind, "chapter": "4", "sourceKind": "BASELINE", "source": ref, "title": title, "prompt": title, "intro": [], "lines": [], "wrong": [], "success": [], "bindings": [], "return": {"graphNext": True}, "runtimeReady": True, "retry": {"sameTask": True, "preserveEvidence": True, "preservePublicFacts": True, "cancellationIsSuccess": False}, **fields}
        return tm[tid]
    for tid, kind, a, b, weakness, key, wrongs, success in (
        ("T4-NS-01", "nonstop", 5, 34, "고정까지 저절로", "external-fastening", [(35, 40), (41, 48)], (49, 60)),
        ("T4-PN-01", "panic", 61, 76, "처음까지 아카리가 만든 결과", "rewind-scope", [(77, 82), (83, 90)], (91, 104)),
        ("T4-RS-01", "showdown", 182, 201, "그대로 채택", "photo-comparison", [(202, 207), (208, 215)], (216, 225)),
    ):
        lines = says("166", a, b)
        target = next(e for e in lines if weakness in e["text"])
        make(tid, kind, "166", a, lines=lines, intro=[e for e in events("166", a, b) if e["type"] == "stage"], targets=[{"lineId": target["id"], "word": weakness, "actor": target["actor"], "verdict": "refute"}], answerEvidenceId="v4:4:knowledge:" + key, requiresEvidence=["v4:4:knowledge:" + key], evidencePool="actually-acquired-v4-cards-only", judgment="refute", wrongVariants=[{"cause": f"source-wrong-{i}", "script": events("166", x, y)} for i, (x, y) in enumerate(wrongs, 1)], success=events("166", *success))
    tm["T4-PN-01"]["lanes"] = [{"id": slot, "actor": actor, "lines": [e["id"] for e in tm["T4-PN-01"]["lines"] if e["actor"] == actor]} for slot, actor in (("왼쪽", "koto"), ("가운데", "akari"), ("오른쪽", "nana"))]
    tm["T4-PN-01"]["laneLayoutPolicy"] = "authored first-speaker order; layout does not assert new witness facts"
    make("T4-MM-01", "mindmine", "166", 105, regionDescription="막힌 수납 구획과 그 뒤 기존 외벽", imageDescription="공용 도면/14일차 보호 기록/두 장소 사진/직접 본 수납 구획의 대조", wrongVariants=[{"cause": "wrong-region:" + k, "script": events("166", a, b)} for k, a, b in (("A", 118, 121), ("C", 122, 125), ("D", 126, 131))], success=events("166", 132, 137), bindings=[{"kind": "forensicImageRegions", "required": True, "description": "Bind actually inspected rear compartment and original exterior-wall polygons, not option-index coordinates."}], runtimeReady=False)
    questions = []
    for no, (a, b, answer, prompt) in enumerate(((142, 163, "B", "다음으로 무엇을 물어야 할까?"), (164, 181, "C", "지금 하지 말아야 할 비약은?")), 1):
        opts = [{"id": m[1], "label": m[2]} for l in docs["166"].lines[a - 1:b] if (m := re.match(r"^- ([ABC]) (.+)$", l))]
        heads = [(i, m[1]) for i in range(a, b + 1) if (m := re.match(r"^\*\*([ABC](?:/[ABC])?) — (?:정답|오답)", docs["166"].lines[i - 1]))]
        scripts = {}
        for ix, (line, keys) in enumerate(heads):
            script = events("166", line + 1, heads[ix + 1][0] - 1 if ix + 1 < len(heads) else b)
            for k in keys.split("/"): scripts[k] = script
        questions.append({"id": f"T4-RL-01:link:{no}", "q": prompt, "options": opts, "answer": answer, "success": scripts[answer], "wrongVariants": [{"optionId": k, "script": v} for k, v in scripts.items() if k != answer], "retryPolicy": "currentLinkOnly", "source": docs["166"].ref(a)})
    make("T4-RL-01", "reasoning", "166", 138, questions=questions)

    lie = make("T4-LIE-01", "nonstop", "169", 140, lines=says("169", 144, 150), answerEvidenceId="v4:4:knowledge:first-hand", requiresEvidence=["v4:4:knowledge:first-hand"], evidencePool="actually-acquired-v4-cards-only", judgment="refute-or-intentional-lie", wrong=events("169", 154, 160))
    last = lie["lines"][-1]
    lie["targets"] = [{"lineId": last["id"], "word": word, "actor": "koto", "verdict": verdict} for word, verdict in (("자료도 없는 거지", "refute"), ("사진이 없으면", "lie"))]
    lie["transformation"] = {"sourceEvidenceId": "v4:4:knowledge:first-hand", "normalLabel": "최초 손 사진 없음/각자의 직접 관찰 있음", "lieLabel": "최초 손 사진 있음", "intentionalHold": True, "changesHistoricalFacts": False, "createsPhoto": False}

    pairs = []
    for ix, (a, b, them, us) in enumerate(((232, 245, "rei", "mio"), (246, 259, "koto", "akari"), (260, 277, "nana", "sho"), (278, 291, "satsuki", "rin")), 1):
        raw = docs["166"].lines[a + 1]
        quote = re.search(r"「(.+)」", raw)[1]
        keyword = re.search(r"\*\*(.+?)\*\*", quote)[1]
        wrong = next(i for i in range(a, b + 1) if docs["166"].lines[i - 1].startswith("**오답"))
        reply = says("166", a, wrong - 1)[0]
        pairs.append({"id": f"T4-SD-01:round:{ix}", "them": them, "themText": quote.replace("**", ""), "keyword": keyword, "us": us, "usText": reply["text"], "responseKeyword": re.findall(r"\*\*(.+?)\*\*", docs["166"].lines[a + 3])[-1].rsplit("/", 1)[0].strip(), "success": events("166", reply["source"]["line"], wrong - 1), "wrong": events("166", wrong + 1, b), "source": docs["166"].ref(a)})
    make("T4-SD-01", "scrum", "166", 226, intro=events("166", 229, 231), pairs=pairs, teams={"us": ["mio", "rin", "akari", "sho"], "them": ["rei", "nana", "koto", "satsuki"]}, teamMeaning="current causal questions, not loyalty or innocence", success=events("166", 292, 299))
    make("T4-FA-01", "anagram", "166", 300, intro=says("166", 304, 304), answer="형체유지", answerGlyphs=list("형체유지"), distractorDescription="생/존/회/복", mechanic={"selectGlyphCount": 1, "arrivalJudgment": True, "poolSlots": 20, "specialCollectibleSeparate": True}, success=events("166", 314, None), retryPolicy="wrongSlotOnly", editorialMechanicCorrection="REA single glyph selection and arrival judgment; same-glyph-pair manuscript wording is not an executable rule")
    make("T4-AA-01", "armament", "14c3", 495, waves=[{"id": f"T4-AA-01:wave:{i}", "script": events("14c3", a, b), "retryPolicy": "sameWave"} for i, (a, b) in enumerate(((501, 516), (517, 532), (533, 548)), 1)], answerParts=["살아 있는 줄", "알고도", "덮개를", "고정했다"], fixedSubject="레이는 하루카가", distractors=["이미 죽은 줄", "모르고", "사진을", "사라지게 했다"], wrongVariants=[{"cause": "wrong-knowledge", "script": events("14c3", 551, 556)}, {"cause": "wrong-object-or-action", "script": events("14c3", 557, 562)}, {"cause": "wrong-order", "script": events("14c3", 563, 568)}], success=events("14c3", 569, 582), bindings=[{"kind": "rhythmWaveTiming", "required": True, "description": "Bind authored three waves to actual beat windows and native input. Never auto-advance successful responses."}], runtimeReady=False)
    slots = []
    for no, (a, b, answer) in enumerate(((21, 54, "1C"), (55, 90, "2A"), (91, 126, "3B"), (127, 158, "4C"), (159, 194, "5A"), (195, 230, "6B")), 1):
        candidates = [{"id": m[1], "imageDescription": m[2]} for l in docs["160"].lines[a - 1:b] if (m := re.match(r"^\|([1-6][ABC])\|([^|]+)\|(?:정답|오답)\|", l))]
        heads = [(i, m[1]) for i in range(a, b + 1) if (m := re.match(r"^### ([1-6][ABC])를 놓았다", docs["160"].lines[i - 1]))]
        responses = {k: events("160", line + 1, heads[ix + 1][0] - 1 if ix + 1 < len(heads) else b) for ix, (line, k) in enumerate(heads)}
        slots.append({"id": f"T4-MG-01:slot:{no}", "candidates": candidates, "answer": answer, "wrong": {k: v for k, v in responses.items() if k != answer}, "success": responses[answer], "retryPolicy": "currentSlotOnly", "source": docs["160"].ref(a)})
    make("T4-MG-01", "climax", "160", 21, slots=slots, bindings=[{"kind": "authoredComicPanels", "required": True, "description": "Bind all18 exact authored candidate panels; a text list is not the finished reconstruction mechanic."}], runtimeReady=False)
    make("T4-VOTE-01", "vote", "14c3", 697, answer="rei", candidates=["mio", "rei", "sora", "ken", "nana", "riku", "akari", "yuu", "koto", "satsuki", "taiga", "rin", "sho", "ai", "haruka", "kaede"], deadCandidatesSelectable=True, finalVote=True, authoredResult={"total": 8, "rei": 7, "koto": 1, "otherVoteOwnerRevealedOnlyAfterResult": True})


REVIEWED_SOURCE_HASHES = {
    "14a_4장_일상_초고.md": "89937179f250e4bf5bb286e835328b92b3b2ca2a56da270fb260d052187cf444",
    "14a2_4장_작은_공원_초고.md": "124b765023f47f8d788a9a7661984573cc77823482d11c7b50c6d61cd6bc813e",
    "14a3_4장_없어진_받침_초고.md": "a685c4ceeb80a98543c19e01a11d09f4a5158834547ea01daf154d05b38e945c",
    "14a4_4장_함께_있을_조건_초고.md": "981e913f8b73f7da4ebb2508a2f69cfcb1f871097e0f2a3063dd18a5afb8bfac",
    "14a5_4장_읽었다는_대답_초고.md": "42ae50f06869c5fabdbc41e8a4e5016a9c9778f1dcc9cdbd61e68269c615a59c",
    "14a6_4장_만든_사람_초고.md": "b86570b8a913a72b090175b1d7046885cb4c5918cc624ba02c904385353b9c18",
    "14a7_4장_내가_먼저_말할게_초고.md": "ed45602afa5cfc0c72a8eb7eac84bcf4e7f230728da4113346c55d4f6561b524",
    "14a8_4장_같이_확인한_바닥_초고.md": "f6b0bd840396abb8d64694615abb71ee69b07f4a4533319824be10850fb8ce3b",
    "14a9_4장_길을_가진_사람_초고.md": "765c6b35c6bb92011129ead820abd089f96b9a4c7c426b8f8e685abc3b5d04cb",
    "14a10_4장_밖으로_가져갈_것_초고.md": "f6479185ff87a9b7fd33acc04d14dd8e0efc7ec46893db950c3d90731741277d",
    "14a11_4장_조건이_남은_손_초고.md": "f796889b58ab1174091ad316bfddf2ce031eb33a29d7a58af7779d66a6ba92e0",
    "14a12_4장_어제와_다른_방_초고.md": "6f685f0253b09d5d0077f7657c4a19ebb20beaeefc7e5fea42a650dd467d4c4b",
    "14a13_4장_문을_연_뒤_초고.md": "573365e0a765107c084286e79e9058c7ec77004f47975deedac220ba96155885",
    "14b1_4장_첫_수사_초고.md": "3f15d267d63e3590b86548b34476a8a930fc19bccc8b795d971ec87d1c889242",
    "14b2_4장_입구와_햇빛_초고.md": "47b13067ba33ee4fa88b5121946b403150f20db7838f53ad5f5168b66111bb3e",
    "14b3_4장_사진을_보는_사람_초고.md": "0b07d49b5e9bb0bbcd1133ff7248244beb4fde975a794967105aded8bedae8e8",
    "14b4_4장_조사에서_남긴_말_초고.md": "ca2c42752f0ca48a383ea061e7274d7fc51cd6450c38a412f95a04d42f0373a8",
    "14c1_4장_재판_죽은_시간_초고.md": "6f2bb49395049c594780dad1d299dfe5705dd98ac817233886f4910910cd4a12",
    "14c2_4장_재판_남겨_두고_싶은_것_초고.md": "036d77c3c961c028e73dc8620f5604696222a060c0b39967477df570596a9b6a",
    "14c3_4장_재판_남의_선택을_닫은_사람_초고.md": "ca5c63b0f1b3e97c4c848515e3e13ba76c6e77bab079e5b66fc9cbdd0519746b",
    "14d_4장_결과와_남은_기록_초고.md": "99e15f26d3109db8db84dbb72019c54f7aec49a4b1de9430ee0b3e7338057383",
    "08_4장_생성과_기억_경계_스포주의.md": "faf951f9806aec860e957a8816f0f65661e34a8cddec890b3f02c9b58f133142",
    "09_4장_사건원장_스포주의.md": "22ca833fe276b36c2a36a1f357500181f6e6a400aa641b167add7187d10a8eb2",
    "80_4장_손님으로_온_하루_보강.md": "675e9801b86dde09e1cebdfb93bafdd3ccf99e018ea11b64ad3e65313035da94",
    "106_4장_일등을_세우는_손_보강.md": "a59721de82224d000751e8e3d136aec17573e3c34e6a254b54e5840677c50fbd",
    "124_4장_씹고_있는_동안에는_보강.md": "a7d1b917aecd83707a4d316e6fb4198a9076b9c69a6aec3b983eb412d847cd67",
    "127_4장_잠깐만_몰랐으면_보강.md": "cfadeb6b34c15e09e73e513e03093950a0f03d9b7dc93e80936d371900593e8e",
    "134_4장_같이_들고_가는_사람_보강.md": "64fc1cf127aa1e2847958a05c33aa99bc927dcaa7414d94bafbc392f853b6407",
    "174_4장_쉬는_사람의_손_연속대본.md": "0e4378df059c20663727823c182db9d22a92b7694eefef1733719becf9761fde",
    "178_4장_문을_열_사람의_등_연속대본.md": "44ff30db7360e896c45777020a9a81e2e3e6d56a85d87306c91ca48333901ad1",
    "142_4장_접어서_내놓은_이름_보강.md": "51af1ae8f98d842f4400eb7d24033f5d394fd8647ee860175de32527e1f7ebdd",
    "71_4장_아홉_사람의_이름_보강.md": "ac56164d4bd817da0619a077acd8176c568c56cb747363ef0c570374d854170f",
    "85_4장_아직_여기_있는_몸_보강.md": "9557a7ed565ce0988e8e4abc32d3e601e026bed82f2a5de6bcdfe18f1fe6f07e",
    "99_4장_문_밖이라고_부른_곳_보강.md": "80718e7dd613c0cf6a484e4d5b33bc4165e34d48b8e06d473d2486d7562c2bd5",
    "77_4장_같이_있었다는_말_보강.md": "5fcb6989df7edda6183ffb3c559f0f0d110ee17b66d4ba791ff42fcd5facb4ac",
    "131_4장_이번에도_거짓말이라면_보강.md": "af403650a4d1604399a29d3f1a6305bdebc29ae58722d1784af83542cd77e18e",
    "114_4장_같은_얼굴을_더_만들_수_있다면_보강.md": "c9983d759ed1ee8a2eb21748758cb7678c0121b545528a7f9362dd706dd08f20",
    "166_4장_재판_형식별_연속대본.md": "205e772e4696836716a698bfa0e3d84f3025d87a1f9c3547140e2532460097bd",
    "160_4장_재구성만화_슬롯과_실제문답.md": "f444e531b7e44c598153739199a99b92266f908d8f1eafaf817b9a13c778b619",
    "169_2_4_5_6장_우소다마와_후과_연속대본.md": "954fbe7b6d6f59c6f2dedd9c564654f08a20f15f378fdc284c27ec66d7428964",
    "184_4장_재판_반복논의와_지목_연속대본.md": "9e030c8db34b1960efe0e9619d69f516a5a5901794ce480150f04438935ef996",
    "192_4장_재판_한번만_그_얼굴로_연속대본.md": "9f4d719b40cf118711b1189c41263182dd6103539f2e8da2c7ef87198cf3b04c"
}
