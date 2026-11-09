"""Source-exact public procedural records, acquired on their actual event only.

This is a catalog of callbacks, not a starting inventory. It never scans all
dialogue for the word 'rule', registers trial distractors, or publishes private
ability/manuscript ledgers. Existing document-node capture remains independent.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REVIEWED_HASHES={
 '10_프롤로그_초고.md':'07c72705a081ed420b3444d1c8ce374657ac85a3a697c92a45a74880842d6a86',
 '11a2_1장_둘째날_초고.md':'762934c1125fba86aa28fa4faa5e2090536ae620c2b3ce6a473d11fc36526bb8',
 '11c1_1장_재판_전반_초고.md':'f390ca7c4f6c5d4579c23bbdf980be408cfdb2942635218d505ad413099e1115',
 '12a4_2장_읽어버린_말_초고.md':'9b19a07bdb9a869843fe3e17ea82f9300845a039bf04ac80b7ab886ce6c56475',
 '12c1_2장_재판_시작_초고.md':'d298af172597c751832482fbc1eca10e0b41b6d1987db1cd000c81342ec655a4',
 '13b1_3장_아직_살아있는_사람_초고.md':'ac8f9cd2ddd3908425f49e98b1e89f0e85df340cdfca2ed29e526e94e00e566d',
 '13c1_3장_재판_몸의_이름_초고.md':'36d842f455ba6d7130195c2abfcc498410b38d674136df9c2f8d414541f52a32',
 '14a4_4장_함께_있을_조건_초고.md':'981e913f8b73f7da4ebb2508a2f69cfcb1f871097e0f2a3063dd18a5afb8bfac',
 '14a7_4장_내가_먼저_말할게_초고.md':'ed45602afa5cfc0c72a8eb7eac84bcf4e7f230728da4113346c55d4f6561b524',
 '14c2_4장_재판_남겨_두고_싶은_것_초고.md':'036d77c3c961c028e73dc8620f5604696222a060c0b39967477df570596a9b6a',
 '15a_5장_일상_초고.md':'8ad308556d60430b05043d9b9f71e8d74865e44fb5f12e5b5b63cb9c7bbf8454',
 '16a2_6장_마지막_조건_초고.md':'43a345cb1268d6c4b943a2212fdfa0f370742d03bd69e2b7d45e120c9bffe4f4',
 '16c3_6장_재판_같은_이름을_고른_사람들_초고.md':'1a4f9a1478d6753add49d87c33e54bcaa9f5252321d237683c8f4dcec910d329',
}

# (key, source-file, trigger line, exact row lines, title, category, reveal)
# All rows precede/equal their trigger except the explicitly read condition
# list at16a2:31. Its five lines form the current public reading, not a reveal
# at a later narrative event. They must actually open once before continuing.
RULES=(
 ('P-graduation','10_프롤로그_초고.md',577,(571,577),'졸업과 발각','공통 안내',False),
 ('P-no-deadline','10_프롤로그_초고.md',601,(589,597,601),'생활과 기한','공통 안내',False),
 ('P-disclosure','10_프롤로그_초고.md',637,(637,),'수첩의 공개 범위','공통 안내',False),
 ('1-contact','11a2_1장_둘째날_초고.md',855,(833,839,843,847,851,855),'외부 연락 신청과 대표','연락 안내',False),
 ('1-contact-unused','11a2_1장_둘째날_초고.md',859,(859,),'미사용 신청의 보관','연락 안내',False),
 ('1-contact-reply','11a2_1장_둘째날_초고.md',866,(866,),'외부 응답의 보장 범위','연락 안내',False),
 ('1-trial-result','11c1_1장_재판_전반_초고.md',36,(36,),'학급 재판의 판정','재판 규칙',False),
 ('1-trial-abstention','11c1_1장_재판_전반_초고.md',44,(40,44),'표와 기권','재판 규칙',False),
 ('2-contact-status','12a4_2장_읽어버린_말_초고.md',116,(96,106,112,116),'신청인의 현재 상태','연락 안내',False),
 ('2-contact-new','12a4_2장_읽어버린_말_초고.md',122,(122,),'새 연락 신청','연락 안내',False),
 ('2-contact-window','12a4_2장_읽어버린_말_초고.md',144,(132,144),'현재 통신 창구','연락 안내',False),
 ('2-trial-reconfirmation','12c1_2장_재판_시작_초고.md',26,(26,),'두 번째 재판의 재확인','재판 규칙',False),
 ('3-controller','13b1_3장_아직_살아있는_사람_초고.md',163,(155,163),'조종과 살해의 판정 이름','재판 규칙',False),
 ('3-first-case','13c1_3장_재판_몸의_이름_초고.md',52,(52,),'이번 재판의 대상 사건','재판 규칙',False),
 ('3-deceased-culprit','13c1_3장_재판_몸의_이름_초고.md',56,(56,),'행위자의 사망과 판정','재판 규칙',False),
 ('4-created-participant','14a4_4장_함께_있을_조건_초고.md',325,(325,),'생성된 참가자의 살해 책임','재판 규칙',False),
 ('4-suppression-start','14a7_4장_내가_먼저_말할게_초고.md',241,(241,),'현 억제 규칙의 시작 시점','공개 질의',False),
 ('4-execution','14c2_4장_재판_남겨_두고_싶은_것_초고.md',337,(337,),'판정 뒤 집행 절차','재판 규칙',False),
 ('5-consent','15a_5장_일상_초고.md',47,(47,),'공개 질의 — 합의와 평범한 대답','공개 질의',False),
 ('5-terms','15a_5장_일상_초고.md',51,(51,),'공개 질의 — 개별 조건과 대가','공개 질의',False),
 ('5-refusal','15a_5장_일상_초고.md',75,(75,),'공개 질의 — 거부와 이미 한 합의','공개 질의',False),
 ('5-hearing','15a_5장_일상_초고.md',79,(79,),'설명을 듣는 것과 동의','공개 질의',False),
 ('6-target','16a2_6장_마지막_조건_초고.md',25,(19,25),'마지막 절차의 대상','마지막 조건',False),
 ('6-five-votes','16a2_6장_마지막_조건_초고.md',31,(33,34,35,36,37),'다섯 표의 조건','마지막 조건',True),
 ('6-separate-effects','16a2_6장_마지막_조건_초고.md',45,(45,),'게임 종료와 개별 효과','마지막 조건',False),
 ('6-erased-content','16a2_6장_마지막_조건_초고.md',51,(51,),'종료와 없어진 기억','마지막 조건',False),
 ('6-operator','16a2_6장_마지막_조건_초고.md',79,(79,),'운영자에게 남은 조건','마지막 조건',False),
 ('6-unchanged','16c3_6장_재판_같은_이름을_고른_사람들_초고.md',13,(11,13),'마지막 표결 전 재확인','마지막 조건',False),
 ('6-complete','16c3_6장_재판_같은_이름을_고른_사람들_초고.md',367,(367,),'현재 절차의 종료 표시','공개 상태',False),
)


def build_records(root=None):
    from build_v4_story import Source,clean,SAY
    workspace=Path(root) if root is not None else ROOT
    sources={name:Source(workspace/'docs/design/rewrite_v4'/name) for name in REVIEWED_HASHES}
    for name,source in sources.items():
        if source.hash!=REVIEWED_HASHES[name]:
            raise ValueError('Public record source changed; re-read its exact release boundary: '+name)
    records={};event_by_id={};ranges=[]
    for key,file,line,row_lines,title,category,reveal in RULES:
        source=sources[file];events=source.paragraphs(line,line)
        if len(events)!=1 or events[0]['type'] not in ('say','stage'):
            raise ValueError('Public record acquisition must be an exact executable say/stage: '+str((file,line)))
        event=events[0];rows=[];refs=[]
        for n in row_lines:
            raw=source.lines[n-1].strip();match=SAY.fullmatch(raw)
            if match:rows.append(clean(match[2]))
            elif raw.startswith('- '):rows.append(clean(raw[2:]))
            elif raw.startswith('(') and raw.endswith(')'):rows.append(raw[1:-1])
            else:raise ValueError('Unreviewed record row format: '+str((file,n)))
            refs.append(source.ref(n))
        ident='v4:public-record:'+key
        records[ident]={'id':ident,'title':title,'rows':rows,'category':category,'private':False,
                        'sourceRefs':refs,'acquireEventId':event['id'],'showOnAcquire':reveal,
                        'acquisition':'only-after-exact-event-commit','classification':'publicly-heard-clarification' if category=='공개 질의' else 'public-procedure',
                        'grantsEvidence':False,'grantsAbility':False,'changesStoryFlags':False}
        event_by_id.setdefault(event['id'],[]).append(ident)
        ranges.append({'file':file,'firstLine':line,'lastLine':line,'location':event['source']['location'],
                       'fileSha256':source.hash,'eventId':event['id'],'eventType':event['type'],'recordIds':[ident],
                       'exactEventOnly':True})
    return {'schemaVersion':1,'contentVersion':'v4','eventById':event_by_id,'sourceRanges':ranges,'records':records,
            'reviewedSourceHashes':dict(REVIEWED_HASHES),'startingInventory':[],
            'existingDocumentCapturePreserved':['v4:10:P-06-READ:document','v4:10:P-06a:document'],
            'policy':'Catalog entries are not acquired at startup. Resolve only the actually committed event; never preload future rows, all branch variants, private ability pages or legacy nineteen school rules.',
            'runtimeVerified':False}
