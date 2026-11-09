"""Reviewed chapter-five source routes. Never combine another branch or time."""
from pathlib import Path
import json

REVIEWED_SOURCE_HASHES = {
    "15a": "8ad308556d60430b05043d9b9f71e8d74865e44fb5f12e5b5b63cb9c7bbf8454",
    "15a2": "934ca5451ac4be5dc3f96a46fc2d4bb77eec43073ce2c32c14e532fdd408a857",
    "15a3": "ab26f8351d0ffabc1dd26f6126335e835a8ded7ca39579616d8ea79f84b93bd7",
    "121": "dbe6b7a3e00ef0c16a7b3ae8417a6fba98911799c17d3fa14ba97401db81701a",
    "133": "f5b59d982b7b7fb82e35fe4a6145ae1b4b90fa5f51cc7d4ef2e16bccdf86f6e2",
    "15a4": "a52f0ef8e1aebea1dcc57d47d09fadd2550a4292b8a21d5752aead851686a521",
    "95": "0c372c73b5fa7bf64837a3de86b52e2871e8d66d479c031564609b905c6d5d6d",
    "15a5": "30c676374b431a3d99ea26c9fa12f4662712017f1ef96956e05954a41c731245",
    "103": "c56ab73b4d3675d5e2cbfce3de4328bea6775452e62b3a604c80514d310af284",
    "15a6": "66249841dc50013997cea875e820bbe9475213607623394aaf5ca84765063b03",
    "127": "cfadeb6b34c15e09e73e513e03093950a0f03d9b7dc93e80936d371900593e8e",
    "72": "8463133adb5f513f660f7e24f1d40b523b1f8ad3ed9cbd7778139f785a2c92d2",
    "15a7": "31929abe1dc32d6c30a0ddaf08145c1855ffa9ad5a019289dbca43d4f545e1aa",
    "15a8": "526650835e3117daa4bbd22dddc867766ace35c14fc3de8af582980a49062ab2",
    "15a9": "9a4aa5eed40b873397ac2aa8bf0bbe6724acceddd8fd6d9c7fc287e0801ee866",
    "175": "3117aa1dbd7335f2c55a92a5f7600b92d89cdabc876b3c3eaa67dc04a67ddf44",
    "15a10": "9d315c3530e29b633e65ae474d503c36fcafb4d8af28295e1d98bb209abe69a5",
    "15a11": "0e536eefef75f4ae567814fc48e81f43d29ff6a69e15f99d624536b57956ddfb",
    "15b1": "c2860b29664e1322c5ac7feb9fd8b2fc1b7b98faf70325e72d2450e48a736efe",
    "15b2": "a827fd9f8d2fe2165f5859544b97ffa959fa889eee191faf1075f4c43728c4a7",
    "15b3": "03272fe532a1cad06636a76edabedc30269fd73dca7ae5562000ea12c283c46b",
    "15d": "8f564cba5a6ddd6a2a01fae3649107a63f82cdaf8f16fd2169d26c4a7f422d4a",
    "100": "e5f99c08c355ccb6062b30604605ff10855c6bea87331044e1412ec8928466db",
    "169": "954fbe7b6d6f59c6f2dedd9c564654f08a20f15f378fdc284c27ec66d7428964"
}


def route_source_hashes(sources):
    result={}
    for prefix,expected in REVIEWED_SOURCE_HASHES.items():
        source=next(s for s in sources.values() if s.prefix==prefix)
        if source.hash!=expected:raise ValueError('Chapter five source changed; re-read actual scope: '+source.name)
        result[source.name]=expected
    return result


class Router:
    def __init__(self,g,sources):
        self.g=g;self.docs={s.prefix:s for s in sources.values()};self.spans=[];self.cache={}
    def seq(self,p,a,b,to):
        source=self.docs[p];b=len(source.lines) if b is None else b
        key=(p,a,b,to)
        if key in self.cache:return self.cache[key]
        self.spans.append({'file':source.name,'first':a,'last':b,'sha256':source.hash})
        entry=self.g.sequence(source,a,b,to);self.cache[key]=entry
        return entry
    def gate(self,key,reason,p,line):
        return self.g.add('v4:5:'+key,{'type':'gate','reason':reason,'source':self.docs[p].ref(line)})
    def menu(self,flag,p,line,rows,to):
        options=[]
        for key,label,a,b in rows:options.append({'id':key,'label':label,'to':self.seq(p,a,b,to),'set':{flag:key}})
        return self.g.add('v4:5:menu:'+flag,{'type':'menu','q':self.docs[p].lines[line-1].lstrip('# ').strip(),'source':self.docs[p].ref(line),'options':options})
    def remember(self,key,flag,rows,to,default=None):
        if default is None:default=self.gate(key+':missing','Required earlier choice is absent; no unseen memory is manufactured.',rows[0][1],rows[0][2])
        return self.g.add('v4:5:'+key,{'type':'branch','cases':[{'flag':flag,'equals':value,'to':self.seq(p,a,b,to)} for value,p,a,b in rows],'default':default})
    def document(self,key,title,p,a,b,to,private=False):
        source=self.docs[p]
        rows=[line.removeprefix('- ').removeprefix('> ').strip() for line in source.lines[a-1:b] if line.strip() not in ('','>')]
        return self.g.add('v4:5:document:'+key,{'type':'document','title':title,'rows':rows,'private':private,'source':source.ref(a),'next':to,'authoredSourceOnly':True})


def compile_chapter_five(sources,freetime_graphs,tasks):
    from build_v4_story import Graph
    from v4_story_case5_trial import compile_trial_five,route_source_hashes as trial_source_hashes
    route_source_hashes(sources)
    g=Graph('5');g.taskDefinitions=tasks['tasks'];r=Router(g,sources)
    result=_result(r)
    pending=r.gate('evening-pending','The first reviewed living day is routed. Later living days, actual investigation and trial still need explicit source contracts.','15a4',5)
    noon=r.gate('noon-pending','The actual afternoon disclosure and subsequent investigation/trial are still being routed.','15a6',5)
    trial=r.gate('trial-pending','The actual living days and investigation are routed. The source-addressed trial helper is being connected.','15c1',5)
    trial_entry=compile_trial_five(g,sources,tasks,result)
    g.nodes[trial]={'id':trial,'type':'stage','direction':'확보한 자료를 가지고 재판장으로 들어간다.','source':r.docs['15c1'].ref(5),'next':trial_entry,'pendingResultEntry':result}
    investigation,catalogue=_investigation(r,trial)
    discovery=_discovery(r,investigation)
    tea=_tea_preparation(r,discovery)
    after_claim=_false_claim_afternoon(r,tea)
    conflict=_afternoon_conflict(r,after_claim)
    after_noon=_early_afternoon(r,conflict)
    noon_entry=_noon_disclosure(r,after_noon)
    g.nodes[noon]={'id':noon,'type':'stage','direction':'약속한 정오에 본인의 말과 실제 문서를 확인한다.','next':noon_entry}
    morning=_day_seventeen_morning(r,noon)
    evening=_day_sixteen_evening(r,morning)
    g.nodes[pending]={'id':pending,'type':'stage','direction':'그날 저녁의 실제 작업과 식사로 이어진다.','next':evening}
    after_private=r.seq('15a3',154,335,pending)
    agreement=r.document('new-oath','지금 합의할 문구','15a3',149,152,after_private,private=True)
    late_private=r.seq('15a3',79,148,agreement)
    confrontation=r.seq('133',5,359,late_private)
    afternoon=r.seq('15a3',5,76,confrontation)
    lunch_tail=r.seq('15a2',545,616,afternoon)
    seat_echo=r.remember('C01:afternoon-seat','5-C01',[('A','15a2',529,533),('B','15a2',529,533),('C','15a2',537,541)],lunch_tail)
    lunch_common=r.seq('15a2',399,526,seat_echo)
    lunch_echo=r.remember('C01:lunch','5-C01',[('A','15a2',353,365),('B','15a2',369,381),('C','15a2',385,395)],lunch_common)
    worked=r.seq('15a2',75,350,lunch_echo)
    breakfast_choice=r.menu('5-C01','15a2',37,[('A','자신의 두려움을 나나의 의도처럼 물었다고 인정한다',45,49),('B','지금은 편하게 대답할 수 없다고 말하고 거리를 둔다',53,57),('C','나나의 옛 약속 때문에 더 의심스럽다고 말한다',61,71)],worked)
    day_start=r.seq('15a2',5,36,breakfast_choice)
    morning_end=r.seq('15a',399,420,day_start)
    marked_lists=r.seq('121',5,251,morning_end)
    entry=r.seq('15a',5,396,marked_lists)
    for node in g.nodes.values():
        source=node.get('source',{})
        if source.get('file')==r.docs['15a2'].name and 77<=source.get('line',0)<=218:
            node['observedBy']=['rin','sho'];node['notMioObservation']=True
        if source.get('file') in (r.docs['15a3'].name,r.docs['133'].name) and (source.get('file')!=r.docs['15a3'].name or source.get('line',0)<314):
            node['pov']='akari';node['notMioObservation']=True
        if source.get('file')==r.docs['15a7'].name and 67<=source.get('line',0)<107 and node.get('actor')=='rin':
            node['appearanceActor']='nana';node['physicalActor']='rin';node['voiceActor']='rin'
        if source.get('file')==r.docs['15a11'].name and source.get('line')==185:
            node.setdefault('set',{})['v4:death:koto:public']=True
        if source.get('file')==r.docs['15d'].name and source.get('line')==67:
            node.setdefault('set',{})['v4:death:akari:public']=True
        if source.get('file')==r.docs['15a9'].name and source.get('line',0)<=89:
            node['pov']='nana';node['notMioObservation']=True
        if source.get('file')==r.docs['15a10'].name and 63<=source.get('line',0)<=141:
            node['pov']='akari';node['notMioObservation']=True
    return g.export(entry,routingStatus='reviewed-full-mandatory-route-with-explicit-input-bindings',contentScope='All living-day choices and exact callbacks, actual disclosure/death, 58 source-ordered investigation sections and20 acquisition/revision records,39 actual trial input boundaries with three separated scrum rounds, exclusive honest/intentional lie agreement, final vote and18 result sections to chapter6. Unbound art/rhythm stays gated.',evidenceCatalog=catalogue,sourceSpans=r.spans+g.trialFiveRanges,reviewedSourceHashes={**route_source_hashes(sources),**trial_source_hashes(sources)},canonicalGuard=g.trialFiveGuards,campaignReady=False,chapterComplete=False)


def _day_sixteen_evening(r,to):
    tail=r.seq('15a4',569,988,to)
    dinner=r.menu('5-C02','15a4',275,[('A','여분의 잔을 치우고 린 옆에 앉는다',283,387),('B','잔을 그대로 두고 그 앞에 앉는다',391,485),('C','식사 전에 밖으로 나간다',489,565)],tail)
    private=r.seq('15a4',63,274,dinner)
    letter_tail=r.seq('95',187,243,private)
    seen=r.seq('95',175,179,letter_tail);unseen=r.seq('95',183,183,letter_tail)
    reminder=r.g.add('v4:5:SHO03:letter-reminder',{'type':'branch','cases':[{'flag':'fte:56:complete','equals':True,'to':seen}],'default':unseen})
    letter=r.seq('95',97,172,reminder)
    first_seen=r.seq('95',91,95,letter)
    prior=r.g.add('v4:5:SHO03:prior-letter',{'type':'branch','cases':[{'flag':'fte:56:complete','equals':True,'to':first_seen}],'default':letter})
    revision=r.seq('95',5,88,prior)
    return r.seq('15a4',5,60,revision)


def _day_seventeen_morning(r,to):
    mother=r.seq('15a5',519,590,to)
    after=r.seq('103',187,192,mother)
    notation=r.remember('C07:private-note','5-C07',[('A','103',177,177),('B','103',181,181),('C','103',185,185)],after)
    note_start=r.seq('103',171,174,notation)
    classification=r.remember('C07:classification','5-C07',[('A','103',159,161),('B','103',159,161),('C','103',165,167)],note_start)
    bargain=r.menu('5-C07','103',93,[('A','다른 사람에게 전하기 전에 코토에게 먼저 묻겠다고 한다',97,111),('B','목록을 먼저 공개하고 정오에 직접 말하라고 요구한다',115,131),('C','도움을 받지 않고 자기가 찾으러 간다',135,151)],classification)
    introduction=r.seq('103',5,92,bargain)
    public_notice=r.seq('15a5',363,516,introduction)
    ask=r.menu('5-C03','15a5',319,[('A','나나에게 언제 다시 물을지 묻고 쇼와 간다',327,331),('B','자기 이름이 적힌 부분을 지금 보여 달라고 계속 요구한다',335,345),('C','자료는 기다리되 코토가 남는 것이 괜찮은지 나나에게 묻는다',349,359)],public_notice)
    return r.seq('15a5',5,318,ask)


def _noon_disclosure(r,to):
    after_choice=r.seq('72',155,169,to)
    hand=r.menu('5-C06','72',89,[('A','손을 거두고 시험하려던 마음을 말한다',93,111),('B','손을 거두되 자신의 의도는 말하지 않는다',115,129),('C','시험하려 했다는 것을 말하면서 다시 잘못을 묻는다',133,153)],after_choice)
    confrontation=r.seq('72',5,88,hand)
    lunch=r.seq('15a6',262,455,confrontation)
    earlier=r.remember('C10:noon','4-C10',[('A','127',149,163),('B','127',167,179),('C','127',183,185)],lunch)
    refusal=r.seq('15a6',188,259,earlier)
    transaction=r.remember('C07:noon','5-C07',[('A','103',201,219),('B','103',223,235),('C','103',239,249)],refusal)
    contract_after=r.seq('15a6',126,185,transaction)
    contract=r.document('old-oath','그날 확인한 맹세의 조건','15a6',121,124,contract_after)
    return r.seq('15a6',5,120,contract)


def _early_afternoon(r,to):
    tail=r.seq('15a7',401,484,to)
    corrected=r.seq('15a7',375,399,tail)
    correction=r.g.add('v4:5:RIN03:actual-correction',{'type':'branch','cases':[{'flag':'v4:5:rin03:correction-needed','equals':True,'to':corrected}],'default':tail})
    before_correction=r.seq('15a7',251,370,correction)
    common=r.seq('15a7',249,250,before_correction)
    memory=r.remember('RIN03:current','RIN-03A',[('A1','15a7',203,215),('A2','15a7',219,229),('A3','15a7',233,245)],common)
    # Only the earlier actual A1 memory creates the current correction promise.
    a1=r.g.nodes[memory]['cases'][0]['to'];r.g.nodes[a1].setdefault('set',{})['v4:5:rin03:correction-needed']=True
    optional=r.g.add('v4:5:RIN03:seen',{'type':'branch','cases':[{'flag':'fte:54:complete','equals':True,'to':memory}],'default':before_correction})
    after_hands=r.seq('15a7',169,196,optional)
    hand_echo=r.remember('C06:afternoon','5-C06',[('A','15a7',139,145),('B','15a7',149,153),('C','15a7',157,165)],after_hands)
    return r.seq('15a7',5,134,hand_echo)


def _afternoon_conflict(r,to):
    tail=r.seq('15a8',329,396,to)
    echo=r.remember('C04:after-push','5-C04',[('A','15a8',295,301),('B','15a8',305,315),('C','15a8',319,325)],tail)
    arrival=r.seq('15a8',191,290,echo)
    witnessed=r.seq('15a8',173,189,arrival)
    saw=r.g.add('v4:5:C04:actual-push-witness',{'type':'branch','cases':[{'flag':'5-C04','equals':'A','to':arrival},{'flag':'5-C04','equals':'B','to':witnessed},{'flag':'5-C04','equals':'C','to':witnessed}],'default':r.gate('C04:absent','The actual earlier response is required.','15a8',85)})
    choice=r.menu('5-C04','15a8',85,[('A','아카리를 부르러 나간다',93,99),('B','먼저 어머니 작업물의 위치 항목을 옮긴다',103,137),('C','사츠키 옆에서 함께 원본 분류 공개를 요구한다',141,171)],saw)
    return r.seq('15a8',5,84,choice)


def _false_claim_afternoon(r,to):
    tail=r.seq('15a9',477,662,to)
    six=r.seq('175',5,len(r.docs['175'].lines),tail)
    claim=r.seq('15a9',371,474,six)
    game=r.seq('15a9',149,369,claim)
    answer=r.remember('C04:courtyard-response','5-C04',[('A','15a9',121,125),('B','15a9',129,135),('C','15a9',139,145)],game)
    waiting=r.seq('15a9',113,115,answer)
    address=r.remember('C04:courtyard-call','5-C04',[('A','15a9',103,103),('B','15a9',107,107),('C','15a9',111,111)],waiting)
    return r.seq('15a9',5,100,address)


def _tea_preparation(r,to):
    tail=r.seq('15a10',199,320,to)
    choice=r.menu('5-C05','15a10',159,[('A','그가 없었으면 좋겠다고 답한다',165,174),('B','지금은 마주치고 싶지 않다고 답한다',175,184),('C','그런 대답을 자신에게서 받으려 하지 말라고 한다',185,196)],tail)
    return r.seq('15a10',5,158,choice)


def _discovery(r,to):
    tail=r.seq('15a11',313,334,to)
    echo=r.remember('C05:actual-discovery','5-C05',[('A','15a11',301,301),('B','15a11',305,305),('C','15a11',309,309)],tail)
    return r.seq('15a11',5,296,echo)


CARD_TEXT={
    '01':('중독 사인 파일','코토의 사인은 R-7 중독이에요.팔꿈치 외상은 사인이 아니고 자료가 투입자나 정확한 투입 시각을 지정하지는 않아요.'),
    '02':('개인 잔과 공용 차 대조','코토의 잔에 R-7이 확인됐고 공용 물·찻잎·포트의 차·남은 다른 새 잔에서는 확인되지 않았어요.이 비교만으로 투입자나 시각을 정하지 않아요.'),
    '03':('아카리와 코토의 최근 서류 맹세','코토의 전문 선공개 제한과 아카리의 원본 훼손 금지,손목 통증이 있어요.17일21시 또는 아카리가 다른 생존자 한 명에게 세번째 진술 전문을 직접 보여주는 것이 종료 조건이에요.사망 자체나 상호 비가해 조건은 없어요.'),
    '04':('실제로 읽은 세 번째 진술 전문','아카리가 사츠키에게 세 번째 진술 전체와 최근 서명을 직접 보여줬어요.기존 진술에 정정할 사항이 없다는 확인이며 아카리는 제대로 다시 읽지 않았다고 말했어요.'),
    '05':('보호 페이지와 보통 메모','앞선 음용과 어지럽다는 호소는 두 종이에 남고 현재 기억에도 있어요.사츠키/빈잔 표기만 보호 페이지에 있고 보통 메모 회수 칸은 비어 있어요.현재 사츠키가 회수한 목격으로 바꾸지 않아요.'),
    '06':('아카리의 사용 시각 인정','14시 이미 썼다는 말은 사실이 아니었다고 아카리가 인정했어요.두 종이가 달라진16시52분 부근의 사용은 인정했지만 진짜 목적까지 자백한 자료는 아니에요.'),
    '07':('세 열쇠와 동반 출입','린·쇼·나나가 각각 열쇠를 소지한다고 진술했어요.아카리는14시 나나와 들어갔어요.현재 잠금만으로 앞선 정상 출입을 배제하지 않아요.'),
    '08':('최초 공동 봉함 확인','나나와 아카리는14시 처음 여섯 용기의 표지와 개별 봉함을 확인했어요.나나는 문밖 표찰을 본 뒤 다시 세지 않았고 앞선 손을 계속 본 것도 아니에요.'),
    '09':('현재 R-7 D칸의 결손','현재 R-7 상자에 다섯 용기가 남고 D칸이 비어 있어요.처음 계수와 마지막 뚜껑 확인을 같은 지속 감시로 합치지 않아요.'),
    '10':('D칸에서 확보한 포장 조각','D칸 가장자리의 이미 찢긴 식별 종이를 위치와 세 사람 이름을 기록한 봉투에 확보했어요.다른 다섯 칸의 포장은 건드리지 않았어요.'),
    '11':('문밖 표찰과 안쪽 시야','나나가 목록을 확인한 문밖 자리에서는 D칸이 보이지 않아요.읽는 소리와 안쪽 손동작 목격은 달라요.정확한 공백 초수는 재지 않았어요.'),
    '12':('망각의 물리 문서 경계','래피는 망각이 사람의 기억에 작용하며 종이·잉크를 되돌리거나 문서를 바꾸지 않는다고 확인했어요.나나의 실제 사용 이력을 측정한 자료는 아니에요.'),
    '13':('운영동 실제 작업 동행','린·쇼는 함께 작업했고 나나가 호텔에서 돌아온 뒤 세 사람이 표찰·도면을 맞췄다는 진술이에요.모방은 몸이나 독립 소지품을 복제하지 않아요.모든 손을 계속 보았다는 뜻은 아니에요.'),
    '14':('사후 회수된 D용기','사츠키가 내놓은 용기는 R-7 D이고 봉함이 풀려 있어요.현재 소지가 사망 전 투입을 증명하지 않아요.남은 물질의 일치는 별도 비교 뒤 갱신해요.'),
    '15':('쇼가 본 사후 가방 인계','쇼는 미오 일행이 떠난 뒤 사츠키가 아카리 가방에서 작은 물건을 꺼내 주머니에 넣는 순서를 봤어요.그때 D 글자나 앞선 넣는 동작까지 본 것은 아니에요.'),
    '16':('가방 안감과 맞물린 포장','가방 안감 조각은 D칸 조각과 인쇄·가장자리가 이어지고 식용 금지 문구가 있어요.미오는 준비대에서 같은 모양 포장을 풀어 가방에 넣는 손을 봤지만 당시 문구는 못 읽었어요.'),
    '17':('마개 봉함띠와 실제 개봉 손','안감의 좁은 띠와 D마개의 인쇄·찢긴 끝이 이어져요.몸체의 다른 파손·재접착 흔적은 없어요.미오는 나나가 떠난 뒤 마개와 몸체 사이 띠를 끊는 손을 봤어요.'),
    '18':('기록 보존과 물건 되감기','되감기는 물리 행동을 이전 상태로 돌리고 아카리의 기억·사용횟수와 보호 손글씨는 남아요.보호 글만으로 현재 살해행위가 생기지 않고10초 전보다 앞의 음용까지 없애지는 않아요.'),
    '19':('창가의 공동 관찰과 그림자 조건','마지막 준비와 직접 인계 동안 사츠키 본체는 미오와 햇빛 속 창가에서 다트판을 정리했어요.빛 안의 본체가 유지할 수 없는 그림자로 빈 동선을 채우지 않아요.'),
    '20':('아카리의 잔 선택과 앞선 음용','아카리가 코토에게 직접 잔을 건넸고 미오는 음용과 뒤의 어지럼 호소를 기억해요.준비대 뒤 모든 손은 보지 못했어요.잔 선택·동선은 후속 질문에서 따로 확인해요.'),
}


def _investigation(r,to):
    cat={}
    def grant(code,p,line,target,revision=False,text=None):
        cid='v4:E5-'+code;name,desc=CARD_TEXT[code]
        cat.setdefault(cid,{'id':cid,'name':name,'text':desc,'source':r.docs[p].ref(line),'grantPolicy':'actual-scope-only'})
        return r.g.add('v4:5:grant:'+code+':'+p+':'+str(line),{'type':'evidence','evidenceId':cid,'name':name,'text':text or desc,'revision':revision,'source':r.docs[p].ref(line),'next':target})
    def scope(key,label,p,a,b,to,cards=(),custom=None,space='hotel_lobby'):
        ident='v4:5:investigate:'+key;ret=r.g.add(ident+':return',{'type':'return'});end=ret
        for code,revision in reversed(cards):end=grant(code,p,b,end,revision)
        entry=custom(end) if custom else r.seq(p,a,b,end)
        sid=ident+':spot';flag=sid+':complete'
        return r.g.add(ident,{'type':'investigate','title':label,'source':r.docs[p].ref(a),'spots':[{'id':sid,'label':label,'space_id':space,'target_id':None,'geometryReady':False,'interactionPolicy':'source-backed-text-inspection-awaiting-authored-world-placement','entry':entry,'returnTo':ident,'completionFlag':flag,'onReturnSet':{flag:True},'required':True}],'requiredSpotIds':[sid],'requiredCards':['v4:E5-'+c for c,_ in cards],'next':to,'orderPolicy':'Explicit ordered source dependencies, not an arbitrary-order investigation claim.'})
    leaving=r.seq('15b3',473,484,to)
    bundled=scope('I57','재판에 가지고 갈 실제 자료','15b3',467,472,leaving)
    separate=scope('I56','별개로 남는 옛 맹세와 폭력','15b3',455,466,bundled)
    def share(end):
        short=r.remember('I-C01:common-day','5-C04',[('A','15b3',425,428),('B','15b3',431,436),('C','15b3',439,442)],end)
        after_a=r.seq('15b3',402,408,short);after_b=r.seq('15b3',410,416,short);after_c=r.seq('15b3',445,452,end)
        ctail=r.seq('15b3',393,396,after_c)
        cday=r.remember('I-C01:C-day','5-C04',[('A','15b3',347,356),('B','15b3',359,372),('C','15b3',375,390)],ctail)
        c=r.seq('15b3',343,344,cday)
        menu=r.g.add('v4:5:menu:I5-C01',{'type':'menu','q':'먼저 공유할 것','source':r.docs['15b3'].ref(237),'options':[{'id':'A','label':'실제 되감기와 두 종이를 먼저 정리한다','to':r.seq('15b3',243,292,after_a),'set':{'I5-C01':'A'}},{'id':'B','label':'D와 포장 조각의 이동부터 정리한다','to':r.seq('15b3',293,340,after_b),'set':{'I5-C01':'B'}},{'id':'C','label':'자신의 낮 선택부터 먼저 말한다','to':c,'set':{'I5-C01':'C'}}]})
        return menu
    current=scope('I55','지금 공유하는 순서와 실제 낮 선택','15b3',235,454,separate,custom=share)
    groups=[
        ('I39-41','두 종이와 기억의 실제 경계','15b3',5,44,(('05',True),),None),
        ('I42-44','사용했다고 말한 시간과 실제 인정','15b3',45,96,(('06',False),),None),
        ('I45-46','되감기 뒤 물건과 기록의 조건','15b3',97,126,(('18',False),),None),
        ('I47-49','음용보다 뒤의 회수 자백','15b3',127,168,(('20',True),),None),
        ('I50','직접 골랐던 마지막 준비대','15b3',169,188,(('20',True),),None),
        ('I51','햇빛 드는 창가의 실제 몸','15b3',189,198,(('19',False),),None),
        ('I52','독립된 운영동 작업 동행','15b3',199,210,(('13',True),),None),
        ('I53-54','코토의 손과 미오가 쓴 범위','15b3',211,234,(('20',True),),None),
    ]
    for key,label,p,a,b,cards,custom in reversed(groups):current=scope(key,label,p,a,b,current,cards,custom)
    groups2=[
        ('I19-20','현재 잠금과 D칸의 결손','15b2',5,26,(('09',False),),None),
        ('I21','D칸에서 확보하는 실제 포장 조각','15b2',27,38,(('10',False),),None),
        ('I22-23','문밖 목록과 안쪽의 보이지 않는 손','15b2',39,66,(('11',False),),None),
        ('I24-25','기억과 물리 종이를 나누는 질문','15b2',67,94,(('12',False),),None),
        ('I26-28','작업 동행과 남는 세 열쇠','15b2',95,136,(('13',False),('07',True)),'central_control'),
        ('I29-30','호텔 부재 중의 가방 이동 진술','15b2',137,162,(('15',False),),'hotel_lobby'),
        ('I31-34','지금 내놓은 D와 사후 인계','15b2',163,272,(('14',False),('15',True)),'hotel_lobby'),
        ('I35-36','안감의 조각과 봉함띠 대조','15b2',273,348,(('16',False),('17',False)),'hotel_lobby'),
        ('I37-38','가방의 공백과 회수물 비교','15b2',349,372,(('14',True),),'hotel_lobby'),
    ]
    for key,label,p,a,b,cards,space in reversed(groups2):current=scope(key,label,p,a,b,current,cards,space=space)
    groups1=[
        ('I02-05','새 사인과 서로 확인하는 가방','15b1',21,76,()),
        ('I06-07','현재 읽는 최근 맹세 문구','15b1',77,104,(('03',False),)),
        ('I08-09','직접 제시한 전문과 종료한 선','15b1',105,134,(('04',False),('03',True))),
        ('I11-12','씻은 잔과 마지막 직접 인계','15b1',150,181,(('20',False),)),
        ('I13-14','두 종이와 처음 들었던 사용 설명','15b1',182,209,(('05',False),)),
        ('I15-16','세 열쇠와 최초 여섯 봉함','15b1',210,235,(('07',False),('08',False))),
        ('I17-18','물건을 남겨 두고 떠나는 세 사람','15b1',236,261,()),
    ]
    # I10 belongs between the actual oath disclosure and the first-cup testimony.
    for key,label,p,a,b,cards in reversed(groups1[3:]):current=scope(key,label,p,a,b,current,cards)
    after_compare=r.seq('15b1',144,148,grant('02','15b1',142,current))
    compare=r.document('cup-comparison','현장 물건 비교 자료','15b1',139,142,after_compare)
    current=r.seq('15b1',135,138,compare)
    for key,label,p,a,b,cards in reversed(groups1[:3]):current=scope(key,label,p,a,b,current,cards)
    after_file=r.seq('15b1',13,20,grant('01','15b1',19,current))
    file=r.document('death-file','래피 사망 자료','15b1',9,11,after_file)
    return r.seq('15b1',5,8,file),cat


def _result(r):
    end=r.g.add('v4:5:end',{'type':'end','chapterComplete':True,'nextChapter':'6','source':r.docs['15d'].ref(528),'survivors':['mio','rin','nana','sho','satsuki'],'campaignReady':False})
    tail=r.seq('15d',482,529,end)
    after_letter=r.seq('15d',426,481,tail)
    letter=r.document('unfinished-akari-note','다 쓰지 못한 설명','15d',418,424,after_letter,private=True)
    before_letter=r.seq('15d',374,417,letter)
    reflection=r.remember('T5-C02:private-result','T5-C02',[('A','15d',349,354),('B','15d',357,362),('C','15d',365,370)],before_letter)
    night=r.seq('15d',221,346,reflection)
    after_lie=r.seq('169',312,328,night)
    lie=r.g.add('v4:5:result:T5-LIE-B',{'type':'branch','cases':[{'flag':'T5-LIE-B','equals':True,'to':after_lie}],'default':night})
    sorting=r.seq('15d',161,218,lie)
    aftermath=r.remember('T5-C03:result','T5-C03',[('A','100',287,297),('B','100',301,309),('C','100',313,319)],sorting)
    return r.seq('15d',5,158,aftermath)
