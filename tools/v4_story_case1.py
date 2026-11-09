"""Hand-authored V4 case-one investigation routes and evidence acquisition.

The source dialogue is not edited here. Every scope ends by returning to its
investigation hub; evidence is awarded only inside the completed source scope.
"""
from __future__ import annotations

from typing import Any


CARD_TEXT = {
    "E1-01": ("목 손상 파일", "래피 파일: 사인은 목 부위의 지속적 압박. 압박 흔적은 피해자 자신의 손과 일치하지 않아요. 정확한 분 단위 사망 시각은 특정되지 않았어요."),
    "E1-02": ("전면A 개폐 기록과 표찰", "센서는 문의 열림과 닫힘을 기록해요. 표찰은 문이 닫혔다는 표시예요. 사람의 이름·인원·생존을 기록한 장치가 아니에요."),
    "E1-03": ("뒤 보수문B와 고정 구조", "B의 봉인·외부 보강판·문짝과 프레임, 고정 창과 상부·수납 구조를 확인했어요. 린의 시험 자국과 실제 개방을 구별해요."),
    "E1-04": ("인쇄 번호와 출력 목록", "인쇄 목록에는 번호와 완료 순서가 남아요. 미오가 맡은16번 사본과 현장의17번 보고서는 별개예요. 번호만으로 시각·사용자를 알 수는 없어요."),
    "E1-05": ("17번 보고서 원본", "현장 보고서의 찢긴 결손과 본문을 보존했어요. 아카리가 투명 보관 봉투에 든 원본을 맡아요. 이 사실이 이전의 완전한 봉인을 증명하지는 않아요."),
    "E1-06": ("보호대 종이 조각 대조", "나나가 발견 전에 보호대에서 꺼내 따로 둔 조각을 소라와 대조했어요.17번 원본의 가장자리·본문과 이어져요. 직접 살해한 손이나 종이가 들어간 순간을 본 자료는 아니에요."),
    "E1-07": ("원본 순찰표", "처음 숫자와 수정된 요약, 실제 합류와 각각의 이동을 나누어 보아요. 같은 행의 두 이름이 전 시간의 연속 동행을 보증하지는 않아요."),
    "E1-08": ("처음 지급한 손목 보호대", "짐을 옮기던 날 나나가 새 보호대의 안쪽 종이띠를 빼고 안팎을 확인했어요. 기존 통증과 뒤에 나온 이물질을 나누어 보아요. 모든 동작의 힘이 없었다는 진단은 없어요."),
    "E1-09": ("작동 확인 기록과 공개 유예", "작동 확인 불가와 정상 기록의 차이, 장비 표시·커버 상태와 레이의 공개 유예 요청을 대조했어요. 전체 고장 원인이나 보지 않은 손동작은 확정되지 않았어요."),
    "E1-10": ("피해자 동선과 별개 목격", "나나는 카에데의 얼굴과 휴게실로 가는 방향을 직접 보았어요. 당시 들은 말과 나중에 덧붙인 해석을 따로 보존해요."),
    "E1-11": ("결빙 위치와 현장 구조", "가구·문 구조와 목의 지속 압박 손상, 바닥의 결빙을 대조했어요. 결빙 흔적만으로 선제공격이나 정확한 발생 시각을 정하지 않아요."),
    "E1-12": ("미오의 요약과 원래 관찰", "함께 점검했다는 제목과 실제로 각각 본 구간을 나누어요. 요약의 오류 하나가 모든 관찰과 노트 전체를 지우지는 않아요."),
    "CONTACT": ("대표 통화 신청 조건", "대표를 정해 접수하면 신청은 그 사람에게 남아요. 다른 참가자에게 넘기거나 대표를 바꾸어 새로 신청할 수 없어요. 옆에서 도울 수 있다는 조건은 별개예요."),
}


def card_id(code: str) -> str:
    return "v4:11a2:1-16:contact-rule" if code == "CONTACT" else "v4:" + code


def compile_investigation(graph: Any, sources: dict[str, Any], next_id: str) -> tuple[str, dict[str, Any]]:
    source = next(s for s in sources.values() if s.prefix == "11b")
    case_ledger = next(s for s in sources.values() if s.name.startswith("03_1장_사건원장"))
    catalogue = {card_id(k): {"id": card_id(k), "name": name, "text": text, "source": case_ledger.ref(1), "grantPolicy": "actual-scope-only"} for k, (name, text) in CARD_TEXT.items()}

    def seq(a: int, b: int, target: str) -> str:
        return graph.sequence(source, a, b, target)

    def grant(code: str, target: str, at: int, *, revision: bool = False, text: str = "") -> str:
        ident = f"v4:11b:grant:{code}:{at}"
        name, description = CARD_TEXT[code]
        return graph.add(ident, {"type": "evidence", "evidenceId": card_id(code), "name": name, "text": text or description, "revision": revision, "source": source.ref(at), "next": target})

    def hub(ident: str, label: str, space: str, target_id: str, first: int, last: int, next_hub: str, grants: tuple[str, ...] = (), custom=None) -> str:
        node_id = f"v4:1:investigate:{ident}"
        returned = graph.add(node_id + ":return", {"type": "return"})
        end = returned
        for code in reversed(grants):
            end = grant(code, end, last)
        entry = custom(end) if custom else seq(first, last, end)
        spot_id = f"v4:11b:{ident}"
        flag = spot_id + ":complete"
        graph.add(node_id, {"type": "investigate", "title": label, "source": source.ref(first), "spots": [{"id": spot_id, "label": label, "space_id": space, "target_id": target_id, "geometryReady": bool(target_id), "interactionPolicy": "authored-world-target" if target_id else "source-backed-inspection-or-person-interview-awaiting-placement", "entry": entry, "returnTo": node_id, "completionFlag": flag, "onReturnSet": {flag: True}, "required": True}], "requiredSpotIds": [spot_id], "requiredCards": [card_id(c) for c in grants], "next": next_hub, "orderPolicy": "The authored information dependencies use successive scopes. This is not a claim that arbitrary inspection-order permutations are verified."})
        return node_id

    # The elevator sequence remains actual dialogue. It does not silently start
    # or solve the later trial while its data is still being authored.
    leaving = seq(897, len(source.lines), next_id)
    equipment = hub("I-12d", "통신 장비의 실제 상태", "management_office", "", 877, 896, leaving, ("E1-09",))
    # The later re-question is a real update, not a fact that appeared in the
    # first witness card before anyone had been asked the earlier interval.
    witness_update = grant("E1-10", "v4:1:investigate:I-12c:return", 875, revision=True, text=CARD_TEXT["E1-10"][1] + " 뒤의 재질문에서 아카리의 앞선 마당 대기와 사츠키의 나중 합류를 분리했어요. 둘의 목격을 처음부터 같은 연속 관찰로 합치지 않아요.")
    earlier_witness = hub("I-12c", "먼저 있던 마당과 나중 합류", "service_lounge", "", 825, 876, equipment, custom=lambda end: seq(825, 876, witness_update))
    print_update = grant("E1-04", "v4:1:investigate:I-12b:return", 823, revision=True, text=CARD_TEXT["E1-04"][1] + " 린이 마지막으로 확인했을 때의 목록과 발견 전에 회수된 조각을 대조해 상대 순서를 추가했어요. 정확한 분 단위 시각은 여전히 아니에요.")
    printing = hub("I-12b", "마지막으로 확인한 출력 목록", "service_lounge", "printer", 787, 824, earlier_witness, custom=lambda end: seq(787, 824, print_update))

    def search(end: str) -> str:
        common = seq(776, 786, end)
        menu = graph.add("v4:11b:I-C01", {"type": "menu", "q": "수색의 범위", "options": [{"id": "A", "label": "현재 보고서와 연결되는 자료부터 찾는다", "to": seq(704, 744, common), "set": {"I-C01": "A"}}, {"id": "B", "label": "현장 증거가 충분할 때까지 방을 보류한다", "to": seq(746, 774, common), "set": {"I-C01": "B"}}], "source": source.ref(701)})
        before_menu = graph.add("v4:11b:1-C04:permission", {"type": "branch", "cases": [{"flag": "1-C04", "equals": "B", "to": seq(692, 694, menu)}], "default": seq(696, 698, menu)})
        return seq(673, 690, before_menu)

    searching = hub("I-12", "받은 사본과 열람 범위", "hotel_lobby", "", 673, 786, printing, custom=search)
    sho = hub("I-11", "쇼에게 남은 질문", "service_lounge", "", 641, 672, searching)
    scene = hub("I-10", "현장 구조와 남은 결빙", "service_lounge", "", 613, 640, sho, ("E1-11",))
    rescue_claim = hub("I-09", "소라가 말한 가능성", "hotel_corridor", "", 585, 612, scene)
    paper = hub("I-08", "보호대에서 회수한 조각", "clinic", "", 525, 584, rescue_claim, ("E1-06",))
    patrol = hub("I-07", "순찰표의 원래 숫자", "hotel_lobby", "", 469, 524, paper, ("E1-07", "E1-12"))
    nana = hub("I-06", "나나가 직접 본 얼굴", "service_lounge", "", 431, 468, patrol, ("E1-10",))

    def rear(end: str) -> str:
        common = seq(426, 430, end)
        conditional = graph.add("v4:11b:RIN01:access", {"type": "branch", "cases": [{"flag": "RIN-01B", "equals": "C", "to": seq(410, 418, common)}], "default": seq(420, 424, common)})
        return seq(363, 408, conditional)

    rear_door = hub("I-05", "뒤 보수문과 고정 상태", "service_lounge", "door_B", 363, 430, nana, ("E1-03",), custom=rear)
    front_door = hub("I-04", "전면 문과 표찰·센서", "service_lounge", "door_A", 321, 362, rear_door, ("E1-02",))
    printer = hub("I-03", "16번 사본과17번 원본", "service_lounge", "printer", 291, 320, front_door, ("E1-04", "E1-05"))
    body_scene = hub("I-02", "현장에서 먼저 남긴 배치", "service_lounge", "", 74, 290, printer)
    after_file = seq(65, 73, body_scene)
    acquired_file = grant("E1-01", after_file, 64)
    file_page = graph.add("v4:11b:I-01:document", {"type": "document", "title": "래피 파일", "rows": [source.lines[61][2:]], "private": False, "source": source.ref(62), "next": acquired_file})
    entry = seq(6, 61, file_page)
    return entry, catalogue


def insert_prior_observations(graph: Any, sources: dict[str, Any]) -> None:
    """Attach only facts already explicitly shown in compulsory daily scenes."""
    for prefix, line, code in (("11a2", 530, "E1-08"), ("11a2", 861, "CONTACT")):
        source = next(s for s in sources.values() if s.prefix == prefix)
        matches = [n for n in graph.nodes.values() if n.get("source", {}).get("file") == source.name and n.get("source", {}).get("line") == line]
        if len(matches) != 1:
            raise ValueError(f"{source.name}:{line}: prior-observation source is not unique")
        previous = matches[0]
        node_id = f"v4:{prefix}:observe:{code}"
        name, text = CARD_TEXT[code]
        graph.add(node_id, {"type": "evidence", "evidenceId": card_id(code), "name": name, "text": text, "source": source.ref(line), "next": previous["next"], "revision": False})
        previous["next"] = node_id


def bind_tasks(tasks: dict[str, Any]) -> None:
    bindings = {"T1-NS-A01": "E1-01", "T1-NS-A02": "E1-11", "T1-NS-A03": "E1-02", "T1-NS-A05": "E1-10", "T1-NS-A06": "CONTACT", "T1-NS-A07": "E1-07", "T1-NS-A08": "E1-06", "T1-NS-A09": "E1-04", "T1-NS-A10": "E1-02", "T1-PN-A02": "E1-06", "T1-PN-A03": "E1-09", "T1-RS-A02": "E1-08", "T1-RS-A03": "E1-09", "T1-EVIDENCE-A01": "E1-02"}
    for task_id, code in bindings.items():
        task = tasks["tasks"][task_id]
        task["answerEvidenceId"] = card_id(code)
        task["requiresEvidence"] = [card_id(code)]
        task["evidencePool"] = "actually-acquired-v4-cards-only"
        task["bindings"] = [b for b in task["bindings"] if b["kind"] != "evidenceAcquisition"]
        task["runtimeReady"] = not task["bindings"]
        task["bindingSource"] = "Hand-authored case-one source scopes, not legacy evidence.json or automatic keyword matching."
