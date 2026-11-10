// Preserve published code, UI, artwork and routes; graft only source-reviewed dialogue bytes.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {approvedPanicBuilder} from './approved-panic-build.mjs';
const game=path.resolve(import.meta.dirname,'..'),work=path.join(game,'Saved/voice-rewrite-20261107');
const read=async p=>JSON.parse(await fs.readFile(p,'utf8')),sha=b=>createHash('sha256').update(b).digest('hex');
const base=await read(path.join(work,'base-build.json')),module=await read(path.join(game,'Saved/game-trial-work-20261102/game-module-dialogue-pages-v1-20261107.json'));
assert.equal((await read(path.join(game,'build-result.json'))).id,base.id,'New publication requires a reviewed merge');
const engine=module.engineSDKRoot,load=async n=>import(pathToFileURL(path.join(engine,n)));
const {fileContent}=await load('tools/build-content.mjs'),{readProjectManifest}=await load('tools/project-manifest.mjs'),{nativeSignature}=await load('tools/build-game.mjs');
const {canonicalNativeText,parseNativeHeader}=await load('prototype/native-model.js');
const manifest=await read(path.join(base.output,'game.hbpack.json'));
const {openGameResources}=await import(pathToFileURL(path.join(base.output,'tools/game-resource-archive.mjs')));
const archive=await openGameResources(path.join(base.output,manifest.contentArchive.path));
const flat=[];
for(const name of ['native-panic-views-1793690486425','native-panic-views-anagram-transition-final']){
 const root=path.join(game,'Saved',name,'package');
 const m=await read(path.join(root,'game.hbpack.json')).catch(()=>null);
 if(m&&!m.contentArchive)flat.push({root,rows:new Map(m.files.map(r=>[r.path,r]))});
}
const patch=await read(path.join(work,'runtime-patch.json'));
const changed=new Set(patch.files.map(r=>r.path));
const content=new Map(),sources=[];let retainedFiles=0,archiveBuffers=0;
try{
 for(const [name,row]of archive.entries){
  if(changed.has(name)){const b=await fs.readFile(path.join(work,'runtime',name));const edit=patch.files.find(r=>r.path===name);assert.equal(row.sha256,edit.before);assert.equal(sha(b),edit.after);content.set(name,b);continue;}
  const match=!/\.(json|gltf|h|hpp|hh|inl|cpp|cc|cxx|c)$/i.test(name)&&flat.find(p=>p.rows.get('Content/'+name)?.sha256===row.sha256);
  if(match){const value=await fileContent(path.join(match.root,'Content',name),{root:match.root});assert.equal(value.length,row.bytes);content.set(name,value);++retainedFiles;}
  else{content.set(name,await archive.read(name));++archiveBuffers;}
 }
 for(const [name,digest]of Object.entries(module.sourceSHA256)){const bytes=content.get(name);assert(Buffer.isBuffer(bytes));assert.equal(sha(bytes),digest);sources.push({path:name,content:bytes.toString('utf8')});}
 const header=canonicalNativeText(content.get('Source/Yumeno.h').toString()),source=canonicalNativeText(content.get('Source/Yumeno.cpp').toString()),entry={headerPath:'Source/Yumeno.h',sourcePath:'Source/Yumeno.cpp'};
 const bpName='Assets/Blueprints/BP_Yumeno.hbblueprint.json',bp=JSON.parse(await archive.read(bpName));assert.equal(bp.nodes.length,2);
 Object.assign(bp.native,entry,parseNativeHeader(header,{files:sources,sourcePath:entry.headerPath}));delete bp.native.header;delete bp.native.source;content.set(bpName,Buffer.from(JSON.stringify(bp)));
 const record=await readProjectManifest(path.join(game,'YumenoKuni.hbproject'));assert.equal(record.manifest.id,manifest.id);
 const provenance=base.approvedPanicRuntime||await read(path.join(game,'Saved/nonstop-all-20261106/runtime-selection.json'));
 const player=provenance.player;assert.equal(sha(await fs.readFile(player)),provenance.playerSHA256||provenance.sha256);
 const adapter=await approvedPanicBuilder({root:game,engineRoot:engine,player,compileMs:300000});
 const report={...base,files:content.size,verifiedNativeSnapshot:{base:base.id,sourceSHA256:module.sourceSHA256,dialogueVoiceOnly:true},warnings:base.warnings||[]};delete report.id;delete report.output;delete report.executable;
 const natives=new Map([[nativeSignature(header,source,entry),{header,source,...entry,files:sources}]]);
 const result=await adapter.build(record,base.profile,{content,natives,report},{onProgress:p=>console.log(p)});result.approvedPanicRuntime=adapter.provenance;result.engineSDKRoot=engine;
 const m=await read(path.join(result.output,'game.hbpack.json')),packed=await openGameResources(path.join(result.output,m.contentArchive.path));
 try{assert.equal(packed.entries.size,archive.entries.size);for(const [name,row]of archive.entries){const expected=changed.has(name)||name===bpName?sha(content.get(name)):row.sha256;assert.equal(packed.entries.get(name)?.sha256,expected,name);}}finally{await packed.close();}
 await fs.writeFile(path.join(result.output,'build-report.json'),JSON.stringify(result,null,2));
 await fs.writeFile(path.join(work,'build-result.json'),JSON.stringify(result,null,2));
 await fs.writeFile(path.join(work,'package-parity.json'),JSON.stringify({ok:true,base:base.id,build:result.id,sources:sources.length,changedDataFiles:[...changed],allCodeUIArtworkAudioAndNonTextLogicPreserved:true,engineEdits:false,retainedFiles,archiveBuffers},null,2));
 console.log(JSON.stringify({id:result.id,output:result.output}));
}finally{await archive.close();}
