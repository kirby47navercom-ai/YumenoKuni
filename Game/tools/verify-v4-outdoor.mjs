// Real native outdoor atmosphere; direct authored-map fixtures, no preceding chapter replay.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/v4-outdoor-'+Date.now());await fs.mkdir(work,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms)),checks=[],states=[];let probe;process.env.HB_PLAYER_SOAK_HOURS='1';
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);await delay(500);
 const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
 const env=async()=>JSON.parse((await call('EnvironmentStats')).outputs.result),stats=async()=>JSON.parse((await call('Stats')).outputs.result);
 const show=async(index,phase)=>{await call('DebugV4OutdoorFixture',{index,phase});await delay(1200);const s=await env();assert(!(await stats()).error,JSON.stringify(await stats()));assert.equal(s.outdoor,index<10);assert.equal(s.phase,phase);for(let p=0;p<3;p++)for(const k of ['sky','cloud','sun'])assert.equal(s.profiles[p][k],index<10&&p===phase&&k!=='cloud',JSON.stringify(s));assert.equal(s.dome,index<10);if(index<10)assert(s.mesh.includes(['day','night','evening'][phase]));states.push(s);return s;};
 await show(0,0);await probe.capture('01-plaza-day-sky.png');await show(0,1);await probe.capture('02-plaza-night-sky.png');await show(0,2);await probe.capture('03-plaza-evening-sky.png');checks.push('actual native sky/cloud/sun actors select one day/night/evening profile at the exact plaza fixture');
 for(let i=1;i<10;i++){await show(i,0);if(i===1||i===4||i===5)await probe.capture('outdoor-'+i+'.png');}checks.push('all10 explicit exterior/view-through-glass sets enable atmosphere; classification is authored, independent of background filenames');
 await show(10,0);await probe.capture('04-interior-no-sky-leak.png');checks.push('interior restores its own lighting and disables every exterior sky/cloud/sun actor');
 await call('DebugV4Task',{taskId:'T1-ANSWER-A01'});await delay(700);const c=await env();for(const p of c.profiles)assert(!p.sky&&!p.cloud&&!p.sun);checks.push('returning to courtroom disables exterior atmosphere and restores court lighting');
 assert.deepEqual(probe.errors,[]);const report={ok:true,fixture:true,executable,work,checks,states,scope:'Native environment actor state and actual captures at exact authored-map/task fixtures; no chapter/prologue traversal, original V3 weather identity, all authorial time-of-day annotations or whole-game visual acceptance.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,checks,states,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
