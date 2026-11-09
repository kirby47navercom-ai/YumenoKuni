"""Explicit reviewed FTE callbacks and late introductions; no generic flatten."""

REVIEWED_HASHES={
    '21':'fa89b862743305b347524c590639e84b6f2115c79b79cffefa77dfe4c4fc2520',
    '46':'f0350e6d9fba1119d660f4c5e5630e79c0c2ec52bd2bb5b13655b10bcdc4225a',
    '152':'4af21fa040fe227ee1e742263255bb4f1cc7351a9bc47d310811eb3af64894d4',
    '51':'5ac6a0e3cb44d1f05fc77cd6849c7c300e4e0059e22a8a4ee4bc9a7378d5185c',
    '43':'f47828e4acc93bf6084a95641f6c74910d25254a312796e725c95de7d947ab4b',
    '49':'4c49a7b7b05f4e396d868e8360af5310edda516340a55f50ad436353c38b7503',
    '23':'fc98b0b95f76e4e0d50f3ceae47cce95a15838631229cd454b63feb4d4cd3567',
    '40':'c7ae09b9922a2cca2e42ed19f2dc5d2a0d72180738545fefce16c85d6ecad424',
    '50':'309deb8efe6f5ffa32cc885749daf86b04f2fd8730b5791d53b22772cae18448',
    '153':'b4cb90305678983bf7765eb063ee7e0605fc53e74cc6ec1c54d6bc6fc6bdf826',
    '35':'44db9fd52a95a299e81c02014d3674d8d3f14f5b62f14c01371b8c6ed3cedf88',
    '41':'866ef84d553df0de1701a950dc2f562ce4bb6665d5d6834f5ad157ba47e32deb',
    '44':'c9708a37da6edcf826e4b6857845411cd215938f4dbe5b20168df12a891b3a56',
    '45':'23f15ccccecd53867626941767668ef20326efe4081b27d91b4b58f79080f1c8',
    '48':'b1691be00edcb5400ec5917ae02f041bdc84dc499833fdf003187c625ea4cbe2',
    '39':'a6f1f5066085b03379514f902f2f299d494f64cfeab54ed110d1629798aa2a33',
    '42':'06e8807606eb7c05bb935357c25aec7a628ab9308ccf3ce4fbbde2382a8bd55d',
    '47':'c0ed1c0bca684d7bb6fcf38fe7b74b13c23e479697153b4e354ceb81246f7b34',
    '52':'abfd24bee3ebfd66a28658d698a0c72b4a93327afdab0c66d1e2b50b10d913bc',
    '54':'8de7dc6ea0ae4dbc163e2fecd2a2f4cae88063108096a605cf957b508af190e3',
    '63':'a6e99629abdd73dbe27262e7a60c9cfba3f89e708d85f5c328d8404fa513619d',
    '36':'bfd60e4d46fc3d13cc38ca2b3374790098e78cfd20120d666103cf20e90c5fea',
    '53':'7c2dadbcceba142a0f9c1d082c4c26e2d968621785a6b44a5bb77fb4f9556ba3',
}


def compile_followup(prefix,sources):
    from build_v4_story import Graph,compile_choice_scene,clean
    docs={s.prefix:s for s in sources.values()};s=docs[prefix];g=Graph('freetime')
    for key,expected in REVIEWED_HASHES.items():
        if docs[key].hash!=expected:raise ValueError('Reviewed FTE source changed; re-read exact branches: '+docs[key].name)
    end=g.add('v4:'+prefix+':return',{'type':'return'});cache={}
    def seq(a,b,to):
        key=(a,b,to)
        if key not in cache:cache[key]=g.sequence(s,a,b,to)
        return cache[key]
    def menu(flag,line,rows,to):
        opts=[]
        for value,a,b in rows:
            label=clean(s.lines[a-1]).split('. ',1)[-1]
            opts.append({'id':value,'label':label,'to':seq(a+1,b,to),'set':{flag:value}})
        return g.add('v4:'+prefix+':'+flag+':menu',{'type':'menu','q':s.lines[line-1].split('—')[-1].strip(),'source':s.ref(line),'options':opts})
    def recall(key,flag,rows,to,default=None):
        if default is None:default=g.add('v4:'+prefix+':missing:'+key,{'type':'gate','reason':'Actual previous meeting choice absent: '+flag})
        return g.add('v4:'+prefix+':'+key,{'type':'branch','cases':[{'flag':flag,'equals':value,'to':seq(a,b,to)} for value,a,b in rows],'default':default})
    extra={}
    if prefix=='21':
        tail=seq(394,418,end)
        b=menu('KOTO-01B',344,[('A',354,367),('B',368,377),('C',378,393)],tail)
        request=seq(346,352,b)
        echo=recall('current-Yuu','KOTO-01A',[('A',268,294),('B',298,318),('C',322,342)],request)
        common=seq(146,264,echo)
        a=menu('KOTO-01A',70,[('A',72,97),('B',98,123),('C',124,145)],common)
        entry=seq(6,69,a)
        extra.update(eligibility='Actual first-case F1-B only. Later day-five uses manuscript144, not this morning reference.',physicalState='A/C do not manufacture a marker made by Mio. B alone makes two prototypes; no general adoption or inventory gift is granted.')
    elif prefix=='46':
        def timed_line(line,last,text,proof,to):
            rest=seq(line+1,last,to)
            e=next(e for e in s.paragraphs(line,line) if e['type']=='say')
            normal=g.add(e['id'],{**e,'next':rest})
            late=g.add(e['id']+':late3AM',{**e,'text':text,'source':docs['152'].ref(proof),'baseSource':e['source'],'authoredTimeReplacement':True,'next':rest})
            return g.add('v4:46:time:'+str(line),{'type':'branch','cases':[{'flag':'TA01Late2B','equals':True,'to':late}],'default':normal})
        tail=seq(467,468,end)
        b1=timed_line(449,451,'어제 입간판 옮길 때처럼 어디 놓을지만 말해 줘도 돼.내가 드는 거랑 정하는 거 다 할 필요는 없으니까.',67,tail)
        b2=seq(455,458,tail);b3=seq(461,465,tail)
        previous_b=g.add('v4:46:previous-B',{'type':'branch','cases':[{'flag':'F-TA01-B','equals':k,'to':to} for k,to in [('B1',b1),('B2',b2),('B3',b3)]],'default':g.add('v4:46:missing:previous-B',{'type':'gate','reason':'The actual first-meeting work choice is required.'})})
        finish=seq(433,446,previous_b)
        b1_finish=seq(393,398,finish)
        a2=seq(381,384,b1_finish);other=seq(387,390,b1_finish)
        inspecting=g.add('v4:46:B1:actually-repaired',{'type':'branch','cases':[{'flag':'F-TA02-A','equals':'A2','to':a2}],'default':other})
        b1=seq(373,378,inspecting)
        b=g.add('v4:46:F-TA02-B:menu',{'type':'menu','q':'끝난 일을 확인할까','source':s.ref(369),'options':[{'id':key,'label':label,'to':target,'set':{'F-TA02-B':key}} for key,label,target in [('B1','지금 고친 부분을 같이 확인한다',b1),('B2','모양이 마음에 안 드는지 묻는다',seq(401,416,finish)),('B3','미오가 먼저 일어난다',seq(419,432,finish))]]})
        common=seq(311,368,b)
        a=menu('F-TA02-A',101,[('A1',103,166),('A2',167,246),('A3',247,308)],common)
        before_a=seq(71,100,a)
        a1=timed_line(33,42,'어제 네가 앞에 가니까 생각보다 천천히 돌더라.',65,before_a)
        a2=seq(45,54,before_a)
        a3=timed_line(57,68,'어제 잘한 데서 끝내 달라고 했지.',66,before_a)
        old=g.add('v4:46:previous-A',{'type':'branch','cases':[{'flag':'F-TA01-A','equals':k,'to':to} for k,to in [('A1',a1),('A2',a2),('A3',a3)]],'default':g.add('v4:46:missing:previous-A',{'type':'gate','reason':'The actual first-meeting walking choice is required.'})})
        shared_intro=seq(17,28,old)
        normal=seq(5,16,shared_intro)
        late=g.sequence(docs['152'],41,61,shared_intro)
        entry=g.add('v4:46:actual-entry-day',{'type':'branch','cases':[{'flag':'TA01Late2B','equals':True,'to':late}],'default':normal})
        extra.update(requiresPriorFlags={'F-TA01-A':['A1','A2','A3'],'F-TA01-B':['B1','B2','B3']},eligibility='Normal same-day F1-B after33, or exact next-morning F1-early after152. No wrist injury yet.',physicalState='Ordinary bag lining repaired. Only A2 is actual Mio sewing; A1 held it and A3 did no work. Sewing kit remains on the table and Yuu button remains unrepaired.')
    elif prefix=='35':
        normal_end=seq(398,420,end)
        bc=menu('RIN-02B-BC',282,[('B1',284,319),('B2',320,359),('B3',360,397)],normal_end)
        repaired=seq(234,281,bc)
        exclusive_end=seq(230,232,end)
        early=menu('RIN-02B-A',168,[('A1',170,195),('A2',196,223),('A3',224,229)],exclusive_end)
        a=seq(164,167,early)
        first=g.add('v4:35:RIN-02A:menu',{'type':'menu','q':'자기가 아는 것','source':s.ref(110),'options':[{'id':key,'label':label,'to':target,'set':{'RIN-02A':key}} for key,label,target in [('A','린보다 먼저 레버의 위치까지 설명한다',seq(114,129,a)),('B','린이 직접 대답하게 기다린다',seq(132,145,repaired)),('C','수리한 물건이라는 것만 말하고 방법은 말하지 않겠다고 한다',seq(148,161,repaired))]]})
        object=seq(42,109,first)
        previous=recall('actual-first-record','RIN-01B',[('B',14,21),('A',24,31),('C',34,40)],object)
        entry=seq(6,11,previous)
        extra.update(requiresPriorFlags={'RIN-01B':['A','B','C']},authoredMenuCount=3,eligibility='Only fifth-day F2-A after actualRin01. Source143 delayed sixth-day introduction is separate.',physicalState='A ends before new-foot work and receives no old paper foot. B/C have one later B1 held-body/B2 old-paper received/B3 observed choice. Not a secret building passage or mandatory evidence.')
    elif prefix=='41':
        tail=seq(553,591,end)
        second=menu('SHO-02B',507,[('A',509,524),('B',525,538),('C',539,552)],tail)
        common=seq(435,506,second)
        first=menu('SHO-02A',125,[('A',127,230),('B',231,314),('C',315,434)],common)
        # This literal spoken addition is explicit inside the stage direction.
        # Extract only that authorised sentence, never speak the producer note.
        source=s.ref(123)
        current_line=g.add('v4:41:actual-chapter-two-addition',{'type':'say','speaker':'미오','actor':'mio','text':'다시 여기로 돌아오고 싶을지는 모르겠지만.','mono':False,'source':source,'authoredInlineQuotation':True,'next':first})
        front=seq(93,122,current_line)
        btail=seq(75,76,front)
        becho=recall('B-actual-waking','SHO-01A',[('A',63,66),('B',69,72),('C',69,72)],btail)
        used=seq(55,60,becho)
        others=seq(79,90,front)
        slept=seq(43,52,front)
        a_and_b=g.add('v4:41:actually-slept-and-left',{'type':'branch','cases':[{'flag':'SHO-01A','equals':'A','to':slept}],'default':others})
        prior=g.add('v4:41:previous-inventory-question',{'type':'branch','cases':[{'flag':'SHO-01B','equals':'B','to':used},{'flag':'SHO-01B','equals':'A','to':a_and_b},{'flag':'SHO-01B','equals':'C','to':others}],'default':g.add('v4:41:missing:previous-inventory-question',{'type':'gate','reason':'Actual first-meeting request and waking are absent.'})})
        entry=seq(5,38,prior)
        extra.update(requiresPriorFlags={'SHO-01A':['A','B','C'],'SHO-01B':['A','B','C']},eligibility='Only fifth-day F2-A after actual23. Source148 delayed seventh-day introduction is separate.',physicalState='A borrows a working bus/B leaves all toys/C borrows the bent wind-up car. String stays only withC after02A-B; it is removed inA/B. No repair, monetary bet, gift to Mio or new sleeping promise.')
    elif prefix=='36':
        tail=seq(292,326,end)
        worked=seq(258,258,tail);observed=seq(260,288,tail)
        labour=g.add('v4:36:actual-labour-not-repeated',{'type':'branch','cases':[{'flag':'KOTO-02A','equals':'A','to':worked}],'default':observed})
        return_to_work=seq(256,256,labour)
        second=menu('KOTO-02B',210,[('A',212,224),('B',226,234),('C',236,250)],return_to_work)
        confronted=seq(174,206,second)
        reply=recall('actual-current-work-answer','KOTO-02A',[('A',162,162),('B',166,166),('C',170,170)],confronted)
        cart=seq(156,158,reply)
        first=menu('KOTO-02A',56,[('A',58,126),('B',128,138),('C',140,150)],cart)
        waiting=seq(52,52,first)
        previous=recall('actual-first-witness-promise','KOTO-01B',[('A',34,36),('B',40,42),('C',46,48)],waiting)
        entry=seq(8,28,previous)
        extra.update(requiresPriorFlags={'KOTO-01B':['A','B','C']},eligibility='Seventh-day F2-D only after actual21 or144. New current towels, not a reversal of prior day16 work.',physicalState='A Mio actually carries towels before challenge, B refuses, C asksKoto towork. Only02B-A public correction toNana; B private correction/C future individual confirmation. CurrentA never replays Koto/Nana joint towel scene. No compulsory labour, automatic after-refusalhelp, oath, signed consent, event evidence or gift.')
    elif prefix=='53':
        tail=seq(381,399,end)
        dedicated_end=seq(357,361,tail)
        b2echo=recall('actual-prior-public-name-scope','F-YU01-B',[('B1',353,353),('B2',349,349),('B3',353,353)],dedicated_end)
        dedicated=seq(341,345,b2echo)
        second=g.add('v4:53:F-YU03-B:menu',{'type':'menu','q':'이 한 장을 받을까','source':s.ref(327),'options':[{'id':key,'label':label,'to':target,'set':{'F-YU03-B':key}} for key,label,target in [('B1','지금 종이 그대로 받는다',seq(331,337,tail)),('B2','미오 이름까지 써 달라고 한다',dedicated),('B3','종이는 받지 않는다',seq(365,377,tail))]]})
        offer=seq(317,325,second)
        performance=recall('actual-first-performance-observation','2-C05',[('A',293,301),('B',305,311)],offer)
        playing=seq(113,289,performance)
        first=menu('F-YU03-A',63,[('A1',65,77),('A2',79,93),('A3',95,107)],playing)
        paper=seq(39,61,first)
        entry=recall('current-invitation-owner','F-YU02-B',[('B1',9,19),('B2',9,19),('B3',23,33)],paper)
        extra.update(requiresPriorFlags={'F-YU02-B':['B1','B2','B3'],'F-YU01-B':['B1','B2','B3'],'2-C05':['A','B']},eligibility='Seventh-day F2-D only after26/44 and actual first small performance. Same source after exact146 late chain; no same-window second candidate.',physicalState='CurrentA changes practice signature shape. B1 one plain autograph/B2 one private dedication actually goes toMio; B3 staysYuu and is never delivered. Original public-name agreement remains only actual26B2N1/N2, personal dedication is separate. No protected-copy, public oath, handwriting proof, recording or emotion-use certificate.')
    elif prefix=='52':
        final=seq(339,339,end)
        labour=recall('actual-current-labour','F-AI03-A',[('A1',329,329),('A2',333,333),('A3',337,337)],final)
        tail=seq(325,325,labour)
        second=menu('F-AI03-B',283,[('B1',285,295),('B2',297,307),('B3',309,321)],tail)
        talk=seq(263,281,second)
        first=menu('F-AI03-A',209,[('A1',211,223),('A2',225,237),('A3',239,257)],talk)
        current=seq(65,207,first)
        previous=recall('previous-actual-meeting-place','F-AI02-B',[('B1',29,35),('B2',39,47),('B3',51,59)],current)
        entry=seq(7,23,previous)
        extra.update(requiresPriorFlags={'F-AI02-B':['B1','B2','B3']},eligibility='Only sixth-day F2-C after actual25/43 and the chosenC05A/B performance route. Late145 replacement must use its own exact opening.',physicalState='All paths begin dinner preparation late. A1 Mio actually carries plates, A2 changes division and Nana finishes hers first, A3 Mio remains apart until common confrontation. No retroactive punctuality, automatic help, food deprivation, new medicine/danger material, photograph gift or early ability rule.')
    elif prefix=='54':
        day_tail=seq(512,522,end)
        normal=seq(504,504,day_tail);late=seq(508,508,day_tail)
        day=g.add('v4:54:actual-return-calendar',{'type':'branch','cases':[{'flag':'RIN01Late5','equals':True,'to':late}],'default':normal})
        returned=recall('actual-current-borrower-return','RIN-03A',[('A1',436,456),('A2',460,478),('A3',482,498)],day)
        pocket=seq(432,432,returned)
        second=menu('RIN-03B',368,[('B1',370,386),('B2',388,406),('B3',408,428)],pocket)
        making=seq(210,366,second)
        first=menu('RIN-03A',114,[('A1',116,148),('A2',150,182),('A3',184,206)],making)
        request=seq(82,112,first)
        stopped=recall('actual-prior-disagreement','RIN-02B-A',[('A1',12,22),('A2',26,34),('A3',38,48)],request)
        observed_work=recall('actual-prior-work-contribution','RIN-02B-BC',[('B1',58,60),('B2',64,70),('B3',74,76)],request)
        together=seq(52,54,observed_work)
        prior=g.add('v4:54:actual-prior-work-ended',{'type':'branch','cases':[{'flag':'RIN-02A','equals':'A','to':stopped},{'flag':'RIN-02A','equals':'B','to':together},{'flag':'RIN-02A','equals':'C','to':together}],'default':g.add('v4:54:missing:prior-work-choice',{'type':'gate','reason':'The actual second meeting stopped/worked branch is absent.'})})
        entry=seq(8,8,prior)
        extra.update(requiresPriorFlags={'RIN-02A':['A','B','C']},conditionalPriorFlags={'RIN-02B-A':{'when':{'RIN-02A':'A'},'values':['A1','A2','A3']},'RIN-02B-BC':{'when':{'RIN-02A':['B','C']},'values':['B1','B2','B3']}},eligibility='Normal sixth-day F2-B after actual35. The143 seventh-day late introduction is separate and the explicit ending calendar remains conditional.',physicalState='A1 Mio falsely borrows as own user and returns without correcting Nana, A2 Rin borrows/returns directly, A3 no tape is borrowed and paper strip is folded twice. B1 Mio handwriting/Rin attached, B2 Rin handwriting/Mio heldcloth, B3 blanklabel and one short actual load test. Pouch andtools alwaysRin; old paper foot only prior35B2, no new gift or mimicry permission.')
    elif prefix=='63':
        b1story=seq(257,325,end)
        b1echo=recall('current-apology-not-universal','F-SA03-A',[('A1',233,237),('A2',241,245),('A3',249,251)],b1story)
        b1=seq(215,229,b1echo)
        fountain=seq(351,445,end)
        first_stamp=recall('existing-first-stamp','F-SA02-A',[('A1',341,341),('A2',345,345),('A3',349,349)],fountain)
        b2=seq(329,337,first_stamp)
        second=g.add('v4:63:F-SA03-B:menu',{'type':'menu','q':'지금 하고 싶은 것','source':s.ref(211),'options':[{'id':key,'label':label,'to':target,'set':{'F-SA03-B':key}} for key,label,target in [('B1','고양이를 보며 여기 더 있는다',b1),('B2','사츠키가 원하는 곳으로 같이 걷는다',b2),('B3','지각에 대한 사과와 별개로 오늘은 헤어진다',seq(449,459,end))]]})
        cat=seq(199,209,second)
        emptyfoot=g.add('v4:63:actual-empty-first-square',{'type':'branch','cases':[{'flag':'F-SA02-A','equals':'A3','to':seq(193,193,cat)}],'default':cat})
        b3=seq(185,189,emptyfoot)
        priorcard=g.add('v4:63:actual-postcard-state',{'type':'branch','cases':[{'flag':'F-SA02-B','equals':key,'to':target} for key,target in [('B1',seq(169,171,cat)),('B2',seq(175,181,cat)),('B3',b3)]],'default':g.add('v4:63:missing:postcard-state',{'type':'gate','reason':'Actual prior stamp completion is absent.'})})
        sitting=seq(163,165,priorcard)
        first=menu('F-SA03-A',97,[('A1',99,121),('A2',123,141),('A3',143,159)],sitting)
        priorwait=recall('actual-prior-wait','F-SA02-B',[('B1',67,73),('B2',77,83),('B3',87,93)],first)
        entry=seq(9,63,priorwait)
        extra.update(requiresPriorFlags={'F-SA02-A':['A1','A2','A3'],'F-SA02-B':['B1','B2','B3']},eligibility='Normal sixth-day F2-B only after32/49. Source149 late afternoon current promise replaces9..39, never repeats it.',physicalState='Mio actually arrives10minutes late and borrows the common novel once. B1 novel staysbag, fictionalendingunknown, cat watched; B2 retrieves own postcard, bookleftroom, stamps only each actual missing square, bothcardsdry andseparatelyowned; B3 returnsroomwithoutreconciliation or unseenSatsuki completion. No catfeeding/touching, new postc ard gift, ability, prediction or numeric relationship reward.')
    elif prefix=='39':
        tail=seq(473,489,end)
        taste_left=recall('B1-current-cup-not-universal','F-AK02-A',[('A1',391,391),('A2',395,395),('A3',399,403)],tail)
        second=g.add('v4:39:F-AK02-B:menu',{'type':'menu','q':'남은 차를 두고','source':s.ref(371),'options':[{'id':key,'label':label,'to':target,'set':{'F-AK02-B':key}} for key,label,target in [('B1','지금은 함께 마시고 싶다고 말한다',seq(375,387,taste_left)),('B2','확인하러 가고 싶으면 끝내도 된다고 말한다',seq(409,419,tail)),('B3','정리하고 같이 표를 확인하러 가자고 한다',seq(423,469,tail))]]})
        request=seq(357,367,second)
        tasting=recall('current-different-taste','F-AK02-A',[('A1',323,329),('A2',333,339),('A3',343,353)],request)
        first=menu('F-AK02-A',135,[('A1',137,151),('A2',153,167),('A3',169,313)],seq(319,319,tasting))
        tea=seq(91,131,first)
        prior=recall('previous-request','F-AK01-B',[('B1',49,57),('B2',61,75),('B3',79,85)],tea)
        arrival=seq(27,43,prior)
        laundry=seq(9,23,arrival)
        not_already_done=g.add('v4:39:B2-laundry-is-current',{'type':'branch','cases':[{'flag':'AK01Late5','equals':True,'to':arrival}],'default':laundry})
        entry=g.add('v4:39:actually-chosen-order',{'type':'branch','cases':[{'flag':'F-AK01-B','equals':'B2','to':not_already_done}],'default':arrival})
        extra.update(requiresPriorFlags={'F-AK01-B':['B1','B2','B3']},eligibility='Sixth-day F2-B after actual31. Only priorB2 earns current introductory laundry; actual151 lateB2 already did it and is never repeated.',physicalState='Exactly two current common cups withdrawn and eventually returned. A1 matchesAkari/A2 onlyMio/A3 overbrews; onlyB1 has the exact source cup-water replacement. B2 Akari voluntarily remains, B3 returns cups then compares existing two item numbers without deleting either. No poison-test claim, newcup, oath, rewind, numerical relationship reward or inherited personal cup.')
    elif prefix=='42':
        waving=seq(455,455,end)
        distance=recall('actual-earlier-throwing-line','SORA-02A',[('A',445,447),('B',451,453),('C',445,447)],waving)
        farewell=seq(363,441,distance)
        second=menu('SORA-02B',277,[('A',279,299),('B',301,335),('C',337,359)],farewell)
        new_game=seq(211,275,second)
        first=menu('SORA-02A',89,[('A',91,111),('B',113,133),('C',135,205)],new_game)
        line=seq(67,87,first)
        previous=recall('actual-earlier-praise','SORA-01B',[('A',33,41),('B',45,51),('C',55,61)],line)
        entry=seq(7,27,previous)
        extra.update(requiresPriorFlags={'SORA-01B':['A','B','C']},eligibility='Sixth-day F2-B only, after actual24 and before first small performance. Sora is alive in his own body.',physicalState='A same backline: Mio2outside/3fallen vsSora5outside/6fallen. B nearerMio6 vsfartherSora5. C six rebuilt racks, accumulatedMio4/Sora7. LaterYuu single-ball6 vsSora4 is separate, as areB rematch/rack failure/spectating. No miniature arcade judgment, prize, new photo, ability, fourth throw or uniform retroactive scoring is fabricated.')
    elif prefix=='47':
        second=menu('F-KE02-B',201,[('B1',203,229),('B2',231,317),('B3',319,329)],end)
        customer=recall('actual-first-customer-role','F-KE01-B',[('B1',175,179),('B2',183,187),('B3',191,197)],second)
        next_scene=seq(131,169,customer)
        first=menu('F-KE02-A',81,[('A1',83,95),('A2',97,109),('A3',111,125)],next_scene)
        setting=seq(57,79,first)
        previous=recall('actual-earlier-stop','F-KE01-A',[('A1',47,51),('A2',47,51),('A3',37,43)],setting)
        entry=seq(7,31,previous)
        extra.update(requiresPriorFlags={'F-KE01-A':['A1','A2','A3'],'F-KE01-B':['B1','B2','B3']},eligibility='Sixth-day F2-B only after28, including actual150 late28. Ken andRiku are alive in their own bodies.',physicalState='Bus, ticket and fare are acted imaginary situations; Riku retains his blank-paper prop. B1 Mio one driving role, B2 observes an extended nondeparture, B3 exits before unseen following scene. No real timetable, escape route, family confession, gift, hypnotic/surrogate action or private thirty-card knowledge is granted.')
    elif prefix=='44':
        stayed=seq(471,483,end);left=seq(487,487,end)
        listened=seq(413,423,stayed)
        last_lyric=recall('actually-heard-last-lyric','F-YU01-B',[('B1',401,401),('B2',405,409),('B3',401,401)],listened)
        after_song=seq(393,397,last_lyric)
        song=recall('actual-priority-song','F-YU01-B',[('B1',321,353),('B2',357,389),('B3',321,353)],after_song)
        second=g.add('v4:44:F-YU02-B:menu',{'type':'menu','q':'다음에 실제로 할 것','source':s.ref(309),'options':[{'id':key,'label':label,'to':target,'set':{'F-YU02-B':key}} for key,label,target in [('B1','한 곡을 끝까지 듣고 구체적으로 답한다',seq(313,317,song)),('B2','함께 소리를 내 본다',seq(427,447,stayed)),('B3','오늘은 듣지 않고 간다',seq(451,465,left))]]})
        new_memory=seq(239,307,second)
        current_echo=recall('current-invitation-not-inferred','F-YU02-A',[('A1',217,219),('A2',223,227),('A3',231,235)],new_memory)
        personal=seq(197,213,current_echo)
        old_hearing=recall('previous-actual-hearing','F-YU01-A',[('A1',167,171),('A2',175,179),('A3',183,191)],personal)
        short_phrase=seq(163,163,old_hearing)
        name_consent=recall('previous-name-consent','F-YU01-B2-N',[('N1',141,143),('N2',147,149)],short_phrase)
        lower=seq(133,137,name_consent)
        previous_song=g.add('v4:44:previous-selected-song',{'type':'branch','cases':[{'flag':'F-YU01-B','equals':key,'to':target} for key,target in [('B1',seq(113,129,short_phrase)),('B2',lower),('B3',seq(153,159,short_phrase))]],'default':g.add('v4:44:missing:previous-song',{'type':'gate','reason':'Actual first-meeting choice of song is absent.'})})
        first=menu('F-YU02-A',35,[('A1',37,57),('A2',59,81),('A3',83,105)],previous_song)
        entry=seq(7,33,first)
        extra.update(requiresPriorFlags={'F-YU01-A':['A1','A2','A3'],'F-YU01-B':['B1','B2','B3']},conditionalPriorFlags={'F-YU01-B2-N':{'when':{'F-YU01-B':'B2'},'values':['N1','N2']}},eligibility='Only fifth-day F2-A after26. The source146 late introduction and sixth-day44 replacement are separate windows.',physicalState='Riku never hears the full song here. Only currentA2 hears his corridor reaction; onlyA3 brings a cup. B1 hears exactly one priority song and its clarified last phrase, B2 sings a short phrase together, B3 leaves before listening. Strap intact; no recording, transmission, public name-consent reversal or compulsory emotional magic.')
    elif prefix=='45':
        stayed=seq(355,365,end);left=seq(369,369,end)
        for node in g.nodes.values():
            if node.get('source',{}).get('file')==s.name and node.get('source',{}).get('line')==369:node['pov']='rei';node['knowledgeOwner']='rei'
        second=g.add('v4:45:F-RE02-B:menu',{'type':'menu','q':'그 그림으로 할 일','source':s.ref(287),'options':[{'id':key,'label':label,'to':target,'set':{'F-RE02-B':key}} for key,label,target in [('B1','지금 모습의 한 부분을 함께 더한다',seq(291,309,stayed)),('B2','그린 종이를 잠깐 받아 멀리서 본다',seq(313,331,stayed)),('B3','평가를 여기서 끝내고 자리를 뜬다',seq(335,349,left))]]})
        common=seq(219,285,second)
        first=menu('F-RE02-A',153,[('A1',155,177),('A2',179,195),('A3',197,213)],common)
        drawing=seq(69,151,first)
        previous=recall('actual-garden-work','F-RE01-B',[('B1',33,39),('B2',43,51),('B3',55,63)],drawing)
        entry=seq(7,27,previous)
        extra.update(requiresPriorFlags={'F-RE01-B':['B1','B2','B3']},eligibility='Only fifth-day F2-A after27, before creation ability disclosure. Source147 delayed27 and sixth-day45 replacement are separate windows.',physicalState='OnlyA1 actually corrects the drawn pillar width. B1 Rei adds a footrest to his original and Mio keeps her own separate sheet; B2 original returned toRei; B3 leaves before the draft is seen, whose closing observation belongs only toRei. No magical creation, deleted old leaf, handkerchief gift, original drawing gift or incident evidence.')
    elif prefix=='48':
        final=seq(451,451,end)
        answer=recall('current-reason-to-watch','F-RI02-B',[('B1',441,441),('B2',445,445),('B3',449,449)],final)
        leave=seq(431,437,answer)
        old_game=recall('actual-previous-card-game','F-RI01-B',[('B1',409,413),('B2',417,419),('B3',423,425)],leave)
        personal=seq(389,405,old_game)
        second=menu('F-RI02-B',309,[('B1',311,335),('B2',337,357),('B3',359,385)],personal)
        old_guess=recall('actual-previous-guess','F-RI01-A',[('A1',291,293),('A2',297,299),('A3',303,305)],second)
        demonstration=seq(249,285,old_guess)
        first=menu('F-RI02-A',27,[('A1',29,49),('A2',51,151),('A3',153,243)],demonstration)
        entry=seq(9,25,first)
        extra.update(requiresPriorFlags={'F-RI01-A':['A1','A2','A3'],'F-RI01-B':['B1','B2','B3']},eligibility='Only fifth-day F2-A after30. Source90 late first plus sixth-day introduction is a separate contract.',physicalState='OnlyA1/A2/A3 respective personal answer is known. OnlyB1 sees the cushion-side method; B2 hidden recovery plus a different second demonstration, B3 fails without learning the first method. Coin always returns toRiku; no surrogate, teleportation, technique reward, heirloom or new incident evidence.')
    elif prefix=='23':
        tail=seq(230,526,end)
        learned=recall('result-awake','SHO-01A',[('A',222,223),('B',226,227),('C',226,227)],tail)
        after=seq(212,219,learned)
        ctail=seq(206,210,after)
        c=seq(184,189,recall('C-actual-promise','SHO-01A',[('A',192,197),('B',200,203),('C',200,203)],ctail))
        btail=seq(178,180,after)
        b=seq(160,167,recall('B-actual-waking','SHO-01A',[('A',170,171),('B',174,175),('C',174,175)],btail))
        atail=seq(148,156,after)
        a=recall('A-actual-rest','SHO-01A',[('A',140,141),('B',144,145),('C',144,145)],atail)
        second=g.add('v4:23:SHO-01B:menu',{'type':'menu','q':'지금 깨울까','source':s.ref(134),'options':[{'id':key,'label':label,'to':target,'set':{'SHO-01B':key}} for key,label,target in [('A','나중에 직접 물어보게 한다',a),('B','쇼에게 용건을 전한다',b),('C','코토와 함께 확인하러 간다',c)]]})
        first=menu('SHO-01A',54,[('A',56,69),('B',70,87),('C',88,99)],seq(100,133,second))
        entry=seq(6,53,first)
        extra.update(eligibility='Actual first-case F1-E after contact announcement and78, before the candidate meeting. Source148 is a different day-five introduction.',physicalState='Only A actually sleeps. B/C rest awake. Each later waking/continuing rest/promise change utterance is selected from actualA, not merged. The book/title are seen, not borrowed or gifted.')
    elif prefix=='40':
        tail=seq(677,680,end)
        observed_c=recall('Ai-only-observed-current-item','KAEDE-02B',[('A',665,666),('B',669,670),('C',673,674)],tail)
        observed=g.add('v4:40:Ai-actual-work',{'type':'branch','cases':[{'flag':'KAEDE-02A','equals':'A','to':seq(657,658,tail)},{'flag':'KAEDE-02A','equals':'B','to':seq(661,662,tail)},{'flag':'KAEDE-02A','equals':'C','to':observed_c}],'default':g.add('v4:40:missing:actual-work',{'type':'gate','reason':'The current practice choice is required.'})})
        finishing=seq(631,654,observed)
        exhibition=recall('actual-exhibition','KAEDE-02A',[('A',581,592),('B',595,606),('C',609,614)],finishing)
        b=g.add('v4:40:KAEDE-02B:menu',{'type':'menu','q':'남길 받침','source':s.ref(557),'options':[{'id':key,'label':label,'to':target,'set':{'KAEDE-02B':key}} for key,label,target in [('A','잘된 것 하나를 보관하게 해 달라고 한다',seq(561,576,finishing)),('B','서로 만든 것을 골라 함께 둔다',exhibition),('C','모두 통으로 돌려보내자고 한다',seq(619,630,finishing))]]})
        common=seq(463,556,b)
        a=menu('KAEDE-02A',103,[('A',105,192),('B',193,304),('C',305,462)],common)
        # Ask before handing over the piping bag. Observers never make the
        # common practice blobs which the later C callbacks say do not exist.
        practice_return=g.add('v4:40:after-accepted-practice',{'type':'branch','cases':[{'flag':'KAEDE-02A','equals':o['id'],'to':o['to']} for o in g.nodes[a]['options'] if o['id'] in ('A','B')],'default':g.add('v4:40:missing:accepted-practice',{'type':'gate','reason':'Only an accepted hands-on practice choice can reach this work.'})})
        practice=seq(75,102,practice_return)
        for option in g.nodes[a]['options']:
            if option['id'] in ('A','B'):option['to']=practice
        previous=recall('previous-bag','KAEDE-01B',[('A',33,44),('B',47,60),('C',63,72)],a)
        shared=seq(13,28,previous);normal=seq(5,12,shared);late=g.sequence(docs['153'],59,63,shared)
        entry=g.add('v4:40:actual-entry-day',{'type':'branch','cases':[{'flag':'KAEDE01Late3D','equals':True,'to':late}],'default':normal})
        extra.update(requiresPriorFlags={'KAEDE-01B':['A','B','C']},eligibility='First-case F1-D after actual22, or F1-E after exact153 late22 and the intervening contact announcement/78. Never chain in one window.',physicalState='Only02B-A gives one non-edible practice flower. B leaves a joint display with actual authored pieces; C returns Mio material and leaves Kaede one flower. The returned empty auxiliary tin is a different item.')
    elif prefix=='50':
        at_home=seq(565,566,end)
        room=g.add('v4:50:actual-box-return',{'type':'branch','cases':[{'flag':'KAEDE-03B','equals':'A','to':at_home}],'default':end})
        farewell=seq(543,562,room)
        akept=seq(261,266,farewell)
        a=g.add('v4:50:A-actual-box-maker',{'type':'branch','cases':[{'flag':'KAEDE-03A','equals':'C','to':seq(253,258,akept)}],'default':seq(247,250,akept)})
        b=g.add('v4:50:KAEDE-03B:menu',{'type':'menu','q':'포장 뒤에 남을 것','source':s.ref(241),'options':[{'id':key,'label':label,'to':target,'set':{'KAEDE-03B':key}} for key,label,target in [('A','미오 몫을 받아 방으로 가져간다',a),('B','여기서 먹고 포장은 가져가지 않는다',seq(269,388,farewell)),('C','더 먹거나 가져가지 않는다',seq(391,542,farewell))]]})
        common=seq(229,240,b)
        private=seq(207,226,common)
        prior_competitor=g.add('v4:50:actually-heard-competitor',{'type':'branch','cases':[{'flag':'KAEDE-02A','equals':'B','to':private}],'default':common})
        ribbons=seq(181,204,prior_competitor)
        a=menu('KAEDE-03A',129,[('A',131,150),('B',151,164),('C',165,180)],ribbons)
        preparation=seq(95,128,a)
        display=seq(53,56,recall('actual-displayed-piece','KAEDE-02A',[('A',59,62),('B',65,70),('C',73,78)],preparation))
        previous=g.add('v4:50:actual-practice-item',{'type':'branch','cases':[{'flag':'KAEDE-02B','equals':'A','to':seq(33,50,preparation)},{'flag':'KAEDE-02B','equals':'B','to':display},{'flag':'KAEDE-02B','equals':'C','to':seq(81,94,preparation)}],'default':g.add('v4:50:missing:practice-item',{'type':'gate','reason':'Actual prior flower ownership/display/return choice is absent.'})})
        entry=seq(5,28,previous)
        extra.update(requiresPriorFlags={'KAEDE-02A':['A','B','C'],'KAEDE-02B':['A','B','C']},eligibility='Only living Kaede on fourth-day F1-F, after actual22/40 and failed contact. Exact153 delayed pair still uses the same next-day reference.',physicalState='Practice flower ownership is separate from edible box. Only03B-A actually carries the food box home after farewell; B eats now/C leaves it. Only02A-B knows the private competitor conversation.')
    elif prefix=='153':
        base=compile_choice_scene(docs['22']);g.nodes=base['nodes']
        first=next(n['id'] for n in g.nodes.values() if n['type']=='menu' and n.get('source',{}).get('line')==40)
        entry=g.sequence(s,5,51,first)
        extra.update(completionSet={'fte:22:complete':True,'KAEDE01Late3D':True},eligibility='Only third-day F1-D when22 is uncompleted. Current hand-wash introduction replaces22 start; exact01A/B and actual dishes follow.40 requires a separate laterF1-E.',physicalState='Only one splashed plate rinsed now. Earlier baked three cookies are tasted; no instant baking, no earlier broken-plate observation.')
    elif prefix=='51':
        tail=seq(375,379,end)
        ending=recall('actually-waited','F-TA03-A',[('A1',359,360),('A2',363,366),('A3',369,372)],tail)
        finish=seq(351,356,ending)
        b=menu('F-TA03-B',301,[('B1',303,318),('B2',319,334),('B3',335,350)],finish)
        after_rin=seq(295,300,b)
        actual=recall('actual-path-observation','F-TA03-A',[('A1',285,286),('A2',289,290),('A3',293,294)],after_rin)
        afternoon=seq(133,282,actual)
        a=menu('F-TA03-A',79,[('A1',81,96),('A2',97,114),('A3',115,132)],afternoon)
        walk=seq(57,78,a)
        def time_variant(key,line,last,late_text,proof):
            rest=seq(line+1,last,walk)
            e=next(e for e in s.paragraphs(line,line) if e['type']=='say')
            normal=g.add(e['id'],{**e,'next':rest})
            late=g.add(e['id']+':late3AM',{**e,'text':late_text,'source':docs['152'].ref(proof),'baseSource':e['source'],'authoredTimeReplacement':True,'next':rest})
            return g.add('v4:51:time:'+key,{'type':'branch','cases':[{'flag':'TA02Late3AM','equals':True,'to':late}],'default':normal})
        a1=time_variant('A1',23,28,'가방은 괜찮아. 아침에 잡아 준 데. 조금 전에 안을 보니까 그대로더라.',78)
        a2=seq(31,40,walk)
        a3=time_variant('A3',43,54,'아침에 내가 가방 다 하고 나서 유우 다시 안 왔어.',88)
        previous=g.add('v4:51:previous-repair',{'type':'branch','cases':[{'flag':'F-TA02-A','equals':k,'to':target} for k,target in [('A1',a1),('A2',a2),('A3',a3)]],'default':g.add('v4:51:missing:previous-repair',{'type':'gate','reason':'Actual second meeting sewing participation is absent.'})})
        entry=seq(5,18,previous)
        extra.update(requiresPriorFlags={'F-TA02-A':['A1','A2','A3']},eligibility='Only third-day lunch window, after actual46 and fixed wrist treatment. Later152 path uses the exact morning reference.',physicalState='Right wrist remains protected. A1 hears the fence from Taiga; A2 sees it; A3 does not inspect it. Ordinary shadow game is not an ability and creates no alternate route.')
    elif prefix=='43':
        ending=recall('previous-taste','F-AI01-B',[('B1',411,422),('B2',425,438),('B3',441,454)],end)
        common_end=seq(405,408,ending)
        b2tail=seq(381,382,common_end)
        puzzle=seq(351,366,b2tail);photos=seq(369,380,b2tail)
        activity=g.add('v4:43:current-activity',{'type':'branch','cases':[{'flag':'F-AI02-A','equals':'A2','to':photos}],'default':puzzle})
        b2=seq(347,348,activity)
        b=g.add('v4:43:F-AI02-B:menu',{'type':'menu','q':'남은 시간의 약속','source':s.ref(319),'options':[{'id':key,'label':label,'to':target,'set':{'F-AI02-B':key}} for key,label,target in [('B1','같이 주방으로 가자고 한다',seq(323,344,common_end)),('B2','여기서 하던 일을 끝낸다',b2),('B3','미오가 먼저 다른 곳으로 간다',seq(385,404,common_end))]]})
        common=seq(253,318,b)
        a=menu('F-AI02-A',109,[('A1',111,134),('A2',135,228),('A3',229,252)],common)
        photographs=seq(77,108,a)
        meal=recall('actual-lunch','F-AI01-A3-LUNCH',[('EAT',63,66),('LEAVE',69,73)],photographs)
        a3=seq(59,60,meal)
        earlier=g.add('v4:43:previous-request',{'type':'branch','cases':[{'flag':'F-AI01-A','equals':key,'to':target} for key,target in [('A1',seq(33,44,photographs)),('A2',seq(47,56,photographs)),('A3',a3)]],'default':g.add('v4:43:missing:previous-request',{'type':'gate','reason':'Actual previous food request is absent.'})})
        entry=seq(7,28,earlier)
        extra.update(requiresPriorFlags={'F-AI01-A':['A1','A2','A3'],'F-AI01-B':['B1','B2','B3']},eligibility='Only actual first-case afternoon after25 and the authored current lunch callback. Day-six late introduction is a separate source145 contract.',physicalState='Only A1/A3 progress a puzzle; A2 shares the photo book. Current lunch eaten/left is consumed as prior fact, not selected again. No automatic substitute meal, repaired salt shaker or tasting reward.')
    elif prefix=='49':
        b1end=seq(445,454,end);b2end=seq(457,466,end);b3end=seq(469,470,end)
        b=g.add('v4:49:F-SA02-B:menu',{'type':'menu','q':'미오의 다음 행동','source':s.ref(253),'options':[{'id':key,'label':label,'to':target,'set':{'F-SA02-B':key}} for key,label,target in [('B1','여기서 함께 기다린다',seq(257,360,b1end)),('B2','혼자 분수에 다녀오고 여기서 다시 만나자고 한다',seq(363,422,b2end)),('B3','오늘은 두 번째 칸을 찍지 않는다',seq(425,440,b3end))]]})
        meeting=seq(199,252,b)
        a=menu('F-SA02-A',71,[('A1',73,122),('A2',123,168),('A3',169,198)],meeting)
        postcard=seq(47,70,a)
        earlier=recall('previous-cat-observation','F-SA01-B',[('B1',27,30),('B2',33,36),('B3',39,44)],postcard)
        entry=seq(5,24,earlier)
        extra.update(requiresPriorFlags={'F-SA01-B':['B1','B2','B3']},eligibility='Only actual first-case afternoon after32. The delayed day-six introduction from149 is a separate route.',physicalState='No new cat feeding or dish washing. Mio stamp states differ: A1 double/A2 single/A3 blank; B1/B2 finish her card, B3 leaves it incomplete. Satsuki B2 has an unfilled second square, not a completed gift.')
    elif prefix=='152':
        base=compile_choice_scene(docs['33']);g.nodes=base['nodes']
        first=next(e['id'] for e in docs['33'].paragraphs(30,59) if e['type'] in ('say','stage'))
        entry=g.sequence(s,5,33,first)
        extra.update(completionSet={'fte:33:complete':True,'TA01Late2B':True},eligibility='Only2nd-day F1-B when33 is uncompleted. It replaces the original33 introduction and retains every actual33 A/B choice. Next46 is another morning window.',physicalState='Before the fixed wrist pain. No extra wound, forced another lap or skipped time.')
    else:raise ValueError('Unreviewed followup '+prefix)
    return g.export(entry,kind='freetime',sourceFile=s.name,completionFlag='fte:'+prefix+':complete',routingStatus='reviewed-explicit-callbacks',campaignReady=False,**extra)
