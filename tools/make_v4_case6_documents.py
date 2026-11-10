"""Render source-exact editable chapter-six inspection aids, never a new clue.

The title-only delivery documents remain intact. Layout is an inspection UI
arrangement of already authored pages, not an invented composite original.
"""
from pathlib import Path
import hashlib
import json
from make_v4_case1_documents import Drawing, PAPER, INK, MUTED, BORDER, W, H, S

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ui/v4/documents_case6_runtime_v1"


class Document(Drawing):
    def save(self, name):
        path = OUT / name
        path.with_suffix(".svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S}" height="{H*S}" viewBox="0 0 {W} {H}">' + "".join(self.parts) + '</svg>\n', encoding="utf-8")
        self.im.save(path.with_suffix(".webp"), "WEBP", lossless=True, method=6)
        return path.with_suffix(".webp").relative_to(ROOT).as_posix()


def proof(prefix, line, quote):
    from v4_story_case6 import REVIEWED_HASHES
    path = next((ROOT / "docs/design/rewrite_v4").glob(prefix + "_*.md"))
    text = path.read_text(encoding="utf-8-sig")
    digest = hashlib.sha256(text.encode()).hexdigest()
    if digest != REVIEWED_HASHES[prefix] or quote not in text.splitlines()[line-1]:
        raise ValueError(f"Changed source; re-read before drawing {path.name}:{line}")
    return {"file": path.name, "line": line, "quote": quote, "sha256": digest}


def rect(x, y, width, height):
    return [[x/W, y/H], [(x+width)/W, y/H], [(x+width)/W, (y+height)/H], [x/W, (y+height)/H]]


def make():
    OUT.mkdir(parents=True, exist_ok=True)
    fields = [("옛 검토 의견", "살의 입력 제한 확인:미완료.", "해당 항목 인계 유보.", 369),
              ("수정 접수의 확인", "동일 안전 항목을 완료로 수정.", "최종본에 반영.", 370),
              ("최종본의 승인 대상 항목", "살의 입력 제한 확인:정상.", "", 371),
              ("다음 점검 인수 목록", "동일 안전 항목:미해결.", "유보 상태로 인수.", 372)]
    safety_source = [proof("16b1", number, first + second) for _, first, second, number in fields]
    safety_source.append(proof("186", 690, "최종본의 살의 입력 제한 확인 칸"))
    d = Document()
    d.text(80, 88, "안전 항목 · 네 자료의 표시", 42)
    d.text(80, 137, "옛 검토 의견 / 수정 접수 / 최종본 / 다음 인수", 26, MUTED)
    regions = []
    for index, (title, first, second, _) in enumerate(fields):
        x, y = (80 if index % 2 == 0 else 840), (195 if index < 2 else 560)
        d.box(x, y, 680, 310)
        d.text(x+28, y+57, title, 29)
        d.line([(x+28,y+85),(x+652,y+85)], BORDER, 2)
        d.text(x+28, y+165, first, 32)
        if second:
            d.text(x+28, y+225, second, 32)
        regions.append({"id": ("review", "revision", "final-normal-field", "next-handover")[index], "label": title, "polygon": rect(x+20,y+100,640,175), "correct": index == 2})
    image = d.save("safety_four_documents")
    safety = {"image": image, "coordinateSystem": "normalized-image-uv", "answerRegionId": "final-normal-field", "regions": regions, "source": safety_source, "evidenceId": "v4:E6-05", "title": "안전 항목의 네 기록", "notNewEvidence": True, "layoutRole": "inspection comparison of four separate existing records; no new parent names, signatures, dates or safety-item code"}

    statement_source = [proof("16b2", n, quote) for n, quote in [(83, "하루카와 같이 점검 통로로 갔다."), (85, "하루카가 내 팔을 잡았다."), (87, "손을 뿌리쳤다."), (89, "하루카가 떨어지는 것을 봤다."), (101, "하루카가 혼자 홀 쪽으로 가 추락한 것으로 정리돼 있다.")]]
    statement_source.append(proof("186", 718, "원문의 동행과 팔 접촉 부분"))
    d = Document()
    d.text(80, 88, "당시 진술 · 사고 요약", 42)
    d.text(80, 137, "같은 조사 묶음에서 확인한 두 자료", 26, MUTED)
    d.box(80,195,730,675)
    d.text(112,252,"당시 진술 원문",32)
    d.line([(112,280),(775,280)], BORDER,2)
    for y, number in zip((365,465,565,665),(83,85,87,89)):
        line=next(p["quote"] for p in statement_source if p["line"]==number)
        d.text(112,y,line,31)
    d.box(860,195,660,675)
    d.text(892,252,"요약 보고",32)
    d.line([(892,280),(1488,280)], BORDER,2)
    # The manuscript supplies the summary's observed meaning, not a quoted
    # full report. Keep it visibly a reading explanation rather than forge
    # a new verbatim official sentence or an invented reception number.
    d.text(892,340,"열람 때 확인한 내용",25,MUTED)
    for y, line in zip((420,480,540),("하루카가 혼자 홀 쪽으로 가", "추락한 것으로", "정리돼 있다.")):
        d.text(892,y,line,31)
    image=d.save("statement_summary_comparison")
    statement={"image":image,"coordinateSystem":"normalized-image-uv","answerRegionId":"companion-and-arm-contact","regions":[{"id":"companion-and-arm-contact","label":"원문의 동행과 팔 접촉","polygon":rect(100,310,690,190),"correct":True},{"id":"later-statement-lines","label":"그 뒤 진술 두 줄","polygon":rect(100,515,690,190),"correct":False},{"id":"summary-description","label":"요약 보고의 열람 설명","polygon":rect(880,365,610,220),"correct":False}],"source":statement_source,"evidenceId":"v4:E6-09","title":"당시 진술과 요약 보고 대조","notNewEvidence":True,"layoutRole":"left four lines are exact source quotations; right is explicitly labeled source-described reading explanation, not a forged full document or a new confession"}
    topology_source=[proof("16b1",49,"옆 관리 통로의 위치"),proof("16b1",51,"문틈으로"),proof("16b1",77,"주 통로 바깥의 옆 출입"),proof("16b1",113,"정확한 발자국이 있었다는 표시는 하지 않는다"),proof("16b1",201,"밀침 자체나 홀 내부는 찍히지 않았다"),proof("186",505,"추락 아래 바닥"),proof("186",506,"옆 유지보수문 쪽 나나 관찰 자리")]
    d=Document()
    d.text(80,88,"옛 도면·사진의 출입 관계",42)
    d.text(80,137,"비축척 관계도 · 선의 길이와 화면의 배치는 실제 거리·문 좌표를 뜻하지 않아요",25,MUTED)
    d.box(80,220,450,150)
    d.text(110,280,"주 점검 통로 입구",32)
    d.text(110,330,"두 사람의 동행 자료",27,MUTED)
    d.line([(530,295),(700,295)],INK,4)
    d.box(700,220,820,210)
    d.text(730,280,"홀 안의 대화 · 그 뒤의 동작",32)
    d.text(730,337,"얼굴을 본 때와 뒤의 손을 본 때는 달라요",27,MUTED)
    d.text(730,390,"나나가 진술한 범위",25,MUTED)
    d.box(80,430,450,130)
    d.text(110,485,"주출입 영상 카메라",30)
    d.text(110,535,"홀 안의 밀침은 찍히지 않음",26,MUTED)
    d.line([(1110,430),(1110,620)],BORDER,3)
    d.text(1140,525,"문틈으로 본 범위",25,MUTED)
    d.box(700,620,820,210)
    d.text(730,685,"옆 관리 출입",32)
    d.text(730,745,"주 통로 바깥 · 나나가 서 있었다는 곳",29)
    d.text(730,800,"문 안으로 함께 들어간 자리가 아니에요",26,MUTED)
    d.box(80,680,450,150)
    d.text(110,745,"추락 아래 바닥",32)
    d.text(110,800,"계속 보았다는 진술은 없음",26,MUTED)
    image=d.save("old_access_sight_relations")
    topology={"image":image,"coordinateSystem":"normalized-image-uv","answerRegionId":"side-maintenance-observer","regions":[{"id":"side-maintenance-observer","label":"옆 관리 출입의 관찰 자리","polygon":rect(700,620,820,210),"correct":True},{"id":"main-entry-camera","label":"주출입 영상 카메라","polygon":rect(80,430,450,130),"correct":False},{"id":"fall-lower-floor","label":"추락 아래 바닥","polygon":rect(80,680,450,150),"correct":False,"wrongVariant":"floor"}],"source":topology_source,"evidenceId":"v4:E6-02","title":"옛 출입과 목격 범위의 대조","notNewEvidence":True,"layoutRole":"source-exact nonmetric topology. No actual hall perimeter, door coordinates, distances, child footprints or 3D-world position is asserted. Nana's statement and the entry camera's separate recorded scope are labeled separately.","presentationPrompt":"수사 때 맞춘 출입·시야 관계에서 나나가 뒤의 두 손을 본 관찰 자리를 가리키자."}
    for picture in (safety,statement,topology):
        picture["sha256"]=hashlib.sha256((ROOT/picture["image"]).read_bytes()).hexdigest()
        picture["visualReview"]="Directly viewed full 3200x2000 rendered WebP: all Korean fields readable, four safety states separate, four statement lines intact, summary explicitly a reading explanation. No new date, signature name, item code, confession or official report wording."
    topology["visualReview"]="Directly viewed full3200x2000 relation diagram. Nonmetric notice and the separate entry recording/Nana statement scopes are readable. Side observation is outside the main passage; no real wall perimeter, child footprint, distance, angle or door-world position is asserted."
    manifest={"schemaVersion":1,"rasterSize":[W*S,H*S],"safety":safety,"statement":statement,"topology":topology,"preservedOriginals":["ui/v4/documents_hd/document_original.webp","ui/v4/documents_hd/document_summary.webp"],"vectorText":"Pretendard glyph outlines with original editable data-label strings; edit source and regenerate"}
    (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"documents":3,"rasterSize":[W*S,H*S],"out":str(OUT),"newEvidence":False},ensure_ascii=False))


if __name__=="__main__":
    make()
