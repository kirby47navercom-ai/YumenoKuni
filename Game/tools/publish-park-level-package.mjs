// Publish only if the previously frozen current build is still current.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/park-levels-20261104'),currentFile=path.join(root,'build-result.json');
const before=await fs.readFile(currentFile),current=JSON.parse(before),baseline=JSON.parse(await fs.readFile(path.join(work,'baseline-build.json'),'utf8')),build=JSON.parse(await fs.readFile(path.join(work,'build-result.json'),'utf8'));
const expected=process.argv.find(a=>a.startsWith('--expected-current='))?.slice(19)||baseline.base.id;
assert.equal(current.id,expected,'A newer independent full build exists: preserve it; do not overwrite it.');
if(current.id!==baseline.base.id){assert(current.parkLevels&&current.baseline===baseline.base.output);const predecessor=JSON.parse(await fs.readFile(path.join(current.output,'park-level-build-receipt.json'),'utf8'));assert(predecessor.ok&&predecessor.base===baseline.base.id&&predecessor.engineFilesChanged===0);}
const smoke=JSON.parse(await fs.readFile(path.join(work,'final-packed-smoke.json'),'utf8'));assert(smoke.ok&&smoke.build===build.id&&smoke.compressedPackage&&smoke.noContentOrModuleOverrides&&smoke.sourceSavesUnchanged);
for(const r of smoke.rows){const open=JSON.parse(await fs.readFile(path.join(r.run,'pad.ui.json'),'utf8')),closed=JSON.parse(await fs.readFile(path.join(r.run,'pad-closed.ui.json'),'utf8'));assert(open.rects.some(n=>n.id==='PdFloor'));assert(!closed.rects.some(n=>n.id==='PdFloor'));}
const manifest=JSON.parse(await fs.readFile(path.join(build.output,'game.hbpack.json'),'utf8')),receipt=JSON.parse(await fs.readFile(path.join(build.output,'park-level-build-receipt.json'),'utf8'));
assert(receipt.ok&&receipt.base===baseline.base.id&&receipt.engineFilesChanged===0);
const hash=b=>createHash('sha256').update(b).digest('hex'),module=await fs.readFile(path.join(build.output,manifest.nativeModules[0].binary));assert.equal(hash(module),receipt.gameModuleSHA256);
const result={...build,target:'windows-x64',windowsRuntime:manifest.windowsRuntime,startupScene:manifest.startupScene,gameInstance:manifest.gameInstance,nativeModules:manifest.nativeModules,windowsApplication:manifest.windowsApplication,signing:manifest.windowsApplication?.signing||current.signing,totalFiles:manifest.files.length,totalBytes:manifest.files.reduce((n,r)=>n+r.bytes,0),scopedReceipt:path.join(build.output,'park-level-build-receipt.json')};
const backup=path.join(work,'pre-publish-build-result-'+current.id+'.json');await fs.copyFile(currentFile,backup,fs.constants.COPYFILE_EXCL);
assert((await fs.readFile(currentFile)).equals(before),'Current changed during publication');
await fs.writeFile(currentFile+'.park.tmp',JSON.stringify(result,null,2));await fs.rename(currentFile+'.park.tmp',currentFile);
await fs.writeFile(path.join(work,'publish-receipt.json'),JSON.stringify({ok:true,before:current.id,after:result.id,output:result.output,sourceSHA256:hash(before),publishedSHA256:hash(await fs.readFile(currentFile)),engineFilesChanged:0,scope:'One scoped full build over the unchanged frozen baseline; independent unshipped UI source changes are preserved but not included.'},null,2));console.log(JSON.stringify({ok:true,before:current.id,after:result.id}));
