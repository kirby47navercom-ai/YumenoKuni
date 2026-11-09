"""Five first meetings with real nested choices and delayed physical callbacks."""


def compile_nested_first_meeting(source):
    from build_v4_story import Graph,clean
    g=Graph('F');p=source.prefix
    end=g.add(f'v4:{p}:return',{'type':'return'})
    def seq(a,b,to):return g.sequence(source,a,b,to)
    def menu(flag,line,rows,to):
        opts=[]
        for value,a,b in rows:
            heading=source.lines[a-1]
            label=clean(heading).split('. ',1)[-1].strip('*')
            opts.append({'id':value,'label':label,'to':seq(a+1,b,to),'set':{flag:value}})
        return g.add(f'v4:{p}:{flag}:menu',{'type':'menu','q':source.lines[line-1].split('—')[-1].strip(),'source':source.ref(line),'options':opts})
    def remember(ident,flag,rows,default):
        return g.add(f'v4:{p}:{ident}',{'type':'branch','cases':[{'flag':flag,'equals':value,'to':to} for value,to in rows],'default':default})
    if p=='26':
        tail=seq(505,532,end)
        nested=menu('F-YU01-B2-N',331,[('N1',333,358),('N2',359,394)],tail)
        b2=seq(315,330,nested)
        b1=seq(179,312,tail);b3=seq(399,502,tail)
        b=g.add('v4:26:F-YU01-B:menu',{'type':'menu','q':'남의 무대에 보태는 취향','source':source.ref(176),'options':[{'id':key,'label':label,'to':to,'set':{'F-YU01-B':key}} for key,label,to in [('B1','사람들이 아는 첫 곡을 고른다',b1),('B2','유우가 오래 듣던 두 번째 곡을 고른다',b2),('B3','두 곡을 다 들을 수 있는지 묻는다',b3)]]})
        a=menu('F-YU01-A',40,[('A1',42,55),('A2',56,73),('A3',74,91)],seq(94,175,b))
        entry=seq(6,39,a)
    elif p=='27':
        wiped=seq(395,395,end);observed=seq(399,399,end)
        hands=remember('hands','F-RE01-A',[('A1',wiped)],remember('hands-after-B','F-RE01-B',[('B2',wiped)],observed))
        tail=seq(373,392,hands)
        b=menu('F-RE01-B',319,[('B1',321,336),('B2',337,350),('B3',351,370)],tail)
        a=menu('F-RE01-A',53,[('A1',55,76),('A2',77,92),('A3',93,110)],seq(113,318,b))
        entry=seq(5,52,a)
    elif p=='28':
        tail=seq(431,476,end)
        b2=seq(419,424,tail);other=seq(427,428,tail)
        b_echo=remember('B-current','F-KE01-B',[('B2',b2)],other)
        b=menu('F-KE01-B',341,[('B1',343,362),('B2',363,386),('B3',387,410)],seq(413,416,b_echo))
        common=seq(323,340,b)
        aecho=remember('A-current','F-KE01-A',[(value,seq(a,b,common)) for value,a,b in [('A1',267,282),('A2',285,302),('A3',305,320)]],g.add('v4:28:missing-A',{'type':'gate','reason':'Required current role-play choice missing.'}))
        a=menu('F-KE01-A',47,[('A1',49,68),('A2',69,90),('A3',91,108)],seq(111,264,aecho))
        entry=seq(5,46,a)
    elif p=='31':
        b=menu('F-AK01-B',200,[('B1',202,217),('B2',218,242),('B3',243,356)],seq(359,378,end))
        cup_common=seq(180,199,b)
        fresh=seq(162,168,cup_common);sweetened=seq(172,176,cup_common)
        cups=remember('cup-current','F-AK01-A',[('A1',fresh),('A2',fresh)],sweetened)
        a=menu('F-AK01-A',100,[('A1',102,115),('A2',116,135),('A3',136,153)],seq(156,159,cups))
        entry=seq(6,99,a)
    elif p=='34':
        tail=seq(322,513,end)
        b3_common=seq(294,318,tail)
        own_photo=seq(278,282,b3_common);shared_photo=seq(286,290,b3_common)
        deleted=remember('B3-deletion','F-HA01-A',[('A2',own_photo)],shared_photo)
        b3=seq(272,275,deleted)
        b=g.add('v4:34:F-HA01-B:menu',{'type':'menu','q':'남길 사진','source':source.ref(126),'options':[{'id':key,'label':label,'to':to,'set':{'F-HA01-B':key,'photo:F-HA01:kept':key!='B3','photo:F-HA01:replacement':key=='B2'}} for key,label,to in [('B1','지금의 어색한 사진을 남긴다',seq(130,142,tail)),('B2','둘이 준비해서 한 장 새로 찍는다',seq(146,269,tail)),('B3','오늘 찍은 사진을 지워 달라고 한다',b3)]]})
        a=menu('F-HA01-A',34,[('A1',36,49),('A2',50,73),('A3',74,97)],seq(100,125,b))
        entry=seq(8,33,a)
    else:raise ValueError('Unreviewed nested meeting '+p)
    return g.export(entry,kind='freetime',routingStatus='reviewed-nested-first-meeting',sourceFile=source.name,completionFlag=f'fte:{p}:complete',eligibility='Only the exact first-case daytime window. Late-entry replacements are separate and cannot use this introduction.',sourceConditionalPolicy='Nested song-name consent, actual leaf-wiping, actual role-play response, current tea and current-photo deletion remain distinct. No unseen branch is replayed.')
