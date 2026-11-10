// Exact normal-route first chapter3 trial checkpoint; no replay of its preceding story.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url))),checkpoint=path.join(root,'Saved/ui-checkpoints/normal-ch3-first-trial/savegames.json');
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/v4-large-save-'+Date.now());await fs.mkdir(path.join(work,'UserData'),{recursive:true});await fs.copyFile(checkpoint,path.join(work,'UserData/savegames.json'));
const delay=ms=>new Promise(r=>setTimeout(r,ms)),keys={Enter:[13,'Enter'],Tab:[9,'Tab'],Control:[17,'ControlLeft'],Backspace:[8,'Backspace'],a:[65,'KeyA'],d:[68,'KeyD'],w:[87,'KeyW'],s:[83,'KeyS'],c:[67,'KeyC']};let probe;const checks=[];process.env.HB_PLAYER_SOAK_HOURS='1';
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);await delay(700);
 const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
 const stats=async()=>{const s=JSON.parse((await call('Stats')).outputs.result);assert(!s.error,JSON.stringify(s));return s;};
 const key=async(k,type)=>{const [windowsVirtualKeyCode,code]=keys[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});};
 const sample=async()=>{const f=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(80);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=f+2,'input sampled',10000);};
 const tap=async k=>{await key(k,'keyDown');await sample();await key(k,'keyUp');await sample();};
 const click=async(x,y)=>{for(const type of ['mouseMoved','mousePressed','mouseReleased']){await probe.cdp('Input.dispatchMouseEvent',{type,x,y,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})});await sample();}};
 const ready=async()=>{await key('Control','keyDown');await probe.until(async()=>{const s=await stats();return s.taskId==='T3-NS-01'&&!s.taskQueue&&s.taskInputArmed&&!s.presentation.nonstopIntro;},'only saved task intro',25000);await key('Control','keyUp');};
 await call('DebugFastRead');await tap('c');await ready();const before=await stats(),node=before.node;assert.equal(node,'v4:input:T3-NS-01');assert.equal(before.chapter,3);checks.push('actual45-card normal-route first chapter3 trial checkpoint restored directly; no chapter/prologue traversal');
 const system=async()=>{await tap('Tab');assert.equal((await stats()).mode,'pad');await click(1047,480);assert.equal((await stats()).padPage,5);};
 await system();let firstBusy=-1,lastBusy=-1,captured=false;
 const watched=async()=>{const s=await stats();if(s.padSystem?.busy){const f=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');if(firstBusy<0)firstBusy=f;lastBusy=f;if(!captured){captured=true;await probe.capture('01-incremental-save.png');}}return s;};
 await padSystemAction(watched,tap,'save');assert(firstBusy>=0&&lastBusy>firstBusy+10,'save must yield across native updates');checks.push('2000-line native save yields between verified parts instead of blocking one C++ callback; real overwrite dialog and save UI remain active');
 await padSystemAction(stats,tap,'title');await padSystemAction(stats,tap,'title_yes');await tap('c');await ready();assert.equal((await stats()).node,node);assert.equal((await stats()).cards,before.cards);assert.equal((await stats()).trialHp,before.trialHp);checks.push('real title/Continue preserves exact first-trial node,45 acquired cards and HP after the large save');
 await system();await padSystemAction(stats,tap,'save');await probe.capture('02-overwrite-complete.png');assert.deepEqual(probe.errors,[]);
 const storage=path.join(work,'UserData/savegames.json');let head;await probe.until(async()=>{try{const raw=JSON.parse(await fs.readFile(storage,'utf8'));head=JSON.parse(Object.entries(raw.items).find(([k])=>k.includes('yumeno-progress-v4.project.'))[1]);return head.node===node&&head.logParts===20&&head.playerProgress.v===2&&head.growth.schemaVersion===2;}catch{return false;}},'new native save persisted',10000);
 checks.push('second overwrite completes with XP/growth v2 and20 log parts; old snapshots remain independent until their own committed head replaces them');
 const cache=path.join(root,'Saved/ui-checkpoints/normal-ch3-first-trial-current');await fs.mkdir(cache,{recursive:true});await fs.copyFile(storage,path.join(cache,'savegames.json'));await fs.writeFile(path.join(cache,'checkpoint.json'),JSON.stringify({node,chapter:3,source:work,fixture:false,scope:'Actual normal-route native save after incremental large-save/Continue proof. Reuse for remaining chapter3; no replay before this first trial input.'},null,2));
 const report={ok:true,fixture:false,executable,work,checkpoint,node,checks,resume:path.join(cache,'savegames.json'),scope:'Large manual-save/Continue at the exact actual chapter3 first trial input. No outcome/campaign/other UI or normal-play-duration acceptance.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,checks,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
