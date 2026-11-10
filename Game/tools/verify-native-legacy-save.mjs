import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),build=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8')),work=path.join(root,'Saved/native-legacy-save-'+Date.now());let probe;
try{
 const resume=path.join(root,'Saved/ui-checkpoints/normal-ch3-latest/savegames.json');probe=await nativeWindowProbe({source:build.output,work,resume,legacyOnly:true});await probe.tap('c');await probe.sampled(12);const state=await probe.stats();assert.equal(state.mode,'title','This baseline checks that the unchanged legacy flat format is currently not discovered');assert.equal(await fs.readFile(path.join(work,'State/savegames.json'),'utf8'),await fs.readFile(resume,'utf8'));await probe.capture('legacy-save-undiscovered');const runtime=await probe.close();probe=null;
 const report={ok:true,productBehavior:'FAIL-legacy-save-not-discovered',work,build:build.id,originalSaveChanged:false,legacyOnly:true,manualNativeSlotConversion:false,state,frames:runtime.frames,scope:'Actual Win32 Continue with the unchanged old flat savegames.json copied into owned native state. Native continues to title; no auto migration. This is a confirmed compatibility failure, not save loss or successful native save migration.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({work,behavior:report.productBehavior}));
}catch(error){await fs.mkdir(work,{recursive:true});await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack},null,2));throw error;}finally{await probe?.close().catch(()=>{});}
