"""Geographical wording changes required by the separate themed park levels.

Stable node IDs/line counts/choices/evidence/room-local geometry stay unchanged.
The former wheel-side waiting room is the mask observatory's waiting room;
the wheel itself belongs to the later starlight district.
"""
from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1]
PAIRS=[
 ('거울 미로·대관람차·드림 시어터','거울·가면 공원의 거울 미로·가면 전망대·드림 시어터'),
 ('거울 미로·대관람차·극장의 구역 잠금','거울·가면 공원 안의 미로·전망대·극장 구역 잠금'),
 ('대관람차 하단의 정비 대기실','가면 전망대 하단의 정비 대기실'),
 ('대관람차 밑 대기실','가면 전망대 밑 대기실'),
 ('대관람차의 안내도','가면 전망대의 안내도'),
 ('관람차 안내도','가면 전망대 안내도'),
 ('대관람차 탐색 결과','가면 전망대 탐색 결과'),
 ('관람차의 실제 접근/시야','가면 전망대의 실제 접근/시야'),
 ('미로 입구와 관람차 장식 조명','미로 입구와 가면 전망대 장식 조명'),
 ('대관람차군요.','가면 전망대군요.'),
 ('그러면 타 보면 알겠네.','그러면 올라가 보면 알겠네.'),
 ('운행 확인부터 해야지.','올라갈 수 있는 데부터 확인해야지.'),
 ('네가 안 탈 거면 내가 먼저 탈게.','네가 안 올라갈 거면 내가 먼저 갈게.'),
]
def text(value):
    for a,b in PAIRS:value=value.replace(a,b)
    return value
def adapt(node):
    source=node.get('source',{}).get('file','')
    if not source.startswith('13a'):return node
    for k in ['text','direction']:
        if isinstance(node.get(k),str):node[k]=text(node[k])
    return node
def main():
    work=R/'Game/Saved/park-levels-20261104';backup=work/'story-before';backup.mkdir(exist_ok=True);rows=[]
    for p in sorted((R/'docs/design/rewrite_v4').glob('13a*.md')):
        old=p.read_text(encoding='utf8');new=text(old)
        if new==old:continue
        target=backup/p.name
        if not target.exists():shutil.copy2(p,target)
        assert len(old.splitlines())==len(new.splitlines());p.write_text(new,encoding='utf8');rows.append({'file':p.relative_to(R).as_posix(),'before':hashlib.sha256(old.encode()).hexdigest(),'after':hashlib.sha256(new.encode()).hexdigest()})
    graph=R/'data/v4_story/chapters/3.json';g=json.loads(graph.read_text(encoding='utf8'));count=0
    for n in g['nodes'].values():
        before=json.dumps(n,ensure_ascii=False);adapt(n);count+=before!=json.dumps(n,ensure_ascii=False)
        source=n.get('source',{});p=R/'docs/design/rewrite_v4'/source.get('file','')
        if p.is_file()and source.get('file','').startswith('13a'):source['fileSha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    if not(backup/'chapter3.json').exists():shutil.copy2(graph,backup/'chapter3.json')
    graph.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    prior=json.loads((work/'story-geography.json').read_text(encoding='utf8'))if(work/'story-geography.json').exists()else{}
    (work/'story-geography.json').write_text(json.dumps({'files':rows or prior.get('files',[]),'nodesUpdated':count or prior.get('nodesUpdated',0),'stableIDs':True,'lineCountsPreserved':True,'clueRulesChanged':False,'reason':'Wheel opens with starlight district; chapter3 waiting-room geometry and viewing/stair/control-room distinctions remain in mask observatory.'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if __name__=='__main__':main()
