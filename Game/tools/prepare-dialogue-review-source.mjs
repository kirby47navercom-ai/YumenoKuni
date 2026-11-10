import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const game=path.resolve(import.meta.dirname,'..'),work=path.join(game,'Saved/dialogue-audit-20261107');
const build=JSON.parse(await fs.readFile(path.join(game,'build-result.json'),'utf8'));
const inventory=JSON.parse(await fs.readFile(path.join(work,'shipping-inventory.json'),'utf8'));
assert.equal(build.id,inventory.build,'Audit the current published build before freezing');
const manifest=JSON.parse(await fs.readFile(path.join(build.output,'game.hbpack.json'),'utf8'));
const {openGameResources}=await import(pathToFileURL(path.join(build.output,'tools/game-resource-archive.mjs')));
const archive=await openGameResources(path.join(build.output,manifest.contentArchive.path)),sources={};
const changed=new Set(['Source/DialogueTextV4.hpp','Source/DialogueWindowV4.hpp']);
try{
 for(const [name,entry]of archive.entries)if(name.startsWith('Source/')){
  const original=await archive.read(name),bytes=changed.has(name)?await fs.readFile(path.join(game,name)):original;
  const file=path.join(work,'snapshot',name);await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file,bytes);
  sources[name]={before:entry.sha256,after:createHash('sha256').update(bytes).digest('hex')};
 }
}finally{await archive.close();}
assert.equal(Object.values(sources).filter(r=>r.before!==r.after).length,2,'Only pagination implementation and dialogue call site');
await fs.writeFile(path.join(work,'base-build.json'),JSON.stringify(build,null,2));
await fs.writeFile(path.join(work,'source-boundary.json'),JSON.stringify({base:build.id,sources,engineEdits:false,scriptWordsChanged:false,scope:'Only sentence-aware dialogue page boundaries; document pagination, utterance text, plot, graph IDs and routes preserved. Other current-source changes not imported.'},null,2));
console.log(JSON.stringify({base:build.id,sources:Object.keys(sources).length,changed:2}));
