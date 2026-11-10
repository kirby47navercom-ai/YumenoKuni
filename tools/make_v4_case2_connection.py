"""Source-exact connection topology, not a composite scene photograph."""
from pathlib import Path
import hashlib
import json
from make_v4_case1_documents import Drawing, INK, MUTED, BORDER, W, H, S
from make_v4_case6_documents import rect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"ui/v4/documents_case2_connection_v1"


def proof(prefix,line,quote):
    from v4_story_case2 import REVIEWED_HASHES
    p=next((ROOT/"docs/design/rewrite_v4").glob(prefix+"_*.md"))
    text=p.read_text(encoding="utf-8-sig")
    digest=hashlib.sha256(text.encode()).hexdigest()
    if digest!=REVIEWED_HASHES[prefix] or quote not in text.splitlines()[line-1]:
        raise ValueError(f"Changed connection source {p.name}:{line}")
    return {"file":p.name,"line":line,"quote":quote,"sha256":digest}


def make():
    source=[proof("12a6",371,"음향 탁자의 별도 입력으로 소리가 나온다"),proof("12b2",195,"선이 꽂혀 있다"),proof("12b2",197,"카드 칸이 비었다"),proof("12c2",179,"기존 기기를 바탕으로 한 연결 도식"),proof("12c2",183,"없던 분배기/무선 장치/새 카메라를 더하지 않는다"),proof("12c2",188,"녹음기에서 음향 탁자의 별도 입력으로 가는 선 끝")]
    d=Drawing()
    d.text(80,88,"음향 기기의 연결",42)
    d.text(80,137,"연결 구조를 대조한 도식 · 서로 다른 시각의 작동 상태를 한 현장 사진으로 합치지 않아요",25,MUTED)
    d.box(80,220,350,250)
    d.text(110,280,"마이크",34)
    d.box(110,340,280,80)
    d.text(132,392,"전원 스위치",28)
    d.box(80,620,350,250)
    d.text(110,685,"공용 녹음기",34)
    d.box(110,750,280,80)
    d.text(132,802,"저장 카드 칸",28)
    d.box(700,250,440,470)
    d.text(745,320,"음향 탁자",36)
    d.box(680,345,40,60)
    d.text(745,389,"마이크 입력",29)
    d.line([(430,375),(680,375)],INK,5)
    d.box(680,540,40,60)
    d.text(745,584,"별도 입력",29)
    d.line([(430,685),(565,685),(565,570),(680,570)],INK,5)
    d.text(445,748,"녹음기의 연결선",25,MUTED)
    d.box(1260,350,270,250)
    d.text(1300,422,"스피커",34)
    d.text(1290,500,"소리가 나가는 쪽",25,MUTED)
    d.line([(1140,460),(1260,460)],INK,5)
    OUT.mkdir(parents=True,exist_ok=True)
    svg=OUT/"audio_connection.svg"
    svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S}" height="{H*S}" viewBox="0 0 {W} {H}">' + "".join(d.parts) + '</svg>\n',encoding="utf-8")
    image=OUT/"audio_connection.webp"
    d.im.save(image,"WEBP",lossless=True,method=6)
    contract={"schemaVersion":1,"image":image.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(image.read_bytes()).hexdigest(),"coordinateSystem":"normalized-image-uv","answerRegionId":"recorder-separate-input-end","regions":[{"id":"microphone-switch","label":"마이크 전원 스위치","polygon":rect(110,340,280,80),"correct":False,"wrongVariant":"microphone-switch"},{"id":"recorder-separate-input-end","label":"녹음기 선의 별도 입력 끝","polygon":rect(665,530,260,80),"correct":True},{"id":"recorder-card-slot","label":"녹음기 저장 카드 칸","polygon":rect(110,750,280,80),"correct":False,"wrongVariant":"card-slot"},{"id":"speaker-output","label":"스피커로 나가는 쪽","polygon":rect(1140,425,390,150),"correct":False,"wrongVariant":"speaker-output"}],"evidenceId":"v4:E2-06","title":"낮의 시험과 수사에서 확인한 기기 연결","notNewEvidence":True,"source":source,"layoutRole":"Topology of the explicitly authored microphone, public recorder, separate desk input, card slot and speaker output. No exact hardware socket shape, device-brand, live power/card state or new splitter/wireless device is asserted.","visualReview":"Directly viewed full3200x2000 WebP. Four different selectable elements and both separate input connections are legible. No live switch/card status is painted and no added splitter, radio or camera appears."}
    (OUT/"manifest.json").write_text(json.dumps(contract,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"diagram":1,"rasterSize":[W*S,H*S],"out":str(OUT),"newEvidence":False},ensure_ascii=False))


if __name__=="__main__":
    make()
