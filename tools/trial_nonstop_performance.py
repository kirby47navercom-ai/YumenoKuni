"""Nonstop cues belong to utterances, not answer status or expression IDs."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REVIEWED = json.loads((ROOT/'data/presentation/nonstop_speech_reviewed.json').read_text(encoding='utf-8'))
# lighting, camera, perspective, face; choreography is the profile itself.
STYLES = {
 'reason': ('measured',0,-9,'gothica1/GothicA1-Regular.ttf'),
 'infer': ('measured',6,12,'dohyeon/DoHyeon-Regular.ttf'),
 'qualify': ('measured',7,-12,'gothica1/GothicA1-Bold.ttf'),
 'compare': ('measured',8,14,'gugi/Gugi-Regular.ttf'),
 'question': ('measured',7,17,'songmyung/SongMyung-Regular.ttf'),
 'recall': ('measured',4,-8,'gowunbatang/GowunBatang-Regular.ttf'),
 'correct': ('measured',6,-14,'gothica1/GothicA1-Bold.ttf'),
 'deny': ('assertive',11,15,'blackhansans/BlackHanSans-Regular.ttf'),
 'insist': ('assertive',11,-16,'blackhansans/BlackHanSans-Regular.ttf'),
 'drop': ('assertive',10,19,'blackhansans/BlackHanSans-Regular.ttf'),
 'hesitate': ('uneasy',4,-7,'nanumpenscript/NanumPenScript-Regular.ttf'),
 'regret': ('regret',4,8,'gowunbatang/GowunBatang-Regular.ttf'),
 'suspect': ('suspect',7,-13,'songmyung/SongMyung-Regular.ttf'),
 'tease': ('measured',6,15,'kiranghaerang/KirangHaerang-Regular.ttf'),
 'address': ('measured',0,7,''),
 'still': ('measured',0,0,''),
}
OVERRIDES = {
 'v4:181:T1-NS-A03:e:67110db471a1:1':('qualify','Unknown start time limits one part of the ordering.'),
 'v4:181:T1-NS-A03:e:70f96074edf2:1':('tease','Dry conditional concession, not distress.'),
 'v4:181:T1-NS-A03:e:649e148bd5bd:1':('infer','Sweeping inference from a limited unknown.'),
 'v4:181:T1-NS-A03:e:1830ada6783b:1':('correct','Contrasts missing time with the surviving record.'),
 'v4:181:T1-NS-A03:e:67372888ab88:1':('compare','Contrasts the two candidate orders.'),
 'v4:181:T1-NS-A03:e:af6ebef1e726:1':('reason','Separates categories of uncertainty.'),
 'claude:x:T1-NS-A03:1':('question','Proposes a specific test of elapsed time.'),
 'claude:x:T1-NS-A03:2':('drop','Words descend once when describing the fall.'),
 'v4:182:T2-NS-A06:e:6eb3b11d43f1:1':('infer','Infers an uncovered alternative from observers facing one way.'),
 'v4:182:T2-NS-A06:e:8cbda7cad57d:1':('deny','Rejects an overstatement of the speaker own claim.'),
 'v4:182:T2-NS-A06:e:7bc8b34ccea5:1':('correct','Restores the distinction between observed intervals.'),
 'v4:182:T2-NS-A06:e:dd8122b17f90:1':('infer','Generalizes from one person limited coverage.'),
 'v4:182:T2-NS-A06:e:1a7ae08a8737:1':('question','Challenges whether partial observations can be combined.'),
 'v4:182:T2-NS-A06:e:ddec4794c813:1':('reason','Pairs observers with their doors.'),
 'claude:x:T2-NS-A06:1':('qualify','Affirms one observation while disclaiming another.'),
 'claude:x:T2-NS-A06:2':('recall','Direct first-person observation.'),
 'claude:x:T2-NS-A06:3':('tease','Provocative generalization delivered lightly.'),
 'claude:x:T2-NS-A06:4':('insist','Forcefully pushes the uncovered-door claim.'),
 'v4:163:T1-LIE-01:e:f60f0091fcc8:1':('recall','Quotes the earlier claim.'),
 'v4:163:T1-LIE-01:e:240765b8fce6:1':('recall','Adds a second quoted detail.'),
 'v4:163:T1-LIE-01:e:a1a476e5a82d:1':('reason','Establishes the later common opportunity.'),
 'v4:163:T1-LIE-01:e:e8d428dc5d57:1':('suspect','Suggests a later opportunity for substitution.'),
 'claude:x:T1-LIE-01:1':('hesitate','Stammering self-defence, not floating letters.'),
 'claude:x:T1-LIE-01:2':('tease','Suggestive comment aimed at the preceding defence.'),
 'claude:x:T1-LIE-01:3':('recall','Reminds the group of a shared visit.'),
 'claude:x:T1-LIE-01:4':('suspect','Turns opportunity into an accusation of concealment.'),
 'v4:182:T2-NS-A09:e:3c61b00fae4b:1':('correct','Denies evidence for the proposed fall; not a falling performance.'),
 'v4:182:T2-NS-A09:e:ce396a463382:1':('recall','Recalls a wider observation, not an emotional denial.'),
 'v4:185:T5-NS-A01:e:d165df92aaf7:1':('qualify','Admits contact while limiting what that establishes.'),
 'claude:x:T3-NS-A11:4':('reason','Explains what the absence of a test establishes.'),
}
FOLLOW = {
 'v4:181:T1-NS-A03:e:649e148bd5bd:1':('U5',.54),
 'v4:182:T2-NS-A06:e:dd8122b17f90:1':('C09',.58),
 'v4:163:T1-LIE-01:e:240765b8fce6:1':('U5',.60),
}
def choose(row):
 if row['id'] in OVERRIDES:return OVERRIDES[row['id']]
 if row['id'] in REVIEWED:
  cue=REVIEWED[row['id']]
  assert cue['text']==row['text'], 'Speech changed: review its cue again: '+row['id']
  return cue['profile'],cue['reason']
 t=row['text']
 rules=[
  ('regret',('미안','후회','내 잘못','내 탓'),'Explicit regret or responsibility.'),
  ('hesitate',('저, 저','저는 정말','모, 몰','그, 그','아, 아니','무서','두려'),'Explicit hesitation or fear.'),
  ('drop',('넘어졌','떨어졌','미끄러졌','추락'),'Describes a fall or slip.'),
  ('deny',('안 했','안했','아니라고','말한 적 없','그런 뜻이 아니'),'Rejects an attributed statement.'),
  ('correct',('그게 아니라','그건 아니','정정','다르','잘못','틀렸'),'Corrects a premise or distinction.'),
  ('suspect',('숨겼','숨길','속였','일부러','수상','의심','거짓말'),'Questions intent or credibility.'),
  ('compare',('먼저인지','어느 쪽','둘 중','각각','반대로','비교','서로 다른'),'Contrasts alternatives or counterparts.'),
  ('question',('?','？'),'Asks or challenges a premise.'),
  ('insist',('!','！'),'Audible insistence in the authored line.'),
  ('qualify',('뿐','까지만','전부는','모르','수 없어','수는 없','한 건 아니'),'Limits scope or certainty.'),
  ('infer',('그러면','그렇다면','그럼','결국','니까','겠네','잖아'),'Draws a consequence from a claim.'),
  ('recall',('봤','보았','들었','기억','했어','했어요','했지','있었','없었'),'Reports a remembered action or observation.'),
  ('reason',('기록','순서','항목','대응','조건','구간','확인','나눠','증거'),'Organizes observations or relations.'),
 ]
 for profile,phrases,reason in rules:
  if any(p in t for p in phrases):return profile,reason
 return 'address','Direct statement: speaker face, grouped entrance and camera framing.'
def apply(direction,tasks):
 ledger=[]
 for tid,task in tasks.items():
  debate=task.get('debate') or {}
  if debate.get('kind')!='nonstop':continue
  rows=list(debate.get('lines') or [])
  for extra in reversed(direction.get('extra',{}).get(tid,[])):rows.insert(extra.get('after',-1)+1,extra)
  for row in rows:
   e=direction['debate'].get(row['id'])
   if not e:continue
   profile,reason=choose(row);tone,shot,yaw,font=STYLES[profile];follow,phase=FOLLOW.get(row['id'],('',.5))
   # Do not inherit the old expression-ID-wide motion, swirl or follow pose.
   for k in ('delivery','composition','followAt','followPose','shot','yaw','font','fx'):e.pop(k,None)
   # One node: preserve the engine's 10,000-node data budget.
   e['acting']='|'.join(map(str,(tone,profile,follow,phase,shot,yaw,font)))
   ledger.append({'task':tid,'id':row['id'],'actor':row.get('actor'),'text':row['text'],'profile':profile,'reason':reason,'font':font or 'authored-speaker','reviewedOverride':row['id'] in OVERRIDES or row['id'] in REVIEWED})
 (ROOT/'docs/analysis/v3_rebuild/nonstop_speech_cues_20261105.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
 return len(ledger)
