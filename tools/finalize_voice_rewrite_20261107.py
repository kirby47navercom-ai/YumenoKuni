"""Close the reviewed voice-pass release without asserting full literary approval."""
import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'Game/Saved/voice-rewrite-20261107'
DOC=ROOT/'docs/analysis/voice_rewrite_20261107'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):
    temp=p.with_name(p.name+'.voice-final-tmp');temp.write_text(json.dumps(v,ensure_ascii=False,indent=1)+'\n',encoding='utf-8');os.replace(temp,p)
base=read(WORK/'base-build.json');build=read(WORK/'build-result.json')
assert read(ROOT/'Game/build-result.json')['id']==base['id']
assert read(WORK/'source-invariance.json')['ok']
assert read(WORK/'runtime-patch.json')['manualSources'].__len__()==738
parity=read(WORK/'package-parity.json');assert parity['ok']and parity['build']==build['id']
last=read(WORK/'packed-native-report-selected-3.json');assert last['ok']and last['base']==build['id']
first=read(WORK/'candidate-v1-native-report.json');free=read(WORK/'packed-native-report-selected-5.json')
inherit=read(WORK/'native-inheritance.json');assert inherit['to']==build['id']
unchanged={r['id']for r in inherit['proof']if r['unchanged']}
cases={r['id']:{**r,'testedBuild':first['base']}for r in first['cases']if r['ok']and r['id']in unchanged}
for report in [free,last]:
    for r in report['cases']:
        assert r['ok']and r['followedAuthoredNext']and r['padReturnedSamePage']
        assert r['id']in unchanged or report is last
        cases[r['id']]={**r,'testedBuild':report['base']}
assert len(cases)==6
pages=read(WORK/'page-audit.json');assert pages['ok']and pages['utterances']==36164
assert read(WORK/'compiler-after/manifest.json')['tasks']['typedReady']==220
save=ROOT/'Game/Saved/ui-checkpoints/normal-ch3-latest/savegames.json'
save_sha=hashlib.sha256(save.read_bytes()).hexdigest();assert save_sha=='d43c126c6df61cb9f96b312cb65fdcf9992605368617f23c572fc5c6e9850fe7'
closed=[]
for version in ['v1','v2']:
    old=read(WORK/f'candidate-{version}-build-result.json');src=Path(old['output']).resolve()
    dst=(ROOT/'삭제 대기/20261107-말투재집필-닫힌후보'/src.name).resolve()
    assert src.is_relative_to((ROOT/'Game/Builds/windows').resolve())and dst.is_relative_to((ROOT/'삭제 대기').resolve())
    assert src!=Path(build['output']).resolve()and src!=Path(base['output']).resolve()and not dst.exists()
    assert(src/'game.hbpack.json').is_file()
    files=[p for p in src.rglob('*')if p.is_file()];count=len(files);size=sum(p.stat().st_size for p in files)
    dst.parent.mkdir(parents=True,exist_ok=True);src.rename(dst)
    assert len([p for p in dst.rglob('*')if p.is_file()])==count
    closed.append({'from':str(src),'to':str(dst),'files':count,'logicalBytes':size})
write(WORK/'cleanup.json',{'moved':closed,'actualDeletions':0,'reclaimedSpaceClaim':False,'policy':'Owned closed voice candidates only; current and rollback build, source, report, screenshots, original saves retained.'})
report={'closedAt':datetime.now(timezone.utc).isoformat(),'base':base['id'],'build':build['id'],'phase':'published-first-voice-pass',
 'manualRewrittenRows':738,'spacingOnlyRows':7473,'sourceFilesChanged':244,'castCount':17,'allSourceRows':35073,
 'runtimeTextOccurrencesChanged':9314,'runtimeDataFilesChanged':161,'stableSourceParagraphIdsPreserved':52745,
 'runtimeRulesChoicesAnswersUIArtAudioAndNativeCodeUnchanged':True,
 'tests':{'sourceInvariance':'source-invariance.json','compilerCandidate':'compiler-after/manifest.json','packageParity':'package-parity.json','nativeInheritance':'native-inheritance.json','pageAudit':'page-audit.json','actualPackedCases':list(cases.values()),'actualPackedPages':sum(r['expectedPages']for r in cases.values()),'allSixFreshOnFinal':False,'finalPolishedCaseFresh':True},
 'editorGeneratedLayer':'editor-assets-layer.json','sourceOwnedPublisher':'Game/tools/v4-voice-revisions.mjs','sourceSaveSHA256':save_sha,
 'allDialogueLiteraryAcceptance':False,'wholeCampaignPlaythrough':False,'originalGameExecuted':False,'engineModified':False,'commit':False,'scheduled':False,
 'remaining':'This is the recorded 738-line contextual voice rewrite plus punctuation pass, across all cast and story phases. Whole-corpus line-by-line literary review of the remaining noncandidate dialogue is not complete. Do not report all 35,073 source utterances rewritten or the full game accepted.',
 'resume':'Use progress.json, applied-edits.json, batches01–18 and the source-addressed manual change table. Do not restart completed pagination/UI/738-line revisions.',
 'cleanup':'cleanup.json'}
write(WORK/'final-review.json',report)
progress=read(WORK/'progress.json');progress.update(phase=report['phase'],build=build['id'],fullLiteraryAcceptance=False);write(WORK/'progress.json',progress)
DOC.mkdir(parents=True,exist_ok=True)
text=f'''# 말투 재집필 1차 반영 결과

실행본: `{build['id']}`. 기준은 `{base['id']}`예요.

17명 전체와 일상·자유행동·수사·재판·오답/성공 반응을 대상으로, 앞뒤 문맥을 보고 **738개 발화**를 개별 재집필했어요. 반복되는 추상적 설명을 구체적인 요구·반박·감정으로 바꾸고, 레이의 격식, 린의 직설, 나나의 정중한 거절처럼 인물별 거리를 살렸어요. 별도로 문장부호 뒤 공백 **7,473곳**을 정리했어요. 공백을 재집필 수에 더하지 않아요.

원고 244파일의 8,211개 변경 발화가 원본에 반영됐고, 게임 압축 데이터 161파일의 실제 중복 포함 텍스트 9,314곳에도 연결됐어요. 개별 재집필 738개는 모두 현재 실행 데이터에서 연결을 확인했어요. 에디터의 현재 생성 데이터에도 같은 원본 소유 변환을 적용했고, 다른 대화의 생성/Source 변경을 덮어쓰지 않았어요.

사건·선택지·분기·지문·화자·대사 순서와 52,745개 원고 문단 식별자를 보존했어요. 추리용 강조/약점/동의 구절과 숫자도 보존했어요. 별도 잡음의 source는 원문 인용이 아닌 문맥 앵커이므로 그 말로 덮어쓰지 않았어요. 스크럼 각색문과 이미 나뉜 특수 발언도 같은 이유로 무조건 원문으로 교체하지 않았어요.

## 확인한 범위

- 원고 구조·식별자·대상 구절·숫자 검사 통과. 별도 저작 컴파일의 220입력 연결도 통과했어요. 기존 manifest의 campaignReady=false를 전편 합격으로 바꾸지 않았어요.
- 전체 배포 고유 발화 36,164개를 일상/재판 두 대화창으로 각각 계산해 74,083페이지의 바이트·폭·행 한도를 확인했어요. 미종결 경계 8개는 남은 긴 단문/절 후보이며 실제 플레이 발생 횟수나 문학 합격률이 아니에요.
- 실제 숨긴 네이티브 창에서 6개 수정 대화의 페이지·다음 대사·패드 왕복을 확인했어요. 그중 최종 다듬은 장면은 마지막 압축본에서 새로 검사했고, 나머지는 실제 검사한 노드 전체와 모듈 바이트가 동일하다는 근거로 계승했어요. 전6개를 마지막 압축본에서 새로 플레이했다고 세지 않아요.
- 원본 정상 저장 SHA와 기존 코드115파일, UI·그림·음향·비텍스트 판정은 보존했어요. 이 출하에는 다른 대화의 미발행 게임 변경을 통째로 넣지 않았어요.

## 남은 범위

이번 결과는 위 **738개 개별 재집필과 공백 교정의 1차 반영**이에요. 전체 35,073개 발화를 모두 문맥 단위로 다시 쓴 상태나, 전편을 실제 플레이한 상태는 아니에요. 남은 비후보 문장을 포함한 전량 문학 검수는 별도 미완료로 남겨요. 자연스러움의 최종 평가는 자동 검사나 수정 개수로 합격 처리하지 않아요.

원문/개정문 전부는 `개별_재집필_변경표_스포주의.md`, 재개점은 `Game/Saved/voice-rewrite-20261107/progress.json`이에요. 닫힌 자체 후보 두 빌드는 프로젝트 루트의 삭제 대기로 이동했으며 실제 삭제나 공간 회수는 하지 않았어요.
'''
(DOC/'재집필결과.md').write_text(text,encoding='utf-8')
write(ROOT/'Game/build-result.json',build)
marker=f'''<!-- VOICE_REWRITE_20261107 -->
최신 요청은 전체 말투 자연스러운 재집필이에요. **1차 반영본 {build['id']}**(기준c447b98d). 재개 `Game/Saved/voice-rewrite-20261107/final-review.json`·progress.json, 보고 `docs/analysis/voice_rewrite_20261107/재집필결과.md`와 스포주의 개별변경표. 17명/244원고파일, 문맥 개별재집필738·공백7473=8211발화, packed161JSON/9314중복포함텍스트반영·738전부연결. 52745문단ID/지문·화자·선택·분기·숫자·강조대상보존, weak offset만동반조정, 잡음앵커/특수각색/분할문장원문강제덮기없음. source-owned v4-voice-revisions·publisher·에디터생성데이터도같은층반영, 다른pending Source/Assets보존.
source검증/저작컴파일220입력/36164고유문구×2창74083페이지바이트·폭·행 PASS, 긴문장미종결8잔여(실플레이발생횟수아님). 실제숨김native6진입페이지/후속/Pad PASS; 최종다듬은장면최종압축fresh+나머지는해당노드와모듈전바이트동일근거계승. 전6개최종fresh·전편/FPS/사용자문학합격아님. 이전첫native5번실패는자유행동scope8노드를1장fixture로지정한검사오류,3장으로고쳐PASS; 저장원본SHA d43c126c…불변. Source115/기존UI·그림·음향·판정보존; 엔진/원작실행/예약/목표/커밋0. 닫힌own후보2개root삭제대기move,실제삭제/회수0.
**전량문학검수·35073발화전체재집필은미완료**. 2396휴리스틱후보중선별738집필을전체문장재집필이라고하지말아요. 다음은비후보대사까지장면맥락으로보는남은문학검수이며batches01–18/변경표에서이어가요. 기존UI·문장페이지수정·738개를처음부터반복하지말아요. 기존컴파일의stale guard/JSON식true문제는별도원인기록후정상화,source구조·이미지/UV보존근거로metadata hash만갱신; preexisting관람차→전망대저작차이는이번packed출하에섞지않았어요.
<!-- VOICE_REWRITE_20261107_END -->
'''
for name in ['HANDOFF.md','CODEX_HANDOFF.md','DEBUG_HANDOFF.md']:
    p=ROOT/name;old=p.read_text(encoding='utf-8-sig');assert '<!-- VOICE_REWRITE_20261107 -->'not in old;p.write_text(marker+'\n'+old,encoding='utf-8')
print(json.dumps({'published':build['id'],'manual':738,'actualUniquePackedCases':len(cases),'pages':sum(r['expectedPages']for r in cases.values()),'fullLiteraryAcceptance':False},ensure_ascii=False))
