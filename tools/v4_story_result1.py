"""Correct-vote aftermath; no wrong vote, private sheet or absent FTE is merged."""


def compile_result(g, sources, next_id):
    d={s.prefix:s for s in sources.values()}

    def seq(p,a,b,to):
        return g.sequence(d[p],a,b if b is not None else len(d[p].lines),to)

    def remembered(ident,flag,rows,to,default=None):
        if default is None:
            default=g.add(ident+':missing',{'type':'gate','reason':'Required prior choice is absent; aftermath cannot invent a shared memory.'})
        return g.add(ident,{'type':'branch','cases':[{'flag':flag,'equals':value,'to':seq(p,a,b,to)} for value,p,a,b in rows],'default':default})

    ending=seq('11d',669,690,next_id)
    kaede=remembered('v4:11d:KAEDE03C:aftermath','KAEDE-03B',[('C','11d',641,667)],ending,default=ending)
    personal_after=seq('11d',545,636,kaede)
    inspected=remembered('v4:11d:I-C01:aftermath','I-C01',[('A','11d',537,537),('B','11d',541,541)],personal_after)
    leader=seq('11d',493,534,inspected)
    phone_common=seq('176',450,458,leader)
    phone_recall=remembered('v4:176:W1-C02:aftermath','W1-C02',[('A','176',412,420),('B','176',424,432),('C','176',436,446)],phone_common)
    phone_start=seq('176',404,408,phone_recall)
    patrol_after=seq('11d',473,489,phone_start)
    lie_echo=remembered('v4:11d:T1-LIE-B:aftermath','T1-LIE-B',[(True,'11d',454,468)],patrol_after,default=patrol_after)
    patrol=seq('11d',430,448,lie_echo)
    food_after=seq('112',133,None,patrol)
    ridicule=remembered('v4:112:1-C07:aftermath','1-C07',[('A','112',121,121),('B','112',125,125),('C','112',129,129)],food_after)
    food=seq('112',5,118,ridicule)
    body=seq('11d',282,427,food)
    summary_recall=remembered('v4:93:T1-C05:aftermath','T1-C05',[('A','93',395,401),('B','93',405,411),('C','93',415,425)],body)
    summary_start=seq('93',381,391,summary_recall)
    privacy=remembered('v4:11d:T1-C02:aftermath','T1-C02',[('A','11d',232,238),('B','11d',242,264),('C','11d',268,276)],summary_start)
    opening=seq('11d',6,229,privacy)
    # This flag changes only after the death is actually announced in R03.
    nodes=[n for n in g.nodes.values() if n.get('source',{}).get('file')==d['11d'].name and n.get('source',{}).get('line')==152]
    if len(nodes)!=1: raise ValueError('Actual R03 death announcement not uniquely routed')
    nodes[0].setdefault('set',{})['public:taiga:death-confirmed']=True
    return opening
