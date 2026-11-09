import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const inside=(root,file)=>{const relative=path.relative(root,file);return relative&&!relative.startsWith('..'+path.sep)&&!path.isAbsolute(relative);};

// Inspect the content that will actually ship. Live editable Assets can belong
// to another unfinished task, and must not become a snapshot build dependency.
export async function snapshotInspectionRecord(record,{root,engineRoot,file}){
 const saved=await fs.realpath(path.join(root,'Saved'));
 file=await fs.realpath(path.resolve(root,file));assert(inside(saved,file),'Snapshot receipt outside Saved');
 const snapshot=JSON.parse(await fs.readFile(file,'utf8'));
 assert(snapshot.contentPackage,'Snapshot inspection requires pinned content');
 const contentRoot=await fs.realpath(path.join(snapshot.contentPackage,'Content'));
 assert(inside(saved,contentRoot),'Snapshot content outside Saved');
 const {ProjectService}=await import(pathToFileURL(path.join(engineRoot,'tools/project-service.mjs')));
 return {...record,root:contentRoot,project:new ProjectService(contentRoot)};
}

// Pin a tested C++ snapshot without replacing another chat's editable source.
// The engine's normal inspector, cooker, compiler and packager still run.
export async function applyVerifiedNativeSnapshot(payload,{root,engineRoot,file}){
 const saved=await fs.realpath(path.join(root,'Saved'));
 file=await fs.realpath(path.resolve(root,file));assert(inside(saved,file),'Snapshot receipt must belong to Saved');
 const snapshot=JSON.parse(await fs.readFile(file,'utf8'));
 const sourceRoot=await fs.realpath(snapshot.sourceRoot),receiptFile=await fs.realpath(snapshot.moduleReceipt);
 assert(inside(saved,sourceRoot)&&inside(saved,receiptFile),'Snapshot source/receipt outside Saved');
 const receipt=JSON.parse(await fs.readFile(receiptFile,'utf8'));
 assert.equal(hash(await fs.readFile(receipt.binary)),receipt.binarySHA256,'Tested binary changed');
 assert.equal(payload.natives.size,1,'Review multiple native modules before snapshot build');
 const files=[];
 for(const [name,sha256] of Object.entries(receipt.sourceSHA256)){
  assert(/^Source\/[A-Za-z0-9_.-]+$/.test(name),'Invalid frozen source name');
  const resolved=await fs.realpath(path.join(sourceRoot,name));assert(inside(sourceRoot,resolved));
  const bytes=await fs.readFile(resolved);assert.equal(hash(bytes),sha256,'Frozen source changed: '+name);
  files.push({path:name,content:bytes.toString('utf8')});
 }
 let contentSnapshot;
 if(snapshot.contentPackage){
  const packageRoot=await fs.realpath(snapshot.contentPackage);assert(inside(saved,packageRoot),'Content snapshot outside Saved');
  const manifestBytes=await fs.readFile(path.join(packageRoot,'game.hbpack.json')),manifest=JSON.parse(manifestBytes);
  const project=JSON.parse(await fs.readFile(path.join(root,'YumenoKuni.hbproject'),'utf8'));assert.equal(manifest.id,project.id);
  const {fileContent}=await import(pathToFileURL(path.join(engineRoot,'tools/build-content.mjs')));
  const indexed=new Map(manifest.files.map(row=>[row.path,row]));payload.content.clear();
  for(const row of manifest.entries){
   assert(/^(Assets|Source)\//.test(row.path)&&!row.path.split('/').includes('..'),'Invalid content snapshot entry');
   assert(indexed.has('Content/'+row.path),'Unindexed snapshot content');
   const resolved=await fs.realpath(path.join(packageRoot,'Content',row.path));assert(inside(packageRoot,resolved));
   const value=/\.(json|gltf|h|hpp|hh|inl|cpp|cc|cxx|c)$/i.test(row.path)?await fs.readFile(resolved):await fileContent(resolved,{root:packageRoot});payload.content.set(row.path,value);
  }
  const manifestFile=path.join(path.dirname(file),'publish-content-manifest-'+hash(manifestBytes).slice(0,12)+'.json');await fs.writeFile(manifestFile,manifestBytes);
  contentSnapshot={packageRoot,manifestFile,manifestSHA256:hash(manifestBytes),entries:manifest.entries.length,kind:'Already cooked base plus the exact loose content exercised by actual input tests; State and QA runtime excluded'};
 }
 const {canonicalNativeText,parseNativeHeader}=await import(pathToFileURL(path.join(engineRoot,'prototype/native-model.js')));
 const {nativeModuleKey}=await import(pathToFileURL(path.join(engineRoot,'prototype/native-entry.js')));
 const {isFileContent}=await import(pathToFileURL(path.join(engineRoot,'tools/build-content.mjs')));
 const headerPath='Source/Yumeno.h',sourcePath='Source/Yumeno.cpp';
 const header=canonicalNativeText(files.find(f=>f.path===headerPath).content),source=canonicalNativeText(files.find(f=>f.path===sourcePath).content);
 const owned=new Set(files.map(f=>f.path));
 for(const name of payload.content.keys())if(name.startsWith('Source/')&&!owned.has(name))payload.content.delete(name);
 for(const item of files)payload.content.set(item.path,Buffer.from(item.content));
 const blueprint='Assets/Blueprints/BP_Yumeno.hbblueprint.json';
 // The loose QA copy has Stats/AimStats log nodes. Ship the original graph,
 // never those per-frame diagnostic calls.
 assert(snapshot.shippingBlueprintPackage,'A tested source snapshot needs a clean shipping Blueprint');
 const baseline=await fs.realpath(snapshot.shippingBlueprintPackage);assert(inside(path.join(root,'Builds'),baseline),'Blueprint baseline outside Builds');
 const baselineManifest=JSON.parse(await fs.readFile(path.join(baseline,'game.hbpack.json'),'utf8'));
 const {openGameResources}=await import(pathToFileURL(path.join(engineRoot,'tools/game-resource-archive.mjs')));
 const baselineArchive=await openGameResources(path.join(baseline,baselineManifest.contentArchive.path));let asset;
 try{asset=JSON.parse(await baselineArchive.read(blueprint));}finally{await baselineArchive.close();}
 assert(!asset.nodes.some(n=>['Yumeno.Stats','Yumeno.AimStats'].includes(n.nativeId)),'Diagnostic calls in shipping baseline');
 const graph={...asset};delete graph.native;const graphBytes=Buffer.from(JSON.stringify(graph));
 const graphFile=path.join(path.dirname(file),'shipping-blueprint-graph-'+hash(graphBytes).slice(0,12)+'.json');await fs.writeFile(graphFile,graphBytes);
 asset.native={...parseNativeHeader(header,{files,sourcePath:headerPath}),headerPath,sourcePath};
 payload.content.set(blueprint,Buffer.from(JSON.stringify(asset,null,2)+'\n'));
 payload.natives.clear();payload.natives.set(hash(nativeModuleKey(header,source,{headerPath,sourcePath})),{header,source,headerPath,sourcePath,files});
 const values=[...payload.content.values()];
 Object.assign(payload.report,{files:payload.content.size,bytes:values.reduce((n,b)=>n+b.length,0),nativeModules:1,
  streaming:{...payload.report.streaming,fileBackedFiles:values.filter(isFileContent).length,fileBackedBytes:values.filter(isFileContent).reduce((n,b)=>n+b.length,0),bufferedBytes:values.filter(b=>!isFileContent(b)).reduce((n,b)=>n+b.length,0)},
  verifiedNativeSnapshot:{contentSnapshot,shippingBlueprint:{baseline,graphFile,sha256:hash(graphBytes),diagnosticNodes:0},receipt:file,moduleReceipt:receiptFile,sourceRoot,sourceFiles:files.length,testedModuleSHA256:receipt.binarySHA256,sourceSHA256:receipt.sourceSHA256,liveSourceModified:false}});
 const {validateNativeContent}=await import(pathToFileURL(path.join(engineRoot,'tools/build-native-game.mjs')));validateNativeContent(payload.content,payload.report.profile);
 return payload;
}
