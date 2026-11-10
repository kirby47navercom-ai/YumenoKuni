// Compile only the declared level-ownership changes over the shipped game source.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';import {pathToFileURL} from 'node:url';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/park-levels-20261104');
const flat=path.join(root,'Saved/game-trial-work-20261102/flat-current-2026-11-03T12-13-56-429Z-3ea6518d'),base=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const sdk='C:/Users/kirby/HBEngine/Versions/efed7aac955ad918',manifest=JSON.parse(await fs.readFile(path.join(base.output,'game.hbpack.json'),'utf8'));
const changed=new Set(['ExploreWorld.hpp','RuntimeScenesV4.hpp','V4Explore.hpp','PadMapV4.hpp','V4Story.hpp','GameInputV4.hpp','DisplayV4.hpp']),files=[];
const scopedCodeBaseline=path.join(work,'theme-v2-code-baseline.json'),codeBase=JSON.parse(await fs.readFile(scopedCodeBaseline,'utf8'));
if(process.argv.includes('--reuse-verified')){
 const binary=path.join(base.output,manifest.nativeModules[0].binary),sha=b=>createHash('sha256').update(b).digest('hex');assert.equal(sha(await fs.readFile(binary)),codeBase.binarySHA256);
 for(const [name,file]of Object.entries(codeBase.sourceFiles))assert.equal(sha(await fs.readFile(file)),codeBase.sourceSHA256[name]);
 const receipt={...codeBase,binary,scopedCodeBaseline,scopedCodeBaselineSHA256:sha(await fs.readFile(scopedCodeBaseline)),frozenNativeReuse:true,headerOverlay:'Exact verified native code; this revision changes assets/scenes/world data and removes the hint widget definition.'};
 await fs.writeFile(path.join(work,'game-module.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify({reusedVerifiedCode:true,binarySHA256:receipt.binarySHA256,sourceFiles:Object.keys(receipt.sourceFiles).length}));process.exit(0);
}
for(const entry of await fs.readdir(path.join(work,'baseline/Source'),{withFileTypes:true})){
 assert(entry.isFile());files.push({path:'Source/'+entry.name,content:await fs.readFile(path.join(changed.has(entry.name)?root:path.join(work,'baseline'),'Source',entry.name),'utf8')});
}
for(const name of changed)if(!files.some(f=>f.path==='Source/'+name))files.push({path:'Source/'+name,content:await fs.readFile(path.join(root,'Source',name),'utf8')});
const headerFile=files.find(f=>f.path==='Source/Yumeno.h'),alias=' using UI=widgetownersv4::UI;';assert(headerFile.content.includes(alias));headerFile.content=headerFile.content.replace(alias,alias+'\n using Input=gameinputv4::Input;');
const {nativeModuleKey}=await import(pathToFileURL(path.join(sdk,'prototype/native-entry.js'))),{canonicalNativeText}=await import(pathToFileURL(path.join(sdk,'prototype/native-model.js')));
const {NativeHost}=await import(pathToFileURL(path.join(sdk,'tools/native-host.mjs')));const host=new NativeHost();
const sha=b=>createHash('sha256').update(b).digest('hex');
try{
 const result=await host.build(files.find(f=>f.path==='Source/Yumeno.h').content,files.find(f=>f.path==='Source/Yumeno.cpp').content,{configuration:'development',files,headerPath:'Source/Yumeno.h',sourcePath:'Source/Yumeno.cpp'});
 assert.deepEqual(result.metadata,manifest.nativeModules[0].metadata);
 const binary=path.join(work,'game-park-levels.exe');await fs.copyFile(host.sessions.get(result.token).binary,binary);
 const sourceFiles={};for(const file of files){const dest=path.join(work,'module-source',file.path);await fs.mkdir(path.dirname(dest),{recursive:true});await fs.writeFile(dest,file.content);sourceFiles[file.path]=dest;}
 const signature=sha(nativeModuleKey(canonicalNativeText(files.find(f=>f.path==='Source/Yumeno.h').content),canonicalNativeText(files.find(f=>f.path==='Source/Yumeno.cpp').content),{headerPath:'Source/Yumeno.h',sourcePath:'Source/Yumeno.cpp'}));
 const receipt={signature,sourceFiles,binary,baseBuild:base.id,baseOutput:base.output,flat,engineSDKRoot:sdk,engineModified:false,gameSourceOnly:true,binarySHA256:sha(await fs.readFile(binary)),sourceSHA256:Object.fromEntries(files.map(f=>[f.path,sha(f.content)])),changedSource:[...changed,'Yumeno.h'],headerOverlay:'Only Input alias over frozen baseline; other current authoring header changes remain unshipped',sdk:result.sdk,sdkUsed:result.sdkUsed,cacheKey:result.cacheKey};
 await fs.writeFile(path.join(work,'game-module.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify({...receipt,sourceSHA256:undefined,sourceFiles:undefined}));
}finally{await host.close();}
