// Explicit environment fixture, using the game's existing authored-map QA entry.
// This is not evidence of a normally played story route or unlocked destinations.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {makeNode,connect} from '../../../engineCreate/prototype/blueprint-model.js';
import {createOwnedNativePackage} from './native-owned-package.mjs';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const root=path.resolve(import.meta.dirname,'..'),base=path.join(root,'Saved/game-trial-work-20261102');
const build=JSON.parse(await fs.readFile(path.join(base,'current-flat-build-result.json'),'utf8'));
const work=path.join(root,'Saved/native-outdoor-checkpoint-'+Date.now());
await fs.mkdir(work);
const prepared=await createOwnedNativePackage({source:build.output,work,stats:true,gameContentOverrides:path.join(base,'architecture-overrides.json')});
const name='Content/Assets/Blueprints/BP_Yumeno.hbblueprint.json',file=path.join(prepared.output,name),bp=JSON.parse(await fs.readFile(file,'utf8'));
const input=makeNode('input',100,900),call=makeNode('nativeCall',400,900);
input.options={key:'F9'};call.nativeId='Yumeno.DebugV4OutdoorFixture';call.inputValues={index:0,phase:0};
bp.nodes.push(input,call);const edge=connect(bp,{node:input.id,pin:'then'},{node:call.id,pin:'exec'});assert(edge.ok,edge.reason);
const bytes=Buffer.from(JSON.stringify(bp)),sha=b=>createHash('sha256').update(b).digest('hex');await fs.writeFile(file,bytes);
const row=prepared.manifest.files.find(r=>r.path===name);Object.assign(row,{bytes:bytes.length,sha256:sha(bytes)});
await fs.writeFile(path.join(prepared.output,'game.hbpack.json'),JSON.stringify(prepared.manifest));
const ownedReceipt=JSON.parse(await fs.readFile(path.join(work,'owned-package.json'),'utf8'));
ownedReceipt.alterations.push({name,after:{bytes:bytes.length,sha256:sha(bytes)},scope:'QA-only F9 binding invokes the existing DebugV4OutdoorFixture(0,0); explicit environment fixture, not played progression.'});
await fs.writeFile(path.join(work,'owned-package.json'),JSON.stringify(ownedReceipt,null,2));
let p;
try{
 p=await nativeWindowProbe({source:build.output,work,prepared,maxFrames:null});
 await p.tap('F9');await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.scenes.explore&&!s.scenes.loading;},'environment fixture scene',90000);
 if((await p.stats()).world.space!=='plaza')await p.tap('F9');
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.mode==='explore'&&s.world.space==='plaza';},'explicit plaza fixture');
 const before=await p.stats();await p.key('ArrowRight',true);await p.sampled(12);await p.key('ArrowRight',false);
 await p.key('w',true);await p.sampled(12);await p.key('w',false);
 const moved=await p.stats();assert.notEqual(moved.world.yaw,before.world.yaw);assert.notDeepEqual(moved.world.position,before.world.position);
 await p.capture('outdoor-moving');
 await p.tap('Tab');await p.click(1047,480);if((await p.stats()).padPage!==5){await p.tap('Backspace');await p.click(1047,480);}
 assert.equal((await p.stats()).padPage,5);await padSystemAction(p.stats,p.tap,'save');await p.sampled(15);await p.tap('Tab');
 const saveDir=path.join(work,'State/Saves'),items={};
 for(const f of await fs.readdir(saveDir))if(f.endsWith('.json')){const value=await fs.readFile(path.join(saveDir,f),'utf8');JSON.parse(value);items['hbengine.savegame.json.'+decodeURIComponent(f.slice(0,-5))+'.project.'+encodeURIComponent(prepared.manifest.id)]=value;}
 const saved=JSON.parse(Object.entries(items).find(([k])=>k.startsWith('hbengine.savegame.json.yumeno-progress-v4.project.'))[1]);assert.equal(saved.worldId,'plaza');
 const checkpoint=path.join(work,'actual-native-savegames.json');await fs.writeFile(checkpoint,JSON.stringify({version:1,items,fixture:true,fixtureEntry:'Existing DebugV4OutdoorFixture(0,0), followed by actual native camera/walk/manual save. Not normal-route progression.'}));
 const runtime=await p.close();p=null;
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,fixture:true,baseBuild:build.id,work,checkpoint,beforeWorld:before.world,movedWorld:moved.world,savedNode:saved.node,runtime,scope:'Explicit environment QA fixture; actual geometry, physical movement and manual save. No normally played route or destination-unlock acceptance.'},null,2));
 await fs.writeFile(path.join(base,'outdoor-fixture-checkpoint.json'),JSON.stringify({checkpoint,work,fixture:true}));
 console.log(JSON.stringify({ok:true,work,checkpoint,fixture:true}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,last:await p?.stats().catch(()=>null)},null,2));throw error;}
finally{await p?.close().catch(()=>{});}
