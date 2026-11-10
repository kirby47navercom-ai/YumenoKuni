// Existing real Pad save must retain its stored yaw after entry camera changes.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/v4-old-entry-view-'+Date.now());
const source=path.join(root,'Saved/v4-fte-editorial-1793500442912/45-2/actual-manual-savegames.json');
const save=JSON.parse(await fs.readFile(source,'utf8')),head=JSON.parse(Object.entries(save.items).find(([k])=>k.includes('yumeno-progress-v4.project.'))[1]);
assert.equal(head.node,'v4:45:F-RE02-B:menu');assert.equal(head.world.garden_rest_area[3],0);
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
await fs.mkdir(path.join(work,'UserData'),{recursive:true});await fs.copyFile(source,path.join(work,'UserData/savegames.json'));
let probe,last;
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
 const stats=async()=>{const r=await probe.evaluate("window.hbPlayerDebug.call('Driver','Yumeno.Stats',{})");return last=JSON.parse(r.outputs.result);};
 for(const type of ['keyDown','keyUp']){await probe.cdp('Input.dispatchKeyEvent',{type,key:'c',code:'KeyC',windowsVirtualKeyCode:67});await new Promise(r=>setTimeout(r,130));}
 await probe.until(async()=>{const s=await stats();return s.node===head.node&&s.choice;},'exact restored interactive FTE menu',60000);
 const current=await stats();assert.equal(current.world.space,'garden_rest_area');assert.equal(current.world.yaw,0);assert.equal(current.world.pitch,0);
 assert.equal(current.choice.pending,-1);assert(!current.routeBlocked&&!current.error);assert.deepEqual(probe.errors,[]);
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,executable,source,node:current.node,storedPose:head.world.garden_rest_area,restoredWorld:current.world,fixture:true,scope:'Cold Continue from an earlier actual manual FTE save. Existing yaw0 preserved; new authored entry yaw50 does not rewrite stored orientation.'},null,2));
 console.log(JSON.stringify({ok:true,work,restoredYaw:current.world.yaw}));
}catch(e){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:e.stack,last},null,2));throw e;}
finally{await probe?.stop?.();}
