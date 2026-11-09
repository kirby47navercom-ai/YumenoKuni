"""Exact late-entry substitutions; each route keeps its own stable graph IDs.

Base choices are retained, never flattened. Cloning is necessary because normal
and late meetings can both be in a chapter and have different outgoing edges.
"""
from copy import deepcopy

LATE_KEYS=('143','144','145','146','147','148','149','150','151','87','88','89','90','RIN02Late6AM','RIN03Late7','AI02Late6AM','AI03Late6PM','YU02Late6AM','RE02Late6PM','SHO02Late7','SA02Late6AM','SA03Late6PM','AK02Late6AM','RI02Late6AM','YU03Late7','38-late')

REVIEWED_HASHES={
    '143':'a874a0b7cb05ce3c13097e971c2002017168af35c5fee43477403e249c1c7df2',
    '144':'68bb731a446d77351c834ef55ec55a969086035e03019531be34c9dbd431acc2',
    '145':'1528665171ed516d9adc6b6a5be95330b5197647a669495bbc69d00ddc3da2d0',
    '146':'3c48d90f91ede1f9ac34e97db4de65a4f249f048ee1a5255bf4a36fe8d16300c',
    '147':'9b5839d04030c66e1507340b1bf94aef5226d43d4a7d9ce587ba4669a583d298',
    '148':'09a0c17928b747cce9691cc8a176bf6c9ae0c9e3a7df290e7d8099521ad2fe70',
    '149':'ebea4c61e7da3b6c4af5202170e1f4147cdc8d941c32495e3a9b64e63559efb6',
    '150':'21a6ea36f81433716d0dca221406f4e20a6c6e9ad45b346c45383db3274dd069',
    '151':'b43ea1f8db4cd1c9a022aa5aff4fd17b45893f625c1ab6efce644fac6495b739',
    '87':'5d0732e18a1ad6b9948f74bec4d70a37009eb54d5a1fb94f79c42598a136dc4c',
    '88':'5a0be2c047f07953e7ef124a9edd26d70226f7f82ac8f89e49514a18bb18757c',
    '89':'f533426420bc480077be71d0925c053bfcfad932aa2cb4798de94818231794db',
    '90':'896a55642eb80a12c9587cf65175f908bdddd09a32ecf33b8e8e0d9af6e96206',
}


class LateRoute:
    def __init__(self,key,base,source):
        from build_v4_story import Graph
        self.g=Graph('freetime');self.base=base;self.source=source
        self.ids={ident:ident+':late:'+key for ident in base['nodes']}
        def remap(value):
            if isinstance(value,str):return self.ids.get(value,value)
            if isinstance(value,list):return [remap(v) for v in value]
            if isinstance(value,dict):return {k:remap(v) for k,v in value.items()}
            return value
        self.g.nodes=remap(deepcopy(base['nodes']))
        # Dictionary keys themselves were not covered by value remapping.
        self.g.nodes={self.ids[k]:v for k,v in self.g.nodes.items()}
        self.entry=self.ids[base['entry']]
        self.end=next(n['id'] for n in self.g.nodes.values() if n['type']=='return')
        self.cache={}

    def seq(self,a,b,to):
        key=(a,b,to)
        if key not in self.cache:self.cache[key]=self.g.sequence(self.source,a,b,to)
        return self.cache[key]

    def node_at(self,line):
        hits=[n['id'] for n in self.g.nodes.values() if n.get('source',{}).get('file')==self.base['sourceFile'] and n.get('source',{}).get('line')==line]
        if len(hits)!=1:raise ValueError('Late route exact source event absent/ambiguous: '+str((self.base['sourceFile'],line,hits)))
        return hits[0]

    def menu(self,flag):
        hits=[n['id'] for n in self.g.nodes.values() if n['type']=='menu' and any(flag in o.get('set',{}) for o in n['options'])]
        if len(hits)!=1:raise ValueError('Late route menu absent/ambiguous: '+flag)
        return hits[0]

    def redirect(self,old,new):
        def replace(value):
            if isinstance(value,str):return new if value==old else value
            if isinstance(value,list):return [replace(v) for v in value]
            if isinstance(value,dict):return {k:(v if k=='id' else replace(v)) for k,v in value.items()}
            return value
        self.g.nodes={key:replace(node) for key,node in self.g.nodes.items()}
        if self.entry==old:self.entry=new

    def replace(self,first,last,start,stop):
        a=self.node_at(first);b=self.node_at(last);after=self.g.nodes[b]['next']
        target=self.seq(start,stop,after) if start is not None else after
        self.redirect(a,target)
        # Removed source ranges are metadata in blocks.json, not executable
        # stale normal-date dialogue hidden in the late route's node pool.
        for ident in [n['id'] for n in self.g.nodes.values() if n.get('source',{}).get('file')==self.base['sourceFile'] and first<=n.get('source',{}).get('line',0)<=last]:del self.g.nodes[ident]

    def insert_before(self,line,first,last):
        target=self.node_at(line);entry=self.seq(first,last,target)
        self.redirect(target,entry)
        next(n for n in self.g.nodes.values() if n.get('source',{}).get('file')==self.source.name and n.get('source',{}).get('line')==last)['next']=target

    def append(self,first,last):
        target=self.seq(first,last,self.end);self.redirect(self.end,target)
        next(n for n in self.g.nodes.values() if n.get('source',{}).get('file')==self.source.name and n.get('source',{}).get('line')==last)['next']=self.end

    def export(self,key,entry=None,**extra):
        meta={k:deepcopy(v) for k,v in self.base.items() if k in ('authoredMenuCount','requiresPriorFlags','conditionalPriorFlags','physicalState')}
        return self.g.export(entry or self.entry,kind='freetime',sourceFile=self.source.name,baseSourceFile=self.base['sourceFile'],completionFlag='fte:'+key+':complete',routingStatus='explicit-reviewed-late-calendar',campaignReady=False,**meta,**extra)


def compile_late(key,sources,freetime_graphs):
    docs={s.prefix:s for s in sources.values()}
    for p,digest in REVIEWED_HASHES.items():
        if docs[p].hash!=digest:raise ValueError('Late FTE source changed; re-read substitutions: '+docs[p].name)
    aliases={'RIN02Late6AM':('35','143'),'RIN03Late7':('54','143'),'YU02Late6AM':('44','146'),'RE02Late6PM':('45','147'),'AI02Late6AM':('43','145'),'AI03Late6PM':('52','145'),'SHO02Late7':('41','148'),'SA02Late6AM':('49','149'),'SA03Late6PM':('63','149'),'AK02Late6AM':('39','151'),'RI02Late6AM':('48','90'),'YU03Late7':('53','146'),'38-late':('38','88')}
    if key in aliases:base,p=aliases[key]
    else:base,p={'143':('20','143'),'144':('21','144'),'145':('25','145'),'146':('26','146'),'147':('27','147'),'148':('23','148'),'149':('32','149'),'150':('28','150'),'151':('31','151'),'87':('34','87'),'88':('29','88'),'89':('24','89'),'90':('30','90')}[key]
    r=LateRoute(key,freetime_graphs[base],docs[p]);g=r.g
    if key=='143':
        r.replace(160,170,63,83)
        entry=r.seq(7,55,r.menu('RIN-01A'))
    elif key=='144':
        r.replace(84,84,87,87);r.replace(352,352,151,151)
        r.replace(268,294,95,119);r.replace(298,318,123,141)
        # The normal bread-bag rustle happens first, then the late actual meal.
        tail=r.seq(157,199,r.end);r.redirect(r.end,tail)
        # redirect also touched the newly inserted tail's exit; restore it.
        last=next(n for n in g.nodes.values() if n.get('source',{}).get('file')==docs[p].name and n.get('source',{}).get('line')==199);last['next']=r.end
        entry=r.seq(7,79,r.menu('KOTO-01A'))
    elif key=='145':
        r.replace(359,361,55,57)
        entry=r.seq(7,47,r.menu('F-AI01-A'))
    elif key=='146':
        r.replace(529,531,137,143)
        prior=r.node_at(96);insert=r.seq(125,131,prior);r.redirect(prior,insert)
        # Preserve the newly inserted final edge, avoiding an insertion loop.
        next(n for n in g.nodes.values() if n.get('source',{}).get('file')==docs[p].name and n.get('source',{}).get('line')==131)['next']=prior
        requested=r.seq(97,119,r.menu('F-YU01-A'))
        gate=g.add('v4:146:missing-actual-C01',{'type':'gate','reason':'Actual current morning2-C01 response absent.'})
        branch=g.add('v4:146:actual-C01',{'type':'branch','cases':[{'flag':'2-C01','equals':v,'to':r.seq(a,b,requested)} for v,a,b in [('A',55,63),('B',67,79),('C',83,91)]],'default':gate})
        entry=r.seq(7,49,branch)
    elif key=='147':entry=r.seq(7,103,r.menu('F-RE01-A'))
    elif key=='148':
        r.replace(296,296,77,77)
        entry=r.seq(7,69,r.menu('SHO-01A'))
    elif key=='149':entry=r.seq(7,31,r.node_at(11))
    elif key=='150':entry=r.seq(7,103,r.menu('F-KE01-A'))
    elif key=='151':entry=r.seq(7,39,r.node_at(20))
    elif key=='87':
        tail=r.seq(111,117,r.end)
        missing=g.add('v4:87:missing-actual-photo-choice',{'type':'gate','reason':'The actual current personal photo preservation choice is absent.'})
        choice=g.add('v4:87:actual-personal-photo',{'type':'branch','cases':[{'flag':'F-HA01-B','equals':v,'to':r.seq(a,b,tail)} for v,a,b in [('B1',81,85),('B2',89,95),('B3',99,107)]],'default':missing})
        replaced=r.seq(51,77,choice);r.redirect(r.node_at(496),replaced)
        for ident in [n['id'] for n in g.nodes.values() if n.get('source',{}).get('file')==r.base['sourceFile'] and 496<=n.get('source',{}).get('line',0)<=512]:del g.nodes[ident]
        entry=r.seq(9,45,r.entry)
    elif key=='88':
        r.replace(9,37,9,67)
        r.replace(271,271,91,105)
        r.replace(365,373,113,135)
        before=r.menu('F-NA01-A');insert=r.seq(73,85,before);r.redirect(before,insert)
        next(n for n in g.nodes.values() if n.get('source',{}).get('file')==docs[p].name and n.get('source',{}).get('line')==85)['next']=before
        entry=r.entry
    elif key=='38-late':
        r.replace(9,19,147,161)
        r.replace(383,391,167,179)
        entry=r.entry
    elif key=='89':
        r.insert_before(122,45,77)
        before=r.menu('SORA-01B');insert=r.seq(83,99,before);r.redirect(before,insert)
        next(n for n in g.nodes.values() if n.get('source',{}).get('file')==docs[p].name and n.get('source',{}).get('line')==99)['next']=before
        r.append(105,115)
        entry=r.seq(7,39,r.entry)
    elif key=='90':
        r.insert_before(269,51,75);r.append(81,93)
        entry=r.seq(9,45,r.entry)
    elif key=='RIN02Late6AM':entry=r.seq(91,103,r.node_at(10))
    elif key=='RIN03Late7':
        # Current question already spoken by late introduction. Only the
        # apology path's first question is omitted; its answer is retained.
        r.replace(12,12,None,None)
        prior=r.node_at(8);entry=r.seq(111,127,g.nodes[prior]['next'])
    elif key=='YU02Late6AM':entry=r.entry
    elif key=='YU03Late7':entry=r.entry
    elif key=='RE02Late6PM':entry=r.seq(111,123,r.node_at(13))
    elif key=='AI02Late6AM':
        r.replace(33,43,123,129)
        r.replace(339,339,None,None)
        for node in g.nodes.values():
            if node['type']=='branch' and any(c.get('flag')=='F-AI01-A3-LUNCH' for c in node.get('cases',[])):
                for case in node['cases']:case['flag']='AI01Dinner5A3'
                node['calendarMealSource']=docs['145'].ref(139)
        entry=r.seq(91,117,g.nodes[r.ids['v4:43:previous-request']]['id'])
    elif key=='AI03Late6PM':
        r.replace(29,35,165,171)
        entry=r.seq(149,159,r.node_at(19))
    elif key=='SHO02Late7':entry=r.seq(85,101,r.node_at(21))
    elif key=='SA02Late6AM':entry=r.entry
    elif key=='SA03Late6PM':entry=r.seq(47,63,r.node_at(43))
    elif key=='RI02Late6AM':entry=r.seq(101,113,r.entry)
    elif key=='AK02Late6AM':
        # The new laundry action is part of this single current meeting. It
        # precedes39, whose actual late flag suppresses its normal substitute.
        entry=g.add('v4:151:actual-first-laundry',{'type':'branch','cases':[{'flag':'F-AK01-B','equals':'B2','to':r.seq(47,55,r.entry)}],'default':r.entry})
    else:raise ValueError(key)
    graph=r.export(key,entry,lateCalendarKey=key,eligibility=('Twelfth-day4-00b initial29 only, then separate thirteenth-day4-69b38-late; no originalfirst-case/normal38 duplication or same-window chain.' if key in ('88','38-late') else 'Only the exact source-authored separate calendar window; never a first-case substitute or same-window chain.'))
    if key=='146':graph['requiresPriorFlags']={'2-C01':['A','B','C']};graph['authoredMenuCount']=3
    if key=='RIN03Late7':graph['requiresPriorFlags']={**graph.get('requiresPriorFlags',{}),'RIN01Late5':[True]}
    if key=='AI02Late6AM':graph['conditionalPriorFlags']={'AI01Dinner5A3':{'when':{'F-AI01-A':'A3'},'values':['EAT','LEAVE']}}
    if key=='AK02Late6AM':graph['requiresPriorFlags']={**graph.get('requiresPriorFlags',{}),'AK01Late5':[True]}
    if key=='38-late':graph['requiresPriorFlags']={**graph.get('requiresPriorFlags',{}),'fte:88:complete':[True]}
    return graph
