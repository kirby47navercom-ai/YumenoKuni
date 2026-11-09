import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {emitPresentationV4} from '../../tools/v4_presentation_widget.mjs';
import {mineHintSvg} from './v4-mine-ui.mjs';
import {emitMineObjects,bindMineObjects} from './v4-mine-objects.mjs';
import {assetReferences} from '../../../engineCreate/tools/project-service.mjs';
import {validGameJson} from '../../../engineCreate/prototype/game-json.js';
import {emitV4DataPacks} from './v4-data-pack.mjs';
import {incidentShots} from './v4-incident-shots.mjs';
import {nativeWidgetPng} from './native-png-runtime.mjs';
import {voiceReviser} from './v4-voice-revisions.mjs';

export function v4Bucket(id,count){let hash=2166136261;for(const byte of Buffer.from(id,'utf8'))hash=Math.imul(hash^byte,16777619)>>>0;return hash%count;}

// HBEngine treats a string named `source` as a packaged asset reference.
// Manuscript provenance stays available without becoming a missing runtime file.
export function runtimeV4Data(value){
 if(Array.isArray(value))return value.map(runtimeV4Data);
 if(!value||typeof value!=='object')return value;
 const out={};
 for(const [key,item] of Object.entries(value)){
  if(key==='source'&&typeof item==='string'&&!item.startsWith('Assets/')&&!item.startsWith('Source/'))out.provenance=item;
  else if(key==='parent'&&typeof item==='string'&&item.endsWith('.md'))out.manuscriptParent=item;
  else out[key]=runtimeV4Data(item);
 }
 return out;
}
export async function publishEvidenceArtOnly({repo,write}){
 const data=JSON.parse(execFileSync('python',['-X','utf8',path.join(repo,'tools/v4_evidence_art_bindings.py')],{encoding:'utf8',maxBuffer:8*1024*1024})),copied=new Set();
 for(const rows of Object.values(data.items))for(const row of rows){const original=row.image;assertEvidencePath(original);const dest='Assets/Art/v4_story/'+createHash('sha256').update(original).digest('hex').slice(0,16)+path.extname(original);if(!copied.has(dest)){const bytes=await fs.readFile(path.join(repo,original));await write(dest,/\.png$/i.test(original)?nativeWidgetPng(bytes):bytes);copied.add(dest);}row.image=dest;}
 if(!validGameJson(data))throw Error('Evidence art exceeds native bounds');await write('Assets/Data/v4_story/evidence_art.json',data);return {items:Object.keys(data.items).length,assets:[...copied],storyChanged:false};
}
function assertEvidencePath(value){if(!/^(art|ui)\/[^\x00-\x1f]*\.(svg|png|webp)$/i.test(value)||value.includes('..'))throw Error('Unsafe evidence art source');}
export async function publishWorldData(world,write){
 // GLB inventory is retained in the authoring catalogue. Runtime locate() only
 // needs the largest matching node for each of its finite semantic search terms.
 world.instances.story_guest_room={label:'객실',space:'guest_room',storyGeometryOnly:true};
 const terms=[...new Set(world.terms.map(t=>t[1]))],worldBins=Array.from({length:16},()=>({spaces:{}}));
 const worldSpaces=Object.entries(world.spaces).map(([id,s])=>{
  const selected=new Map();for(const term of terms){let best=0,chosen;
   for(const node of s.nodes){if(!node.id.includes(term))continue;const [a,b]=node.box,volume=Math.abs((a[0]-b[0])*(a[1]-b[1])*(a[2]-b[2]));if(volume>best){best=volume;chosen=node;}}
   if(chosen)selected.set(chosen.id,chosen);
  }return [id,{...s,nodes:[...selected.values()]}];
 }).sort((a,b)=>JSON.stringify(b[1]).length-JSON.stringify(a[1]).length);
 const worldIndex={};
 for(const [id,space] of worldSpaces){
  const ranked=worldBins.map((bin,i)=>[i,JSON.stringify(bin).length]).sort((a,b)=>a[1]-b[1]);let assigned=-1;
  for(const [i] of ranked){const proposal={spaces:{...worldBins[i].spaces,[id]:space}};if(validGameJson(proposal)){worldBins[i]=proposal;assigned=i;break;}}
  if(assigned<0)throw new Error('Authored space exceeds native bounded pages: '+id);
  worldIndex[id]={bucket:'Assets/Data/explore3d/'+assigned+'.json'};
 }
 world.spaces=worldIndex;world.storage='bounded-space-pages-v1';
 if(!validGameJson(world))throw new Error('Authored world header exceeds native JSON');
 for(let i=0;i<worldBins.length;i++)await write('Assets/Data/explore3d/'+i+'.json',worldBins[i]);
 await write('Assets/Data/explore_world.json',world);
 return world;
}
export async function publishV4Data({repo,write,copy}){
 const voice=await voiceReviser(repo);
 execFileSync('python',['-X','utf8',path.join(repo,'tools/build_v4_scene_bindings.py')],{stdio:'pipe'});
 const presentationBindings=JSON.parse(await fs.readFile(path.join(repo,'data/presentation/v4_scenes.json'),'utf8')),sceneBindings=presentationBindings.sections;
 execFileSync('python',['-X','utf8',path.join(repo,'tools/v4_growth_bindings.py')],{stdio:'pipe'});
 execFileSync('python',['-X','utf8',path.join(repo,'tools/v4_gift_bindings.py')],{stdio:'pipe'});
 const graphs={};
 for(const dir of ['chapters','freetime'])for(const file of await fs.readdir(path.join(repo,'data/v4_story',dir)))if(file.endsWith('.json')&&!(dir==='freetime'&&file==='index.json'))graphs[dir+'/'+file]=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story',dir,file),'utf8'));
 const prepared=JSON.parse(execFileSync('python',['-X','utf8',path.join(repo,'tools/prepare_v4_runtime.py')],{input:JSON.stringify({graphs,world:JSON.parse(await fs.readFile(path.join(repo,'art/space_v4/runtime_v1/world.json'),'utf8')),native:JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')),gifts:JSON.parse(await fs.readFile(path.join(repo,'tools/v4_gift_contract.json'),'utf8'))}),encoding:'utf8',maxBuffer:128*1024*1024}));
 for(const row of prepared.copies)await copy(row.from,row.to);
 const imageCopies=new Map();
 const mapImages=async value=>{
  if(typeof value==='string'&&/^(art|ui)\/.*\.(svg|png|webp)$/i.test(value)){
   if(!imageCopies.has(value)){
    // Register the in-flight copy before sibling references can start another
    // copy to the same OneDrive-managed destination.
    imageCopies.set(value,(async()=>{const dest='Assets/Art/v4_story/'+createHash('sha256').update(value).digest('hex').slice(0,16)+path.extname(value);
     if(/\.png$/i.test(value))await write(dest,nativeWidgetPng(await fs.readFile(path.join(repo,value))));else await copy(value,dest);return dest;
    })());
   }return imageCopies.get(value);
  }
  if(Array.isArray(value))return Promise.all(value.map(mapImages));
  if(value&&typeof value==='object'){const out={};for(const [key,item] of Object.entries(value))out[key]=await mapImages(item);return out;}
  return value;
 };
 const checkedWrite=async(dest,value)=>{
  const data=dest.startsWith('Assets/Data/')?await mapImages(voice.revise(runtimeV4Data(value))):value;
  for(const reference of assetReferences(data,dest))await fs.access(path.join(repo,'Game',reference)).catch(()=>{throw new Error(dest+': missing runtime reference '+reference);});
  return write(dest,data);
 };
 await emitPresentationV4({repo,copy,write:checkedWrite});
 const evidenceArt=JSON.parse(execFileSync('python',['-X','utf8',path.join(repo,'tools/v4_evidence_art_bindings.py')],{encoding:'utf8',maxBuffer:8*1024*1024}));
 if(!validGameJson(evidenceArt))throw new Error('V4 evidence art exceeds native bounds');await checkedWrite('Assets/Data/v4_story/evidence_art.json',evidenceArt);
 // Keep the source-owned direction table reproducible in a fresh Assets tree.
 // Its font values are relative to Assets/Fonts, as the game reader expects.
 const direction=await fs.readFile(path.join(repo,'data/v4_story/trial_direction.json'),'utf8').then(JSON.parse,e=>{if(e.code==='ENOENT')return null;throw e;});
 if(direction){if(!validGameJson(direction))throw new Error('Trial direction exceeds native bounds');for(const table of ['debate','queue'])for(const row of Object.values(direction[table]||{}))if(row.font){if(typeof row.font!=='string'||row.font.includes('..')||row.font.includes('\\'))throw new Error('Unsafe trial direction font');await fs.access(path.join(repo,'Game/Assets/Fonts',row.font));}await write('Assets/Data/v4_story/trial_direction.json',direction);}
 const armamentLayout=JSON.parse(execFileSync('python',['-X','utf8',path.join(repo,'tools/build_v3_armament_layout.py')],{encoding:'utf8'}));await checkedWrite('Assets/Data/presentation/v3_armament_layout.json',armamentLayout);
 await publishWorldData(prepared.world,checkedWrite);
 const compact=value=>{
  if(Array.isArray(value))return value.map(compact);
  if(!value||typeof value!=='object')return value;
  const out={};for(const [key,item] of Object.entries(value)){
   if(key==='source'&&item&&typeof item==='object')out.source={file:item.file||'',location:item.location||'',line:item.line||0};
   else if(!['fileSha256','provenance','routePolicy','orderPolicy','eligibility','contentScope','acting'].includes(key))out[key]=compact(item);
  }return out;
 };
 const gift=compact(prepared.gifts);
 const growth=compact(JSON.parse(await fs.readFile(path.join(repo,'tools/v4_growth_contract.json'),'utf8')));
 growth.giftOffers=Object.fromEntries(Object.entries(gift.offers).map(([id,row])=>[id,Object.fromEntries(['actor','allowedGifts','acceptedNode','requiresAnyCompletionFlags','bondDelta'].map(key=>[key,row[key]]))]));
 for(const [id,value]of [['growth',growth],['gifts',gift]]){if(!validGameJson(value))throw new Error('V4 '+id+' exceeds native bounds');await checkedWrite('Assets/Data/v4_story/'+id+'.json',value);}
 const nodeCount=128,taskCount=64,nodes=Array.from({length:nodeCount},()=>({nodes:{}})),tasks=Array.from({length:taskCount},()=>({tasks:{}}));
 const seen=new Map();let nodeTotal=0;
 const comicPages=new Map();for(const bundle of Object.values(prepared.native.tasks)){const c=bundle.stage?.comicPresentation;if(c?.completion?.owner==='story-graph')for(const id of c.completion.nodeIds)comicPages.set(id,c.board.image);}
 const discoveries=incidentShots(prepared.graphs,JSON.parse(await fs.readFile(path.join(repo,'art/v4_production/forensic_repair/selected.json'),'utf8')));
 for(const dir of ['chapters','freetime'])for(const file of await fs.readdir(path.join(repo,'data/v4_story',dir)))if(file.endsWith('.json')){
  if(dir==='freetime'&&file==='index.json')continue;
  const graph=prepared.graphs[dir+'/'+file];
  const entryTypes=dir==='chapters'?new Map([[graph.entry,0]]):new Map();
  if(dir==='chapters'&&/^[1-6]$/.test(graph.chapter)){
   const ordered=Object.values(graph.nodes).filter(n=>n.source?.file&&n.source?.line>0).sort((a,b)=>a.source.file.localeCompare(b.source.file,'en',{numeric:true})||a.source.line-b.source.line);
   for(const [type,test] of [[3,n=>new RegExp('^1'+graph.chapter+'c').test(n.source.file)]]){const n=ordered.find(test);if(n&&!entryTypes.has(n.id))entryTypes.set(n.id,type);}
  }
  for(const [id,original] of Object.entries(graph.nodes)){
   const node=compact(original);if(dir==='chapters'&&node.type==='menu'&&node.selectionRole==='freetime')node.chapterEntryType=1;else if(dir==='chapters'&&node.type==='investigate')node.chapterEntryType=2;if(entryTypes.has(id))node.chapterEntryType=entryTypes.get(id);if(dir==='chapters'&&/^[1-6]$/.test(graph.chapter)&&node.type==='end'&&(node.chapterComplete||node.campaignNarrativeEnd))node.xpReward={kind:'Script',id:'chapter-completion:'+graph.chapter};const key=node.source?node.source.file+':'+node.source.location:'';
   if(comicPages.has(id))node.comicPage=comicPages.get(id);
   for(const range of presentationBindings.timeRanges||[])if(node.source?.file===range.source.file&&node.source.line>=range.startLine&&node.source.line<range.endLineExclusive)node.timeOfDay=range.timeOfDay;
   const records=presentationBindings.publicRecords?.eventById?.[id];if(records){node.publicRecords=records.map(key=>compact(presentationBindings.publicRecords.records[key]));node.showRecord=node.publicRecords.some(record=>record.showOnAcquire);}
   if(sceneBindings[key])node.scene={space:sceneBindings[key].space,perspective:sceneBindings[key].perspective||'current-observation',leaveCourt:/^1[1-6]d/.test(node.source.file)};
   for(const range of presentationBindings.sceneRanges||[])if(node.source?.file===range.source.file&&node.source.line>=range.startLine&&node.source.line<range.endLineExclusive)node.scene={space:range.space,perspective:range.perspective,leaveCourt:/^1[1-6]d/.test(node.source.file)};
   for(const range of presentationBindings.conditionalSceneRanges||[])if(node.source?.file===range.source.file&&node.source.line>=range.startLine&&node.source.line<range.endLineExclusive)(node.sceneVariants??=[]).push({space:range.space,when:range.when,perspective:range.perspective});
   if(['say','stage'].includes(node.type))for(const range of presentationBindings.cgRanges||[])if(node.source?.file===range.source.file&&node.source.line>=range.startLine&&node.source.line<range.endLineExclusive){if(node.shot)throw new Error('Overlapping V4 CG source ranges: '+node.id);node.shot={image:range.image.replaceAll('\\','/'),perspective:range.perspective||'current-observation'};}
   if(discoveries.byNode.has(id)){const shot=discoveries.byNode.get(id);if(node.shot&&node.shot.image!==shot.image)throw new Error('Conflicting discovery CG: '+id);node.shot=shot;}
   const signature=JSON.stringify(node);
   if(seen.has(id)&&seen.get(id)!==signature)throw new Error('Conflicting stable V4 node: '+id);
   const bucket=nodes[v4Bucket(id,nodeCount)].nodes;
   if(!seen.has(id)){bucket[id]=node;bucket[id].scope=0;seen.set(id,signature);nodeTotal++;}
   if(dir==='chapters')bucket[id].scope|=1<<(graph.chapter==='P'?0:Number(graph.chapter));
  }
  graph.taskNodes=Object.fromEntries(Object.entries(graph.nodes).filter(([,n])=>n.type==='task').map(([id,n])=>[n.taskId,id]));
  if(dir==='chapters'&&/^[1-6]$/.test(graph.chapter)){const id=graph.resultTaskId||`T${graph.chapter}-VOTE-01`;if(!['vote','reasoning'].includes(prepared.native.tasks[id]?.stage?.kind)||!graph.taskNodes[id])throw Error('Result boundary missing '+id);graph.resultTaskId=id;}
  const firstTask=Object.values(graph.nodes).find(n=>n.type==='task');if(firstTask)graph.trialRoster={dead:firstTask.trialDead,seats:firstTask.seats};
  delete graph.nodes;
  const header={...compact(graph),storage:'hash-shards-v1',bucketCount:nodeCount,bucketPrefix:'Assets/Data/v4_story/nodes/',taskBucketCount:taskCount,taskBucketPrefix:'Assets/Data/v4_story/native_tasks/'};
  if(!validGameJson(header))throw new Error('V4 header exceeds native data bounds: '+file);
  await checkedWrite('Assets/Data/v4_story/'+dir+'/'+file,header);
 }
 const taskFile=prepared.native;
 const mineObjectBanks=await emitMineObjects({repo,write});for(const bank of mineObjectBanks)bindMineObjects(taskFile.tasks[bank.taskId],bank);
 for(const [id,task] of Object.entries(taskFile.tasks))if(task.stage?.kind==='mindmine'&&!task.stage.mineObjects){
  if(task.stage.regions.length>10)throw Error('Mine hint supports at most ten authored regions');
  for(const [index,region] of task.stage.regions.entries()){
   const target='Assets/Art/ui/mine-hints/'+createHash('sha256').update(id+':'+index).digest('hex').slice(0,16)+'.svg';
   await write(target,mineHintSvg(region.polygon));region.hintOutline=target;
  }
 }
 for(const [id,task] of Object.entries(taskFile.tasks))tasks[v4Bucket(id,taskCount)].tasks[id]=compact(task);
 for(const [prefix,shards] of [['nodes',nodes]])for(let i=0;i<shards.length;i++){
  if(!validGameJson(shards[i]))throw new Error('V4 native shard bounds: '+prefix+'/'+i);
  await checkedWrite('Assets/Data/v4_story/'+prefix+'/'+i+'.json',shards[i]);
 }
 await emitV4DataPacks({repo,write:checkedWrite,family:'native_tasks',shards:tasks});
 const sourceManifest=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/manifest.json'),'utf8'));
 await checkedWrite('Assets/Data/v4_story/manifest.json',{schemaVersion:1,contentVersion:'v4',campaignReady:sourceManifest.campaignReady,playableNarrativeChapters:sourceManifest.playableNarrativeChapters,nodeCount:nodeTotal,nodeBuckets:nodeCount,taskBuckets:taskCount,storage:'hash-shards-v1'});
 // This is an obsolete generated copy, never the source evidence catalogue.
 await fs.rm(path.join(repo,'Game/Assets/Data/v4_story/tasks.json'),{force:true});
}
