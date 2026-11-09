"""Exact chapter-three body/identity labels without changing answer IDs."""


def bind_candidate_identity(graph,sources,tasks):
    if str(graph['chapter'])!='3':return
    d={s.prefix:s for s in sources.values()}
    for tid in ('T3-PERSON-A01','T3-PERSON-A02','T3-CULPRIT-A01','T3-VOTE-01'):
        t=tasks['tasks'][tid]
        if tid in ('T3-PERSON-A01','T3-PERSON-A02'):
            overrides={
                'ken':{'label':'켄의 몸','caption':'몸의 원래 주인: 켄 · 현재 조종자 미확인','identityScope':'physical-body-before-confirmation'},
                'sora':{'label':'소라의 본체','caption':'두 번째 사망 확인 · 영정','identityScope':'actual-dead-original-body'},
            }
            at=391 if tid=='T3-PERSON-A02' else 195
        else:
            # The answer is Sora's identity, not the original owner of the
            # body. Labelling ken as only Sora would make a truthful-looking
            # selection map to the authored wrong identity after confirmation.
            overrides={
                'ken':{'label':'켄(몸의 원래 주인)','caption':'현재 모습: 소라(켄의 몸)','identityScope':'original-owner-not-current-controller','physicalActor':'ken'},
                'sora':{'label':'소라(현재 켄의 몸)','caption':'소라 본체: 영정 · 조종자 정체로 지목','identityScope':'confirmed-current-controller','physicalActor':'ken'},
            }
            at=399
        t['candidateOverrides']=overrides
        t['candidateIdentitySource']={'source':d['13c2'].ref(at),'firstConfirmationResponse':d['13c2'].ref(399),'idsAndCorrectAnswerUnchanged':True,'noPrematureControllerDisclosure':True}
