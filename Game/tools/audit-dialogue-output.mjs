// Read the published archive; do not confuse concurrently edited source with shipping text.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game);
const work=path.join(game,'Saved/dialogue-audit-20261107');
await fs.mkdir(work,{recursive:true});
const build=JSON.parse(await fs.readFile(path.join(game,'build-result.json'),'utf8'));
const manifest=JSON.parse(await fs.readFile(path.join(build.output,'game.hbpack.json'),'utf8'));
const {openGameResources}=await import(pathToFileURL(path.join(build.output,'tools/game-resource-archive.mjs')));
const archive=await openGameResources(path.join(build.output,manifest.contentArchive.path));
const rows=[],unique=new Map(),files=[],compiledKorean=[];
const actorNames={mio:'미오',rei:'레이',sora:'소라',ken:'켄',nana:'나나',riku:'리쿠',akari:'아카리',yuu:'유우',koto:'코토',satsuki:'사츠키',taiga:'타이가',rin:'린',sho:'쇼',ai:'아이',haruka:'하루카',kaede:'카에데',lappy:'래피'};
function visit(value,file,where='$'){
 if(Array.isArray(value)){value.forEach((v,i)=>visit(v,file,where+'['+i+']'));return;}
 if(!value||typeof value!=='object')return;
 if(value.themText&&value.usText){for(const role of ['them','us'])visit({id:(value.id||where)+':'+role,speaker:value[role],text:value[role+'Text'],source:value.source},file,where+'.'+role+'Text');}
 if(typeof value.text==='string'&&(typeof value.speaker==='string'||actorNames[value.actor])&&value.text){
  const source=typeof value.source==='object'?value.source:value.provenance;
  const row={file,where,id:value.id||'',speaker:value.speaker||actorNames[value.actor],actor:value.actor||'',mono:!!value.mono,text:value.text,source:source||null};
  rows.push(row);
  const key=JSON.stringify([source?.file||file,source?.line||row.id||where,row.speaker,row.mono,row.text]);
  if(!unique.has(key))unique.set(key,{...row,copies:0});unique.get(key).copies++;
 }
 for(const [key,v] of Object.entries(value))if(key!=='source'&&key!=='provenance')visit(v,file,where+'.'+key);
}
try{
 for(const [name,entry] of archive.entries){
  if(name.startsWith('Source/')){
   const raw=(await archive.read(name)).toString('utf8');
   for(const m of raw.matchAll(/"((?:\\.|[^"\\])*)"/g))if(/[가-힣]/.test(m[1]))compiledKorean.push({file:name,line:raw.slice(0,m.index).split('\n').length,literal:m[1],context:raw.slice(Math.max(0,m.index-100),m.index+m[0].length+100),scope:'Compiled Korean string literal; may be a label, rule, lookup, or fallback dialogue. Not automatically a spoken line.'});
  }
  if(!/^Assets\/Data\/v4_story\/.*\.json$/.test(name))continue;
  const bytes=await archive.read(name);files.push({path:name,sha256:entry.sha256});visit(JSON.parse(bytes),name);
 }
 for(const name of ['Assets/Data/v4_story/dialogue_layout.json','Assets/Data/v4_story/choice_layout.json','Source/DialogueTextV4.hpp','Source/DialogueWindowV4.hpp']){
  const bytes=await archive.read(name);await fs.writeFile(path.join(work,path.basename(name)),bytes);
 }
}finally{await archive.close();}
assert(rows.length>10000);
await fs.writeFile(path.join(work,'shipping-dialogue.json'),JSON.stringify([...unique.values()],null,1));
await fs.writeFile(path.join(work,'compiled-korean-literals.json'),JSON.stringify(compiledKorean,null,1));
await fs.writeFile(path.join(work,'shipping-inventory.json'),JSON.stringify({build:build.id,files,occurrences:rows.length,uniqueSourceUtterances:unique.size,sourceArchive:manifest.contentArchive.path,sha256:createHash('sha256').update(JSON.stringify([...unique.values()])).digest('hex'),sourceManuscripts:path.join(repo,'docs/design/rewrite_v4'),scope:'All speaker/text records in the published V4 data archive, including nested queues and debate records. Copies deduplicated by source/text identity; traversal is not all-branch gameplay or human prose approval.'},null,2));
console.log(JSON.stringify({build:build.id,files:files.length,occurrences:rows.length,unique:unique.size,work}));
