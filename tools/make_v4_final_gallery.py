"""Offline review index. Story content is opt-in; this is not the game."""
from pathlib import Path
import json,html
R=Path(__file__).resolve().parents[1];O=R/'art/v4_production/completion'
def read(p):return json.loads((R/p).read_text(encoding='utf8'))
c=read('art/v4_production/completion/final_catalog.json');entries=[]
def add(group,ident,file,spoiler=False,**extra):entries.append(dict(group=group,id=ident,file=file,spoiler=spoiler,**extra))
for s in read(c['ui_layouts'])['screens']:add('UI 화면',s['id'],s['fixture_image'],source=s['source'])
for p in c['ui_components']:
 for a in read(p)['assets']:add('UI 부품',a['id'],a['file'],source=a['source'])
for a in read(c['gift_icons'])['assets']:add('선물',a['id']+' '+a['name'],a['webp'])
for a in read(c['characters'])['assets']:add('인물',a['id'],a['webp'])
for a in c['backgrounds']:add('배경 판',a['id'],a['delivery'],True)
for a in read(c['world_maps'])['assets']:add('지도',a['id'],a['file'],True,source=a['source'])
for a in c['base_props']:add('3D 기본 소품',a['id'],a['file'],True,model=True)
for a in c['spaces']:
 if a.get('file'):add('3D 공간',a['id'],a['file'],True,model=True)
for a in c['story_cg']:add('스토리 CG',a['logical_id'],a['webp'],True)
for a in c['reconstruction_candidates']:add('만화 후보',a['id'],a['webp'],True,caption=a['caption'])
for a in c['reconstruction_pages']:add('만화 완성 페이지','chapter_'+str(a['chapter']),a['webp'],True)
for a in c['inspection_views']:add('조사 상세',a['id'],a['webp'],True)
for a in c.get('forensic_details',[]):add('현장 단서 확대',a['id'],a['webp'],True,caption=a['caption'])
for a in c['effects']:
 frames=a['frames'];files=[x.get('webp',x.get('file')) for x in frames]
 add('효과',a['id'],files[len(files)//2],frames=files,fps=a['fps'],opacity=a.get('frame_opacity',[1]*len(files)))
for a in c['additional_model_files']:add('3D 파일',a['id'],a['file'],True,model=True)
for a in read(c['new_original_audio'])['assets']:add('새 효과음',a['id'],a['ogg'],audio=True)
data=json.dumps(entries,ensure_ascii=False).replace('</','<\\/')
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>유메노쿠니 에셋 검수</title>
<style>body{background:#14131b;color:#f3ead9;font:16px system-ui;margin:32px}h1{border-bottom:4px solid #9770cf;padding-bottom:15px}button,input,select{font:inherit;padding:10px;background:#25212c;color:inherit;border:1px solid #9770cf;border-radius:5px}label{display:inline-block;margin:12px}#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px}article{background:#25212c;padding:15px;border-radius:8px;min-width:0}img{width:100%;height:210px;object-fit:contain;background:#655e6b}a{color:#c8b2e9}p{line-height:1.5}small{display:block;overflow-wrap:anywhere}audio{width:100%}.muted{color:#b2aabc}</style>
<h1>유메노쿠니 · 에셋 검수</h1><p>제작 파일과 배치 예시예요. 게임 실행 화면이나 구현 완료 판정이 아니에요. 새 그림은 내장 생성·로컬 4배, UI는 편집 가능한 벡터, 3D는 Blender로 제작했어요. NAI 추가 호출은 없어요.</p>
<p><a href="final_catalog.json">전체 선택본 목록</a> · <a href="README.md">제작·검수 기록</a> · <a href="final_technical_qa.json">파일 검사</a></p>
<select id="group"></select> <input id="search" placeholder="파일 이름 검색" aria-label="파일 이름 검색"><label><input type="checkbox" id="spoilers"> 스토리·사건·정답 그림 표시</label><p id="count" class="muted"></p><div id="grid"></div>
<script>const data=DATA,root='../../../',sel=document.querySelector('#group'),grid=document.querySelector('#grid');let timers=[];for(const name of ['전체',...new Set(data.map(x=>x.group))]){let o=document.createElement('option');o.textContent=name;sel.append(o)}
function render(){timers.forEach(clearInterval);timers=[];grid.replaceChildren();let items=data.filter(a=>(!a.spoiler||document.querySelector('#spoilers').checked)&&(sel.value==='전체'||a.group===sel.value)&&a.id.toLowerCase().includes(document.querySelector('#search').value.toLowerCase()));document.querySelector('#count').textContent=items.length+'개 파일 · 아래 그림을 누르면 원본 출력이 열려요';for(const a of items){let card=document.createElement('article'),title=document.createElement('h3');title.textContent=a.id;card.append(title);if(a.audio){let el=document.createElement('audio');el.controls=true;el.preload='none';el.src=root+a.file;card.append(el)}else if(a.model){let el=document.createElement('a');el.href=root+a.file;el.textContent='GLB 파일 열기';card.append(el)}else{let link=document.createElement('a'),img=document.createElement('img');link.href=root+a.file;img.src=root+a.file;img.loading='lazy';img.alt=a.id;link.append(img);card.append(link);if(a.frames){let button=document.createElement('button');button.textContent='효과 재생';let timer=null;button.onclick=()=>{if(timer){clearInterval(timer);timer=null;button.textContent='효과 재생';return}let i=0;button.textContent='정지';timer=setInterval(()=>{img.src=root+a.frames[i];img.style.opacity=a.opacity[i];i=(i+1)%a.frames.length},1000/a.fps);timers.push(timer)};card.append(button)}}if(a.caption){let p=document.createElement('p');p.textContent=a.caption;card.append(p)}if(a.source){let source=document.createElement('a');source.href=root+a.source;source.textContent='편집 원본';card.append(source)}let path=document.createElement('small');path.textContent=a.file;card.append(path);grid.append(card)}}sel.onchange=render;document.querySelector('#search').oninput=render;document.querySelector('#spoilers').onchange=render;render();</script>'''.replace('DATA',data)
(O/'gallery.html').write_text(page,encoding='utf8');print('Offline gallery indexed',len(entries),'entries; story hidden initially')
