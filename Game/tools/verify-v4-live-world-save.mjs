// Focused own-player regression: physically move/look, menu-save, cold Continue.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/v4-live-world-save-'+Date.now());
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const seed=JSON.parse(await fs.readFile(path.join(root,'Saved/editorial-fixtures-20261101/chapter-3.json'),'utf8'));
const headKey=Object.keys(seed.items).find(k=>k.includes('yumeno-progress-v4.project.'));
const head=JSON.parse(seed.items[headKey]);head.node='v4:3:investigate:I3-05-rule';head.snapshot='2026110115-1';head.court.active=false;
head.worldId='mirror_maze';head.world={};head.presentation={};head.stack=[];head.flags={};seed.items[headKey]=JSON.stringify(head);
await fs.mkdir(path.join(work,'UserData'),{recursive:true});await fs.writeFile(path.join(work,'UserData/savegames.json'),JSON.stringify(seed));
const keys={c:[67,'KeyC'],w:[87,'KeyW'],ArrowRight:[39,'ArrowRight'],ArrowUp:[38,'ArrowUp'],Tab:[9,'Tab'],a:[65,'KeyA'],d:[68,'KeyD'],Enter:[13,'Enter'],Backspace:[8,'Backspace']};
const delay=ms=>new Promise(r=>setTimeout(r,ms));let probe,last;
try{
 const launch=async()=>{probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);};
 await launch();
 const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
 const stats=async()=>{last=JSON.parse((await call('Stats')).outputs.result);assert(!last.error&&!last.routeBlocked,JSON.stringify(last));return last;};
 const sample=async()=>{const f=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(65);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=f+2,'sample',10000);};
 const key=async(k,type)=>{const[windowsVirtualKeyCode,code]=keys[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});};
 const hold=async(k,ms)=>{await key(k,'keyDown');await delay(ms);await sample();await key(k,'keyUp');await sample();};
 const tap=k=>hold(k,0);
 await tap('c');await probe.until(async()=>(await stats()).mode==='explore'&&last.node===head.node,'authored investigation hub',60000);
 const entry=await stats();assert.equal(entry.world.space,'mirror_maze');assert.equal(entry.world.control,'free_walk');await delay(1500);await probe.capture('mirror-entry.png');
 await hold('w',260);await hold('ArrowRight',180);await hold('ArrowUp',130);const moved=await stats();
 assert(Math.hypot(moved.world.position[0]-entry.world.position[0],moved.world.position[2]-entry.world.position[2])>.1,'physical walking changes position');
 assert(moved.world.yaw>entry.world.yaw+1&&moved.world.pitch>entry.world.pitch+1,'physical view input changes angles');
 await tap('Tab');for(const type of ['mouseMoved','mousePressed','mouseReleased']){await probe.cdp('Input.dispatchMouseEvent',{type,x:1047,y:480,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})});await sample();}
 await padSystemAction(stats,tap,'save');
 const disk=JSON.parse(await fs.readFile(path.join(work,'UserData/savegames.json'),'utf8')),saved=JSON.parse(disk.items[headKey]);
 const pose=[...moved.world.position,moved.world.yaw,moved.world.pitch];assert(saved.world.mirror_maze,'live room exists in real manual save');
 saved.world.mirror_maze.forEach((v,i)=>assert(Math.abs(v-pose[i])<.001,`saved live pose ${i}`));assert.equal(saved.node,head.node);
 await fs.copyFile(path.join(work,'UserData/savegames.json'),path.join(work,'actual-manual-savegames.json'));assert.deepEqual(probe.errors,[]);
 await probe.stop();probe=null;await launch();await tap('c');await probe.until(async()=>(await stats()).mode==='explore'&&last.node===head.node,'cold exact authored hub Continue',60000);
 const restored=await stats(),actual=[...restored.world.position,restored.world.yaw,restored.world.pitch];actual.forEach((v,i)=>assert(Math.abs(v-pose[i])<.001,`cold restored live pose ${i}`));
 await delay(1200);await probe.capture('cold-continue.png');assert.deepEqual(probe.errors,[]);
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,executable,fixture:true,normalRoute:false,entry,moved,savedPose:saved.world.mirror_maze,restored,errors:probe.errors,scope:'Isolated authored chapter3 hub. Physical walk and yaw/pitch input; actual Pad manual save then player restart and exact node/position/yaw/pitch Continue. Own mirror lighting screenshots; no original V3 access or full-campaign/duration claim.'},null,2));console.log(JSON.stringify({ok:true,work}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,last,errors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
