// Reproducible QA package; shipped output and engine originals remain immutable.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {makeNode,connect} from '../../../engineCreate/prototype/blueprint-model.js';
const hash=b=>createHash('sha256').update(b).digest('hex');
export async function createOwnedNativePackage({source,work,candidate,rendererCandidate,runnerCandidate,widgetCandidate,playerCandidate,migrationCandidate,uiPngCandidate,uiRuntimeCandidate,uiFrameCandidate,transportCandidate,paintCandidate,gameModuleCandidate,gameContentOverrides,stats=false,aimStats=false}){
 const directories=new Map(),mkdir=dir=>{if(!directories.has(dir))directories.set(dir,fs.mkdir(dir,{recursive:true}));return directories.get(dir);};
 const manifest=JSON.parse(await fs.readFile(path.join(source,'game.hbpack.json'),'utf8'));assert.equal(manifest.windowsRuntime,'native');assert(!manifest.contentArchive||!stats&&!gameContentOverrides,'Stats/content overrides require a verified flat QA representation: native archive lookup ignores loose overrides');const output=path.join(work,'package');await fs.mkdir(output,{recursive:true});
 const changed=new Set([...(candidate?['tools/headless-model.mjs']:[]),...(rendererCandidate?['prototype/native-scene-renderer.js']:[]),...(runnerCandidate?['tools/native-game-runner.mjs']:[]),...(widgetCandidate?['tools/native-widget-layer.mjs']:[]),...(playerCandidate?[manifest.windowsApplication.executable]:[]),...(migrationCandidate?['tools/native-save-migration.mjs']:[]),...(uiPngCandidate?['tools/native-ui-png.mjs']:[]),...(stats?['Content/Assets/Blueprints/BP_Yumeno.hbblueprint.json']:[])]);
 if(paintCandidate)changed.add('tools/native-widget-paint.mjs');
 if(transportCandidate)changed.add('prototype/native-transport.js');
 if(uiRuntimeCandidate)changed.add('prototype/ui-runtime.js');
 if(uiFrameCandidate)changed.add('tools/native-ui-frame.mjs');
 if(gameModuleCandidate){assert.equal(manifest.nativeModules.length,1);changed.add(manifest.nativeModules[0].binary);}
 const gameContent=gameContentOverrides?JSON.parse(await fs.readFile(gameContentOverrides,'utf8')):{};
 for(const [name,file]of Object.entries(gameContent)){assert(name.startsWith('Content/Assets/')&&!name.includes('..')&&!name.includes('\\')&&path.isAbsolute(file));changed.add(name);}
 for(let at=0;at<manifest.files.length;at+=32)await Promise.all(manifest.files.slice(at,at+32).map(async row=>{assert(!path.isAbsolute(row.path)&&!row.path.split('/').some(x=>x==='..'));const to=path.join(output,row.path);await mkdir(path.dirname(to));if(changed.has(row.path))await fs.copyFile(path.join(source,row.path),to);else await fs.link(path.join(source,row.path),to);}));

 const alterations=[],fileRows=new Map(manifest.files.map(row=>[row.path,row])),entryPaths=new Set(manifest.entries.map(row=>row.path));
 const write=async(name,bytes)=>{const file=path.join(output,name);let row=fileRows.get(name);assert(row||Object.hasOwn(gameContent,name)||['tools/native-save-migration.mjs','tools/native-ui-png.mjs','tools/native-ui-frame.mjs'].includes(name));await mkdir(path.dirname(file));await fs.writeFile(file,bytes);const old=row?{bytes:row.bytes,sha256:row.sha256}:null;if(!row){row={path:name};manifest.files.push(row);fileRows.set(name,row);}Object.assign(row,{bytes:Buffer.byteLength(bytes),sha256:hash(bytes)});alterations.push({name,before:old,after:{bytes:row.bytes,sha256:row.sha256}});};
 const contentRows=Object.entries(gameContent);for(let at=0;at<contentRows.length;at+=32)await Promise.all(contentRows.slice(at,at+32).map(async([name,file])=>{await write(name,await fs.readFile(file));const asset=name.slice(8);if(!entryPaths.has(asset)){entryPaths.add(asset);manifest.entries.push({path:asset,name:path.basename(asset),kind:asset.endsWith('.hbwidget.json')?'widget':asset.endsWith('.hbspriterig.json')?'spriterig':asset.endsWith('.hbsprite.json')?'sprite':asset.endsWith('.hbscene.json')?'scene':'texture'});}}));

 if(candidate)await write('tools/headless-model.mjs',await fs.readFile(candidate));
 if(gameModuleCandidate)await write(manifest.nativeModules[0].binary,await fs.readFile(gameModuleCandidate));
 if(rendererCandidate)await write('prototype/native-scene-renderer.js',await fs.readFile(rendererCandidate));
 if(runnerCandidate)await write('tools/native-game-runner.mjs',await fs.readFile(runnerCandidate));
 if(widgetCandidate)await write('tools/native-widget-layer.mjs',await fs.readFile(widgetCandidate));
 if(uiPngCandidate)await write('tools/native-ui-png.mjs',await fs.readFile(uiPngCandidate));
 if(paintCandidate)await write('tools/native-widget-paint.mjs',await fs.readFile(paintCandidate));
 if(transportCandidate)await write('prototype/native-transport.js',await fs.readFile(transportCandidate));
 if(uiRuntimeCandidate)await write('prototype/ui-runtime.js',await fs.readFile(uiRuntimeCandidate));
 if(uiFrameCandidate)await write('tools/native-ui-frame.mjs',await fs.readFile(uiFrameCandidate));
 if(playerCandidate)await write(manifest.windowsApplication.executable,await fs.readFile(playerCandidate));
 if(migrationCandidate)await write('tools/native-save-migration.mjs',(await fs.readFile(migrationCandidate,'utf8')).replace("from '../../../engineCreate/prototype/game-json.js'","from '../prototype/game-json.js'"));
 if(stats){
  const name='Content/Assets/Blueprints/BP_Yumeno.hbblueprint.json',bp=JSON.parse(await fs.readFile(path.join(output,name),'utf8')),update=bp.nodes.find(n=>n.nativeId==='Yumeno.Update');assert(update);
  const read=makeNode('nativeCall',700,180);read.nativeId='Yumeno.Stats';const save=makeNode('print',1000,180);bp.nodes.push(read,save);
  for(const[from,to]of [[{node:update.id,pin:'then'},{node:save.id,pin:'exec'}],[{node:read.id,pin:'result'},{node:save.id,pin:'message'}]]){const result=connect(bp,from,to);assert(result.ok,result.reason);}
  if(aimStats){const aim=makeNode('nativeCall',700,700),print=makeNode('print',1000,700);aim.nativeId='Yumeno.AimStats';bp.nodes.push(aim,print);for(const[from,to]of [[{node:save.id,pin:'then'},{node:print.id,pin:'exec'}],[{node:aim.id,pin:'result'},{node:print.id,pin:'message'}]]){const r=connect(bp,from,to);assert(r.ok,r.reason);}}
  await write(name,JSON.stringify(bp));
 }
 await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest,null,2));
 await fs.writeFile(path.join(work,'owned-package.json'),JSON.stringify({source,output,alterations,stats,sourcePackageOrEngineModified:false,scope:gameModuleCandidate?'Owned game C++ module substitution and optional read-only Stats binding. Engine files and base package remain unchanged. Included source listings remain the base package: consult the separate game-module receipt for tested source hashes. Diagnostic output is not a shipping acceptance claim.':'Only an owned candidate and optional read-only Stats -> intercepted QA log binding. Candidate/instrumented output is never a shipping acceptance claim.'},null,2));
 return {output,executable:path.join(output,manifest.windowsApplication.executable),manifest};
}
export async function importLegacySaveForQA(file,state,id){
 const source=JSON.parse(await fs.readFile(file,'utf8'));assert.equal(source.version,1);const prefix='hbengine.savegame.json.',suffix='.project.'+encodeURIComponent(id),destination=path.join(state,'Saves');await fs.mkdir(destination,{recursive:true});let count=0;
 for(const[key,value]of Object.entries(source.items))if(key.startsWith(prefix)&&key.endsWith(suffix)){
  const slot=key.slice(prefix.length,-suffix.length);assert(slot&&slot.length<=80&&!/[\\/\x00-\x1f]/.test(slot)&&!['.','..'].includes(slot));JSON.parse(value);await fs.writeFile(path.join(destination,encodeURIComponent(slot)+'.json'),value,{flag:'wx'});count++;
 }
 assert(count>0);return {source:file,sourceSha256:hash(await fs.readFile(file)),slots:count,state,scope:'Owned QA copy from the unchanged actual WebView save to the native per-slot format. Not automatic player-profile migration.'};
}
