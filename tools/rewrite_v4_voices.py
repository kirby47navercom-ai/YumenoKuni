"""Apply individually authored dialogue edits, preserving source lines and save IDs."""
import argparse
import hashlib
import json
import pathlib
import re
import shutil
from collections import Counter

ROOT=pathlib.Path(__file__).resolve().parents[1]
SRC=ROOT/'docs/design/rewrite_v4'
WORK=ROOT/'Game/Saved/voice-rewrite-20261107'
EDITS=ROOT/'data/presentation/voice_rewrite_20261107'
SAY=re.compile(r'^(\[([^\]]+)\]\s*)(.+)$')
NAMES={'미오','레이','소라','켄','나나','리쿠','아카리','유우','코토','사츠키','타이가','린','쇼','아이','하루카','카에데','래피'}
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
def inventory():
    from build_v4_story import Source
    result=[]
    for p in sorted(SRC.glob('*.md')):
        source=Source(p)
        for n,line in enumerate(source.lines,1):
            m=SAY.fullmatch(line)
            if m and m[2].split('·')[0]in NAMES:
                result.append({'file':p.name,'prefix':source.prefix,'line':n,'location':source.ref(n)['location'],'speaker':m[2],'before':line,'text':m[3]})
    return result
def prepare():
    WORK.mkdir(parents=True,exist_ok=True);EDITS.mkdir(parents=True,exist_ok=True)
    if (WORK/'before.json').exists():return
    rows=inventory();files={r['file']for r in rows}
    for name in files:
        target=WORK/'manuscripts-before'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(SRC/name,target)
    dump(WORK/'before.json',{'build':load(ROOT/'Game/build-result.json')['id'],'rows':rows,'files':{name:sha((SRC/name).read_bytes())for name in sorted(files)}})
    candidates=[r for r in rows if re.search(r'그 말|뜻은|뜻이|판단|확인|조건|책임|구분|한 게 아니라|있는 게 아니라|라는 건|라고 하면|라고 하는|라고 말|가능성|상대|당사자|존중|성립|전제',r['text'])]
    dump(WORK/'candidates.json',candidates)
    dump(WORK/'progress.json',{'phase':'authoring','baselineRows':len(rows),'candidateRows':len(candidates),'applied':False,'manualBatches':[],'literaryAcceptance':False})
    print(json.dumps({'rows':len(rows),'files':len(files),'candidates':len(candidates)},ensure_ascii=False))
def excerpt(start,count):
    candidates=load(WORK/'candidates.json')[start:start+count]
    for i,r in enumerate(candidates,start):
        lines=(WORK/'manuscripts-before'/r['file']).read_text(encoding='utf-8-sig').splitlines();n=r['line']
        prev=next((x for x in reversed(lines[max(0,n-6):n-1])if x.strip()),'')
        following=next((x for x in lines[n:min(len(lines),n+4)]if x.strip()),'')
        print(f"{i} {r['prefix']}:{n} {prev}\n{r['before']}\n> {following}")
def apply():
    from v4_editorial_ids import fingerprint
    before=load(WORK/'before.json');by={(r['prefix'],r['line']):r for r in before['rows']};authored={};batches=[]
    # Later scene passes can be applied to a release that already has the first
    # pass's spacing or wording. Keep exact earlier versions as accepted inputs.
    prior_revisions={}
    registry=ROOT/'tools/v4_voice_revisions_20261107.json'
    if registry.exists():
        prior_revisions={(r['file'],r['line']):r for r in load(registry)['revisions']}
    for p in sorted(EDITS.glob('batch*.json')):
        rows=load(p);batches.append(p.name)
        for prefix,line,text in rows:
            key=(str(prefix),line);assert key in by,key;assert key not in authored,key
            assert isinstance(text,str)and text.strip()and'\n'not in text
            assert not re.search(r'[\u3040-\u30ff]',text),(key,'Korean dialogue contains unexpected kana')
            old=by[key]['text']
            assert re.findall(r'【.*?】|〔.*?〕',old)==re.findall(r'【.*?】|〔.*?〕',text),(key,'Preserve exact evidence target phrases')
            authored[key]=text
    revisions=[];changed=[];manual=spacing=0;by_name={}
    def spaced(text):
        # Marked phrases also bind minigame keywords. Do not move their bytes.
        parts=re.split(r'(【.*?】|〔.*?〕|\*\*.*?\*\*)',text)
        return ''.join(p if i%2 else re.sub(r'(?<=[가-힣0-9\]】〕”」)])[.!?,](?=[가-힣])',lambda m:m[0]+' ',p)for i,p in enumerate(parts))
    for row in before['rows']:
        key=(row['prefix'],row['line']);m=SAY.fullmatch(row['before']);text=authored.get(key,row['text']);text=spaced(text);after=m[1]+text
        if after==row['before']:continue
        if key in authored:manual+=1
        else:spacing+=1
        name=row['file'];by_name.setdefault(name,[]).append((row['line'],row['before'],after))
        original=fingerprint(row['prefix'],row['location'],row['before'])
        prior=prior_revisions.get((name,row['line']),{})
        versions=list(dict.fromkeys([*prior.get('beforeVersions',[]),prior.get('after',row['before'])]))
        versions=[v for v in versions if v not in (row['before'],after)]
        revisions.append({'file':name,'line':row['line'],'before':row['before'],'after':after,'fingerprint':original,'manual':key in authored,**({'beforeVersions':versions} if versions else {})})
        changed.append({**row,'after':after,'manual':key in authored})
    # Never overwrite concurrent manuscript changes.
    previous={}
    if (WORK/'applied-edits.json').exists():
        for row in load(WORK/'applied-edits.json'):previous.setdefault(row['file'],[]).append(row)
    for name in by_name:
        expected=(WORK/'manuscripts-before'/name).read_text(encoding='utf-8-sig').splitlines()
        for row in previous.get(name,[]):expected[row['line']-1]=row['after']
        assert (SRC/name).read_text(encoding='utf-8-sig').splitlines()==expected,(name,'Concurrent manuscript change needs a merge')
    for name,edits in by_name.items():
        original=(WORK/'manuscripts-before'/name).read_text(encoding='utf-8-sig')
        current=original
        lines=current.splitlines(keepends=True)
        for n,old,new in edits:
            ending='\r\n'if lines[n-1].endswith('\r\n')else'\n'if lines[n-1].endswith('\n')else''
            assert lines[n-1].rstrip('\r\n')==old;lines[n-1]=new+ending
        (SRC/name).write_text(''.join(lines),encoding='utf-8',newline='')
    dump(ROOT/'tools/v4_voice_revisions_20261107.json',{'policy':'Line-specific original fingerprints; only exact current line matches. Preserve published event IDs without colliding with other identical replies. No routing/line count changes.','revisions':revisions})
    dump(WORK/'applied-edits.json',changed)
    dump(WORK/'progress.json',{'phase':'source-applied','baselineRows':len(before['rows']),'manualEdits':manual,'spacingOnly':spacing,'filesChanged':len(by_name),'manualBatches':batches,'applied':True,'literaryAcceptance':False})
    print(json.dumps({'manualEdits':manual,'spacingOnly':spacing,'files':len(by_name)},ensure_ascii=False))
def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','excerpt','apply']);p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int,default=40);a=p.parse_args()
    if a.mode=='prepare':prepare()
    elif a.mode=='excerpt':excerpt(a.start,a.count)
    else:apply()
if __name__=='__main__':main()
