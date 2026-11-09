import assert from 'node:assert/strict';
import {createHash,randomUUID} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {connect, makeNode} from '../../../engineCreate/prototype/blueprint-model.js';
import {prepareTaskFixtures} from './native-task-fixtures.mjs';
import {createOwnedNativePackage} from './native-owned-package.mjs';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {trialAimPlan} from './v4-aim-test-input.mjs';
import {bulletCycleKey} from './v4-bullet-test-input.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
import {emitRevisedRuntimeAssets} from './revised-campaign-data.mjs';
import {validGameJson} from '../../../engineCreate/prototype/game-json.js';

const game = path.resolve(import.meta.dirname, '..');
const root = 'Assets/Data/v4_story/revision';
const normalArchive = process.argv.find(arg=>arg.startsWith('--normal-archive='))?.slice(17);
const normalEntry = Boolean(normalArchive)||process.argv.includes('--normal-entry');
const normalRuntime = normalEntry||process.argv.includes('--normal-runtime');
const revisionRoot = path.join(game, 'Saved', 'campaign-revision');
const previewContent = path.resolve(revisionRoot,
 process.argv.find(arg=>arg.startsWith('--preview-content='))?.slice(18)||'content');
assert(previewContent.startsWith(revisionRoot+path.sep));
const source = path.resolve(process.argv[2]);
const runtimeContentArgument=process.argv.find(arg=>arg.startsWith('--runtime-content='))?.slice(18);
const module = path.resolve(process.argv[3]);
const work = path.join(game, 'Saved', 'campaign-revision', `native-${Date.now()}-${randomUUID().slice(0, 8)}`);
const checks = [];
const authoredTasks = {};
const reused = process.argv.find(arg => arg.startsWith('--reuse='))?.slice(8);
const preparedRevision = process.argv.find(arg=>arg.startsWith('--prepared-revision='))?.slice(20);
const secondOnly = process.argv.includes('--chapter-two');
const secondOpening = process.argv.includes('--chapter-two-opening');
const secondLate = process.argv.includes('--chapter-two-later');
const firstInvestigation = process.argv.includes('--chapter-one-investigation');
const firstOnly = firstInvestigation || process.argv.includes('--chapter-one');
const firstDaily = process.argv.includes('--chapter-one-daily');
const secondDaily = process.argv.includes('--chapter-two-daily');
const secondPriorMeeting = process.argv.includes('--prior-sora-meeting');
const thirdDaily = process.argv.includes('--chapter-three-daily');
const fourthDaily = process.argv.includes('--chapter-four-daily');
const thirdOnly = process.argv.includes('--chapter-three');
const thirdTimeline = process.argv.includes('--chapter-three-timeline');
const thirdPanic = process.argv.includes('--chapter-three-panic');
const thirdPaper = process.argv.includes('--chapter-three-paper');
const thirdContinuity = process.argv.includes('--chapter-three-continuity');
const thirdArmament = process.argv.includes('--chapter-three-armament');
const thirdVictim = process.argv.includes('--chapter-three-victim');
const thirdVote = process.argv.includes('--chapter-three-vote');
const thirdComic = process.argv.includes('--chapter-three-comic');
const thirdArchive = process.argv.includes('--chapter-three-archive');
const thirdBook = thirdVote || thirdComic;
const thirdLater = thirdArchive || thirdBook || thirdVictim || thirdArmament || thirdContinuity || thirdPaper || thirdTimeline || thirdPanic || process.argv.includes('--chapter-three-later');
const thirdNoDemo = process.argv.includes('--chapter-three-opening-no-demo');
const thirdOpening = thirdNoDemo || process.argv.includes('--chapter-three-opening');
const prologueOnly = process.argv.includes('--prologue-only');
const laterOnly = process.argv.includes('--chapter-one-later');
const mineOnly = process.argv.includes('--door-mine');
const paperMine = process.argv.includes('--paper-mine');
const witnessOnly = process.argv.includes('--witness-view');
const witnessBoundaries = process.argv.includes('--witness-boundaries');
const paperLie = process.argv.includes('--paper-lie');
const paperOnly = paperLie || process.argv.includes('--paper-comparison');
const rescueOnly = process.argv.includes('--rescue-hearing');
const paperSequence = process.argv.includes('--paper-sequence');
const phoneEvidence = process.argv.includes('--phone-evidence');
const phoneOnly = phoneEvidence || process.argv.includes('--phone-hearing');
const signatureOnly = process.argv.includes('--signature-hearing');
const armamentOnly = process.argv.includes('--armament-hearing');
const comicOnly = process.argv.includes('--comic-hearing');
const voteOnly = process.argv.includes('--vote-hearing');
const theatreRing = process.argv.includes('--theatre-ring');
const theatreArguments = process.argv.includes('--chapter-two-arguments');
const theatreSighting = process.argv.includes('--chapter-two-sighting');
const theatreArmament = process.argv.includes('--chapter-two-armament');
const theatreComic = process.argv.includes('--chapter-two-comic');
const theatreVote = process.argv.includes('--chapter-two-vote');
const theatrePhysical = process.argv.includes('--chapter-two-physical');
const fourthPhysical=process.argv.includes('--chapter-four-physical');
const fourthIdentity=process.argv.includes('--chapter-four-identity');
const fourthRoute=process.argv.includes('--chapter-four-route');
const fourthComic=process.argv.includes('--chapter-four-comic');
const fourthVote=process.argv.includes('--chapter-four-vote');
const fourthFinal=process.argv.includes('--chapter-four-final');
const fourthLie=process.argv.includes('--chapter-four-lie');
const fourthLast=fourthLie||process.argv.includes('--chapter-four-last');
const fourthReasoning=process.argv.includes('--chapter-four-reasoning');
const fourthBook=fourthComic||fourthVote;
const fourthFocus=fourthPhysical||fourthIdentity||fourthRoute||fourthBook||fourthFinal||fourthLast||fourthReasoning;
const fifthTiming=process.argv.includes('--chapter-five-timing');
const fifthPackage=process.argv.includes('--chapter-five-package');
const fifthLate=process.argv.includes('--chapter-five-late');
const fifthFinal=process.argv.includes('--chapter-five-final');
const fifthComic=process.argv.includes('--chapter-five-comic');
const fifthDaily=process.argv.includes('--chapter-five-daily');
const fifthFocus=fifthTiming||fifthPackage||fifthLate||fifthFinal||fifthComic;
const sixthPast=process.argv.includes('--chapter-six-past');
const sixthOpening=process.argv.includes('--chapter-six-opening');
const sixthTransition=process.argv.includes('--chapter-six-transition');
const sixthPersonal=process.argv.includes('--chapter-six-personal');
const sixthOperating=process.argv.includes('--chapter-six-operating');
const sixthPost=process.argv.includes('--chapter-six-post');
const sixthClosing=process.argv.includes('--chapter-six-closing');
const sixthComic=process.argv.includes('--chapter-six-comic');
const sixthEnding=process.argv.includes('--chapter-six-ending');
const sixthDaily=process.argv.includes('--chapter-six-daily');
const dailyAlternate=process.argv.includes('--daily-alternate');
const sixthSupportEnds=process.argv.includes('--support-ends');
const sixthFocus=sixthOpening||sixthPast||sixthTransition||sixthPersonal||sixthOperating||sixthPost||sixthClosing||sixthComic||sixthEnding;
const lateChapter = sixthFocus||sixthDaily ? 6 : fifthFocus||fifthDaily ? 5 : fourthFocus||fourthDaily ? 4 : [['--chapter-four', 4], ['--chapter-five', 5], ['--chapter-six', 6]]
 .find(([arg]) => process.argv.includes(arg))?.[1];
const blueprint = 'Content/Assets/Blueprints/BP_Yumeno.hbblueprint.json';

function addPreviewKeys(bp) {
 const keys = [['F7', 7], ['F8', 8]];
 for (const [enabled, key, index] of [[secondOnly || secondOpening || secondDaily, 'F9', 9], [thirdOnly || thirdLater, 'F10', 10],
  [laterOnly, 'F11', 11], [mineOnly, 'F12', 12], [witnessOnly||witnessBoundaries, 'F6', 13], [paperOnly, 'F5', 14],
  [paperMine, 'F4', 15], [rescueOnly, 'F3', 16], [paperSequence, 'F1', 17],
  [secondLate, 'F13', 18], [thirdOpening||thirdDaily, 'F14', 19], [phoneOnly && !phoneEvidence, 'F18', 23], [phoneEvidence, 'F22', 27],
  [signatureOnly, 'F19', 24], [armamentOnly, 'F20', 25], [comicOnly, 'F21', 26], [theatreRing || theatreArguments, 'F23', 28],
  [voteOnly, 'F24', 29], [theatreSighting, 'F22', 30], [theatreArmament, 'F21', 31],
  [theatreComic,'F20',32],[theatreVote,'F19',33],[theatrePhysical,'F18',34]]) if (enabled) keys.push([key, index]);
 if (lateChapter) keys.push(['F' + (lateChapter + 11), lateChapter + 16]);
 for (const [key, index] of keys) {
  if (bp.nodes.some(node => node.nativeId === 'Yumeno.DebugV4Chapter' && node.inputValues?.index === index)) continue;
  assert(!bp.nodes.some(node => node.options?.key === key), `QA key already bound: ${key}`);
  const input = makeNode('input', 100, 800 + index * 100);
  const call = makeNode('nativeCall', 400, 800 + index * 100);
  input.options = {key};
  call.nativeId = 'Yumeno.DebugV4Chapter';
  call.inputValues = {index};
  bp.nodes.push(input, call);
  const result = connect(bp, {node: input.id, pin: 'then'}, {node: call.id, pin: 'exec'});
  assert(result.ok, result.reason);
 }
 return Buffer.from(JSON.stringify(bp));
}

async function prepare() {
 await fs.mkdir(work, {recursive: true});
 const content = {};
 const tasks = authoredTasks;
 const selection = `Content/${root}/campaign.json`;
 const growth = `${root}/growth.json`;
 const growthFile = path.join(previewContent,growth);
 if(await fs.access(growthFile).then(()=>true,()=>false))content['Content/'+growth]=growthFile;
 const previouslySelected = reused && await fs.access(path.join(reused, selection)).then(() => true, () => false);
 if (normalRuntime || previouslySelected) {
  content[selection] = path.join(work, 'campaign-selection.json');
  await fs.writeFile(content[selection], JSON.stringify({campaignRevision: normalRuntime ? 'rewrite-v5' : ''}));
 }
 for (const dir of ['chapters', 'nodes', 'tasks', 'mine']) {
  for (const file of await fs.readdir(path.join(previewContent, root, dir))) {
   const key = `${root}/${dir}/${file}`;
   content[`Content/${key}`] = path.join(previewContent, key);
   if (dir === 'tasks') Object.assign(tasks, JSON.parse(await fs.readFile(path.join(previewContent, key), 'utf8')).tasks);
  }
 }
 const mineArt = 'Assets/Art/revision_mine/';
 for (const file of await fs.readdir(path.join(previewContent, mineArt))) {
  const key = mineArt + file;
  content[`Content/${key}`] = path.join(previewContent, key);
 }
 const caseArt = 'Assets/Art/revision_case/';
 const caseFiles = await fs.readdir(path.join(previewContent,caseArt)).catch(error=>{
  if(error.code!=='ENOENT')throw error;
  return [];
 });
 for(const file of caseFiles)content['Content/'+caseArt+file]=path.join(previewContent,caseArt,file);
 for (const task of Object.values(tasks)) for (const object of task.stage.mineObjects || []) {
  for (const key of [object.texture, object.maskAsset, object.hintLocal]) {
   await fs.access(content[`Content/${key}`] || path.join(source, 'Content', key));
  }
 }
 for (const task of Object.values(tasks)) if (['nonstop', 'panic', 'lie'].includes(task.stage.kind)) {
  const labels = task.stage.options.map(option => option.name);
  if (task.transformation?.lieLabel) labels.push(task.transformation.lieLabel);
  for (const label of labels) for (const letter of label.replace(/\s/g, '')) {
   const key = `Assets/Art/nonstop_solid_type/u_${letter.codePointAt(0).toString(16)}_w.glb`;
   try {await fs.access(path.join(source, 'Content', key));}
   catch (error) {
    if (error.code !== 'ENOENT') throw error;
    content[`Content/${key}`] = path.join(previewContent, key);
   }
  }
 }
 const nativeContent = runtimeContentArgument?path.resolve(runtimeContentArgument):path.join(source,'Content');
 if(runtimeContentArgument){
  assert(nativeContent===game||nativeContent.startsWith(path.join(game,'Saved')+path.sep));
  for(const font of ['pretendard/Pretendard-Medium.otf','pretendard/Pretendard-Regular.otf','dohyeon/DoHyeon-Regular.ttf'])
   content['Content/Assets/Fonts/'+font]=path.join(nativeContent,'Assets/Fonts',font);
 }
 const writeGlyph = async (name, value) => {
  if (name.startsWith('Assets/Data/')) assert(validGameJson(value, {object: false}), `GPU layout exceeds native asset limits: ${name}`);
  const file = path.join(work, 'glyphs', name);
  const bytes=Buffer.isBuffer(value)?value:Buffer.from(JSON.stringify(value));
  const digest=createHash('sha256').update(bytes).digest('hex');
  const cached=path.join(revisionRoot,'runtime-asset-cache',digest.slice(0,2),digest+path.extname(name));
  await fs.mkdir(path.dirname(cached),{recursive:true});
  if(!await fs.access(cached).then(()=>true,()=>false)){
   const temporary=cached+'.'+randomUUID()+'.tmp';
   try{
    await fs.writeFile(temporary,bytes,{flag:'wx'});
    await fs.link(temporary,cached).catch(error=>{if(error.code!=='EEXIST')throw error;});
   }finally{await fs.rm(temporary,{force:true});}
  }
  await fs.mkdir(path.dirname(file), {recursive: true});
  if(await fs.access(file).then(()=>true,()=>false)){
   const old=await fs.readFile(file);
   if(!old.equals(bytes)){await fs.unlink(file);await fs.link(cached,file);}
  }else{
  await fs.link(cached,file);
  }
  content[`Content/${name}`] = file;
 };
 if(firstInvestigation){
  const name=root+'/chapters/1.json';
  const header=JSON.parse(await fs.readFile(path.join(previewContent,name),'utf8'));
  // The investigation also needs the application earned during daily life.
  // Resume at its authored acquisition rather than inventing checkpoint cards.
  header.entry='rev:01:application';
  await writeGlyph(name,header);
 }
 if (thirdLater) {
  const name = root + '/chapters/3.json';
  const header = JSON.parse(await fs.readFile(path.join(previewContent,name),'utf8'));
  const checkpoint = thirdArchive ? 'archive-inspection' : thirdVote ? 'vote-hearing' : thirdComic ? 'comic-hearing' : thirdVictim ? 'victim-hearing' : thirdArmament ? 'armament-hearing' : thirdContinuity ? 'continuity-hearing' : thirdPaper ? 'paper-hearing' : thirdPanic ? 'handover-hearing' : thirdTimeline ? 'timeline-hearing' : 'later-hearing';
  assert(header.qaCheckpoints[checkpoint]);
  header.qaCheckpoints.incident = header.qaCheckpoints[checkpoint];
  await writeGlyph(name,header);
 }
 if(fourthFocus){
  const name=root+'/chapters/4.json';
  const header=JSON.parse(await fs.readFile(path.join(previewContent,name),'utf8'));
  header.entry=header.qaCheckpoints[fourthReasoning?'reasoning-hearing':fourthLast?'last-hearing':fourthFinal?'final-hearing':fourthComic?'comic-hearing':fourthVote?'vote-hearing':fourthRoute?'route-hearing':fourthIdentity?'identity-hearing':'physical-hearing'].entry;
  await writeGlyph(name,header);
 }
 if(fifthFocus){
  const name=root+'/chapters/5.json';
  const header=JSON.parse(await fs.readFile(path.join(previewContent,name),'utf8'));
  const checkpoint=fifthComic?'comic-hearing':fifthFinal?'final-hearing':fifthLate?'late-hearing':fifthPackage?'package-hearing':'timing-hearing';
  header.entry=header.qaCheckpoints[checkpoint].entry;
  await writeGlyph(name,header);
 }
 if(sixthFocus){
  const name=root+'/chapters/6.json';
  const header=JSON.parse(await fs.readFile(path.join(previewContent,name),'utf8'));
  const checkpoint=sixthOpening?'opening-hearing':sixthPast?'past-hearing':sixthTransition?'transition-hearing':
   sixthPersonal?'personal-hearing':sixthOperating?'operating-hearing':sixthPost?'post-operating-hearing':
   sixthClosing?'closing-hearing':sixthComic?'comic':'ending';
  header.entry=header.qaCheckpoints[checkpoint].entry;
  await writeGlyph(name,header);
 }
 if(secondDaily&&secondPriorMeeting){
  const name=root+'/chapters/2.json';
  const header=JSON.parse(await fs.readFile(path.join(previewContent,name),'utf8'));
  header.entry=header.qaCheckpoints['life-with-prior-meeting'].entry;
  await writeGlyph(name,header);
 }
 if(witnessBoundaries){
  const name=root+'/chapters/1.json';
  const header=JSON.parse(await fs.readFile(path.join(previewContent,name),'utf8'));
  header.qaCheckpoints['witness-view']=header.qaCheckpoints['witness-boundaries'];
  await writeGlyph(name,header);
 }
 const runtimeHash=createHash('sha256').update(JSON.stringify(tasks))
  .update(nativeContent)
  .update(await fs.readFile(path.join(source,'game.hbpack.json')))
  .update(await fs.readFile(path.join(game,'Source/Yumeno.cpp')))
  .update(await fs.readFile(path.resolve(game,'../../engineCreate/tools/native-widget-paint.mjs')));
 for(const name of (await fs.readdir(import.meta.dirname)).filter(name=>name.endsWith('.mjs')).sort())
  runtimeHash.update(name).update(await fs.readFile(path.join(import.meta.dirname,name)));
 const runtimeIndex=path.join(revisionRoot,'runtime-asset-cache','sets',runtimeHash.digest('hex')+'.json');
 const retained=runtimeContentArgument?null:await fs.readFile(runtimeIndex,'utf8').then(JSON.parse,error=>{
  if(error.code==='ENOENT')return null;throw error;
 });
 let glyphs;
 if(retained){
  for(const [name,file]of Object.entries(retained.assets)){
   assert(file.startsWith(path.join(revisionRoot,'runtime-asset-cache')+path.sep));
   await fs.access(file);
   content['Content/'+name]=file;
  }
  glyphs=retained.report;
 }else{
  const assets={};
  const retain=async(name,value)=>{
   await writeGlyph(name,value);
   const bytes=Buffer.isBuffer(value)?value:Buffer.from(JSON.stringify(value));
   const digest=createHash('sha256').update(bytes).digest('hex');
   assets[name]=path.join(revisionRoot,'runtime-asset-cache',digest.slice(0,2),digest+path.extname(name));
  };
  glyphs=await emitRevisedRuntimeAssets({source:nativeContent,tasks,write:retain});
  await fs.mkdir(path.dirname(runtimeIndex),{recursive:true});
  const temporary=runtimeIndex+'.'+randomUUID()+'.tmp';
  await fs.writeFile(temporary,JSON.stringify({report:glyphs,assets}));
  await fs.rename(temporary,runtimeIndex);
 }
 const revisedTasks=Object.values(tasks);
 const controller=revisedTasks.find(task=>task.stage.controllerQuestions)?.stage;
 if(controller){
  // Earlier checkpoint modules read this base filename. The current module
  // reads the questions from its own task, leaving the V4 build data intact.
  const name='Assets/Data/armament_final_questions.json';
  const authored=JSON.parse(await fs.readFile(path.join(previewContent,name),'utf8'));
  assert.deepEqual(authored.questions,controller.controllerQuestions);
  if(!normalRuntime)await writeGlyph(name,authored);
 }
 const comics=revisedTasks.map(task=>task.stage).filter(stage=>stage.kind==='climax');
 if(comics.length){
  const readNative=async name=>JSON.parse(await fs.readFile(path.join(nativeContent,name),'utf8'));
  for (const stage of comics) {
   const book = stage.comicPresentation.bookFile;
   const comicArt = 'Assets/Art/revision_comic/' + path.basename(book, '.json');
   for (const file of await fs.readdir(path.join(previewContent, comicArt))) {
    const name = comicArt + '/' + file;
    content['Content/' + name] = path.join(previewContent, name);
   }
   content['Content/' + book] = path.join(previewContent, book);
  }
  const artName = 'Assets/Data/art.json', art = await readNative(artName);
  const currentArt = JSON.parse(await fs.readFile(path.join(game,artName),'utf8'));
  for (const cue of ['bgm_trial_climax_replay','bgm_trial_climax_replay_intro']) {
   const asset = currentArt.audio[cue];
   const descriptor = JSON.parse(await fs.readFile(path.join(game,asset),'utf8'));
   art.audio[cue] = asset;
   if (currentArt.audioLen[cue]) art.audioLen[cue] = currentArt.audioLen[cue];
   content['Content/'+asset] = path.join(game,asset);
   content['Content/'+descriptor.clip] = path.join(game,descriptor.clip);
  }
  await writeGlyph(artName,art);
 }
 await fs.writeFile(path.join(work, 'glyph-report.json'), JSON.stringify(glyphs));
 if (reused) {
  const output = path.resolve(reused);
  assert(output.startsWith(path.join(game, 'Saved', 'campaign-revision') + path.sep));
  const manifestFile = path.join(output, 'game.hbpack.json');
  const manifest = JSON.parse(await fs.readFile(manifestFile, 'utf8'));
  const manifestRows = new Map(manifest.files.map(row => [row.path, row]));
  const sha = bytes => createHash('sha256').update(bytes).digest('hex');
  assert(module.startsWith(path.join(game, 'Saved') + path.sep));
  const binary = manifest.nativeModules[0].binary;
  assert(manifest.files.some(row => row.path === binary));
  content[binary] = module;
  if (firstDaily || secondDaily || thirdDaily || firstOnly || secondOnly || secondOpening || secondLate || thirdOnly || thirdOpening || laterOnly || mineOnly || witnessOnly || witnessBoundaries ||
      paperOnly || paperMine || rescueOnly || paperSequence || lateChapter || thirdLater || phoneOnly || signatureOnly || armamentOnly || comicOnly ||
      theatreRing || theatreArguments || theatreSighting || theatreArmament || theatreComic || theatreVote || theatrePhysical || voteOnly) {
   const bp = JSON.parse(await fs.readFile(path.join(source, blueprint), 'utf8'));
   content[blueprint] = path.join(work, 'qa-blueprint.json');
   await fs.writeFile(content[blueprint], addPreviewKeys(bp));
  }
  for (const [name, file] of Object.entries(content)) {
   const bytes = await fs.readFile(file);
   const digest = sha(bytes);
   const destination = path.join(output, name);
   let row = manifestRows.get(name);
   if (row?.sha256 === digest && row.bytes === bytes.length &&
       await fs.stat(destination).then(stat => stat.size === bytes.length, () => false)) continue;
   if (!row) {
    assert(/^Content\/Assets\/Art\/ui\/gpu_(trial|anagram|showdown|panic)\//.test(name) ||
     name.startsWith('Content/Assets/Art/ui/scrum_v3text/') ||
     name.startsWith('Content/Assets/Art/ui/armament_stream/') ||
     name.startsWith('Content/Assets/Art/ui/armament_ink/') ||
     name === 'Content/Assets/Data/armament_text_revision.json' ||
     name.startsWith('Content/Assets/Art/revision_comic/') ||
     name.startsWith('Content/Assets/Art/revision_case/') ||
     name.startsWith('Content/Assets/Art/revision_armament/') ||
     name.startsWith('Content/Assets/Data/revision_comic/') ||
     /^Content\/Assets\/Audio\/(?:S_)?bgm_trial_climax_replay(?:_intro)?\.(?:ogg|hbaudioasset\.json)$/.test(name) ||
     /^Content\/Assets\/Data\/gpu_showdown_revision_\d+\.json$/.test(name) ||
     name.startsWith('Content/Assets/Art/nonstop_solid_type/') || name.startsWith(`Content/${root}/`) || name.startsWith(`Content/${mineArt}`), name);
    row = {path: name};
    manifest.files.push(row);
    manifestRows.set(name, row);
    const kind = name.endsWith('.hbaudioasset.json') ? 'audioasset' : name.endsWith('.ogg') ? 'media' :
     name.endsWith('.hbspriterig.json') ? 'spriterig' : name.endsWith('.hbsprite.json') ? 'sprite' :
     name.endsWith('.json') ? 'json' : name.endsWith('.glb') ? 'model' : 'texture';
    manifest.entries.push({path: name.slice(8), name: path.basename(name), kind});
   }
   await fs.mkdir(path.dirname(destination), {recursive: true});
   await fs.writeFile(destination + '.revision.tmp', bytes);
   await fs.rename(destination + '.revision.tmp', destination);
   Object.assign(row, {bytes: bytes.length, sha256: digest});
  }
  await fs.writeFile(manifestFile, JSON.stringify(manifest));
  return {output, manifest, executable: path.join(output, manifest.windowsApplication.executable)};
 }
 const baseBp = path.join(source, blueprint);
 const hasStats = JSON.parse(await fs.readFile(baseBp, 'utf8')).nodes.some(node => node.nativeId === 'Yumeno.Stats');
 if (hasStats) content[blueprint] = baseBp;
 const overlay = path.join(work, 'overlay.json');
 await fs.writeFile(overlay, JSON.stringify(content));
 const options = {gameModuleCandidate: module, gameContentOverrides: overlay};
 const prepared = hasStats ? await createOwnedNativePackage({source, work, ...options}) : await prepareTaskFixtures(source, work, options);
 const file = path.join(prepared.output, blueprint);
 const bp = JSON.parse(await fs.readFile(file, 'utf8'));
 const bytes = normalEntry ? Buffer.from(JSON.stringify(bp)) : addPreviewKeys(bp);
 await fs.writeFile(file, bytes);
 Object.assign(prepared.manifest.files.find(row => row.path === blueprint), {
  bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex'),
 });
 await fs.writeFile(path.join(prepared.output, 'game.hbpack.json'), JSON.stringify(prepared.manifest));
 return prepared;
}

let prepared;
if(preparedRevision){
 assert(reused,'Repeating a prepared scenario requires the existing owned package');
 await fs.mkdir(work,{recursive:true});
 const output=path.resolve(reused);
 assert(output.startsWith(path.join(game,'Saved','campaign-revision')+path.sep));
 const manifest=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8'));
 const bp=JSON.parse(await fs.readFile(path.join(output,blueprint),'utf8')),before=JSON.stringify(bp);
 addPreviewKeys(bp);
 assert.equal(JSON.stringify(bp),before,'The prepared package must already contain the selected scenario bindings');
 const taskDirectory=path.join(output,'Content',root,'tasks');
 for(const name of await fs.readdir(taskDirectory))
  Object.assign(authoredTasks,JSON.parse(await fs.readFile(path.join(taskDirectory,name),'utf8')).tasks);
 prepared={output,manifest,executable:path.join(output,manifest.windowsApplication.executable)};
}else prepared=await prepare();
const revisionFiles = prepared.manifest.files.filter(row =>
 row.path.startsWith('Content/'+root+'/') ||
 row.path.startsWith('Content/Assets/Data/revision_comic/') ||
 /^Content\/Assets\/Data\/armament_(?:final_questions|text_revision|transcripts_v4)\.json$/.test(row.path) ||
 /^Content\/Assets\/Art\/revision_(?:comic|case|armament|mine)\//.test(row.path))
 .map(({path,sha256})=>({path,sha256})).sort((a,b)=>a.path.localeCompare(b.path));
const identity = {revisionSHA256:createHash('sha256').update(JSON.stringify(revisionFiles)).digest('hex'),
 revisionFiles:revisionFiles.length,gameModule:prepared.manifest.nativeModules[0].binary,
 gameModuleSHA256:prepared.manifest.files.find(row=>row.path===prepared.manifest.nativeModules[0].binary).sha256,
 runtimeContent:runtimeContentArgument?path.resolve(runtimeContentArgument):path.join(source,'Content'),
 fontSHA256:Object.fromEntries(prepared.manifest.files.filter(row=>/^Content\/Assets\/Fonts\/(pretendard|dohyeon)\//.test(row.path)&&/\.(ttf|otf)$/.test(row.path)).map(row=>[row.path,row.sha256]))};
if(preparedRevision){
 assert.equal(identity.revisionSHA256,preparedRevision,'The prepared content must match the exact prior scenario');
 assert.equal(identity.gameModuleSHA256,createHash('sha256').update(await fs.readFile(module)).digest('hex'));
 assert.equal(identity.gameModuleSHA256,createHash('sha256').update(await fs.readFile(path.join(prepared.output,identity.gameModule))).digest('hex'));
}
let preparedNodes;
async function readPreparedNodes(){
 if(!preparedNodes){
  const directory=path.join(prepared.output,'Content',root,'nodes');
  preparedNodes=Promise.all((await fs.readdir(directory)).map(async name=>
   JSON.parse(await fs.readFile(path.join(directory,name),'utf8')).nodes)).then(pages=>Object.assign({},...pages));
 }
 return preparedNodes;
}
let probe;
try {
 const run = path.join(work, 'run');
 const open = dir => nativeWindowProbe({source, prepared, work: dir, maxFrames: null, heartbeatTimeoutMs: 120000});
 const saveDirectory = dir => path.join(dir, 'State', 'Saves');
 const legacyName = 'yumeno-progress-v4.json';
 const legacy = JSON.stringify({contentVersion:'v4',chapter:'P',node:'v4:legacy-isolation-sentinel'});
 if (normalArchive) {
  const archive=path.resolve(revisionRoot,normalArchive);
  assert(archive.startsWith(revisionRoot+path.sep));
  await fs.mkdir(path.join(run,'State'),{recursive:true});
  await fs.cp(saveDirectory(archive),saveDirectory(run),{recursive:true,errorOnExist:true,force:false});
 } else if (normalEntry) {
  await fs.mkdir(saveDirectory(run), {recursive:true});
  await fs.writeFile(path.join(saveDirectory(run), legacyName), legacy, {flag:'wx'});
 }
 probe = await open(run);
 const state = async () => {
  const stats = await probe.stats();
  assert(!stats.error && !stats.routeBlocked, JSON.stringify({node: stats.node, error: stats.error}));
  return stats;
 };
 const restraintWitnesses = new Set();
 const fourthViews=new Set();
 const advance = async stats => {
  if(fourthPhysical&&/^rev:04:(?:remote-pull|sound)-hypotheses:done:\d$/.test(stats.node))fourthViews.add(stats.node);
  let scenarioChoice = ({
   'rev:04:door-comparison:0':1,'rev:04:door-comparison:1':0,
   'rev:04:door-comparison:2':1,'rev:04:door-comparison:3':0,
   'rev:05:cup-separation':1,
   'rev:02:sort-perjury':1,'rev:02:outside-force':1,
   'rev:01:final-evidence-custody':2,
   'rev:02-I07n:observation:0':2,'rev:03-I00f:observation:0':2,
   'rev:03:paper-observation-separation':2,
   'rev:03-D0A:choice':thirdNoDemo ? 1 : 0,
   'rev:03-D01t:choice':2,
   'rev:04:rescue-hypotheses:fall-direction':1,
   'rev:04:rescue-hypotheses:photo-boundary':2,
   'rev:04:visibility-match:0':1,
   'rev:04:visibility-match:1':0,
   'rev:04:visibility-match:2':1,
   'rev:04:witness-source-match:0':1,
   'rev:04:witness-source-match:1':0,
   'rev:04:witness-source-match:2':1,
   'rev:04:rewind-boundaries':1,
   'rev:05:package-custody':1,
   'rev:05:call-and-wait':1,
   'rev:05:first-open-witness':2,
   'rev:05:rewind-claim-boundary':2,
  })[stats.node];
  if((firstDaily||secondDaily||thirdDaily||fourthDaily)&&stats.mode==='menu'){
   const node=(await readPreparedNodes())[stats.node];
   scenarioChoice=dailyAlternate ? (node?.options?.length??1)-1 : 0;
  }
  if(fifthDaily||sixthDaily){
   const choices=dailyAlternate?{
    'rev:05:free-before-agreement':1,'rev:05:free-before-duties':1,'rev:05:free-before-case':0,
    'rev:05-F02:choice':1,'rev:05-D03a:choice':2,
    'rev:05-D02g:choice':2,'rev:06-D01d:choice':2,'rev:06-D03f:choice':2,
   }:{
    'rev:05:free-before-agreement':0,'rev:05:free-before-duties':0,'rev:05:free-before-case':0,
    'rev:05-F01:choice':0,'rev:05-F02:choice':0,'rev:05-D03a:choice':0,
   };
   scenarioChoice=choices[stats.node]??scenarioChoice;
  }
  if (thirdLater && stats.node === 'rev:03:restraint-witnesses') {
   scenarioChoice = [...Array(4).keys()].find(index=>!restraintWitnesses.has(index)) ?? 4;
  }
  if (scenarioChoice !== undefined && stats.mode === 'menu' && stats.choice?.pending < 0) {
   if (stats.choice.hover === scenarioChoice) {
    await probe.tap('Enter');
    if (stats.node === 'rev:03:restraint-witnesses' && scenarioChoice < 4) restraintWitnesses.add(scenarioChoice);
   } else await probe.tap('ArrowDown');
   return;
  }
  if (stats.auto?.kind === 'key') await probe.tap(stats.auto.key);
  else if (stats.auto?.kind === 'click') await probe.click(stats.auto.x, stats.auto.y);
  else if (stats.auto?.kind === 'move') await probe.move(stats.auto.x, stats.auto.y);
  else if (stats.auto?.kind === 'rapid-key' && stats.auto.key === 'mouse0') await probe.click(640, 360);
  else if (stats.auto?.kind === 'sd-slash') {
   const {x, y, blade} = stats.auto;
   await probe.move(x, y);
   await probe.sampled(5);
   if (blade) {
    await probe.rightClick(x, y);
    await probe.sampled(15);
    const fresh = (await state()).auto;
    await probe.click(fresh?.kind === 'sd-slash' ? fresh.x : x, fresh?.kind === 'sd-slash' ? fresh.y : y);
   } else await probe.click(x, y);
  }
  else await probe.sampled(4);
 };
 const verifyOpening = async () => {
  await probe.tap('F7');
  await probe.until(async () => (await state()).node?.startsWith('rev:P01:'), 'revised opening', 90000);
  await probe.capture('revised-opening');
  checks.push({kind: 'prologue-start', node: (await state()).node});
  await probe.tap('F2');
  await probe.key('Control', true);
  await probe.until(async () => (await state()).node === 'rev:P02:walk-to-gate', 'first exploration', 180000);
  await probe.key('Control', false);
  const inspected = new Set();
  const first = await probe.until(async () => {
   const s = await state();
   if (s.node === 'rev:P02:choice') return s;
   if (s.node?.startsWith('rev:P02:inspect:')) inspected.add(s.node);
   await advance(s);
   return false;
  }, 'authored opening choice after both inspections', 90000);
  assert.equal(inspected.size, 2);
  assert.equal(first.mode, 'menu');
  await probe.tap('ArrowDown');
  await probe.tap('Enter');
  const consequence = await probe.until(async () => {
   const s = await state();
   return s.node === 'rev:P02:response:B' ? s : false;
  }, 'second prologue branch and consequence');
  checks.push({kind: 'prologue-choice', inspections: [...inspected], before: first.node, after: consequence.node});
 };
 if (normalEntry) {
  const readSave = async (dir,slot) => JSON.parse(await fs.readFile(path.join(saveDirectory(dir),'rewrite-v5-'+slot+'.json'),'utf8'));
  const saveThroughPad = async () => {
   await probe.tap('Tab');
   assert.equal((await state()).mode,'pad');
   await probe.click(1047,480);
   if((await state()).padPage!==5){await probe.tap('Backspace');await probe.click(1047,480);}
   await padSystemAction(state,probe.tap,'save');
  };
  if(normalArchive){
   const index=await readSave(run,'yumeno-v4-chapter-index');
   assert(index.entries.some(entry=>entry.id==='1:0'),'Actual chapter one archive is required');
   for(const key of ['s','s','Enter','d','Enter','Enter'])await probe.tap(key);
   await probe.until(async()=>(await state()).difficulty?.open,'chapter replay difficulty');
   for(const key of ['ArrowDown','ArrowDown','Enter'])await probe.tap(key);
   await probe.until(async()=>{
    const s=await state();
    return s.mode==='story'&&s.chapter===1&&!s.scenes.loading;
   },'restored authored chapter archive',90000);
  }else{
  const hub = 'rev:P02:walk-to-gate';
  await probe.tap('c');
  assert.equal((await state()).mode, 'title', 'V4-only save must not enable V5 Continue');
  await probe.tap('Enter');
  await probe.until(async () => (await state()).difficulty?.open, 'normal new-game difficulty');
  await probe.tap('ArrowDown');
  await probe.tap('ArrowDown');
  assert.equal((await state()).difficulty.row, 2);
  await probe.tap('Enter');
  const card = await probe.until(async () => (await state()).mode === 'card', 'normal new-game chapter card');
  assert.equal(card && (await state()).node, 'rev:P01');
  await probe.tap('Enter');
  const first = await probe.until(async () => {
   const s = await state();
   return s.mode === 'story' && !s.scenes.loading && s.node?.startsWith('rev:P01:') ? s : false;
  }, 'normal prologue dialogue', 90000);
  await probe.capture('normal-prologue');
  await probe.tap('F2');
  await probe.until(async () => (await state()).options?.values?.readOnlySkip === false, 'QA unread skip enabled', 10000);
  await probe.key('Control', true);
  await probe.until(async () => (await state()).node === hub, 'normal prologue exploration', 180000);
  await probe.key('Control', false);
  await probe.until(async () => {
   const s = await state();
   return s.mode === 'explore' && s.world?.active && !s.scenes.loading;
  }, 'loaded normal prologue park');
  await probe.key('ArrowRight', true);
  await probe.sampled(8);
  await probe.key('ArrowRight', false);
  const position = (await state()).world;
  await saveThroughPad();
  await probe.capture('normal-save');
  const files = saveDirectory(run);
  const head = await readSave(run,'yumeno-progress-v4');
  const manual = await readSave(run,'yumeno-manual-v1-1');
  const archive = await readSave(run,'yumeno-v4-chapter-index');
  assert.equal(head.campaignRevision, 'rewrite-v5');
  assert.equal(manual.campaignRevision, head.campaignRevision);
  assert.equal(head.node, hub);
  assert.equal(manual.node, hub);
  assert.notEqual(manual.snapshot, head.snapshot);
  assert(head.readParts > 0 && head.logParts > 0);
  assert(archive.entries.some(entry => entry.id === 'P:0' && entry.node === 'rev:P01'));
  assert.equal(await fs.readFile(path.join(files, legacyName), 'utf8'), legacy);
  await probe.close();
  probe = null;
  const restarted = path.join(work, 'restart');
  await fs.mkdir(path.join(restarted, 'State'), {recursive:true});
  await fs.cp(files, saveDirectory(restarted), {recursive:true,errorOnExist:true,force:false});
  probe = await open(restarted);
  await probe.tap('c');
  const resumed = await probe.until(async () => {
   const s = await state();
   return s.node === hub && s.mode === 'explore' && s.world?.active && !s.scenes.loading ? s : false;
  }, 'normal Continue in fresh process', 90000);
  for (const key of ['space','position','yaw','pitch']) assert.deepEqual(resumed.world[key], position[key], key);
  await probe.capture('normal-continue');
  const next = await probe.until(async () => {
   const s = await state();
   if (s.node?.startsWith('rev:P02:inspect:')) return s;
   await advance(s);
   return false;
  }, 'resumed investigation responds to normal input', 60000);
  checks.push({kind:'normal-new-save-restart',first:first.node,saved:head.node,resumed:resumed.node,next:next.node,
   space:resumed.world.space,readParts:head.readParts,logParts:head.logParts,oldSaveUnchanged:true});
  }
  await probe.tap('F2');
  await probe.until(async () => (await state()).options?.values?.readOnlySkip === false, 'restart unread skip enabled', 10000);
  const meeting = 'rev:01-F02:visit';
  let fast = false;
  let chapterCard = false;
  try {
   await probe.until(async () => {
    const s=await state();
    if(s.node===meeting&&s.mode==='explore'&&!s.scenes.loading)return s;
    if(s.mode==='card'&&s.chapter===1)chapterCard=true;
    const skip=s.mode==='story'&&s.v4Kind==='say'&&!s.scenes.loading;
    if(skip!==fast){await probe.key('Control',skip);fast=skip;}
    if(!skip)await advance(s);
    return false;
   },'normal prologue to chapter one physical free time',540000);
  } finally {
   if(fast)await probe.key('Control',false);
  }
  if(!normalArchive)assert(chapterCard,'The normal chapter transition must show the Chapter 1 card');
  const location=await state();
  assert.equal(location.world.space,'hotel_lobby');
  assert.equal(location.world.position[1],Math.fround(1.55),'Free-time entry must use the lobby floor');
  assert.equal(location.giftV4.role,'freetime');
  await probe.sampled(30);
  await probe.capture('normal-free-time-world');
  await probe.tap('Tab');
  await probe.click(150,480);
  assert.equal((await state()).padPage,0);
  for(const key of ['Space','d','d'])await probe.tap(key);
  await probe.sampled(20);
  await probe.capture('normal-free-time-map');
  const mapUI=JSON.parse(await fs.readFile(path.join(probe.work,'normal-free-time-map.ui.json'),'utf8'));
  const mapNode=(widget,id)=>mapUI.widgets.find(row=>row.instance===widget).nodes.find(node=>node.id===id);
  assert.equal(mapNode('padmap','MpCharDim2').properties.visible,false,'The available encounter is located');
  assert.equal(mapNode('padmapatlas','MaPerson2').properties.visible,true);
  assert(mapNode('padmapatlas','MaName').properties.text.includes('소라'));
  assert(mapNode('padmap','MpHint').properties.text.includes('Enter 이동'));
  await probe.tap('Tab');
  const entered=await probe.until(async () => {
   const s=await state();
   if(s.mode==='menu'&&s.node===meeting&&s.giftV4?.present?.includes('sora'))return s;
   await advance(s);
   return false;
  },'normal physical encounter opens character confirmation',60000);
  await probe.tap('Enter');
  const met=await probe.until(async () => {
   const s=await state();
   return s.mode==='story'&&s.node?.startsWith('rev:01-F02:')&&s.node!==meeting?s:false;
  },'physical encounter follows authored optional dialogue',60000);
  await probe.sampled(24);
  await probe.capture('normal-encounter-dialogue');
  checks.push({kind:'normal-chapter-transition-and-world-encounter',entry:meeting,
   room:location.world.space,confirmedActor:entered.giftV4.present[0],dialogue:met.node});
  if(normalArchive){
   await probe.until(async()=>{
    const s=await state();
    if(s.mode==='story'&&s.node?.startsWith('rev:01-D01c:'))return s;
    await advance(s);return false;
   },'free time completes before the next scheduled scene',120000);
   await saveThroughPad();
   const progress=await readSave(run,'yumeno-progress-v4');
   assert.deepEqual(progress.growth.completed,['sora:1']);
   assert.deepEqual(progress.growth.fpClaims,['sora:1']);
   assert.equal(progress.flags['rev:encounter:01-F02'],true);
   assert(progress.bonds.sora>0&&progress.growth.fp>0);
   assert.equal(await fs.readFile(path.join(saveDirectory(run),legacyName),'utf8'),legacy);
   await probe.tap('Backspace');
   await probe.click(680,480);
   if((await state()).padPage!==3){await probe.tap('Backspace');await probe.click(680,480);}
   for(const key of ['d','d','s'])await probe.tap(key);
   assert.equal((await state()).padReportActor,'sora');
   assert.equal((await state()).padReportPage,1);
   await probe.sampled(20);
   await probe.capture('normal-encounter-memo');
   const memoUI=JSON.parse(await fs.readFile(path.join(run,'normal-encounter-memo.ui.json'),'utf8'));
   const memo=memoUI.widgets.find(widget=>widget.instance==='padreport').nodes.find(node=>node.id==='PrMemo').properties.text;
   assert(memo.includes('소라'));
   assert(memo.includes('「'),'A completed revised encounter must show actually read dialogue');
   checks.push({kind:'completed-encounter-growth',encounter:progress.growth.completed[0],
    fp:progress.growth.fp,bond:progress.bonds.sora,sourceArchive:normalArchive});
  }
 } else {
 if (mineOnly || paperMine || paperSequence || theatreRing) {
  await probe.tap(theatreRing ? 'F23' : paperSequence ? 'F1' : paperMine ? 'F4' : 'F12');
  if (!paperSequence) {
  const mineInput = async auto => {
   if (auto?.kind === 'move') await probe.rightClick(auto.x, auto.y);
   else await advance({auto});
  };
  const [id, followup, wrongItems] = theatreRing
   ? ['T2-MM-REV01', 'rev:02:ring-physical-match', ['theatre-apron-buckle', 'theatre-washer', 'theatre-tag-clip']]
   : paperMine
    ? ['T1-MM-REV02', 'rev:01:torn-report-match', ['stored-number', 'medical-strip', 'check-cover']]
    : ['T1-MM-REV01', 'rev:01:door-comparison-record', ['latch', 'front-plate', 'frost']];
  await probe.until(async () => {
   const s = await state();
   if (s.taskId === id && s.mineV4?.wrongInputs && !s.taskQueue && s.taskInputArmed && !s.scenes.loading) return true;
   await advance(s);return false;
  }, 'revised mine checkpoint', 120000);
  const errors = [];
  for (const option of wrongItems) {
   const initial = (await state()).trialHp;
   const wrong = await probe.until(async () => {
    const s = await state();
    if (s.taskQueue && s.queueAfter === 'resume' && s.trialHp < initial) return s;
    await mineInput(s.mineV4?.wrongInputs?.[option]);return false;
   }, `reveal and submit ${option}`, 100000);
   errors.push({option, hpBefore: initial, hpAfter: wrong.trialHp, queue: wrong.queueAfter});
   await probe.until(async () => {
    const s = await state();if (!s.taskQueue) return true;
    await advance(s);return false;
   }, 'return to mine after wrong evidence');
  }
  await probe.until(async () => {
   const s = await state();
   if (s.lastTaskOutcome?.taskId === id) return true;
   if (s.taskQueue) await advance(s);
   else await mineInput(s.auto);
   return false;
  }, 'mine accepts the fully exposed correct comparison', 150000);
  await probe.until(async () => {
   const s = await state();
   if (s.node === followup && !s.scenes.loading) return true;
   await advance(s);return false;
  }, 'show the authored follow-up comparison');
  await probe.capture('revised-mine-comparison');
  checks.push({kind: 'revised-mine', errors, success: (await state()).lastTaskOutcome, followup});
  }
  if (paperMine || paperSequence) {
   const taskId = 'T1-QA-REV03';
   const reached = new Set();
   const outcome = await probe.until(async () => {
    const s = await state();
    if (s.lastTaskOutcome?.taskId === taskId) return s.lastTaskOutcome;
    if (s.taskId === taskId && s.taskQueue && s.queueAfter === 'resume') reached.add(s.stage.selection);
    if (s.taskId === taskId && !s.taskQueue && s.taskInputArmed && !reached.size) await probe.tap('Enter');
    else await advance(s);
    return false;
   }, 'report chronology rejects the first claim and accepts the supported timing', 120000);
   assert(reached.size > 0);
   checks.push({kind: 'report-timing', wrong: [...reached], outcome});
   const anagram = await probe.until(async () => {
    const s = await state();
    if (s.lastTaskOutcome?.taskId === 'T1-AN-REV01') return s.lastTaskOutcome;
    if (s.scenes.loading || (s.taskId === 'T1-AN-REV01' && !s.taskInputArmed && !s.taskQueue)) await probe.sampled(4);
    else await advance(s);
    return false;
   }, 'select the serial number characters in order', 150000);
   await probe.until(async () => (await state()).node === 'rev:01:number-comparison', 'reveal the finished printout comparison');
   checks.push({kind: 'report-anagram', outcome: anagram});
  } else if (theatreRing) {
   await probe.until(async () => {
    const s = await state();if(s.taskId === 'T2-NS-REV03' && !s.scenes.loading) return true;
    await advance(s);return false;
   }, 'ring comparison returns to the seal-photo argument', 100000);
  } else {
  await probe.until(async () => {
   const s = await state();if(s.taskId === 'T1-SP-REV01' && !s.scenes.loading) return true;
   await advance(s);return false;
  }, 'comparison dialogue advances into witness sightline', 150000);
  }
 } else if (secondOpening) {
  await probe.tap('F9');
  await probe.until(async () => (await state()).node?.startsWith('rev:02-D01:'),'chapter two opening',90000);
  await probe.tap('F2');
  await probe.key('Control',true);
  const seen=new Set(), choices=new Set();
  await probe.until(async () => {
   const s=await state();
   if(s.node)seen.add(s.node);
   if(s.mode==='explore'&&s.node==='rev:02:investigate')return true;
   if(s.mode==='menu'&&!choices.has(s.node)&&s.choice?.pending<0&&
      ['rev:02-F01:locker-choice','rev:02-F01:ring-choice'].includes(s.node)){
    choices.add(s.node);
    await probe.tap('ArrowDown');
    await probe.tap('Enter');
    return false;
   }
   if(s.mode==='story'&&s.v4Kind==='say')await probe.sampled(2);
   else await advance(s);
   return false;
  },'day scenes, optional workshop choice, discovery and investigation',360000);
  await probe.key('Control',false);
  for(const name of ['rev:02:free-time','rev:02-F01:leave-ring'])assert(seen.has(name),name);
  assert([...seen].some(node=>node.startsWith('rev:02-D08:')));
  assert.equal(choices.size,2);
  checks.push({kind:'chapter-two-opening',choices:[...choices],observed:seen.size});
 } else if(thirdArchive){
  await probe.tap('F10');await probe.tap('F2');
  const seen=new Set();
  await probe.until(async()=>{
   const s=await state();if(s.node)seen.add(s.node);
   if(s.mode==='title'&&seen.has('rev:03:record:V5-3:archive-pieces'))return true;
   await advance(s);return false;
  },'all archive fragment views, normal evidence grant and return',180000);
  for(let i=0;i<3;i++)assert(seen.has('rev:03:archive-fragment-boundaries:'+i));
  checks.push({kind:'chapter-three-archive',views:3,record:'v4:V5-3:archive-pieces',observed:seen.size});
 } else if (thirdOpening) {
  await probe.tap('F14');
  await probe.until(async () => (await state()).node?.startsWith('rev:03-D01:'), 'chapter-three daily opening');
  await probe.tap('F2');
  await probe.key('Control', true);
  await probe.until(async () => {
   const s = await state();
   if (s.node === 'rev:03-D01j:choice' && s.mode === 'menu') return true;
   if (s.mode === 'story' && s.v4Kind === 'say') await probe.sampled(2);
   else await advance(s);
   return false;
  }, 'authored card table choice', 120000);
  await probe.key('Control', false);
  await probe.tap('ArrowDown');
  await probe.tap('ArrowDown');
  await probe.tap('Enter');
  const seen = new Set();
  let fastDaily = true;
  await probe.key('Control', true);
  await probe.until(async () => {
   const s = await state();
   if (s.node === 'rev:03:incident' || s.node?.startsWith('rev:03-D04:')) return true;
   if (s.node) seen.add(s.node);
   if(s.node==='rev:03-D0A:choice'&&fastDaily){await probe.key('Control',false);fastDaily=false;}
   if (fastDaily && s.mode === 'story' && s.v4Kind === 'say') await probe.sampled(2);
   else await advance(s);
   return false;
  }, 'card decision and experiment advance into the authored incident', 240000);
  await probe.key('Control', false);
  for (const prefix of ['rev:03-D01e:', 'rev:03-D02:', 'rev:03-D03:'])
   assert([...seen].some(node => node.startsWith(prefix)), prefix);
  checks.push({kind:'chapter-three-route-observations',nodes:[...seen]});
  for(const node of ['rev:03-D0A:choice','rev:03-D01t:choice',
                    'rev:03:write-after-blindfold','rev:03:unopened-handover','rev:03:unreturned-body'])
   assert(seen.has(node),node);
  assert([...seen].some(node=>node.startsWith('rev:03-D0A:choice:'+(thirdNoDemo?'1':'0')+':')));
  const nodeDir = path.join(previewContent, root, 'nodes');
  const pages = await Promise.all((await fs.readdir(nodeDir)).map(async name =>
   JSON.parse(await fs.readFile(path.join(nodeDir, name), 'utf8')).nodes));
  const callback = pages.find(page => page['rev:03:card-game-callback'])['rev:03:card-game-callback'];
  for (const {equals, to} of callback.cases) {
   const segment = to.slice(0, to.lastIndexOf(':', to.lastIndexOf(':') - 1) + 1);
   assert.equal([...seen].some(node => node.startsWith(segment)), equals === 'C', 'callback must match the chosen card branch');
  }
  checks.push({kind: 'chapter-three-opening', cardChoice: 'C',hypnosisChoice:thirdNoDemo?'B':'A',observedNodes: seen.size});
 } else if (comicOnly || voteOnly || theatreComic || theatreVote || thirdBook || fourthBook || fifthComic || sixthComic || sixthEnding) {
  const secondBook = theatreComic || theatreVote;
  const comicChapter = sixthComic||sixthEnding ? 6 : fifthComic ? 5 : fourthBook ? 4 : thirdBook ? 3 : secondBook ? 2 : 1;
  const holes = comicChapter===1||comicChapter>=4 ? 15 : 16;
  const gateIndex = comicChapter>=5 ? 8 : comicChapter===1 ? 7 : 6;
  const gateCount = thirdBook ? 3 : 2;
  const pageCount = thirdBook ? 16 : 15;
  if (sixthEnding) await probe.tap('F17');
  else if (voteOnly || theatreVote || thirdVote || fourthVote) await probe.tap(fourthVote?'F15':thirdVote ? 'F10' : theatreVote ? 'F19' : 'F24');
  else {
  const comic = 'T'+comicChapter+'-CM-REV01';
  await probe.tap(sixthComic?'F17':fifthComic?'F16':fourthComic?'F15':thirdComic ? 'F10' : theatreComic ? 'F20' : 'F21');
  const opened = await probe.until(async () => {
   const s = await state();
   if (s.taskId === comic && s.comicV4 && s.auto?.kind === 'click') return s;
   await advance(s);
   return false;
  }, 'authored comic book loaded', 90000);
  assert.equal(opened.comicV4.pageCount,pageCount);
  assert.equal(opened.comicV4.stockCount,comicChapter===1 ? 17 : comicChapter>=4 ? 15 : 16);
  assert.equal(opened.comicV4.readyAnswers, 6);
  assert.equal(opened.comicV4.remaining[gateIndex],gateCount);
  await probe.capture('revised-comic-opening');
  const place = async hole => {
   const s = await state();
   const [x,y,w,h] = s.comicV4.slotRects[hole];
   await probe.click(x+w/2,y+h/2);
  };
  await probe.tap('d');
  await probe.tap('d');
  const decoy = await state();
  assert.equal(decoy.comicV4.selectedOrigin,comicChapter===1 ? -1 : 2);
  await place(0);
  const wrong = await probe.until(async () => {
   const s = await state();
   return s.trialHp < opened.trialHp && !s.comicV4.feedback && s;
  }, 'decoy lowers HP without filling a hole', 12000);
  assert.deepEqual(wrong.comicV4.filledSlots, []);
  await probe.tap('x');
  assert.equal((await state()).comicV4.stockPage, 1);
  await probe.capture('revised-comic-second-stock');
  await probe.tap('z');
  assert.equal((await state()).comicV4.stockPage, 0);
  if (comicChapter===1) await probe.tap('d');
  await probe.tap('d');
  const unrelated = await state();
  assert.equal(unrelated.comicV4.selectedOrigin, 3);
  for (let i=0;i<3;i++) {
   await probe.tap('e');
   await probe.until(async () => !(await state()).comicV4.pageTurning,'page turn settled',5000);
  }
  await place(3);
  const afterUnrelated = await probe.until(async () => {
   const s=await state();
   return s.comicV4.filledSlots.includes(3) && !s.comicV4.feedback && s;
  },'out-of-order panel places without opening an unrelated gate',10000);
  assert.equal(afterUnrelated.comicV4.remaining[gateIndex],gateCount);
  const replay = new Set();
  let last = opened;
  await probe.until(async () => {
   const s = await state();
   if (s.lastTaskOutcome?.taskId === comic) return true;
   const c = s.comicV4;
   if (c) {
    if (c.replay && s.taskQueue && !replay.has(c.replayAct)) {
     replay.add(c.replayAct);
     if (c.replayAct === holes) await probe.capture('revised-comic-recap');
    }
    if (!c.replay) last = s;
   }
   await advance(s);
   return false;
  }, 'placed panels and complete narrated replay', 240000);
  assert.equal(last.comicV4.placed, holes);
  assert.deepEqual([...replay], Array.from({length:holes+1}, (_,i)=>i));
  checks.push({kind:'comic',chapter:comicChapter,pages:pageCount,holes,replay:replay.size,wrongRejected:true,stockPaging:true});
  }
  if(comicChapter===6){
   const seen=new Set(),done=new Set();let resultShown=false;
   const endingNodes=await readPreparedNodes(), endingShots=new Set();
   await probe.until(async()=>{
    const s=await state();
    if(s.mode==='title'&&seen.has('rev:06:support-choice'))return true;
    if(s.node)seen.add(s.node);
    if(normalRuntime&&endingNodes[s.node]?.trialResultAtEnd&&s.mode==='trial'){
     if(!resultShown){
      await probe.sampled(5);
      await probe.capture('revised-final-trial-result');
      const ui=JSON.parse(await fs.readFile(path.join(probe.work,'revised-final-trial-result.ui.json'),'utf8'));
      assert(ui.widgets.some(widget=>widget.instance==='trialresultv4'),'The actual result widget must be mounted');
      resultShown=true;
     }
     await probe.tap('Enter');return false;
    }
    const shot=endingNodes[s.node]?.shot?.image;
    if(shot?.includes('/ending-')&&!s.scenes.loading){
     const name=path.basename(shot,'.webp');
     if(!endingShots.has(name)){
      await probe.sampled(3);
      await probe.capture('revised-'+name);
      endingShots.add(name);
     }
    }
    if(s.mode==='menu'&&s.choice?.pending<0){
     if(s.node==='rev:06:control-choice'&&!done.has(s.node)){
      done.add(s.node);await probe.tap('ArrowDown');await probe.tap('Enter');return false;
     }
     if(sixthSupportEnds&&['rev:06:support-choice','rev:06:support-final-confirm'].includes(s.node)&&!done.has(s.node)){
      done.add(s.node);await probe.tap('ArrowDown');await probe.tap('Enter');return false;
     }
    }
    await advance(s);return false;
   },'reject premature support decision, then verify gate, response and chosen ending',300000);
   for(const node of ['control-choice:support','outside-contact','manual-verification','support-notice','support-choice'])
    assert(seen.has('rev:06:'+node),node);
   assert(seen.has('rev:06:support-'+(sixthSupportEnds?'final-confirm':'choice')));
   if(normalRuntime){
    assert(resultShown,'The installed campaign settles its final trial before returning to title');
    const head=JSON.parse(await fs.readFile(path.join(saveDirectory(run),'rewrite-v5-yumeno-progress-v4.json'),'utf8'));
    assert.equal(head.campaignRevision,'rewrite-v5');
    assert.equal(head.chapter,'6');
    assert(endingNodes[head.node]?.campaignNarrativeEnd);
    assert(head.trialResults.current.paid&&head.trialResults.current.complete);
    assert.equal(head.trialResults.current.chapter,head.chapter);
    assert.deepEqual(head.trialResults.best[head.chapter],head.trialResults.current);
    const records=head.trialResults.current.records.map(record=>record.id);
    if(sixthComic)assert(records.includes('T6-CM-REV01'),'The played comic must be in the saved ledger');
    checks.push({kind:'installed-ending-save',chapter:head.chapter,node:head.node,paid:true,records});
   }
   checks.push({kind:'closing-route',support:sixthSupportEnds?'ended':'held',nodes:[...seen],shots:[...endingShots],resultShown});
  }else{
  const vote = 'T'+comicChapter+'-VOTE-REV01';
  if(thirdBook||fifthComic){
   for(const who of (fifthComic?['satsuki','nana']:['ken','riku'])){
    const target=authoredTasks[vote].stage.candidates.indexOf(who);
    const variant=authoredTasks[vote].queues.wrongVariants.find(row=>row.optionIndex===target).script[0];
    await probe.until(async()=>{
     const s=await state();
     if(s.taskId!==vote||s.taskQueue||!['key','click'].includes(s.auto?.kind)){await advance(s);return false;}
     if(s.stage.selection===target){await probe.tap('Enter');return true;}
     await probe.tap(s.stage.selection%4!==target%4?'ArrowRight':'ArrowDown');
     return false;
    },'select a distinct authored wrong vote',90000);
    const reaction=await probe.until(async()=>{
     const s=await state();
     return s.taskId===vote&&s.taskQueue&&s.queueAfter==='resume'&&s;
    },'specific wrong-vote response',20000);
    assert.equal(reaction.speaker,variant.speaker);
    assert.equal(reaction.line,variant.text);
    checks.push({kind:'vote-wrong-response',who,speaker:reaction.speaker});
    await probe.until(async()=>{
     const s=await state();if(s.taskId===vote&&!s.taskQueue)return true;
     await advance(s);return false;
    },'return to the same vote board',20000);
   }
  }
  await probe.until(async () => {
   const s = await state();
   if (s.lastTaskOutcome?.taskId === vote) return true;
   if (s.taskId === vote && s.auto?.kind === 'wait' &&
       ['투표가 끝났네. 그럼 결과를 발표할게!', '과연 누가 검정으로 뽑혔을까? 그리고 그 선택은 맞았을까, 틀렸을까?'].includes(s.line)) await probe.tap('Enter');
   else await advance(s);
   return false;
  }, 'native voting and verdict', 120000);
  const shots = new Set();
  await probe.until(async () => {
   const s = await state();
   if (s.node?.startsWith('rev:0'+(comicChapter+1)+'-D01:')) return true;
   if (s.node?.startsWith('rev:0'+comicChapter+':verdict-') && !shots.has(s.node)) {
    shots.add(s.node);
    await probe.capture('revised-'+s.node.split(':').at(-1));
   }
   if (s.mode === 'trial' && s.auto?.kind === 'wait') await probe.tap('Enter');
   else await advance(s);
   return false;
  }, 'authored verdict, aftermath and chapter two', 250000);
  const expectedShots=Object.keys(await readPreparedNodes()).filter(id=>id.startsWith(`rev:0${comicChapter}:verdict-`)).length;
  if(!thirdVote)assert.equal(expectedShots,4,'A normal comic route requires all four authored verdict shots');
  assert.equal(shots.size,expectedShots);
  checks.push({kind:'vote-to-next-chapter',chapter:comicChapter,taskId:vote,shots:shots.size});
  }
 } else if(firstDaily||secondDaily||thirdDaily||fourthDaily||fifthDaily||sixthDaily){
  const chapter=firstDaily?1:secondDaily?2:thirdDaily?3:fourthDaily?4:fifthDaily?5:6;
  const dailyNodes=await readPreparedNodes();
  await probe.tap(firstDaily?'F8':secondDaily?'F9':thirdDaily?'F14':'F'+(chapter+11));
  await probe.until(async()=>{
   const s=await state();return s.chapter===chapter&&s.mode!=='title'&&!s.scenes.loading;
  },'revised chapter is ready for input',90000);
  await probe.tap('F2');
  await probe.until(async()=>!(await state()).options?.values?.readOnlySkip,'allow skipping unread lines in QA',10000);
  const seen=new Set();
  const recallLocations=new Set(['01-D03k','02-D02c','03-D01c','05-D02b']);
  const nearRecall=id=>{
   const pending=[{id,depth:0}],visited=new Set();
   while(pending.length){
    const {id,depth}=pending.pop();
    if(visited.has(id))continue;
    visited.add(id);
    const node=dailyNodes[id];
    if(!node)continue;
    if(recallLocations.has(node.source?.location))return true;
    if(depth>=16||node.type==='menu'||node.type==='investigate')continue;
    for(const next of [node.next,node.default,...(node.cases||[]).map(item=>item.to)])
     if(next)pending.push({id:next,depth:depth+1});
   }
   return false;
  };
  let skipping=false;
  let skipNode='',skipChanged=Date.now();
  await probe.until(async()=>{
   const s=await state();
   if(s.node===(thirdDaily?'rev:03:first-investigation':'rev:0'+chapter+':investigate')){
    if(skipping){await probe.key('Control',false);skipping=false;}
    return true;
   }
   if(s.node)seen.add(s.node);
   const location=dailyNodes[s.node]?.source?.location;
   const sampledRecall=recallLocations.has(location)||nearRecall(s.node);
   const speech=s.mode==='story'&&s.v4Kind==='say'&&!s.scenes.loading&&!sampledRecall;
   if(speech!==skipping){await probe.key('Control',speech);skipping=speech;}
   if(s.node!==skipNode){skipNode=s.node;skipChanged=Date.now();}
   if(speech&&Date.now()-skipChanged>1000){await probe.key('Control',true);skipChanged=Date.now();}
   if(speech)await probe.sampled(2);else await advance(s);
   return false;
  },'play revised daily choices into investigation',chapter<=4?600000:360000);
  checks.push({kind:'revised-daily',chapter,alternate:dailyAlternate,nodes:[...seen]});
  const required=chapter===1?['01-D00','01-D01','01-D01a','01-D01e','01-D01g','01-D01b','01-D01d','01-D01c',
    '01-D01f','01-D01j','01-D01h','01-D01i','01-D02','01-D02g','01-D02b','01-D02h','01-D02i','01-D02a',
    '01-D02e','01-D02c','01-D02j','01-D02d','01-D02m','01-D02f','01-D02k','01-D02l','01-D02n','01-D03k',
    '01-D02o','01-D03','01-D03m','01-D03j','01-D03i','01-D03f','01-D03d','01-D03e','01-D03a','01-D03b',
    '01-D03h','01-D03l','01-D04']:
   chapter===2?['02-D01','02-D02','02-D02f','02-D02a','02-D02h','02-D02b','02-D02c','02-D02d','02-D02e',
    '02-D02i','02-D02g','02-D03','02-D03a','02-D03b','02-D03c','02-D03d','02-D03e','02-D03f',
    '02-D04','02-D04r','02-D04a','02-D04b','02-D04c','02-D04d','02-D04e','02-D04h','02-D04g','02-D04i',
    '02-D04l','02-D04t','02-D04f','02-D04v','02-D04x','02-D04j','02-D04m','02-D04k','02-D04s','02-D04u',
    '02-D04w','02-D05','02-D05a','02-D05b','02-D05c','02-D06a','02-D06','02-D07','02-D08']:
   chapter===3?['03-D01','03-D01i','03-D01a','03-D01g','03-D01b','03-D01c','03-D01d','03-D01r','03-D01j',
    '03-D01l','03-D01e','03-D01u','03-D0A','03-D01w','03-D01f','03-D01h','03-D01k','03-D01m','03-D01o',
    '03-D0C','03-D01p','03-D01n','03-D01q','03-D01s','03-D01y','03-D01z','03-D0B','03-D0E','03-D01t',
    '03-D0F','03-D01v','03-D0D','03-D01x','03-D02','03-D03','03-D04']:
   chapter===4?['04-D00','04-D00a','04-D00e','04-D00h','04-D00i','04-D00m','04-D00l','04-D00g','04-D00b',
    '04-D00j','04-D00c','04-D00n','04-D00d','04-D00o','04-D00f','04-D00k','04-D00r','04-D00p','04-D00q',
    '04-D00s','04-D01','04-D01a','04-D01d','04-D01b','04-D01e','04-D01i','04-D01f','04-D01k','04-D01j',
    '04-D01n','04-D01c','04-D01g','04-D01h','04-D01m','04-D01l','04-D01o','04-D02','04-D03']:
   chapter===5?['05-D01b','05-D01c','05-D01a','05-D02e','05-D02d','05-D02b','05-D02n','05-D02f',
    '05-D02g','05-D02i','05-D02j','05-D02h','05-D02l','05-D02k','05-D02m','05-D02o','05-D02q','05-D02p',
    '05-D03b','05-D03c','05-D03d','05-D03e','05-D03f','05-D03g','05-D03h']:
   ['06-D01b','06-D01a','06-D01c','06-D01d','06-D01e','06-D02a','06-D02b','06-D02c','06-D03c','06-D03a',
    '06-D03b','06-D03e','06-D03d','06-D03f','06-D03g'];
  for(const location of required)assert([...seen].some(node=>node.startsWith('rev:'+location+':')),location);
  if(chapter===1){
   const nodes=await readPreparedNodes();
   assert.equal(seen.has('rev:01-F08:visit'),!dailyAlternate,'The second meeting requires the first');
   assert.equal(seen.has('rev:01-F01:choice'),!dailyAlternate);
   const memory=nodes['rev:01-D03k:cushion-memory'];
   const expected=memory.cases.find(item=>item.equals===(dailyAlternate?'C':'A')).to;
   assert(seen.has(expected),'The cushion callback must match the chosen user');
   for(const other of memory.cases.filter(item=>item.to!==expected))
    assert(!seen.has(other.to),'Only the chosen cushion user answers');
  }
  if(chapter===2){
   assert.equal(seen.has('rev:02-F04:visit'),secondPriorMeeting);
   assert.equal(seen.has('rev:02-F05:visit'),!dailyAlternate);
   const nodes=await readPreparedNodes();
   const texts=[...seen].filter(id=>nodes[id]?.source?.location==='02-D02c').map(id=>nodes[id]?.text);
   assert(!texts.includes(dailyAlternate?'일찍 왔네. 우수 직원.':'미오, 이거 두 개 다 먹어도 돼?'));
   const supper=[...seen].findIndex(id=>id.startsWith('rev:02-D04l:'));
   const afternoon=[...seen].findIndex(id=>id.startsWith('rev:02-D04b:'));
   assert(afternoon>=0&&supper>afternoon,'The afternoon meeting precedes its supper recall');
  }
  if(chapter===3){
   const nodes=await readPreparedNodes();
   const texts=[...seen].filter(id=>nodes[id]?.source?.location==='03-D01c').map(id=>nodes[id]?.text);
   assert(!texts.includes(dailyAlternate?'아까는 안 산다고 하고 금방 나갔잖아.':'나는 아까 네가 웃었을 때 조금 좋았어.'));
   assert(!texts.includes('같이 나가자고 했을 때 미오 혼자 남았잖아.'));
  }
  if(chapter===5){
   for(const key of ['rev:05-F02:choice','rev:05-D03a:choice'])assert(seen.has(key),key);
   const nodes=await readPreparedNodes();
   const heard=text=>[...seen].some(id=>nodes[id]?.text===text);
   assert.equal(heard('옆에 뭘 더 하셔야 되는지 제가 생각해 뒀어요. 여기에는 안 적었어요.'),!dailyAlternate);
   assert.equal(heard('답을 쓰라고 미리 놓아 둔 것은 아니에요. 제가 필요할 줄 알고 가져온 거고요.'),false);
   assert.equal(seen.has('rev:05-F05:visit'),!dailyAlternate,'Follow-up requires the earlier meeting');
   assert.equal(seen.has('rev:05-F04:choice'),dailyAlternate);
   assert.equal(seen.has('rev:05-F03:choice'),!dailyAlternate);
  }
 } else if (prologueOnly) {
  await verifyOpening();
  await probe.key('Control', true);
  const visited = new Set();
  const arrived = await probe.until(async () => {
   const s = await state();
   if (s.node?.startsWith('rev:01-D01:')) return s;
   if (s.node) visited.add(s.node);
   if (s.mode === 'story' && s.v4Kind === 'say') await probe.sampled(2);
   else await advance(s);
   return false;
  }, 'revised prologue advances into revised chapter one', 270000);
  await probe.key('Control', false);
  assert([...visited].some(node => node.startsWith('rev:P08:')));
  checks.push({kind: 'prologue-to-chapter-one', node: arrived.node, visited: visited.size});
 } else {
 if (thirdLater) {
  await probe.tap('F10');
 } else if(fourthFocus){
  await probe.tap('F15');
 } else if(fifthFocus){
  await probe.tap('F16');
 } else if(sixthFocus){
  await probe.tap('F17');
 } else if (thirdOnly) {
  await probe.tap('F10');
  await probe.until(async () => (await state()).node?.startsWith('rev:03-D04:'), 'chapter three incident', 90000);
  await probe.tap('F2');
  const visited = new Set();
  const records = [];
  const retried = new Set();
  const corrected = new Set();
  const nativeNodes=await readPreparedNodes();
  const nativeNode=id=>nativeNodes[id];
  const expectedRecords=new Set(['rev:03:first-investigation','rev:03:second-investigation']
   .flatMap(id=>nativeNode(id).spots.map(spot=>'rev:03:record:'+spot.id)));
  await probe.until(async () => {
   const s = await state();
   if (s.node === 'rev:03:first-investigation' && !visited.has(s.node)) await probe.capture('chapter-three-first-investigation');
   if (s.node === 'rev:03:second-investigation' && !visited.has(s.node)) await probe.capture('chapter-three-second-investigation');
   if (s.node?.startsWith('rev:03:record:') && !visited.has(s.node)) records.push(s.node);
   if (s.node) visited.add(s.node);
   if (s.taskId === 'T3-NS-REV01') return [...expectedRecords].every(id=>records.includes(id));
   if (/^rev:03:classify:[02]$/.test(s.node) && s.choice?.pending < 0) {
    if (!retried.has(s.node)) {
     await probe.tap('Enter');
     await probe.until(async () => (await state()).node === s.node + ':retry', 'separate an unsupported interpretation');
     retried.add(s.node);
    } else if (!corrected.has(s.node)) {
     await probe.tap('ArrowDown');
     await probe.tap('Enter');
     corrected.add(s.node);
    }
    return false;
   }
   await advance(s);
   return false;
  }, 'both ordered investigations and all required records', 600000);
  for (const node of ['rev:03:first-announcement', 'rev:03:first-investigation', 'rev:03:living-observation-choice',
                     'rev:03:second-impact', 'rev:03:second-announcement', 'rev:03:second-investigation']) assert(visited.has(node), node);
  assert(records.slice(0, 4).every(node => /reflection|index|loan|first-injury/.test(node)));
  assert(records.slice(4).every(node => /movement|blade-stop|second-status|cloth-handover|written-order|condition|archive-pieces/.test(node)));
  assert(visited.has('rev:03-I03e:choice'));
  assert(visited.has('rev:03:notebook-conditions'));
  assert.equal(corrected.size, 2);
  assert(visited.has('rev:03:classify:1'));
  assert(visited.has('rev:03:comparison-record'));
  checks.push({kind: 'ordered-investigations', records, classified: [...corrected]});
 } else if (lateChapter) {
  await probe.tap('F' + (lateChapter + 11));
  const chapter = '0' + lateChapter;
  const records = new Set();
  const phases = new Set();
  const chosen = new Set();
  await probe.tap('F2');
  await probe.until(async () => {
   const s = await state();
   if (s.taskId === `T${lateChapter}-NS-REV01`) return true;
   if (s.node?.startsWith(`rev:${chapter}:record:`)) records.add(s.node);
   if (s.node) phases.add(s.node);
   if (s.mode === 'menu' && s.choice?.pending < 0 && !chosen.has(s.node) &&
       ['rev:04:wait-option', 'rev:04:verify-exterior-end'].includes(s.node)) {
    chosen.add(s.node);
    await probe.tap('ArrowDown');
    await probe.tap('Enter');
    return false;
   }
   await advance(s);
   return false;
  }, 'reach the first courtroom task after authored investigation', 330000);
  const expected=(await readPreparedNodes())[`rev:${chapter}:investigate`].spots.map(spot=>`rev:${chapter}:record:`+spot.id);
  assert.deepEqual([...records].sort(),expected.sort());
  if (lateChapter === 4) for (const node of ['rev:04:wait-reply:B', 'rev:04:first-rescue-attempt', 'rev:04:rewind-to-rescue', 'rev:04:investigate']) assert(phases.has(node), node);
  if (lateChapter === 5) for (const node of ['rev:05:initial-stock', 'rev:05:marked-cup-observation', 'rev:05:investigate']) assert(phases.has(node), node);
  checks.push({kind: 'late-chapter-investigation', chapter: lateChapter, records: [...records]});
 } else if (theatreArguments) {
  await probe.tap('F23');
 } else if (theatreSighting) {
  await probe.tap('F22');
 } else if (theatreArmament) {
  await probe.tap('F21');
 } else if (theatrePhysical) {
  await probe.tap('F18');
 } else if (armamentOnly) {
  await probe.tap('F20');
 } else if (signatureOnly) {
  await probe.tap('F19');
 } else if (phoneOnly) {
  await probe.tap(phoneEvidence ? 'F22' : 'F18');
 } else if (secondLate) {
  await probe.tap('F13');
 } else if (rescueOnly) {
  await probe.tap('F3');
 } else if (paperOnly) {
  await probe.tap('F5');
 } else if (witnessBoundaries) {
  await probe.tap('F6');await probe.tap('F2');
 } else if (witnessOnly) {
  await probe.tap('F6');
  for (const taskId of ['T1-SP-REV01', 'T1-SP-REV02', 'T1-SP-REV03']) {
   const result = await probe.until(async () => {
    const s = await state();
    if (s.lastTaskOutcome?.taskId === taskId) return s.lastTaskOutcome;
    if (s.scenes.loading || (s.taskId === taskId && !s.taskInputArmed && !s.taskQueue)) await probe.sampled(4);
    else await advance(s);
    return false;
   }, `solve witness sightline ${taskId}`, 120000);
   checks.push({kind: 'witness-sightline', taskId, result});
  }
 } else if (laterOnly) {
  await probe.tap('F11');
  await probe.until(async () => {
   const s = await state();
   if (s.taskId === 'T1-NS-REV05' && s.mode === 'trial') return true;
   await advance(s);
   return false;
  }, 'later courtroom checkpoint', 120000);
  checks.push({kind: 'later-courtroom-checkpoint', node: (await state()).node});
 } else {
 if (secondOnly) {
  await probe.tap('F9');
  await probe.until(async () => (await state()).node?.startsWith('rev:02-D01:'), 'revised chapter two opening', 90000);
  await probe.capture('revised-chapter-two-opening');
  checks.push({kind: 'chapter-two-start', node: (await state()).node});
  await probe.tap('F2');
 } else {
 if (!firstOnly) await verifyOpening();
 await probe.tap('F8');
 if(firstInvestigation){
  await probe.until(async()=>{
   const s=await state();
   return s.chapter===1&&s.mode!=='title'&&!s.scenes.loading;
  },'chapter one investigation checkpoint',90000);
  checks.push({kind:'investigation-checkpoint',chapter:1,entry:'rev:01:application',evidenceInjected:false});
  await probe.tap('F2');
  await probe.until(async()=>!(await state()).options?.values?.readOnlySkip,'allow unread checkpoint dialogue in QA',10000);
 }else{
 if (firstOnly) {
  await probe.until(async () => (await state()).node?.startsWith('rev:01-D00:'), 'revised chapter one opening', 90000);
  checks.push({kind: 'chapter-one-start', node: (await state()).node});
  await probe.tap('F2');
 }
 await probe.until(async () => {
  const s = await state();
  if (s.node === 'rev:01:preview-entry') return true;
  await advance(s);
  return false;
 }, 'free-time choice entry', 150000);
 await probe.tap('Enter');
 const meetingStart = Date.now();
 while (Date.now() - meetingStart < 60000) {
  const s = await state();
  if (s.node === 'rev:01-F01:choice') break;
  await advance(s);
 }
 assert.equal((await state()).node, 'rev:01-F01:choice');
 await probe.tap('ArrowDown');
 await probe.tap('Enter');
 const reply = await probe.until(async () => (await state()).node === 'rev:01-F01:B:0', 'authored free-time response');
 assert(reply);
 const callbackStart = Date.now();
 while (Date.now() - callbackStart < 60000) {
  const s = await state();
  if (s.node === 'rev:01-F01:callback:B') break;
  await advance(s);
 }
 assert.equal((await state()).node, 'rev:01-F01:callback:B');
 checks.push({kind: 'free-time-choice', chosen: 'B', callback: (await state()).node});
 }
 }
 const chapter = secondOnly ? '02' : '01';
 const investigate = `rev:${chapter}:investigate`;
 const firstTask = secondOnly ? 'T2-QA-REV01' : 'T1-NS-REV01';
 const departure = Date.now();
 let application = false;
 const dailyChoices = new Set();
 while (Date.now() - departure < (firstInvestigation?180000:90000)) {
  const s = await state();
  if (s.node === investigate) break;
  if (s.node === 'rev:01:application') application = true;
  if (['rev:01-D03:choice', 'rev:01-D04:choice'].includes(s.node) && s.choice?.pending < 0 && !dailyChoices.has(s.node)) {
   dailyChoices.add(s.node);
   await probe.tap('ArrowDown');
   await probe.tap('Enter');
   continue;
  }
  if(firstInvestigation&&s.mode==='story'&&s.v4Kind==='say'&&!s.scenes.loading){
   await probe.key('Control',true);await probe.sampled(2);
  }else{
   if(firstInvestigation)await probe.key('Control',false);
   await advance(s);
  }
 }
 if(firstInvestigation)await probe.key('Control',false);
 if (!secondOnly&&!firstInvestigation) {
  assert.equal(dailyChoices.size, 2, 'The document and discovery choices must both be reached');
  assert(application, 'The signed application must be recorded during daily life');
  checks.push({kind: 'daily-decisions', choices: [...dailyChoices], application});
 }
 await probe.until(async () => {
  const s = await state();
  return s.node === investigate && s.mode === 'explore' && !s.scenes.loading;
 }, 'revised investigation entry', 90000);
 await probe.capture('revised-investigation');
 await probe.tap('F2');
 const start = Date.now();
 const acquired = new Set();
 let triedWrongCorner = false;
 let revisitedCorner = false;
 let matchedSeal = false;
 while (Date.now() - start < 240000) {
  const stats = await state();
  if (stats.node?.startsWith(`rev:${chapter}:record:`)) acquired.add(stats.node);
  if (stats.taskId === firstTask && stats.mode === 'trial' && !stats.taskQueue) break;
  if (stats.node === 'rev:02:seal-overlay' && stats.choice?.pending < 0) {
   if (!matchedSeal) {
    await probe.tap('Enter');
    await probe.until(async () => (await state()).node === 'rev:02:seal-overlay:number','matching numbers do not prove a continuous seal');
    matchedSeal = true;
   } else {
    if (stats.choice.hover !== 1) await probe.tap('ArrowDown');
    await probe.tap('Enter');
   }
   continue;
  }
  if (stats.node === 'rev:01:report-comparison' && stats.choice?.pending < 0) {
   if (!triedWrongCorner) {
    await probe.tap('Enter');
    await probe.until(async () => (await state()).node === 'rev:01:report-wrong-corner', 'intact corner cannot match');
    triedWrongCorner = true;
   } else if (!revisitedCorner) {
    await probe.tap('ArrowDown');
    await probe.tap('Enter');
    revisitedCorner = true;
   }
   continue;
  }
  await advance(stats);
 }
 const trial = await state();
 const evidenceCount=Object.keys(await readPreparedNodes()).filter(id=>id.startsWith(`rev:${chapter}:record:`)).length;
 assert.equal(acquired.size,evidenceCount);
 if (secondOnly) {
  assert(matchedSeal);
  const order = [...acquired];
  const key = order.indexOf('rev:02:record:v4:E203');
  for (const sight of ['rev:02:record:v4:E202', 'rev:02:record:v4:E204']) assert(order.indexOf(sight) < key);
  for (const [before,after] of [[201,208],[206,207],[206,209],[208,209],[210,211]]) {
   assert(order.indexOf('rev:02:record:v4:E'+before)<order.indexOf('rev:02:record:v4:E'+after));
  }
 }
 if (!secondOnly) {
  assert(triedWrongCorner && revisitedCorner);
  assert(acquired.has('rev:01:record:v4:E1-PAPER'));
 }
 checks.push({kind: 'evidence-records', nodes: [...acquired]});
 assert.equal(trial.taskId, firstTask);
 assert.equal(trial.mode, 'trial');
 await probe.capture('revised-court-opening');
 checks.push({kind: 'court-start', node: trial.node, task: trial.taskId});
 }
 const firstAmmo = ['v4:E1-07', 'v4:E1-02', 'v4:E1-09'];
 const laterRounds = [
  {taskId: 'T1-NS-REV05', bullets: ['v4:E1-01', 'v4:E1-PHOTO', 'v4:E1-DISC'], wrong: 'v4:E1-PHOTO'},
  {taskId: 'T1-QA-REV02', choice: true, answerIndex: 0},
  {taskId: 'T1-PE-REV01', person: true, answerIndex: 0},
  {taskId: 'T1-NS-REV06', bullets: ['v4:E1-02', 'v4:E1-03', 'v4:E1-09'], wrong: 'v4:E1-02'},
 ];
 const lateRounds = {
  4: [
   {taskId:'T4-NS-REV02',bullets:['v4:V5-4:handover','v4:V5-4:photos','v4:V5-4:condition'],wrong:'v4:V5-4:photos'},
   {taskId:'T4-PN-REV01',bullets:['v4:V5-4:handover','v4:V5-4:photos','v4:V5-4:condition'],panic:true},
   {taskId:'T4-QA-REV01',choice:true,answerIndex:1},
   {taskId:'T4-NS-REV03',bullets:['v4:V5-4:light','v4:V5-4:photos','v4:V5-4:handover'],wrong:'v4:V5-4:light',judgment:'agree'},
   {taskId:'T4-NS-REV04',bullets:['v4:V5-4:camera','v4:V5-4:latch','v4:E4-13'],wrong:'v4:V5-4:camera'},
   {taskId:'T4-NS-REV05',bullets:['v4:V5-4:handover','v4:E4-13','v4:V5-4:latch'],wrong:'v4:V5-4:handover'},
  ],
  5: [
   {taskId:'T5-LI-REV01',bullets:['v4:V5-5:stock','v4:V5-5:cup'],wrong:'v4:V5-5:cup',useLie:true,judgment:'lie'},
   {taskId:'T5-MM-REV01',mine:true},
   {taskId:'T5-NS-REV02',bullets:['v4:V5-5:cup','v4:V5-5:stock','v4:V5-5:mark-window'],wrong:'v4:V5-5:cup'},
  ],
  6: [
   {taskId:'T6-QA-REV01',choice:true,answerIndex:1},
   {taskId:'T6-NS-REV02',bullets:['v4:V5-6:voice-window','v4:V5-6:signature','v4:V5-6:motion'],wrong:'v4:V5-6:voice-window'},
   {taskId:'T6-NS-REV03',bullets:['v4:V5-6:side-door','v4:V5-6:motion','v4:V5-6:railing'],wrong:'v4:V5-6:side-door'},
  ],
 };
 const fifthRounds = [
  [9,'package-pieces','window-witness','custody-sequence'],
  [10,'cup','package-pieces','late-cup-contact'],
  [11,'fitting-edge','cup','warning-match'],
  [12,'cup','warning-match','d-storage-match'],
  [13,'warning-match','rewind','marked-selection'],
  [14,'death-confirmation','nana-line','oath-closure'],
 ].map(([number,...keys])=>({taskId:'T5-NS-REV'+String(number).padStart(2,'0'),
  bullets:keys.map(key=>'v4:V5-5:'+key),wrong:'v4:V5-5:'+keys[0]}));
 const sixthNonstop=(number,keys,judgment)=>({
  taskId:'T6-NS-REV'+String(number).padStart(2,'0'),bullets:keys.map(key=>'v4:V5-6:'+key),
  wrong:'v4:V5-6:'+keys[0],judgment,
 });
 const rounds = firstDaily||secondDaily||thirdDaily||fourthDaily||fifthDaily||sixthDaily ? [] : sixthOpening ? [
  {taskId:'T6-SP-REV01',point:true},{taskId:'T6-RE-REV02',reasoning:true},
  {taskId:'T6-PN-REV02',bullets:['entry-count','railing','side-door'].map(key=>'v4:V5-6:'+key),panic:true},
  sixthNonstop(15,['document-edit','safety-hold','inspection-order']),
  sixthNonstop(16,['entry-count','separate-connections','old-intake-scope']),
  sixthNonstop(17,['signature','operation-screen','document-order']),
  ...(authoredTasks['T6-RE-REV03']?[
   {taskId:'T6-RE-REV03',reasoning:true},{taskId:'T6-RE-REV04',reasoning:true},
   {taskId:'T6-QA-REV08',choice:true,answerIndex:1},
  ]:[]),
 ] : witnessBoundaries ? [
  {taskId:'T1-NS-REV15',bullets:['v4:E1-03','v4:E1-04','v4:E1-SIGHT'],wrong:'v4:E1-03'},
  {taskId:'T1-RE-REV02',reasoning:true},{taskId:'T1-BU-REV01',picker:true,answerIndex:2},
 ] : sixthPast ? [
  {taskId:'T6-MM-REV01',mine:true},
  sixthNonstop(4,['railing','side-door','continuous-view']),
  {taskId:'T6-BU-REV01',picker:true,answerIndex:2},
  sixthNonstop(5,['signature','side-door','document-order']),
  {taskId:'T6-AN-REV01',anagram:true},
  sixthNonstop(6,['signature','safety-hold','document-edit']),
  {taskId:'T6-QA-REV02',choice:true,answerIndex:1},{taskId:'T6-QA-REV03',choice:true,answerIndex:2},
  {taskId:'T6-RS-REV01',showdown:true},{taskId:'T6-MM-REV02',mine:true},{taskId:'T6-VOTE-REV01',historicVote:true},
 ] : sixthTransition ? [
  {taskId:'T6-PN-REV01',bullets:['side-door','first-approval','harm-separation'].map(key=>'v4:V5-6:'+key),panic:true},
  sixthNonstop(13,['harm-separation','emergency-open','alarm-order']),
  sixthNonstop(14,['side-door','first-approval','emergency-open']),
  {taskId:'T6-SD-REV01',scrum:true,scrumWrong:{pair:3,option:4}},
 ] : sixthPersonal ? [
  {taskId:'T6-QA-REV05',choice:true,answerIndex:1},
  sixthNonstop(18,['document-order','first-approval','memory-scope']),
  {taskId:'T6-RS-REV03',showdown:true},{taskId:'T6-RS-REV04',showdown:true},{taskId:'T6-RS-REV05',showdown:true},
  {taskId:'T6-QA-REV06',choice:true,answerIndex:1},
 ] : sixthOperating ? [
  sixthNonstop(7,['reapprove','operation-screen','first-approval']),
  {taskId:'T6-RS-REV02',showdown:true},{taskId:'T6-QA-REV04',choice:true,answerIndex:2},
  sixthNonstop(8,['operation-screen','oath-rule','origin']),
  sixthNonstop(9,['document-order','first-approval','reapprove']),
  sixthNonstop(10,['first-approval','origin','reapprove'],'agree'),
  sixthNonstop(11,['origin','first-approval','separate-connections']),
  sixthNonstop(12,['operation-screen','origin','separate-connections'],'agree'),
  {taskId:'T6-AA-REV01',armament:true},{taskId:'T6-RE-REV01',reasoning:true},
 ] : sixthPost ? [
  sixthNonstop(19,['operation-screen','separate-connections','independent-records']),
  {taskId:'T6-AN-REV02',anagram:true},{taskId:'T6-QA-REV07',choice:true,answerIndex:0},
 ] : sixthClosing ? [
  {taskId:'T6-LI-REV01',bullets:['v4:V5-6:entry-count','v4:V5-6:private-records'],wrong:'v4:V5-6:entry-count',
   useLie:process.argv.includes('--use-lie'),judgment:process.argv.includes('--use-lie')?'lie':'refute'},
 ] : fifthFinal ? [
  fifthRounds[5],{taskId:'T5-AN-REV02',anagram:true},{taskId:'T5-AA-REV01',armament:true},
  {taskId:'T5-QA-REV03',choice:true,answerIndex:1},{taskId:'T5-QA-REV04',choice:true,answerIndex:1},
  {taskId:'T5-QA-REV05',choice:true,answerIndex:2},
 ] : fifthLate ? [
  fifthRounds[0],{taskId:'T5-PE-REV01',person:true,answerIndex:1},{taskId:'T5-QA-REV07',choice:true,answerIndex:1},
  {taskId:'T5-QA-REV08',choice:true,answerIndex:0},{taskId:'T5-QA-REV09',choice:true,answerIndex:2},
  {taskId:'T5-QA-REV10',choice:true,answerIndex:1},fifthRounds[1],
  {taskId:'T5-QA-REV11',choice:true,answerIndex:2},...fifthRounds.slice(2,5),
 ] : fifthPackage ? [
  {taskId:'T5-NS-REV07',bullets:['v4:V5-5:stock','v4:V5-5:window-witness','v4:V5-5:package-pieces'],wrong:'v4:V5-5:stock',judgment:'agree'},
  {taskId:'T5-SD-REV01',scrum:true,scrumWrong:{pair:3,option:4}},
  {taskId:'T5-RS-REV02',showdown:true},
  {taskId:'T5-MM-REV02',mine:true},
  {taskId:'T5-SP-REV01',point:true},
  {taskId:'T5-BU-REV02',picker:true,answerIndex:2},
  {taskId:'T5-NS-REV08',bullets:['v4:V5-5:archive-route','v4:V5-5:drink-timing','v4:V5-5:rewind'],wrong:'v4:V5-5:archive-route',judgment:'agree'},
  {taskId:'T5-RE-REV01',reasoning:true},
  {taskId:'T5-RS-REV03',showdown:true},
 ] : fifthTiming ? [
  {taskId:'T5-NS-REV03',bullets:['v4:V5-5:injury','v4:V5-5:cup','v4:V5-5:drink-timing'],wrong:'v4:V5-5:injury'},
  {taskId:'T5-NS-REV04',bullets:['v4:V5-5:stock','v4:V5-5:archive-route','v4:V5-5:first-stock'],wrong:'v4:V5-5:stock'},
  {taskId:'T5-BU-REV01',picker:true,answerIndex:1},
  {taskId:'T5-NS-REV05',bullets:['v4:V5-5:first-stock','v4:V5-5:stock','v4:V5-5:sealed-five'],wrong:'v4:V5-5:first-stock'},
  {taskId:'T5-NS-REV06',bullets:['v4:V5-5:cup','v4:V5-5:injury','v4:V5-5:pour-boundary'],wrong:'v4:V5-5:cup'},
  {taskId:'T5-PN-REV01',bullets:['v4:V5-5:archive-route','v4:V5-5:drink-timing','v4:V5-5:rewind'],panic:true},
  {taskId:'T5-RS-REV01',showdown:true},
  {taskId:'T5-AN-REV01',anagram:true},
  {taskId:'T5-PN-REV02',bullets:['v4:V5-5:mark-window','v4:V5-5:package-pieces','v4:V5-5:pour-boundary'],panic:true},
 ] : fourthReasoning ? [{taskId:'T4-RE-REV01',reasoning:true}] : fourthLast ? [
  {taskId:'T4-LI-REV01',bullets:['v4:V5-4:handover','v4:V5-4:latch'],wrong:'v4:V5-4:latch',useLie:fourthLie,judgment:fourthLie?'lie':'refute'},
  {taskId:'T4-QA-REV06',choice:true,answerIndex:0},
  {taskId:'T4-QA-REV07',choice:true,answerIndex:0},
  {taskId:'T4-BU-REV01',picker:true,answerIndex:1},
  {taskId:'T4-NS-REV12',bullets:['v4:V5-4:condition','v4:V5-4:camera','v4:V5-4:closure-line'],wrong:'v4:V5-4:condition'},
  {taskId:'T4-NS-REV13',bullets:['v4:V5-4:handover','v4:V5-4:condition','v4:E4-13'],wrong:'v4:V5-4:handover'},
  {taskId:'T4-NS-REV14',bullets:['v4:E4-13','v4:V5-4:handover','v4:V5-4:light'],wrong:'v4:E4-13'},
  {taskId:'T4-SD-REV01',scrum:true,scrumWrong:{pair:3,option:4}},
  {taskId:'T4-RE-REV01',reasoning:true},
 ] : fourthFinal ? [
  {taskId:'T4-RS-REV05',showdown:true},
  {taskId:'T4-AA-REV01',armament:true},
 ] : fourthRoute ? [
  {taskId:'T4-MM-REV01',mine:true},
  {taskId:'T4-MM-REV02',mine:true},
  {taskId:'T4-RS-REV04',showdown:true},
  {taskId:'T4-NS-REV11',bullets:['v4:V5-4:handover','v4:V5-4:photos','v4:E4-08'],wrong:'v4:V5-4:handover'},
 ] : fourthIdentity ? [
  {taskId:'T4-RS-REV01',showdown:true},
  {taskId:'T4-RS-REV02',showdown:true},
  {taskId:'T4-RS-REV03',showdown:true},
  {taskId:'T4-NS-REV09',bullets:['v4:V5-4:condition','v4:V5-4:photos','v4:V5-4:continuous-rescue'],wrong:'v4:V5-4:condition'},
  {taskId:'T4-AN-REV01',anagram:true},
  {taskId:'T4-PN-REV02',bullets:['v4:E4-13','v4:V5-4:handover','v4:V5-4:continuous-rescue'],panic:true},
  {taskId:'T4-NS-REV10',bullets:['v4:V5-4:handover','v4:V5-4:rescue-comparison','v4:V5-4:continuous-rescue'],wrong:'v4:V5-4:handover'},
 ] : fourthPhysical ? [
  {taskId:'T4-QA-REV02',choice:true,answerIndex:1},
  {taskId:'T4-QA-REV03',choice:true,answerIndex:0},
  {taskId:'T4-QA-REV04',choice:true,answerIndex:0},
  {taskId:'T4-SP-REV01',point:true},
  {taskId:'T4-NS-REV06',bullets:['v4:V5-4:light','v4:V5-4:handover','v4:V5-4:mechanism-comparison'],wrong:'v4:V5-4:light'},
  {taskId:'T4-NS-REV07',bullets:['v4:V5-4:photos','v4:V5-4:handover','v4:V5-4:mechanism-comparison'],wrong:'v4:V5-4:photos'},
  {taskId:'T4-NS-REV08',bullets:['v4:V5-4:light','v4:V5-4:condition','v4:V5-4:mechanism-comparison'],wrong:'v4:V5-4:light'},
  {taskId:'T4-PE-REV01',person:true,answerIndex:0},
  {taskId:'T4-QA-REV05',choice:true,answerIndex:1},
 ] : lateChapter ? [{
  taskId: `T${lateChapter}-NS-REV01`,
  bullets: ({
   4: ['v4:V5-4:photos', 'v4:V5-4:handover', 'v4:E4-08'],
   5: ['v4:V5-5:archive-route', 'v4:V5-5:injury', 'v4:V5-5:cup'],
   6: ['v4:V5-6:signature', 'v4:V5-6:side-door', 'v4:V5-6:voice-window'],
  })[lateChapter],
  wrong: ({4: 'v4:V5-4:photos', 5: 'v4:V5-5:archive-route', 6: 'v4:V5-6:signature'})[lateChapter],
 }, ...lateRounds[lateChapter]] : theatreArguments ? [
  {taskId:'T2-MM-REV01',mine:true},
  {taskId:'T2-NS-REV03',bullets:['v4:E205','v4:E202','v4:E207'],wrong:'v4:E202'},
  {taskId:'T2-NS-REV04',bullets:['v4:E203','v4:E205','v4:E206'],wrong:'v4:E206',judgment:'agree'},
  {taskId:'T2-RS-REV01',showdown:true},
  {taskId:'T2-QA-REV03',choice:true,answerIndex:2},
  {taskId:'T2-NS-REV05',bullets:['v4:E204','v4:E205','v4:E203'],wrong:'v4:E204',judgment:'agree'},
  {taskId:'T2-LI-REV01',bullets:['v4:E202','v4:E204','v4:E205'],wrong:'v4:E204',useLie:true,judgment:'lie'},
  {taskId:'T2-NS-REV06',bullets:['v4:E207','v4:E204','v4:E206'],wrong:'v4:E207'},
  {taskId:'T2-SD-REV01',scrum:true,scrumWrong:{pair:2,option:0}},
 ] : theatrePhysical ? [
  {taskId:'T2-MM-REV02',mine:true},
  {taskId:'T2-RS-REV02',showdown:true},
 ] : theatreSighting ? [
  {taskId:'T2-NS-REV07',bullets:['v4:E204','v4:E207','v4:E206'],wrong:'v4:E204'},
  {taskId:'T2-SP-REV02',point:true},
  {taskId:'T2-QA-REV07',choice:true,answerIndex:2},
  {taskId:'T2-PN-REV02',bullets:['v4:E204','v4:E206','v4:E202'],panic:true},
  {taskId:'T2-QA-REV04',choice:true,answerIndex:2},
  {taskId:'T2-QA-REV05',choice:true,answerIndex:1},
  {taskId:'T2-AN-REV01',anagram:true},
 ] : theatreArmament ? [{taskId:'T2-AA-REV01',armament:true}] :
 armamentOnly ? [{taskId: 'T1-AA-REV01', armament: true}] : signatureOnly ? [
  {taskId: 'T1-AN-REV02', anagram: true},
  {taskId: 'T1-SD-REV01', scrum: true},
  {taskId: 'T1-QA-REV05', choice: true, answerIndex: 1},
 ] : phoneOnly ? [
  ...(!phoneEvidence ? [{taskId: 'T1-QA-REV04', choice: true, answerIndex: 1},
  {taskId: 'T1-PN-REV02', bullets: ['v4:E1-13', 'v4:E1-02', 'v4:E1-03'], panic: true},
  {taskId: 'T1-PE-REV02', picker: true, answerIndex: 1},
  {taskId: 'T1-PE-REV03', picker: true, answerIndex: 1}] : []),
  {taskId: 'T1-RE-REV01', reasoning: true},
  {taskId: 'T1-NS-REV14', bullets: ['v4:E1-06', 'v4:E1-13', 'v4:E1-11'], wrong: 'v4:E1-06'},
  {taskId: 'T1-RS-REV02', showdown: true},
 ] : rescueOnly ? [
  {taskId: 'T1-RS-REV01', showdown: true},
  {taskId: 'T1-NS-REV13', bullets: ['v4:E1-09', 'v4:E1-02', 'v4:E1-13'], wrong: 'v4:E1-09'},
 ] : thirdArmament ? [
  {taskId:'T3-AA-REV01',armament:true},
 ] : thirdVictim ? [
  {taskId:'T3-PE-REV02',picker:true,answerIndex:0},
  {taskId:'T3-AN-REV02',anagram:true},
 ] : thirdContinuity ? [
  {taskId:'T3-QA-REV13',choice:true,answerIndex:2},
  {taskId:'T3-QA-REV14',choice:true,answerIndex:2},
  {taskId:'T3-NS-REV13',bullets:['v4:V5-3:condition','v4:V5-3:clock-bench','v4:V5-3:new-sentence'],wrong:'v4:V5-3:condition'},
  {taskId:'T3-NS-REV14',bullets:['v4:V5-3:reflection','v4:V5-3:second-status','v4:V5-3:continuity'],wrong:'v4:V5-3:reflection'},
  {taskId:'T3-RS-REV02',showdown:true},
  {taskId:'T3-SP-REV02',point:true},
  {taskId:'T3-SD-REV01',scrum:true,scrumWrong:{pair:2,option:1}},
 ] : thirdPaper ? [
  {taskId:'T3-NS-REV09',bullets:['v4:V5-3:reflection','v4:V5-3:loan','v4:V5-3:sealed-route'],wrong:'v4:V5-3:reflection'},
  {taskId:'T3-LI-REV01',bullets:['v4:V5-3:unread-sentence','v4:V5-3:reflection','v4:V5-3:loan'],useLie:true},
  {taskId:'T3-NS-REV10',bullets:['v4:V5-3:new-sentence','v4:V5-3:sealed-route','v4:V5-3:reflection'],wrong:'v4:V5-3:new-sentence'},
  {taskId:'T3-NS-REV11',bullets:['v4:V5-3:index','v4:V5-3:new-sentence','v4:V5-3:written-order'],wrong:'v4:V5-3:index',judgment:'agree'},
  {taskId:'T3-RS-REV01',showdown:true},
  {taskId:'T3-QA-REV10',choice:true,answerIndex:1},
  {taskId:'T3-QA-REV11',choice:true,answerIndex:0},
  {taskId:'T3-QA-REV12',choice:true,answerIndex:2},
  {taskId:'T3-RE-REV01',reasoning:true},
  {taskId:'T3-NS-REV12',bullets:['v4:V5-3:reflection','v4:V5-3:new-sentence','v4:V5-3:perception'],wrong:'v4:V5-3:reflection'},
 ] : thirdPanic ? [
  {taskId:'T3-PN-REV02',bullets:['v4:V5-3:blade-stop','v4:V5-3:loan','v4:V5-3:cloth-handover'],panic:true},
 ] : thirdTimeline ? [
  {taskId:'T3-PE-REV01',picker:true,answerIndex:1},
  {taskId:'T3-QA-REV08',choice:true,answerIndex:0},
  {taskId:'T3-QA-REV09',choice:true,answerIndex:2},
 ] : thirdLater ? [
  {taskId:'T3-NS-REV07',bullets:['v4:V5-3:second-status','v4:V5-3:first-injury','v4:V5-3:cloth-handover'],wrong:'v4:V5-3:first-injury'},
  {taskId:'T3-QA-REV06',choice:true,answerIndex:1},
  {taskId:'T3-MM-REV02',mine:true},
  {taskId:'T3-NS-REV08',bullets:['v4:V5-3:blade-stop','v4:V5-3:first-injury','v4:V5-3:movement'],wrong:'v4:V5-3:blade-stop'},
 ] : thirdOnly ? [
  {taskId: 'T3-NS-REV01', bullets: ['v4:V5-3:reflection', 'v4:V5-3:loan', 'v4:V5-3:camera-compare'], wrong: 'v4:V5-3:reflection'},
  {taskId: 'T3-MM-REV01', mine: true},
  {taskId: 'T3-SP-REV01', point: true},
  {taskId: 'T3-NS-REV02', bullets: ['v4:V5-3:reflection', 'v4:V5-3:loan', 'v4:V5-3:camera-compare'], wrong: 'v4:V5-3:reflection', judgment: 'agree'},
 ] : paperOnly ? [
  {taskId: 'T1-NS-REV09', bullets: ['v4:E1-08', 'v4:E1-04', 'v4:E1-PAPER'], wrong: 'v4:E1-08'},
  {taskId: 'T1-LI-REV01', bullets: ['v4:E1-08', 'v4:E1-06'], wrong: 'v4:E1-08', useLie: paperLie},
  {taskId: 'T1-NS-REV10', bullets: ['v4:E1-05', 'v4:E1-08', 'v4:E1-06'], wrong: 'v4:E1-08'},
 ] : witnessOnly ? [
  {taskId: 'T1-NS-REV07', bullets: ['v4:E1-03', 'v4:E1-04', 'v4:E1-02'], wrong: 'v4:E1-03'},
  {taskId: 'T1-NS-REV08', bullets: ['v4:E1-03', 'v4:E1-02', 'v4:E1-04'], wrong: 'v4:E1-03'},
 ] : secondOnly || secondLate ? [
  ...secondLate ? [] : [
   {taskId: 'T2-QA-REV01', choice: true, answerIndex: 2},
   {taskId: 'T2-NS-REV01', bullets: ['v4:E202', 'v4:E203', 'v4:E204'], wrong: 'v4:E203'},
   {taskId: 'T2-QA-REV02', choice: true, answerIndex: 1},
  ],
  {taskId: 'T2-BU-REV01', picker: true, answerIndex: 1},
  {taskId: 'T2-PE-REV01', picker: true, answerIndex: 1},
  {taskId: 'T2-PN-REV01', bullets: ['v4:E205', 'v4:E202', 'v4:E203'], panic: true},
  {taskId: 'T2-SP-REV01', point: true},
  {taskId: 'T2-NS-REV02', bullets: ['v4:E205', 'v4:E202', 'v4:E203'], wrong: 'v4:E202'},
 ] : laterOnly ? laterRounds : [
  {taskId: 'T1-NS-REV01', bullets: firstAmmo},
  {taskId: 'T1-PN-REV01', bullets: firstAmmo, panic: true},
  {taskId: 'T1-NS-REV02', bullets: ['v4:E1-08', 'v4:E1-07', 'v4:E1-02'], wrong: 'v4:E1-08'},
  {taskId: 'T1-QA-REV01', choice: true, answerIndex: 1},
  {taskId: 'T1-NS-REV03', bullets: ['v4:E1-03', 'v4:E1-11', 'v4:E1-01'], wrong: 'v4:E1-03'},
  {taskId: 'T1-NS-REV04', bullets: ['v4:E1-09', 'v4:E1-APP', 'v4:E1-13'], wrong: 'v4:E1-13'},
  ...laterRounds,
 ];
 for (const {taskId, bullets, wrong, panic, choice, person, picker, point, reasoning, answerIndex, useLie,
             showdown, anagram, scrum, armament, mine, historicVote, judgment, scrumWrong={pair:3,option:1}} of rounds) {
  const start = Date.now();
  let captured = false, shots = 0, silencers = 0, silenced = 0, wrongResponse = false;
  const reasoningLinks = new Set();
  const rhythmPhases = new Set();
  const rhythmHeld = new Set();
  let finalPhraseCaptured = false, defeatCaptured = false, selectionParked = false;
  while (Date.now() - start < (armament ? taskId.startsWith('T6-') ? 480000 : 310000 : 170000)) {
   const s = await state();
   if (s.lastTaskOutcome?.taskId === taskId) break;
   if (s.taskId !== taskId || s.taskQueue) {
    if (armament) for (const key of rhythmHeld) {
     await probe.key(key, false);
     rhythmHeld.delete(key);
    }
    if (s.taskId === taskId && (s.queueAfter === 'nonstop-wrong' ||
        s.queueAfter === 'resume' && !armament)) wrongResponse = true;
    await advance(s); continue;
   }
   if (!s.taskInputArmed || s.presentation?.nonstopIntro || s.scenes.loading) { await probe.sampled(4); continue; }
   if (mine) {
    if (s.auto?.kind === 'move') await probe.rightClick(s.auto.x,s.auto.y);
    else await advance(s);
    continue;
   }
   if (historicVote && s.auto?.kind==='wait') { await probe.tap('Enter'); continue; }
   if (historicVote || showdown || point || anagram) { await advance(s); continue; }
   if (armament) {
    const {kind, key} = s.auto || {};
    if (s.armamentV4?.notes?.length && !rhythmPhases.has(s.armamentV4.phase)) {
     rhythmPhases.add(s.armamentV4.phase);
     await probe.capture('revised-armament-phase-'+s.armamentV4.phase);
    }
    if (!finalPhraseCaptured && s.armamentV4?.final >= 0) {
     await probe.capture('revised-armament-final');
     finalPhraseCaptured = true;
    }
    if (!defeatCaptured && s.armamentV4?.finish > 0 && s.armamentV4.finish < 2) {
     await probe.capture('revised-armament-defeat');
     defeatCaptured = true;
    }
    if (kind === 'hold-key' && !rhythmHeld.has(key)) {
     await probe.key(key, true);
     rhythmHeld.add(key);
    } else if (kind === 'release-after' && rhythmHeld.has(key)) {
     await probe.key(key, false);
     rhythmHeld.delete(key);
    } else if (kind === 'rapid-key' || kind === 'key') {
     if (!rhythmHeld.has(key)) await probe.tap(key, 1);
    } else await probe.sampled(1);
    if (!s.armamentV4?.notes?.some(note => note.held >= 0 || note.type === 1 && note.due >= -.16)) {
     for (const held of rhythmHeld) { await probe.key(held, false); rhythmHeld.delete(held); }
    }
    continue;
   }
   if (scrum) {
    if (!wrongResponse && s.scrumV4?.pair === scrumWrong.pair && s.auto?.kind === 'key') {
     await probe.tap(s.stage.selection === scrumWrong.option ? 'Enter' : 's');
    } else await advance(s);
    continue;
   }
   if (reasoning) {
    if (s.endingV4?.time >= 0) { await advance(s); continue; }
    reasoningLinks.add(s.taskLink);
    if (s.taskLink === 0 && !wrongResponse) {
     const question=authoredTasks[taskId].stage.questions[0];
     const incorrect=question.options.findIndex(option=>option!==question.answer);
     await probe.tap(s.stage.selection===incorrect?'Enter':'s');
    } else await advance(s);
    continue;
   }
   if (!captured && panic) {
    await probe.capture('revised-panic');
    captured = true;
   }
   if (choice || person || picker) {
    if (wrongResponse) await advance(s);
    else {
     if(!selectionParked){await probe.move(100,40);await probe.sampled(8);selectionParked=true;continue;}
     if ((person || picker) && s.trialPicker?.pending >= 0) { await probe.sampled(4); continue; }
     if (s.stage.selection === answerIndex) {
      await probe.tap(s.stage.kind === 'bullet' ? 's' : person || picker ? 'd' : 'ArrowUp');
      await probe.sampled(8);continue;
     }
     await probe.tap('Enter');
     await probe.sampled(12);
    }
    continue;
   }
   const tr = s.trial;
   silenced = Math.max(silenced, tr?.noiseSilenced || 0);
   const loud = panic && tr?.noise >= 0 && (s.gpuNoiseHud?.panicPoints || []).find(([,x,y,,alpha]) => alpha > .65 && x > 40 && x < 1240 && y > 40 && y < 640);
   if (loud) { await probe.rightClick(loud[1], loud[2]); ++silencers; continue; }
   if (!tr || tr.clearing || tr.turning || tr.shotRecovery?.ready === false || !tr.answer || !tr.weakPoint) {
    await probe.sampled(4); continue;
   }
   const wanted = wrong && !wrongResponse ? wrong : tr.answer;
   if (tr.bullet !== wanted) { await probe.tap(bulletCycleKey(bullets, tr.bullet, wanted)); continue; }
   const plan = trialAimPlan(tr.weakPoint, await probe.aim());
   if (plan.kind === 'key') {
    await probe.key(plan.key, true);
    await new Promise(resolve => setTimeout(resolve, plan.ms));
    await probe.key(plan.key, false);
   } else {
    await probe.move(...plan.point);
    await probe.button(...plan.point, true, tr.shotButton || 'left');
    let release = plan.point;
    try {
     if (useLie && wanted === tr.answer) {
      const transformed = await probe.until(async () => {
       const next = await state();
       return next.trial?.lie ? next.trial : false;
      }, 'held evidence changes into a lie', 5000, 25);
      if (transformed.weakPoint) {
       const corrected = trialAimPlan(transformed.weakPoint, await probe.aim());
       if (corrected.kind === 'mouse') release = corrected.point;
      }
     }
    } finally {
     await probe.button(...release, false, tr.shotButton || 'left');
    }
    ++shots;
   }
  }
  const outcome = (await state()).lastTaskOutcome;
  assert.equal(outcome?.taskId, taskId, 'Native task did not reach an authored result');
  if (judgment) assert.equal(outcome.judgment,judgment);
  if (taskId === 'T1-LI-REV01') {
   assert.equal(outcome.judgment, useLie ? 'lie' : 'refute');
   assert.equal(outcome.sets['01-T04a:perjury'], useLie ? true : undefined);
  }
  if (panic) assert(silenced > 0, 'Panic must require the authored loud interruption to be cleared');
  if (wrong || choice || person || picker || reasoning || scrum) assert(wrongResponse, 'The wrong answer must return through its authored response');
  if (reasoning) assert.equal(reasoningLinks.size, authoredTasks[taskId].stage.questions.length, 'Each reasoning link was available for actual input');
  if (taskId === 'T3-LI-REV01') {
   assert.equal(outcome.judgment,'lie');
   assert.equal(outcome.sets['03-T02:perjury'],true);
  }
  if(taskId==='T4-LI-REV01')assert.equal(outcome.sets['04-T03c:perjury'],fourthLie?true:undefined);
  if (armament) {
   for (const key of rhythmHeld) await probe.key(key, false);
   assert.equal(rhythmPhases.size, taskId.startsWith('T6-')?4:3, 'Each rhythmic phase used native input');
  }
  checks.push({kind: 'task-outcome', taskId, outcome, shots, silencers, silenced, wrongResponse});
 }
 if(!firstDaily&&!secondDaily&&!thirdDaily&&!fourthDaily&&!fifthDaily&&!sixthDaily)await probe.until(async () => {
  const s = await state();
  if ((s.mode === 'title' ||
       (lateChapter===4&&!fourthFocus&&s.taskId==='T4-QA-REV02') ||
       (lateChapter===5&&!fifthFocus&&s.taskId==='T5-NS-REV03') ||
       (fifthTiming&&s.taskId==='T5-NS-REV07') ||
       (fifthPackage&&s.taskId==='T5-NS-REV09') ||
       (fifthLate&&s.taskId==='T5-NS-REV14') ||
       (fifthFinal&&s.taskId==='T5-CM-REV01') ||
       (lateChapter===6&&!sixthFocus&&s.taskId==='T6-MM-REV01') ||
       (sixthPast&&s.taskId==='T6-PN-REV01') ||
       (sixthOpening&&s.taskId==='T6-NS-REV01') ||
       (sixthTransition&&(s.taskId==='T6-QA-REV05'||s.taskId==='T6-NS-REV07')) ||
       (sixthPersonal&&s.taskId==='T6-NS-REV07') ||
       (sixthOperating&&(s.taskId==='T6-NS-REV19'||s.taskId==='T6-LI-REV01')) ||
       (sixthPost&&s.taskId==='T6-LI-REV01') ||
       (sixthClosing&&s.taskId==='T6-CM-REV01') ||
       (fourthPhysical&&s.taskId==='T4-RS-REV01') ||
       (fourthIdentity&&s.taskId==='T4-MM-REV01') ||
       (fourthFinal&&s.taskId==='T4-CM-REV01') ||
       (fourthRoute&&s.taskId==='T4-LI-REV01') ||
       (fourthLast&&s.mode==='story'&&s.lastTaskOutcome?.taskId==='T4-RE-REV01') ||
       (fourthReasoning&&s.taskId==='T4-RS-REV05') ||
       (theatreSighting && s.taskId === 'T2-QA-REV06-1') || (theatreArmament && s.taskId === 'T2-CM-REV01') ||
       (theatreArguments && s.taskId === 'T2-NS-REV07') ||
       (theatrePhysical && s.node === 'rev:02:spare-key-hypotheses') ||
       (thirdTimeline && s.taskId === 'T3-PN-REV02') ||
       (thirdLater && !thirdVictim && !thirdArmament && !thirdContinuity && !thirdPaper && !thirdTimeline && !thirdPanic && s.taskId === 'T3-PE-REV01') ||
       (thirdArmament && s.taskId==='T3-PE-REV02') ||
       (thirdPaper && s.taskId === 'T3-QA-REV13') ||
       (thirdPanic && s.taskId === 'T3-NS-REV09') ||
       (thirdContinuity && s.mode==='story' && s.v4Kind==='say' && s.lastTaskOutcome?.taskId==='T3-SD-REV01') ||
       (armamentOnly && s.taskId === 'T1-CM-REV01') || (signatureOnly && s.node === 'rev:01:pressure-armament') ||
       (phoneOnly && s.taskId === 'T1-AN-REV02') || (rescueOnly && s.taskId === 'T1-QA-REV04') ||
       ((secondOnly || secondLate) && s.taskId === 'T2-MM-REV01') || (thirdOnly && s.taskId === 'T3-NS-REV03') ||
       (witnessOnly && s.taskId === 'T1-NS-REV09') || (paperOnly && s.taskId === 'T1-MM-REV02') ||
       (witnessBoundaries && s.taskId === 'T1-NS-REV08') ||
       (!paperOnly && !secondOnly && !witnessOnly && s.taskId === 'T1-MM-REV01')) && !s.scenes.loading) return true;
  await advance(s);
  return false;
 }, 'authored follow-up finishes or reaches the next tested excerpt', 120000);
 if(fourthPhysical){assert.equal(fourthViews.size,6,'Three remote force and three sound hypotheses were all reviewed');checks.push({kind:'chapter-four-physical-hypotheses',views:[...fourthViews]});}
 }
 if(thirdLater&&!thirdArchive&&!thirdBook&&!thirdVictim&&!thirdArmament&&!thirdContinuity&&!thirdPaper&&!thirdTimeline&&!thirdPanic){
  assert.equal(restraintWitnesses.size,4,'All four witnesses answered only for their observed position');
  checks.push({kind:'restraint-witnesses',views:[...restraintWitnesses]});
 }
 }
 await probe.close();
 probe = null;
 await fs.writeFile(path.join(work, 'report.json'), JSON.stringify({ok: true, source, module, identity, checks}, null, 2));
 console.log(JSON.stringify({work,checks:checks.map(({nodes,...check})=>({...check,...nodes?{observedNodes:nodes.length}:{}}))}));
} catch (error) {
 const last = await probe?.stats().catch(() => null);
 await fs.writeFile(path.join(work, 'failure.json'), JSON.stringify({error: error.stack, identity, last, checks}, null, 2));
 throw error;
} finally {
 await probe?.close().catch(() => {});
}
