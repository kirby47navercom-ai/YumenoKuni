import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),build=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/native-continue-'+Date.now());
const candidate=process.argv.find(a=>a.startsWith('--candidate='))?.slice(12),rendererCandidate=process.argv.find(a=>a.startsWith('--renderer-candidate='))?.slice(21);
const resume=path.join(root,'Saved/ui-checkpoints/normal-ch3-latest/savegames.json');let probe;
try{
 probe=await nativeWindowProbe({source:build.output,work,candidate,rendererCandidate,resume});
 const title=await probe.stats();await probe.capture('title-with-save');
 await probe.tap('c');const loaded=await probe.until(async()=>{const s=await probe.stats();assert(!s.error,JSON.stringify(s));return s.mode==='trial'&&s.node==='v4:input:T3-NS-A11'&&s.taskId==='T3-NS-A11'?s:false;},'exact native normal-three Continue',60000);
 await probe.until(async()=>{const s=await probe.stats();return !s.taskQueue&&s.taskInputArmed&&!s.presentation?.nonstopIntro&&s.presentation?.inputArmed&&s.trial?.speakerSeat>=0?s:false;},'restored task presentation and input ready',120000);
 await probe.capture('restored-trial');
 const trialUI=JSON.parse(await fs.readFile(path.join(work,'restored-trial.ui.json'),'utf8'));for(const name of ['Aim','Timer','Bullet'])assert(trialUI.widgets.find(w=>w.instance==='main')?.nodes.find(n=>n.name===name)?.properties.visible,'Missing active trial UI '+name);
 await probe.tap('Tab');const pad=await probe.until(async()=>{const s=await probe.stats();return s.mode==='pad'?s:false;},'native pad');await probe.capture('pad');await probe.sampled(12);
 await probe.tap('Tab');const returned=await probe.until(async()=>{const s=await probe.stats();return s.mode==='trial'?s:false;},'pad returns to trial');assert.equal(returned.node,loaded.node);assert.equal(returned.trialHp,loaded.trialHp);
 await probe.tap('o');const options=await probe.until(async()=>{const s=await probe.stats();return s.options.open?s:false;},'native options');await probe.capture('options');await probe.click(708,109);const changed=await probe.stats();assert.equal(changed.options.values.music,options.options.values.music-1,'Visible native option arrow must accept mouse click');await probe.tap('d');assert.equal((await probe.stats()).options.values.music,options.options.values.music);await probe.tap('Escape');await probe.until(async()=>!(await probe.stats()).options.open,'options closes');await probe.capture('trial-after-options');
 const runtime=await probe.close();probe=null;
 const report={ok:true,work,build:build.id,engineCandidates:{candidate,rendererCandidate},title,loaded,pad,returned,options,runtime:{frames:runtime.frames,inputs:runtime.inputs,memory:runtime.memory,audio:runtime.audio,renderer:runtime.renderer,ui:runtime.ui},scope:'Actual Win32 targeted input, D3D11 plus Skia captures, unchanged normal-three save manually copied into owned native slot format. Candidate engine QA only; not shipping acceptance or automatic save migration.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({ok:true,work,frames:runtime.frames,inputs:runtime.inputs}));
}catch(e){await fs.mkdir(work,{recursive:true});await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:e.stack,stats:await probe?.stats().catch(()=>null)},null,2));throw e;}finally{await probe?.close().catch(()=>{});}
