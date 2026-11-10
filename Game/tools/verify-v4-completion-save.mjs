import {padSystemAction} from './v4-pad-test-input.mjs';
// Actual input regression: a committed success saved during its dialogue is not awarded twice.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/v4-completion-save-'+Date.now());await fs.mkdir(work,{recursive:true});
const resume=process.env.V4_COMPLETION_RESUME;if(resume){await fs.mkdir(path.join(work,'UserData'),{recursive:true});await fs.copyFile(resume,path.join(work,'UserData/savegames.json'));}
const delay=ms=>new Promise(r=>setTimeout(r,ms));let probe;const checks=[];
const keys={Enter:[13,'Enter'],Tab:[9,'Tab'],Backspace:[8,'Backspace'],Control:[17,'ControlLeft'],w:[87,'KeyW'],s:[83,'KeyS'],a:[65,'KeyA'],d:[68,'KeyD'],c:[67,'KeyC'],o:[79,'KeyO']};
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);await delay(700);
 const call=(n,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+n)},${JSON.stringify(args)})`);
 const stats=async()=>JSON.parse((await call('Stats')).outputs.result),growth=async()=>JSON.parse((await call('GrowthStats')).outputs.result);
 const key=async(k,type)=>{const [windowsVirtualKeyCode,code]=keys[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});};
 const tap=async k=>{await key(k,'keyDown');await delay(100);await key(k,'keyUp');await delay(100);};
 const pad=id=>padSystemAction(stats,tap,id);
 let node,before,q;
 if(resume){const raw=JSON.parse(await fs.readFile(resume,'utf8')),head=JSON.parse(Object.entries(raw.items).find(([k])=>k.includes('yumeno-progress-v4.project.'))[1]);assert.equal(head.taskResume.phase,'success');node=head.node;before={correct:head.court.correct,trialHp:head.court.hp};await call('DebugFastRead');await tap('c');}
 else{
 await tap('o');for(let i=0;i<3;i++)await tap('s');await tap('d');await tap('Backspace');
 await call('DebugFastRead'); // Explicit QA text pacing; leave gameplay/HP/reward rules intact.
 await call('DebugV4CompletionFixture');await key('Control','keyDown');await probe.until(async()=>{const s=await stats();assert(!s.error,JSON.stringify(s));return !s.taskQueue&&s.taskInputArmed;},'intro',20000);await key('Control','keyUp');await delay(200);
 q=await stats();node=q.node;assert.equal(q.auto.kind,'click');
 await probe.cdp('Input.dispatchMouseEvent',{type:'mouseMoved',x:q.auto.x,y:q.auto.y});await probe.cdp('Input.dispatchMouseEvent',{type:'mousePressed',x:q.auto.x,y:q.auto.y,button:'left',clickCount:1});await delay(100);await probe.cdp('Input.dispatchMouseEvent',{type:'mouseReleased',x:q.auto.x,y:q.auto.y,button:'left',clickCount:1});await delay(150);
 await probe.until(async()=>{const s=await stats();assert(!s.error,JSON.stringify(s));return s.taskQueue&&s.queueAfter==='success';},'answer confirmation animation and actual committed success',10000);
 q=await stats();assert(!q.error,JSON.stringify(q));assert.equal(q.queueAfter,'success');before=await growth();assert.equal(before.correct,2);assert.equal(before.trialHp,6000);checks.push('one completed answer awards one count and the equipped periodic 2000 HP recovery');await probe.capture('01-committed-success.png');
 await tap('Tab');for(let i=0;i<5;i++)await tap('d');await tap('Enter');await pad('save');await pad('title');await pad('title_yes');assert.equal((await stats()).mode,'title');await tap('c');await delay(300);
 }
 await probe.until(async()=>{const s=await stats();assert(!s.error,JSON.stringify(s));return s.node===node&&s.taskQueue&&s.queueAfter==='success';},'cooperative restore reaches saved success queue',60000);
 q=await stats();assert(!q.error,JSON.stringify(q));assert.equal(q.node,node);assert.equal(q.queueAfter,'success');assert(q.taskQueue);let restored=await growth();assert.equal(restored.correct,before.correct);assert.equal(restored.trialHp,before.trialHp);checks.push('loading returns to the committed success dialogue with the exact count and HP');await probe.capture('02-restored-success.png');
 await key('Control','keyDown');await probe.until(async()=>{const s=await stats();assert(!s.error,JSON.stringify(s));return s.node!==node;},'success route',20000);await key('Control','keyUp');restored=await growth();assert.equal(restored.correct,before.correct);assert.equal(restored.trialHp,before.trialHp);checks.push('success route continues without replaying its input or its reward');
 assert.deepEqual(probe.errors,[]);const report={ok:true,work,executable,fixture:true,resume:resume||null,checks,before,restored};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,checks},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
