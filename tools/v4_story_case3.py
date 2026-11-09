"""Explicit V4 chapter-three routes; no legacy plot or automatic branch flattening.

This module only constructs in-memory data. The story compiler owns all writes.
Source ranges below are reviewed authoring contracts, protected by source hashes
returned by ``route_source_hashes``. Unbound images/meetings stay real gates.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re


# Compact route notation. End points are inclusive, just like Source.paragraphs.
def S(p, a, b): return ("span", p, a, b)
def C(flag, rows, required=True): return ("case", flag, rows, required)
def I(flag, value, ops): return C(flag, [(value, ops)], False)
def M(p, line, flag, labels, rows): return ("menu", p, line, flag, labels, rows)
def T(ident): return ("task", ident)
def E(key): return ("evidence", key)
def H(key, title, space, ops): return ("investigate", key, title, space, ops)
def V(values): return ("set", values)


SOURCE_PREFIXES = (
    "13a", "13a2", "13a3", "13a4", "13a5", "13a6", "13a7", "13a8",
    "13a9", "13a10", "13a11", "13a12", "13b1", "13b2", "13b3", "13b4",
    "13c1", "13c2", "13c3", "13d", "83", "98", "156", "136", "128",
    "173", "180", "110", "70", "74", "169", "102", "116", "172", "177",
    "165", "159", "183", "191",
)


REVIEWED_SOURCE_HASHES = {
    "13a_3장_일상_초고.md": "6aed86ad5420d00f7ffd6f708fe2c1e71a50449b7d9ae747791ad200b0c567f5",
    "13a2_3장_거울앞의_시연_초고.md": "710270922502f32c190581d7e597c33cfb263a2a2f81784ad460b176a11233f5",
    "13a3_3장_각자의_자료실_초고.md": "71d49f7d08a4944290f9e8b951779bc06e06aecaa1dff417d4036f40351ddb63",
    "13a4_3장_저녁상영_초고.md": "84fb7d77d5321d7c12cf604fcc8203b46a70e2d32e7c5b29b0f1cf743fee3ca7",
    "13a5_3장_공개를_부탁한_사람_초고.md": "7506b3f9ed2d8ac5db57852eda63e689cddd168a1365e1940334cdb2d622d7bc",
    "13a6_3장_두몸의_기억_초고.md": "a27fd940d3aed1e384ecdbd4fbf7147508334de1314efa75027eb8f6a17dc864",
    "13a7_3장_남는정보_초고.md": "5d6a54d97508c6aba659cc508a75371cb5054dfef7dc57ce204db6aa3e0673bd",
    "13a8_3장_거울의_모서리_초고.md": "c7bbbc091bdb3b6d02e0ae6da5672d68275599dd6686000b1ef7cb4931827801",
    "13a9_3장_밤의_선긋기_초고.md": "93954641978a6b9cf8afb1fa60136c0bd10e8108d1904f94e6563137b1fd05bd",
    "13a10_3장_남겨진_한줄_초고.md": "6f01f79e8124a33ee56b7351ea32caeca6f0b4957d688b5f1cb40f190f3cf148",
    "13a11_3장_확인하러_가는_사람들_초고.md": "2aa93bc08d55b1da65ca2881eef989658a51c3e99706478e36ae64f4c7d60237",
    "13a12_3장_끝났다는_말_초고.md": "8ac013b445c89cf40b7c59695801a415b32705b5cb38cfa407651c080f2d8c3d",
    "13b1_3장_아직_살아있는_사람_초고.md": "ac8f9cd2ddd3908425f49e98b1e89f0e85df340cdfca2ed29e526e94e00e566d",
    "13b2_3장_두번째_이름_초고.md": "3bb9488ba2b30aa141958250965d2599ceb4d60f295d2ec00b038d9887e5687a",
    "13b3_3장_건네지_않은_말_초고.md": "e972c97d50a6c3ae07619a3942b458659c71998ae9e320f0e987c6d631de2784",
    "13b4_3장_아침에_쓴_기회_초고.md": "1642c7bdd2598a7504b4df4e17989dc83e6145e477d4cff266c4fe974ebb145b",
    "13c1_3장_재판_몸의_이름_초고.md": "36d842f455ba6d7130195c2abfcc498410b38d674136df9c2f8d414541f52a32",
    "13c2_3장_재판_미오가_만든_거짓말_초고.md": "ed18a9100c700d8f580c35aa4ac8c90e25ca89f77b34fdfce48f4de837ac414d",
    "13c3_3장_재판_돌아가지_않은_사람_초고.md": "90dfd7fa1c653842f25b723a87ee3cc14c48045368a28f9edd00fa6edaa2967f",
    "13d_3장_결과와_남겨진_목소리_초고.md": "51548037dfaac7a8e6c42dec0aea35d1ecdfc51739358d6523f66d8e2a1bdc4c",
    "83_3장_먼저_나가_있는_사람_보강.md": "453f32a3666273b72b08336698ad764f665df176ebd872d1b0c0425a95f89cae",
    "98_3장_손님_없는_매표소_보강.md": "489c57eb66462b78727fc1587b0200f58a9269f978b6ca99da8f6384a07a2b92",
    "156_3장_내_차례에는_말하지_마_보강.md": "c071d831eeb102f52e3259eef94f8ca0ac581209449043080efdd7f84b98f4bd",
    "136_3장_부르지_않은_아침_보강.md": "d28ee762a73d2c291e8e70c77b254f6bb3b50e4f954a3e3582b67a1e825bb35c",
    "128_3장_내_이름이면_오는_사람들_보강.md": "cbe9703ee1fb7d8f5465c5460e767902b7ecdafe0cd5394957f32b131303b38b",
    "173_3장_빌린_몸을_돌려놓는_손_연속대본.md": "355421e3a7143e7be9ff4c53b25b674dc2a4f838d739f4f13b2007979f27aad9",
    "180_3장_세_장의_같은_숫자_연속대본.md": "977dc067e7d099c7fb97a3ff551e3c255fceeae1960e1df729436003b5aa450a",
    "110_3장_먼저_고개를_끄덕인_사람_보강.md": "3b5900f11f669cba99703bd89b74e4e4da018a656fdd45f9ff5ecadb249606f0",
    "70_3장_뒤로_미룬_사람_보강.md": "904af801fae89d2765cd9a11c42d928059194070792580324500e9a8eee82da4",
    "74_3장_읽어_주면_끝나는_질문_보강.md": "e890d06b436802b7e53115d53b55c34f9c50ac0c540306e9ac88ce890bf2b003",
    "169_2_4_5_6장_우소다마와_후과_연속대본.md": "954fbe7b6d6f59c6f2dedd9c564654f08a20f15f378fdc284c27ec66d7428964",
    "102_3장_아직_그_목소리가_나는_자리_보강.md": "f4115f5b3fb5ffae95507ab1cec395bd07107a195a943840639620a5fa2c782c",
    "116_3장_다음에도_필요한_사람_보강.md": "197f7870e9f7c3c4bed4b70ad2ccf20b0a224ff5a1b6b6f7c2ee19638d00da4d",
    "172_2장_네가_선생님이면_연속대본.md": "8cb27f9c7af285abd04a1473857e5e0d1f1e0cd73006cf6c0fe5d976d8646328",
    "177_2장_아프지_않은_손_연속대본.md": "1cb31b1cedd649c735e3b92e4a323d06d07ebb627504c010b1f567c8c4f224b4",
    "165_3장_재판_형식별_연속대본.md": "0d9b7bf79e3484d89885a34773c306c890509f3d7c871d3ab93d382c4fd2bbd3",
    "159_3장_재구성만화_슬롯과_실제문답.md": "3cf72765cc0317be8fc3e362a57fdb7403c71206fc03218f995cd376b14f41ee",
    "183_3장_재판_반복논의와_지목_연속대본.md": "5f8fadabc65270e4dec16a4bedcefca654a8f7acde9a389ee3eaf4ebef7638e9",
    "191_3장_재판_내일도_기억할_사람_연속대본.md": "83fe92044935d017d7a651da0abad12e9f6ac4ac826f0e33b01e72581dab7d94"
}


def route_source_hashes(sources):
    """Called by the owner to add these reviewed dependencies to route guards."""
    current = {s.name: s.hash for s in sources.values() if s.prefix in SOURCE_PREFIXES}
    if current != REVIEWED_SOURCE_HASHES:
        raise ValueError("Chapter3 reviewed source hashes changed; re-read routing before changing line ranges")
    return dict(REVIEWED_SOURCE_HASHES)


def compile_chapter_three(sources, freetime_graphs, tasks):
    from build_v4_story import Graph, SPEAKERS, clean

    route_source_hashes(sources)
    docs = {s.prefix: s for s in sources.values()}
    missing = set(SOURCE_PREFIXES) - set(docs)
    if missing:
        raise ValueError("Chapter3 source dependency missing: " + ",".join(sorted(missing)))
    g = Graph("3")
    taskmap = tasks["tasks"]
    g.taskDefinitions = taskmap
    spans = []
    span_cache = {}
    evidence = _evidence(docs)
    investigation = []

    def ident(label, anchor=""):
        # Source say/stage IDs are already semantic. Synthetic routing IDs are
        # anchored to their semantic continuation, never global row ordinals.
        suffix = ":" + hashlib.sha256(anchor.encode("utf-8")).hexdigest()[:12] if anchor else ""
        return "v4:3:route:" + label + suffix

    def gate(label, reason, source=None, anchor=""):
        return g.add(ident(label, anchor), {"type": "gate", "reason": reason, **({"source": source} if source else {})})

    def span(p, a, b, target):
        source = docs[p]
        a = source.at(a) if isinstance(a, str) else a
        b = source.at(b) - 1 if isinstance(b, str) else len(source.lines) if b is None else b
        if b < a:
            return target
        key = (p, a, b, target)
        if key in span_cache:
            return span_cache[key]
        spans.append({"file": source.name, "first": a, "last": b, "sha256": source.hash})
        # Explicit on-screen quoted records must not disappear as editorial
        # notes. These are source text, never newly authored witness dialogue.
        document_ranges = {
            "13a4": [(56, 62, "준비 기록의 음성"), (76, 80, "준비 기록의 음성"), (92, 104, "준비 기록의 음성"), (116, 122, "준비 기록의 음성"), (140, 140, "기록 음성"), (146, 146, "기록 음성")],
            "13a6": [(332, 337, "정상 시연에서 확인한 범위")],
            "13a7": [(386, 400, "빌린 책의 본문")],
            "13a9": [(261, 261, "보통 메모")],
            "13a10": [(29, 29, "보호된 손글씨")],
            "180": [(311, 311, "마지막 공개 A"), (313, 313, "마지막 공개 B"), (315, 315, "마지막 공개 C")],
        }
        ranges = [(x, y, title) for x, y, title in document_ranges.get(p, []) if a <= x and y <= b]
        for x, y, title in reversed(ranges):
            tail = g.sequence(source, y + 1, b, target) if y < b else target
            rows = [clean(re.sub(r"^>\s*|^-\s*", "", l)) for l in source.lines[x - 1:y] if l.strip() not in ("", ">")]
            target = g.add(f"v4:{p}:document:{x}", {"type": "document", "title": title, "rows": rows, "private": p not in ("13a4", "180"), "source": source.ref(x), "next": tail, "sourceKind": "authored_quote", "notLiveWitness": True})
            b = x - 1
        result = g.sequence(source, a, b, target) if a <= b else target
        span_cache[key] = result
        return result

    def route(ops, target):
        for op in reversed(ops):
            kind = op[0]
            if kind == "span":
                target = span(*op[1:], target)
            elif kind == "set":
                target = g.add(ident("state", json.dumps(op[1], sort_keys=True) + target), {"type": "stage", "direction": "", "set": op[1], "next": target})
            elif kind == "case":
                _, flag, rows, required = op
                default = gate("missing-choice-" + flag, "Required authored choice missing: " + flag, anchor=target) if required else target
                cases = []
                for val, body in rows:
                    dst = route(body, target)
                    cases.extend({"flag": flag, "equals": value, "to": dst} for value in (val if isinstance(val, tuple) else (val,)))
                target = g.add(ident("branch-" + flag, target), {"type": "branch", "cases": cases, "default": default})
            elif kind == "menu":
                _, p, line, flag, labels, rows = op
                if len(rows) != len(labels):
                    raise ValueError(flag + ": options differ")
                options = [{"id": "ABC"[i], "label": title, "to": route(body, target), "set": {flag: "ABC"[i]}} for i, (title, body) in enumerate(zip(labels, rows))]
                question = "가방을 맡기는 선택" if flag == "I3-C01" else docs[p].lines[line - 1].split("—")[-1].lstrip("# ").strip()
                target = g.add(ident("menu-" + flag), {"type": "menu", "q": question, "options": options, "source": docs[p].ref(line)})
            elif kind == "any":
                _, conditions, body = op
                dst = route(body, target)
                target = g.add(ident("earned-callback", target), {"type": "branch", "cases": [{"flag": flag, "equals": val, "to": dst} for flag, val in conditions], "default": target})
            elif kind == "task":
                tid = op[1]
                if tid not in taskmap:
                    raise ValueError("Missing authored chapter3 input: " + tid)
                target = g.add("v4:input:" + tid, {"type": "task", "taskId": tid, "runtimeReady": taskmap[tid]["runtimeReady"], "source": taskmap[tid]["source"], "next": target, "success": target})
            elif kind == "evidence":
                card = evidence[op[1]]
                target = g.add("v4:3:acquire:" + op[1], {"type": "evidence", **card, "next": target})
            elif kind == "investigate":
                _, key, title, space, body = op
                hub_id = "v4:3:investigate:" + key
                ret = g.add(hub_id + ":return", {"type": "return"})
                entry = route(body, ret)
                flag = "investigation:3:" + key + ":complete"
                spot = {"id": key, "label": title, "space_id": space, "target_id": None, "geometryReady": False, "entry": entry, "returnTo": hub_id, "completionFlag": flag, "onReturnSet": {flag: True}, "required": True, "interactionPolicy": "authored text investigation scope; exact actor/evidence geometry not yet bound"}
                investigation.append(spot)
                target = g.add(hub_id, {"type": "investigate", "title": title, "spots": [spot], "requiredSpotIds": [key], "requiredCards": [], "next": target})
            elif kind == "fte":
                # No guessed fallthrough if the requested meeting has not been
                # compiled. Import only a selected eligible meeting at call time.
                options = []
                if len(op)>1:
                    _,window,source_prefix,source_line,candidates=op
                else:
                    window,source_prefix,source_line,candidates='F3','13a3',587,(("55", "코토", ("21", "36")), ("58", "레이", ("27", "45")), ("60", "켄", ("28", "47")), ("61", "리쿠", ("30", "48")))
                for prefix, name, prerequisites in candidates:
                    if prefix in freetime_graphs:
                        ft = freetime_graphs[prefix]
                        for nid, node in ft["nodes"].items():
                            if nid not in g.nodes:
                                g.add(nid, copy.deepcopy(node))
                        entry = g.add(ident(window+"-call-" + prefix), {"type": "call", "target": ft["entry"], "returnTo": target, "onReturnSet": {f"fte:{prefix}:complete": True, "window:"+window+":completed": True}})
                    else:
                        entry = gate(window+"-unbound-" + prefix, f"Selected authored meeting {prefix} has nested conditional routing not compiled; do not substitute another meeting.", docs[source_prefix].ref(source_line))
                    options.append({"id": prefix, "label": name, "to": entry, "requires": {f"fte:{p}:complete": True for p in prerequisites}})
                options.append({'id':'REST','label':'혼자 시간을 보낸다','to':target,'set':{'window:'+window+':completed':True}})
                target = g.add(ident(window+"-personal-window"), {"type": "menu", "selectionRole":"freetime", "q": "개인시간 — 함께 있을 사람", "options": options, "source": docs[source_prefix].ref(source_line), "noEligibleOptions": "rest", "window": window, "oneMeetingOnly": True})
            else:
                raise ValueError("Unknown chapter3 operation: " + kind)
        return target

    _baseline_tasks(taskmap, docs)
    _bind_additional_tasks(taskmap, evidence)
    day = _daily_ops()
    inv = _investigation_ops()
    trial = _trial_ops()
    ending = _result_ops()
    end = g.add("v4:3:chapter-end", {"type": "end", "chapterComplete": True, "nextChapter": "4"})
    entry = route(day + inv + trial + ending, end)
    _physical_display(g.nodes, taskmap)
    # Every actual input in this chapter is after BOTH deaths and before the
    # execution. The vacant Sora-body seat and occupied Ken-body seat remain
    # distinct even after the controller's identity is established.
    seats = [actor for actor in SPEAKERS.values() if actor != "lappy"]
    for node in g.nodes.values():
        if node["type"] == "task":
            node["trialDead"] = ["kaede", "taiga", "ai", "yuu", "riku", "sora"]
            node["seats"] = seats
            node["seatOccupants"] = {"ken": {"physicalActor": "ken", "bodyAlive": True, "originalConsciousnessIsNotAssumedAlive": True}, "sora": {"bodyAlive": False, "vacant": True}}
            node["rosterSource"] = docs["13c1"].ref(10)
    catalogue = {card["evidenceId"]: {"id": card["evidenceId"], **card} for card in evidence.values()}
    return g.export(entry, routingStatus="authored_routes_with_explicit_binding_gates", contentScope="chapter3 daily/investigation/trial/result authored choices and exact insert returns; unbound original-input geometry is never auto-completed", sourceFiles=[docs[p].name for p in SOURCE_PREFIXES], routeRanges=spans, investigationScopes=investigation, evidenceCatalog=catalogue, campaignReady=False, runtimeIntegrationTested=False, allBindingsReady=not any(b.get("required") for t in taskmap.values() if t.get("chapter") == "3" for b in t.get("bindings", [])), canonicalGuard={"chapter": "3", "fixedCulprit": "sora", "twoDiscoveriesSequential": True, "displayIdentityIsNotProof": True})


def _daily_ops():
    # Chronological source order, with mutually exclusive alternatives routed
    # before each common return. The range list is deliberately not inferred
    # from file names or all indexed headings.
    return [
        V({"3:livingBodies": 12}), S("13a", 6, 73), S("136", 5, 196), S("13a", 76, 189),
        M("13a", 190, "3-C01", ["리쿠와 함께 간다", "하루카와 함께 간다", "소라와 함께 간다"], [
            [S("13a", 193, 207), S("83", 5, 106)],
            [S("13a", 208, 225), S("83", 109, 206)],
            [S("13a", 227, 243), S("83", 209, 314)],
        ]), S("13a", 246, None), S("13a2", 6, None),
        S("13a3", 5, 186), S("98", 5, 84),
        M("98", 85, "3-C03", ["미오가 손님을 맡는다", "하루카와 같이 손님을 맡는다", "연기하지 않고 관객으로 남는다"], [
            [S("98", 90, 142)], [S("98", 144, 198)], [S("98", 200, 246)]
        ]), S("98", 249, 252),
        C("3-C03", [("A", [S("98", 254, 260)]), ("B", [S("98", 262, 268)]), ("C", [S("98", 270, 286)])]),
        S("98", 288, 464), S("13a3", 189, 586), ("fte",),
        S("156", 5, 104),
        M("156", 105, "3-C04", ["나나에게 2를 내라는 손짓을 한다", "유리에 비친다고 알리고 처음부터 다시 하자고 한다", "말은 하지 않고 이번 판에서는 빠지겠다고 한다"], [
            [S("156", 108, 172)], [S("156", 174, 240)], [S("156", 242, 262), V({"viewpoint": "nana"}), S("156", 264, 286), V({"viewpoint": "mio"})]
        ]),
        C("3-C04", [(("A", "B"), [S("156", 290, 292)]), ("C", [S("156", 294, 296)])]),
        S("156", 298, 300), S("13a4", 6, 43),
        C("3-C03", [("A", [S("98", 472, 490)]), ("B", [S("98", 492, 510)]), ("C", [S("98", 512, 528)])]),
        C("3-C04", [("A", [S("156", 306, 320)]), ("B", [S("156", 322, 334)]), ("C", [S("156", 336, 358)])]),
        S("13a4", 48, None), S("13a5", 5, 24), S("128", 5, 114), S("13a5", 27, 328),
        S("13a6", 6, 400),
        I("fte:60:complete", True, [S("13a6", 405, 408),
            C("F-KE03-A", [("A2", [C("F-KE03-B", [(("B2", "B3"), [S("13a6", 410, 422)]), ("B1", [S("13a6", 424, 426)])])]), (("A1", "A3"), [S("13a6", 424, 426)])]),
            C("F-KE03-B", [("B1", [S("13a6", 428, 432)]), ("B2", [S("13a6", 434, 438)]), ("B3", [S("13a6", 440, 444)])]), S("13a6", 446, 448)]),
        S("173", 5, None), S("13a7", 6, 53),
        I("fte:61:complete", True, [
            C("F-RI03-A", [("A1", [C("F-RI03-B", [("B1", [S("13a7", 59, 65)]), (("B2", "B3"), [S("13a7", 67, 75)])])]), ("A2", [S("13a7", 77, 83)]), ("A3", [S("13a7", 85, 91)])]),
            C("F-RI03-B", [("B1", [S("13a7", 95, 101)]), ("B2", [S("13a7", 103, 107)]), ("B3", [S("13a7", 109, 116)])])]),
        S("13a7", 118, 323),
        I("fte:55:complete", True, [
            C("KOTO-03B", [("B1", [S("13a7", 329, 337)]), ("B2", [S("13a7", 339, 347)]), ("B3", [S("13a7", 349, 357)])]),
            C("KOTO-03A", [("A1", [S("13a7", 361, 363)]), ("A2", [S("13a7", 365, 367)]), ("A3", [S("13a7", 369, 371)])]), S("13a7", 373, 379)]),
        I("fte:63:complete", True, [C("F-SA03-B", [("B1", [S("13a7", 384, 487)]), (("B2", "B3"), [S("13a7", 491, 499)])])]),
        S("13a7", 500, 608), V({"3:lunch:complete": True}),
        ("fte","F3-after-lunch","13a7",604,(("56","쇼",("23","41")),("59","소라",("24","42")))),
        S("13a7",610,611), S("13a8", 6, 247),
        S("13a9", 5, 22), S("180", 5, 166),
        M("180", 167, "W3-C15", ["소라에게 나나도 3을 고를 거라고 알린다", "나나에게 켄이 소라의 3을 알고 있다고 말한다", "들은 말을 옮기지 않고 정한 2를 낸다"], [[S("180", 170, 218)], [S("180", 220, 258)], [S("180", 260, 306)]]),
        S("180", 307, 310),
        C("W3-C15", [("A", [S("180", 311, 311)]), ("B", [S("180", 313, 313)]), ("C", [S("180", 315, 315)])]),
        S("180", 317, 328),
        C("W3-C15", [(("A", "C"), [S("180", 338, 342)]), ("B", [S("180", 330, 336)])]), S("180", 344, 350),
        C("W3-C15", [("A", [S("180", 352, 356)]), ("B", [S("180", 358, 362)]), ("C", [S("180", 364, 368)])]), S("180", 370, 400),
        S("13a9", 25, 82),
        M("13a9", 83, "3-C02", ["정보 경로를 지킬 수 없으면 중단하자고 한다", "돌아오는 절차부터 확인한다", "오늘과 내일 확인할 것을 따로 남긴다"], [[S("13a9", 86, 98)], [S("13a9", 100, 112)], [S("13a9", 114, 124)]]),
        S("13a9", 127, 264),
        I("fte:59:complete", True, [S("13a9", 269, 274),
            C("SORA-03A", [("A1", [C("SORA-03B-A", [("B1", [S("13a9", 276, 286)]), (("B2", "B3"), [S("13a9", 288, 302)])])]), ("A2", [C("SORA-03B-B", [("B1", [S("13a9", 304, 312)]), ("B2", [S("13a9", 314, 324)]), ("B3", [S("13a9", 326, 334)])])]), ("A3", [S("13a9", 326, 334)])]), S("13a9", 336, 340)]),
        S("13a9", 341, 348), S("13a10", 7, 278),
        C("3-C04", [("A", [S("13a10", 280, 286)]), ("B", [S("13a10", 288, 296)]), ("C", [S("13a10", 298, 306)])]),
        S("13a10", 308, 460), S("13a11", 5, 328), S("13a12", 6, 75),
        E("private-phrase"), S("13a12", 76, 243), S("13a12", 244, 397), V({"3:first-discovery": True, "3:livingBodies": 11}),
    ]


def _investigation_ops():
    return [
        S("13b1", 5, 30), V({"3:second-body-alive": True}), E("alive-confirmation"),
        S("13b1", 31, 130),
        H("I3-05-rule", "첫 파일과 조종자의 판정 규칙", "mirror_waiting", [S("13b1", 131, 192), E("file-first"), E("culprit-rule"), E("possession-rules")]),
        S("13b1", 193, 216), S("110", 5, 204),
        H("I3-09-first-scene", "첫 현장의 상태와 직접 확인", "mirror_workbay", [S("13b1", 219, 432),
            C("W3-C15", [("A", [S("13b1", 434, 440)]), ("B", [S("13b1", 442, 448)]), ("C", [S("13b1", 450, 456)])]), S("13b1", 458, 480)]),
        H("I3-10-tools", "작업대의 종이와 도구", "mirror_workbay", [S("13b1", 481, 552), E("knife-work")]),
        H("I3-12-reflection", "반사면과 직접 보이는 경계", "mirror_workbay", [S("13b1", 553, 654), E("reflection-geometry"), E("first-attack"), E("camera-timing")]),
        S("13b1", 655, 720), S("13b2", 5, 114),
        S("13b2", 115, 190), V({"3:second-discovery": True, "3:second-body-alive": False, "3:livingBodies": 10}), E("file-second"),
        S("13b2", 191, 352), E("restraint-awake"),
        S("70", 5, 74),
        M("70", 75, "I3-C02", ["하루카와 첫 현장으로 간다", "나나 곁에 남는다", "코토와 정리에 필요한 천을 가져간다"], [[S("70", 78, 112)], [S("70", 114, 158)], [S("70", 160, 196)]]),
        S("70", 197, 218),
        H("I3-30-paper", "봉투의 준비와 실제 인계", "mirror_waiting", [S("13b3", 5, 74), E("envelope-route"), E("camera-preparation")]),
        H("I3-33-memory", "접촉과 기억 기능의 범위", "mirror_waiting", [S("13b3", 75, 144), E("nana-contact"), E("memory-rule")]),
        S("13b3", 145, 166),
        H("I3-36-observers", "서로 다른 목격 범위", "mirror_waiting", [S("13b3", 167, 232), E("continuous-awake"), E("riku-function")]),
        S("13b3", 233, 244),
        M("13b3", 239, "I3-C01", ["봉투째 맡기고 열기 전에는 같이 본다", "가방은 들되 지금부터 손을 같이 본다", "나를 못 믿는다고 먼저 말해 달라고 한다"], [[S("13b3", 246, 256)], [S("13b3", 258, 266)], [S("13b3", 268, 280)]]),
        S("13b3", 281, 294),
        H("I3-40-record", "자료 색인과 이어지는 영상", "record_room", [S("13b4", 5, 100), E("riku-index"), E("father-record")]),
        H("I3-46-morning", "오전에 사용한 기회", "mirror_waiting", [S("13b4", 101, 190), E("morning-use")]),
        H("I3-51-two-files", "두 파일과 소지품의 규칙 설명", "mirror_waiting", [S("13b4", 191, 240), E("private-notebook")]),
        S("13b4", 241, 290),
    ]


def _trial_ops():
    return [
        S("13c1", 6, 37), S("110", 207, 244), S("13c1", 40, 57), T("T3-NS-01"),
        S("13c1", 60, 177), T("T3-MM-01"), S("13c1", 179, 425),
        T("T3-PN-01"), S("13c1", 430, 475), T("T3-RL-01"), T("T3-RL-02"), T("T3-RL-03"),
        S("13c1", 566, 726), T("T3-FA-01"), S("13c1", 729, 870), E("current-nonattempt"), S("13c1", 871, 920),
        C("I3-C01", [(("A", "C"), [S("13c1", 922, 926)]), ("B", [S("13c1", 928, 932)])]),
        S("13c1", 933, 996), S("74", 5, 118),
        C("I3-C01", [(("A", "C"), [S("74", 120, 122)]), ("B", [S("74", 124, 126)])]), S("74", 128, None),
        C("I3-C01", [(("A", "C"), [S("13c2", 8, 10)]), ("B", [S("13c2", 12, 14)])]), S("13c2", 16, 24),
        I("T1-LIE-B", True, [S("13c2", 28, 32)]),
        T("T3-LIE-01"), S("13c2", 51, 120), S("13c2", 121, 188), T("T3-RS-01"),
        S("13c2", 190, 298), I("T1-LIE-B", True, [S("13c2", 302, 326)]),
        I("T2-LIE-B", True, [S("169", 124, 139)]), S("128", 117, 124), T("T3-SD-01"),
        S("13c2", 337, 392), V({"3:identity:confirmed": True}), S("13c2", 393, 440),
        S("102", 5, 98),
        M("102", 99, "T3-C01", ["켄의 말과 지금 소라가 고른 말을 나눈다", "원래 켄이 대답할 여지가 남는지 확인한다", "지금 대답을 시키는 일을 멈추고 첫 살해로 돌아간다"], [[S("102", 104, 116)], [S("102", 118, 134)], [S("102", 136, 150)]]),
        S("102", 153, 268), S("13c2", 443, 542), S("13c3", 5, 228),
        I("3:lunch:complete", True, [S("13c3", 229, 262)]), S("116", 5, 54),
        C("2-C05", [("A", [S("116", 56, 58)]), ("B", [S("116", 60, 62)])]),
        S("116", 64, 194), S("13c3", 265, 316),
        # Both the first and delayed introductory meeting set the same earned
        # actor relationship flag; a missing meeting never defaults to viewed.
        ("any", [("fte:24:complete", True), ("fte:89:complete", True)], [S("13c3", 320, 354)]),
        S("13c3", 355, 520), S("191", 5, None), S("13c3", 521, 762), S("172", 277, None), T("T3-AA-01"),
        S("13c3", 767, 770), S("13c3", 771, 876), S("159", 7, 22),
        T("T3-MG-01"), S("159", 239, 274), S("13c3", 879, 986), T("T3-VOTE-01"),
        S("13c3", 987, 1024),
    ]


def _result_ops():
    return [
        S("13d", 5, 130), V({"3:livingBodies": 9}), S("13d", 131, 224), I("I3-C02", "B", [S("13d", 226, 234)]), S("13d", 236, 238),
        C("T3-C01", [("A", [S("102", 276, 284)]), ("B", [S("102", 286, 294)]), ("C", [S("102", 296, 304)])]),
        S("13d", 241, 268), I("I3-C02", "A", [S("13d", 270, 280)]), S("13d", 282, 562),
        I("I3-C02", "C", [S("13d", 564, 576)]),
        I("fte:61:complete", True, [I("F-RI03-A", "A1", [C("F-RI03-B", [(("B2", "B3"), [S("13d", 580, 605)])], False)])]),
        S("177", 329, 372), S("13d", 609, 634),
    ]


def _evidence(docs):
    """Information actually seen/heard at each scope, not invented E3 numbers.

    The prefix is deliberately separate from the old data/evidence.json. A
    knowledge card does not transfer custody of its described physical object.
    """
    rows = [
        ("private-phrase", "비공개 시험 문장 원본", "켄의 시야를 가린 뒤 미오가 새 보통 종이에 썼다. 미오와 소라만 읽고, 미오가 접고 나나가 불투명 봉투에 넣었다. 보호 마법 기록이 아니다. 내용: 낡은 구두 속 파란새는 설탕을 숨긴다.", "13a12", 28, True),
        ("alive-confirmation", "소라 본체 생명징후 확인", "리쿠 첫 발견 이후 대기실의 소라 본체에는 호흡과 맥박이 있었다. 잠들어 있는 상태와 사망은 같은 판정이 아니다.", "13b1", 29, False),
        ("file-first", "첫 사건 파일", "리쿠의 사망 확인, 목 부위 날붙이 손상과 발견 당시 상태. 넓은 추정 범위는 목격보다 정밀한 시계가 아니다.", "13b1", 143, False),
        ("culprit-rule", "첫 사건의 행위자 규칙", "다른 몸을 조종해 직접 살해했다면 실제 조종자가 검정이다. 몸 원래 소유자라는 이유만으로 대신 지목하지 않는다.", "13b1", 153, False),
        ("possession-rules", "빙의의 기본과100퍼센트 조건", "기본15분과100%의 시간 제한 제거는 다르다. 조종 경험은 원래 소유자에게 공유되지 않는다. 이미100%로 들어간 중 본체가 죽으면 고정되고 원래 의식이 소멸한다. 호스트 마법 사용은 불가하다.", "13b1", 191, False),
        ("knife-work", "미로 작업 도구의 사용", "리쿠가 표식 작업에 쓰던 날붙이와 작업 종이를 확인했다. 첫 공격 이후 칼은 켄 몸의 왼손에 계속 남아 있었다. 처음 손잡이를 취한 순간은 가려져 있다.", "13b1", 551, False),
        ("reflection-geometry", "반사와 실제 시야의 겹침", "B 관찰 모퉁이 옆에서 H 작업 홈의 반사된 머리와 직접 나온 어깨가 동시에 보이는 경계를 확인했다. 안쪽 바닥과 몸 뒤 모두가 보인 것은 아니다.", "13b1", 653, False),
        ("first-attack", "공격 전후 연속 관찰", "첫 손잡이는 가려졌다. 그 뒤 팔 재하강, 리쿠가 주저앉음, 칼 든 켄 몸의 퇴장은 미오와 린이 보았다. 반사와 직접 목격을 구별한다.", "13b1", 647, False),
        ("camera-timing", "현장 사진의 촬영 시점", "사진은 공격 뒤 현장 및 시야를 확인할 때 찍었다. 첫 손잡이나 공격 순간을 새로 담은 사진은 없다. 카메라는 하루카에게 돌아갔다.", "13b1", 651, False),
        ("file-second", "두 번째 사망 확인", "첫 사건 수사 중 살아 있던 소라 본체가 두 번째 공격을 받았다. 생존 확인, 공격, 사망 확인과 바깥 선반의 칼 보관은 차례가 다르다.", "13b2", 189, False),
        ("restraint-awake", "제압 중 지속 각성", "린과 레이가 양팔을 제압한 뒤 왼손 악력은 풀렸지만 몸 전체가 의식을 잃거나 잠들지 않았다. 공격 전 관찰과 공격 뒤 제압을 구별한다.", "13b2", 351, False),
        ("envelope-route", "봉투 인계와 합류 동선", "켄 몸과 리쿠가 나가 방 안을 볼 수 없게 된 뒤 나나가 미오에게 봉투를 넘겼다. 미오는 가방 안쪽에 넣고 린과 합류했으며 내용을 읽어 주지 않았다. 나나는 내용 미열람을 진술했다.", "13b3", 73, False),
        ("camera-preparation", "준비 때 닫힌 카메라", "새 문장을 쓸 때 카메라는 덮개가 닫힌 채 미오 가방 안에 있었다. 현재 반환과 첫 현장 사진은 그 준비 순간의 촬영을 증명하지 않는다.", "13a12", 16, False),
        ("nana-contact", "나나의 당시 접촉 대상", "기본 최근1시간 흐림을 나나가 처음 밝혔다. 현재 사용하지 않았다고 진술했고 접촉한 사람은 소라 본체와 쇼라고 말했다. 만졌다는 사실은 자동 사용 증명이 아니다.", "13b3", 121, False),
        ("memory-rule", "기억과 최면의 확인된 한계", "최면은 모르는 문장을 새 기억으로 넣거나 기존 기억을 지우지 않는다. 망각은 새 기억 삽입이 아니다. 기본/100% 조종 경험은 원래 소유자에게 넘어가지 않는다.", "13b3", 143, False),
        ("continuous-awake", "켄 몸의 연속 각성", "미오의 반사와 직접 목격 뒤 린의 관찰, 레이의 합류가 이어졌다. 첫 공격부터 두 번째 공격까지 몸은 깨어 있었다. 이미 들어온 조종자의 퇴출까지 막는 관찰은 아니다.", "13b3", 185, False),
        ("riku-function", "착각의 확인된 기능 범위", "리쿠의 대역은 신원 인식을 바꾼다. 물리적 몸, 실제 음성, 거울과 물리 사진은 바꾸지 않는다. 확장30분을 실제 사용 이력으로 단정하지 않는다.", "13b3", 231, False),
        ("riku-index", "리쿠의 자료 색인", "리쿠가 소라와 거래하던 자료의 색인. 미오가 접어 봉투에 넣은 시험 문장과 다른 종이다. 색인의 항목과 실제 이어지는 기록을 나누어 확인한다.", "13b4", 50, False),
        ("father-record", "사고 뒤 이어지는 기록", "소라가 자리를 뜬 뒤의 다른 위치 기록까지 실제로 확인했다. 앞서 상영된 조각만으로 구조 요원의 생사를 완성하지 않았으며 현재 확인 내용은 그 기록의 범위다.", "13b4", 100, False),
        ("morning-use", "아카리 아침 사용 기록", "07시 갱신 뒤 오전에 이미 되감기를 썼다는 설명과 보호 손글씨를 대조했다. 기본10초/100%30초라도 하루 사용 횟수는 늘지 않는다. 미오가 덮어쓴 기억을 되찾은 것은 아니다.", "13b4", 189, False),
        ("private-notebook", "소라 수첩의 빙의 설명", "수첩의 정상15분, 기억 미공유,100% 지속과 본체 사망 시 고정/원래 의식 소멸 부분을 함께 확인했다. 언제 읽고 결심했는지는 접힌 모서리만으로 정하지 않는다.", "13b4", 239, False),
        ("current-nonattempt", "현재 재시연 미실시", "현재 최면 재시연은 이루어지지 않았다. 미오와 린이 하지 않겠다고 한 일은 성공이나 실패 결과가 아니다. 거절만으로 현재 조종자를 판정하지 않는다.", "13c1", 869, False),
    ]
    result = {key: {"evidenceId": "v4:3:knowledge:" + key, "name": title, "text": text, "revision": False, "private": private, "knowledgeOnly": True, "source": docs[p].ref(line)} for key, title, text, p, line, private in rows}
    result["private-phrase"].update(displayFact="소라를 비난하지 않은 글", displayLie="소라를 비난한 글", courtroomPublicOnlyAfter="T3-19", physicalCustodyIsSeparate=True)
    return result


def _bind_additional_tasks(taskmap, evidence):
    # These cards are awarded only after the exact corresponding source scope.
    names = {
        "T3-NS-A01": "riku-function", "T3-NS-A02": "first-attack", "T3-NS-A03": "possession-rules",
        "T3-NS-A04": "alive-confirmation", "T3-NS-A05": "first-attack", "T3-NS-A06": "memory-rule",
        "T3-NS-A07": "envelope-route", "T3-NS-A08": "morning-use", "T3-NS-A09": "nana-contact",
        "T3-NS-A10": "continuous-awake", "T3-NS-A11": "current-nonattempt", "T3-PN-A02": "continuous-awake",
        "T3-PN-A03": "restraint-awake", "T3-RS-A02": "camera-preparation", "T3-RS-A03": "envelope-route",
        "T3-EVIDENCE-A01": "private-phrase",
    }
    for tid, key in names.items():
        task = taskmap[tid]
        task["answerEvidenceId"] = evidence[key]["evidenceId"]
        task["requiresEvidence"] = [evidence[key]["evidenceId"]]
        task["evidencePool"] = "actually-acquired-v4-cards-only"
        task["bindings"] = [b for b in task["bindings"] if b["kind"] != "evidenceAcquisition"]
        task["runtimeReady"] = not any(b.get("required") for b in task["bindings"])
    # This source literally specifies left Ken-body / centre Rin / right Nana.
    # The generic parser only recognises a name followed by its actor token,
    # so the physical-body label requires this reviewed local binding.
    task = taskmap["T3-PN-A02"]
    task["lanes"] = [{"id": slot, "actor": actor, "lines": [e["id"] for e in task["lines"] if e["actor"] in (original, actor)]} for slot, actor, original in (("왼쪽", "ken", "sora"), ("가운데", "rin", "rin"), ("오른쪽", "nana", "nana"))]
    assert {e["id"] for e in task["lines"]} == {x for lane in task["lanes"] for x in lane["lines"]}
    task["bindings"] = [b for b in task["bindings"] if b["kind"] != "panicLanes"]
    task["runtimeReady"] = not any(b.get("required") for b in task["bindings"])


def _baseline_tasks(taskmap, docs):
    def events(p, a, b):
        return [e for e in docs[p].paragraphs(a, b) if e["type"] in ("say", "stage")]

    def says(p, a, b): return [e for e in events(p, a, b) if e["type"] == "say"]

    def make(tid, kind, p, line, **fields):
        ref = docs[p].ref(line)
        title = ref["heading"].split(" ", 1)[-1].split(" — ", 1)[0]
        taskmap[tid] = {"id": tid, "kind": kind, "chapter": "3", "sourceKind": "BASELINE", "source": ref, "title": title, "prompt": title, "intro": [], "lines": [], "wrong": [], "success": [], "bindings": [], "return": {"graphNext": True}, "runtimeReady": True, "retry": {"sameTask": True, "preserveEvidence": True, "preservePublicFacts": True, "cancellationIsSuccess": False}, **fields}
        return taskmap[tid]

    for tid, kind, a, stop, wrongs, correct, cardkey, weakness in (
        ("T3-NS-01", "nonstop", 5, 24, [(25, 32), (33, 40)], (41, 54), "culprit-rule", "첫 사건 이름도 켄"),
        ("T3-PN-01", "panic", 88, 101, [(102, 107), (108, 115)], (116, 127), "possession-rules", "지났으니까,내가 돌아왔어"),
        ("T3-RS-01", "showdown", 148, 171, [(172, 177), (178, 185)], (186, 195), "private-phrase", "아예 근거에서 빼"),
    ):
        line_events = says("165", a, stop)
        marked = [e for e in line_events if weakness in e["text"]]
        if len(marked) != 1:
            raise ValueError(tid + ": source weakness moved")
        make(tid, kind, "165", a, lines=line_events, intro=[e for e in events("165", a, stop) if e["type"] == "stage"], wrongVariants=[{"cause": f"source-wrong-{i}", "script": events("165", x, y)} for i, (x, y) in enumerate(wrongs, 1)], success=events("165", *correct), targets=[{"lineId": marked[0]["id"], "actor": "ken" if "켄의몸" in marked[0].get("delivery", "") else marked[0]["actor"], "word": weakness, "verdict": "refute"}], answerEvidenceId="v4:3:knowledge:" + cardkey, requiresEvidence=["v4:3:knowledge:" + cardkey], evidencePool="actually-acquired-v4-cards-only", judgment="refute")
    taskmap["T3-PN-01"]["lanes"] = [{"id": lane, "actor": actor, "lines": [e["id"] for e in taskmap["T3-PN-01"]["lines"] if e["actor"] == actor]} for lane, actor in (("왼쪽", "akari"), ("가운데", "sora"), ("오른쪽", "nana"))]
    make("T3-MM-01", "mindmine", "165", 55, prompt="반사와 직접 시야가 겹치는 경계를 찾는다", regionDescription="B 관찰 모퉁이에서 H 작업 홈 출구로 이어지는 반사/직접 시야의 겹침", imageDescription="기존 실제 통로와 거울의 평면", wrongVariants=[{"cause": "wrong-region:" + key, "script": events("165", a, b)} for key, a, b in (("A", 68, 71), ("B", 72, 75), ("D", 76, 81))], success=events("165", 82, 87), bindings=[{"kind": "forensicImageRegions", "required": True, "description": "Bind the actually inspected B/H reflection boundary. A numeric option list is not mine geometry."}], runtimeReady=False)
    make("T3-FA-01", "anagram", "165", 128, intro=says("165", 130, 135), answer="빙의고정", answerGlyphs=["빙", "의", "고", "정"], distractors=["귀", "환", "소", "생"], success=events("165", 143, 147), mechanic={"selectGlyphCount": 1, "arrivalJudgment": True, "poolSlots": 20, "specialCollectibleSeparate": True}, retryPolicy="wrongSlotOnly", wrongText={"귀환": "돌아갈 자기 몸이 사망했어.기본 시간이 지나면 돌아간다는 줄을 그대로 붙일 수 없어.", "소생": "다른 몸에서 지속하는 것과 죽은 몸이 살아나는 건 달라.두 번째 죽음을 없던 일로 만들지 마.", "other": "죽은 뒤 처음 들어가는 조건이 아니야.이미 들어가 있던 쪽의 지속을 말해야 해."})
    for tid, a, b, answer in (("T3-RL-01", 476, 505, "B"), ("T3-RL-02", 506, 535, "A"), ("T3-RL-03", 536, 565, "B")):
        rows = docs["13c1"].lines[a - 1:b]
        question = next(l.split("**질문:**", 1)[1].strip() for l in rows if l.startswith("**질문:**"))
        opts = [{"id": m[1], "label": m[2]} for l in rows if (m := re.match(r"^- ([ABC]) 「(.+)」[.]?$", l))]
        heads = [(i, re.match(r"^#### ([ABC]) — (정답|오답)", docs["13c1"].lines[i - 1])) for i in range(a, b + 1)]
        heads = [(i, m) for i, m in heads if m]
        scripts = {m[1]: events("13c1", i + 1, heads[n + 1][0] - 1 if n + 1 < len(heads) else b) for n, (i, m) in enumerate(heads)}
        make(tid, "reasoning", "13c1", a, questions=[{"id": tid + ":link:1", "q": question, "options": opts, "answer": answer, "wrong": {k: v for k, v in scripts.items() if k != answer}, "success": scripts[answer], "retryPolicy": "currentLinkOnly"}], answer=answer)

    # A single required intentional inversion; the truth is not first emitted
    # into the courtroom then retrospectively erased.
    make("T3-LIE-01", "lie", "13c2", 35, fact="소라를 비난하지 않은 글", lie="소라를 비난한 글", holdToInvert=True, releaseRestoresFact=True, targetActor="ken", trueCardAttempt=events("13c2", 39, 43), intro=events("13c2", 45, 48), success=[], requiresEvidence=["v4:3:knowledge:private-phrase"], answerEvidenceId="v4:3:knowledge:private-phrase", factAttemptReturnsSameInput=True, cancelPausesScene=True, noHonestSuccessBypass=True, noOriginalTextDisplayed=True)

    pairs = []
    # Exact authored opposing propositions and response speakers, not colour
    # assignments inferred from trust or the current culprit answer.
    for index, (a, b, them, us) in enumerate(((214, 229, "satsuki", "sho"), (230, 243, "ken", "nana"), (244, 257, "koto", "rin"), (258, 279, "akari", "haruka"), (280, 293, "rei", "mio")), 1):
        raw = docs["165"].lines[a + 1]
        quoted = re.search(r"「(.+)」", raw)
        if not quoted:
            raise ValueError("T3 scrum proposition moved")
        proposition = quoted[1].replace("**", "")
        keyword = re.search(r"\*\*(.+?)\*\*", quoted[1])[1]
        wrong_line = next(i for i in range(a, b + 1) if docs["165"].lines[i - 1].startswith("**오답"))
        response = says("165", a, wrong_line - 1)
        pairs.append({"id": f"T3-SD-01:round:{index}", "them": them, "themText": proposition, "keyword": keyword, "us": us, "usText": response[0]["text"], "responseKeyword": re.findall(r"\*\*(.+?)\*\*", docs["165"].lines[a + 3])[-1].rsplit("/", 1)[0].strip(), "success": events("165", response[0]["source"]["line"], wrong_line - 1), "wrong": events("165", wrong_line + 1, b), "source": docs["165"].ref(a)})
    make("T3-SD-01", "scrum", "165", 196, intro=events("165", 199, 213), pairs=pairs, teams={"us": ["mio", "rin", "nana", "sho", "haruka"], "them": ["ken", "koto", "satsuki", "akari", "rei"]}, success=events("165", 294, 303), teamMeaning="current proof positions, not blanket loyalty")

    make("T3-AA-01", "armament", "165", 304, waves=[{"id": f"T3-AA-01:wave:{i}", "script": events("165", a, b), "retryPolicy": "sameWave"} for i, (a, b) in enumerate(((310, 315), (316, 325), (326, 333)), 1)], answerParts=["리쿠를 죽인 뒤", "돌아가지 않고", "소라 몸을 죽여", "켄의 의식을 없앴다"], distractors=["리쿠가 살아 있을 때", "정상 귀환한 다음", "이미 죽은 몸에 새로 들어가", "켄이 자리를 비켰다"], success=events("165", 342, None), bindings=[{"kind": "rhythmWaveTiming", "required": True, "description": "Authored 3 waves require actual beat/timing windows and native wave input, not automatic dialogue advance."}], runtimeReady=False)
    slots = []
    for no, (a, b, answer) in enumerate(((23, 58, "1A"), (59, 94, "2C"), (95, 130, "3B"), (131, 166, "4A"), (167, 202, "5C"), (203, 238, "6B")), 1):
        candidates = []
        for line in docs["159"].lines[a - 1:b]:
            match = re.match(r"^\|([1-6][ABC])\|([^|]+)\|(정답|오답)\|", line)
            if match:
                candidates.append({"id": match[1], "imageDescription": match[2]})
        heads = [(i, m[1]) for i in range(a, b + 1) if (m := re.match(r"^### ([1-6][ABC])를 놓았다", docs["159"].lines[i - 1]))]
        responses = {key: events("159", i + 1, heads[n + 1][0] - 1 if n + 1 < len(heads) else b) for n, (i, key) in enumerate(heads)}
        slots.append({"id": f"T3-MG-01:slot:{no}", "candidates": candidates, "answer": answer, "wrong": {k: v for k, v in responses.items() if k != answer}, "success": responses[answer], "retryPolicy": "currentSlotOnly", "source": docs["159"].ref(a)})
    make("T3-MG-01", "climax", "159", 23, slots=slots, bindings=[{"kind": "authoredComicPanels", "required": True, "description": "The exact 18 authored candidate panels need actual images; text-only candidates are not the finished climax mechanic."}], runtimeReady=False)
    make("T3-VOTE-01", "vote", "13c3", 987, answer="sora", candidates=["mio", "rei", "sora", "ken", "nana", "riku", "akari", "yuu", "koto", "satsuki", "taiga", "rin", "sho", "ai", "haruka", "kaede"], deadCandidatesSelectable=True, finalVote=True, actorDisplaySeparateFromCulprit=True, authoredResult={"total": 10, "sora": 9, "ken": 1, "otherVoteOwnerRevealedOnlyAfterResult": True}, noWrongCanonicalResult=True)


def _physical_display(nodes, taskmap):
    """Author tags retain source evidence; runtime names follow knowledge time."""
    def patch(event, post_identity=None):
        if not isinstance(event, dict):
            return
        if event.get("type") == "say" and "켄의몸" in event.get("delivery", ""):
            source = event.get("source", {})
            prefix = source.get("file", "").split("_", 1)[0]
            line = source.get("line", 0)
            public_demo = prefix == "13a6" or (prefix == "13a12" and line < 244)
            revealed = post_identity if post_identity is not None else (prefix in {"13c3", "13d", "102", "116", "159", "172", "191"} or (prefix == "13c2" and line >= 399))
            # 102 trial/results and 116/159/172 chapter3 ranges are post-T25.
            event.update(actor="ken", speaker="소라(켄의 몸)" if public_demo or revealed else "켄의 몸", voiceActor="ken", physicalActor="ken", authorSpeaker="소라", preserveHistoricalDisplay=True)
        for key, value in list(event.items()):
            if key in {"source", "routing", "canonicalGuard"}:
                continue
            if isinstance(value, list):
                for item in value:
                    patch(item, post_identity)
            elif isinstance(value, dict):
                patch(value, post_identity)
    for node in nodes.values():
        patch(node)
    for tid, task in taskmap.items():
        if task.get("chapter") != "3":
            continue
        after = tid in {"T3-NS-A10", "T3-CULPRIT-A01", "T3-RL-A02", "T3-RL-A03", "T3-AA-01", "T3-MG-01", "T3-VOTE-01"}
        patch(task, after)
        for line in task.get("lines", []):
            for target in task.get("targets", []):
                if target.get("lineId") == line.get("id"):
                    target["actor"] = line.get("actor", target.get("actor"))
        for lane in task.get("lanes", []):
            if lane.get("actor") == "sora":
                lane["actor"] = "ken"
