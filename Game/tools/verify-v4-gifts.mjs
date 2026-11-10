import {padSystemAction} from './v4-pad-test-input.mjs';
// Native gift UI fixture: explicit initial inventory/meeting flags, not a played FTE.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/v4-gifts-'+Date.now());await fs.mkdir(work,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const keys={Enter:[13,'Enter'],Escape:[27,'Escape'],Backspace:[8,'Backspace'],Tab:[9,'Tab'],Control:[17,'ControlLeft'],w:[87,'KeyW'],s:[83,'KeyS'],a:[65,'KeyA'],d:[68,'KeyD'],l:[76,'KeyL'],c:[67,'KeyC'],m:[77,'KeyM'],o:[79,'KeyO'],g:[71,'KeyG']};
process.env.HB_PLAYER_SOAK_HOURS='1';let probe;const checks=[];
try{
 probe=await editorWindowProbe({work,mode:'player',executable});
 await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);await delay(700);
 const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call("Driver",${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
 const stats=async()=>JSON.parse((await call('Stats')).outputs.result);
 const key=async(k,type)=>{const [windowsVirtualKeyCode,code]=keys[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});};
 const tap=async k=>{await key(k,'keyDown');await delay(90);await key(k,'keyUp');await delay(90);if((await stats()).choice?.pending>=0)await probe.until(async()=>((await stats()).choice?.pending??-1)<0,'authored choice confirm visual',5000);};
 const imageErrors=()=>probe.evaluate(`Array.from(document.images).filter(i=>i.offsetWidth>0&&i.src&&i.complete&&i.naturalWidth===0).map(i=>i.src)`);
 const padAction=id=>padSystemAction(stats,tap,id);
 const growth=async()=>JSON.parse((await call('GrowthStats')).outputs.result);
 await call('DebugFastRead'); // Explicit QA dialogue pacing; not a source option row or a played-path claim.
 await call('DebugV4GiftFixture');let s=await stats();assert(!s.error,JSON.stringify(s));const node=s.node;assert.equal(s.giftV4.mode,0);
 const pick=async id=>{let q=await stats();const index=q.giftV4.choices.indexOf(id);assert(index>=0,JSON.stringify({id,q}));for(let i=0;i<index;i++)await tap('s');await tap('Enter');};
 const dialogue=async expected=>{await key('Control','keyDown');await probe.until(async()=>{const q=await stats();assert(!q.error,JSON.stringify(q));return q.giftV4.mode!==3;},'gift dialogue',20000);await key('Control','keyUp');assert.equal((await stats()).giftV4.mode,expected);};
 const open=async()=>{await tap('g');assert.equal((await stats()).giftV4.mode,1);await pick('rin');await dialogue(2);};
 const initial=await growth();assert.equal(initial.inventory.G14,2);assert.equal(initial.inventory.G01,1);
 await open();await probe.capture('01-owned-item-picker.png');await pick('G01');await dialogue(2);assert.equal((await growth()).inventory.G01,1);checks.push('refusal returns to the same picker without consumption');
 await pick('G14');await dialogue(5);await probe.capture('02-explicit-confirmation.png');assert.equal((await growth()).inventory.G14,2);await pick('defer');await dialogue(0);assert.equal((await growth()).inventory.G14,2);checks.push('willing dialogue and defer never consume an item');
 await open();await pick('G14');await dialogue(5);await pick('give');assert.equal((await growth()).inventory.G14,1);await dialogue(0);assert.equal((await growth()).giftClaims,1);assert.equal((await stats()).node,node);checks.push('final accepted transaction consumes one, records one claim, returns to the actual free window');
 await tap('g');assert.deepEqual((await stats()).giftV4.choices,['back']);await tap('Backspace');assert.equal((await growth()).inventory.G14,1);checks.push('same-recipient same-window duplicate is absent');
 await tap('Tab');for(let i=0;i<5;i++)await tap('d');await tap('Enter');await padAction('save');await padAction('title');await padAction('title_yes');assert.equal((await stats()).mode,'title');await tap('c');await probe.until(async()=>{const q=await stats();assert(!q.error,JSON.stringify(q));return q.mode==='menu'&&q.node===node;},'cooperative gift-window restore',60000);s=await stats();assert.equal(s.node,node);assert.equal((await growth()).inventory.G14,1);assert.equal((await growth()).giftClaims,1);checks.push('save/load preserves actual inventory and transaction claim');
 // The source machine replaced the old capsule mode4/6. Its payment, inventory,
 // extra draws, Pad and save routes have a separate verify-v4-machine-skills proof.
 const missing=await imageErrors();assert.deepEqual(missing,[]);
 const report={ok:true,checks,work,executable,node,fixture:true,errors:probe.errors,scope:'Actual input on an explicit gift fixture; rejects, defer, accepted transaction, duplicate guard and separate save/load. Source machine has a separate current proof. Not normal FTE traversal or all 1650 reactions.'};
 assert.equal(probe.errors.length,0);await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({ok:false,checks,error:error.stack},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}
finally{await probe?.stop?.();}
