"""Index actual native screenshot evidence without copying large PNGs."""
from pathlib import Path
import hashlib
import json
import re
import struct

ROOT=Path(__file__).resolve().parents[1]
SAVED=ROOT/'Game/Saved'
OUT=ROOT/'연출 모아보기'
KINDS={'nonstop':'논스톱 논의','lie':'거짓말·우소다마','panic':'패닉 논의',
       'showdown':'반론 쇼다운','mindmine':'발굴 이매지네이션','anagram':'섬광 애너그램',
       'scrum':'논의 스크럼','armament':'이론 무장','climax':'클라이맥스 추리',
       'vote':'인물 투표','person':'인물 지목','spot':'화면 지점 지목','bullet':'증거 제시',
       'choice':'정답 선택','reasoning':'추리 연결'}

def read(p):
    try:return json.loads(p.read_text(encoding='utf-8-sig'))
    except (OSError,ValueError):return None

def category(d,p):
    for k,v in KINDS.items():
        if k==p.parent.name or 'gpu-'+k+'-' in d:return '재판 · '+v
    if 'trial' in d:return '재판 · 논스톱 논의'
    if 'all-tasks' in d:return '재판 · 개별 과제'
    if 'mode-matrix' in d:return '재판 · '+KINDS.get(p.parent.name,p.parent.name)
    if 'ending' in d:return '결과·마무리'
    if 'choices' in d:return '일상·선택'
    if any(k in d for k in ('world','outdoor')):return '탐색·수사'
    if 'new-entry' in d:return '일상·대화'
    if any(k in d for k in ('display','startup','background','canvas-input','fps-options')):return '시작·메뉴'
    if 'scroll' in d:return '증거·문서'
    return '기타 화면 기록'

def main():
    OUT.mkdir(exist_ok=True)
    build=read(ROOT/'Game/build-result.json');current=build['id']
    rows=[];seen=set();issues=[]
    for d in sorted(SAVED.iterdir(),reverse=True):
        if not d.is_dir() or not d.name.startswith('native-'):continue
        if any(k in d.name for k in ('performance','cost','palette','diagnos','compat','delta','test','candidate','engine','migration','packet','transport','coverage','checkpoint')):continue
        report=read(d/'report.json')
        if not report or (not report.get('ok') and not report.get('shots')) or not report.get('build'):continue
        if report.get('shippingEngine') is False:continue
        stamp=report['build']
        if not isinstance(stamp,str):continue
        explicit={str(Path(s['file']).resolve()):s for s in report.get('shots',[]) if 'file' in s}
        paths=list(d.glob('*.png'))
        for sub in d.iterdir():
            if sub.is_dir() and sub.name not in ('package','State','Content','WebView2','Cache'):
                paths.extend(sub.glob('*.png'))
        for p in sorted(paths):
            if p.name in ('ui.png','scene-only.png') or '.ui.' in p.name or 'failure' in p.name:continue
            meta=explicit.get(str(p.resolve()),{})
            try:
                data=p.read_bytes()
                if data[:8]!=b'\x89PNG\r\n\x1a\n':continue
                w,h=struct.unpack('>II',data[16:24]);sha=hashlib.sha256(data).hexdigest()
            except OSError as e:issues.append(str(p));continue
            # Keep identical pixels from different versions only once per build.
            cat=meta.get('category') or category(d.name,p)
            snapshot=read(p.with_suffix('.ui.json'))
            if snapshot and any(v.get('id')=='LoadingLabel' for v in snapshot.get('rects',[])):
                cat='전환·로딩'
                meta={**meta,'label':'로딩 덮개 · '+p.stem,'spoiler':False}
            key=(stamp,cat,sha)
            if key in seen:continue
            seen.add(key)
            safe=cat=='시작·메뉴' and not any(k in p.stem for k in ('gallery','replay','ending','result'))
            label=meta.get('label') or (KINDS.get(p.parent.name,'')+' · '+p.stem).strip(' ·')
            proof=next((v for v in report.get('proofs',[]) if isinstance(v,dict) and v.get('image') and Path(v['image']).name==p.name),{})
            fixture=bool(meta.get('fixture') or report.get('fixture') or proof.get('fixture') or any(k in d.name for k in ('all-choices','all-tasks')))
            experimental=bool(report.get('experimental') or report.get('shippingGame') is False or report.get('gameModule') or report.get('gameContentOverrides'))
            rows.append({'id':hashlib.sha256(str(p).encode()).hexdigest()[:20],
                'path':p.relative_to(ROOT).as_posix(),'label':label,'category':cat,
                'build':stamp,'current':stamp==current and not experimental,'width':w,'height':h,
                'spoiler':meta.get('spoiler',not safe),'fixture':fixture,'experimental':experimental,
                'report':(d/'report.json').relative_to(ROOT).as_posix(),'sha256':sha})
    rows.sort(key=lambda r:(not r['current'],r['category'],r['path']))
    kinds={r['category'] for r in rows if r['current'] and r['category'].startswith('재판 · ')}
    manifest={'build':current,'scope':'현재 출하 빌드와 과거 네이티브 캡처 기록. 수정 중인 새 대본은 미반영. 정지 화면/일부 주요 프레임이며 음향·전환 전체 영상이나 전편 모든 프레임 촬영이 아님.',
        'rows':rows,'counts':{'total':len(rows),'current':sum(r['current'] for r in rows),'currentTrialTypes':len(kinds)},'readErrors':issues}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    html=OUT/'index.html'
    if html.exists():
        text=html.read_text(encoding='utf8')
        payload=json.dumps(manifest,ensure_ascii=False).replace('<','\\u003c')
        tag='<script id="capture-data" type="application/json">'+payload+'</script>'
        if '<script id="capture-data"' in text:
            text=re.sub(r'<script id="capture-data" type="application/json">.*?</script>',lambda _:tag,text,flags=re.S)
        else:text=text.replace('<script>\nlet data',tag+'\n<script>\nlet data')
        html.write_text(text,encoding='utf8')
    (OUT/'안내.md').write_text('# 실제 게임 연출 캡처\n\n현재 빌드: '+current+'\n\n'+manifest['scope']+'\n\nPNG는 원래 검증 폴더에 보존하고 갤러리에서 참조해요. 별도 대용량 복사를 만들지 않아요. 비공개 사건 화면은 갤러리의 스포일러 표시를 켜면 볼 수 있어요.\n',encoding='utf8')
    print(json.dumps(manifest['counts'],ensure_ascii=False))

if __name__=='__main__':main()
