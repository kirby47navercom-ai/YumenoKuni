// Reuse the verified published cook, replacing only reviewed Nonstop resources.
// One output archive; no second private project/content copy and no QA BP graph.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import{createHash}from'node:crypto';import{pathToFileURL}from'node:url';
import{approvedPanicBuilder}from'./approved-panic-build.mjs';
const game=path.resolve(import.meta.dirname,'..'),work=path.join(game,'Saved/nonstop-all-20261106'),read=async p=>JSON.parse(await fs.readFile(p,'utf8')),hash=b=>createHash('sha256').update(b).digest('hex');
const integration=await read(path.join(work,'integration.json')),base=await read(path.join(integration.publishedOutput,'build-report.json')),manifest=await read(path.join(base.output,'game.hbpack.json'));
assert.equal((await read(path.join(game,'build-result.json'))).id,integration.published,'A newer publication needs integration before building');
const tag=process.argv.find(a=>a.startsWith("--tag="))?.slice(6)||"nonstop-source-hud-v8-20261106";const module=await read(path.join(game,"Saved/game-trial-work-20261102/game-module-"+tag+".json")),assets=await read(path.join(work,'integrated-assets.json')),overlays=new Map(assets.overlays.map(r=>[r.path,r]));
const engine=module.engineSDKRoot,load=async n=>import(pathToFileURL(path.join(engine,n)));
const{readProjectManifest}=await load('tools/project-manifest.mjs'),{fileContent}=await load('tools/build-content.mjs'),{canonicalNativeText,parseNativeHeader}=await load('prototype/native-model.js'),{nativeSignature}=await load('tools/build-game.mjs');
const record=await readProjectManifest(path.join(game,'YumenoKuni.hbproject'));assert.equal(record.manifest.id,manifest.id);assert.equal(record.manifest.startupBlueprint,manifest.startupBlueprint);
const{openGameResources}=await import(pathToFileURL(path.join(base.output,'tools/game-resource-archive.mjs'))),archive=await openGameResources(path.join(base.output,manifest.contentArchive.path)),content=new Map(),qa=assets.qa;
const flat=await read(path.join(qa,'game.hbpack.json')),flatRows=new Map(flat.files.map(r=>[r.path,r])),sources=[];
try{
 for(const[name,row]of archive.entries){
  if(overlays.has(name))continue;
  if(/\.(json|gltf|h|hpp|hh|inl|cpp|cc|cxx|c)$/i.test(name))content.set(name,await archive.read(name));
  else{assert.equal(flatRows.get('Content/'+name)?.sha256,row.sha256,'QA retained resource hash: '+name);const value=await fileContent(path.join(qa,'Content',name),{root:qa});assert.equal(value.length,row.bytes);content.set(name,value);}
 }
 for(const[name,row]of overlays){const bytes=await fs.readFile(path.join(work,'integrated-assets',name));assert.equal(hash(bytes),row.sha256);content.set(name,bytes);}
 for(const[name,digest]of Object.entries(module.sourceSHA256)){const bytes=content.get(name);assert(Buffer.isBuffer(bytes));assert.equal(hash(bytes),digest,'Compiled source: '+name);sources.push({path:name,content:bytes.toString('utf8')});}
 const header=canonicalNativeText(content.get('Source/Yumeno.h').toString()),source=canonicalNativeText(content.get('Source/Yumeno.cpp').toString()),entry={headerPath:'Source/Yumeno.h',sourcePath:'Source/Yumeno.cpp'};
 const bpName='Assets/Blueprints/BP_Yumeno.hbblueprint.json',bp=JSON.parse(await archive.read(bpName));assert.equal(bp.nodes.length,2,'Retain published graph, never diagnostic print nodes');Object.assign(bp.native,entry,parseNativeHeader(header,{files:sources,sourcePath:entry.headerPath}));delete bp.native.header;delete bp.native.source;content.set(bpName,Buffer.from(JSON.stringify(bp)));
 const signature=nativeSignature(header,source,entry),natives=new Map([[signature,{header,source,...entry,files:sources}]]),runtime=await read(path.join(work,'runtime-selection.json'));assert.equal(hash(await fs.readFile(runtime.player)),runtime.sha256);
 const adapter=await approvedPanicBuilder({root:game,engineRoot:engine,player:runtime.player,compileMs:300000});
 const report={...base,files:content.size,verifiedNativeSnapshot:{base:base.id,sourceSHA256:module.sourceSHA256,nonstopOnly:!process.argv.includes("--all-ui"),allSourceUI:process.argv.includes("--all-ui")},warnings:base.warnings||[]};delete report.id;delete report.output;delete report.executable;
 const result=await adapter.build(record,base.profile,{content,natives,report},{onProgress:p=>console.log(p)});result.approvedPanicRuntime=adapter.provenance;result.engineSDKRoot=engine;
 const builtManifest=await read(path.join(result.output,'game.hbpack.json')),packed=await openGameResources(path.join(result.output,builtManifest.contentArchive.path));
 let retained=0,changed=0;try{for(const[name,row]of archive.entries){const expected=name===bpName?hash(content.get(name)):overlays.get(name)?.sha256||row.sha256;assert.equal(packed.entries.get(name)?.sha256,expected,'Packed parity: '+name);overlays.has(name)?changed++:retained++;}for(const[name,row]of overlays)assert.equal(packed.entries.get(name)?.sha256,row.sha256);}finally{await packed.close();}
 const parity={ok:true,id:result.id,base:base.id,retained,changed,overlays:overlays.size,compiledSources:sources.length,qaGraphIncluded:false,engineModified:false};
 await fs.writeFile(path.join(work,'integrated-build-result.json'),JSON.stringify(result,null,2));await fs.writeFile(path.join(work,'integrated-package-parity.json'),JSON.stringify(parity,null,2));await fs.writeFile(path.join(result.output,'build-report.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({id:result.id,output:result.output,parity}));
}finally{await archive.close();}
