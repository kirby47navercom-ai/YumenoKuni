import{applyTrialDialogueResponsive}from'./v3-trial-dialogue-source.mjs';
import{centerEndingSourceCanvas}from'./v4-agreement-cast.mjs';
import{assetKind}from'../../../engineCreate/tools/project-service.mjs';
import{makeNode,connect}from'../../../engineCreate/prototype/blueprint-model.js';
import{mergeNonstopCook}from'./merge-nonstop-cook.mjs';
import fs from'node:fs/promises';import path from'node:path';import assert from'node:assert/strict';import{createHash}from'node:crypto';import{pathToFileURL}from'node:url';import{applyKotodamaScene,applyKotodamaFlight}from'./v4-kotodama-flight.mjs';
const game=path.resolve(import.meta.dirname,'..'),work=path.join(game,'Saved/nonstop-all-20261106'),read=async p=>JSON.parse(await fs.readFile(p,'utf8')),receipt=await read(path.join(work,'integration.json')),base=receipt.publishedOutput;
const qa=path.join(game,'Saved/native-panic-views-1793690486425/package'),prior=await read(path.join(qa,'game.hbpack.json')),known=new Map(prior.files.map(r=>[r.path,r])),manifest=await read(path.join(base,'game.hbpack.json'));
const{openGameResources}=await import(pathToFileURL(path.join(base,'tools/game-resource-archive.mjs'))),archive=await openGameResources(path.join(base,manifest.contentArchive.path));
const hash=b=>createHash('sha256').update(b).digest('hex'),rows=new Map(),overlays=new Map();let copied=0;
async function publish(name,bytes){const target=path.join(qa,name);await fs.mkdir(path.dirname(target),{recursive:true});await fs.writeFile(target+'.ns.tmp',bytes);await fs.rename(target+'.ns.tmp',target);rows.set(name,{path:name,bytes:bytes.length,sha256:hash(bytes)});copied++;}
async function overlay(name,bytes){await publish('Content/'+name,bytes);overlays.set(name,rows.get('Content/'+name));const file=path.join(work,'integrated-assets',name);await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file,bytes);}
try{
 for(const row of manifest.files){if(row.path===manifest.contentArchive.path||row.path===manifest.nativeModules[0].binary)continue;rows.set(row.path,row);if(known.get(row.path)?.sha256!==row.sha256)await publish(row.path,await fs.readFile(path.join(base,row.path)));}
 for(const[name,row]of archive.entries){rows.set('Content/'+name,{path:'Content/'+name,bytes:row.bytes,sha256:row.sha256});if(known.get('Content/'+name)?.sha256!==row.sha256)await publish('Content/'+name,await archive.read(name));}
 for(const file of await fs.readdir(path.join(game,'Assets/Art/ui/nonstop_source')))await overlay('Assets/Art/ui/nonstop_source/'+file,await fs.readFile(path.join(game,'Assets/Art/ui/nonstop_source',file)));
 for(const name of ['Assets/UI/NonstopSourceHud.hbwidget.json','Assets/Data/nonstop_source_hud.json','Assets/Fonts/pretendard/Pretendard-Regular.otf'])await overlay(name,await fs.readFile(path.join(game,name)));
 for(const file of await fs.readdir(path.join(game,'Assets/Art/ui/v3/dialogue/source')))if(file.endsWith('.png'))await overlay('Assets/Art/ui/v3/dialogue/source/'+file,await fs.readFile(path.join(game,'Assets/Art/ui/v3/dialogue/source',file)));
 await overlay('Assets/Data/v4_story/dialogue_layout.json',await fs.readFile(path.join(game,'Assets/Data/v4_story/dialogue_layout.json')));
 const agreement=await read(path.join(game,'Saved/nonstop-guidance-20261106/agreement-cast/generated-assets.json')).catch(e=>{if(e.code==='ENOENT')return null;throw e;});
 if(agreement)for(const row of agreement.resources||agreement.changes)if(row.path.startsWith('Assets/')){const bytes=await fs.readFile(row.sourcePath||path.join(game,row.path));assert.equal(hash(bytes),row.sha256);await overlay(row.path,bytes);}
 const layout=await mergeNonstopCook({game,work,archive,overlay});layout.nonstopOriginalClock=await read(path.join(game,'Assets/Data/nonstop_source_hud.json'));await overlay('Assets/Data/gpu_trial_layout.json',Buffer.from(JSON.stringify(layout)));
 await overlay('Assets/UI/Main.hbwidget.json',Buffer.from(JSON.stringify(applyTrialDialogueResponsive(JSON.parse(await archive.read('Assets/UI/Main.hbwidget.json'))))));
 await overlay('Assets/UI/EndingSourceV4.hbwidget.json',Buffer.from(JSON.stringify(centerEndingSourceCanvas(JSON.parse(await archive.read('Assets/UI/EndingSourceV4.hbwidget.json'))))));
 const scene=applyKotodamaScene(JSON.parse(await archive.read('Assets/Scenes/DebateHud.hbscene.json')));await overlay('Assets/Scenes/DebateHud.hbscene.json',Buffer.from(JSON.stringify(scene)));
 const debateFx=applyKotodamaFlight(JSON.parse(await archive.read('Assets/UI/DebateFX.hbwidget.json')));await overlay('Assets/UI/DebateFX.hbwidget.json',Buffer.from(JSON.stringify(debateFx)));
 const glyphs=await read(path.resolve(game,'../art/nonstop_solid_type/manifest.json'));for(const g of glyphs.glyphs){const name='u_'+g.codepoint.toString(16)+'_w.glb',relative='Assets/Art/nonstop_solid_type/'+name;const bytes=await fs.readFile(path.resolve(game,'../art/nonstop_solid_type',name));if(hash(bytes)!==archive.entries.get(relative)?.sha256)await overlay(relative,bytes);}
 if(process.argv.includes('--all-ui')){
  const ui=await read(path.join(game,'Saved/all-ui-source-20261107/generated.json'));
  for(const row of ui.files){if(row.path==='Assets/Data/gpu_trial_layout.json')continue;const bytes=await fs.readFile(row.sourcePath||path.join(game,row.path));assert.equal(hash(bytes),row.sha256,'Reviewed UI output changed '+row.path);await overlay(row.path,bytes);}
  // Keep the published Nonstop glyph/style banks, adding only reviewed UI layout pointers/glyphs.
  const updated=await read(path.join(game,'Assets/Data/gpu_trial_layout.json'));
  for(const k of ['anagramLayout','showdownLayout'])if(updated[k])layout[k]=updated[k];
  layout.glyphs=[...new Map([...layout.glyphs,...updated.glyphs].map(r=>[JSON.stringify(r),r])).values()];
  await overlay('Assets/Data/gpu_trial_layout.json',Buffer.from(JSON.stringify(layout)));
 }
 const tag=process.argv.find(a=>a.startsWith('--tag='))?.slice(6)||'nonstop-source-hud-v8-20261106';const moduleName='Binaries/'+tag+'.exe';await publish(moduleName,await fs.readFile(path.join(game,'Saved/game-trial-work-20261102/game-'+tag+'.exe')));manifest.nativeModules[0].binary=moduleName;
 const {canonicalNativeText}=await import(pathToFileURL(path.resolve(game,'../../engineCreate/prototype/native-model.js')));const {nativeModuleKey}=await import(pathToFileURL(path.resolve(game,'../../engineCreate/prototype/native-entry.js')));const header=await fs.readFile(path.join(work,'integrated/Source/Yumeno.h'),'utf8'),source=await fs.readFile(path.join(work,'integrated/Source/Yumeno.cpp'),'utf8');manifest.nativeModules[0].signature=hash(Buffer.from(nativeModuleKey(canonicalNativeText(header),canonicalNativeText(source),{headerPath:'Source/Yumeno.h',sourcePath:'Source/Yumeno.cpp'})));
 const compiled=await read(path.join(game,'Saved/game-trial-work-20261102/game-module-'+tag+'.json'));for(const name of await fs.readdir(path.join(work,'integrated/Source'))){const bytes=await fs.readFile(path.join(work,'integrated/Source',name));assert.equal(hash(bytes),compiled.sourceSHA256['Source/'+name],'Compiled UI source snapshot changed: '+name);await overlay('Source/'+name,bytes);}
 const bpName='Assets/Blueprints/BP_Yumeno.hbblueprint.json',bp=JSON.parse(await archive.read(bpName)),update=bp.nodes.find(n=>n.nativeId==='Yumeno.Update');assert(update);
 const readStats=makeNode('nativeCall',700,180),printStats=makeNode('print',1000,180),readAim=makeNode('nativeCall',700,700),printAim=makeNode('print',1000,700);readStats.nativeId='Yumeno.Stats';readAim.nativeId='Yumeno.AimStats';bp.nodes.push(readStats,printStats,readAim,printAim);
 for(const[from,to]of [[{node:update.id,pin:'then'},{node:printStats.id,pin:'exec'}],[{node:readStats.id,pin:'result'},{node:printStats.id,pin:'message'}],[{node:printStats.id,pin:'then'},{node:printAim.id,pin:'exec'}],[{node:readAim.id,pin:'result'},{node:printAim.id,pin:'message'}]]){const r=connect(bp,from,to);assert(r.ok,r.reason);}await publish('Content/'+bpName,Buffer.from(JSON.stringify(bp)));
 delete manifest.contentArchive;manifest.files=[...rows.values()];const entries=new Map(manifest.entries.map(r=>[r.path,r]));for(const[name,row]of overlays)entries.set(name,{...entries.get(name),path:name,name:path.basename(name),kind:assetKind(name),bytes:row.bytes,sha256:row.sha256});manifest.entries=[...entries.values()];
 await fs.writeFile(path.join(qa,'game.hbpack.json'),JSON.stringify(manifest));await fs.writeFile(path.join(work,'integrated-assets.json'),JSON.stringify({published:receipt.published,overlays:[...overlays].map(([name,row])=>({...row,path:name})),copied,qa,originalCacheReused:true},null,2));console.log(JSON.stringify({published:receipt.published,copied,overlays:overlays.size,newWholePackage:false}));
}finally{await archive.close();}
