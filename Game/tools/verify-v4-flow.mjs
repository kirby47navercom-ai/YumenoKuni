import {padSystemAction} from './v4-pad-test-input.mjs';
import {trialAimPlan} from './v4-aim-test-input.mjs';
import {bulletCycleKey} from './v4-bullet-test-input.mjs';
// Normal V4 route traversal using real inputs and actual evidence acquired along the path.
// DebugV4Chapter is used only once, as the entry point while title rollout is pending.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
assert.notEqual(JSON.parse(await fs.readFile(path.join(path.dirname(executable),'game.hbpack.json'),'utf8')).windowsRuntime,'native','This previous V4 runner requires WebView/CDP. The new backend uses native-window-probe.mjs; previous reports are not new-native acceptance.');
const work=path.join(root,'Saved/v4-flow-'+Date.now());await fs.mkdir(work,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const keys={ArrowLeft:[37,'ArrowLeft'],ArrowUp:[38,'ArrowUp'],ArrowRight:[39,'ArrowRight'],ArrowDown:[40,'ArrowDown'],Enter:[13,'Enter'],Space:[32,'Space'],Tab:[9,'Tab'],Backspace:[8,'Backspace'],Control:[17,'ControlLeft'],Shift:[16,'ShiftLeft'],w:[87,'KeyW'],s:[83,'KeyS'],a:[65,'KeyA'],d:[68,'KeyD'],q:[81,'KeyQ'],e:[69,'KeyE'],o:[79,'KeyO'],m:[77,'KeyM'],c:[67,'KeyC'],1:[49,'Digit1'],2:[50,'Digit2'],3:[51,'Digit3'],4:[52,'Digit4']};
const first=Number(process.argv[2]||0),last=Number(process.argv[3]||6);
const entryOnly=process.argv.includes('--entry-only');
const endingOnly=process.argv.includes('--ending-only');
const endingChoice=process.argv.find(a=>a.startsWith('--ending-choice='))?.split('=')[1];if(endingChoice)assert(['A','B'].includes(endingChoice));
let probe;const results=[];let debateOptions=[];process.env.HB_PLAYER_SOAK_HOURS='8';
const resume=process.env.V4_RESUME;if(resume){await fs.mkdir(path.join(work,'UserData'),{recursive:true});await fs.copyFile(path.resolve(resume),path.join(work,'UserData/savegames.json'));}
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);await delay(700);
 const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call("Driver",${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
 const stats=async()=>{const result=await call('Stats');if(typeof result?.outputs?.result!=='string')throw new Error('Stats unavailable: '+JSON.stringify(result));return JSON.parse(result.outputs.result);};
 const key=async(k,type)=>{const [windowsVirtualKeyCode,code]=keys[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k==='Space'?' ':k,code,windowsVirtualKeyCode});};
 const sampled=async(ms,frames=2)=>{const frame=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(ms);const start=Date.now();while((await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))<frame+frames){assert(Date.now()-start<10000,'player did not sample an input edge');await delay(16);}};
 const tap=async(k,ms=55,frames=2)=>{await key(k,'keyDown');await sampled(ms,frames);await key(k,'keyUp');await sampled(ms,frames);};
 const move=async(x,y,buttons=0)=>probe.cdp('Input.dispatchMouseEvent',{type:'mouseMoved',x,y,buttons,button:buttons?'left':'none'});
 const button=async(x,y,type)=>probe.cdp('Input.dispatchMouseEvent',{type,x,y,button:'left',buttons:type==='mousePressed'?1:0,clickCount:1});
 const click=async(x,y,ms=55)=>{await move(x,y);await button(x,y,'mousePressed');await sampled(ms);await button(x,y,'mouseReleased');await sampled(55);};
 // QA dialogue pacing is isolated from the original PC option kinds.
 await call('DebugFastRead'); // Explicit QA dialogue pacing; not a source option row or a played-path claim.
 if(resume)await tap('c',100);else await call('DebugV4Chapter',{index:first});await delay(1000);
 for(const k of ['c','Enter','Tab','Space'])await key(k,'keyUp');await delay(350);if(resume)assert((await stats()).node,'actual save did not restore');
 if(entryOnly||endingOnly){
  assert(resume,'focused restore requires an actual native save');const raw=JSON.parse(await fs.readFile(resume,'utf8')),head=Object.entries(raw.items).find(([k])=>k.includes('yumeno-progress-v4.project.'));assert(head);const saved=JSON.parse(head[1]),loaded=await stats();assert.equal(loaded.chapter,Number(saved.chapter==='P'?0:saved.chapter));assert.equal(loaded.node,saved.node);assert(!loaded.error);
  const graph=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/v4_story/chapters',saved.chapter+'.json'),'utf8')),savedTask=Object.entries(graph.taskNodes).find(([,node])=>node===saved.node)?.[0];
  const expectedMode=endingOnly?'credits':savedTask?'trial':'story';assert.equal(loaded.mode,expectedMode);if(savedTask)assert.equal(loaded.taskId,savedTask,'Continue must restore the persisted task, not merely show a trial background');
  let endingHUD;
  if(endingOnly){assert.equal(saved.chapter,'6');assert(saved.trialResults.best['6'].paid&&saved.trialResults.best['6'].complete);assert.equal(loaded.coins,saved.coins,'Continue must not pay the ending or trial reward again');
   endingHUD=await probe.evaluate(`Object.fromEntries(['FHud','FHudImg','FHudSub','FHudGauge','FLevelUp','FCredits'].map(n=>{const e=document.querySelector('[data-widget-name="'+n+'"]'),r=e?.getBoundingClientRect();return[n,!!r?.width&&!!r?.height&&getComputedStyle(e).visibility!=='hidden'&&getComputedStyle(e).display!=='none'];}))`);
   assert(endingHUD.FCredits,'credits text must be visible');for(const n of ['FHud','FHudImg','FHudSub','FHudGauge','FLevelUp'])assert(!endingHUD[n],n+' must not leak into credits');
   await fs.writeFile(path.join(work,'ending-hud.json'),JSON.stringify(endingHUD,null,2));
  }
  await probe.capture(endingOnly?'restored-ending.png':'restored-entry.png');assert.deepEqual(probe.errors,[]);const report={ok:true,entryOnly:!endingOnly,endingOnly,executable,work,resume,chapter:loaded.chapter,node:loaded.node,coins:loaded.coins,scope:endingOnly?'Fresh native Continue validates the normal saved ending parts and restores credits and the same wallet. No replay or task success injection.':'Fresh native player restores the exact persisted chapter/node through Continue. No chapter traversal or campaign acceptance.'};await fs.writeFile(path.join(work,'entry-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }else{
 await key('Control','keyDown');
 const start=Date.now(),visited=new Set(),tasks=new Set(),captured=new Set(),chapters=new Set(),savedChapters=new Set(),savedTasks=new Set();let activeTask='',taskStarted=0,focused=false,lastNode='',changedAt=Date.now(),steps=0,complete=false,lastReport=0,lastControl=0;let taskProgress=new Set(),endingChoiceTaken=false;
 const persistHead=async name=>{
  await key('Control','keyUp');await key('Shift','keyUp');focused=false;const original=(await stats()).mode;await tap('Tab',100);await click(1047,480,100);
  const pad=await stats();assert.equal(pad.mode,'pad');assert.equal(pad.padPage,5);const savedNode=pad.node,savedChapter=pad.chapter;assert(pad.padActions.includes('save'));await padSystemAction(stats,tap,'save');
  const checkpoint=path.join(work,name),storage=path.join(work,'UserData/savegames.json');let persisted=false;const writtenAt=Date.now();
  while(Date.now()-writtenAt<10000){try{const raw=JSON.parse(await fs.readFile(storage,'utf8')),head=Object.entries(raw.items).find(([k])=>k.includes('yumeno-progress-v4.project.'));if(head){const saved=JSON.parse(head[1]);persisted=saved.node===savedNode&&saved.chapter===(savedChapter===0?'P':String(savedChapter));if(persisted)break;}}catch{}await delay(100);}
  assert(persisted,'native saved head not persisted to exact checkpoint');await fs.copyFile(storage,checkpoint);await fs.copyFile(storage,path.join(work,'latest-savegames.json'));await fs.writeFile(path.join(work,'latest-save-point.json'),JSON.stringify({chapter:savedChapter,node:savedNode,taskId:pad.taskId||null,file:checkpoint,fixture:false,scope:'Actual normal-route native save; resume this point after interruptions, not the chapter start.'},null,2));
  debateOptions=[];
  if(pad.taskId){
   const raw=JSON.parse(await fs.readFile(storage,'utf8')),saved=JSON.parse(Object.entries(raw.items).find(([k])=>k.includes('yumeno-progress-v4.project.'))[1]);
   let hash=2166136261;for(const byte of Buffer.from(pad.taskId))hash=Math.imul(hash^byte,16777619)>>>0;const bucket=hash%64;
   const packed=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/v4_story/native_tasks/pack_'+(bucket%32)+'.json'),'utf8')),bundle=packed.buckets[bucket].tasks[pad.taskId];
   const local=bundle.scopeOnlyEvidence===true,stage=bundle.stage;
   debateOptions=(stage.options||[]).filter(o=>!stage.filterOwnedEvidence||Object.hasOwn(saved.evidence,o.id)||(local&&(bundle.requiresEvidence||[]).includes(o.id))).map(o=>o.id);
  }
  for(const k of ['Enter','Tab'])await key(k,'keyUp');await delay(800);await key('Tab','keyDown');const closedAt=Date.now();while((await stats()).mode==='pad'&&Date.now()-closedAt<5000)await delay(80);await key('Tab','keyUp');await delay(150);assert.equal((await stats()).mode,original);await key('Control','keyDown');return savedChapter;
 };
 while(steps++<500000&&Date.now()-start<6*3600000){
  // Another window can release held inputs. Reassert the same skip input;
  // this never changes the game's flags, choices, clock or save contents.
  if(Date.now()-lastControl>1000){await key('Control','keyDown');lastControl=Date.now();}
  let s=await stats();assert(!s.error,JSON.stringify(s));assert(!s.routeBlocked,JSON.stringify(s));
  if(endingChoice&&s.chapter===6&&s.v4Kind==='menu'&&!endingChoiceTaken){
   const graph=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/chapters/6.json'),'utf8')),n=graph.nodes[s.node];
   if(n?.selectionRole==='consciousness-support-decision'){
    await persistHead('ending-decision-savegames.json');await key('Control','keyUp');const target=n.options.findIndex(o=>o.id===endingChoice);assert(target>=0);for(let i=0;i<6&&(await stats()).choice.hover!==target;i++)await tap('s');assert.equal((await stats()).choice.hover,target);await tap('Enter');endingChoiceTaken=true;await probe.capture('ending-decision-selected-'+endingChoice+'.png');await key('Control','keyDown');continue;
   }
  }
  if(s.taskId&&!s.taskQueue&&s.taskInputArmed===false){for(const k of ['Enter','Space'])await key(k,'keyUp');await button(10,700,'mouseReleased');await sampled(40);continue;}
  if(s.mode==='credits'){complete=true;break;}
  // Chapter headers may first expose a stage or public document. Save that
  // actual Story head before a requested-range exit, rather than losing the
  // next chapter checkpoint while waiting for its first spoken line.
  if(!savedChapters.has(s.chapter)&&s.mode==='story'&&!s.taskId){
   savedChapters.add(await persistHead('chapter-'+s.chapter+'-savegames.json'));continue;
  }
  if(s.chapter>last){complete=true;break;}
  if(s.mode==='trial'&&s.taskId&&!s.taskQueue&&s.taskInputArmed&&!savedTasks.has(s.taskId)){await persistHead('task-'+s.taskId+'-savegames.json');savedTasks.add(s.taskId);continue;}
  chapters.add(s.chapter);visited.add(s.node);
  if(Date.now()-lastReport>20000){lastReport=Date.now();await fs.writeFile(path.join(work,'checkpoint.json'),JSON.stringify({chapter:s.chapter,node:s.node,kind:s.v4Kind,task:s.taskId,stageKind:s.stage?.kind,scrum:s.scrumV4,comic:s.comicV4,anagram:s.anagramV4,armament:s.armamentV4,seconds:(Date.now()-start)/1000,nodes:visited.size,tasks:results.length},null,2));}
  if(s.node!==lastNode){lastNode=s.node;changedAt=Date.now();taskProgress=new Set();}
  const progressKey=JSON.stringify([s.taskLink,s.trial?.broken,s.comicV4?.placed,s.scrumV4?.pair,s.scrumV4?.phase,s.scrumV4?.success,s.showdownV4?.group,s.showdownV4?.statement,s.armamentV4?.noteIndex,s.armamentV4?.opponent,s.armamentV4?.final,s.armamentV4?.order]);
  if(!taskProgress.has(progressKey)){taskProgress.add(progressKey);changedAt=Date.now();}
  assert(Date.now()-changedAt<300000,'STALL '+JSON.stringify(s));
  if(s.taskId!==activeTask){
   if(activeTask){const row={taskId:activeTask,seconds:(Date.now()-taskStarted)/1000,outcome:s.lastTaskOutcome};assert.equal(row.outcome?.taskId,activeTask);results.push(row);console.log(JSON.stringify(row));await fs.writeFile(path.join(work,'progress.json'),JSON.stringify({chapters:[...chapters],nodes:visited.size,results},null,2));}
   activeTask=s.taskId||'';taskStarted=Date.now();if(activeTask)tasks.add(activeTask);
  }
  const shot=s.mode==='trial'&&!s.taskId?'result-'+s.chapter:s.taskId?(s.taskQueue?'queue':s.stage?.kind):s.v4Kind==='say'?'story-'+s.chapter:s.v4Kind;
  if(!captured.has(shot)&&!s.presentation?.nonstopIntro){captured.add(shot);await probe.capture(String(captured.size)+'-'+shot+'.png');}
  if(s.v4Kind==='say'&&!s.taskId){await delay(100);continue;}
  if(s.taskQueue){await delay(80);continue;}
  const action=s.auto;
  if(action.kind==='debate'){
   const t=s.trial;
   if(!t||t.clearing||t.turning||t.shotRecovery?.ready===false||!['weak','agree'].includes(t.kind)||!t.weakPoint){if(focused){await key('Shift','keyUp');focused=false;}await delay(30);continue;}
   if(!focused){await key('Shift','keyDown');focused=true;await delay(50);continue;}
   if(t.bullet!==t.answer){await tap(bulletCycleKey(debateOptions,t.bullet,t.answer),30);continue;}
   const cursor=JSON.parse((await call('AimStats')).outputs.result),plan=trialAimPlan(t.weakPoint,cursor);if(plan.kind==='key'){await tap(plan.key,plan.ms);continue;}await click(...plan.point,t.needLie?Math.ceil((t.chargeRequired??.45)*1000)+100:40);
  }else{
   if(focused){await key('Shift','keyUp');focused=false;}
   if(action.kind==='key')await tap(action.key,35);
   else if(action.kind==='rapid-key'){
    // Keep physical20ms rhythm taps inside the live mash window. Frame
    // polling is per burst, not several debug roundtrips for every edge.
    if(s.stage?.kind==='armament'){
     // Schedule real DOM keyboard events through the unchanged player handler.
     // Each down/up spans one completed Update from an idle boundary, with no transport roundtrip
     // between the ten mash presses. This does not mutate gameplay state.
     const code=keys[action.key][1];
     await probe.evaluate(`(async()=>{const target=document.querySelector('canvas'),options={key:${JSON.stringify(action.key)},code:${JSON.stringify(code)},bubbles:true,cancelable:true};const yieldFrame=()=>new Promise(resolve=>setTimeout(resolve,2)),edge=async type=>{while(window.hbPlayerDebug.lifecycle().busy)await yieldFrame();const frame=window.hbPlayerDebug.lifecycle().frame;target.dispatchEvent(new KeyboardEvent(type,options));while(window.hbPlayerDebug.lifecycle().frame<frame+1||window.hbPlayerDebug.lifecycle().busy)await yieldFrame();};try{for(let i=0;i<10;i++){await edge('keydown');await edge('keyup');}}finally{target.dispatchEvent(new KeyboardEvent('keyup',options));}})()`);
    }
    else await tap(action.key,20);
   }
   else if(action.kind==='hold-key'){await key(action.key,'keyDown');await delay(action.seconds*1000);await key(action.key,'keyUp');await delay(40);}
   else if(action.kind==='release-after'){await key(action.key,'keyDown');await delay(Math.max(1,action.remaining*1000));await key(action.key,'keyUp');await delay(35);}
   else if(action.kind==='hold-target'){await key(action.key,'keyDown');await delay(action.seconds*1000);await click(action.x,action.y);await key(action.key,'keyUp');}
   else if(action.kind==='click')await click(action.x,action.y,40);
   else if(action.kind==='move'){await move(action.x,action.y);await delay(35);}
   else if(action.kind==='drag'||action.kind==='blade-drag'){
    // Long lines travel farther during CDP dispatch. Use a real full-width
    // horizontal stroke and the normal direction input, then sample both edges.
    const showdown=s.stage?.kind==='showdown',x0=showdown?20:action.x0,x1=showdown?1260:action.x1;
    if(showdown)await key('d','keyDown');if(action.kind==='blade-drag')await key('Space','keyDown');
    await move(x0,action.y);await button(x0,action.y,'mousePressed');await sampled(30);
    for(let i=1;i<=6;i++){await move(x0+(x1-x0)*i/6,action.y,1);await delay(18);}
    await button(x1,action.y,'mouseReleased');await sampled(40);
    if(action.kind==='blade-drag')await key('Space','keyUp');if(showdown)await key('d','keyUp');await delay(50);
   }
   else await delay(action.scale!==undefined?6:35);
  }
 }
 await key('Control','keyUp');await key('Shift','keyUp');assert(complete,'campaign did not reach the requested ending');
 await fs.writeFile(path.join(work,'visited.json'),JSON.stringify({chapters:[...chapters],tasks:[...tasks],nodes:[...visited]},null,2));
 const missing=await probe.evaluate('Array.from(document.images).filter(i=>i.offsetWidth>0&&i.src&&i.complete&&i.naturalWidth===0).map(i=>i.src)');assert.deepEqual(missing,[]);assert.deepEqual(probe.errors,[]);
 const endingState=await stats();if(endingChoice){assert(endingChoiceTaken);assert.equal(endingState.node,"v4:6:end:"+endingChoice);}const report={ok:true,executable,work,results,resume:resume||null,requestedChapters:[first,last],endedAtChapter:endingState.chapter,endingChoice:endingChoice||null,savedChapters:[...savedChapters],scope:'Normal authored V4 route for the requested chapter range, with actual acquired evidence and real input; dialogue used explicit DebugFastRead QA pacing and real Control input. A resume uses an actual prior native save. Not all branches, normal play duration, final choreography or listening acceptance.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({ok:true,work,tasks:results.length}));
 }
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,results,probeErrors:probe?.errors,ended:probe?.ended},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
