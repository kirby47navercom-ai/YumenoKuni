import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import {pathToFileURL} from 'node:url';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/park-levels-20261104'),base=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const flat=path.join(root,'Saved/game-trial-work-20261102/flat-current-2026-11-03T12-13-56-429Z-3ea6518d'),manifest=JSON.parse(await fs.readFile(path.join(base.output,'game.hbpack.json'),'utf8')),prior=JSON.parse(await fs.readFile(path.join(flat,'game.hbpack.json'),'utf8'));
const previous=new Map(prior.files.map(r=>[r.path,r]));
for(const row of manifest.files)if(row.path!=='game.hbdata'&&!manifest.nativeModules.some(n=>n.binary===row.path))assert.equal(row.sha256,previous.get(row.path)?.sha256,'Changed engine/runtime file: '+row.path);
const {openGameResources}=await import(pathToFileURL(path.join(base.output,'tools/game-resource-archive.mjs'))),archive=await openGameResources(path.join(base.output,manifest.contentArchive.path)),overrides={};
try{for(const [name,row] of archive.entries){
 if(name.startsWith('Source/')){const dest=path.join(work,'baseline',name);await fs.mkdir(path.dirname(dest),{recursive:true});await fs.writeFile(dest,await archive.read(name));}
 if(previous.get('Content/'+name)?.sha256===row.sha256)continue;
 const dest=path.join(work,'baseline-content',name);await fs.mkdir(path.dirname(dest),{recursive:true});await fs.writeFile(dest,await archive.read(name));overrides['Content/'+name]=dest;
}}finally{await archive.close();}
await fs.writeFile(path.join(work,'baseline-overrides.json'),JSON.stringify(overrides,null,2));await fs.writeFile(path.join(work,'baseline-build.json'),JSON.stringify({base,flat,engineUnchanged:true,changedContent:Object.keys(overrides).length},null,2));console.log(JSON.stringify({baseline:base.id,changedContent:Object.keys(overrides).length}));
