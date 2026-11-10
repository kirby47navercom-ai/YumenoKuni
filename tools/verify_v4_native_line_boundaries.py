"""Native48 conversion regression; source text and target positions survive."""
from copy import deepcopy
import json
from build_v4_story import OUT,load
from v4_native_tasks import convert_task,bounded_debate_lines


def utf16(text):return len(text.encode('utf-16-le'))//2
def at_utf16(text,start,word):return text.encode('utf-16-le')[start*2:(start+utf16(word))*2].decode('utf-16-le')==word


def main():
    tasks=load(OUT/'tasks.json')['tasks'];checks=0
    for ident,needle in [('T6-PN-A03','같은 힘이면'),('T3-PN-01','시작은 그 방 시계로'),('T5-PN-01','그동안 린은')]:
        task=tasks[ident];before=deepcopy(task);native=convert_task(task)
        original=next(l for l in task['lines'] if needle in l['text']);text=original['text'].replace('【','').replace('】','').replace('〔','').replace('〕','')
        rows=[l for l in native['stage']['lines'] if l.get('sourceLineId',l['id'])==original['id']]
        assert len(rows)==2 and ''.join(l['text'] for l in rows)==text
        assert rows[0]['text']==text[:text.index('.')+1] and rows[1]['text']==text[text.index('.')+1:]
        assert all(utf16(l['text'])<=48 and l['actor']==original['actor'] and l['speaker']==original['speaker'] and l['source']==original['source'] for l in rows)
        assert rows[1]['kind']=='plain' and not any(rows[1].get(k) for k in ('weak','lieWeak','agree','targets'))
        assert task==before and native['debate']['lines']==native['stage']['lines']
        if ident=='T6-PN-A03':
            weak=rows[0]['weak'];assert at_utf16(rows[0]['text'],weak['start'],weak['word'])
            assert weak['word']=='오늘 사용으로 옛 안전 판정도 확인'
        checks+=6
    # A target after the split must move, not remain on the now-plain prefix.
    prefix='가'*34+'. ';body='반박 진짜표적 거짓 거짓표적.';tail=' 나'*20+'.';text=prefix+body+tail
    line={'id':'unit','text':text,'kind':'weak','source':{'file':'synthetic','line':1},'actor':'mio','speaker':'미오'}
    weak={'start':text.index('진짜표적'),'word':'진짜표적','answer':'card','lie':False}
    lie={'start':text.index('거짓표적'),'word':'거짓표적','answer':'original','lie':True}
    line.update(weak=weak,lieWeak=lie,targets=[{'kind':'weak','weak':deepcopy(weak),'outcome':'A'},{'kind':'weak','weak':deepcopy(lie),'outcome':'B'}]);before=deepcopy(line)
    rows=bounded_debate_lines(line)
    assert ''.join(r['text'] for r in rows)==text and line==before
    assert rows[0]['kind']=='plain' and not rows[0].get('weak') and not rows[0].get('lieWeak')
    assert sum(bool(r.get('weak')) for r in rows)==sum(bool(r.get('lieWeak')) for r in rows)==1
    for row in rows:
        for key in ('weak','lieWeak'):
            if row.get(key):assert at_utf16(row['text'],row[key]['start'],row[key]['word'])
        for target in row.get('targets',[]):assert at_utf16(row['text'],target['weak']['start'],target['weak']['word'])
    checks+=4
    agree={'id':'agreement','text':prefix+' 동의할 합의표적입니다.','kind':'agree','agree':'card','source':{},'actor':'nana','speaker':'나나','targets':[{'kind':'agree','word':'합의표적','answer':'card'}]}
    rows=bounded_debate_lines(agree);marked=next(r for r in rows if r.get('agree'))
    assert rows[0]['kind']=='plain' and marked['kind']=='agree' and len([r for r in rows if r.get('agree')])==1
    target=marked['targets'][0];assert at_utf16(marked['text'],target['start'],target['word'])
    # Leading spaces and a non-BMP glyph are preserved; native offsets count
    # the same UTF-16 cells as Windows, without splitting a surrogate pair.
    emoji={'id':'utf16','text':'😀 앞 표적','kind':'weak','actor':'mio','speaker':'미오','source':{},'weak':{'start':4,'word':'표적','answer':'c'}}
    row=bounded_debate_lines(emoji)[0];assert row['weak']['start']==5 and at_utf16(row['text'],5,'표적')
    checks+=3
    broken={'id':'too-long','text':'가'*49,'kind':'weak','actor':'mio','speaker':'미오','source':{},'weak':{'start':0,'word':'가'*49,'answer':'c'}}
    try:bounded_debate_lines(broken)
    except ValueError as error:assert 'single target exceeds' in str(error)
    else:raise AssertionError('Long target silently cut')
    try:bounded_debate_lines({'id':'unbreakable','text':'나'*49,'kind':'plain','source':{}})
    except ValueError as error:assert 'no source sentence/word boundary' in str(error)
    else:raise AssertionError('Unbreakable utterance silently cut')
    print(json.dumps({'passed':True,'actualLongUtterances':3,'checks':checks+2,'sourceMutation':False,'nativeLimitUtf16':48,'runtimeExecuted':False}))


if __name__=='__main__':main()
