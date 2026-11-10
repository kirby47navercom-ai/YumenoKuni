// Package the reviewed Nonstop fixes without collecting another chat's unfinished source.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {installBuildSharing} from './build-share.mjs';
import {approvedPanicBuilder} from './approved-panic-build.mjs';
const game=path.resolve(import.meta.dirname,'..'),work=path.join(game,'Saved/nonstop-all-20261106');
const baseline=JSON.parse(await fs.readFile(path.join(work,'build.json'),'utf8'));
const module=JSON.parse(await fs.readFile(path.join(game,'Saved/game-trial-work-20261102/game-module-nonstop-word-compact-20261106.json'),'utf8'));
const manifest=JSON.parse(await fs.readFile(path.join(baseline.output,'game.hbpack.json'),'utf8'));
const engine=baseline.engineSDKRoot;
const {readProjectManifest}=await import(pathToFileURL(path.join(engine,'tools/project-manifest.mjs')));
const {inspectBuild}=await import(pathToFileURL(path.join(engine,'tools/build-game.mjs')));
const {parseNativeHeader}=await import(pathToFileURL(path.join(engine,'prototype/native-model.js')));
const flightAssets=JSON.parse(await fs.readFile(path.join(work,'flight-assets.json'),'utf8')),overlays=new Map(flightAssets.changes.map(r=>[r.path.slice(8),r]));
const project=path.join(work,'full-project');await fs.mkdir(project,{recursive:true});
const hash=b=>createHash('sha256').update(b).digest('hex');
const copy=async(from,to)=>{await fs.mkdir(path.dirname(to),{recursive:true});await fs.copyFile(from,to);};
const link=async(from,to)=>{await fs.mkdir(path.dirname(to),{recursive:true});await fs.link(from,to).catch(e=>{if(e.code!=='EEXIST')throw e;});};
const qa=path.join(game,'Saved/native-panic-views-1793690486425/package');
const flat=JSON.parse(await fs.readFile(path.join(qa,'game.hbpack.json'),'utf8')),flatRows=new Map(flat.files.map(r=>[r.path,r]));
const {openGameResources}=await import(pathToFileURL(path.join(baseline.output,'tools/game-resource-archive.mjs')));
const archive=await openGameResources(path.join(baseline.output,manifest.contentArchive.path));
try{for(const [relative,row]of archive.entries){
 const target=path.join(project,relative);assert(!relative.split('/').includes('..'));await fs.mkdir(path.dirname(target),{recursive:true});
 if(relative.startsWith('Source/')){
  const bytes=await fs.readFile(path.join(work,'frozen',relative));assert.equal(hash(bytes),module.sourceSHA256[relative]);await fs.writeFile(target,bytes);
 }else if(relative==='Assets/Blueprints/BP_Yumeno.hbblueprint.json')await fs.writeFile(target,await archive.read(relative));
 else if(overlays.has(relative)){const bytes=await fs.readFile(path.join(work,'candidate-assets',relative));assert.equal(hash(bytes),overlays.get(relative).sha256);await fs.writeFile(target+'.flight.tmp',bytes);await fs.rename(target+'.flight.tmp',target);}
 else {assert.equal(flatRows.get('Content/'+relative)?.sha256,row.sha256,'Retained QA resource changed: '+relative);await link(path.join(qa,'Content',relative),target);}
}}finally{await archive.close();}
for(const [relative,digest]of Object.entries(module.sourceSHA256)){const bytes=await fs.readFile(path.join(work,'frozen',relative));assert.equal(hash(bytes),digest);await fs.writeFile(path.join(project,relative),bytes);}
for(const [relative,row]of overlays){const target=path.join(project,relative);const bytes=await fs.readFile(path.join(work,'candidate-assets',relative));assert.equal(hash(bytes),row.sha256);await fs.mkdir(path.dirname(target),{recursive:true});await fs.writeFile(target+'.flight.tmp',bytes);await fs.rename(target+'.flight.tmp',target);}
await copy(path.join(game,'YumenoKuni.hbproject'),path.join(project,'YumenoKuni.hbproject'));
const bpFile=path.join(project,'Assets/Blueprints/BP_Yumeno.hbblueprint.json'),bp=JSON.parse(await fs.readFile(bpFile,'utf8'));
const header=await fs.readFile(path.join(project,'Source/Yumeno.h'),'utf8'),source=await fs.readFile(path.join(project,'Source/Yumeno.cpp'),'utf8');
Object.assign(bp.native,parseNativeHeader(header),{header,source});await fs.writeFile(bpFile,JSON.stringify(bp));
// An immutable hardlinked baseline lets the existing byte-checked sharing helper work.
const previous=path.join(project,'Builds',baseline.profile.id,baseline.id);await fs.mkdir(previous,{recursive:true});
for(const row of manifest.files)await link(path.join(baseline.output,row.path),path.join(previous,row.path));
await copy(path.join(baseline.output,'game.hbpack.json'),path.join(previous,'game.hbpack.json'));
const record=await readProjectManifest(path.join(project,'YumenoKuni.hbproject'));
const runtime=JSON.parse(await fs.readFile(path.join(work,'runtime-selection.json'),'utf8'));assert.equal(hash(await fs.readFile(runtime.player)),runtime.sha256,'Pinned approved player changed');
const adapter=await approvedPanicBuilder({root:game,engineRoot:engine,player:runtime.player,compileMs:300000});
const sharing=await installBuildSharing({root:project,profile:baseline.profile.id,previous,projectId:manifest.id});let result;
try{
 const inspected=await inspectBuild(record,baseline.profile);
 // Other QA checkouts add hardlinks to these same immutable bytes. That changes
 // inode ctime and invalidates file descriptors during packaging. Feed official
 // archive-verified byte buffers instead; keep the SDK's checks enabled.
 const {isFileContent}=await import(pathToFileURL(path.join(engine,'tools/build-content.mjs')));
 const pinned=await openGameResources(path.join(baseline.output,manifest.contentArchive.path));let buffered=0;
 try{for(const [name,value]of inspected.content)if(isFileContent(value)){
  const overlay=overlays.get(name);assert(overlay||pinned.entries.has(name),'Opaque resource outside pinned inputs: '+name);
  const bytes=overlay?await fs.readFile(path.join(work,'candidate-assets',name)):await pinned.read(name);assert.equal(bytes.length,value.length);assert.equal(hash(bytes),overlay?.sha256||pinned.entries.get(name).sha256);inspected.content.set(name,bytes);buffered+=bytes.length;
 }}finally{await pinned.close();}
 console.log(JSON.stringify({immutableOpaqueBytes:buffered,privateDiskCopy:false}));
 result=await adapter.build(record,baseline.profile,inspected,{onProgress:p=>console.log(p)});
}finally{sharing.restore();}
result.approvedPanicRuntime=adapter.provenance;result.engineSDKRoot=engine;result.contentSharing=sharing.stats;
await fs.writeFile(path.join(work,'full-build-result.json'),JSON.stringify(result,null,2));
await fs.writeFile(path.join(work,'full-build-provenance.json'),JSON.stringify({base:baseline.id,sourceSHA256:module.sourceSHA256,changedAssets:flightAssets.changes,engineModified:false,otherChatSourceIncluded:false,contentSharing:sharing.stats},null,2));
console.log(JSON.stringify({id:result.id,output:result.output}));
