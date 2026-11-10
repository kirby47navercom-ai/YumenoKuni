from pathlib import Path
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"qa_2026-10-29/trial_input_reedit.json"
prior=json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}
CHANGES=prior.get("changes",[])
ENTRIES=prior.get("entries",[])

def add(ch,kind,num,parent,start,end,title,dialogue,answer,wrong,wrong_reply):
    source=next(ROOT.glob(parent+"_*.md"))
    s=source.read_text(encoding="utf-8")
    before=hashlib.sha256(s.encode()).hexdigest()
    a=s.index(start);b=s.index(end,a+len(start))
    assert s.count(start)==1,(parent,start)
    removed=s[a:b]
    ident=f"T{ch}-{kind}-A{num:02d}"
    name=f"{180+ch}_{ch}장_재판_반복논의와_지목_연속대본.md"
    target=ROOT/name
    if not target.exists():
        target.write_text(f"# {ch}장 재판 — 반복 논의와 별도 지목\n\n> 제작자용 스포일러.2026-10-29 사용자 회차 정정.게임 적용 전 대본이에요.각 블록은 부모의 지정 발언을 대체하고 첫 정답 발언 직전으로 돌아가요.파일 전체를 첫 진입에 읽지 않아요.기존 결론을 설명한 다음 같은 문제를 다시 푸는 구성이 아니에요.재시도는 새 단서/자백/능력을 만들지 않아요.\n\n",encoding="utf-8")
    lines=[l for l in dialogue.strip().splitlines() if l]
    assert len(lines)>=3
    block=f"## {ident} {title} — {kind}\n\n진입: `{source.name}`의 `{start}`부터 기존 정답 앞까지를 대체해요.귀환 첫 발언: `{end}`.\n\n"
    if kind=="NS":
        block+="(다이나믹 논스톱 진입.아래 발언이 한 순환이에요.화자/문장 이동과 소음은 약점을 읽을 수 있게 배치해요.틀린 명제만 【】로,동의 대상은 〔〕로 구별해요.소음 제거/집중/반복 청취는 답을 자동으로 선택하지 않아요.)\n\n"
    block+="\n\n".join(lines)+"\n\n"
    block+=f"### 입력과 판정\n\n- 정답: {answer}\n- 구체적 오답: {wrong}\n- 다른 표적/다른 근거/취소 뒤 미확정은 성공으로 진행하지 않아요.\n\n### 오답 반응 → 같은 질문 재개\n\n{wrong_reply}\n\n(해설로 정답을 먼저 공개하지 않고 같은 논의/지목으로 돌아가요.시간·발언력 전체 실패는 재시도 뒤 이 블록 진입으로 돌아와요.오답 장면은 정상 경로 분량에 더하지 않아요.)\n\n### 정답 → 부모의 실제 대면\n\n(정답 컷인 뒤 위에 지정한 첫 귀환 발언부터 계속해요.이미 확인한 것 외의 사실을 새로 확정하지 않아요.최종 범인 지목과 표 확정은 별도예요.)\n\n"
    with target.open("a",encoding="utf-8") as h:h.write(block)
    link=f"> **필수 입력 {ident}:** [{title}]({name}#{ident.lower()}-{title.replace(' ','-')}--{kind.lower()}).방금 삭제한 선행 문답 대신 이 블록 한 번을 진행하고 아래 첫 발언으로 돌아와요.정답 설명을 먼저 읽지 않아요.\n\n"
    # Anchor uses the heading's actual CommonMark-compatible slug (Hangul and hyphens kept).
    s=s[:a]+link+s[b:]
    source.write_text(s,encoding="utf-8")
    CHANGES.append({"source":source.name,"before_sha256":before,"after_sha256":hashlib.sha256(s.encode()).hexdigest(),"id":ident,"removed_sha256":hashlib.sha256(removed.encode()).hexdigest(),"removed_text":removed})
    ENTRIES.append({"id":ident,"chapter":ch,"kind":kind,"file":name,"parent":source.name,"return_first":end,"answer":answer})
    save()

def save():
    q=ROOT/"qa_2026-10-29"
    (q/"trial_input_reedit.json").write_text(json.dumps({"scope":"manuscript only; explicit input and authored wrong reply; not runtime; no timing claim","entries":ENTRIES,"changes":CHANGES},ensure_ascii=False,indent=2),encoding="utf-8")


def select(ch,kind,num,parent,anchor,title,question,options,right,wrong_reply,correct_reply):
    source=next(ROOT.glob(parent+"_*.md"));s=source.read_text(encoding="utf-8")
    assert s.count(anchor)==1,(parent,anchor,s.count(anchor))
    ident=f"T{ch}-{kind}-A{num:02d}"
    name=f"{180+ch}_{ch}장_재판_반복논의와_지목_연속대본.md"
    target=ROOT/name
    body=f"## {ident} {title} — {kind}\n\n진입: `{source.name}`의 `{anchor}` 직전.정답 뒤 그 발언으로 돌아가요.\n\n[미오·속말] {question}\n\n"
    if kind in ("PERSON","CULPRIT"):
        body+="(인물 지목.16인 얼굴/이름을 선택하고 별도 확정해요.영정도 대상에서 자동 제외하지 않아요.단순 인물 지목/범인 지목은 최종 투표 화면과 다르고 지금 표를 집계하지 않아요.래피가 질문 대상인 별도 장면은 참가자16인 표에 억지로 추가하지 않아요.)\n\n"
    elif kind=="SPOT":
        body+="(그림 지점 지목.수사에서 본 아래 그림 한 장을 표시해요.선택 영역과 바깥/나머지를 구별해요.숫자 보기 선택으로 바꾸지 않아요.영역 이름은 제작용 마스크 ID이고 플레이 화면의 정답 표지가 아니에요.마스크 픽셀 좌표는 최종 원화와 맞출 때 확정해요.)\n\n"
    elif kind=="EVIDENCE":
        body+="(독립 언령 선택.보유 목록에서 카드와 설명을 열고 하나를 확정해요.논스톱에 탄환을 발사하는 입력과 구별해요.)\n\n"
    else:
        body+="(객관식 추리 질문.아래 보기 중 하나를 선택/확정해요.관계 취향을 고르는 대화 선택이 아니며 오답은 아래 반응 뒤 같은 질문으로 돌아가요.)\n\n"
    body+="- 질문: "+question+"\n- 후보/표시 그림: "+options+"\n- 정답 판정: "+right+"\n\n### 오답 — 다른 인물/카드/영역/보기\n\n"+wrong_reply+"\n\n(같은 문제로 돌아가요.미선택·영역0·취소를 정답으로 진행하지 않아요.전부 실패/시간 종료는 재시도 뒤 이 문제로,보존된 증거와 공개 상태 그대로 돌아와요.)\n\n### 정답 뒤\n\n"+correct_reply+"\n\n(지정한 부모의 첫 발언으로 돌아가요.새 단서/자백/득표/능력을 추가하지 않아요.)\n\n"
    with target.open("a",encoding="utf-8") as f:f.write(body)
    slug=f"{ident.lower()}-{title.replace(' ','-')}--{kind.lower()}"
    link=f"> **필수 입력 {ident}:** [{title}]({name}#{slug}).정답 뒤 아래 발언부터 이어가요.최종 투표는 별도예요.\n\n"
    a=s.index(anchor);new=s[:a]+link+s[a:]
    source.write_text(new,encoding="utf-8")
    CHANGES.append({"id":ident,"source":source.name,"before_sha256":hashlib.sha256(s.encode()).hexdigest(),"after_sha256":hashlib.sha256(new.encode()).hexdigest()})
    ENTRIES.append({"id":ident,"chapter":ch,"kind":kind,"file":name,"parent":source.name,"return_first":anchor,"answer":right})
    save()


def puzzle(ch,kind,num,parent,anchor,title,thought,content,wrong,reply):
    source=next(ROOT.glob(parent+"_*.md"));s=source.read_text(encoding="utf-8")
    if anchor.startswith("HEADING:"):
        label=anchor.split(":",1)[1]
        matches=re.findall(r"^#{2,3} "+re.escape(label)+r" [^\n]+",s,re.M)
        assert len(matches)==1,(parent,label,matches)
        anchor=matches[0]
    assert s.count(anchor)==1,(parent,anchor,s.count(anchor))
    ident=f"T{ch}-{kind}-A{num:02d}"
    name=f"{180+ch}_{ch}장_재판_반복논의와_지목_연속대본.md";target=ROOT/name
    block=f"## {ident} {title} — {kind}\n\n진입: `{source.name}`의 `{anchor}` 직전.아래 정답 뒤 그 지점부터 법정 대면을 이어가요.\n\n[미오·속말] {thought}\n\n"
    if kind=="MM":
        block+="(발굴 이매지네이션.수사 때 확인한 지정 그림을 색 블록으로 가려요.빨강/파랑/노랑/초록의 인접 동색군 제거→떨어지는 블록 재결합→그림의 실제 영역 지목을 진행해요.블록 제거는 현실 물건을 옮기거나 문을 여는 행위가 아니에요.지목 전 정답 이름/테두리를 표시하지 않아요.새 물건/글자/목격을 밑에 추가하지 않아요.)\n\n"
        question,image,regions,correct=content
        block+=f"- 가린 그림: {image}\n- 지목 질문: {question}\n- 노출되는 영역: {regions}\n- 정답 영역: {correct}\n"
        key=correct
    elif kind=="FA":
        question,word,distractors=content
        glyphs=list(word.replace(" ",""));pool=" / ".join(g+"·"+g for g in glyphs)
        block+="(섬광 애너그램Ver.3.0.동일 글자 구슬 두 개를 짝지어 순차 답안 칸에 넣어요.같은 글자가 두 번 필요한 답은 각 자리용 두 쌍을 별도로 내요.완성 전 배경에 완성 낱말을 써 두지 않아요.서로 다른 글자의 억지 조합/다른 순서/미적중과 특수 수집물 입력은 구별해요.)\n\n"
        block+=f"- 질문: {question}\n- 제작용 답안 순서: {' / '.join(glyphs)}\n- 필수 쌍 출현: {pool}\n- 혼동 구슬: {distractors} (같은 글자 쌍으로도 나오지만 이번 답안은 아니에요.)\n- 짝을 맞춰도 현재 답안 자리와 다르면 오답 피드백 뒤 그 자리로 돌아와요.\n"
        key=word
    else:
        block+="(브레인 드라이브 대체 추리 연결판.차/길/승객/주행 없음.관찰 카드→조건 카드→결론 카드를 실제 선택으로 연결해요.다음 질문을 열기 전 현재 연결을 판정하고,전체 사건 만화를 다시 맞추지 않아요.)\n\n"
        for i,(q,opts,right) in enumerate(content,1):
            block+=f"### 연결 {i}\n\n- 질문: {q}\n- 보기: {opts}\n- 정답: {right}\n- 틀리면 이 연결만 해제하고 같은 연결의 입력으로 돌아가요.이미 정답인 앞 연결은 보존해요.\n\n"
        key=[x[2] for x in content]
    block+="\n### 오답의 실제 반응\n\n"+wrong+"\n\n(같은 지목/답안 자리/틀린 연결로 돌아가요.오답 때 새 단서를 주지 않아요.시간·발언력 전체 실패는 재시도 뒤 이 과제의 초기 준비로,같은 단서와 공개 상태를 보존해 돌아와요.)\n\n### 정답 뒤 법정으로\n\n"+reply+"\n\n(지정한 부모 지점부터 이어가요.이 문제의 상세 설명은 귀환 뒤 처음 진행하고,끝난 게임을 다시 처음인 척 재생하지 않아요.)\n\n"
    with target.open("a",encoding="utf-8") as f:f.write(block)
    slug=f"{ident.lower()}-{title.replace(' ','-')}--{kind.lower()}"
    link=f"> **필수 입력 {ident}:** [{title}]({name}#{slug}).이 블록의 정답 뒤 아래 지점으로 돌아와요.\n\n"
    a=s.index(anchor);new=s[:a]+link+s[a:];source.write_text(new,encoding="utf-8")
    CHANGES.append({"id":ident,"source":source.name,"before_sha256":hashlib.sha256(s.encode()).hexdigest(),"after_sha256":hashlib.sha256(new.encode()).hexdigest()})
    ENTRIES.append({"id":ident,"chapter":ch,"kind":kind,"file":name,"parent":source.name,"return_first":anchor,"answer":key})
    save()
