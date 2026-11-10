"""Read-only, non-overlapping per-file cleanup plan. Never removes files."""
from pathlib import Path
from collections import Counter
import os, json, csv

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/analysis/storage_cleanup_2026-10-29'
OUT.mkdir(exist_ok=True)
def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
files={}
for parent, dirs, names in os.walk(ROOT):
    dirs[:]=[d for d in dirs if not d.startswith('_삭제대기_')]
    for name in names:
        p=Path(parent)/name
        try: files[p.relative_to(ROOT).as_posix()]=p.stat().st_size
        except OSError: pass
rows={}
def add(path,category,reason,retained,condition):
    if path in files and path not in rows:
        rows[path]={'path':path,'bytes':files[path],'category':category,'reason':reason,'retained':retained,'condition':condition}
def subtree(prefix,category,reason,retained,condition):
    for p in files:
        if p.startswith(prefix+'/'): add(p,category,reason,retained,condition)
catalog=read(ROOT/'art/v4_production/completion/final_catalog.json')
selected={x['logical_id']:x for x in catalog['story_cg']}
pair_audit=read(ROOT/'Game/Saved/storage-duplicate-audit-2026-10-29.json')
extra=ROOT/'Game/Saved/storage-additional-pairs-2026-10-29.json'
if extra.exists(): pair_audit['pairs']+=read(extra)['pairs']
for x in pair_audit['pairs']:
    if x['rgba_identical']:
        add(x['png'],'A_pixel_identical_png','RGBA 모든 픽셀과 치수 일치를 앞선 조사에서 확인',x['webp'],'PNG를 읽는 제작 스크립트/manifest를 WebP로 변경 후. 출력 픽셀 유지')
for p in files:
    if p.endswith('.blend1') and p[:-1] in files:
        add(p,'B_blender_backup','Blender 이전 저장 백업',p[:-1],'현재 .blend 유지. 이전 버전 복귀가 불필요할 때')
    if p.startswith('Game/Saved/') and '/WebView2/' in p:
        add(p,'C_test_browser_cache','자체 게임 검증 전용 WebView 프로필','같은 검증 폴더의 report.json과 캡처','해당 검증 플레이어 종료 후. 사용자 실제 세이브는 포함하지 않음')
built=read(ROOT/'Game/build-result.json')
exe=Path(built['executable']); current=exe.parent.relative_to(ROOT).as_posix()
for p in files:
    if p.startswith('Game/Builds/') and not p.startswith(current+'/'):
        add(p,'D_previous_build','현재 build-result 외 다시 만들 수 있는 개발 빌드',current,'현재 빌드 실행/집중 검증 성공 후. 공유 대상이 옛 경로를 필요로 하지 않아야 함')
overrides=read(ROOT/'art/space_v4/full_v2/interior_art_r4/manifest.json')['spaces']
for x in overrides:
    final=x['file']; name=Path(final).name
    for old in ['art/space_v4/full_v2/'+name,'art/space_v4/full_v2/interior_art_r3/'+name]:
        if old!=final:
            add(old,'E_superseded_3d_export','같은 공간 ID의 이전 마감/토폴로지 출력',final+' + art/space_v4/full_v2/space_finish_source.blend','r4 생성/검사 도구의 이전 GLB 입력 의존 해소 후. Blender 편집 원본 유지')
if 'art/space_v4/full_v2/park_exterior_r2.glb' in files:
    add('_삭제대기_2026-10-29/제작참조확인필요/art/space_v4/full_v2/park_exterior.glb','E_superseded_3d_export','공원 이전 출력','art/space_v4/full_v2/park_exterior_r2.glb','이전 출력으로 향하는 제작 참조를 현재 출력으로 변경 후')
for p in list(files):
    if p.startswith('art/cg_v4/builtin/') and p.endswith('.json'):
        try: meta=read(ROOT/p)
        except (ValueError,OSError): continue
        current_cg=selected.get(meta.get('logical_id'))
        if current_cg and meta.get('id')!=current_cg['selected_id']:
            old=meta.get('id','')
            for stem in ['art/cg_v4/builtin/'+old,'art/hd_v4/cg/builtin/'+old,'art/cg_v4/delivery/'+old]:
                for ext in ['.png','.webp']:
                    add(stem+ext,'F_rejected_cg_revision','최종 목록에서 같은 논리 컷의 다른 버전이 채택됨',current_cg['source']+' + '+current_cg['webp'],'현재 선택/갤러리를 정본으로 하고 이전 비교 이미지 참조 정리 후. 메타데이터 이력 유지')
for x in catalog['story_cg']:
    raw=x.get('raw_4x','')
    if raw and x.get('source') in files and x.get('webp') in files:
        for p in [raw,str(Path(raw).with_suffix('.webp')).replace('\\','/')]:
            add(p,'G_reproducible_cg_intermediate','원본과 최종 16:9 출력 사이에 있는 4배 중간 이미지',x['source']+' + '+x['webp'],'원본/로컬 확대기/보간 및 비율 설정 유지. 재제작 시 다시 확대 필요')
subtree('art/sprites_nai_v4','H_excluded_nai_poses','사용자 지시로 최종 채택에서 제외된 이전 NAI 포즈','art/hd_v4/masters + art/hd_v4/derived','이전 후보를 읽는 제작/비교 도구 정리 후. 현재 채택 368포즈는 삭제 대상 아님')
subtree('art/hd_v4/archive_candidates','I_archived_hd_candidates','현재 clean_masters/derived와 분리한 이전 후보 보관','art/hd_v4/clean_masters + art/hd_v4/masters + art/hd_v4/derived','채택의 유일 원본을 포함하지 않는지 각 manifest와 대조할 때까지 조건부')
manifest=read(ROOT/'Game/Assets/Art/court_figures/manifest.json')
keep={Path(x[k]).name for x in manifest.values() for k in ['texture','back'] if k in x}
for p in files:
    if p.startswith('Game/Assets/Art/court_figures/') and p.endswith('.webp') and Path(p).name not in keep:
        add(p,'J_unused_runtime_export','384 정규 키 manifest에 없는 이전 변환 잔여','Game/Assets/Art/court_figures/manifest.json','생성기가 참조 집합으로 출력을 관리하도록 수정 후')
    if p.startswith('.git/objects/') and Path(p).name.startswith('tmp_obj_'):
        add(p,'K_git_temporary_garbage','Git이 사용하는 해시 객체 이름이 아닌 중단된 임시 객체 후보','.git/objects의 정규 객체/pack 및 모든 refs','활성 Git 작업이 없고 git fsck 통과 후 Git 유지보수로 정리. 객체 전체 삭제 금지')
for x in rows.values():
    if x['retained'] in rows:
        equivalent=x['retained'];other=rows[equivalent]
        x['retained']=equivalent+' (즉시 동등본) → '+other['retained']+' (전체 정리 뒤 유지본)'
        x['condition']+='; 동등본도 정리하는 경우 그 행의 선행 조건과 최종 유지본까지 함께 확인'
totals=Counter()
for x in rows.values(): totals[x['category']]+=x['bytes']
top=Counter()
for p,n in files.items(): top['/'.join(p.split('/')[:2])]+=n
result={'scope':'READ ONLY; NO DELETION ATTEMPT','total_bytes':sum(files.values()),'current_build':current,'current_build_bytes':sum(n for p,n in files.items() if p.startswith(current+'/')),'listed_bytes':sum(totals.values()),'remaining_after_all_conditions_bytes':sum(files.values())-sum(totals.values()),'categories':dict(totals),'rows':sorted(rows.values(),key=lambda x:(x['category'],-x['bytes'])),'top_folders':dict(top.most_common(30)),'protected':['.git history','docs/data/tools/ui source','current Blender editable sources','selected master/derived/CG/delivery','intentional reconstruction puzzle decoys','unique supplied audio','current build','test reports and captures'],'deleted_bytes':0}
(OUT/'files.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'files.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['path','bytes','category','reason','retained','condition']);w.writeheader();w.writerows(result['rows'])
labels={'A_pixel_identical_png':'픽셀 동일 PNG 중복','B_blender_backup':'Blender 이전 저장 백업','C_test_browser_cache':'실행 검증용 브라우저 캐시','D_previous_build':'이전 개발 빌드','E_superseded_3d_export':'r4/r2로 대체된 3D 출력','F_rejected_cg_revision':'최신 선택에서 제외된 CG 수정본','G_reproducible_cg_intermediate':'다시 만들 수 있는 CG 4배 중간본','H_excluded_nai_poses':'채택 제외 NAI 포즈','I_archived_hd_candidates':'HD 후보 보관본(추가 대조 필요)','J_unused_runtime_export':'현재 입상 manifest 밖 변환 잔여','K_git_temporary_garbage':'Git 임시 객체 후보(검사 선행)'}
gb=lambda n:f'{n/2**30:.3f}'
md=['# 작업 폴더 삭제 후보 전수 목록 — 2026-10-29','','읽기 전용 조사예요. 실제 삭제는 0바이트예요. 각 파일 경로/바이트/유지본/선행 조건은 files.csv와 files.json에 있어요. 범주는 중복 집계하지 않았어요.','','| 구분 | 파일 수 | GiB |','|---|---:|---:|']
for c,n in totals.items():md.append(f'| {labels[c]} | {sum(x["category"]==c for x in rows.values())} | {gb(n)} |')
md+=['',f'- 조사 시점 전체 작업 폴더: {gb(result["total_bytes"])} GiB',f'- 현재 실행 빌드 한 벌: {gb(result["current_build_bytes"])} GiB',f'- 전체 조건 충족 후 삭제 후보 합: {gb(result["listed_bytes"])} GiB',f'- 위 목록을 모두 정리해도 남는 제작 폴더: {gb(result["remaining_after_all_conditions_bytes"])} GiB','','5GB 미만인 실행 빌드와 원본/작업 이력/Git를 포함한 제작 폴더는 서로 달라요. 이 목록만으로 전체 제작 폴더가 5GB 아래가 된다고 약속하지 않아요. 원본을 지워서 숫자만 맞추지 않아요.','','PNG 중복은 RGBA 픽셀까지 일치하지만 제작 도구의 PNG 경로를 WebP로 바꿔야 해요. 오래된 GLB는 r4 생성/검사의 입력이어서 도구를 먼저 정리해야 해요. I 범주는 보관본의 유일 원본 여부까지 확인하기 전에는 확정 삭제하지 않아요. 최신 만화의 오답 조각은 필요한 퍼즐 에셋이므로 후보라는 이름만 보고 지우지 않아요.','','이전 삭제 호출은 자동 승인 검토가 거절했어요. 이번에는 사용자가 요청한 목록만 만들었고, 같은 삭제나 다른 도구로 우회하지 않았어요.']
(OUT/'README.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['total_bytes','current_build_bytes','listed_bytes','remaining_after_all_conditions_bytes','categories']},ensure_ascii=False))
