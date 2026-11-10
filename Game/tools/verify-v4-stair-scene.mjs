// Resume a real isolated menu save; verify only the repaired set and its old-body return.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/v4-stair-scene-'+Date.now());
await fs.mkdir(path.join(work,'UserData'),{recursive:true});
const checkpoint=path.join(root,'Saved/v4-story-extension-1793461693288/UserData/savegames.json');
await fs.copyFile(checkpoint,path.join(work,'UserData/savegames.json'));
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const graph=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/chapters/6.json'),'utf8'));
let probe,last;const delay=ms=>new Promise(r=>setTimeout(r,ms));
const entryOnly=process.argv.includes('--entry-only');
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
 const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
 const stats=async()=>{last=JSON.parse((await call('Stats')).outputs.result);assert(!last.error&&!last.routeBlocked);return last;};
 const key=async(k,type)=>{const v=k==='Control'?17:k==='Enter'?13:67;await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code:k==='Control'?'ControlLeft':k==='Enter'?'Enter':'KeyC',windowsVirtualKeyCode:v});};
 const tap=async k=>{await key(k,'keyDown');await delay(130);await key(k,'keyUp');await delay(150);};
 await tap('c');await probe.until(async()=>(await stats()).node?.endsWith('6-LC01'),'exact prior stair choice save',60000);
 await delay(1800);await probe.capture('stair-choice-after.png');const start=await stats();
 const world=start.world;assert.equal(world.space,'lower_stairway');
 if(!entryOnly){
 await tap('Enter');await probe.until(async()=>(await stats()).node!==start.node,'confirm once',10000);
 await call('DebugFastRead');await key('Control','keyDown');await probe.until(async()=>graph.nodes[(await stats()).node]?.source?.file.startsWith('16a_'),'existing chapter body',180000);await key('Control','keyUp');
 await delay(800);await probe.capture('returned-existing-body.png');assert.deepEqual(probe.errors,[]);
 }
 assert.deepEqual(probe.errors,[]);
 const report={ok:true,executable,checkpoint,work,world,returned:entryOnly?null:last.node,entryOnly,scope:entryOnly?'Final regenerated scene/blueprint startup and the exact prior B-menu Continue only; already-passed selected route is not replayed.':'Actual isolated prior B-menu Continue, repaired stair scene pixels, and return to unchanged chapter body. Not a full campaign or human-duration test.'};
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({ok:true,work}));
}catch(e){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:e.stack,last,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw e;}finally{await probe?.stop?.();}
