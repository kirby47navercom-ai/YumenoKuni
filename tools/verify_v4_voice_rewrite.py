"""Prove that the voice pass changes dialogue bytes, never source routing or IDs."""
import hashlib,json,re,sys
from collections import Counter
from pathlib import Path
from build_v4_story import Source,speaker_line
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'Game/Saved/voice-rewrite-20261107'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
baseline=read(WORK/'before.json');edits=read(WORK/'applied-edits.json')
allowed={(r['file'],r['line']):r for r in edits}
speakers=Counter();events=0;files=0;changes=0
for name in baseline['files']:
    old=Source(WORK/'manuscripts-before'/name);new=Source(ROOT/'docs/design/rewrite_v4'/name)
    assert len(old.lines)==len(new.lines),(name,'line count')
    assert old.headings==new.headings,(name,'headings/scene boundaries')
    for n,(a,b) in enumerate(zip(old.lines,new.lines),1):
        if a==b:continue
        row=allowed[(name,n)];assert (a,b)==(row['before'],row['after'])
        x,y=speaker_line(a),speaker_line(b);assert x and y
        assert {k:v for k,v in x.items()if k!='text'}=={k:v for k,v in y.items()if k!='text'}
        assert re.findall(r'【.*?】|〔.*?〕|\*\*.*?\*\*',a)==re.findall(r'【.*?】|〔.*?〕|\*\*.*?\*\*',b),(name,n,'target/keyword')
        assert re.findall(r'\d+(?:[:.%]\d*)?',a)==re.findall(r'\d+(?:[:.%]\d*)?',b),(name,n,'numeric fact')
        assert not re.search(r'[\u3040-\u30ff]',b),(name,n,'unexpected kana')
        if row['manual']:speakers[row['speaker'].split('·')[0]]+=1
        changes+=1
    before=old.paragraphs();after=new.paragraphs();assert len(before)==len(after)
    for a,b in zip(before,after):
        assert a['id']==b['id'],(name,a['source']['line'],'save ID changed')
        for k in a:
            if k not in ('text','source'):assert a[k]==b[k],(name,a['id'],k)
        events+=1
    files+=1
save=ROOT/'Game/Saved/ui-checkpoints/normal-ch3-latest/savegames.json'
assert hashlib.sha256(save.read_bytes()).hexdigest()=='d43c126c6df61cb9f96b312cb65fdcf9992605368617f23c572fc5c6e9850fe7'
result={'ok':True,'sourceFiles':files,'sourceParagraphIdsPreserved':events,'changedDialogueRows':changes,'manualEdits':sum(speakers.values()),'manualBySpeaker':dict(speakers),'sameHeadingsStageDirectionsChoicesLineCountsDeliveryTargetsNumbers':True,'saveUnchanged':True,'allBranchRuntimeOrFullLiteraryAcceptance':False}
(WORK/'source-invariance.json').write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
