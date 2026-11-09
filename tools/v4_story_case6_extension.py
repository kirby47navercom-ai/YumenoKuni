"""Authored arrival scene, with one selected response and its delayed callback."""


def compile_arrival(r, after):
    source = r.d['187']

    def section(key, target):
        start, end = source.section(key)
        return r.seq('187', start, end, target)

    tail = section('6-L06', after)
    callbacks = [(value, section('6-LR01' + value, tail)) for value in 'ABC']
    recalled = r.recall('6-LC01:arrival-reaction', '6-LC01', callbacks, '187', source.section('6-L05')[0])
    common = section('6-L04', recalled)
    options = [
        ('A', '나나에게 이유를 더 말하라고 하지 않고 길을 비킨다', section('6-LA01', common)),
        ('B', '함께 읽을 때 가방을 내려놓는 자리는 먼저 정하자고 한다', section('6-LB01', common)),
        ('C', '사츠키에게 자신도 맡기고 싶지 않은 것이 있다고 말한다', section('6-LC01C', common)),
    ]
    menu_line = source.section('6-LC01')[0]
    menu = r.menu('187', '6-LC01', menu_line, options)
    r.g.nodes[menu].update(selectionRole='shared-arrival-boundaries', caseEvidenceChanged=False,
                         finalSupportChoiceChanged=False)
    intro = r.seq('187', source.section('6-L03')[0], menu_line - 1, menu)
    return compile_corridor(r, section('6-L01', section('6-L02', intro)))


def compile_corridor(r, after):
    source = r.d['188']

    def section(key, target):
        start, end = source.section(key)
        return r.seq('188', start, end, target)

    tail = section('6-D07', after)
    callback = r.recall('6-DC01:corridor-reaction', '6-DC01',
                        [(value, section('6-DR01' + value, tail)) for value in 'ABC'],
                        '188', source.section('6-D06')[0])
    common = section('6-D05', callback)
    menu_line = source.section('6-DC01')[0]
    menu = r.menu('188', '6-DC01', menu_line, [
        ('A', '아카리에게 화났던 일을 미화하지 않고 말한다', section('6-DA01', common)),
        ('B', '사츠키에게 함께 있었던 평범한 장면 하나만 물어본다', section('6-DB01', common)),
        ('C', '더 묻지 않고 먼저 내려가겠다고 말한다', section('6-DC01C', common)),
    ])
    r.g.nodes[menu].update(selectionRole='current-corridor-speaking-boundary',
                          caseEvidenceChanged=False, finalSupportChoiceChanged=False)
    entry = section('6-D01', section('6-D02', section('6-D03', menu)))
    r.g.nodes[entry]['timeOfDay'] = 'day'  # Explicit18th-day morning, before the old16a range.
    return entry
