// Restore existing outdoor checkpoints; do not invent progression or alter source saves.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createOwnedNativePackage} from './native-owned-package.mjs';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),build=JSON.parse(await fs.readFile(process.argv.find(v=>v.startsWith('--build-result='))?.slice(15)||path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/native-outdoor-'+Date.now());await fs.mkdir(work,{recursive:true});
const gameContentOverrides=process.argv.find(v=>v.startsWith('--content-overrides='))?.slice(20);
const candidates=process.argv.slice(2).filter(v=>!v.startsWith('--'));const [runnerCandidate,widgetCandidate,playerCandidate,rendererCandidate]=candidates;
const prepared=await createOwnedNativePackage({source:build.output,work,stats:true,runnerCandidate,widgetCandidate,playerCandidate,rendererCandidate,gameContentOverrides,migrationCandidate:runnerCandidate?path.join(root,'tools/native-save-migration.candidate.mjs'):undefined});
const fixtures=[
 {label:'plaza',save:'Saved/v4-editorial-scenes-1793497926027/1-04L1/actual-manual-savegames.json'}
];
const rows=[];let probe;
try{
 for(const fixture of fixtures){
  const resume=path.join(root,fixture.save),bytes=await fs.readFile(resume),sha=createHash('sha256').update(bytes).digest('hex');
  const flat=JSON.parse(bytes),head=JSON.parse(Object.entries(flat.items).find(([k])=>k.startsWith('hbengine.savegame.json.yumeno-progress-v4.project.'))[1]);
  probe=await nativeWindowProbe({source:build.output,work:path.join(work,fixture.label),prepared,resume,legacyOnly:!!runnerCandidate,heartbeatTimeoutMs:120000});
  const restoreStarted=Date.now();await probe.tap('c');
  const loaded=await probe.until(async()=>{const s=await probe.stats();assert(!s.error,s.error);return s.node===head.node&&s.scenes?.explore&&!s.scenes.loading?s:false;},'exact existing outdoor checkpoint',60000);
  await probe.sampled(5);const image=await probe.capture('restored-outdoor');const runtime=await probe.close();probe=null;
  assert(runtime.renderer.info.calls>0,'Outdoor geometry must render');
  assert.equal(createHash('sha256').update(await fs.readFile(resume)).digest('hex'),sha);
  rows.push({label:fixture.label,resume,sha256:sha,loaded,image,restoreAndCaptureMs:Date.now()-restoreStarted,drawCalls:runtime.renderer.info.calls,frames:runtime.frames,finalMemory:runtime.memory,peakSampledRSS:runtime.peakSampledRSS,audioErrors:runtime.audio.errors});
 }
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,work,build:build.id,shippingEngine:!runnerCandidate&&!widgetCandidate&&!playerCandidate&&!rendererCandidate,gameContentOverrides:gameContentOverrides||null,runnerCandidate,widgetCandidate,playerCandidate,rendererCandidate,rows,scope:(gameContentOverrides?'Declared game-owned visual content candidate; not completed shipping art acceptance. ':'')+'Existing plaza dialogue checkpoint restored exactly. Actual Win32/D3D11 plus native Skia capture, geometry present, original save immutable. Representative daylight snapshot, not a replayed route or all outdoor/time-of-day acceptance. Removed garden-call fixture because its authored call automatically enters a different scene, so an exact call-node comparison was a QA mistake.'},null,2));
 console.log(JSON.stringify({ok:true,work}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,last:await probe?.stats().catch(()=>null)},null,2));throw error;}finally{await probe?.close().catch(()=>{});}
