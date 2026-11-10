import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {voiceReviser} from './v4-voice-revisions.mjs';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game),work=path.join(game,'Saved/voice-rewrite-20261107');
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const base=await read(path.join(game,'build-result.json'));
assert.equal(base.id,'2026-11-07T03-31-02-451Z-c447b98d','Review a changed publication before grafting text');
const manifest=await read(path.join(base.output,'game.hbpack.json'));
const {openGameResources}=await import(pathToFileURL(path.join(base.output,'tools/game-resource-archive.mjs')));
const {validGameJson}=await import(pathToFileURL(path.resolve(repo,'../engineCreate/prototype/game-json.js')));
const archive=await openGameResources(path.join(base.output,manifest.contentArchive.path));
const voice=await voiceReviser(repo),changed=[];
const sha=b=>createHash('sha256').update(b).digest('hex');
try{
 for(const[name,row]of archive.entries){
  if(!/^Assets\/Data\/v4_story\/.*\.json$/.test(name))continue;
  const bytes=await archive.read(name),before=JSON.parse(bytes),after=voice.revise(structuredClone(before));
  if(JSON.stringify(before)===JSON.stringify(after))continue;
  assert(validGameJson(after),'Native JSON bounds: '+name);
  // A source rewrite may affect text and exact weak offsets only.
  let edits=0;
  function compare(a,b,where='$'){
   if(JSON.stringify(a)===JSON.stringify(b))return;
   if(Array.isArray(a)){assert(Array.isArray(b)&&a.length===b.length,where);a.forEach((v,i)=>compare(v,b[i],where+'['+i+']'));return;}
   assert(a&&b&&typeof a==='object'&&typeof b==='object','Unreviewed change '+where);assert.deepEqual(Object.keys(a),Object.keys(b));
   for(const k of Object.keys(a)){
    if(k==='text'&&a[k]!==b[k]){assert(typeof b[k]==='string');++edits;continue;}
    if(k==='start'&&a[k]!==b[k]){assert(typeof a.word==='string'&&a.word===b.word,'Only word offsets may move');continue;}
    compare(a[k],b[k],where+'.'+k);
   }
  }
  compare(before,after);const out=Buffer.from(JSON.stringify(after));
  const target=path.join(work,'runtime',name);await fs.mkdir(path.dirname(target),{recursive:true});await fs.writeFile(target,out);
  changed.push({path:name,before:row.sha256,after:sha(out),edits});
 }
}finally{await archive.close();}
const report={base:base.id,...voice.report(),files:changed,onlyReviewedTextAndTargetOffsets:true,otherArchiveContentPreserved:true};
assert.equal(report.manualSources.length,738,'Every manually rewritten source must reach published runtime data');
await fs.writeFile(path.join(work,'runtime-patch.json'),JSON.stringify(report,null,1));
await fs.writeFile(path.join(work,'base-build.json'),JSON.stringify(base,null,2));
console.log(JSON.stringify({base:base.id,changed:report.changed,manualSources:report.manualSources.length,files:changed.length,boundedStageChanges:report.boundedStageChanges,skippedAdaptations:report.skippedAdaptations}));
