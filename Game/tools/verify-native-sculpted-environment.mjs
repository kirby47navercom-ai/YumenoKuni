// Environment presentation fixtures only. Physical native input/capture; no played-route claim.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {makeNode,connect} from '../../../engineCreate/prototype/blueprint-model.js';
import {createOwnedNativePackage} from './native-owned-package.mjs';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root);
const build=JSON.parse(await fs.readFile(process.argv.find(v=>v.startsWith('--build-result='))?.slice(15)||path.join(root,'Saved/game-trial-work-20261102/current-flat-build-result.json'),'utf8'));
const overrides=process.argv.find(v=>v.startsWith('--content-overrides='))?.slice(20);
const reuse=process.argv.find(v=>v.startsWith('--reuse-package='))?.slice(16);
const room=process.argv.find(v=>v.startsWith('--room='))?.slice(7);assert(!room||/^[a-z_]+$/.test(room));if(room)assert(JSON.parse(await fs.readFile(path.join(repo,'art/space_v4/runtime_v1/copy_manifest.json'),'utf8')).some(r=>r.to==='Assets/Art/explore3d/'+room+'.glb'),'Known authored room required');
const work=path.join(root,'Saved/native-sculpted-environment-'+Date.now());await fs.mkdir(work);
let prepared;
if(reuse){
 const owned=JSON.parse(await fs.readFile(path.join(reuse,'owned-package.json'),'utf8'));assert.equal(owned.source,build.output);assert.equal(owned.stats,true);
 const manifest=JSON.parse(await fs.readFile(path.join(owned.output,'game.hbpack.json'),'utf8'));prepared={output:owned.output,manifest,executable:path.join(owned.output,manifest.windowsApplication.executable)};
 if(overrides){
  const content=JSON.parse(await fs.readFile(overrides,'utf8'));
  for(const [name,source]of Object.entries(content)){
   assert(name.startsWith('Content/Assets/')&&!name.includes('..')&&owned.alterations.some(r=>r.name===name));
   const bytes=await fs.readFile(source),file=path.join(owned.output,name),temporary=file+'.qa-refresh.tmp';await fs.writeFile(temporary,bytes,{flag:'wx'});await fs.rename(temporary,file);
   const sha256=createHash('sha256').update(bytes).digest('hex');Object.assign(manifest.files.find(r=>r.path===name),{bytes:bytes.length,sha256});owned.alterations.push({name,after:{bytes:bytes.length,sha256},scope:'Refreshed declared game art only in closed owned QA package.'});
  }
 }
 await fs.writeFile(path.join(owned.output,'game.hbpack.json'),JSON.stringify(manifest));
 await fs.writeFile(path.join(work,'owned-package.json'),JSON.stringify(owned,null,2));
}else prepared=await createOwnedNativePackage({source:build.output,work,stats:true,gameContentOverrides:overrides});
const name='Content/Assets/Blueprints/BP_Yumeno.hbblueprint.json',file=path.join(prepared.output,name),bp=JSON.parse(await fs.readFile(file,'utf8'));
const allFixtures=[['F5','plaza-day',0,0,'plaza'],['F6','plaza-night',0,1,'plaza'],['F7','plaza-evening',0,2,'plaza'],['F8','hotel-corridor',10,0,'hotel_corridor']],fixtures=room?[['c',room,-1,0,room]]:process.argv.includes('--day-only')?allFixtures.slice(0,1):allFixtures;
if(!reuse&&!room)for(const [key,label,index,phase]of fixtures){const input=makeNode('input',100,900),call=makeNode('nativeCall',400,900);input.options={key};call.nativeId='Yumeno.DebugV4OutdoorFixture';call.inputValues={index,phase};bp.nodes.push(input,call);assert(connect(bp,{node:input.id,pin:'then'},{node:call.id,pin:'exec'}).ok);}
const bytes=Buffer.from(JSON.stringify(bp)),hash=b=>createHash('sha256').update(b).digest('hex');await fs.writeFile(file,bytes);Object.assign(prepared.manifest.files.find(r=>r.path===name),{bytes:bytes.length,sha256:hash(bytes)});await fs.writeFile(path.join(prepared.output,'game.hbpack.json'),JSON.stringify(prepared.manifest));
const receipt=JSON.parse(await fs.readFile(path.join(work,'owned-package.json'),'utf8'));receipt.alterations.push({name,after:{bytes:bytes.length,sha256:hash(bytes)},scope:'QA-only authored environment fixture key bindings; no gameplay outcome/progression acceptance.'});await fs.writeFile(path.join(work,'owned-package.json'),JSON.stringify(receipt,null,2));
let p;const rows=[];
try{
 let resume;
 if(room){
  const source=path.join(root,'Saved/native-outdoor-checkpoint-1793680307759/actual-native-savegames.json'),original=await fs.readFile(source),save=JSON.parse(original);
  const key=Object.keys(save.items).find(k=>k.startsWith('hbengine.savegame.json.yumeno-progress-v4.project.')),head=JSON.parse(save.items[key]);head.worldId=room;save.items[key]=JSON.stringify(head);save.fixture=true;save.fixtureEntry='Environment art fixture derived from existing explicit map QA save; worldId selects '+room+'. Not normal progression.';
  resume=path.join(work,'room-art-fixture-save.json');await fs.writeFile(resume,JSON.stringify(save));assert.equal(hash(await fs.readFile(source)),hash(original));
 }
 p=await nativeWindowProbe({source:build.output,prepared,work,resume,maxFrames:null,heartbeatTimeoutMs:120000});
 for(const [key,label,index,phase,space]of fixtures){
  await p.tap(key);await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.mode==='explore'&&!s.scenes.loading?s:false;},label+' scene ready',120000);
  if((await p.stats()).world.space!==space)await p.tap(key);
  await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.mode==='explore'&&s.world.space===space&&!s.scenes.loading?s:false;},label+' ready',30000);
  await p.sampled(30);const before=await p.stats();await p.capture(label);
  const ui=JSON.parse(await fs.readFile(path.join(work,label+'.ui.json'),'utf8'));
  const scene=ui.world.find(o=>o.id==='ExploreGeometry');assert(scene?.mesh);
  const context=ui.world.find(o=>o.id==='ExteriorContext'),world=JSON.parse(await fs.readFile(path.join(repo,'art/space_v4/runtime_v1/world.json'),'utf8'));assert.equal(!!context?.mesh,!!world.spaces[space].outdoor);
  const sun=ui.world.find(o=>o.id===`Outdoor${phase}_sun`);rows.push({label,space,phase,geometry:scene.mesh,image:path.join(work,label+'.png'),sun,before});
  if(index===0&&phase===0){await p.key('w',true);await p.sampled(35);await p.key('w',false);await p.capture('plaza-day-close');assert.notDeepEqual((await p.stats()).world.position,before.world.position);}
 }
 const runtime=await p.close();p=null;
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,build:build.id,work,overrides:overrides||null,fixtures:true,rows,runtime,scope:'Actual native fixture render, model presence, day/night/evening and corridor scene ownership. Visual review is separate. Not a normal played route, all-room or performance acceptance.'},null,2));console.log(JSON.stringify({ok:true,work}));
}catch(e){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:e.stack,last:await p?.stats().catch(()=>null)},null,2));throw e;}finally{await p?.close().catch(()=>{});}
