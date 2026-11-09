"""Conservative source-bound V4 acting. Never scores emotion or changes identity.
Publisher calls build_acting once, then bind_node before dropping source.line.
"""
import copy,hashlib,json,re
from pathlib import Path
from build_v4_story import ROOT,Source,SPEAKERS,speaker_line

# These pose meanings were checked against spec12, art/poses.json and current
# export sources. No K, M or X pose is a fallback for a scene/identity reveal.
RULES=[
 ('U2','notebook-writing',r'수첩에.{0,15}(적는다|쓴다|적고 있다)',{'mio'}),
 ('U4','finger-snap',r'손가락을.{0,5}튕긴다',{'ken'}),
 ('U6','finger-to-lips',r'(손가락|검지)를.{0,6}입(술|가)에.{0,6}(댄다|가져간다)',{'riku'}),
 ('U1','current-salute',r'(손을.{0,6}이마에.{0,6}(댄다|올린다)|경례한다)',{'taiga'}),
 ('U3','current-wristwatch-check',r'손목시계를.{0,5}(본다|확인한다|들여다본다)',{'akari'}),
 ('U6','short-nod',r'짧게.{0,5}고개를.{0,5}끄덕',{'satsuki'}),
 ('T02','both-hands-on-podium',r'(두 손|양손).{0,18}(증언대|의논석).{0,10}(짚|내려친)|(증언대|의논석).{0,18}(두 손|양손).{0,10}(짚|내려친)',None),
 ('T04','actual-recoil',r'(움찔한다|몸을 뒤로 뺀다|뒤로 (한 |반 )?발 물러(선다|난다))',None),
 ('T01','points-at-interlocutor',r'(맞은편|상대)를.{0,6}손가락으로 가리킨다|손가락으로.{0,6}(맞은편|상대)를 가리킨다',None),
 ('T03','actual-nod',r'고개를.{0,8}끄덕(인다|이며|거린다)',None),
 ('C07','explicit-wailing',r'(울음을 터뜨린다|소리 내어 운다|통곡한다|엉엉 운다)',None),
 ('C06','visible-tears',r'(눈물이 맺힌다|눈물이 고인다|눈가가 젖는다|눈물을 흘린다)',None),
 ('C11','explicit-fear',r'(겁에.{0,8}떤다|공포에.{0,8}움츠|무서워.{0,8}떤다)',None),
 ('C10','explicit-embarrassment',r'(부끄러워|수줍어).{0,12}(볼|얼굴).{0,7}붉',None),
 ('C05','explicit-anger',r'(화를 낸다|분노를 터뜨린다|이를 악문다)',None),
 ('C04','explicit-surprise',r'(놀라서.{0,8}물러|눈을 크게 뜬다|놀란 얼굴로)',None),
 ('C09','visible-nervous-sweat',r'(식은땀을 흘린다|진땀을 흘린다)',None),
 ('C03','explicit-big-laugh',r'(크게 웃는다|소리 내어 웃는다|배를 잡고 웃는다)',None),
 ('C02','explicit-small-smile',r'(미소를 짓는다|미소 짓는다|작게 웃는다|짧게 웃는다|조금 웃는다|웃는다|웃으며)',None),
 ('C08','hand-on-chin',r'턱을.{0,4}(괴고|괴며|짚고)|턱에.{0,4}손을.{0,4}(댄다|얹는다)',None),
 ('C13','actual-side-glance',r'(곁눈질한다|눈을 가늘게 뜬다|의심스러운 눈으로)',None),
 ('C14','actual-sigh',r'한숨을.{0,6}(쉰다|내쉰다)',None),
 ('C12','explicit-resolve',r'결연한 (얼굴|표정|목소리)|결의를 다진다',None),
]
# Reject production/counterfactual/history clauses rather than turning their
# vocabulary into a present facial expression.
UNSAFE=re.compile(r'(경로|선택|경우|이면|라면|때에는|때는|했을|했었다|했었|어제|그제|지난|이전|회상|떠올|기억|사진 속|그림 속|녹음|재생|원고|대본|분기|조건|미열람|지문|연기|흉내|처럼|듯이|하려다|려다가|려던|웃는 척|웃으려|비웃|억지|않|못|아니|없|멈춘|그친|그만|굳어|사라진|5년|몇 년 전|그때|옛날|어릴|기억 속|당시)')
NAMES=sorted(SPEAKERS,key=len,reverse=True)
SUBJECT=re.compile('('+'|'.join(map(re.escape,NAMES))+r')(?:가|는|은|이)(?=\s|[가-힣])')
BLOCKED={('koto','T02'):'The corrected T02 retains one held clipboard; it cannot depict both authored hands braced on a podium.',('ken','C02'):'The selected sprite holds the pendulum; smile alone cannot prove a presently-held prop.',('haruka','C14'):'Selected sprite has camera put away; a sigh alone cannot prove its current storage state.'}


def normal(text):
    return re.sub(r'\s+','',text.replace('【','').replace('】','').replace('〔','').replace('〕',''))


def own_clauses(direction,name):
    # Each sentence must explicitly assign its subject. Never inherit the
    # previous actor or a pronoun across a new speaker/action sentence.
    for sentence in re.split(r'[.!?。]\s*',direction.strip('()（） ')):
        matches=list(SUBJECT.finditer(sentence))
        for i,match in enumerate(matches):
            if match[1]!=name:continue
            clause=sentence[match.end():matches[i+1].start() if i+1<len(matches) else len(sentence)]
            if not UNSAFE.search(clause):yield clause.strip()


def direction_choice(direction,name,actor):
    if UNSAFE.search(direction) and any(x in direction for x in ('경로','선택','경우','이면','라면','원고','대본','미열람','회상','떠올','사진 속','그림 속','5년','그때','옛날','어릴','기억 속','당시')):return None
    for clause in own_clauses(direction,name):
        for suffix,reason,pattern,actors in RULES:
            if actors and actor not in actors:continue
            if re.search(pattern,clause):return suffix,reason,clause
    return None


def speech_choice(text,delivery):
    # Direct present speech acts only: no question->confusion, apology->cry,
    # acceptance->smile or exclamation->anger substitutions.
    if any(q in text for q in ('"','“','”','「','」','『','』')):return None
    if re.fullmatch(r'(동의합니다|동의해|그 말에 동의해|그 점에는 동의합니다)[.!。]*',text.strip()):return 'T03','explicit-current-agreement',text
    if re.match(r'^(그건 틀렸어!|그 말은 틀렸습니다!|이의 있어!|이의 있습니다!)',text.strip()):return 'T01','explicit-forceful-objection',text
    if re.fullmatch(r'(하아|휴|후우)[….。]+',text.strip()):return 'C14','audible-current-sigh',text
    # Explicit author delivery only; current source tags are mostly body/mono.
    for marker,suffix in [('크게웃음','C03'),('작게웃음','C02'),('분노','C05'),('식은땀','C09'),('울먹임','C06'),('통곡','C07')]:
        if re.search(r'[·(/（]'+marker+r'[)）\]]?$',delivery):return suffix,'explicit-current-delivery',delivery
    return None


def build_acting():
    manifest_path=ROOT/'Game/Assets/Art/court_figures/manifest.json'
    exported=ROOT/'Game/Saved/court-figures-export.json'
    assets=json.loads(manifest_path.read_text(encoding='utf-8'));selections=json.loads(exported.read_text(encoding='utf-8'))
    valid={}
    for key,row in assets.items():
        actor=key.split('_',1)[0]
        if actor not in SPEAKERS.values():continue
        if key!=actor and not re.fullmatch(re.escape(actor)+r'_(C(?:0[2-9]|1[0-4])|T0[1-4]|U[1-6])',key):continue
        source=selections.get(key,{}).get('source','')
        if not source or not (ROOT/source).is_file():raise ValueError('Missing exact selected HD acting source: '+key)
        for field in ('texture','back'):
            if not (ROOT/'Game'/row[field]).is_file():raise ValueError('Missing runtime acting export: '+key)
        valid[key]={**row,'selectedHdSource':source}
    by_source={};source_hashes={};raw_speech={}
    for path in sorted((ROOT/'docs/design/rewrite_v4').glob('*.md')):
        s=Source(path);source_hashes[s.name]=s.hash
        for i,raw in enumerate(s.lines,1):
            event=speaker_line(raw)
            if not event or event.get('mono') or any(k in event.get('delivery','') for k in ('회상','복원','방송')):continue
            if re.search(r'5년|과거|회상|복원|어린|녹음|영상|사진 속',s.ref(i)['heading']):continue
            actor=event['actor'];name=event['speaker'];raw_speech[s.name+':'+str(i)]={'sourceActor':actor,'sourceSpeaker':name,'sourceDelivery':event.get('delivery',''),'utterance':event['text'],'source':s.ref(i),'quote':raw};chosen=speech_choice(event['text'],event.get('delivery',''))
            proof_line=i;quote=raw
            # Only the immediately previous visible source item can supply a
            # current body action. A heading or dialogue breaks the relation.
            previous=i-1
            while previous>0 and not s.lines[previous-1].strip():previous-=1
            if previous>0 and s.lines[previous-1].strip().startswith(('(','（')):
                d=s.lines[previous-1].strip();direct=direction_choice(d,name,actor)
                if direct:chosen=direct;proof_line=previous;quote=d
            if not chosen:continue
            suffix,reason,clause=chosen
            by_source[s.name+':'+str(i)]={'sourceActor':actor,'sourceSpeaker':name,'sourceDelivery':event.get('delivery',''),'utterance':event['text'],'suffix':suffix,'basis':reason,'clause':clause,'source':s.ref(proof_line),'quote':quote,'utteranceSource':s.ref(i)}
    # Explicit native debate target is a present testimony/support speech act,
    # even when its asserted fact concerns the past. It never certifies truth,
    # emotion or judgment, and applies only to an actual bound target line.
    claims={}
    native=ROOT/'data/v4_story/native_tasks.json'
    if native.exists():
        def walk(value):
            if isinstance(value,list):
                for x in value:walk(x)
            elif isinstance(value,dict):
                source=value.get('source',{});source=source if isinstance(source,dict) else {};key=source.get('file','')+':'+str(source.get('line',''))
                if value.get('kind') in ('weak','agree') and key in raw_speech and normal(raw_speech[key]['utterance'])==normal(value.get('text','')):
                    claims[key]=raw_speech[key]
                for x in value.values():walk(x)
        walk(json.loads(native.read_text(encoding='utf-8')))
    return {'schemaVersion':1,'assets':valid,'bySource':by_source,'claimSources':claims,'sourceHashes':source_hashes,'blocked':{a+'_'+p:r for (a,p),r in BLOCKED.items()},'policy':{'baseFallback':True,'randomOrCyclicSelection':False,'changesIdentity':False,'usesKMX':False,'monoOrHistoricalVoiceGetsPortrait':False,'stagePersistsAcrossOtherSpeakers':False,'sourceBoundIsNotRuntimeVisualAcceptance':True}}


_DEFAULT=None

def bind_node(node,acting=None):
    """Copy and bind say/debate/queue records; original identity fields survive.
    Recursive dictionaries cover native intro/wrong/success/line/pair queues.
    Apply BEFORE runtime publisher compact() removes source.line.
    """
    global _DEFAULT
    if acting is None:
        if _DEFAULT is None:_DEFAULT=build_acting()
        acting=_DEFAULT
    if isinstance(node,list):return [bind_node(x,acting) for x in node]
    if not isinstance(node,dict):return node
    out={k:bind_node(v,acting) for k,v in node.items()}
    if out.get('pose') or out.get('mono') or not isinstance(out.get('text'),str) or not isinstance(out.get('actor'),str):return out
    source=out.get('source',{});source=source if isinstance(source,dict) else {};lookup=source.get('file','')+':'+str(source.get('line',''))
    if source.get('fileSha256') and source['fileSha256']!=acting['sourceHashes'].get(source.get('file')):return out
    record=acting['bySource'].get(lookup)
    if record and normal(record['utterance'])!=normal(out['text']):record=None
    if record is None and out.get('kind') in ('weak','agree'):
        claim=acting.get('claimSources',{}).get(lookup)
        target=out.get('weak',{});word=target.get('word','') if out.get('kind')=='weak' else out.get('text','')
        valid_target=(out.get('kind')=='weak' and bool(word) and bool(target.get('answer')) and word in out['text']) or (out.get('kind')=='agree' and bool(out.get('agree')))
        if claim and valid_target and normal(claim['utterance'])==normal(out['text']):
            record={**claim,'suffix':'T03' if out['kind']=='agree' else 'T02','basis':'explicit-bound-support-utterance' if out['kind']=='agree' else 'explicit-bound-testimony-utterance','clause':out['text']}
    if not record:return out
    actor=out['actor'];appearance=out.get('appearanceActor',actor)
    if actor not in SPEAKERS.values() or appearance not in SPEAKERS.values():return out
    if actor!=record['sourceActor'] and not (actor=='ken' and record['sourceActor']=='sora' and '켄의몸' in record.get('sourceDelivery','').replace(' ','')):return out
    suffix=record['suffix']
    # Unique U gestures belong to the literal character, not a body-swapped
    # controller or a disguise. Common C/T acting may use its physical body.
    if suffix.startswith('U') and (actor!=record['sourceActor'] or appearance!=actor):return out
    key=appearance+'_'+suffix
    if key not in acting['assets'] or key in acting['blocked']:return out
    # Koto's corrected T02 holds one clipboard with her left arm; it cannot
    # depict an authored action using both hands on a podium.
    if appearance=='koto' and suffix=='T02':return out
    out['pose']=key
    out['acting']={'basis':record['basis'],'source':record['source'],'quote':record['quote'],'ownCurrentClause':record['clause'],'sourceSpeaker':record['sourceSpeaker'],'sourceActor':record['sourceActor'],'physicalActor':actor,'appearanceActor':appearance,'selectedHdSource':acting['assets'][key]['selectedHdSource'],'identityUnchanged':True,'poseDoesNotJudgeOrDisclose':True}
    return out


if __name__=='__main__':
    import sys
    if '--stdin-json' in sys.argv:
        payload=json.load(sys.stdin);json.dump(bind_node(payload,build_acting()),sys.stdout,ensure_ascii=False,separators=(',',':'))
    else:
        path=ROOT/'tools/v4_acting_index.json';d=build_acting();path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'selectedExportKeys':len(d['assets']),'sourceExpressionBindings':len(d['bySource']),'explicitNativeClaimSources':len(d['claimSources']),'output':str(path),'centralOutputsWritten':False},ensure_ascii=False))
