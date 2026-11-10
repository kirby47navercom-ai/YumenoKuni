from pathlib import Path
import collections,hashlib,json,re,urllib.parse
ROOT=Path(__file__).resolve().parents[1]
Q=Path(__file__).resolve().parent
ledger=json.loads((Q/"trial_input_reedit.json").read_text(encoding="utf-8"))
es=ledger["entries"];by={e["id"]:e for e in es};errors=[]
def check(v,msg):
    if not v:errors.append(msg)
def slug(t):return re.sub(r"[^\w -]","",t.lower()).replace(" ","-")
check(len(es)==len(by),"unique active entries")
revision=ledger.get("purpose_revision",{})
retired=revision.get("retired",[])
old=json.loads(json.loads((Q/"before_trial_purpose_revision.json").read_text(encoding="utf-8"))["qa_2026-10-29/trial_input_reedit.json"])
old_ids={e["id"] for e in old["entries"]}
retired_ids={r["entry"]["id"] for r in retired}
added_ids=set(revision.get("new_ids",[]))
check(set(by)==(old_ids-retired_ids)|added_ids,"active inputs reconcile with preserved pre-edit source")
check(not retired_ids&set(by),"retired tasks cannot remain active")
for r in retired:
    parent=(ROOT/r["entry"]["parent"]).read_text(encoding="utf-8")
    check(r["replacement_dialogue"] in parent,r["entry"]["id"]+" replacement dialogue retained")
    check(r["reason"] and r["former_block"],r["entry"]["id"]+" reason and original text preserved")
    check(not re.search(r"^> \*\*필수 입력 "+re.escape(r["entry"]["id"])+r":",parent,re.M),r["entry"]["id"]+" inactive parent")
counts_new={}
source_text={}
for ch in range(1,7):
    got=dict(collections.Counter(e["kind"] for e in es if e["chapter"]==ch))
    counts_new[ch]=got
    check(any(e.get("judgment")=="agree" for e in es if e["chapter"]==ch),f"chapter {ch}: agreement")
for e in es:
    s=(ROOT/e["file"]).read_text(encoding="utf-8");parent=(ROOT/e["parent"]).read_text(encoding="utf-8")
    source_text[e["file"]]=s;source_text[e["parent"]]=parent
    definition=re.findall(r"^## "+re.escape(e["id"])+r" [^\n]+",s,re.M)
    check(len(definition)==1,e["id"]+" definition")
    if not definition:continue
    a=s.index(definition[0]);b=s.find("\n## ",a+5);block=s[a:b if b>=0 else len(s)]
    if e["kind"]=="FA":
        mword=re.search(r"^- 제작용 답안 순서: (.+)$",block,re.M)
        check(bool(mword) and re.sub(r"[ /]","",mword[1])==e["answer"].replace(" ",""),e["id"]+" ordered glyph answer")
    else:
        expected_answers=e["answer"] if isinstance(e["answer"],list) else [e["answer"]]
        check(all(x in block for x in expected_answers),e["id"]+" ledger answer equals manuscript")
    call=re.findall(r"> \*\*필수 입력 "+re.escape(e["id"])+r":\*\*[^\n]+",parent)
    check(len(call)==1,e["id"]+" parent call")
    check("### 오답" in block and "### 정답" in block,e["id"]+" correct/wrong text")
    check("**정답의 다음 진입:**" in block,e["id"]+" explicit next")
    if e["kind"]=="NS":
        check(e.get("vpoint_optional") is True,e["id"]+" optional V")
        check("선택·발사 언령 한 개:" in block,e["id"]+" one projectile")
        if e.get("judgment")=="agree":check("동의" in block and re.search(r"〔[^〕]+〕",block),e["id"]+" true target")
        else:check(bool(re.search(r"【[^】]+】",block)),e["id"]+" weak point")
    if e["kind"]=="PN":check("왼쪽" in block and "가운데" in block and "오른쪽" in block,e["id"]+" three lanes")
    if e["kind"]=="RS":check("발전" in block and "칼날" in block,e["id"]+" progress and blade")
    if e["kind"]=="MM":check("블록" in block and "정답 영역:" in block,e["id"]+" reveal/region")
    if e["kind"]=="FA":check("필수 쌍 출현:" in block and "제작용 답안 순서:" in block,e["id"]+" pairs/slots")
    if e["kind"]=="RL":check(len(re.findall(r"^### 연결 [123]$",block,re.M))==3,e["id"]+" three actual connections")
    check(not re.search(r"[ぁ-ヿ]",block),e["id"]+" Japanese kana")
    nxt=e.get("success_next")
    check(nxt is None or nxt in by,e["id"]+" next exists")
    if not nxt:
        lines=parent.splitlines();n=e.get("success_parent_line",0)
        check(0<n<=len(lines) and lines[n-1].startswith(e["return_first"]),e["id"]+" exact return line")
    seen=set();cur=e
    while cur.get("success_next"):
        if cur["id"] in seen:errors.append(e["id"]+" cycle");break
        seen.add(cur["id"]);cur=by[cur["success_next"]]
        check(cur["parent"]==e["parent"],e["id"]+" same parent")
# Existing first games bind to real current source markers, not just a count constant.
base=ledger.get("baseline_entries",[])
check(len(base)==66,"66 baseline games")
for row in base:
    check(row["marker"] in (ROOT/row["file"]).read_text(encoding="utf-8"),"baseline "+str(row))
counts_total={}
for ch in range(1,7):
    total=collections.Counter(e["kind"] for e in es if e["chapter"]==ch)
    total.update(row["kind"] for row in base if row["chapter"]==ch)
    counts_total[ch]=dict(total)
    check(all(total[k]>0 for k in ("NS","PN","RS","MM","FA","RL","SD","AA","CLIMAX","VOTE","PERSON","CULPRIT","EVIDENCE","ANSWER","SPOT")),"major modes and separate selections retained "+str(ch))
    # User clarification: distinct narrative reasons may justify repeated SD/AA/CLIMAX/VOTE.
    # Counts describe the manuscript; no per-chapter maximum proves scene quality.
# New dialogue never grants dead people new speaking turns.
alive={1:set("미오 레이 소라 켄 나나 리쿠 아카리 유우 코토 사츠키 타이가 린 쇼 아이 하루카 래피".split()),2:set("미오 레이 소라 켄 나나 리쿠 아카리 유우 코토 사츠키 린 쇼 하루카 래피".split()),3:set("미오 레이 소라 켄 나나 리쿠 아카리 코토 사츠키 린 쇼 하루카 래피".split()),4:set("미오 레이 나나 아카리 코토 사츠키 린 쇼 래피".split()),5:set("미오 나나 아카리 코토 사츠키 린 쇼 래피".split()),6:set("미오 나나 사츠키 린 쇼 래피".split())}
for ch in range(1,7):
    f=next(ROOT.glob(str(180+ch)+"_*.md"));s=f.read_text(encoding="utf-8")
    for name in re.findall(r"^\[([^]]+)\]",s,re.M):check(name.split("·")[0] in alive[ch],f"{f.name}: speaker {name}")
# Current all-document links; external files are checked without traversing into them.
links=0;anchors=0
for f in ROOT.glob("*.md"):
    s=f.read_text(encoding="utf-8");check("\ufffd" not in s,f.name+" UTF8 replacement")
    for raw in re.findall(r"\]\(([^)]+\.md(?:#[^)]*)?)\)",s):
        if "://" in raw:continue
        raw=urllib.parse.unquote(raw);path,_,anchor=raw.partition("#");t=(f.parent/path).resolve()
        check(t.exists(),f"missing link {f.name}: {raw}");links+=1
        if anchor and t.exists():
            heads=[slug(x) for x in re.findall(r"^#{1,6} (.+)$",t.read_text(encoding="utf-8"),re.M)]
            check(anchor in heads,f"missing anchor {f.name}: {raw}");anchors+=1
for name,h in ledger["final_sources"].items():check(hashlib.sha256((ROOT/name).read_text(encoding="utf-8").encode()).hexdigest()==h,"source SHA "+name)
result={"scope":"Authored manuscript inputs and return links; neither literary approval nor measured duration","new_entries":len(es),"retired_repetitive_inputs":len(retired),"new_disputes":sorted(added_ids),"chapters":6,"counts_per_chapter_new":counts_new,"counts_per_chapter_with_baseline":counts_total,"normal_tasks_per_trial_with_baseline":{ch:sum(c.values()) for ch,c in counts_total.items()},"normal_tasks_six_trials_with_baseline":sum(sum(c.values()) for c in counts_total.values()),"local_md_links":links,"anchors":anchors,"errors":errors,"runtime_playtest":False,"human_reading_test":False,"duration_goal_passed":False,"literary_quality_passed_by_count":False}
result["frequency_policy"]="No per-chapter upper bound, including scrum, armament, climax and vote. Narrative justification is reviewed in the actual manuscript, not proved by counts."
(Q/"trial_input_reedit_verification.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(result,ensure_ascii=False));raise SystemExit(bool(errors))
