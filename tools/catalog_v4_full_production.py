"""Map authored source IDs/staging mentions to production coverage. Counts are not acceptance."""
from pathlib import Path
from collections import Counter
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[1];DRAFT=ROOT/'docs/design/rewrite_v4'
OUT=ROOT/'art/v4_production/full';OUT.mkdir(parents=True,exist_ok=True)
sources=[];mentions=Counter();examples={};sections=[]
pattern=re.compile(r'([가-힣]{2,10}(?:실|홀|통로|광장|매점|정원|무대|수영장|미로|계단|회랑|전실|지하|옥상|복도|정문|창고|로비))')
for p in sorted(DRAFT.glob('*.md')):
    if not any(s in p.name for s in ['초고','보강','자유시간']):continue
    text=p.read_text(encoding='utf8')
    if not re.search(r'^\[[^\]]+\]',text,re.M):continue
    relative=p.relative_to(ROOT).as_posix();sourcehash=hashlib.sha256(p.read_bytes()).hexdigest()
    sources.append({'path':relative,'sha256':sourcehash})
    current=None
    for n,line in enumerate(text.splitlines(),1):
        if re.match(r'^#{2,3} ',line):
            current={'source':relative,'line':n,'heading':line.lstrip('# '),'staging':[]};sections.append(current)
        if line.startswith(('(','（')):
            if current:current['staging'].append({'line':n,'text':line})
            for word in pattern.findall(line):
                mentions[word]+=1;examples.setdefault(word,[])
                if len(examples[word])<3:examples[word].append({'source':relative,'line':n,'text':line})
report={'status':'authored source coverage only; no asset completion claim','source_count':len(sources),'sources':sources,'sections':sections,'place_mentions':[{'term':term,'count':count,'examples':examples[term]} for term,count in mentions.most_common()]}
(OUT/'source_catalog.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Sources',len(sources),'sections',len(sections))
print('Location staging terms:',mentions.most_common(65))
