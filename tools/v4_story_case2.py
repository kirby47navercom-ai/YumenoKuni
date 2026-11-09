"""Explicit chapter-two routes; each choice owns only its observed source range.

This module never publishes output. The central generator supplies sources,
free-time graphs and task definitions. Unreviewed continuations remain gates.
"""
from __future__ import annotations

from typing import Any


REVIEWED_HASHES = {'12a': '76c22ed512dcabe991230b1d8f153d0e25065a0c96ecb487e3f229c90a6317e0', '12a2': '1af5c5d17845bf37be42e4b295707d06b4bc6ac2e1d731a29f33c1b0df61b967', '12a3': '79cc5431884bc10f2cf27ece2b8812d0eaec4be6042433acdcd49b28c8570ac7', '12a4': '9b19a07bdb9a869843fe3e17ea82f9300845a039bf04ac80b7ab886ce6c56475', '12a5': '5856664778f76feae589de7a5cc163f9748a86255da86540e9e8685bd8d456ef', '12a6': 'fff7e39e996a021d6f1c6b443278aa3a09a8c6271e17a8e807d7ea72a2169f9f', '12a7': '89c8012962fd168540f93a1b5283f2d99eb10284e782da55b9b2d562d0179af1', '12b1': '2574cba1fd5e559572086a9d26ead0815ef6683601fec3d6dbf6216b6284a038', '12b2': '048d002f839de495a281083fbd320ab74a35e568ddfc9b9cd5199abf13e3776d', '12b3': '75c3e6463227cb1d53f085712d574014368cebe0183f411c4be8ee446503ac06', '12b4': 'c92988172538c793246bf99a3f145676b714d07f25697410b4cc29bf8f1fa144', '125': 'ec5b4bb35e5afff4aff673df1c10d905d968a3ff9dc5161ec7b1a376ab52c29b', '140': '47ae02ba631716f0ab05b5105f6f4bb283e04fbd9ff28364c0fd690ce8dc6619', '84': 'a1c013375b2e9fbf7c6c6ee68674a5ced13af959834103836d289d4f289a7442', '94': 'ecfb1eb3783c95ef739bc0dba925ba6eef2cac814a647eb588ca8c40c94f3054', '105': '6d2726b2b343cb05485ce5237a2623c0f33bc84d87feb71186215f43bf5b5b5f', '179': '51658fd599b4d132d105b0abf6a0c6172febf032be46719bf94fe66d7550faa3', '68': '74fe7c82fbed95fadfbe9bfa27f5551f0879e76ecad7a70997168af75ce6cf2b', '172': '8cb27f9c7af285abd04a1473857e5e0d1f1e0cd73006cf6c0fe5d976d8646328', '111': '365bd182bdd1e32f1dedc26032523b61d4dd16f1d8539ccc9221e6ef6b31e35a', '69': '47f22d9c2c0e6b673f7da9521303208be14f074a6103e199ac6fa1029f520be6', '177': '1cb31b1cedd649c735e3b92e4a323d06d07ebb627504c010b1f567c8c4f224b4', '132': '21b1571f9f2cd4cbcb44dddb0119798ae9bd4b7b2ee1987818ca95bc37acdf59', '05': '1ffb0225c37ea827d1fee01ef85ef7a50c8da11e27772ee3653501ae56b9c9ea'}

REVIEWED_HASHES['12c1'] = 'd298af172597c751832482fbc1eca10e0b41b6d1987db1cd000c81342ec655a4'
REVIEWED_HASHES['97'] = '394e987c077b34532b728ee882ebcb971e549e24682908483cea3f59f17b9a54'
REVIEWED_HASHES['164'] = '743128d0d5fc46f6498fc5173e6107822e67e6b2fe03de03cf7c5dff6609fedc'
REVIEWED_HASHES['182'] = 'a818493aee5bec401973b48c19d7240789b8fad7392292ac7711cf10804ee8ff'
REVIEWED_HASHES['12c2'] = '58e1eb66bced8fa72e1abe3c3d2639e9b2360ee5f9a856400f08ac95f4dcb1d7'
REVIEWED_HASHES['169'] = '954fbe7b6d6f59c6f2dedd9c564654f08a20f15f378fdc284c27ec66d7428964'
REVIEWED_HASHES.update({'113': 'a7784abb1bf6c2c47fee60aa9cb34dc9a24b961a78d8e2c1602cc4c2483635c1', '126': '0642d8034240c66d95b65d4edd118c7a57e4b704412bc0c7ad79fff63a7b4f75', '12c3': 'a598e0c8311efd407d25aaa5026845ddebe2930d46f00c6e7fd458a50ac8236e', '12d': '575b97dd1832b8b51351b856a20504ddf574e6620f12a68fab04d052f7b9e393', '138': '8bf1b47652a38ffaa3fbe150d79aa1e0319281f0b2c454e4ce38ac6aa587f424', '141': '82ea3f0a2506968a8dad4636c513d311971d99550b4692bf7449a62fa5208d19', '155': '08a7a14c556c030ef4c8cf99aed520b039e9909e77072667f90abcf4385df219', '158': '393a2e04e23403701b98a51519fcfe61bce5c57f367bb60935538cc8a14ac3b1', '79': '12d1dd74fe9b021446773c00269326ca04384c424d72096209a5d4306b0b59cd'})
REVIEWED_HASHES['145'] = '1528665171ed516d9adc6b6a5be95330b5197647a669495bbc69d00ddc3da2d0'
REVIEWED_HASHES['149'] = 'ebea4c61e7da3b6c4af5202170e1f4147cdc8d941c32495e3a9b64e63559efb6'
REVIEWED_HASHES['190'] = '6cbf0021d5e10ca33d48fefb6370f5418790ed118d39967da4d34364e266e156'
SOURCE_PREFIXES = tuple(REVIEWED_HASHES)


def route_source_hashes(sources):
    docs = {s.prefix: s for s in sources.values()}
    return {docs[prefix].name: digest for prefix, digest in REVIEWED_HASHES.items()}


def _late_completion(meeting):
    # The normal first-meeting completion and the actual late calendar route
    # are different facts, both earned only when this exact call returns.
    first = {"87": ("34", "HA01Late5"), "89": ("24", "SO01Late5"), "90": ("30", "RI01Late5"), "143": ("20", "RIN01Late5"), "144": ("21", "KO01Late5"), "145": ("25", "AI01Late5"), "146": ("26", "YU01Late5"), "147": ("27", "RE01Late5"), "148": ("23", "SHO01Late5"), "149": ("32", "SA01Late5"), "150": ("28", "KE01Late5"), "151": ("31", "AK01Late5")}
    later = {"RI02Late6AM": "48", "RIN02Late6AM": "35", "AI02Late6AM": "43", "YU02Late6AM": "44", "SA02Late6AM": "49", "AK02Late6AM": "39", "AI03Late6PM": "52", "RE02Late6PM": "45", "SA03Late6PM": "63", "RIN03Late7": "54", "YU03Late7": "53", "SHO02Late7": "41"}
    if meeting in first:
        base, flag = first[meeting]
        return {f"fte:{base}:complete": True, flag: True}
    if meeting in later:
        return {f"fte:{later[meeting]}:complete": True, meeting: True}
    return {}


class Router:
    def __init__(self, graph, sources, freetime):
        self.g = graph
        self.docs = {s.prefix: s for s in sources.values()}
        self.freetime = freetime
        self.pending = []
        self.used = set()

    def seq(self, prefix, first, last, target):
        source = self.docs[prefix]
        self.used.add(prefix)
        return self.g.sequence(source, first, last, target)

    def gate(self, key, reason, prefix=None, line=1):
        ident = "v4:2:pending:" + key
        self.pending.append(ident)
        return self.g.add(ident, {"type": "gate", "reason": reason, **({"source": self.docs[prefix].ref(line)} if prefix else {})})

    def branch(self, key, flag, cases, default):
        return self.g.add("v4:2:branch:" + key, {"type": "branch", "cases": [{"flag": flag, "equals": value, "to": target} for value, target in cases], "default": default})

    def required_branch(self, key, flag, cases, prefix, line):
        missing = self.gate(key + ":missing", "The actual earlier choice is required; no default memory is invented.", prefix, line)
        return self.branch(key, flag, cases, missing)

    def menu(self, prefix, key, line, rows):
        return self.g.add("v4:2:menu:" + key, {"type": "menu", "q": self.docs[prefix].lines[line - 1].split("—")[-1].strip(), "source": self.docs[prefix].ref(line), "options": [{"id": letter, "label": label, "to": target, "set": {key: letter}} for letter, label, target in rows]})

    def window(self, key, prefix, line, candidates, target):
        options = []
        for meeting, label, requires in candidates:
            # Late introductions have their own identities. A base meeting is
            # never substituted for an uncompiled late introduction.
            fte = self.freetime.get(meeting)
            if fte:
                for ident, node in fte["nodes"].items():
                    if ident not in self.g.nodes:
                        self.g.add(ident, node)
                jump = self.g.add(f"v4:2:{key}:call:{meeting}", {"type": "call", "target": fte["entry"], "returnTo": target, "onReturnSet": {fte["completionFlag"]: True, f"window:{key}:completed": True, **_late_completion(meeting)}})
            else:
                jump = self.gate(f"{key}:meeting:{meeting}", "This exact meeting/late introduction is not yet compiled. Do not grant completion, private memories or borrowed items.", prefix, line)
            options.append({"id": meeting, "label": label, "to": jump, "requires": requires})
        options.append({"id": "REST", "label": "혼자 쉰다", "to": target, "set": {f"window:{key}:completed": True}})
        return self.g.add("v4:2:window:" + key, {"type": "menu", "selectionRole": "freetime", "q": "지금 만날 사람", "maxSelections": 1, "poolComplete": all(x[0] in self.freetime for x in candidates), "source": self.docs[prefix].ref(line), "options": options})


def _day_six_performance(r, target):
    s, b, rb = r.seq, r.branch, r.required_branch
    # The late-night echo consumes C11, not C05's unobserved second half.
    echo = rb("C11:night", "2-C11", [("A", s("105", 287, 301, target)), ("B", s("105", 305, 317, target)), ("C", s("105", 321, 335, target))], "105", 281)
    dinner = s("12a3", 880, 1278, echo)
    ai_b = b("AI03:B", "F-AI03-B", [("B1", s("12a3", 856, 860, dinner)), ("B2", s("12a3", 864, 868, dinner)), ("B3", s("12a3", 872, 876, dinner))], dinner)
    ai_a = b("AI03:A", "F-AI03-A", [("A2", s("12a3", 844, 850, ai_b))], ai_b)
    ai_read = b("AI03:read", "fte:52:complete", [(True, ai_a)], dinner)
    dinner_intro = s("12a3", 824, 839, ai_read)
    after_free = b("C05:private-door", "2-C05", [("B", s("12a3", 784, 822, dinner_intro))], dinner_intro)
    free = r.window("F2-C", "12a3", 768, [
        ("52", "아이와 만난다", {"fte:25:complete": True, "fte:43:complete": True, "AI01Late5": False}),
        ("AI03Late6PM", "아이와 늦은 세 번째 만남", {"AI02Late6AM": True}),
        ("RE02Late6PM", "레이와 늦은 두 번째 만남", {"RE01Late5": True}),
        ("SA03Late6PM", "사츠키와 늦은 세 번째 만남", {"SA02Late6AM": True}),
    ], after_free)
    free_intro = s("12a3", 768, 770, free)
    a_tail = s("12a3", 554, 560, free_intro)
    a_echo = rb("C08:endA", "2-C08", [("A", s("12a3", 528, 532, a_tail)), ("B", s("12a3", 536, 542, a_tail)), ("C", s("12a3", 546, 550, a_tail))], "12a3", 522)
    a = s("12a3", 466, 466, s("12a3", 492, 520, a_echo))
    b_tail = s("12a3", 592, 766, free_intro)
    b_echo = rb("C08:endB", "2-C08", [("A", s("12a3", 572, 574, b_tail)), ("B", s("12a3", 578, 580, b_tail)), ("C", s("12a3", 584, 588, b_tail))], "12a3", 566)
    returned = rb("C05:bag-return", "2-C05", [("A", s("94", 177, 183, a)), ("B", s("94", 187, 197, s("12a3", 564, 564, b_echo)))], "94", 175)
    bag = s("94", 141, 173, returned)
    choice = r.menu("12a3", "2-C05", 444, [("A", "약속한 물품을 돌려준 뒤 공연으로 돌아온다", s("12a3", 448, 462, bag)), ("B", "오늘은 여기까지 듣고 간다고 말한다", s("12a3", 470, 486, bag))])
    propbox = s("12a3", 402, 440, choice)
    # C08-A contains a nested callback to exactly the selected C07 lyric.
    song_tail = s("68", 219, 233, propbox)
    c08a_end = s("68", 181, 185, song_tail)
    c07_lyric = rb("C07:sing", "2-C07", [("A", s("68", 169, 169, c08a_end)), ("B", s("68", 173, 173, c08a_end)), ("C", s("68", 177, 177, c08a_end))], "68", 167)
    c08 = r.menu("68", "2-C08", 159, [("A", "객석에서 마지막 말을 한 번 같이 불러 본다", s("68", 163, 165, c07_lyric)), ("B", "유우 목소리로 한 번 더 듣고 싶다고 한다", s("68", 189, 203, song_tail)), ("C", "말 대신 박수를 친다", s("68", 207, 215, song_tail))])
    song_common = s("68", 143, 157, c08)
    c07 = r.menu("68", "2-C07", 81, [("A", "쉬었다라고 한다", s("68", 85, 99, song_common)), ("B", "삐졌다라고 한다", s("68", 103, 121, song_common)), ("C", "고르지 않고 유우가 정한 걸 듣겠다고 한다", s("68", 125, 141, song_common))])
    song = s("68", 5, 79, c07)
    second_song = s("12a3", 312, 398, song)
    w_end = s("179", 191, 209, second_song)
    w_menu = r.menu("179", "W2-C14", 91, [("A", "다른 흉내를 붙여 분위기를 돌린다", s("179", 95, 123, w_end)), ("B", "유우에게 다음 노래를 시작하라고 한다", s("179", 127, 149, w_end)), ("C", "잠깐 앞자리를 떠나 음향 탁자 옆으로 간다", s("179", 153, 189, w_end))])
    w = s("179", 5, 89, w_menu)
    first_song = s("12a3", 234, 308, w)
    play_end = s("105", 245, 277, first_song)
    c11 = r.menu("105", "2-C11", 115, [("A", "리쿠 옆에서 답을 맞힌다", s("105", 119, 149, play_end)), ("B", "하루카와 짝을 지어 몸짓을 한다", s("105", 153, 193, play_end)), ("C", "켄도 답을 모르는 문제를 내 보라고 한다", s("105", 197, 241, play_end))])
    play = s("105", 5, 113, c11)
    titles = s("12a3", 213, 229, play)
    riku = b("RI02:recall", "F-RI02-B", [("B1", s("12a3", 181, 189, titles)), ("B2", s("12a3", 193, 199, titles)), ("B3", s("12a3", 203, 209, titles))], titles)
    riku_read = b("RI02:read", "fte:48:complete", [(True, riku)], titles)
    ken = b("KE02:recall", "F-KE02-B", [("B1", s("12a3", 151, 159, riku_read)), ("B2", s("12a3", 163, 167, riku_read)), ("B3", s("12a3", 171, 177, riku_read))], riku_read)
    ken_read = b("KE02:read", "fte:47:complete", [(True, ken)], riku_read)
    seating = s("12a3", 143, 143, ken_read)
    invite = rb("C04:arrival", "2-C04", [("A", s("12a3", 125, 129, seating)), ("B", s("12a3", 133, 139, seating))], "12a3", 123)
    before_invite = s("12a3", 107, 121, invite)
    borrow = s("94", 5, 133, before_invite)
    sa_end = s("12a3", 102, 102, borrow)
    sa_a = b("SA03:A", "F-SA03-A", [("A1", s("12a3", 86, 88, sa_end)), ("A2", s("12a3", 92, 94, sa_end)), ("A3", s("12a3", 98, 100, sa_end))], sa_end)
    sa_mid = s("12a3", 80, 80, sa_a)
    sa_b = b("SA03:B", "F-SA03-B", [("B1", s("12a3", 70, 72, sa_mid)), ("B2", s("12a3", 64, 66, sa_mid)), ("B3", s("12a3", 76, 78, sa_mid))], sa_mid)
    sa_intro = s("12a3", 58, 60, sa_b)
    sa_read = b("SA03:read", "fte:63:complete", [(True, sa_intro)], borrow)
    return s("12a3", 6, 54, sa_read)


def _day_six_preparation(r, target):
    s, b, rb = r.seq, r.branch, r.required_branch
    end = s("12a2", 760, 762, target)
    c04 = r.menu("12a2", "2-C04", 698, [("A", "시간과 장소를 전해 주겠다고 한다", s("12a2", 702, 740, end)), ("B", "직접 말하라고 한다", s("12a2", 744, 758, end))])
    preparation = s("12a2", 471, 697, c04)
    free = r.window("F2-B", "12a2", 445, [
        ("39", "아카리와 만난다", {"fte:31:complete": True, "AK01Late5": False}),
        ("42", "소라와 만난다", {"fte:24:complete": True, "SO01Late5": False}),
        ("47", "켄과 만난다", {"fte:28:complete": True}),
        ("54", "린과 세 번째 만남", {"fte:20:complete": True, "fte:35:complete": True, "RIN01Late5": False}),
        ("63", "사츠키와 세 번째 만남", {"fte:32:complete": True, "fte:49:complete": True, "SA01Late5": False}),
        ("RI02Late6AM", "리쿠와 늦은 두 번째 만남", {"RI01Late5": True, "fte:48:complete": False}),
        ("RIN02Late6AM", "린과 늦은 두 번째 만남", {"RIN01Late5": True}),
        ("AI02Late6AM", "아이와 늦은 두 번째 만남", {"AI01Late5": True}),
        ("YU02Late6AM", "유우와 늦은 두 번째 만남", {"YU01Late5": True}),
        ("SA02Late6AM", "사츠키와 늦은 두 번째 만남", {"SA01Late5": True}),
        ("AK02Late6AM", "아카리와 늦은 두 번째 만남", {"AK01Late5": True}),
    ], preparation)
    free_intro = s("12a2", 445, 447, free)
    after_c10 = s("12a2", 406, 443, free_intro)
    echo_c10 = rb("C10:later", "2-C10", [("A", s("12a2", 378, 387, after_c10)), ("B", s("12a2", 390, 397, after_c10)), ("C", s("12a2", 400, 405, after_c10))], "12a2", 376)
    laundry = s("12a2", 236, 375, echo_c10)
    wash_end = s("84", 197, 213, laundry)
    key = rb("C03:key-return", "2-C03", [("A", s("84", 165, 181, wash_end)), ("B", s("84", 185, 195, wash_end))], "84", 161)
    pan_common = s("84", 157, 160, key)
    pan_seen = s("84", 129, 142, pan_common)
    pan_unseen = s("84", 143, 156, pan_common)
    c10 = r.menu("84", "2-C10", 61, [("A", "유우만 닦게 하는 건 얄밉다고 말한다", s("84", 69, 87, pan_seen)), ("B", "린이 닦은 접시까지 포함해서 다시 나누자고 한다", s("84", 91, 109, pan_seen)), ("C", "둘이 정하라고 하고 먼저 나간다", s("84", 113, 127, pan_unseen))])
    pan = s("84", 5, 60, c10)
    breakfast = s("12a2", 172, 233, pan)
    egg = rb("C03:egg", "2-C03", [("A", s("12a2", 164, 167, breakfast)), ("B", s("12a2", 168, 171, breakfast))], "12a2", 164)
    morning_common = s("12a2", 154, 163, egg)
    morning = rb("C03:morning", "2-C03", [("A", s("12a2", 98, 127, morning_common)), ("B", s("12a2", 128, 153, morning_common))], "12a2", 94)
    night = s("140", 5, 245, morning)
    c03_common = s("12a2", 88, 90, night)
    c03 = r.menu("12a2", "2-C03", 38, [("A", "내일 아침 문을 열겠다고 한다", s("12a2", 42, 64, c03_common)), ("B", "맡겠다고 한 말을 거둔다. 함께 다른 방법을 찾는다", s("12a2", 68, 86, c03_common))])
    return s("12a2", 6, 37, c03)


def _day_five(r, target):
    s, b, rb = r.seq, r.branch, r.required_branch
    tail = s("12a", 624, 672, target)
    late_a3=r.g.add('v4:2:menu:AI01Dinner5A3',{'type':'menu','q':'작은 조각을 먹을까','source':r.docs['145'].ref(73),'options':[{'id':'EAT','label':'작은 조각을 먹는다','to':s('145',77,77,tail),'set':{'AI01Dinner5A3':'EAT','AI01Dinner5A3Eat':True}},{'id':'LEAVE','label':'오늘도 남긴다','to':s('145',81,81,tail),'set':{'AI01Dinner5A3':'LEAVE','AI01Dinner5A3Leave':True}}]})
    late_ai=rb('AI01Late5:actual-dinner','F-AI01-A',[('A1',s('145',67,67,tail)),('A2',s('145',71,71,tail)),('A3',late_a3)],'145',65)
    after_day = b("AI01Late5:callback", "AI01Late5", [(True, late_ai)], tail)
    shared = s("12a", 502, 621, after_day)
    kaede = b("KA01:memory", "fte:22:complete", [(True, s("12a", 494, 497, shared))], s("12a", 498, 501, shared))
    kitchen_end = s("12a", 444, 493, kaede)
    kitchen_a = s("12a", 362, 418, kitchen_end)
    kitchen_b = s("12a", 420, 440, kitchen_end)
    c02 = r.menu("12a", "2-C02", 338, [("A", "유우와 주방으로 간다", s("12a", 342, 346, kitchen_a)), ("B", "라운지에 남는다", s("12a", 350, 356, kitchen_b))])
    evening = s("12a", 286, 337, c02)
    candidates = [(p, label, {f"fte:{prior}:complete": True}) for p, label, prior in [("35", "린과 만난다", "20"), ("41", "쇼와 만난다", "23"), ("44", "유우와 만난다", "26"), ("45", "레이와 만난다", "27"), ("48", "리쿠와 만난다", "30")]]
    candidates += [(p, label + ("과" if label in ("린", "켄") else "와") + " 늦은 첫 만남", {f"fte:{prior}:complete": False}) for p, label, prior in [("87", "하루카", "34"), ("89", "소라", "24"), ("90", "리쿠", "30"), ("143", "린", "20"), ("144", "코토", "21"), ("145", "아이", "25"), ("146", "유우", "26"), ("147", "레이", "27"), ("148", "쇼", "23"), ("149", "사츠키", "32"), ("150", "켄", "28"), ("151", "아카리", "31")]]
    free = r.window("F2-A", "12a", 248, candidates, evening)
    carry_common = s("12a", 232, 247, free)
    stay = s("12a", 210, 223, carry_common)
    leave = s("12a", 224, 231, carry_common)
    c01 = r.menu("12a", "2-C01", 178, [("A", "유우 옆에 남는다", s("12a", 182, 188, stay)), ("B", "나나와 조금 떨어진 곳으로 간다", s("12a", 192, 200, stay)), ("C", "재료 운반을 마무리하러 간다", s("12a", 204, 206, leave))])
    after_shop = s("12a", 140, 177, c01)
    menu_title = s("125", 5, 175, after_shop)
    return s("12a", 6, 137, menu_title)


def _day_seven(r, target):
    s, b, rb = r.seq, r.branch, r.required_branch
    dinner = s("12a4", 732, 752, target)
    retract_end = s("111", 329, 339, dinner)
    retract = b("C12:retract-note", "2-C12", [("B", s("111", 319, 325, retract_end))], retract_end)
    hotel_return = s("111", 259, 315, retract)
    notice_echo = rb("C12:disclose", "2-C12", [("A", s("111", 219, 229, hotel_return)), ("B", s("111", 233, 241, hotel_return)), ("C", s("111", 245, 255, hotel_return))], "111", 217)
    notice_reveal = s("111", 209, 215, notice_echo)
    yuu_tail = s("12a4", 718, 728, notice_reveal)
    c07 = rb("C07:doubt", "2-C07", [("A", s("12a4", 706, 706, yuu_tail)), ("B", s("12a4", 710, 710, yuu_tail)), ("C", s("12a4", 714, 714, yuu_tail))], "12a4", 704)
    c08 = rb("C08:doubt", "2-C08", [("A", s("12a4", 682, 686, c07)), ("B", s("12a4", 690, 692, c07)), ("C", s("12a4", 696, 700, c07))], "12a4", 678)
    yuu_visit = s("12a4", 654, 676, c08)
    notice_end = s("111", 161, 201, yuu_visit)
    c12 = r.menu("111", "2-C12", 105, [("A", "다시 그런 일을 겪고 싶지 않아 게시를 돕는다", s("111", 109, 121, notice_end)), ("B", "합의하지 않은 공고라는 자기 글을 옆에 둔다", s("111", 125, 141, notice_end)), ("C", "돕거나 고쳐 쓰지 않고 본 채로 떠난다", s("111", 145, 157, notice_end))])
    notice = s("111", 5, 103, c12)
    after_sho = s("12a4", 588, 650, notice)
    sho_choice = rb("C06:sho", "2-C06", [("A", s("12a4", 462, 534, after_sho)), ("B", s("12a4", 538, 586, after_sho))], "12a4", 460)
    after_power = s("12a4", 400, 458, sho_choice)
    yu03_common = s("12a4", 388, 396, after_power)
    yu03_signed = s("12a4", 370, 376, yu03_common)
    yu03_choice = rb("YU03:B", "F-YU03-B", [("B1", yu03_signed), ("B2", yu03_signed), ("B3", s("12a4", 380, 384, yu03_common))], "12a4", 368)
    yu03 = b("YU03:read", "fte:53:complete", [(True, yu03_choice)], after_power)
    # Public quotation and private file must be shown as real documents rather
    # than silently discarded as editorial blockquotes.
    kitchen_after_page = s("12a4", 264, 362, yu03)
    public_page = r.g.add("v4:2:document:ai-request", {"type": "document", "title": "첫날 조 편성 의견", "rows": [r.docs["12a4"].lines[261][2:]], "private": False, "source": r.docs["12a4"].ref(262), "next": kitchen_after_page})
    kitchen = s("12a4", 254, 260, public_page)
    teacher_end = s("172", 31, 275, kitchen)
    teacher_page = r.g.add("v4:2:document:ken-role-request", {"type": "document", "title": "켄이 공개한 자기 작성문", "rows": [r.docs["172"].lines[28][2:]], "private": False, "source": r.docs["172"].ref(29), "next": teacher_end})
    teacher = s("172", 5, 27, teacher_page)
    private_tail = s("12a4", 234, 236, teacher)
    own_page = r.g.add("v4:2:document:mio-role-request", {"type": "document", "title": "미오의 자기 파일", "rows": [r.docs["12a4"].lines[231][2:]], "private": True, "source": r.docs["12a4"].ref(232), "next": private_tail})
    c06 = r.menu("12a4", "2-C06", 222, [("A", "자기 것을 가져와 혼자 읽는다", s("12a4", 226, 230, own_page)), ("B", "읽지 않고 칸 문을 닫는다", s("12a4", 240, 248, teacher))])
    morning = s("12a4", 54, 220, c06)
    free = r.window("F2-D", "12a4", 40, [
        ("36", "코토와 만난다", {"fte:21:complete": True, "KO01Late5": False}),
        ("53", "유우와 세 번째 만남", {"fte:26:complete": True, "fte:44:complete": True, "YU01Late5": False}),
        ("RIN03Late7", "린과 늦은 세 번째 만남", {"RIN02Late6AM": True}),
        ("YU03Late7", "유우와 늦은 세 번째 만남", {"YU02Late6AM": True}),
        ("SHO02Late7", "쇼와 늦은 두 번째 만남", {"SHO01Late5": True}),
    ], morning)
    return s("12a4", 6, 42, free)


def _waiting_evening(r, target):
    s, rb, b = r.seq, r.required_branch, r.branch
    bedroom = s("12a5", 631, 657, target)
    nana_end = s("177", 247, 325, bedroom)
    cups = r.menu("177", "W2-C03", 169, [("A", "나나가 씻은 컵을 리쿠에게 건넨다", s("177", 173, 195, nana_end)), ("B", "리쿠의 컵만 씻고 방으로 가라고 한다", s("177", 199, 215, nana_end)), ("C", "리쿠의 컵을 자기가 씻겠다고 한다", s("177", 219, 245, nana_end))])
    nana_middle = s("177", 37, 165, cups)
    nana_file = rb("C06:nana-night", "2-C06", [("A", s("177", 25, 27, nana_middle)), ("B", s("177", 31, 33, nana_middle))], "177", 23)
    nana = s("177", 5, 21, nana_file)
    sho_end = s("12a5", 615, 627, nana)
    sho = rb("C06:night", "2-C06", [("A", s("12a5", 523, 593, sho_end)), ("B", s("12a5", 597, 611, sho_end))], "12a5", 521)
    later = s("12a5", 247, 519, sho)
    sa_tail=s('149',147,147,later)
    sa_a=rb('SA03Late6PM:actual-apology','F-SA03-A',[(v,s('149',a,b,sa_tail)) for v,a,b in [('A1',125,127),('A2',131,135),('A3',139,143)]],'149',123)
    sa_common=s('149',113,121,sa_a)
    sa_b=rb('SA03Late6PM:actual-book','F-SA03-B',[(v,s('149',a,b,sa_common)) for v,a,b in [('B1',79,85),('B2',89,97),('B3',101,109)]],'149',77)
    late_sa=s('149',75,75,sa_b)
    sa = b("SA03Late6PM:evening", "SA03Late6PM", [(True, late_sa)], later)
    after_c09 = s("69", 147, 151, sa)
    c09 = r.menu("69", "2-C09", 75, [("A", "기다리게 하려고 식사 순서를 쓴 것은 싫다고 말한다", s("69", 79, 101, after_c09)), ("B", "기다리게 한 마음은 자신도 이해한다고 편든다", s("69", 105, 125, after_c09)), ("C", "더 판단하지 않고 오늘 먹은 감상만 말한다", s("69", 129, 145, after_c09))])
    ai = s("69", 5, 73, c09)
    return s("12a5", 5, 241, ai)


def _day_eight(r, target):
    s, b, rb = r.seq, r.branch, r.required_branch
    discovery = s("12a7", 6, 338, target)
    for node in r.g.nodes.values():
        if node.get("source", {}).get("file") == r.docs["12a7"].name and node["source"]["line"] == 202:
            node["set"] = {"public:ai:body-discovered": True}
    shop = s("12a6", 559, 1075, discovery)
    first_carry = rb("C05:box-memory", "2-C05", [("A", s("12a6", 551, 551, shop)), ("B", s("12a6", 555, 555, shop))], "12a6", 549)
    practice = s("12a6", 349, 547, first_carry)
    before_a1 = s("12a6", 337, 341, practice)
    other_a1 = s("12a6", 345, 345, practice)
    yu01_a = b("YU01:A1", "F-YU01-A", [("A1", before_a1)], other_a1)
    yu01_read = b("YU01:read", "fte:26:complete", [(True, yu01_a)], other_a1)
    arrived = s("12a6", 29, 333, yu01_read)
    chair = s("132", 5, 269, arrived)
    return s("12a6", 5, 25, chair)


CARD_TEXT = {
    "E2-01": ("래피 파일", "사인은 머리에 가해진 강한 타격이에요. 사망 추정은 공연 종료 무렵부터 호텔 귀환 전후의 넓은 범위예요. 함 속 질식이나 분 단위 시각이 확인된 것은 아니에요."),
    "E2-02": ("함의 내부와 걸쇠", "양쪽 뚜껑 받침과 바깥 걸쇠, 남은 추와 천의 위치를 기록했어요. 운반 중의 작은 턱과 호텔 문턱, 닫힌 채 운반했다는 각각의 진술을 남겨요. 처음 적재와 최종 내부 확인은 달라요."),
    "E2-03": ("직원용 통로의 흔적", "통로의 보라색 흔적과 닦은 자국, 벽의 흔적은 함을 끌고 간 바퀴 경로와 달라요. 사진만으로 혈액 주인이나 정확한 시각을 판정하지 않아요."),
    "E2-04": ("무거운 마이크 받침대", "분리된 금속 받침대에 보라색 흔적과 찌그러진 모서리, 벽의 낮은 자국과 맞닿는 마감 조각이 있어요. 차양 추와 다른 물건이며 소유자나 사용자가 곧 살인자는 아니에요."),
    "E2-05": ("장비 적재와 반납", "소라·나나는 일부 추와 천을 넣고 호텔 문을 확인하러 갔어요. 돌아왔을 때 함은 닫혔고 유우는 나머지를 정리했다고 말했어요. 최종 내부를 두 사람이 본 것은 아니에요."),
    "E2-06": ("노랫소리와 몸의 목격", "반복되는 소리의 기억과 카드 파일의 무편집은 달라요. 리쿠는 유우와 함이 떠난 뒤에도 소리가 났고 공용 녹음기 전원을 끈 뒤 카드를 뺐다고 말했어요. 전 공연이 녹음이었다는 결론은 아니에요."),
    "E2-07": ("아이의 생존과 매점 작업", "미오·하루카와의 직접 대화 뒤에도 레이와 리쿠가 각각 아이의 얼굴과 응답을 확인했다고 해요. 눌린 빈 상자에는 돌아온 병이 일부 있어요. 그 뒤 모든 행위나 분 단위 사망을 증명하지는 않아요."),
    "E2-08": ("연결 고리와 접촉 흔적", "아이 손에서 기록 후 회수한 고리 조각은 유우의 개인 재생기에 남은 깨진 경계와 이어져요. 공연 직후 사진에는 연결 고리가 붙어 있어요. 누가 접촉했는지나 마지막에 잡았는지는 이것 하나로 정하지 않아요."),
    "E2-09": ("공명에 관한 실제 관찰과 진술", "미오는7일차 주방에서 갑자기 겁을 느꼈지만 시각·청각이 바뀌거나 보지 못한 공격 장면을 본 일은 없었어요. 그때 유우는 자기 기분이라고 말했어요. 발견 때는 공명을 쓰지 않았다고 답했어요. 그 주장은 각자가 느낀 감정의 원인을 독립 확인한 결과가 아니며 사망 시각이나 사실 전체를 전달하지 않아요."),
    "E2-BAND": ("오전 밴드 확인", "미오와 나나는 오전 켄의 손 부상과 붙인 밴드를 보았어요. 수사에서 확인한 오후 호텔 재등장 때도 밴드가 있었어요. 오후의 모든 새 손상 유무나 도구를 들 수 없었다는 검사는 아니에요."),
    "E2-10": ("접근·인계·접촉의 결합", "생존 목격 뒤 두 입구, 호텔 각자의 직접 관찰, 소라·나나의 귀환 동행과 닫힌 함 인계, 그 뒤의 카드 접근, 소매와 끈의 대조를 함께 검토했어요. 쇼·켄·코토는 로비에서 각자 오간 행동을 계속 보았고 미오·하루카는 귀환 뒤 린의 로비와 다목적실 문 사이 관찰을 확인했어요. 유우는 아이의 귀환을 직접 보았다는 말을 돌아가는 줄 알았다는 말로 고쳤어요. 각 물증 하나가 자동으로 범인 이름을 말하거나 모든 능력 반례를 없애지는 않아요."),
}


def _investigation(r, target):
    s = r.seq
    catalogue = {"v4:" + code: {"id": "v4:" + code, "name": name, "text": text, "source": r.docs["12b3"].ref(71) if code == "E2-BAND" else r.docs["05"].ref(40), "grantPolicy": "actual-source-scope-only"} for code, (name, text) in CARD_TEXT.items()}

    def grant(code, prefix, line, after, revision=False, extra=""):
        name, text = CARD_TEXT[code]
        return r.g.add(f"v4:2:grant:{code}:{prefix}:{line}", {"type": "evidence", "evidenceId": "v4:" + code, "name": name, "text": text + extra, "revision": revision, "source": r.docs[prefix].ref(line), "next": after})

    def hub(key, prefix, first, last, space, after, cards=(), custom=None, target_id="", revisions=(), extra=""):
        ident = "v4:2:investigate:" + key
        returned = r.g.add(ident + ":return", {"type": "return"})
        finish = returned
        for code in reversed(cards):
            finish = grant(code, prefix, last, finish, code in revisions, extra)
        entry = custom(finish) if custom else s(prefix, first, last, finish)
        spot = ident + ":spot"
        flag = spot + ":complete"
        r.g.add(ident, {"type": "investigate", "title": r.docs[prefix].lines[first - 1].lstrip("# "), "source": r.docs[prefix].ref(first), "spots": [{"id": spot, "label": r.docs[prefix].lines[first - 1].lstrip("# "), "space_id": space, "target_id": target_id, "geometryReady": bool(target_id), "interactionPolicy": "authored-world-target" if target_id else "source-backed-inspection-or-interview-awaiting-placement", "entry": entry, "returnTo": ident, "completionFlag": flag, "onReturnSet": {flag: True}, "required": True}], "requiredSpotIds": [spot], "requiredCards": ["v4:" + code for code in cards], "next": after, "orderPolicy": "Successive source scopes preserve the authored actual information dependencies; no arbitrary-order proof is claimed."})
        return ident

    # Re-questioning updates the actual cards. The final combination is not
    # available at the earlier plastic-piece observation.
    leave = s("12b4", 341, 357, target)
    sora = hub("I2-45", "12b4", 205, 339, "hotel_lobby", leave)
    retract = hub("I2-44", "12b4", 177, 203, "hotel_lobby", sora, ("E2-10",))
    cloth = hub("I2-43", "12b4", 157, 175, "hotel_lobby", retract, ("E2-08",), revisions=("E2-08",), extra=" 실제 옷감 봉투의 무늬와 찢긴 경계를 유우 소매에 대조했어요. 유우는 그 사이 겉옷을 빌려주거나 벗어 놓은 적 없다고 답했어요. 사진으로 작은 소매 파손의 정확한 발생 시각은 확정하지 못해요.")
    load = hub("I2-42", "12b4", 141, 155, "performance_stage", cloth, ("E2-05",), revisions=("E2-05",), extra=" 나나가 아래로 넣었던 고리 휜 추는 준비실 밖에 있어요. 앞바퀴 축의 잘라 낸 실 흔적과 낡은 손잡이를 미오가 직접 대조했어요. 같은 용기라도 내용물은 따로 검토해요.")
    handoff = hub("I2-41", "12b4", 127, 139, "performance_stage", load)
    clocks = hub("I2-40", "12b4", 109, 125, "hotel_lobby", handoff)
    exits = hub("I2-39", "12b4", 89, 107, "cold_store", clocks)
    list_scope = hub("I2-38", "12b4", 63, 87, "cold_store", exits)
    last_alive = hub("I2-37", "12b4", 31, 61, "cold_store", list_scope, ("E2-07",), revisions=("E2-07",), extra=" 사츠키는 리쿠에게 응답하는 아이 얼굴을 별도로 보았고 이후 그 문으로 돌아오지 않았다고 해요. 목록 시각과 각자 시선을 돌린 구간을 구별해요.")
    next_answer = hub("I2-36", "12b4", 5, 29, "hotel_lobby", last_alive)
    yuu_requestion = hub("I2-35", "12b3", 271, 303, "hotel_lobby", next_answer)
    nana = hub("I2-34", "12b3", 249, 269, "hotel_multiuse", yuu_requestion)
    private = hub("I2-32b-33", "12b3", 193, 247, "hotel_multiuse", nana)
    sleeve = hub("I2-31-32", "12b3", 139, 191, "hotel_lobby", private)
    tool_check = hub("I2-30", "12b3", 113, 137, "hotel_lobby", sleeve, ("E2-03", "E2-04"), revisions=("E2-03", "E2-04"), extra=" 쇼가 직접 현장에 다녀와 머리 손상과 양립하는 모서리를 확인했고 함의 추·벽 돌출부는 맞지 않는다고 했어요. 레이는 사진 기록 뒤 실제 옷감 조각을 쇼와 분리해 일반 봉투로 가져왔어요. 받침대 자체는 현장에 남아요.")
    hotel = hub("I2-27-29", "12b3", 49, 111, "hotel_lobby", tool_check, ("E2-BAND",))
    individual = hub("I2-25-26", "12b3", 5, 47, "cold_store", hotel)
    box = hub("I2-24", "12b2", 315, 329, "cold_store", individual, ("E2-07",))
    riku_alive = hub("I2-23", "12b2", 291, 313, "cold_store", box)
    audio = hub("I2-19-22", "12b2", 193, 289, "performance_stage", riku_alive, ("E2-06",))
    sound = hub("I2-18", "12b2", 139, 191, "performance_stage", audio)
    entrances = hub("I2-16-17", "12b2", 93, 137, "staff_passage", sound, target_id="fixed_fence")
    tool = hub("I2-15", "12b2", 73, 91, "staff_passage", entrances, ("E2-04",))
    floor = hub("I2-14", "12b2", 53, 71, "staff_passage", tool, ("E2-03",))
    equipment = hub("I2-13", "12b2", 31, 51, "performance_stage", floor, ("E2-05",))
    road = s("12b2", 5, 29, equipment)
    departure = s("12b1", 308, 338, road)
    loading = hub("I2-10", "12b1", 278, 306, "hotel_lobby", departure)
    fragments = hub("I2-09", "12b1", 260, 276, "hotel_multiuse", loading, ("E2-08",))
    camera = hub("I2-08", "12b1", 228, 258, "hotel_lobby", fragments)
    feeling = hub("I2-07", "12b1", 202, 226, "hotel_lobby", camera, ("E2-09",))
    player = hub("I2-06", "12b1", 166, 200, "hotel_lobby", feeling)
    carrying = hub("I2-05", "12b1", 138, 164, "hotel_multiuse", player, ("E2-02",))
    plastic = hub("I2-04", "12b1", 102, 136, "hotel_multiuse", carrying)

    def scene(finish):
        common = s("12b1", 94, 100, finish)
        menu = r.menu("12b1", "I2-C01", 70, [("A", "현장 전체와 내부 배치를 남긴다", s("12b1", 74, 82, common)), ("B", "얼굴을 피하고 손·함·물건 위치를 나눠 남긴다", s("12b1", 86, 90, common))])
        return s("12b1", 58, 68, menu)

    scene_scope = hub("I2-03", "12b1", 58, 100, "hotel_multiuse", plastic, custom=scene)
    return s("12b1", 6, 56, scene_scope), catalogue


def _bind_trial_cards(r, tasks):
    mapping = {
        "T2-NS-A01": ("E2-01", ["E2-01", "E2-04"]),
        "T2-NS-A02": ("E2-02", ["E2-02"]),
        "T2-NS-A03": ("E2-BAND", ["E2-BAND"]),
        "T2-NS-A04": ("E2-10", ["E2-10"]),
        "T2-NS-A05": ("E2-02", ["E2-02"]),
        "T2-NS-A06": ("E2-10", ["E2-10"]),
        "T2-NS-A07": ("E2-10", ["E2-10", "E2-06"]),
        "T2-NS-A08": ("E2-06", ["E2-06"]),
        "T2-NS-A09": ("E2-08", ["E2-08"]),
        "T2-NS-A10": ("E2-02", ["E2-02", "E2-04"]),
        "T2-PN-A02": ("E2-10", ["E2-10"]),
        "T2-PN-A03": ("E2-06", ["E2-06"]),
        "T2-EVIDENCE-A01": ("E2-06", ["E2-06"]),
        "T2-RS-A02": ("E2-09", ["E2-09"]),
    }
    for ident, (answer, needed) in mapping.items():
        if ident not in tasks:
            continue
        item = tasks[ident]
        if item["source"]["fileSha256"] != r.docs["182"].hash:
            raise ValueError(f"{ident}: compiled task and reviewed source revision differ")
        item.update(answerEvidenceId="v4:" + answer, requiresEvidence=["v4:" + x for x in needed], evidencePool="actually-acquired-v4-cards-only")
        item["bindings"] = [b for b in item.get("bindings", []) if b["kind"] != "evidenceAcquisition"]
        item["runtimeReady"] = not any(b.get("required") for b in item["bindings"])


def _trial_first_half(r, tasks, target):
    s, rb, b = r.seq, r.required_branch, r.branch

    def says(prefix, a, z):
        return [e for e in r.docs[prefix].paragraphs(a, z) if e["type"] == "say"]

    def define(ident, kind, line, **fields):
        tasks[ident] = {"id": ident, "chapter": "2", "sourceKind": "BASELINE", "kind": kind, "source": r.docs["164"].ref(line), "intro": [], "lines": [], "wrong": [], "success": [], "bindings": [], "runtimeReady": True, "retry": {"sameTask": True, "preserveEvidence": True, "preservePublicFacts": True, "cancellationIsSuccess": False}, "return": {"graphNext": True}, **fields}

    pn_lines = says("164", 114, 120)
    pn_target = next(e for e in pn_lines if e["source"]["line"] == 120)
    define("T2-PD-01", "panic", 108, lines=pn_lines, wrongVariants=[{"cause": "wrong-target:rin", "script": says("164", 126, 128)}, {"cause": "true-statement:sora", "script": says("164", 134, 136)}, {"cause": "wrong-evidence:same-color", "script": says("164", 142, 144)}], success=says("164", 150, 162), answerEvidenceId="v4:E2-05", requiresEvidence=["v4:E2-05"], evidencePool="actually-acquired-v4-cards-only", targets=[{"lineId": pn_target["id"], "word": "받을 때도 같은 내용을 본 거지", "verdict": "refute", "actor": "yuu"}], judgment="refute", lanes=[{"id": pos, "actor": actor, "lines": [e["id"] for e in pn_lines if e["actor"] == actor]} for pos, actor in (("왼쪽", "sora"), ("가운데", "yuu"), ("오른쪽", "rin"))])
    ns_lines = says("164", 219, 229)
    ns_target = next(e for e in ns_lines if e["source"]["line"] == 229)
    define("T2-NS-01", "nonstop", 211, lines=ns_lines, wrongVariants=[{"cause": "wrong-evidence:color", "script": says("164", 235, 237)}, {"cause": "wrong-evidence:voice", "script": says("164", 243, 245)}, {"cause": "wrong-evidence:handoff", "script": says("164", 251, 253)}], success=says("164", 259, 269), answerEvidenceId="v4:E2-05", requiresEvidence=["v4:E2-05"], evidencePool="actually-acquired-v4-cards-only", targets=[{"lineId": ns_target["id"], "word": "두 사람이 그렇게 말한 것뿐", "verdict": "refute", "actor": "riku"}], judgment="refute", vpoint={"optional": True, "character": "두"})

    def task(ident, after):
        return r.g.add("v4:input:" + ident, {"type": "task", "taskId": ident, "runtimeReady": tasks[ident]["runtimeReady"], "source": tasks[ident]["source"], "next": after, "success": after})

    tail = s("12c1", 444, 650, target)
    ns = task("T2-NS-01", tail)
    after_panic = s("97", 201, 345, s("12c1", 316, 440, ns))
    pn_end = s("164", 188, 208, after_panic)
    lie_echo = b("T1-LIE-B:second-trial", "T1-LIE-B", [(True, s("164", 168, 186, pn_end))], pn_end)
    pn = task("T2-PD-01", lie_echo)
    c03 = r.menu("97", "T2-C03", 127, [("A", "자기가 본 추와 천부터 놓는다", s("97", 133, 147, pn)), ("B", "소라와 나나가 떠나기 직전 무엇을 했는지 묻는다", s("97", 151, 167, pn)), ("C", "유우에게 남아서 하기로 한 일을 묻는다", s("97", 171, 193, pn))])
    transport = s("97", 5, 125, c03)
    tool = s("12c1", 116, 313, transport)
    photo = rb("I2-C01:trial", "I2-C01", [("A", s("12c1", 88, 100, tool)), ("B", s("12c1", 104, 114, tool))], "12c1", 86)
    return s("12c1", 6, 84, photo)


def _trial_middle(r, tasks, target):
    s, b, rb = r.seq, r.branch, r.required_branch
    def says(p, a, z):
        return [e for e in r.docs[p].paragraphs(a, z) if e["type"] == "say"]
    def define(ident, kind, prefix, line, **fields):
        tasks[ident] = {"id": ident, "chapter": "2", "sourceKind": "BASELINE", "kind": kind, "source": r.docs[prefix].ref(line), "intro": [], "lines": [], "wrong": [], "success": [], "bindings": [], "runtimeReady": True, "retry": {"sameTask": True, "preserveEvidence": True, "preservePublicFacts": True, "cancellationIsSuccess": False}, "return": {"graphNext": True}, **fields}
        return tasks[ident]
    def task(ident, after, **fields):
        return r.g.add("v4:input:" + ident, {"type": "task", "taskId": ident, "runtimeReady": tasks[ident]["runtimeReady"], "source": tasks[ident]["source"], "next": after, "success": after, **fields})

    define("T2-MM-01", "mindmine", "12c2", 181, prompt="마이크를 꺼도 녹음 재생을 음향 탁자에 넣을 수 있는 별도 연결", imageDescription="낮의 시험과 수사 상태를 구별하는 기기 연결 도식", regionDescription="녹음기에서 음향 탁자의 별도 입력으로 가는 선 끝", wrongVariants=[{"cause": "microphone-switch", "script": says("12c2", 194, 194)}, {"cause": "card-slot", "script": says("12c2", 206, 206)}, {"cause": "speaker-output", "script": says("12c2", 212, 212)}], success=says("12c2", 200, 200), bindings=[{"kind": "forensicImageRegions", "required": True, "description": "Bind the actual authored connection diagram and visible separate-input endpoint; no guessed picture coordinates."}], runtimeReady=False)
    define("T2-FA-01", "anagram", "164", 275, intro=says("164", 281, 281), answer="녹음재생", answerGlyphs=list("녹음재생"), distractorDescription="감/정/이/동", mechanic={"selectGlyphCount": 1, "arrivalJudgment": True, "poolSlots": 20, "specialCollectibleSeparate": True}, retryPolicy="wrongSlotOnly", success=says("164", 291, 291), editorialMechanicCorrection="Native REA e9550/e96c0: one selected glyph, arrival judgment, repeated required glyph respawn; same-glyph pair manuscript staging is not an executable rule.")
    questions = []
    for i, q, options, answer, good, wrongs in (
        (1, "목소리가 남은 동안 아직 필요한 질문", ["목소리가 들린 동안 유우의 몸이 실제로 무엇을 했는가", "노래를 좋아한 사람이 전부 세뇌되었는가", "목소리가 유우의 것이 아닌가"], "A", 321, [("B", 313), ("C", 317)]),
        (2, "그동안 유우가 무엇을 했는가 뒤의 다음 대조", ["소라가 공연을 좋아했으므로 유우의 설명 전부를 채택한다", "손의 고리 조각·개인 끈, 도구의 천·소매를 실제로 맞춘다", "리쿠의 절도가 나빴으므로 리쿠를 먼저 투표한다"], "B", 343, [("A", 335), ("C", 339)]),
    ):
        questions.append({"id": f"T2-RL-01:link:{i}", "q": q, "options": [{"id": k, "label": label} for k, label in zip("ABC", options)], "answer": answer, "retryPolicy": "currentLinkOnly", "success": says("164", good, good), "wrongVariants": [{"optionId": k, "script": says("164", line, line)} for k, line in wrongs]})
    define("T2-RL-01", "reasoning", "164", 295, questions=questions)
    lie = define("T2-LIE-01", "nonstop", "169", 6, lines=says("169", 12, 20), answerEvidenceId="v4:E2-06", requiresEvidence=["v4:E2-06", "v4:E2-10"], evidencePool="actually-acquired-v4-cards-only", judgment="refute-or-intentional-lie", wrong=says("169", 28, 30))
    final_line = lie["lines"][-1]
    lie["targets"] = [{"lineId": final_line["id"], "word": "내가 정리했다는 말부터", "verdict": "refute", "actor": "yuu"}, {"lineId": final_line["id"], "word": "거기 없었어", "verdict": "lie", "actor": "yuu"}]
    lie["transformation"] = {"sourceEvidenceId": "v4:E2-10", "normalLabel": "그동안 미오는 하루카와 호텔에 있었음", "lieLabel": "그동안 미오는 무대에서 직접 봄", "intentionalHold": True, "changesHistoricalFacts": False}
    def role_section(key, after):
        first, last = r.docs['190'].section(key)
        return s('190', first, last, after)
    role_common = role_section('T2-Q02', role_section('T2-Q03', target))
    role_echo = rb('T2-C01:role-aftereffect', 'T2-C01',
                  [(letter, role_section('T2-Q'+letter+'01', role_common)) for letter in 'ABC'],
                  '190', r.docs['190'].section('T2-Q01')[0])
    role_entry = s('190', r.docs['190'].section('T2-Q01')[0],
                   r.docs['190'].section('T2-QA01')[0]-1, role_echo)
    tail = s("12c2", 832, 836, role_entry)
    c01 = r.menu("12c2", "T2-C01", 794, [("A", "기록만 맡겠다는 요구를 거절한다", s("12c2", 798, 804, tail)), ("B", "늦게 판단했던 적을 인정하고 현재 질문을 계속한다", s("12c2", 808, 816, tail)), ("C", "평가에 관해 답하지 않고 구체적인 틀린 점을 요구한다", s("12c2", 820, 828, tail))])
    ko = b("KO01:trial", "fte:21:complete", [(True, s("12c2", 790, 792, c01))], c01)
    after_w = s("12c2", 684, 784, ko)
    w_common = s("179", 271, 293, after_w)
    w = rb("W2-C14:trial", "W2-C14", [("A", s("179", 219, 241, w_common)), ("B", s("179", 245, 255, w_common)), ("C", s("179", 259, 269, w_common))], "179", 213)
    performance_memory = s("12c2", 620, 680, w)
    reasoning = task("T2-RL-01", performance_memory)
    after_c02 = s("12c2", 450, 614, reasoning)
    c02 = r.menu("12c2", "T2-C02", 384, [("A", "리쿠가 카드를 가져갈 수 있었던 순서를 묻는다", s("12c2", 390, 406, after_c02)), ("B", "카드 없이도 말할 수 있는 소리를 묻는다", s("12c2", 410, 426, after_c02)), ("C", "유우에게 재생했다고 인정한 범위를 묻는다", s("12c2", 430, 448, after_c02))])
    after_lie = s("12c2", 224, 382, c02)
    normal = s("169", 36, 38, after_lie)
    lying = s("169", 44, 92, after_lie)
    r.g.nodes[lying].setdefault("set", {})["T2-LIE-B"] = True
    lie["outcomes"] = {"A": {"judgment": "refute", "transformed": False, "to": normal}, "B": {"judgment": "lie", "transformed": True, "to": lying, "sets": {"T2-LIE-B": True}}}
    lie_entry = task("T2-LIE-01", normal, outcomes=lie["outcomes"])
    pre_lie = s("12c2", 218, 220, lie_entry)
    anagram = task("T2-FA-01", pre_lie)
    mine = task("T2-MM-01", anagram)
    return s("12c2", 5, 179, mine)


def _result(r, target):
    s, b, rb = r.seq, r.branch, r.required_branch
    # A current common object is not a posthumous private gift. Its actual
    # repair/disposal decision and all three acknowledgements remain separate.
    end_of_tin = s("155", 253, 259, target)
    tin_echo = rb("R2-C01:acknowledgement", "R2-C01", [("A", s("155", 241, 241, end_of_tin)), ("B", s("155", 245, 245, end_of_tin)), ("C", s("155", 249, 249, end_of_tin))], "155", 239)
    tin_common = s("155", 233, 237, tin_echo)
    tin_choice = r.menu("155", "R2-C01", 141, [("A", "지금 린에게 직접 살펴 달라고 부탁한다", s("155", 145, 167, tin_common)), ("B", "아직 안 맞는 상태로 따로 두자고 한다", s("155", 171, 199, tin_common)), ("C", "이 통은 더 쓰지 않겠다고 한다", s("155", 203, 227, tin_common))])
    before_tin_choice = s("155", 133, 139, tin_choice)
    # Late 145 earns the canonical fte:25 flag only after its real return.
    remembered_tin = b("AI01:tin-current-question", "fte:25:complete", [(True, s("155", 109, 119, before_tin_choice))], s("155", 123, 129, before_tin_choice))
    tin_question = s("155", 75, 105, remembered_tin)
    tin_koto = b("AI01:tin-koto", "fte:25:complete", [(True, s("155", 63, 65, tin_question))], s("155", 69, 71, tin_question))
    tin_after_memory = s("155", 57, 59, tin_koto)
    tin_memory = b("AI01:tin-memory", "fte:25:complete", [(True, s("155", 19, 37, tin_after_memory))], s("155", 41, 51, tin_after_memory))
    tin = s("155", 7, 15, tin_memory)

    morning = s("125", 182, 190, tin)
    next_day = s("12d", 606, 650, morning)
    c04_result = rb("T2-C04:result", "T2-C04", [("A", s("141", 187, 197, next_day)), ("B", s("141", 201, 207, next_day)), ("C", s("141", 211, 219, next_day))], "141", 181)
    c03_result = rb("T2-C03:result", "T2-C03", [("A", s("97", 353, 359, c04_result)), ("B", s("97", 363, 373, c04_result)), ("C", s("97", 377, 387, c04_result))], "97", 347)
    kept_distinct = s("12d", 536, 600, c03_result)
    lie_result = b("T2-LIE-B:result", "T2-LIE-B", [(True, s("169", 102, 122, kept_distinct))], kept_distinct)
    recording_common = s("12d", 496, 532, lie_result)
    c02_result = rb("T2-C02:result", "T2-C02", [("A", s("12d", 456, 468, recording_common)), ("B", s("12d", 472, 480, recording_common)), ("C", s("12d", 484, 494, recording_common))], "12d", 450)
    recording = s("12d", 342, 448, c02_result)
    dinner = s("79", 7, 169, recording)
    return s("12d", 6, 338, dinner)


def _trial_last(r, tasks, target):
    import json
    import re
    from pathlib import Path
    s, rb = r.seq, r.required_branch
    r.used.update(("164", "182", "158"))
    def says(p, a, z):
        return [e for e in r.docs[p].paragraphs(a, z) if e["type"] == "say"]
    def define(ident, kind, p, line, **fields):
        tasks[ident] = {"id": ident, "chapter": "2", "sourceKind": "BASELINE", "kind": kind, "source": r.docs[p].ref(line), "intro": [], "lines": [], "wrong": [], "success": [], "bindings": [], "runtimeReady": True, "retry": {"sameTask": True, "preserveEvidence": True, "preservePublicFacts": True, "cancellationIsSuccess": False}, "return": {"graphNext": True}, **fields}
        return tasks[ident]
    def task(ident, after):
        return r.g.add("v4:input:" + ident, {"type": "task", "taskId": ident, "runtimeReady": tasks[ident]["runtimeReady"], "source": tasks[ident]["source"], "next": after, "success": after})

    rs = define("T2-RS-01", "showdown", "164", 6, lines=says("164", 12, 46), answerEvidenceId="v4:E2-08", requiresEvidence=["v4:E2-08"], evidencePool="actually-acquired-v4-cards-only", wrongVariants=[{"cause": "photograph-not-resolving-damage", "script": says("164", 52, 54)}, {"cause": "stolen-card", "script": says("164", 60, 66)}, {"cause": "two-carriers", "script": says("164", 72, 74)}], success=[e for e in r.docs["164"].paragraphs(80, 104) if e["type"] in ("say", "stage")])
    rs["targets"] = [{"lineId": rs["lines"][-1]["id"], "word": "천도 근거에서 빼야지", "actor": "riku", "verdict": "refute"}]
    pairs = []
    for no, first, them, us, response_at, wrong_end in ((1, 363, "sora", "nana", 367, 371), (2, 377, "koto", "sho", 381, 385), (3, 391, "riku", "haruka", 395, 399), (4, 405, "satsuki", "rei", 409, 413), (5, 419, "yuu", "mio", 423, 429), (6, 435, "ken", "akari", 439, 443)):
        raw = r.docs["164"].lines[first - 1]
        claim = raw.split("「", 1)[1].rsplit("」", 1)[0].replace("**", "")
        keyword = re.findall(r"\*\*(.+?)\*\*", raw)[-1]
        response_key = re.findall(r"\*\*(.+?)\*\*", r.docs["164"].lines[first + 1])[-1].rsplit("/", 1)[0].strip()
        response = says("164", response_at, response_at)[0]
        pairs.append({"id": f"T2-SD-01:round:{no}", "them": them, "themText": claim, "keyword": keyword, "us": us, "usText": response["text"], "responseKeyword": response_key, "wrong": says("164", first + 8, wrong_end), "source": r.docs["164"].ref(first)})
    define("T2-SD-01", "scrum", "164", 347, intro=says("164", 353, 359), pairs=pairs, teams={"us": ["mio", "rin", "nana", "haruka", "sho", "rei", "akari"], "them": ["yuu", "sora", "ken", "riku", "koto", "satsuki"]}, success=[e for e in r.docs["164"].paragraphs(449, 461) if e["type"] in ("say", "stage")], teamMeaning="Current explanation positions, not blanket trust, vote intention, or culprit status.")
    # This premise is heard in the live question; it is not a newly acquired
    # forensic measurement or a claim that successful rescue was possible.
    scope = tasks["T2-RS-A03"]
    scope.update(answerEvidenceId="v4:T2-RS-A03:unobserved-life-check", evidenceOptions=[{"id": "v4:T2-RS-A03:unobserved-life-check", "name": "움직이지 않은 몸과 생명 징후 확인의 구별", "text": "움직이지 않은 몸을 봤다는 말은 생명 징후를 확인했다는 관찰이 아니에요.", "source": r.docs["182"].ref(728)}], evidencePool=["v4:T2-RS-A03:unobserved-life-check"], scopeOnlyEvidence=True, requiresEvidence=[], scopePolicy={"lifetime": "current-input-only", "inventoryGrant": False, "persistAfterReturn": False, "source": "The current admitted observation and its unobserved scope; no rescue result is invented."})
    scope["bindings"] = [x for x in scope.get("bindings", []) if x["kind"] != "evidenceAcquisition"]
    scope["runtimeReady"] = not any(x.get("required") for x in scope["bindings"])
    waves = []
    for index, (a, z) in enumerate(((473, 475), (479, 485), (489, 491)), 1):
        events = says("164", a, z)
        waves.append({"id": f"T2-AA-01:wave:{index}", "pairs": [{"claim": events[i], "response": events[i + 1]} for i in range(0, len(events), 2)], "retryPolicy": "currentWaveLastClaim"})
    define("T2-AA-01", "armament", "164", 465, opponent="yuu", waves=waves, lines=[pair["claim"] for wave in waves for pair in wave["pairs"]], final=["받침대로", "아이를 때리고", "몸을 함에 넣어", "두 사람에게 옮기게 했다"], finalSubject="유우는", finalDistractors=["함 안의 추가", "먼저 아이를 때려", "내용을 알린 뒤", "같이 숨겼다"], wrongVariants=[{"cause": cause, "feedbackText": r.docs["164"].lines[line - 1].split("「", 1)[1].split("」", 1)[0], "source": r.docs["164"].ref(line), "script": []} for cause, line in (("wrong-tool", 497), ("carriers-knew", 498), ("wrong-order", 499))], success=[e for e in r.docs["164"].paragraphs(503, 509) if e["type"] in ("say", "stage")], failureIsPhysicalHarm=False, timingScope="Authored waves and phrase inputs; no complete music-note chart is present in this manuscript.")
    root = Path(__file__).resolve().parents[1]
    contract = json.loads((root / "art/v4_production/completion/comic_contracts.json").read_text(encoding="utf-8-sig"))
    ranges = [{"A": (33, 39), "B": (43, 49), "C": (53, 57)}, {"A": (69, 73), "C": (77, 83), "B": (87, 93)}, {"B": (105, 111), "C": (115, 121), "A": (125, 131)}, {"A": (143, 149), "B": (153, 159), "C": (163, 169)}, {"A": (181, 187), "C": (191, 197), "B": (201, 205)}, {"B": (217, 223), "C": (227, 231), "A": (235, 239)}]
    slots = []
    for record in (x for x in contract["slots"] if x["chapter"] == 2):
        options = []
        for option in record["options"]:
            expected = f"|{record['slot']}{option['key']}|{option['description']}|" + ("정답" if option["correct"] else "오답") + "|"
            if r.docs["158"].lines[option["source_line"] - 1] != expected:
                raise ValueError("Chapter-two climax candidate source changed: " + expected)
            image = f"art/reconstruction_v4/candidates/C2_S{record['slot']:02}_{option['key']}.webp"
            if not (root / image).is_file():
                raise ValueError("Missing actual chapter-two candidate: " + image)
            a, z = ranges[record["slot"] - 1][option["key"]]
            options.append({"id": option["key"], "label": option["description"], "image": image, "source": r.docs["158"].ref(option["source_line"]), "response": says("158", a, z)})
        slots.append({"id": f"T2-MG-01:slot:{record['slot']}", "options": options, "answer": record["correct_key"], "retryPolicy": "currentSlotOnly", "priorCorrectSlotsRemain": True})
    define("T2-MG-01", "climax", "158", 7, intro=says("158", 11, 19), slots=slots, success=[e for e in r.docs["158"].paragraphs(245, 273) if e["type"] in ("say", "stage")], sourceContractPolicy="Every current table caption/key and candidate file checked; runtime visual quality is a separate verification.")
    define("T2-VOTE-01", "vote", "12c3", 833, answer="yuu", candidates=["mio", "rei", "sora", "ken", "nana", "riku", "akari", "yuu", "koto", "satsuki", "taiga", "rin", "sho", "ai", "haruka", "kaede"], deadCandidatesSelectable=True, selectionRole="final-culprit-vote", finalVote=True, wrongPolicy="failure-and-retry-only; never show correct aftermath after another ballot", voteCounts={"yuu": 11, "mio": 2}, otherIndividualBallotsPublic=False)

    # The source's writer-only line835 records private ballots. The player
    # receives the actual aggregate reveal only after committing a correct vote.
    vote = task("T2-VOTE-01", s("12c3", 837, 861, target))
    climax = task("T2-MG-01", s("12c3", 831, 833, vote))
    armor = task("T2-AA-01", s("12c3", 699, 827, climax))
    final_talk = s("12c3", 415, 695, armor)
    old_promise_tail = s("113", 145, 357, final_talk)
    old_promise = rb("1-C08:second-trial", "1-C08", [("A", s("113", 83, 107, old_promise_tail)), ("B", s("113", 111, 123, old_promise_tail)), ("C", s("113", 127, 141, old_promise_tail))], "113", 81)
    c12_tail = s("113", 75, 79, old_promise)
    c12 = rb("2-C12:second-trial", "2-C12", [("A", s("113", 23, 37, c12_tail)), ("B", s("113", 41, 55, c12_tail)), ("C", s("113", 59, 71, c12_tail))], "113", 21)
    one_on_my_side = s("113", 5, 19, c12)
    c09 = rb("2-C09:second-trial", "2-C09", [("A", s("12c3", 375, 381, one_on_my_side)), ("B", s("12c3", 385, 397, one_on_my_side)), ("C", s("12c3", 401, 409, one_on_my_side))], "12c3", 373)
    after_rescue = s("12c3", 139, 371, c09)
    rescue = s("138", 5, 291, s("12c3", 133, 137, after_rescue))
    after_cook_memory = s("126", 61, 155, s("12c3", 89, 129, rescue))
    cook_memory = rb("2-C02:second-trial", "2-C02", [("A", s("126", 33, 43, after_cook_memory)), ("B", s("126", 47, 57, after_cook_memory))], "126", 29)
    could_have_stopped = s("126", 5, 27, cook_memory)
    after_scrum = s("141", 163, 177, s("12c3", 69, 85, could_have_stopped))
    scrum = task("T2-SD-01", after_scrum)
    c04 = r.menu("141", "T2-C04", 41, [("A", "호텔에 있던 사람이 먼저 나갔다 돌아왔다는 대안을 본다", s("141", 45, 77, scrum)), ("B", "닫힌 함을 받은 두 사람이 그 뒤에 살해했다는 대안을 본다", s("141", 81, 113, scrum)), ("C", "리쿠가 녹음 카드를 가져가는 동안 은폐했다는 대안을 본다", s("141", 117, 155, scrum))])
    alternatives = s("141", 5, 39, c04)
    showdown = task("T2-RS-01", s("12c3", 45, 65, alternatives))
    return s("12c3", 5, 41, showdown)


def compile_chapter_two(sources: dict[str, Any], freetime_graphs: dict[str, Any], tasks=None):
    from build_v4_story import Graph
    g = Graph("2")
    if tasks is not None:
        g.taskDefinitions = tasks["tasks"]
    r = Router(g, sources, freetime_graphs)
    for prefix, digest in REVIEWED_HASHES.items():
        if r.docs[prefix].hash != digest:
            raise ValueError(f"{r.docs[prefix].name}: chapter-two route source changed; re-read the altered manuscript before updating its reviewed ranges.")
    continuation = r.gate("trial", "Case-two trial/result need their exact explicit routes; do not fall through to a legacy case or mark chapter complete.", "12c1", 6)
    if "T2-NS-A01" in g.taskDefinitions:
        _bind_trial_cards(r, g.taskDefinitions)
        end = g.add("v4:2:end", {"type": "end", "chapterComplete": True, "nextChapter": "3"})
        ending = r.seq("12d", 668, 682, end)
        file_storage = r.required_branch("2-C06:final-storage", "2-C06", [("A", r.seq("12d", 660, 660, ending)), ("B", r.seq("12d", 664, 664, ending))], "12d", 656)
        result = _result(r, file_storage)
        trial_later = _trial_last(r, g.taskDefinitions, result)
        trial_middle = _trial_middle(r, g.taskDefinitions, trial_later)
        trial_entry = _trial_first_half(r, g.taskDefinitions, trial_middle)
        g.nodes[continuation] = {"id": continuation, "type": "stage", "direction": "수사에서 실제 확인한 자료를 지닌 채 두 번째 재판에 들어간다.", "next": trial_entry}
        r.pending.remove(continuation)
    investigation, catalogue = _investigation(r, continuation)
    day_eight = _day_eight(r, investigation)
    night_seven = _waiting_evening(r, day_eight)
    day_seven = _day_seven(r, night_seven)
    performance = _day_six_performance(r, day_seven)
    preparation = _day_six_preparation(r, performance)
    entry = _day_five(r, preparation)
    # The file is actually read before interactive investigation starts.
    for node in list(g.nodes.values()):
        if node.get("source", {}).get("file") == r.docs["12a7"].name and node["source"]["line"] == 324:
            ident = "v4:2:grant:E2-01:discovery"
            name, text = CARD_TEXT["E2-01"]
            g.add(ident, {"type": "evidence", "evidenceId": "v4:E2-01", "name": name, "text": text, "source": node["source"], "next": node["next"]})
            node["next"] = ident
    seats = ["mio", "rei", "sora", "ken", "nana", "riku", "akari", "yuu", "koto", "satsuki", "taiga", "rin", "sho", "ai", "haruka", "kaede"]
    for node in g.nodes.values():
        if node.get("source", {}).get("file") == r.docs["12d"].name and node["source"]["line"] == 82:
            node.setdefault("set", {}).update({"public:yuu:body-discovered": True, "public:yuu:executed": True})
        if node["type"] == "task":
            node.update(trialDead=["kaede", "taiga", "ai"], seats=seats, rosterSource=r.docs["12c1"].ref(3))
    return g.export(entry, evidenceCatalog=catalogue, routingStatus="explicit-reviewed-routes-through-case-two-end" if "T2-NS-A01" in g.taskDefinitions else "explicit-reviewed-living-discovery-investigation", contentScope="Four living days, discovery, all authored investigation scopes, explicit trial inputs with exclusive choices/lie/past callbacks, six-slot reconstruction, actual vote and aftermath through the current tin decision and private file storage. Unbound pictures and uncompiled meetings remain gates.", campaignReady=False, chapterComplete=False, pendingRouteIds=r.pending, reviewedSourcePrefixes=sorted(r.used), sourceAddressPolicy="Semantic paragraph IDs; edited source revisions must be re-reviewed before ranges can be regenerated.")
