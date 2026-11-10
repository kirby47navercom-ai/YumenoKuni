// One authored dialogue fixture and actual saved read receipt, no chapter replay.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/v4-read-skip-'+Date.now());await fs.mkdir(work,{recursive:true});
const keys={Control:[17,'ControlLeft'],Tab:[9,'Tab'],Enter:[13,'Enter'],Backspace:[8,'Backspace'],w:[87,'KeyW'],s:[83,'KeyS'],a:[65,'KeyA'],d:[68,'KeyD'],c:[67,'KeyC']};
const delay=ms=>new Promise(r=>setTimeout(r,ms));let probe;const checks=[];process.env.HB_PLAYER_SOAK_HOURS='1';
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);await delay(700);
 const call=(n,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+n)},${JSON.stringify(args)})`);
 const stats=async()=>{const s=JSON.parse((await call('Stats')).outputs.result);assert(!s.error,JSON.stringify(s));return s;};
 const sample=async()=>{const f=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(60);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=f+2,'sample',10000);};
 const key=async(k,type)=>{const [windowsVirtualKeyCode,code]=keys[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});};
 const tap=async k=>{for(const type of ['keyDown','keyUp']){await key(k,type);await sample();}};
 await call('DebugFastRead'); // Explicitly permit QA skipping unread text; never set its read receipt.
 await call('DebugV4DialogueFixture',{kind:0});const initial=await stats();assert.equal(initial.v4Kind,'say');assert(!initial.options.values.readOnlySkip);await probe.capture('01-before-skip.png');
 await key('Control','keyDown');await probe.until(async()=>(await stats()).node!==initial.node,'Control leaves the actual line',10000);await key('Control','keyUp');await sample();const after=await stats();assert.notEqual(after.node,initial.node);checks.push('actual Control input reveals and leaves every page of one authored dialogue');
 await tap('Tab');for(const type of ['mouseMoved','mousePressed','mouseReleased']){await probe.cdp('Input.dispatchMouseEvent',{type,x:1047,y:480,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})});await sample();}await padSystemAction(stats,tap,'save');
 const raw=JSON.parse(await fs.readFile(path.join(work,'UserData/savegames.json'),'utf8'));const head=JSON.parse(Object.entries(raw.items).find(([k])=>k.includes('yumeno-progress-v4.project.'))[1]);const reads=new Set(head.read||[]);for(const [k,v] of Object.entries(raw.items))if(k.includes('yumeno-v4-'+head.snapshot+'-read-'))for(const id of JSON.parse(v).rows)reads.add(id);assert(reads.has(initial.node),'skipped final page must persist its read receipt');await probe.capture('02-read-saved.png');checks.push('actual independent manual/canonical save records the skipped dialogue ID; no read-set injection or historical reconstruction');
 await padSystemAction(stats,tap,'title');await padSystemAction(stats,tap,'title_yes');await tap('c');await probe.until(async()=>(await stats()).node===head.node,'same saved node',60000);assert.deepEqual(probe.errors,[]);
 const report={ok:true,fixture:true,work,executable,node:initial.node,savedNode:head.node,readCount:reads.size,checks,scope:'One actual authored dialogue UI fixture, physical Control and actual multipart Save/Continue. Proves newly skipped line receipt only; no retroactive changes to prior normal saves or whole chapter traversal.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,checks,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
