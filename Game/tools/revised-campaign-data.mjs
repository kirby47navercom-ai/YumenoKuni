import path from 'node:path';
import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
import {validGameJson} from '../engineCreate/prototype/game-json.js';
import {v4Bucket} from './v4-data.mjs';
import {emitArmamentWordTextures,emitRevisedArmamentFigures} from './v4-armament-presentation.mjs';
import {emitArmamentText} from './v4-armament-text.mjs';
import {emitRevisedDebateFont} from './v4-gpu-trial-assets.mjs';
import {emitGpuAnagramAssets} from './v4-gpu-anagram-assets.mjs';
import {emitGpuShowdownAssets} from './v4-gpu-showdown-assets.mjs';
import {emitGpuPanicAssets} from './v4-gpu-panic-assets.mjs';
import {emitScrumClaims} from './claude-scrum-text.mjs';
import {extendComicSlots} from './v4-comic-ui.mjs';

export async function emitRevisedRuntimeAssets({source, tasks, write}) {
 const read = async name => JSON.parse(await fs.readFile(path.join(source, name), 'utf8'));
 const revisedTasks = Object.values(tasks);
 const glyphs = await emitRevisedDebateFont({source, tasks, write});
 const has = kind => revisedTasks.some(task => task.stage.kind === kind);
 for(const [kind, emit] of [['anagram',emitGpuAnagramAssets],['showdown',emitGpuShowdownAssets],['panic',emitGpuPanicAssets]]){
  if(has(kind))glyphs[kind]=await emit({output:source,write,revisedTasks});
 }
 if(has('scrum'))glyphs.scrum=await emitScrumClaims({
  tasks:revisedTasks,source,write,existing:await read('Assets/Data/scrum_v3text.json'),
 });
 if(has('armament')){
  await emitRevisedArmamentFigures({write,tasks,source});
  const words=await emitArmamentWordTextures({write,tasks,source});
  const transcript='Assets/Data/armament_transcripts_v4.json';
  await write(transcript,{...await read(transcript),...words.transcripts});
  const controller=revisedTasks.find(task=>task.stage.controllerQuestions)?.stage;
  const writeInk=async (name,value)=>{
   if(name==='Assets/Data/armament_text_revision.json'&&controller){
    for(const question of controller.controllerQuestions)for(const piece of question.final)
     assert(value.final.piece[piece],'Missing revised controller piece ink: '+piece);
   }
   await write(name,value);
  };
  glyphs.armament={textures:words.assets.length,ink:await emitArmamentText({write:writeInk,revisionTasks:tasks,source})};
 }
 if(has('climax')){
  const widgetName='Assets/UI/ComicV4.hbwidget.json',bankName='Assets/Data/climax_ui_v3.json';
  const widget=await read(widgetName),bank=await read(bankName);
  extendComicSlots(widget,bank.nodeIds);
  await write(widgetName,widget);
  await write(bankName,bank);
 }
 return glyphs;
}

export async function publishRevisedCampaign({repo, write, runtimeSource}) {
 const source = path.join(repo, 'tools/build_revised_campaign.py');
 const {chapters, tasks, mineAssets, encounters} = JSON.parse(execFileSync('python', ['-X', 'utf8', source], {
  encoding: 'utf8', maxBuffer: 16 * 1024 * 1024,
 }));
 const growth=JSON.parse(await fs.readFile(path.join(repo,'Game/Assets/Data/v4_story/growth.json'),'utf8'));
 growth.entries={};growth.flagIndex={};
 const actorFlags=new Map();
 for(const {actor,episode,title,flag,source} of encounters){
  const id=actor+':'+episode;
  growth.entries[id]={actor,episode,title,source,completionFlags:[flag],xpReward:'GetKakera'};
  growth.flagIndex[flag]=id;
  if(!actorFlags.has(actor))actorFlags.set(actor,[]);
  actorFlags.get(actor).push(flag);
 }
 for(const [id,offer] of Object.entries(growth.giftOffers)){
  if(actorFlags.has(offer.actor))offer.requiresAnyCompletionFlags=actorFlags.get(offer.actor);
  else delete growth.giftOffers[id];
 }
 await write('Assets/Data/v4_story/revision/growth.json',growth);
 if(!runtimeSource)await emitRevisedArmamentFigures({write,tasks});
 const finalController=Object.values(tasks).map(task=>task.stage).find(stage=>stage.controllerQuestions);
 if(finalController){
  const questions=finalController.controllerQuestions;
  if(finalController.chapter!==6||questions.length!==3||questions.some(question=>question.final.length!==4))
   throw Error('Invalid revised final armament controller');
  if(!runtimeSource)await write('Assets/Data/armament_final_questions.json',{version:1,questions});
 }
 for (const [name, data] of Object.entries(mineAssets)) {
  if (typeof data !== 'string' && !validGameJson(data)) throw Error(`Invalid revised mine asset: ${name}`);
  await write(name, data);
 }
 const caseArt=new Set(Object.values(chapters).flatMap(chapter=>Object.values(chapter.nodes))
  .map(node=>node.image).filter(name=>name?.startsWith('Assets/Art/revision_case/')));
 for(const name of caseArt)await write(name,await fs.readFile(path.join(repo,'art/revision_case',path.basename(name))));
 await write('Assets/Art/revision_mine/rear-door.webp', await fs.readFile(path.join(repo, 'art/inspection_v4/delivery/door_B_fixed_window.webp')));
 await write('Assets/Art/revision_mine/report-torn-edge.webp', await fs.readFile(path.join(repo, 'art/inspection_v4/delivery/report_torn_edge.webp')));
 const comics=Object.values(tasks).map(task=>task.stage).filter(stage=>stage.kind==='climax');
 if(comics.length){
  const bake=path.join(repo,'Game/Saved/campaign-revision/comic-bake');
  const assets=JSON.parse(execFileSync('python',['-X','utf8',path.join(repo,'tools/build_revised_comic_book.py'),bake,'--stdin'],
   {encoding:'utf8',input:JSON.stringify(comics)}));
  for(const [name,file]of Object.entries(assets)){
   const bytes=await fs.readFile(file);
   if(name.endsWith('.json')&&!validGameJson(JSON.parse(bytes.toString('utf8'))))throw Error('Invalid revised comic data: '+name);
   await write(name,bytes);
  }
  const verdictShots=new Set(Object.values(chapters).flatMap(chapter=>Object.values(chapter.nodes))
   .map(node=>node.shot?.image).filter(name=>name?.startsWith('Assets/Art/revision_comic/')));
  for(const name of verdictShots)await write(name,await fs.readFile(path.join(repo,name.replace('Assets/Art/','art/'))));
 }
 const bucketCount = 32;
 const bucketPrefix = 'Assets/Data/v4_story/revision/nodes/';
 const taskBucketPrefix = 'Assets/Data/v4_story/revision/tasks/';
 const buckets = Array.from({length: bucketCount}, () => ({nodes: {}}));
 let nodeCount = 0;
 for (const [chapter, {nodes, ...header}] of Object.entries(chapters)) {
  const scope = 1 << (chapter === 'P' ? 0 : Number(chapter));
  for (const node of Object.values(nodes)) {
   buckets[v4Bucket(node.id, bucketCount)].nodes[node.id] = {...node, scope};
   ++nodeCount;
  }
  await write(`Assets/Data/v4_story/revision/chapters/${chapter}.json`, {
   ...header, storage: 'hash-shards-v1', bucketCount, bucketPrefix, taskBucketPrefix,
  });
 }
 const taskPages = new Map();
 const labels = new Set();
 for (const [id, bundle] of Object.entries(tasks)) {
  const index = v4Bucket(id, 64);
  if (!taskPages.has(index)) taskPages.set(index, {tasks: {}});
  taskPages.get(index).tasks[id] = bundle;
  if (['nonstop', 'panic', 'lie'].includes(bundle.stage.kind)) for (const option of bundle.stage.options) labels.add(option.name);
  if (bundle.transformation?.lieLabel) labels.add(bundle.transformation.lieLabel);
 }
 const letters = new Set([...labels].join('').replace(/\s/g, ''));
 for (const letter of letters) {
  const file = `u_${letter.codePointAt(0).toString(16)}_w.glb`;
  const base = path.join(repo, 'art', 'nonstop_solid_type', file);
  const extra = path.join(repo, 'art', 'revision_kotodama', file);
  const bytes = await fs.readFile(base).catch(error => {
   if (error.code !== 'ENOENT') throw error;
   return fs.readFile(extra).catch(() => {throw Error(`Missing revised evidence projectile letter: ${letter} (${file})`);});
  });
  await write(`Assets/Art/nonstop_solid_type/${file}`, bytes);
 }
 for (const [index, page] of taskPages) {
  if (!validGameJson(page)) throw Error(`Revised task data exceeds native JSON bounds: ${index}`);
  await write(`${taskBucketPrefix}${index}.json`, page);
 }
 for (let i = 0; i < bucketCount; i++) {
  if (!validGameJson(buckets[i])) throw Error(`Revised campaign exceeds native JSON bounds: ${i}`);
  await write(`${bucketPrefix}${i}.json`, buckets[i]);
 }
 const result={chapters:Object.keys(chapters),nodes:nodeCount,tasks:Object.keys(tasks).length};
 if(runtimeSource){
  result.runtimeAssets=await emitRevisedRuntimeAssets({source:runtimeSource,tasks,write});
  await write('Assets/Data/v4_story/revision/campaign.json',{campaignRevision:'rewrite-v5'});
 }
 return result;
}
