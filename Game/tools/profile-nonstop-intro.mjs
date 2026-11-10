import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url))),built=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/nonstop-profile-'+Date.now());await fs.mkdir(work,{recursive:true});
process.env.HB_PLAYER_SOAK_HOURS='1';let probe;
const wait=ms=>new Promise(r=>setTimeout(r,ms));
try{
 probe=await editorWindowProbe({work,mode:'player',executable:built.executable});
 await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
 const key=type=>probe.cdp('Input.dispatchKeyEvent',{type,key:'t',code:'KeyT',windowsVirtualKeyCode:84});
 await key('keyDown');await wait(90);await key('keyUp');await wait(400);
 const stages=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/trials/11c.json'),'utf8')).stages;
 const index=stages.findIndex(x=>x.kind==='nonstop');
 await probe.evaluate(`(()=>{
  const p=window.hbPlayerDebug.runtimePrototype(),original=p.applyNativeOperations;
  window.__opSamples=[];window.__suppressIntroTransforms=false;
  p.applyNativeOperations=async function(ops,b){
   const start=performance.now();
   const filtered=window.__suppressIntroTransforms?ops.filter(o=>!(o.key.startsWith('uiSet')&&['uiSetPosition','uiSetScale','uiSetOpacity'].includes(o.key))):ops;
   try{return await original.call(this,filtered,b);}
   finally{window.__opSamples.push({ms:performance.now()-start,keys:ops.map(o=>o.key),textureWrites:ops.filter(o=>o.args?.property==='texture').map(o=>({key:o.key,target:o.args.target,value:o.args.value})),timing:{...this.nativeTiming}});}
  };
 })()`);
 const run=async(suppress=false)=>{
  await probe.evaluate(`window.__suppressIntroTransforms=false;window.hbPlayerDebug.call('Driver','Yumeno.DebugJump',{index:${index}})`);
  const duration=await probe.evaluate(`window.hbPlayerDebug.call('Driver','Yumeno.Stats',{}).then(r=>JSON.parse(r.outputs.result).presentation.duration)`);
  await probe.evaluate(`window.__opSamples=[];window.__suppressIntroTransforms=${suppress};window.hbPlayerDebug.resetProfile()`);
  await wait(duration*1000+120);
  return probe.evaluate(`(()=>{const d=window.hbPlayerDebug.inspect();return {suppressIntroTransforms:window.__suppressIntroTransforms,profile:window.hbPlayerDebug.profile(),operations:window.__opSamples,nativeFrameGroups:d.nativeFrameGroups};})()`);
 };
 await run();
 const resourceState=()=>probe.evaluate(`(()=>{const d=window.hbPlayerDebug.inspect();return d.sprites.filter(s=>s.id.startsWith('Seat')).map(s=>({id:s.id,resources:s.resources,image:s.image}));})()`);
 const resourcesBefore=await resourceState(),runs=[];for(const suppress of process.argv.includes('--diagnose-ui')?[false,true,false,true]:[false,false])runs.push(await run(suppress));
 const resourcesAfter=await resourceState();
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({executable:built.executable,runs,resourcesBefore,resourcesAfter},null,2));
 console.log(JSON.stringify({work,runs:runs.map(r=>({suppress:r.suppressIntroTransforms,profile:r.profile,operationSamples:r.operations.length}))}));
}finally{await probe?.stop?.();}
