import fs from 'node:fs/promises';import path from 'node:path';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game),root=path.join(game,'Saved/nonstop-guidance-20261106'),work=path.join(game,'Saved/nonstop-all-20261106'),read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const r=await read(path.join(root,'final-review.json')),cleanup=await read(path.join(root,'cleanup.json'));r.cleanup=cleanup;await fs.writeFile(path.join(root,'final-review.json'),JSON.stringify(r,null,2));
const resume=await read(path.join(work,'current-resume.json'));resume.guidanceCorrection={complete:true,build:r.build,executable:r.executable,review:'../nonstop-guidance-20261106/final-review.json',commonTrialSourceWindow:true,thoughts:71,sentences:156,agreementCharacters:16,agreementAllFiveInherited:true,agreementFreshV20WideAndMovie:true,packedSmoke:r.packed.work,videoPaths:r.freshActualMovies.map(v=>v.path),engineModified:false};await fs.writeFile(path.join(work,'current-resume.json'),JSON.stringify(resume,null,2));
const block=`<!-- NONSTOP_DIALOGUE_AGREEMENT_FINAL_20261106 -->
논스톱·재판 공통 대화창·동의 포즈 교정 실행본 **${r.build}**. 재개는 Game/Saved/nonstop-guidance-20261106/final-review.json과 nonstop-all-20261106/current-resume.json이에요. 최신 8eb9 이론무장 세 파일 및 이전 Climax/915 마스크를 보존한 113 Source 통합, 원래 2노드 BP·전콘텐츠 SHA 검사와 최종 압축본 정상저장 QHD 실행/실제 시간진행/exit0 PASS예요. 진단 그래프 출하/엔진 원본 변경/원작 실행 없음.
원본 네 UI 컨테이너 68bitmap의 파란 공통 재판창·얼굴카드·우리 전체이름·수동/AUTO·챕터 및 1280/1920/3440/3840 배치, 일상 ADV 보존을 확인했어요. 71개 고유 자연스러운 순환독백/156문장, 오답/순환 시 이전 증언 글자 숨김도 연결했어요. 동의 전용 16명 새 그림은 손·상체·표정·소품을 각각 다르게 만들었고 머리/눈 앵커는 균등확대·이동으로 맞췄어요. 다른 모드의 일반 T03는 유지해요. 동의 전경/배경 각16 전용 슬롯으로 화면비를 분리했고 일반 EndingLeaf 좌표는 유지해요.
동의 실제5경로 성공/복귀는 v18, 동일 캐스트의 v20 울트라와이드 및 178.218초 전체 동의 영상, 공통창이 같은 v16 논파/위증 전체 영상을 구분해서 재사용해요. 출하 v22는 이 동의소스가 같고 이론무장 두 파일과 새 Encounters 헤더만 추가된 통합이에요. 위증5경로는 변경없는6헤더의 v13 실제증거를 상속하며 최신에서71개전체를 재플레이했다고 부르지 않아요.
검토 영상/20261105-논스톱/43~45 MP4에 실제음향·도입/순환/독백/오답/발사/결과/재판복귀를 공개했어요. 닫힌 own 중간파일 ${cleanup.moves.length}개 ${cleanup.movedBytes}bytes는 프로젝트 root삭제대기로 이동했고 실제삭제/공간회수 주장은 없어요. 사용자 시각승인/전편완벽/보편FPS 합격은 대신 판정하지 않아요. 예약/목표/커밋/원본세이브 변경 없음. 완료된 범위는 이 재개점에서 이어가요.
<!-- NONSTOP_DIALOGUE_AGREEMENT_FINAL_20261106_END -->

`;
for(const name of ['HANDOFF.md','CODEX_HANDOFF.md']){const file=path.join(repo,name),s=await fs.readFile(file,'utf8');if(!s.includes('<!-- NONSTOP_DIALOGUE_AGREEMENT_FINAL_20261106 -->'))await fs.writeFile(file,block+s);}
console.log(JSON.stringify({build:r.build,videos:r.freshActualMovies.map(v=>v.path),cleanup:cleanup.moves.length}));
