// Focused hidden native inputs. No canonical save mutation or task completion injection.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {createOwnedNativePackage} from './native-owned-package.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const root=path.resolve(import.meta.dirname,'..');
const mode=process.argv.find(a=>a.startsWith('--case='))?.slice(7)||'opening';
const openingChoice=process.argv.find(a=>a.startsWith('--opening-choice='))?.split('=')[1];
assert(openingChoice===undefined||openingChoice==='B');
const openingMeal=process.argv.includes('--opening-meal=B');
assert(!openingMeal||!openingChoice);
assert(['opening','final','recognition','secrecy'].includes(mode));
const buildFile=process.argv.find(a=>a.startsWith('--build-result='))?.slice(15);
const build=JSON.parse(await fs.readFile(buildFile?path.resolve(root,buildFile):path.join(root,'Saved/game-trial-work-20261102/current-flat-build-result.json'),'utf8'));
const work=path.join(root,'Saved/native-memory-'+mode+'-'+Date.now());
const read=async file=>JSON.parse(await fs.readFile(file,'utf8'));
const graph=await read(path.join(root,'../data/v4_story/chapters',mode==='opening'?'P.json':mode==='secrecy'?'5.json':'6.json'));
const checkpointDir=process.argv.find(a=>a.startsWith('--checkpoint-dir='))?.slice(17);
assert(!checkpointDir||mode==='secrecy');
let resume=mode==='final'?path.join(root,'Saved/v4-flow-1793453765826/task-T6-VOTE-01-savegames.json'):['recognition','secrecy'].includes(mode)?path.join(root,'Saved/v4-flow-1793453765826/chapter-6-savegames.json'):undefined;
const overrides=process.argv.find(a=>a.startsWith('--story-overrides='))?.slice(18);
const gameModule=process.argv.find(a=>a.startsWith('--game-module='))?.slice(14);
const expectVoteAutoCommit=process.argv.includes('--expect-vote-auto-commit');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
let probe,firstUnknown=false,checkedWrong=false,boundaryReached=false,steps=0;
const observed=new Set(),introduced=new Set(['mio']),links=new Set();
async function checkpoint(label,node){
 await probe.tap('Tab',3);assert.equal((await probe.stats()).mode,'pad');
 await probe.click(1047,480);
 if((await probe.stats()).padPage!==5){await probe.tap('Backspace',3);await probe.click(1047,480);}
 assert.equal((await probe.stats()).padPage,5);await padSystemAction(probe.stats,probe.tap,'save');await probe.tap('Tab',3);
 assert.equal((await probe.stats()).node,node,'Manual save must not advance the dialogue');
 const dir=path.join(work,'checkpoints',label);await fs.mkdir(dir,{recursive:true});
 await fs.cp(path.join(work,'State/Saves'),path.join(dir,'Saves'),{recursive:true,errorOnExist:true,force:false});
 await fs.writeFile(path.join(dir,'receipt.json'),JSON.stringify({node,method:'Actual native pad system save, followed by byte-preserving copy of native save slots.',stateFieldsModified:false},null,2));
}
try{
 if(checkpointDir){
  const from=path.resolve(root,checkpointDir),receipt=await read(path.join(from,'receipt.json'));
  const head=await fs.readFile(path.join(from,'Saves/yumeno-progress-v4.json'));
  assert.equal(createHash('sha256').update(head).digest('hex'),receipt.nativeHeadSha256);
  assert.equal(JSON.parse(head).node,receipt.verifiedActualHeadNode);assert.equal(receipt.stateFieldsModified,false);
  await fs.mkdir(path.join(work,'State'),{recursive:true});
  await fs.cp(path.join(from,'Saves'),path.join(work,'State/Saves'),{recursive:true,errorOnExist:true,force:false});
  await fs.writeFile(path.join(work,'checkpoint-selection.json'),JSON.stringify({source:from,...receipt},null,2));resume=undefined;
 }else if(mode==='recognition'||mode==='secrecy'){
  // Select the actual chapter-start archive blob; never manufacture a node,
  // flag, inventory item or completion. The original export remains untouched.
  const bytes=await fs.readFile(resume),saved=JSON.parse(bytes),chapter=mode==='recognition'?'6':'5';
  const key=Object.keys(saved.items).find(k=>k.includes('.yumeno-v4-entry-'+chapter+'-0.project.'));
  const head=Object.keys(saved.items).find(k=>k.includes('.yumeno-progress-v4.project.'));
  assert(key&&head);const blob=saved.items[key],state=JSON.parse(blob);assert.equal(state.chapter,chapter);
  saved.items[head]=blob;await fs.mkdir(work,{recursive:true});
  await fs.writeFile(path.join(work,'archive-selection.json'),JSON.stringify({source:resume,sourceSha256:createHash('sha256').update(bytes).digest('hex'),selectedSlot:key,node:state.node,selectedBlobSha256:createHash('sha256').update(blob).digest('hex'),stateFieldsModified:false},null,2));
  resume=path.join(work,'selected-archive-savegames.json');await fs.writeFile(resume,JSON.stringify(saved));
 }
 let prepared;
 if(overrides){const rows=await read(overrides);assert(Object.keys(rows).length>0);assert(Object.keys(rows).every(p=>p.startsWith('Content/Assets/Data/v4_story/')&&p.endsWith('.json')));}
 if(overrides||gameModule)prepared=await createOwnedNativePackage({source:build.output,work,gameContentOverrides:overrides,gameModuleCandidate:gameModule,stats:true});
 probe=await nativeWindowProbe({source:build.output,work,prepared,resume,maxFrames:null,heartbeatTimeoutMs:120000});
 if(mode==='opening'){
  await probe.tap('Enter');assert((await probe.stats()).difficulty.open);
  await probe.tap('s');await probe.tap('s');await probe.tap('Enter');
 }else await probe.tap('c');
 const entered=await probe.until(async()=>{const s=await probe.stats();assert(!s.error,s.error);return s.contentVersion==='v4'&&!s.scenes.loading?s:false;},'revised content entry',120000);
 const started=Date.now();let last=entered,sawHistorical=false,resultAfterFinal=false;
 // Chapter 5 covers two days of actual dialogue inputs before the noon boundary.
 const traversalTimeoutMs=mode==='secrecy'?480000:240000;
 while(Date.now()-started<traversalTimeoutMs){
  const s=last=await probe.stats();assert(!s.error,s.error);assert(!s.routeBlocked,'Revised route blocked');
  if(s.scenes.loading){await pause(15);continue;}
  if(mode==='recognition'||mode==='secrecy'){
   const n=graph.nodes[s.node];assert(n,'Unknown revised source node '+s.node);
   if(n.type==='say')assert.equal(s.line,n.text,'Actual packaged prose must match revised source');
   observed.add(s.node);
   if(mode==='recognition'){
    if(n.type==='document'&&n.source?.file?.startsWith('194_')){
     const marker='document:'+n.title;
     if(!observed.has(marker)){
      observed.add(marker);const number=[...observed].filter(k=>k.startsWith('document:')).length;
      let actual='',page=1,pages=1;
      do{
       const key='disclosure-document-'+number+'-page-'+page;
       await probe.capture(key);const ui=await read(path.join(work,key+'.ui.json'));
       const nodes=ui.widgets.flatMap(w=>w.nodes),body=nodes.find(v=>v.id==='DocumentBody'),hint=nodes.find(v=>v.id==='DocumentHint');
       assert(body?.properties?.visible&&hint?.properties?.visible);
       const count=hint.properties.text.match(/^(\d+)\/(\d+)/);assert(count);assert.equal(Number(count[1]),page);pages=Number(count[2]);
       actual+=body.properties.text;
       if(gameModule||!overrides){const rect=ui.rects.find(v=>v.id==='DocumentBody');assert.equal(rect.y,230);assert.equal(rect.h,260);}
       if(page<pages){await probe.tap('Enter',3);steps++;assert.equal((await probe.stats()).node,s.node);}
      }while(page++<pages);
      const normalize=v=>v.replace(/\s/g,'');
      for(const row of n.rows)assert(normalize(actual).includes(normalize(row)),'Document row not presented: '+row);
     }
    }
    if(n.source?.file?.startsWith('194_')&&n.text?.includes('그 열세 분 안에')){observed.add('identity-disclosed');await probe.capture('identity-disclosed');}
    if(n.source?.file?.startsWith('16a_')&&n.source.location==='6-07'){
     assert(observed.has('identity-disclosed'),'Personal accusation before unredacted disclosure');
     for(const title of ['옛 행사 준비물 인계표','옛 성명면·인형 인계 대조','옛 접수·개입·맹세 서명 대조','이번 입소 처리 이력'])assert(observed.has('document:'+title),'Unread relationship source '+title);
     await probe.capture('personal-after-disclosure');boundaryReached=true;break;
    }
   }else{
    if(n.type==='say')for(const old of ['코토 씨하고 맺은 약속이요','제가 그날 여러분 기억을 없앴어요','너는 이미 나한테 한 적 있었네.','예전에는 안 했는데 네가 했고.'])assert(!s.line.includes(old));
    if(n.source?.file?.startsWith('15a_')&&n.text?.includes('지금 이 사본에서는 상대 이름이 가려져')){observed.add('anonymous-pact');await probe.capture('anonymous-pact');}
    if(!checkpointDir&&n.type==='say'&&n.source?.file?.startsWith('15a6_')&&n.source.location==='5-89'&&!observed.has('before-noon-save')){await checkpoint('before-noon',s.node);observed.add('before-noon-save');}
    if(n.source?.file?.startsWith('15a6_')&&n.text?.includes('가려지지 않은 원본')){observed.add('original-request');await probe.capture('original-request');}
    if(n.source?.file?.startsWith('15a6_')&&n.text?.includes('아직은 몰라요.이름이 가려져')){observed.add('anonymous-target');await probe.capture('anonymous-target');}
    if(n.type==='say'&&n.source?.file?.startsWith('127_')&&!observed.has('anonymous-target-callback')){observed.add('anonymous-target-callback');await probe.capture('anonymous-target-callback');}
    if(n.type==='say'&&n.source?.file?.startsWith('15a7_')&&n.text?.includes('린 씨인지는 아직 몰라요.'))observed.add('rin-target-unconfirmed');
    if(n.source?.file?.startsWith('15a8_')){
     const required=['original-request','anonymous-target','anonymous-target-callback','rin-target-unconfirmed'];if(!checkpointDir)required.push('anonymous-pact');
     assert(required.every(k=>observed.has(k)));
     await probe.capture('after-public-disclosure');await checkpoint('after-noon',s.node);boundaryReached=true;break;
    }
   }
   if(s.auto?.kind==='click'){await probe.click(s.auto.x,s.auto.y);steps++;}
   else if(s.auto?.kind==='key'){await probe.tap(s.auto.key,3);steps++;}
   else if(s.mode==='story'||s.mode==='menu'){await probe.tap('Enter',3);steps++;}
   else throw Error('Unexpected mode in revised disclosure path '+s.mode);
   continue;
  }
  if(mode==='opening'){
   const n=graph.nodes[s.node];assert(n,'Unknown current opening node '+s.node);
   if(!observed.has(s.node)){
    observed.add(s.node);
    if(n.type==='say'){
     assert.equal(s.speaker,n.mono?'':n.speaker);
     if(n.introducesActor)introduced.add(n.introducesActor);
     if(n.speaker==='???'&&!firstUnknown){
      await probe.capture('unknown-speaker');const ui=await read(path.join(work,'unknown-speaker.ui.json'));
      const layout=await read(path.join(root,'Assets/Data/v4_story/dialogue_layout.json'));
      assert(layout.nameAssets['???'],'Unknown name must be published as the same outlined-name asset type');
      assert(ui.widgets.some(w=>w.nodes.some(n=>n.id==='Name'&&n.properties?.visible&&n.properties.texture===layout.nameAssets['???'])));
      assert(!ui.world.some(o=>o.id==='CourtGeometry'));
      firstUnknown=true;
     }
    }
   }
   if(s.node==='v4:10:P-C01'){
    assert(firstUnknown);assert.equal(introduced.size,16);
    if(!observed.has('first-choice')){await probe.capture('first-choice');observed.add('first-choice');}
    if(!openingChoice&&!openingMeal)break;
    if(openingChoice){await probe.tap('s',3);steps++;}
    await probe.tap('Enter',3);steps++;continue;
   }
   if(openingMeal&&s.node==='v4:10:P-C02'){
    await probe.capture('meal-choice');await probe.tap('s',3);await probe.tap('Enter',3);steps+=2;continue;
   }
   if(openingMeal&&n.type==='say'&&n.text==='네 것까지 받아 놨는데 이제 가는 거야?'){
    assert.equal(s.line,n.text);observed.add('opening-meal-revised');await probe.capture('opening-meal-revised');break;
   }
   if(openingChoice&&n.type==='say'&&n.text==='나 말고도 이름은 다 들었잖아.'){
    assert.equal(s.line,n.text);observed.add('opening-b-revised');await probe.capture('opening-b-revised');break;
   }
   await probe.tap('Enter',3);steps++;continue;
  }
  if(s.taskId==='T6-VOTE-01')sawHistorical=true;
  if(s.taskId==='T6-VOTE-01'&&s.auto?.kind==='key'&&s.auto?.key==='Enter')observed.add('vote-auto-commit');
  if(s.lastTaskOutcome?.taskId==='T6-VOTE-01'&&!observed.has('after-historical')){
   observed.add('after-historical');await probe.capture('after-historical');
   const ui=await read(path.join(work,'after-historical.ui.json'));
   assert(!ui.widgets.some(w=>w.instance==='trialresultv4'),'Historical identification must not open final results');
  }
  if(s.taskId==='T6-RL-FINAL'&&!s.taskQueue&&s.taskInputArmed){
   links.add(s.taskLink);
   if(!checkedWrong&&s.taskLink===0){
    // Question one opens on A; A is an explicitly authored wrong claim.
    await probe.tap('Enter',3);
    await probe.until(async()=>{const row=await probe.stats();assert(!row.error,row.error);return row.taskQueue?row:false;},'actual first-link wrong response',10000);
    const wrong=await probe.stats();assert.equal(wrong.taskId,'T6-RL-FINAL');assert.equal(wrong.taskLink,0);
    checkedWrong=true;steps++;continue;
   }
  }
  if(s.lastTaskOutcome?.taskId==='T6-RL-FINAL'){
   assert(sawHistorical&&observed.has('after-historical'));assert(checkedWrong);assert.equal(links.size,7);
   await probe.capture('final-result');const ui=await read(path.join(work,'final-result.ui.json'));
   assert(ui.widgets.some(w=>w.instance==='trialresultv4'),'Result must open after the whole final hearing');
   await probe.sampled(240);await probe.tap('Enter',3);
   const closure=graph.nodes[s.lastTaskOutcome.target];assert.equal(closure.set['public:intake:relationship-mask-ended'],true);
   const closed=await probe.until(async()=>{const row=await probe.stats();assert(!row.error,row.error);return row.mode==='story'&&row.node===closure.next?row:false;},'actual control and intake-mask closure after results',20000);
   assert.equal(closed.line,graph.nodes[closure.next].text);
   await probe.capture('control-and-mask-ended');
   resultAfterFinal=true;break;
  }
  if(s.taskQueue){await probe.tap('Enter',3);steps++;continue;}
  const a=s.auto||{};
  if(s.taskId==='T6-VOTE-01'&&a.kind==='click'){
   // Vote portraits select; Enter commits. Do not confuse a selected portrait
   // with a submitted ballot or keep selecting it until the timer expires.
   await probe.click(a.x,a.y);await probe.capture('historical-selected');
   const selected=await probe.stats();assert.equal(selected.taskId,'T6-VOTE-01');
   if(expectVoteAutoCommit){assert.equal(selected.auto?.kind,'key');assert.equal(selected.auto?.key,'Enter');observed.add('vote-auto-commit');}
   await probe.tap('Enter',3);steps+=2;continue;
  }
  if(a.kind==='key'||a.kind==='rapid-key'){await probe.tap(a.key,3);steps++;}
  else if(a.kind==='click'){await probe.click(a.x,a.y);steps++;}
  else if(s.mode==='story'){await probe.tap('Enter',3);steps++;}
  else await pause(15);
 }
 if(mode==='opening'){
  if(openingMeal)assert(observed.has('opening-meal-revised'),'Opening meal did not reach current-day response');
  else if(openingChoice)assert(observed.has('opening-b-revised'),'Opening B did not reach revised stranger response');
  else assert.equal(last.node,'v4:10:P-C01','Opening did not reach first authored choice');
 }
 else if(mode==='final'){assert(resultAfterFinal,'Final hearing did not reach its own result boundary');if(expectVoteAutoCommit)assert(observed.has('vote-auto-commit'),'Game guidance did not request ballot confirmation');}
 else assert(boundaryReached&&observed.has(mode==='recognition'?'identity-disclosed':checkpointDir?'original-request':'anonymous-pact'),'Revised disclosure/consumer boundary not reached');
 const runtime=await probe.close();probe=null;
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,mode,build:build.id,work,steps,
  observedNodes:observed.size,openingChoice,openingMeal,checkpointDir,storyOverrides:overrides,gameModuleCandidate:gameModule,sourceCandidate:!!(overrides||gameModule),introducedActors:mode==='opening'?introduced.size:undefined,
  wrongLinkRetried:mode==='final'?checkedWrong:undefined,voteAutoCommit:observed.has('vote-auto-commit'),finalLinks:[...links],resultAfterFinal,runtime,
  scope:(gameModule?'Own game module and story-data candidate; unchanged engine. ':overrides?'Own story-data candidate on an unchanged native module and engine. ':'Immutable compiled native build. ')+mode+' focused route via actual hidden Win32 input and unchanged normal saves. No original game, no success injection, no play-time or whole-art acceptance.'},null,2));
 console.log(JSON.stringify({ok:true,mode,work,steps,introduced:introduced.size,links:[...links]}));
}catch(error){
 await fs.mkdir(work,{recursive:true});await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,last:await probe?.stats().catch(()=>null)},null,2));
 await probe?.capture('failure').catch(()=>{});throw error;
}finally{await probe?.close().catch(()=>{});}
