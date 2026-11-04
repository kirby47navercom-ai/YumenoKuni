// Claude(2026-11-04) : 패닉 글자만 다시 구운 뒤 GPU 재판 자원의 순서를 원래대로 되돌린다.
// create-project --gpu-trial-finalize 의 순서(패닉→애너그램→시계→쇼다운→법정 범위→소음→패닉 캐시)에서 첫 단계(gpuTrial)·최적화만 뺀 것.
import fs from 'node:fs/promises';import path from 'node:path';import {randomUUID} from 'node:crypto';
import {emitGpuTrialAssets} from './v4-gpu-trial-assets.mjs';import {emitGpuPanicAssets} from './v4-gpu-panic-assets.mjs';import {emitGpuAnagramAssets} from './v4-gpu-anagram-assets.mjs';
import {emitGpuStageClock} from './v4-gpu-stage-clock.mjs';import {emitGpuShowdownAssets} from './v4-gpu-showdown-assets.mjs';
import {emitScopedCourtScenes} from './v4-scoped-court-scenes.mjs';import {emitGpuNoiseAssets} from './v4-gpu-noise-assets.mjs';import {emitPanicCacheScene} from './v4-panic-cache-scenes.mjs';
const root=path.resolve(import.meta.dirname,'..');
const write=async(name,data)=>{const file=path.join(root,name),tmp=file+'.'+randomUUID()+'.tmp';await fs.mkdir(path.dirname(file),{recursive:true});try{await fs.writeFile(tmp,typeof data==='string'||Buffer.isBuffer(data)?data:JSON.stringify(data,null,1)+'\n');await fs.rename(tmp,file);}finally{await fs.rm(tmp,{force:true});}};
const o={output:root,write};
// --gpu-trial-finalize 와 같은 앞 정리(Main 글자 노드 보임 복원, 법정 GPU 객체 제거) 뒤 전체 순서를 그대로 다시 돈다. optimize_assets.py 는 이미 끝난 상태라 뺀다.
{const layout=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/gpu_trial_layout.json'),'utf8')),widget=JSON.parse(await fs.readFile(path.join(root,'Assets/UI/Main.hbwidget.json'),'utf8')),parents=new Map(layout.parents.map(n=>[n.id,n]));
 for(const n of widget.nodes)if(/^(M[FB]|MS|N[FB])\d+$/.test(n.id)||['Aim','TimerPanel','Timer','CourtDim'].includes(n.id))n.properties.visible=parents.get(n.id).visible;
 const court=JSON.parse(await fs.readFile(path.join(root,'Assets/Scenes/Court.hbscene.json'),'utf8'));court.objects=court.objects.filter(o=>!o.id.startsWith('TrialGpu_')&&!o.id.startsWith('TrialBatch_'));
 await write('Assets/UI/Main.hbwidget.json',widget);await write('Assets/Scenes/Court.hbscene.json',court);}
const trial=await emitGpuTrialAssets({output:root,source:root,write});
console.log(JSON.stringify({trial,panic:await emitGpuPanicAssets(o),anagram:await emitGpuAnagramAssets(o),clock:await emitGpuStageClock(o),showdown:await emitGpuShowdownAssets(o),court:await emitScopedCourtScenes(o),noise:await emitGpuNoiseAssets(o),panicCache:await emitPanicCacheScene(o)}).slice(0,600));
