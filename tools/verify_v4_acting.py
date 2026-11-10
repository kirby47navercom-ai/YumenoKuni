"""Read-only acting bounds and full graph identity preservation."""
import collections,copy,json
from pathlib import Path
from v4_acting_bindings import ROOT,build_acting,bind_node,direction_choice,speech_choice

def strip_added(node):
 if isinstance(node,list):return [strip_added(x) for x in node]
 if not isinstance(node,dict):return node
 return {k:strip_added(v) for k,v in node.items() if k not in ('pose','acting')}


def main():
 a=build_acting();assert len(a['assets'])==384
 assert direction_choice('(린이 웃는다.)','린','rin')[0]=='C02'
 assert direction_choice('(린이 웃지 않는다.)','린','rin') is None
 assert direction_choice('(미오가 웃는다.)','린','rin') is None
 assert direction_choice('(A를 선택한 경로에서 린이 웃는다.)','린','rin') is None
 assert direction_choice('(린은 어제 웃었던 일을 말한다.)','린','rin') is None
 assert direction_choice('(5년 전 린이 웃는다.)','린','rin') is None
 assert direction_choice('(린이 웃는 척한다.)','린','rin') is None
 assert direction_choice('(미오가 수첩에 적는다.)','미오','mio')[0]=='U2'
 assert direction_choice('(린이 미오가 웃는 모습을 본다.)','린','rin') is None
 assert speech_choice('미안해.','린') is None and speech_choice('왜 그래?','린') is None
 assert speech_choice('동의합니다.','레이')[0]=='T03'
 # Exact-source synthetic caller: swap/body fields cannot change; U cannot cross bodies.
 key,r=next((k,v) for k,v in a['bySource'].items() if v['suffix']=='C02' and v['sourceActor']=='rin')
 file,line=key.rsplit(':',1);node={'type':'say','id':'fixture','actor':'rin','speaker':'린','text':r['utterance'],'source':{'file':file,'line':int(line)}}
 assert bind_node(node,a)['pose']=='rin_C02'
 body={**node,'actor':'ken','appearanceActor':'ken','speaker':'켄의 몸'};assert 'pose' not in bind_node(body,a)
 disguised={**node,'actor':'rin','appearanceActor':'rei'};assert bind_node(disguised,a)['pose']=='rei_C02'
 assert 'pose' not in bind_node({**node,'mono':True},a)
 assert 'pose' not in bind_node({**node,'actor':'sho'},a)
 assert 'pose' not in bind_node({**node,'source':{**node['source'],'fileSha256':'stale'}},a)
 assert 'pose' not in bind_node({**node,'text':'다른 실제 분기 발화'},a)
 assert bind_node(bind_node(node,a),a)==bind_node(node,a)
 for n in (body,disguised):
  b=bind_node(n,a)
  assert all(n.get(k)==b.get(k) for k in ('id','actor','appearanceActor','speaker','text','source'))
 for record in a['bySource'].values():
  source=(ROOT/'docs/design/rewrite_v4'/record['source']['file']).read_text(encoding='utf-8-sig').splitlines()
  assert source[record['source']['line']-1].strip()==record['quote'].strip()
 total=bound=0;suffix=collections.Counter();actors=collections.Counter();basis=collections.Counter();poses=set();chapter={}
 for path in (ROOT/'data/v4_story/chapters').glob('*.json'):
  g=json.loads(path.read_text(encoding='utf-8'));b=bind_node(g,a);assert strip_added(g)==strip_added(b)
  assert bind_node(b,a)==b
  ct=ct_bound=0
  for node in b['nodes'].values():
   if node.get('type')!='say':continue
   total+=1;ct+=1
   if 'acting' not in node:continue
   bound+=1;ct_bound+=1;poses.add(node['pose']);p=node['pose'].split('_',1)[1]
   suffix[p]+=1;actors[node['actor']]+=1;basis[node['acting']['basis']]+=1
   assert p[0] not in ('K','M','X')
   assert node['pose'].split('_',1)[0]==node.get('appearanceActor',node['actor'])
   assert node['acting']['identityUnchanged'] and node['acting']['poseDoesNotJudgeOrDisclose']
  chapter[path.stem]={'say':ct,'explicitSourceActing':ct_bound,'baseUninferred':ct-ct_bound}
 native=ROOT/'data/v4_story/native_tasks.json';native_bound=0
 if native.exists():
  g=json.loads(native.read_text(encoding='utf-8'));b=bind_node(g,a);assert strip_added(g)==strip_added(b)
  def count(x):
   if isinstance(x,list):return sum(count(v) for v in x)
   if isinstance(x,dict):return int('acting' in x)+sum(count(v) for k,v in x.items() if k!='acting')
   return 0
  native_bound=count(b)
 report={'status':'PASS','selectedExistingExports':384,'sourceBindings':len(a['bySource']),'chapterSay':total,'explicitSourceActing':bound,'baseUninferred':total-bound,'posesUsed':len(poses),'byPose':dict(suffix),'byPhysicalActor':dict(actors),'byBasis':dict(basis),'byChapter':chapter,'nativeQueueAndLineBindings':native_bound,'sourceBoundNotRuntimeAcceptance':True,'identityOrRoutesChanged':False,'gameExecuted':False,'centralOutputsWritten':False}
 (ROOT/'tools/v4_acting_distribution.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
