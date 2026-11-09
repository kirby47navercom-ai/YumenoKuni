"""Explicit final-chapter source routes; this module publishes no output."""
from __future__ import annotations

REVIEWED_HASHES = {'117': '7afd4321b07c9ba6211591a7df2827ae08196359ade9066317df51d86bb204c1', '129': 'babb56c4b72f5855624effe91feb07572df32425d737487dce27d39ade704989', '16a2': '43a345cb1268d6c4b943a2212fdfa0f370742d03bd69e2b7d45e120c9bffe4f4', '16a3': '3c28296a86f8cb7448b1fe64aacffdc4e737dc48e98ad059d2e375a44dd7ef70', '16a4': '279511f574fac98ab5448013bcd5623a2306323fb7b57b22beb9954d3503e0d8', '16a5': 'ae62eec4a8a5625a8083820aeda114afa3d7fe9720102a2b14b2a4d38c818445', '16a': '6ef6519a9dddc75fab92991240093d0c717d380efdcc4b41006cdea66d4a64c6', '16b1': '1f9606f1aa1d0f464ba3dbfe82eb5a725afbf9dd7a908b9a4f4e6d4e7b19861a', '16b2': '7c21e8c05339d824aee447ea5decc953974f27a369e48f9bbb681d611ccedb4e', '171': '86c620cdc0169af5dfe53b06ad1c0122b6e5874b60ebe545fc4966f1c6c360db', '75': '349f368a9d84babde373299434bd30b0326d5bb5ae1e8c92725a0269bf078d45'}
REVIEWED_HASHES.update({'104': 'bad8b1ffd8b9ba363864a19579835fcc3abb1c349ee5144ba0e37cb32761093e', '168': '26b55854d20bc514ecad5d27bb5d0c24fa332c46f3e66e7ac3b075398967564c', '16c1': '87521599d137d422f0c95b501fa1bbca202a955b1aa6504f8bad98cb4feddfd6', '186': '96df7291d701240ba3fd19fb6b2302d939acba465daf2bf300d82f9dcccf6898'})
REVIEWED_HASHES.update({'107': '1aa3c22c875d8bb9ad1387b6e4c57e1729bf41b591f7ac9f9b07933e0275ab31', '118': 'cbe765a00a5de4858aca3b7b73aed8f4b5876052c6a4e5a2541f2c92324ea1f5', '169': '954fbe7b6d6f59c6f2dedd9c564654f08a20f15f378fdc284c27ec66d7428964', '16c2': 'e9ba0f804e337237a0fb883a7b294041e08d4c82c5f73ea6877b87ca9f9f5979', '96': 'b9ef9b9216745adf8f3176d1b8e68b33195a35844cfb3bf138e365375e764411'})
REVIEWED_HASHES.update({'162': 'bece2bb9c8f4ebcb0aec329f5e245fc5e7a938a5a8fe203eb76434bd3889eaad', '16c3': '1a4f9a1478d6753add49d87c33e54bcaa9f5252321d237683c8f4dcec910d329'})
REVIEWED_HASHES.update({'122': 'bccd438c8e474751eb05e71781bfc42c587497f5d571db17bf87458e872c42a6', '16d1': '6c3d46f4110d989324e63cbd85a7e29d9cdd9b4ed33bfb7d913f1dd234468d67', '16d2': '97c75fbc6ef240ded0e1c89b9e3ab2a04340d5890c9b2e42d321614e5e459acd', '73': 'eee96c63dbc23eebe2156661f72d4202f605f63c9d8d27a1f8588389a37ab756'})
REVIEWED_HASHES.update({'187': 'a330de709587dd08380bb44ab76964af749c47becf37d017149c6bba6227d7b0'})
REVIEWED_HASHES.update({'188': 'da96d7a4ee54c414bba976401edac64c164a61192de7ac1171c08794b3913e81'})
REVIEWED_HASHES.update({'194': '1e8186c67871ad20d087c7a2bd9589781c6dac12b85cd6969fdb52040917b287'})
REVIEWED_HASHES.update({'195': '4772234eb2146a05a60cefc48c8386c4ef8c0dd9c7dc9b36b3af98511bdaa169'})
SOURCE_PREFIXES = tuple(REVIEWED_HASHES)


def route_source_hashes(sources):
    docs = {s.prefix: s for s in sources.values()}
    return {docs[p].name: digest for p, digest in REVIEWED_HASHES.items()}


class Router:
    def __init__(self, graph, sources):
        self.g = graph
        self.d = {s.prefix: s for s in sources.values()}
        self.pending = []

    def events(self, p, a, z):
        # Source deliberately allows only the sixteen known actors. These
        # four exact manuscript roles are also spoken lines, never generic
        # square-bracket author/UI instructions or extra trial participants.
        roles = {"외부접수원": ("external_receptionist", "current-telephone"),
                 "현장확인자": ("site_checker", "current-external-role"),
                 "어린 하루카·복원 음성": ("restored_child_haruka_voice", "preserved-incomplete-recording"),
                 "상대·복원 음성": ("restored_other_voice", "preserved-incomplete-recording")}
        events = self.d[p].paragraphs(a, z)
        for i, event in enumerate(events):
            if event["type"] != "editorial":
                continue
            raw = event["direction"]
            if not raw.startswith("[") or "]" not in raw:
                continue
            label, text = raw[1:].split("]", 1)
            if label in roles:
                actor, scope = roles[label]
                events[i] = {"id": event["id"], "source": event["source"], "type": "say", "speaker": label, "actor": actor, "text": text.strip(), "mono": False, "delivery": label, "voiceScope": scope, "participantSeat": False}
        return events

    def seq(self, p, a, z, to):
        import re
        # Same source-addressed Graph.sequence contract, with only the four
        # reviewed role labels above restored before filtering editor notes.
        executable = []
        for event in self.events(p, a, z):
            if event["type"] in ("say", "stage"):
                executable.append(event)
            elif event["type"] == "editorial":
                marker = re.match(r"^>\s*\*\*필수 입력 (T\d+-[A-Z]+-A\d+):", event["direction"])
                if marker:
                    if marker[1] not in self.g.taskDefinitions:
                        raise ValueError("Missing explicit task definition " + marker[1])
                    executable.append({"id": "v4:input:" + marker[1], "type": "task", "taskId": marker[1], "source": event["source"], "runtimeReady": self.g.taskDefinitions[marker[1]]["runtimeReady"]})
        target = to
        for event in reversed(executable):
            node = {**event, "next": target}
            if event["type"] == "task":
                node["success"] = target
            target = self.g.add(event["id"], node)
        return target

    def gate(self, key, reason, p, line):
        ident = "v4:6:pending:" + key
        self.pending.append(ident)
        return self.g.add(ident, {"type": "gate", "reason": reason, "source": self.d[p].ref(line)})

    def branch(self, key, flag, rows, fallback):
        return self.g.add("v4:6:branch:" + key, {"type": "branch", "cases": [{"flag": flag, "equals": value, "to": to} for value, to in rows], "default": fallback})

    def recall(self, key, flag, rows, p, line):
        missing = self.gate(key + ":missing", "A compulsory earlier choice is missing; do not invent its answer or play every alternative.", p, line)
        return self.branch(key, flag, rows, missing)

    def menu(self, p, key, line, rows):
        return self.g.add("v4:6:menu:" + key, {"type": "menu", "q": self.d[p].lines[line - 1].split("—")[-1].lstrip("# "), "source": self.d[p].ref(line), "options": [{"id": value, "label": label, "to": to, "set": {key: value}} for value, label, to in rows]})

    def document(self, key, p, line, title, rows, to, **extra):
        return self.g.add("v4:6:document:" + key, {"type": "document", "title": title, "rows": rows, "private": False, "source": self.d[p].ref(line), "next": to, **extra})


def _living(r, to):
    s, b = r.seq, r.branch
    tested = s("16a5", 6, 355, to)
    after_help = s("75", 129, 153, s("16a4", 315, 345, tested))
    help_choice = r.menu("75", "6-C03", 83, [("A", "나나를 자신의 살의 이유로 쓰지 않겠다고 말한다", s("75", 87, 93, after_help)), ("B", "좋은 약속부터 하지는 않겠다고 답한다", s("75", 97, 105, after_help)), ("C", "자신을 믿지 못하면서 부탁하는 건지 묻는다", s("75", 109, 125, after_help))])
    help_talk = s("75", 7, 81, help_choice)
    consequences = s("16a4", 209, 311, help_talk)
    not_required = s("129", 7, 185, consequences)
    identity_common = s("16a4", 75, 205, not_required)
    identity = r.menu("16a4", "6-C02", 33, [("A", "지금 그 이름으로 부르지는 않겠다고 말한다", s("16a4", 41, 49, identity_common)), ("B", "현재 남은 기억이 무엇인지 먼저 묻는다", s("16a4", 53, 59, identity_common)), ("C", "그 이름과 지금까지의 처형을 함께 묻는다", s("16a4", 63, 69, identity_common))])
    introduction = s("16a4", 7, 29, identity)
    rules = s("16a3", 7, 239, introduction)
    after_rin = s("16a2", 317, 417, rules)
    rin = b("RIN01:unasked-rule", "fte:20:complete", [(True, s("16a2", 309, 309, after_rin))], s("16a2", 313, 313, after_rin))
    first_rules_after = s("16a2", 39, 305, rin)
    conditions = r.document("final-procedure", "16a2", 33, "마지막 절차의 조건", [line.removeprefix("- ") for line in r.d["16a2"].lines[32:37]], first_rules_after)
    first_rules = s("16a2", 7, 31, conditions)
    practice = s("117", 7, 247, s("16a", 573, 619, first_rules))
    remaining = s("16a", 267, 567, practice)
    # A already inspected the actual telephone. B/C receive that fact now,
    # without inheriting A's private exchange or replaying A's conversation.
    shared_phone = s("16a", 253, 261, remaining)
    phone = b("6-C01:phone-common", "6-C01", [("A", remaining)], shared_phone)
    first = r.menu("16a", "6-C01", 209, [("A", "쇼와 함께 외부 연결 경로를 먼저 확인한다", s("16a", 217, 223, phone)), ("B", "린과 함께 단말의 기록 위치를 먼저 확인한다", s("16a", 227, 235, phone)), ("C", "나나에게 이 방에서 기억하는 자기 행위를 먼저 말해 달라고 한다", s("16a", 239, 247, phone))])
    # The first personal accusation needs the unredacted identity evidence,
    # not a later scene retroactively claiming it was already read.
    identity_before = r.d['16a'].at('## 6-06 돌아보지 않는 사람')
    arrival_after = s('16a', identity_before, 205, first)
    arrival = s('16a', 47, identity_before-1, _memory_disclosure(r, arrival_after))
    stairs = s("171", 8, 292, arrival)
    return s("16a", 7, 41, stairs)


def _memory_disclosure(r, to):
    source = r.d['194']
    # A stage direction is skipped by the native dialogue runner. Documents
    # consumed by the next accusation must be actual readable nodes.
    documents = [
        ('prior-relationship-handover', '옛 행사 준비물 인계표',
         '> 옛 행사 준비물 인계표 — 재단 보관 사본', '> 현재 공원에서의 작업 기록과는 날짜가 다름'),
        ('prior-gift-name-match', '옛 성명면·인형 인계 대조',
         '> 미오의 옛 성명면·인형 인계 대조 — 원본 열람용 사본', '> 인형을 건넨 일과 리본을 건네지 못한 일은 서로 다른 때의 기록'),
        ('prior-anonymous-targets-match', '옛 접수·개입·맹세 서명 대조',
         '> 옛 접수·개입 진술·맹세 서명 대조 — 성명 가림 없는 열람용 사본', '> 접수·개입·계약을 대조한 기록이며 사고의 모든 행위를 촬영한 자료는 아님'),
        ('relationship-memory-intake', '이번 입소 처리 이력',
         '> 이번 입소 처리 이력 — 개장 전 처리 완료', '> 한계: 이미 삭제된 기억의 재생성 기능 없음'),
    ]
    cursor = len(source.lines)
    for key, title, first, final in reversed(documents):
        start, last = source.at(first), source.at(final)
        after = r.seq('194', last+1, cursor, to)
        rows = [line[2:] for line in source.lines[start-1:last] if line.startswith('> ')]
        to = r.document(key, '194', start, title, rows, after)
        cursor = start-1
    return r.seq('194', 1, cursor, to)


CARDS = {
    "E6-01": ("옛 사망·수습과 난간 자료", "실제 하루카는 추락 외상으로 사망했어요. 최초 추락 원인은 사망 항목만으로 특정하지 않아요. 현재 난간은 교체됐고 옛 손 접촉·손상 흔적은 잡으려던 움직임과 맞지만 밀친 이름을 알려 주지 않아요."),
    "E6-02": ("나나의 실제 위치와 목격 범위", "옆 관리 출입의 열린 틈, 옛 도면·사진과 시야를 대조했어요. 나나는 대화 때 얼굴을 알아보고 몸이 돌아선 뒤 등으로 나간 두 손과 후속 잡기를 봤다고 해요. 처음 팔 접촉·그 뒤 모든 동선·정확한 분은 못 봤어요."),
    "E6-03": ("입구 동행·중앙 경보·전실 접수", "입구 자료는 두 사람 얼굴과 진행 방향을 보여 주고 홀 안의 밀침을 찍지 않았어요. 지역 시계와 중앙 시계를 경보 전후 사건으로 대응했어요. 먼저14명(나나+13명), 코토20:50의 전실 접수이며 모든 사람의 더 이른 위치를 뜻하지 않아요."),
    "E6-04": ("미오의 옛 노트 세 줄", "코토가 아버지와 점검 일정으로 언성을 높였음/하루카가 서류를 들고 코토에게 간다고 말함/둘이 통로 쪽으로 감. 밀침·정확한 시각·이후 전체가 적힌 기록은 아니에요."),
    "E6-05": ("유보·수정·정상 표시·다음 인수", "입력 제한 점검 미완료·인계 유보 뒤 동일 항목을 완료로 수정하고 최종본에 정상으로 표시했어요. 다음 인수에는 동일 안전 항목이 미해결 유보였어요. 코토 아버지의 수정과 아카리 아버지의 승인은 다른 행위예요."),
    "E6-06": ("서로 다른 옛 맹세와 남은 경고", "레이는 점검 허위·은폐의 코토와 아버지 관여를 의도적으로 전달하지 않는 조건, 코토는 레이의 위험 경고 보류를 레이의 공개 전에 먼저 전하지 않는 조건이에요. 오른팔/손목 대가와 종료시각 없음·재합의 해제예요. 미래 모든 살인·생성의 명령은 없어요."),
    "E6-07": ("0일차 요청과 실제 도착", "현재 소환 요청16/실제 도착15와 나중 생성으로16이 된 기록이에요. 코토가 불일치 확인에 관여했어요. 5년 전 구조15·첫전실14·13명 망각과 날짜·대상이 달라요. 코토도 생성 친숙함의 예외는 아니에요."),
    "E6-08": ("복원 단편의 두 순간", "팔을 잡은 감각과 상대의 손 놓으라는 말·해제 뒤 몸 방향이 바뀌고 등에 힘이 들어오는 감각은 별도예요. 피해자 단편은 자기 등 뒤 두 손을 눈으로 본 완전 영상이 아니며 나나의 옆 시야와 결합해요."),
    "E6-09": ("코토의 당시 네 줄과 요약 누락", "당시 서명·접수 진술에는 동행/하루카의 팔잡기/뿌리침/추락 목격이 있어요. 등뒤 밀침 자백은 없어요. 접수됐지만 혼자 추락한 것으로 정리된 요약에는 동행·접촉이 빠져요. 접수만으로 모든 담당자의 전문 열람·의도까지 확정하지 않아요."),
    "E6-10": ("옛 노출 상태와 현재 제한·완충", "옛 미해결 안전 항목과 노출·입력 운영, 추락 뒤 시설 피해를 나누어요. 현재 한정100% 사용에는 제한·완충과 차폐가 유지됐어요. 같은 힘 이름만으로 두 상태·모든 피해 원인을 같게 만들지 않아요."),
    "E6-11": ("열린 대피 경로 뒤의 개입", "시제품 입력 뒤 비상 보호 경로가 열리고 나나+13명이 먼저 접수됐어요. 나나는 자신과 늦게 온 코토를 제외한13명에게 개입했으며 코토의 뒤 협박 이전에도 자기가 알고 침묵했어요. 이미 삭제한 내용은 현재 맹세 효과가 끝나도 돌아오지 않아요."),
    "E6-12": ("졸업·중앙 통제와 의식 지원", "과거 행위자 지목만으로 통제는 끝나지 않아요. 마지막 진상 심리에서 쟁점을 확인하고 현재 게임·중앙 출입 연동의 종료를 확정해요. 이번 입소의 관계 차폐도 종료하지만 삭제 기억 복원·외부 응답·물리문 수리·모든 개인 능력 소멸·인형 의식 지원 자동 종료를 뜻하지 않아요. 지원을 끝내면 같은 의식이 다시 깨어난다고 약속할 수 없어요."),
    "E6-13": ("전달원·시제품·휴면과 현재 의식", "실제 하루카에게 간 시제품 번호·불완전 의식 입력·휴면·현재 래피와 복원 단편을 대조했어요. 미오 키링과 선물 인형, 생성 하루카와 래피는 별도예요. 현재 운영·자료 통제·처형은 그 의식이 고른 현재 행동으로 남아요."),
    "E6-14": ("오늘 기록100%의 실제 경계", "현재 보호 페이지에 새 손글씨와 사용 의사로 특정 지속 효과를 끝냈어요. 그림자 기본효과 중단과 새효과 재사용을 확인한 뒤 나나의 동의·현재 호흡 문장으로 옛 맹세를 끝냈어요. 사실 인증·이미 끝난 망각 복원·물리원인 치료·영구전능이 아니에요."),
    "E6-16": ("원문 보존과 아직 미합의인 공개", "원문과 각자의 필기를 구별해 보존해요. 함께 읽은 것이 다섯 전원 원문 공개 허락은 아니며 공개할 상대·범위를 아직 합의하지 않았어요. 자료가 남는 일과 외부에서 믿고 판단할 일도 달라요."),
}


def _investigation(r, to):
    s = r.seq
    catalogue = {}
    def grant(code, p, line, after):
        name, text = CARDS[code]
        ident = "v4:" + code
        catalogue[ident] = {"id": ident, "name": name, "text": text, "source": r.d[p].ref(line), "grantPolicy": "actual-completed-scope-only"}
        return r.g.add(f"v4:6:grant:{code}:{p}:{line}", {"type": "evidence", "evidenceId": ident, "name": name, "text": text, "source": r.d[p].ref(line), "next": after})
    def hub(key, p, a, z, after, cards=(), space="operating_archive", custom=None):
        ident = "v4:6:investigate:" + key
        returned = r.g.add(ident + ":return", {"type": "return"})
        finish = returned
        for code in reversed(cards):
            finish = grant(code, p, z, finish)
        entry = custom(finish) if custom else s(p, a, z, finish)
        spot = ident + ":spot"
        flag = spot + ":complete"
        r.g.add(ident, {"type": "investigate", "title": r.d[p].lines[a - 1].lstrip("# "), "source": r.d[p].ref(a), "spots": [{"id": spot, "label": r.d[p].lines[a - 1].lstrip("# "), "space_id": space, "target_id": "", "geometryReady": False, "needsSpaceBinding": not bool(space), "interactionPolicy": "Actual source document/interview; core-hall geometry or actor placement remains unbound.", "entry": entry, "returnTo": ident, "completionFlag": flag, "onReturnSet": {flag: True}, "required": True}], "requiredSpotIds": [spot], "requiredCards": ["v4:" + c for c in cards], "next": after})
        return ident
    def with_document(key, p, a, document_at, rows, tail_at, z, after):
        doc = r.document(key, p, document_at, r.d[p].ref(a)["heading"], rows, s(p, tail_at, z, after))
        return s(p, a, document_at - 1, doc)

    finish = hub("I6-37-40", "16b2", 383, 423, to, ("E6-16",))
    confirmation = r.recall("I6-C01:remaining", "I6-C01", [("A", s("16b2", 357, 361, finish)), ("B", s("16b2", 365, 369, finish)), ("C", s("16b2", 373, 379, finish))], "16b2", 351)
    current_choice = r.menu("16b2", "I6-C01", 193, [("A", "접촉이 풀린 뒤의 밀침과 동행 자료를 먼저 맞춘다", s("16b2", 201, 249, confirmation)), ("B", "점검 수정·사고 요약에서 빠진 사실을 먼저 맞춘다", s("16b2", 253, 297, confirmation)), ("C", "현재 안내자의 운영·종료 조건을 먼저 맞춘다", s("16b2", 301, 347, confirmation))])
    end_scope = hub("I6-33-36", "16b2", 157, 197, current_choice, ("E6-12",), custom=lambda after: s("16b2", 157, 189, after))
    # The final card becomes owned only after its complete current scope.
    # The menu lies outside that call so its next cannot swallow the return.
    contracts = hub("I6-30-32", "16b2", 123, 155, end_scope, ("E6-10", "E6-11", "E6-06"))
    report = hub("I6-27-29", "16b2", 77, 121, contracts, ("E6-09",), custom=lambda after: with_document("koto-four-lines", "16b2", 77, 83, [r.d["16b2"].lines[i - 1].removeprefix("> ") for i in (83, 85, 87, 89)], 91, 121, after))
    fragment = hub("I6-21-26", "16b2", 5, 75, report, ("E6-08", "E6-13", "E6-14"))
    old_creation = hub("I6-18-20", "16b1", 432, 462, fragment, ("E6-07",))
    vows = hub("I6-16-17", "16b1", 412, 430, old_creation, ("E6-06",), custom=lambda after: with_document("rei-old-vow", "16b1", 412, 416, [r.d["16b1"].lines[i - 1].removeprefix("- ") for i in (416, 417, 418)], 420, 430, after))
    modifications = hub("I6-14-15", "16b1", 359, 410, vows, ("E6-05",), custom=lambda after: with_document("four-safety-rows", "16b1", 359, 369, [r.d["16b1"].lines[i - 1].strip("|").replace("|", " : ") for i in (369, 370, 371, 372)], 374, 410, after))
    notebook = hub("I6-13", "16b1", 339, 357, modifications, ("E6-04",), custom=lambda after: with_document("old-note-three-lines", "16b1", 339, 347, [r.d["16b1"].lines[i - 1].removeprefix("> ") for i in (347, 349, 351)], 353, 357, after))
    clocks = hub("I6-09-12", "16b1", 199, 337, notebook, ("E6-03",))
    sight = hub("I6-05-08", "16b1", 47, 197, clocks, ("E6-02",), space="")
    railing = hub("I6-03-04", "16b1", 25, 45, sight, ("E6-01",), space="")
    death = hub("I6-01-02", "16b1", 5, 23, railing, custom=lambda after: with_document("old-death-record", "16b1", 5, 9, [r.d["16b1"].lines[i - 1].removeprefix("- ") for i in (9, 10, 11)], 13, 23, after))
    return death, catalogue


class Trial:
    def __init__(self, r, tasks):
        self.r, self.tasks = r, tasks

    def says(self, p, a, z):
        return [e for e in self.r.events(p, a, z) if e["type"] == "say"]

    def events(self, p, a, z):
        return [e for e in self.r.events(p, a, z) if e["type"] in ("say", "stage")]

    def define(self, ident, kind, p, line, **fields):
        self.tasks[ident] = {"id": ident, "chapter": "6", "sourceKind": "BASELINE", "kind": kind, "source": self.r.d[p].ref(line), "intro": [], "lines": [], "wrong": [], "success": [], "bindings": [], "runtimeReady": True, "retry": {"sameTask": True, "preserveEvidence": True, "preservePublicFacts": True, "cancellationIsSuccess": False}, "return": {"graphNext": True}, **fields}
        return self.tasks[ident]

    def input(self, ident, to, **extra):
        task = self.tasks[ident]
        return self.r.g.add("v4:input:" + ident, {"type": "task", "taskId": ident, "runtimeReady": task["runtimeReady"], "source": task["source"], "next": to, "success": to, **extra})


def _bind_tasks(r, tasks):
    mapping = {"T6-NS-A01": ("E6-14", []), "T6-NS-A03": ("E6-05", []), "T6-NS-A04": ("E6-06", []), "T6-NS-A05": ("E6-09", []), "T6-NS-A06": ("E6-04", []), "T6-NS-A07": ("E6-03", []), "T6-NS-A08": ("E6-11", []), "T6-NS-A09": ("E6-07", []), "T6-NS-A10": ("E6-07", []), "T6-PN-A02": ("E6-05", []), "T6-PN-A03": ("E6-10", []), "T6-RS-A02": ("E6-08", ["E6-02", "E6-09"]), "T6-RS-A03": ("E6-13", []), "T6-EVIDENCE-A01": ("E6-04", [])}
    for ident, (answer, other) in mapping.items():
        if ident not in tasks:
            continue
        task = tasks[ident]
        if task["source"]["fileSha256"] != r.d["186"].hash:
            raise ValueError(ident + ": compiled task source differs from the reviewed manuscript")
        task.update(answerEvidenceId="v4:" + answer, requiresEvidence=["v4:" + x for x in (answer, *other)], evidencePool="actually-acquired-v4-cards-only")
        task["bindings"] = [x for x in task.get("bindings", []) if x["kind"] != "evidenceAcquisition"]
        if ident == "T6-PN-A02":
            # Line529 explicitly names three lanes. Nana's closing observation
            # is shared context after that three-voice loop, not a fourth lane.
            shared = [e for e in task["lines"] if e["actor"] == "nana"]
            task["lines"] = [e for e in task["lines"] if e["actor"] != "nana"]
            task["success"] = shared + task.get("success", [])
            task["lanes"] = [{"id": where, "actor": actor, "lines": [e["id"] for e in task["lines"] if e["actor"] == actor]} for where, actor in (("왼쪽", "satsuki"), ("가운데", "rin"), ("오른쪽", "lappy"))]
            task["bindings"] = [x for x in task["bindings"] if x["kind"] != "panicLanes"]
        task["runtimeReady"] = not any(x.get("required") for x in task["bindings"])
    if "T6-PERSON-A02" in tasks:
        task = tasks["T6-PERSON-A02"]
        task["candidateOverrides"] = {"haruka": {"caption": "옛 행사일 · 실제 아사노 하루카", "identityScope": "actual-past-victim-not-current-created-body", "source": r.d["186"].ref(389)}}
        task["bindings"] = [b for b in task.get("bindings", []) if b["kind"] != "historicalVictimPortrait"] + [{"kind": "historicalVictimPortrait", "required": True, "source": r.d["186"].ref(389), "description": "Bind the actual inspected old event-day picture and its authored date. Current created Haruka memorial/portrait is not this event picture."}]
        task["runtimeReady"] = False


def _trial_opening(t, to):
    r, says = t.r, t.says
    s = r.seq
    debate = t.define("T6-NS-01", "nonstop", "168", 5, lines=says("168", 11, 25), wrongVariants=[{"cause": "erase-adult-names", "script": says("168", 31, 33)}, {"cause": "ignore-old-case", "script": says("168", 37, 39)}], success=t.events("168", 45, 55), answerEvidenceId="v4:E6-05", requiresEvidence=["v4:E6-05", "v4:E6-02"], evidencePool="actually-acquired-v4-cards-only", judgment="refute")
    weak = next(e for e in debate["lines"] if e["source"]["line"] == 23)
    debate["targets"] = [{"lineId": weak["id"], "word": "밀친 사람으로도 골라야", "verdict": "refute", "actor": "satsuki"}]
    debate["vpoint"] = {"optional": True, "character": "밀"}
    end_count = s("104", 157, 233, s("16c1", 359, 363, to))
    count = r.menu("104", "T6-C03", 103, [("A", "초청 명단과 실제 접수를 나눈다", s("104", 109, 121, end_count)), ("B", "나나의 열세 사람 진술을 첫 접수 안에서 맞춘다", s("104", 125, 137, end_count)), ("C", "입구 영상과 중앙 접수의 시각을 직접 빼지 않는다", s("104", 141, 151, end_count))])
    count_intro = s("104", 7, 101, count)
    documents = s("16c1", 37, 353, count_intro)
    main_input = t.input("T6-NS-01", documents)
    return s("16c1", 7, 29, main_input)


def _trial_middle(t, to):
    import re
    r, says = t.r, t.says
    s = r.seq
    pairs = []
    for no, claim_at, response_at, them, us, keyword, good_end, bad_start, bad_end in (
        (1, 41, 45, "sho", "mio", "접촉이 풀린 뒤의 몸 방향", 49, 53, 55),
        (2, 61, 65, "satsuki", "nana", "못 본 앞과 직접 본 뒤", 69, 73, 75),
        (3, 81, 85, "sho", "rin", "잡으려는 손보다 앞선 힘", 89, 93, 95),
        (4, 117, 121, "satsuki", "nana", "같은 장면을 보지 않은 두 경험", 125, 129, 131),
        (5, 137, 141, "sho", "mio", "손상 하나가 아닌 앞뒤 관찰의 연결", 145, 149, 151),
        (6, 157, 161, "satsuki", "rin", "생략된 구간에 남은 다른 관찰", 165, 169, 171),
    ):
        claim = says("16c2", claim_at, claim_at)[0]
        response = says("16c2", response_at, response_at)[0]
        raw = r.d["16c2"].lines[claim_at - 1]
        pairs.append({"id": f"T6-SD-01:round:{no}", "them": them, "themText": claim["text"].replace("**", ""), "keyword": re.search(r"\*\*(.+?)\*\*", raw)[1], "us": us, "usText": response["text"], "responseKeyword": keyword, "success": t.events("16c2", response_at + 2, good_end), "wrong": says("16c2", bad_start, bad_end), "source": r.d["16c2"].ref(claim_at)})
        if no == 3:
            pairs[-1]["afterSuccess"] = t.events("16c2", 101, 107)
    t.define("T6-SD-01", "scrum", "16c2", 5, intro=t.events("16c2", 9, 31), pairs=pairs, teams={"us": ["mio", "nana", "rin"], "them": ["sho", "satsuki"]}, teamMeaning="Current explanations only; Rappy gives his own fragment testimony outside both human teams. No dead speaker is added.", phaseGroups=[[1, 2, 3], [4, 5, 6]], interludePolicy="Play pair3 afterSuccess once before pair4. Each pair success contains its actual follow-up, never all wrong responses.")
    t.define("T6-MM-01", "mindmine", "168", 57, prompt="함께 들어온 두 얼굴·복장과 진행 방향을 확인할 부분", imageDescription="수사에서 확인한 옛 주 통로 입구 장면", regionDescription="입구의 두 얼굴과 같은 쪽으로 향한 몸", wrongVariants=[{"cause": "unfilmed-hall", "script": says("168", 72, 72)}, {"cause": "clock-only", "script": says("168", 76, 76)}, {"cause": "overlaid-signature", "script": says("168", 80, 80)}], success=says("168", 86, 86), runtimeReady=False, bindings=[{"kind": "forensicImageRegions", "required": True, "description": "Actual inspected old entrance picture, two faces/clothing/direction regions; no invented unseen push or option-index geometry."}])
    panic = t.define("T6-PD-01", "panic", "168", 90, lines=says("168", 96, 102), wrongVariants=[{"cause": "erase-physical-push", "script": says("168", 108, 110)}, {"cause": "today-certifies-past", "script": says("168", 114, 116)}], success=t.events("168", 122, 130), answerEvidenceId="v4:E6-10", requiresEvidence=["v4:E6-10", "v4:E6-05"], evidencePool="actually-acquired-v4-cards-only", judgment="refute")
    panic["targets"] = [{"lineId": panic["lines"][-1]["id"], "word": "전부 혼자", "actor": "lappy", "verdict": "refute"}]
    panic["lanes"] = [{"id": where, "actor": actor, "lines": [x["id"] for x in panic["lines"] if x["actor"] == actor]} for where, actor in (("왼쪽", "lappy"), ("가운데", "satsuki"), ("오른쪽", "rin"))]
    showdown = t.define("T6-RS-01", "showdown", "168", 134, lines=says("168", 140, 154), wrongVariants=[{"cause": "wrong-document-signature", "script": says("168", 160, 162)}, {"cause": "culprit-before-reading", "script": says("168", 168, 170)}], success=t.events("168", 176, 190), answerEvidenceId="v4:E6-09", requiresEvidence=["v4:E6-09"], evidencePool="actually-acquired-v4-cards-only", judgment="refute")
    showdown["targets"] = [{"lineId": showdown["lines"][-1]["id"], "word": "따로 남길 필요 없어요", "actor": "lappy", "verdict": "refute"}]
    questions = []
    for index, question, options, answer, right, wrong in ((1, "문구가 직접 요구한 것", ["모든 현재 살해를 코토가 지정했다", "특정 과거를 숨기는 제약이 있으며 그밖에서 고른 침묵은 별도로 남는다", "같은 선을 받았으니 똑같은 내용을 숨겼다"], "B", 218, [("A", 210), ("C", 214)]), (2, "현재 호흡 제약을 끝낸 뒤 남는 것", ["옛날 지운 다른13명의 기억도 전부 돌아왔다", "나나 자신의 과거 기억이 처음 복구됐다", "현재 제약은 끝났고 과거 망각과 그뒤5년은 남는다"], "C", 238, [("A", 230), ("B", 234)])):
        questions.append({"id": f"T6-RL-01:link:{index}", "q": question, "options": [{"id": k, "label": label} for k, label in zip("ABC", options)], "answer": answer, "retryPolicy": "currentLinkOnly", "success": says("168", right, right), "wrongVariants": [{"optionId": key, "script": says("168", line, line)} for key, line in wrong]})
    t.define("T6-RL-01", "reasoning", "168", 194, questions=questions)
    t.define("T6-FA-01", "anagram", "168", 242, intro=says("168", 246, 246), answer="지속효과", answerGlyphs=list("지속효과"), distractorDescription="과/거/복/원", mechanic={"selectGlyphCount": 1, "arrivalJudgment": True, "poolSlots": 20, "specialCollectibleSeparate": True}, retryPolicy="wrongSlotOnly", success=says("168", 256, 256), editorialMechanicCorrection="REA single selected glyph/arrival judgment; repeated glyphs respawn, no same-glyph pairing rule.")
    lie = t.define("T6-LIE-01", "nonstop", "169", 330, lines=says("169", 334, 340), wrong=says("169", 346, 348), answerEvidenceId="v4:E6-16", requiresEvidence=["v4:E6-16"], evidencePool="actually-acquired-v4-cards-only", judgment="refute-or-intentional-lie")
    lie["targets"] = [{"lineId": lie["lines"][-1]["id"], "word": "아무것도 남지 않겠네요", "actor": "lappy", "verdict": "refute"}, {"lineId": lie["lines"][-1]["id"], "word": "약속도 없는데", "actor": "lappy", "verdict": "lie"}]
    lie["transformation"] = {"sourceEvidenceId": "v4:E6-16", "normalLabel": "원문 보존·공개 범위는 아직 미합의", "lieLabel": "다섯 전원 원문 공개 합의", "intentionalHold": True, "changesHistoricalFacts": False}
    waves = []
    for index, (a, z) in enumerate(((266, 272), (276, 282), (286, 292)), 1):
        events = says("168", a, z)
        waves.append({"id": f"T6-AA-01:wave:{index}", "pairs": [{"claim": events[i], "response": events[i + 1]} for i in range(0, len(events), 2)], "retryPolicy": "currentWaveLastClaim"})
    t.define("T6-AA-01", "armament", "168", 260, opponent="lappy", waves=waves, lines=[x["claim"] for w in waves for x in w["pairs"]], final=["네가 남을 조건과", "다섯 사람의 생존을", "같은 문제로", "묶지 않을 거야"], finalDistractors=["네가 사라지면", "모든 과거가", "완전히 복구되니", "지금 혼자 정할게"], wrongVariants=[{"cause": cause, "feedbackText": r.d["168"].lines[line - 1].split("「", 1)[1].split("」", 1)[0], "source": r.d["168"].ref(line), "script": []} for cause, line in (("false-restoration", 300), ("unilateral-future", 301), ("wrong-order", 302))], success=t.events("168", 306, 310), failureIsPhysicalHarm=False, timingScope="Authored waves and four phrase inputs; full audio-note chart not provided.")

    armor = t.input("T6-AA-01", s("16c2", 971, 1121, to))
    after_lie = s("16c2", 955, 965, armor)
    normal = s("169", 354, 356, after_lie)
    lying = s("169", 362, 390, after_lie)
    r.g.nodes[lying].setdefault("set", {})["T6-LIE-B"] = True
    lie["outcomes"] = {"A": {"judgment": "refute", "transformed": False, "to": normal}, "B": {"judgment": "lie", "transformed": True, "to": lying, "sets": {"T6-LIE-B": True}}}
    lie_input = t.input("T6-LIE-01", normal, outcomes=lie["outcomes"])
    shared_names = s("118", 7, 225, s("16c2", 943, 951, lie_input))
    after_letters = s("16c2", 866, 937, shared_names)
    letters = t.input("T6-FA-01", after_letters)
    contracts = s("16c2", 783, 863, letters)
    reasoning = t.input("T6-RL-01", contracts)
    after_report = s("16c2", 523, 777, reasoning)
    report_tail = s("107", 219, 369, after_report)
    report_input = t.input("T6-RS-01", report_tail)
    report = s("107", 7, 215, report_input)
    after_panic = s("16c2", 429, 519, report)
    panic_input = t.input("T6-PD-01", after_panic)
    after_question = s("96", 333, 369, s("16c2", 417, 421, panic_input))
    question = r.menu("96", "T6-C02", 161, [("A", "나나에게 밀침 전후 시야가 끊긴 곳을 다시 묻는다", s("96", 169, 213, after_question)), ("B", "래피에게 자기 단편과 나중 자료의 구별을 다시 묻는다", s("96", 217, 269, after_question)), ("C", "사츠키에게 다른 설명이 맞아야 할 순서를 세워 달라고 한다", s("96", 273, 327, after_question))])
    interests = s("96", 7, 157, question)
    after_entrance = s("16c2", 201, 411, interests)
    mine = t.input("T6-MM-01", after_entrance)
    after_scrum = s("16c2", 177, 197, mine)
    return t.input("T6-SD-01", after_scrum)


def _trial_final(t, to):
    import json
    from pathlib import Path
    r, s = t.r, t.r.seq
    root = Path(__file__).resolve().parents[1]
    contract = json.loads((root / "art/v4_production/completion/comic_contracts.json").read_text(encoding="utf-8-sig"))
    ranges = [{"A": (33, 43), "B": (47, 57), "C": (61, 69)}, {"B": (81, 91), "C": (95, 105), "A": (109, 117)}, {"A": (129, 137), "C": (141, 151), "B": (155, 167)}, {"A": (179, 187), "B": (191, 201), "C": (205, 215)}, {"B": (227, 235), "C": (239, 249), "A": (253, 263)}, {"A": (275, 283), "C": (287, 297), "B": (301, 309)}, {"A": (321, 331), "B": (335, 345), "C": (349, 361)}, {"B": (373, 381), "C": (385, 397), "A": (401, 435)}]
    slots = []
    for record in (x for x in contract["slots"] if x["chapter"] == 6):
        options = []
        for option in record["options"]:
            expected = f"|{record['slot']}{option['key']}|{option['description']}|" + ("정답" if option["correct"] else "오답") + "|"
            if r.d["162"].lines[option["source_line"] - 1] != expected:
                raise ValueError("Final reconstruction candidate source changed: " + expected)
            image = f"art/reconstruction_v4/candidates/C6_S{record['slot']:02}_{option['key']}.webp"
            if not (root / image).is_file():
                raise ValueError("Missing actual reconstruction candidate: " + image)
            a, z = ranges[record["slot"] - 1][option["key"]]
            options.append({"id": option["key"], "label": option["description"], "image": image, "source": r.d["162"].ref(option["source_line"]), "response": t.events("162", a, z)})
        slots.append({"id": f"T6-MG-01:slot:{record['slot']}", "options": options, "answer": record["correct_key"], "retryPolicy": "currentSlotOnly", "priorCorrectSlotsRemain": True})
    t.define("T6-MG-01", "climax", "162", 7, intro=t.events("162", 9, 21), slots=slots, success=t.events("162", 439, 451), sourceContractPolicy="Current caption, key and file existence checked individually; whole-scene image/runtime review remains separate.")
    t.define("T6-VOTE-01", "vote", "16c3", 347, prompt="과거 사건에서 확인한 행위자를 지목하세요", answer="koto", candidates=["mio", "rei", "sora", "ken", "nana", "riku", "akari", "yuu", "koto", "satsuki", "taiga", "rin", "sho", "ai", "haruka", "kaede"], deadCandidatesSelectable=True, selectionRole="historical-fact-intermediate-vote", finalVote=False, voterCount=5, majorityRequired=3, noMajorityPolicy="re-discuss; no new killing case", voteCounts={"koto": 5}, wrongPolicy="Re-examine the historical fact; this identification alone never completes the final hearing or releases control.")
    closing = s("16c3", 411, 551, to)
    name = r.recall("6-C02:post-vote", "6-C02", [("A", s("16c3", 391, 393, closing)), ("B", s("16c3", 397, 399, closing)), ("C", s("16c3", 403, 405, closing))], "16c3", 389)
    control_result = s("16c3", 365, 387, name)
    result = s("16c3", 349, 364, _final_hearing(t, control_result))
    vote = t.input("T6-VOTE-01", result)
    vote_prelude = s("16c3", 237, 347, vote)
    preserve = r.menu("16c3", "T6-C01", 23, [("A", "원문과 자신의 해석을 분리해 남기겠다고 한다", s("16c3", 31, 99, vote_prelude)), ("B", "각자 가져갈 자료부터 확인하겠다고 한다", s("16c3", 103, 169, vote_prelude)), ("C", "밖으로 전체 자료의 사본을 보내려 하겠다고 한다", s("16c3", 173, 231, vote_prelude))])
    lie_echo = r.branch("T6-LIE-B:before-preservation", "T6-LIE-B", [(True, s("169", 400, 406, preserve))], preserve)
    final_condition = s("16c3", 5, 17, lie_echo)
    return t.input("T6-MG-01", final_condition)


def _final_hearing(t, to):
    """The last input closes the whole mystery, not one historical killing."""
    r = t.r
    source = r.d['195']
    questions = []
    rows = [
        ('초청 명단과 실제 접수를 구별하면?', ['같은 숫자이면 같은 몸이 함께 도착했다', '서로 다른 날짜와 생성 전후의 인원을 따로 확인해야 한다', '명단이 맞으니 등록 경위는 확인할 필요 없다'], 'B', 'T6-Z02', '명단 숫자는 몸과 시각까지 증명하지 않아. 요청과 접수를 다시 보자.'),
        ('서로를 알아보지 못한 원인과 옛 망각의 관계는?', ['나나가 지운 한 시간에 모든 학원생활이 들어 있다', '기록을 읽으면 삭제된 경험이 전부 재생된다', '옛 기억 삭제와 이번 입소의 인물 연결 차폐는 별개다'], 'C', 'T6-Z03', '최근 한 시간이라는 범위를 넘겨서 다른 기억까지 지웠다고 할 수는 없어.'),
        ('누구의 의식인지 확인하면 무엇이 면제될까?', ['현재 운영에서 고른 행동은 별도로 따져야 한다', '과거 피해자이므로 현재 처형에 책임이 없다', '생성된 사람과 안내자는 같은 인격의 부활이다'], 'A', 'T6-Z04', '기원이 같은 이름에 닿는다고 지금 한 행동이나 서로 다른 몸까지 하나가 되지는 않아.'),
        ('이번 게임의 관계는 모두 차폐가 만든 가짜일까?', ['관계 기억을 막았으니 이후의 선택도 모두 조종됐다', '광장에서 깨어난 뒤 듣고 고른 행동은 각자의 몫으로 남는다', '옛 친구였다면 지금의 배신은 성립하지 않는다'], 'B', 'T6-Z05', '막힌 것은 광장에서 깨어나기 전의 인물 연결이야.그 뒤 거절을 듣고 한 일까지 그 처리에 맡길 수는 없어.'),
        ('중앙 출입 통제를 끝내면 함께 확정되는 것은?', ['외부 구조와 인형 의식 종료까지 전부 확정된다', '모든 마법과 문 잠금과 부상이 동시에 사라진다', '출입 통제·이번 입소 차폐의 종료를 확인하며 발신·물리 경로·의식 지원은 따로 고른다'], 'C', 'T6-Z06', '출입과 이번 차폐가 끝나도 연락과 의식 지원은 별도야. 한꺼번에 고르지는 말자.'),
        ('밖으로 남길 기록은 무엇을 구별해야 할까?', ['확인한 자료·개별 진술·기록자의 해석을 나누어야 한다', '죽은 사람에게 물을 수 없으니 가장 좋은 해석을 사실로 쓴다', '모든 사람이 같은 책임을 졌다고 쓰면 공평하다'], 'A', 'T6-Z07', '못 묻는 자리는 못 물었다고 남겨야 해. 내가 고른 해석으로 빈 답을 채우지는 않을게.'),
        ('지금 이 재판을 마치며 확정할 수 있는 결정은?', ['한 사람을 모든 원인으로 정하고 새 처형을 요구한다', '확인한 진상과 책임을 남기고 현재 살인 게임의 통제를 끝낸다', '기억을 전부 되찾을 때까지 다음 살인이 나기를 기다린다'], 'B', 'T6-Z08', '사람 하나를 더 골라 없애는 게 마지막 답은 아니야. 무엇을 끝내기로 했는지 다시 보자.'),
    ]
    for i, (prompt, labels, answer, section, retry) in enumerate(rows, 1):
        a, z = source.section(section)
        # Wrong responses are authored current reasoning, not fabricated facts.
        wrong = t.events('195', *source.section(f'T6-ZR{i:02d}'))
        from v4_editorial_ids import original_voice_line
        from build_v4_story import speaker_line
        authored_original = [speaker_line(original_voice_line(source.name,event['source']['line'],source.lines[event['source']['line']-1]))['text'] for event in wrong if event['type']=='say']
        assert authored_original == [retry]
        questions.append({'id':f'T6-RL-FINAL:link:{i}', 'q':prompt,
                          'options':[{'id':key,'label':label} for key,label in zip('ABC',labels)],
                          'answer':answer, 'success':t.events('195',a,z),
                          'wrongVariants':[{'optionId':key,'script':wrong} for key in 'ABC' if key!=answer],
                          'retryPolicy':'currentLinkOnly', 'source':source.ref(a)})
    a, z = source.section('T6-Z01')
    t.define('T6-RL-FINAL','reasoning','195',a, prompt='마지막 기록 — 일곱 쟁점',
             questions=questions, selectionRole='whole-mystery-final-hearing', finalVote=False,
             closesMysteries=['roster','relationship-memory','created-identity','operator-responsibility','participant-agency','control-support','record-accountability'])
    return r.seq('195', a, z, t.input('T6-RL-FINAL',to))


def _ending(r, to):
    s, b, rb = r.seq, r.branch, r.recall
    final_statement = s("16d2", 708, 754, to)
    lie6_tail = s("169", 460, 460, final_statement)
    lie6_support = rb("E6-C01:last-lie", "E6-C01", [("A", s("169", 452, 452, lie6_tail)), ("B", s("169", 456, 456, lie6_tail))], "169", 450)
    lie6 = b("T6-LIE-B:outside", "T6-LIE-B", [(True, s("169", 444, 448, lie6_support))], final_statement)
    lie5 = b("T5-LIE-B:outside", "T5-LIE-B", [(True, s("169", 434, 440, lie6))], lie6)
    lie4 = b("T4-LIE-B:outside", "T4-LIE-B", [(True, s("169", 424, 430, lie5))], lie5)
    lie2 = b("T2-LIE-B:outside", "T2-LIE-B", [(True, s("169", 414, 420, lie4))], lie4)
    lie1 = b("T1-LIE-B:outside", "T1-LIE-B", [(True, s("16d2", 688, 700, lie2))], lie2)
    asked = rb("T6-C02:outside", "T6-C02", [("A", s("16d2", 672, 672, lie1)), ("B", s("16d2", 676, 676, lie1)), ("C", s("16d2", 680, 680, lie1))], "16d2", 668)
    voice = rb("E6-C02:outside", "E6-C02", [("A", s("16d2", 650, 652, asked)), ("B", s("16d2", 656, 658, asked)), ("C", s("16d2", 662, 664, asked))], "16d2", 646)
    own_action = rb("E6-C01:own-action", "E6-C01", [("A", s("16d2", 636, 638, voice)), ("B", s("16d2", 642, 644, voice))], "16d2", 634)
    introduce_self = s("16d2", 628, 632, own_action)
    help_end = s("122", 165, 175, introduce_self)
    help_nana = rb("E6-C01:outside-help", "E6-C01", [("A", s("122", 121, 145, help_end)), ("B", s("122", 149, 159, help_end))], "122", 119)
    help_common = s("122", 7, 115, help_nana)
    all_five = rb("E6-C01:five-locations", "E6-C01", [("A", s("16d2", 540, 568, help_common)), ("B", s("16d2", 572, 620, help_common))], "16d2", 538)
    outside = s("16d2", 470, 536, all_five)
    name = rb("6-C02:written-name", "6-C02", [("A", s("16d2", 456, 456, outside)), ("B", s("16d2", 460, 460, outside)), ("C", s("16d2", 464, 464, outside))], "16d2", 454)
    name_intro = s("16d2", 452, 452, name)
    paper = rb("T6-C01:outside-paper", "T6-C01", [("A", s("16d2", 422, 428, name_intro)), ("B", s("16d2", 432, 438, name_intro)), ("C", s("16d2", 442, 448, name_intro))], "16d2", 420)
    after_support = s("16d2", 396, 418, paper)
    support = r.menu("16d2", "E6-C01", 275, [("A", "현재 의식 지원을 중단한다. 미오 자신의 행위로 남긴다", s("16d2", 284, 338, after_support)), ("B", "현재 의식 지원을 유지한다. 동행과 용서는 따로 거절할 수 있게 한다", s("16d2", 342, 390, after_support))])
    r.g.nodes[support].update(selectionRole="consciousness-support-decision", correctChoice=None, scoreReward=False, changesEscapeEligibility=False)
    # The source requires both the consequence and the prior disagreement to
    # be visible at the actual decision. No correct-choice flourish is scored.
    support_read = r.document("support-current-meaning", "16d2", 280, "현재 의식 지원", ["현재 의식의 유지 조건에 관한 선택이에요.", "중단하면 같은 의식이 다시 깨어난다고 보증할 수 없어요.", "문은 이미 열려 있고 어느 선택도 탈출의 추가 조건이 아니에요.", "나나는 현재 중단에 반대한다고 말했어요."], support)
    last_talk = s("16d2", 121, 273, support_read)
    helping = rb("6-C03:opposition", "6-C03", [("A", s("16d2", 101, 103, last_talk)), ("B", s("16d2", 107, 109, last_talk)), ("C", s("16d2", 113, 115, last_talk))], "16d2", 97)
    phone_again = s("16d2", 65, 95, helping)
    morning_echo = s("171", 298, 312, phone_again)
    before_support = s("16d2", 7, 59, morning_echo)
    door = s("16d1", 139, 227, before_support)
    count = rb("T6-C03:result", "T6-C03", [("A", s("104", 243, 249, door)), ("B", s("104", 253, 259, door)), ("C", s("104", 263, 269, door))], "104", 237)
    papers = rb("T6-C01:actual-paper-action", "T6-C01", [("A", s("16d1", 95, 101, count)), ("B", s("16d1", 107, 113, count)), ("C", s("16d1", 119, 131, count))], "16d1", 91)
    transmitter = s("16d1", 87, 89, papers)
    after_voice = s("73", 163, 173, transmitter)
    external_voice = r.menu("73", "E6-C02", 79, [("A", "래피가 직접 말할 기회를 둔다", s("73", 83, 105, after_voice)), ("B", "미오가 현재 상태를 설명하고 직접 발언은 뒤로 미룬다", s("73", 109, 135, after_voice)), ("C", "현재 연락할 사람에 래피를 넣지 말라고 한다", s("73", 139, 159, after_voice))])
    r.g.nodes[external_voice].update(selectionRole="current-external-speaking-turn", changesSupportChoice=False)
    current_voice = s("73", 7, 77, external_voice)
    return s("16d1", 7, 81, current_voice)


def compile_chapter_six(sources, freetime_graphs, tasks=None):
    from build_v4_story import Graph
    graph = Graph("6")
    if tasks is not None:
        graph.taskDefinitions = tasks["tasks"]
    r = Router(graph, sources)
    for p, digest in REVIEWED_HASHES.items():
        if r.d[p].hash != digest:
            raise ValueError(r.d[p].name + ": source changed; re-read before applying fixed source ranges")
    gate = r.gate("trial", "Final trial and ending require explicit source routes; no old plot or automatic guessed answer.", "16c1", 5)
    if "T6-NS-A01" in graph.taskDefinitions:
        _bind_tasks(r, graph.taskDefinitions)
        common_end = {"type": "end", "chapterComplete": True, "campaignNarrativeEnd": True, "humanSurvivors": ["mio", "rin", "nana", "sho", "satsuki"], "externalVerdict": "open", "familyStatus": "unconfirmed", "source": r.d["16d2"].ref(754)}
        end_a = graph.add("v4:6:end:A", {**common_end, "supportActive": False, "lappyResponsive": False, "nanaLocation": "outside", "humanLocations": {x: "outside" for x in ("mio", "rin", "nana", "sho", "satsuki")}})
        end_b = graph.add("v4:6:end:B", {**common_end, "supportActive": True, "lappyResponsive": True, "nanaLocation": "inside-current-reception", "humanLocations": {**{x: "outside" for x in ("mio", "rin", "sho", "satsuki")}, "nana": "inside-current-reception"}})
        ending_state = r.recall("E6-C01:ending-state", "E6-C01", [("A", end_a), ("B", end_b)], "16d2", 744)
        later = _ending(r, ending_state)
        t = Trial(r, graph.taskDefinitions)
        last = _trial_final(t, later)
        middle = _trial_middle(t, last)
        trial = _trial_opening(t, middle)
        graph.nodes[gate] = {"id": gate, "type": "stage", "direction": "과거 사건의 자료와 현재 다섯 사람의 진술을 별도로 들고 최종 심리로 간다.", "next": trial}
        r.pending.remove(gate)
    investigation, catalogue = _investigation(r, gate)
    entry = _living(r, investigation)
    from v4_story_case6_extension import compile_arrival
    entry = compile_arrival(r, entry)
    # A shared card receives the currently read schedule/actor distinctions
    # only after those actual existing documents are discussed, before PN-A02.
    updates = {("16a5", 113): {"public:nana:old-vow-ended": True}, ("16c3", 367): {"public:game:control-ended": True, "public:intake:relationship-mask-ended": True}, ("16d1", 29): {"public:outside:actual-response": True}, ("16d1", 119): {"public:records:reception-first-page-sent": True}, ("16d1", 153): {"public:loading-gate:opened": True}, ("16d2", 306): {"public:lappy:support-active": False, "public:lappy:responsive": False}, ("16d2", 342): {"public:lappy:support-active": True, "public:lappy:responsive": True}}
    source_prefixes = {v.name: k for k, v in r.d.items()}
    for node in list(graph.nodes.values()):
        ref = node.get("source", {})
        key = (source_prefixes.get(ref.get("file")), ref.get("line"))
        if key in updates:
            node.setdefault("set", {}).update(updates[key])
        if key == ("16c1", 127):
            ident = "v4:6:update:document-signatures-and-schedule"
            name, text = CARDS["E6-05"]
            text += " 실제 개장 일정에는 레이 아버지 이름이 있고, 어른들의 수정·승인·일정과 자녀가 한 일의 날짜·주체를 나누어 읽었어요."
            graph.add(ident, {"type": "evidence", "evidenceId": "v4:E6-05", "name": name, "text": text, "revision": True, "source": ref, "next": node["next"]})
            node["next"] = ident
    seats = ["mio", "rei", "sora", "ken", "nana", "riku", "akari", "yuu", "koto", "satsuki", "taiga", "rin", "sho", "ai", "haruka", "kaede"]
    for node in graph.nodes.values():
        if node["type"] == "task":
            node.update(trialDead=[x for x in seats if x not in ("mio", "rin", "nana", "sho", "satsuki")], seats=seats, rosterSource=r.d["16c1"].ref(3))
    return graph.export(entry, evidenceCatalog=catalogue, resultTaskId="T6-RL-FINAL", campaignReady=False, chapterComplete=False, routingStatus="explicit-reviewed-routes-through-final-open-ending" if "T6-NS-A01" in graph.taskDefinitions else "explicit-living-investigation", contentScope="Current living/shadow/vow uses, scoped investigation/documents, complete final-trial route with exact choices and real vote, actual external call, separate speaking/data/support choices, exclusive source aftermath and two current-location endings. Actual picture geometry/runtime/audio and whole-campaign validation remain separate.", pendingRouteIds=r.pending, reviewedSourcePrefixes=sorted(REVIEWED_HASHES), sourceAddressPolicy="Semantic event IDs; every reviewed source revision is locked.")
