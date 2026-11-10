"""Whole-corpus mechanical screening; never certify literary quality by regex."""
import collections
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / 'Game/Saved/dialogue-audit-20261107'
OUT = ROOT / 'docs/analysis/dialogue_audit_20261107'
NAMES = {'미오','레이','소라','켄','나나','리쿠','아카리','유우','코토','사츠키','타이가','린','쇼','아이','하루카','카에데','래피'}
SAY = re.compile(r'^\[([^\]]+)\]\s*(.+)$')
PATTERNS = {
    'punctuationSpacing': re.compile(r'(?<=[가-힣])[.!?,](?=[가-힣])'),
    'clauseEnding': re.compile(r'(?:하고|해서|지만|는데|니까|으면|으며|면서|거나)[.!…]*$'),
    'sharedAbstractFrame': re.compile(r'(?:그 말은|뜻은 아니|그 말부터|같은 말|확인한|구분|조건|책임|판단)'),
}
def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1)+'\n',encoding='utf-8')
def clean(text):
    return re.sub(r'【|】|〔|〕|\*\*', '', text).strip().strip('"“”')
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source_files={}
    originals=[]
    for p in sorted((ROOT/'docs/design/rewrite_v4').glob('*.md')):
        raw=p.read_text(encoding='utf-8-sig')
        lines=raw.splitlines()
        source_files[p.name]={'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'lines':lines}
        for n,line in enumerate(lines,1):
            m=SAY.match(line)
            if m and m[1].split('·')[0] in NAMES:
                originals.append({'file':p.name,'line':n,'speaker':m[1],'text':m[2]})
    shipped=read(WORK/'shipping-dialogue.json')
    counts=collections.Counter();by_actor=collections.defaultdict(collections.Counter)
    flags=[];unresolved_source=[];explicit_differences=[]
    for r in shipped:
        issues=[name for name,pattern in PATTERNS.items() if pattern.search(r['text'])]
        if len(r['text'])>85:issues.append('longUtterance')
        if not re.search(r'[.!?…？！。」』”"\)—]$',r['text']):issues.append('noTerminalPunctuation')
        counts.update(issues);by_actor[r['speaker']].update(issues)
        source=r.get('source') or {};file=source.get('file');line=source.get('line')
        source_line=None
        if file in source_files and isinstance(line,int) and 1<=line<=len(source_files[file]['lines']):
            source_line=source_files[file]['lines'][line-1]
            m=SAY.match(source_line)
            if not m or clean(m[2])!=clean(r['text']):
                source_body=clean(m[2] if m else source_line)
                stripped=lambda text:re.sub(r'\s','',clean(text))
                if stripped(r['text']) in stripped(source_body):category='excerpt-or-alternate-authored-format'
                elif not source.get('location'):category='generated-presentation-anchor-not-literal-quotation'
                elif '.stage.pairs[' in r['where']:category='scrum-pair-response-adaptation'
                elif ':late' in r['where'] or 'Late' in r['where'] or '배치' in source_line:category='authored-calendar-variant'
                else:category='changed-text-needs-generator-context'
                explicit_differences.append({'record':r,'sourceLine':source_line,'category':category,'status':'not automatically a missing line; verify generator transformation and intended presentation'})
        else:unresolved_source.append(r)
        flags.append({'id':r['id'],'source':source,'speaker':r['speaker'],'file':r['file'],'where':r['where'],'text':r['text'],'flags':issues,'mechanicalScreened':True,'literaryAcceptance':False})
    with (OUT/'utterance-screening.jsonl').open('w',encoding='utf-8') as f:
        for row in flags:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    # Inspect prose patterns with adjacent replies, never isolated suffix replacement.
    candidates=[]
    for who in sorted(NAMES):
        found=[r for r in shipped if r['speaker']==who and PATTERNS['sharedAbstractFrame'].search(r['text']) and (r.get('source') or {}).get('file') in source_files]
        found.sort(key=lambda r:(-len(PATTERNS['sharedAbstractFrame'].findall(r['text'])),r['source']['file'],r['source'].get('line',0)))
        for r in found[:3]:
            lines=source_files[r['source']['file']]['lines'];n=r['source']['line']
            candidates.append({'record':r,'context':lines[max(0,n-6):min(len(lines),n+5)],'reason':'Compare concrete request/reaction against abstract restatement and the speaker motive. This flag is not automatically an error.'})
    write(OUT/'contextual-voice-candidates.json',candidates)
    write(OUT/'source-differences.json',explicit_differences)
    write(OUT/'generated-or-unlocated-records.json',unresolved_source)
    direction=read(ROOT/'data/v4_story/trial_direction.json')
    followup=read(ROOT/'data/presentation/nonstop_followup.json')
    ownership=[]
    for row in unresolved_source:
        m=re.fullmatch(r'\$\.noise\.([^\[]+)\[(\d+)\]',row['where'])
        if m and row['file'].endswith('/trial_direction.json'):
            entries=direction.get('noise',{}).get(m[1],[])
            entry=entries[int(m[2])] if int(m[2])<len(entries) else None
            direct=entry is not None and entry['text']==row['text']
            extra=row['text'] in followup.get('tasks',{}).get(m[1],{}).get('extraNoise',[])
            owner='data/v4_story/trial_direction.json'if direct else 'data/presentation/nonstop_followup.json'if extra else 'published Assets/Data/v4_story/trial_direction.json; no same current-source slot'
            ownership.append({'file':row['file'],'where':row['where'],'text':row['text'],'owner':owner,'exact':direct or extra,'runtimeUseConfirmed':False})
    write(OUT/'generated-ownership.json',ownership)
    compiled=read(WORK/'compiled-korean-literals.json')
    compiled_flags=[]
    for row in compiled:
        issues=[name for name,pattern in PATTERNS.items()if pattern.search(row['literal'])]
        if issues:compiled_flags.append({**row,'flags':issues})
    write(OUT/'compiled-literal-screening.json',compiled_flags)
    result={
        'build':read(WORK/'shipping-inventory.json')['build'],
        'sourceManuscripts':len(source_files),'rawRecognizedSayRows':len(originals),
        'rawSayCharacters':sum(len(r['text'])for r in originals),
        'publishedUniqueUtterances':len(shipped),'publishedActorLabels':len(by_actor),
        'flags':dict(counts),'byActor':{name:dict(value)for name,value in by_actor.items()},
        'sourceTextOrLocationDifferences':len(explicit_differences),'generatedOrUnlocated':len(unresolved_source),
        'sourceDifferenceCategories':dict(collections.Counter(row['category']for row in explicit_differences)),
        'unlocatedRecordsResolvedToDirectionData':sum(row['exact']for row in ownership),
        'compiledKoreanLiterals':len(compiled),'compiledLiteralCandidates':len(compiled_flags),
        'sourceFiles':[{k:v for k,v in record.items()if k!='lines'}for record in source_files.values()],
        'scope':'All published speaker/text records and all current recognized manuscript say rows inventoried; mechanical screens are exhaustive over those sets. Entire campaign playthrough and line-by-line literary acceptance are not claimed.',
        'interpretation':{
            'punctuationSpacing':'Confirmed readability defect: adjoining Korean sentences/clauses have no separating space. Source addressed; not deletion of words.',
            'clauseEnding':'Review candidate, often intentional trailing speech, hesitation, or response to the preceding line. Do not automatically complete.',
            'sharedAbstractFrame':'Cross-speaker rhetorical similarity candidate. Polite technical speakers are not errors merely for formal language.',
            'noTerminalPunctuation':'Review lyrics, quoted documents and interruptions before changing. No blanket punctuation insertion.',
        },
        'manuscriptsChanged':False,'naturalnessCertified':False,'automatedFlagsAreNotCompletionPercent':True,
    }
    write(OUT/'corpus-audit.json',result)
    print(json.dumps({k:result[k]for k in ['build','sourceManuscripts','rawRecognizedSayRows','publishedUniqueUtterances','flags','sourceTextOrLocationDifferences','generatedOrUnlocated']},ensure_ascii=False))
if __name__=='__main__':main()
