"""Resolve individually written dialogue edits to stable source-line addresses."""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'data/presentation/voice_rewrite_20261107'
seen={}
for p in folder.glob('batch*.json'):
    for prefix,line,text in json.loads(p.read_text(encoding='utf-8')):seen[(str(prefix),line)]=p.name
requests=json.load(sys.stdin);out=[];existing=[]
draft=folder/'drafts'/sys.argv[1];draft.parent.mkdir(exist_ok=True);draft.write_text(json.dumps(requests,ensure_ascii=False,indent=1),encoding='utf-8')
for prefix,address,old,new in requests:
    files=list((ROOT/'docs/design/rewrite_v4').glob(str(prefix)+'_*.md'))
    if isinstance(address,int):
        # The writer has already read the numbered scene; assert the speaker
        # at that address before deriving the old body for protection checks.
        speaker=old
        assert len(files)==1,(prefix,'Ambiguous numbered source')
        source=files[0];line=source.read_text(encoding='utf-8-sig').splitlines()[address-1]
        m=re.fullmatch(r'\['+re.escape(speaker)+r'\]\s*(.+)',line)
        assert m,(prefix,address,speaker)
        old=m[1];matches=[(source,address)]
    else:
        speaker=address
        matches=[(p,n)for p in files for n,t in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1)if re.fullmatch(r'\['+re.escape(speaker)+r'\]\s*'+re.escape(old),t)]
    assert len(matches)==1,(prefix,speaker,old,matches)
    source,n=matches[0]
    if(str(prefix),n)in seen:
        existing.append([prefix,n,seen[(str(prefix),n)]]);continue
    assert re.findall(r'【.*?】|〔.*?〕|\*\*.*?\*\*',old)==re.findall(r'【.*?】|〔.*?〕|\*\*.*?\*\*',new),(prefix,n,'target')
    assert re.findall(r'\d+(?:[:.%]\d*)?',old)==re.findall(r'\d+(?:[:.%]\d*)?',new),(prefix,n,'number')
    assert not re.search('[\u3040-\u30ff]',new)
    assert new.strip()and'\n'not in new
    out.append([str(prefix),n,new]);seen[(str(prefix),n)]='new'
target=folder/sys.argv[1];assert not target.exists();target.write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
print(json.dumps({'batch':target.name,'newEdits':len(out),'alreadyRewrittenPreserved':existing},ensure_ascii=False))
