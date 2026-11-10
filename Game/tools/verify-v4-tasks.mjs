// Isolated authored input fixtures in our native game. Does not claim campaign traversal.
import fs from 'node:fs/promises';
import {trialAimPlan} from './v4-aim-test-input.mjs';
import {bulletCycleKey} from './v4-bullet-test-input.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/v4-tasks-'+Date.now());await fs.mkdir(work,{recursive:true});
const resume=process.env.V4_RESUME;if(resume){await fs.mkdir(path.join(work,'UserData'),{recursive:true});await fs.copyFile(path.resolve(resume),path.join(work,'UserData/savegames.json'));}
const resumeHead=resume?JSON.parse(Object.entries(JSON.parse(await fs.readFile(path.resolve(resume),'utf8')).items).find(([k])=>k.includes('yumeno-progress-v4.project.'))[1]):null;
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const keys={ArrowLeft:[37,'ArrowLeft'],ArrowUp:[38,'ArrowUp'],ArrowRight:[39,'ArrowRight'],ArrowDown:[40,'ArrowDown'],Enter:[13,'Enter'],Space:[32,'Space'],Tab:[9,'Tab'],Backspace:[8,'Backspace'],Control:[17,'ControlLeft'],Shift:[16,'ShiftLeft'],w:[87,'KeyW'],s:[83,'KeyS'],a:[65,'KeyA'],d:[68,'KeyD'],q:[81,'KeyQ'],e:[69,'KeyE'],o:[79,'KeyO'],c:[67,'KeyC'],1:[49,'Digit1'],2:[50,'Digit2'],3:[51,'Digit3'],4:[52,'Digit4']};
const fixtures=process.argv.slice(2);if(!fixtures.length){const source=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/native_tasks.json'),'utf8')).tasks;for(const kind of ['choice','bullet','person','spot','reasoning','nonstop','panic','showdown','mindmine','anagram','scrum','climax','armament','vote','lie']){const match=Object.entries(source).find(([id,t])=>id.startsWith('T1-')&&t.stage.kind===kind)||Object.entries(source).find(([,t])=>t.stage.kind===kind);assert(match,'missing fixture kind '+kind);fixtures.push(match[0]);}}
const compiled=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/native_tasks.json'),'utf8')).tasks;
const armSource=JSON.parse(await fs.readFile(path.join(root,'../docs/analysis/v3_rebuild/armament_rhythm_hud_followup.json'),'utf8'));
for(const fixture of fixtures)assert(compiled[fixture.split(':')[0]],'No authored task QA fixture: '+fixture);
if(resume)assert.equal(fixtures.length,1,'A real save may only resume its one exact focused task');
let probe;const results=[];process.env.HB_PLAYER_SOAK_HOURS='2';
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);await delay(700);await fs.writeFile(path.join(work,'driver-session.json'),JSON.stringify({base:probe.base,debuggingPort:probe.debuggingPort},null,2));
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
 if(resume){await tap('c',100);await probe.until(async()=>(await stats()).taskId===fixtures[0].split(':')[0],'saved native task restored',30000);}
 for(const fixture of fixtures){
  const [taskId,variant]=fixture.split(':');
  const bundle=compiled[taskId],stage=bundle.stage,debateOptions=resumeHead?(stage.options||[]).filter(o=>!stage.filterOwnedEvidence||Object.hasOwn(resumeHead.evidence,o.id)||(bundle.scopeOnlyEvidence===true&&(bundle.requiresEvidence||[]).includes(o.id))).map(o=>o.id):[];
  for(const k of ['Control','Shift','Space','w','d','s','a'])await key(k,'keyUp');
  if(!resume)await call('DebugV4Task',{taskId});await delay(250);let s=await stats();assert(!s.error,s.error);assert.equal(s.taskId,taskId);
  const armHud=async state=>{const names=['Hp','Mental','Boss'],keys=['health','mental','boss'],ids=['StatusPanel','StatusLabel','Heart0','Star0','SpkTag','StageTimer',...names.flatMap(n=>['ArmHud'+n,'ArmHud'+n+'Track']),...Array.from({length:20},(_,i)=>'ArmHudTension'+i)];const ui=await probe.evaluate(`(()=>Object.fromEntries(${JSON.stringify(ids)}.map(n=>{const e=document.querySelector('[data-widget-name="'+n+'"]'),r=e?.getBoundingClientRect(),im=e?.tagName==='IMG'?e:e?.querySelector('img');return[n,{x:r?.x,y:r?.y,w:r?.width,h:r?.height,visible:!!e&&r.width>0&&getComputedStyle(e).visibility!=='hidden',src:im?.src,loaded:!!im&&im.complete&&im.naturalWidth>0}];})))()`);const stable=await stats();if(stable.taskQueue||stable.armamentV4.noteIndex!==state.armamentV4.noteIndex||stable.armamentV4.final!==state.armamentV4.final||stable.armamentV4.tension!==state.armamentV4.tension||JSON.stringify(stable.armamentV4.hud)!==JSON.stringify(state.armamentV4.hud))return false;for(const n of ['StatusPanel','StatusLabel','Heart0','Star0','SpkTag'])assert(!ui[n].visible,'no generic status/name card in armament '+n);assert(ui.StageTimer.visible&&ui.StageTimer.x<100&&ui.StageTimer.y>620,'source observed lower-left time');for(let i=0;i<3;i++){const original=armSource[keys[i]].parts.fill.first_local_frame_leaves[0].own1280_rect_xywh;for(const suffix of ['', 'Track']){const q=ui['ArmHud'+names[i]+suffix];assert(q.visible&&q.loaded,'source gauge loads '+names[i]+suffix);assert([q.x,q.y,q.w,q.h].every((v,j)=>Math.abs(v-original[j])<2),'source composed gauge quad '+names[i]);}assert(ui['ArmHud'+names[i]].src.includes('arm_'+names[i]+'_'+state.armamentV4.hud[i]+'.svg'),'actual resource value drives visible gauge');}for(let i=0;i<20;i++){const q=ui['ArmHudTension'+i],t=state.armamentV4.tension,shown=(i%2===1&&i<t)||(t%2===1&&i===t-1);assert.equal(q.visible,shown,'source half/full tension pair '+i);if(shown){const r=armSource.tension.nodes[i].first_local_frame_leaves[0].own1280_rect_xywh;assert(q.loaded&&[q.x,q.y,q.w,q.h].every((v,j)=>Math.abs(v-r[j])<2),'individual source tension quad '+i);}}};
 const armCamera=state=>{const who=compiled[taskId].stage.opponent,seats=['mio','rin','ken','nana','taiga','ai','rei','sora','haruka','sho','koto','akari','riku','satsuki','yuu','kaede'],seat=seats.indexOf(who),c=state.presentation.camera;if(who==='lappy'){assert(Math.abs(c[0])<.02&&Math.abs(c[1]-2.05)<.02&&Math.abs(c[2]+.296)<.02&&Math.abs(c[4]-24)<.02,'host uses its actual throne framing');return;}assert(seat>=0);const angle=seat*Math.PI/8;assert(Math.abs(c[0]-1.28*Math.sin(angle))<.02&&Math.abs(c[1]-1.65)<.02&&Math.abs(c[2]-1.28*Math.cos(angle))<.02&&Math.abs(c[5])<.02,'rhythm and final input return to actual opponent after dialogue');};
 const node=s.node,start=Date.now(),armAnchors=new Set(),armNotes=new Set();let steps=0,focused=false,captured=false,wrongChecked=false,lanesChecked=false,layoutChecked=false,comicUiChecked=false,comicFilled=false,comicReview=false,scrumPushCaptured=false,anagramUiChecked=false,armUiChecked=false,armWrongRounds=0,armExhaustChecked=false;
 const noGenericStatus=async()=>assert(await probe.evaluate(`['StatusPanel','StatusLabel',...Array.from({length:10},(_,i)=>'Star'+i)].every(n=>{const e=document.querySelector('[data-widget-name="'+n+'"]');return !e||!e.getBoundingClientRect().width||getComputedStyle(e).visibility==='hidden';})`),'all generic vitals must hide together during feedback or custom HUD');
 const savePenalty=async expected=>{
  await key('Control','keyUp');await tap('Tab');assert.equal((await stats()).mode,'pad');await click(1047,480);assert.equal((await stats()).padPage,5);await padSystemAction(stats,tap,'save');
  const raw=JSON.parse(await fs.readFile(path.join(work,'UserData/savegames.json'),'utf8')),head=JSON.parse(Object.entries(raw.items).find(([k])=>k.includes('yumeno-progress-v4.project.'))[1]);assert.equal(head.node,node);assert.equal(head.trialResults.current.gaffe,expected);await fs.writeFile(path.join(work,taskId+'-wrong-feedback-savegames.json'),JSON.stringify(raw));
  await padSystemAction(stats,tap,'title');await padSystemAction(stats,tap,'title_yes');await tap('c');await probe.until(async()=>{const a=await stats();return a.node===node&&a.taskId===taskId&&a.mode==='trial';},'same task after real wrong-feedback save',30000);assert.equal(JSON.parse((await call('TrialResultStats')).outputs.result).ledger.current.gaffe,expected,'Continue preserves one gaffe without re-awarding it');await fs.writeFile(path.join(work,taskId+'-penalty-save.json'),JSON.stringify({gaffe:expected,node,continued:true,nativeManualSave:true},null,2));
 };
  await key('Control','keyDown');
  while(steps++<(variant==='exhaust'?9000:4500)&&Date.now()-start<(variant==='exhaust'?480000:240000)){
   s=await stats();assert(!s.error,`${taskId}: ${s.error}`);if(s.node!==node)break;
   if(s.scrumV4&&steps%10===0)await fs.writeFile(path.join(work,taskId+'-state.json'),JSON.stringify({steps,seconds:(Date.now()-start)/1000,inputArmed:s.taskInputArmed,scrum:s.scrumV4,auto:s.auto},null,2));
   if(!s.taskQueue&&s.taskInputArmed===false){for(const k of ['Enter','Space'])await key(k,'keyUp');await button(10,700,'mouseReleased');await sampled(40);continue;}
   if(!s.taskQueue&&s.armamentV4?.final<0&&armNotes.size<2&&!armNotes.has(s.armamentV4.noteIndex)){
    await delay(45);s=await stats();if(s.taskQueue||s.armamentV4.final>=0)continue;const index=s.armamentV4.noteIndex;armCamera(s);if(!armNotes.size)await armHud(s);
    const data=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/presentation/v3_armament_layout.json'),'utf8')),points=data.tracks[compiled[taskId].stage.chapter],point=points[index%points.length].map(n=>n*2/3);
    const geometry=await probe.evaluate(`(()=>{const names=['RingCore','ArmLine','ArmNoteKey','Hint'];return Object.fromEntries(names.map(n=>{const e=document.querySelector('[data-widget-name="'+n+'"]'),r=e?.getBoundingClientRect();return[n,{x:r?.x,y:r?.y,w:r?.width,h:r?.height,text:e?.textContent,visible:!!e&&r.width>0&&getComputedStyle(e).visibility!=='hidden'}];}));})()`);const afterGeometry=await stats();if(afterGeometry.armamentV4.noteIndex!==index||afterGeometry.taskQueue)continue;s=afterGeometry;
    assert(Math.abs(geometry.RingCore.x+geometry.RingCore.w/2-point[0])<2&&Math.abs(geometry.RingCore.y+geometry.RingCore.h/2-point[1])<2,'source chart anchor projects into the note');assert(Math.abs(geometry.ArmLine.x+geometry.ArmLine.w/2-point[0])<2&&Math.abs(geometry.ArmLine.y-Math.max(8,point[1]-128))<2,'claim follows this note');assert(geometry.ArmNoteKey.visible&&!geometry.Hint.visible);assert.equal(geometry.ArmNoteKey.text,['W','D','S','A'][s.armamentV4.button]);armNotes.add(index);armAnchors.add(point.join(','));if(armAnchors.size===2)await probe.capture(taskId+'-second-note-anchor.png');
   }
   if(!s.taskQueue&&s.armamentV4?.final>=0&&!armUiChecked){
    await key('Control','keyUp');await sampled(55);s=await stats();armCamera(s);await armHud(s);const armShot=taskId+(armWrongRounds?'-wrong-round-'+armWrongRounds:'');const initial=s.armamentV4,hp=initial.hp,retries=initial.retries,expected=compiled[taskId].stage.final;
    assert.deepEqual([...initial.choices].sort(),[...expected].sort(),'all four actual fragments together, no regenerated distractor rounds');
    const layout=await probe.evaluate(`(()=>{const names=['Piece0','Piece1','Piece2','Piece3','ArmPieceKey0','ArmPieceKey1','ArmPieceKey2','ArmPieceKey3','ArmPieceBand0','ArmPieceBand1','ArmPieceBand2','ArmPieceBand3','ArmLine','Ring','StageMsg'];return Object.fromEntries(names.map(n=>{const e=document.querySelector('[data-widget-name="'+n+'"]'),r=e?.getBoundingClientRect();return[n,{visible:!!e&&r.width>0&&getComputedStyle(e).visibility!=='hidden',x:r?.x,y:r?.y,w:r?.width,h:r?.height,text:e?.textContent}];}));})()`);
    await fs.writeFile(path.join(work,armShot+'-four-pieces-layout.json'),JSON.stringify(layout,null,2));for(let i=0;i<4;i++)assert(layout['Piece'+i].visible&&layout['ArmPieceKey'+i].visible);const sourceRects=[[485.6667,116.6667,308.6667,56],[852.9333,335,308.6823,56],[485.6667,552.6667,308.6667,56],[111.6667,334.6667,308.6667,56]];for(let i=0;i<4;i++){const b=layout['ArmPieceBand'+i],r=sourceRects[i];assert(b.visible&&[b.x,b.y,b.w,b.h].every((v,j)=>Math.abs(v-r[j])<2),'source final plate '+i);}const textOrigins=[[482.6333,125.7667],[843.4669,347.5667],[482.6333,561.7667],[115.3,343.7667]];for(let i=0;i<4;i++){const t=layout['Piece'+i];assert(Math.abs(t.x-textOrigins[i][0])<2&&Math.abs(t.y-textOrigins[i][1])<2,'source final text '+i);}assert(!layout.Ring.visible&&!layout.ArmLine.visible&&!layout.StageMsg.visible,'no old note or transient rating over final pieces');await probe.capture(armShot+'-four-pieces.png');
    const wrongOrder=[1,0,2,3],slots=wrongOrder.map(logical=>initial.layout.indexOf(logical));
    await tap(String(slots[0]+1));let q=await stats();assert.equal(q.armamentV4.selected,1);assert.equal(q.armamentV4.hp,hp);assert(!q.taskQueue,'wrong partial prefix is not judged');await tap(String(slots[0]+1));assert.equal((await stats()).armamentV4.selected,1,'a piece cannot be selected twice');
    await tap('Tab');const paused=(await stats()).armamentV4;assert.equal((await stats()).mode,'pad');await tap('Tab');assert.deepEqual((await stats()).armamentV4.order,paused.order);assert.equal((await stats()).armamentV4.selected,1,'modal return preserves actual selection');
    for(let n=1;n<3;n++){await tap(String(slots[n]+1));q=await stats();assert.equal(q.armamentV4.selected,n+1);assert.equal(q.armamentV4.hp,hp);assert(!q.taskQueue);}await probe.capture(armShot+'-three-pieces-no-judgment.png');
    const xy=[[640,144.6667],[1007.267,363],[640,580.6667],[266,362.6667]][slots[3]];await click(...xy);q=await stats();await fs.writeFile(path.join(work,armShot+'-fourth-input-state.json'),JSON.stringify({initial,after:q.armamentV4},null,2));assert.equal(q.armamentV4.final,4);assert.equal(q.armamentV4.hp,hp,'no damage before selection transition completes');assert(!q.armamentV4.settled);await tap('Tab');const transitioning=await stats();assert.equal(transitioning.mode,'pad');await delay(180);assert.equal((await stats()).armamentV4.transition,transitioning.armamentV4.transition,'selection transition pauses in Pad');await tap('Tab');await probe.capture(armShot+'-four-pieces-transition.png');await probe.until(async()=>(await stats()).armamentV4.final===-1,'whole wrong order resumes rhythm after transition',5000);q=await stats();assert(q.armamentV4.hp<hp||q.armamentV4.retries>retries,'whole wrong order damages HP or follows the existing exhausted-HP retry');assert.equal(q.node,node);await fs.writeFile(path.join(work,armShot+'-whole-wrong-outcome.json'),JSON.stringify({before:{hp,retries},after:q.armamentV4},null,2));if(q.armamentV4.retries>retries)for(const n of ['ArmQuestion','ArmJoined',...Array.from({length:4},(_,i)=>'ArmPieceKey'+i)])assert(await probe.evaluate(`(()=>{const e=document.querySelector('[data-widget-name="${n}"]'),r=e?.getBoundingClientRect();return !e||!r.width||getComputedStyle(e).visibility==='hidden';})()`),'no final phrase widget leaks into same-wave retry '+n);armWrongRounds++;armExhaustChecked ||= q.armamentV4.retries>retries;armUiChecked=variant!=='exhaust'||armExhaustChecked;await key('Control','keyDown');continue;
   }
   if(!s.taskQueue&&s.stage?.kind==='climax'&&s.comicV4?.placed===1&&!comicFilled){await probe.capture(taskId+'-filled.png');comicFilled=true;}
   if(!s.taskQueue&&s.stage?.kind==='climax'&&s.comicV4?.review&&!comicReview){await probe.capture(taskId+'-review.png');comicReview=true;}
   if(!s.taskQueue&&s.scrumV4?.mash>=0&&!scrumPushCaptured){await probe.capture(taskId+'-push.png');scrumPushCaptured=true;}
   if(!s.taskQueue&&!s.presentation?.nonstopIntro&&!captured){
    if(s.stage?.kind==='armament')assert(await probe.evaluate(`(()=>{const e=document.querySelector('[data-widget-name="AccFig"]'),f=document.querySelector('[data-widget-name="ArmFace"]'),i=f?.tagName==='IMG'?f:f?.querySelector('img');return (!e||e.getBoundingClientRect().width===0||getComputedStyle(e).visibility==='hidden')&&!!i&&getComputedStyle(i).objectFit==='contain';})()`),'only the approved world opponent, uncropped player cut-in');
    if(s.stage?.kind==='nonstop')assert(await probe.evaluate(`(()=>['StatusPanel','Heart0','Star0'].every(n=>{const e=document.querySelector('[data-widget-name="'+n+'"]'),r=e?.getBoundingClientRect();return !!e&&r.width>0&&getComputedStyle(e).visibility!=='hidden';}))()`),'ordinary debate HUD restored after armament');
    if(s.stage?.kind==='nonstop'||s.stage?.kind==='panic'){assert(await probe.evaluate(`(()=>{const e=document.querySelector('[data-widget-name="Aim"]');return !!e&&getComputedStyle(e).visibility!=='hidden';})()`),'debate aim restored after another mode');}
    if(s.stage?.kind==='panic'){await delay(2000);s=await stats();assert.equal(s.trial.lanes.length,3);assert(s.trial.lanes.every(l=>l.glyphs>0));assert(new Set(s.trial.lanes.map(l=>l.line)).size===3);lanesChecked=true;}
    if(s.stage?.kind==='showdown'){
     await delay(650);
     const layout=await probe.evaluate(`(()=>{const names=['SdLeft','SdRight','SdDivider','SdBladeFrame','BladeName','SpkName','StageMsg',...Array.from({length:8},(_,i)=>'OptP'+i)];return Object.fromEntries(names.map(n=>{const e=document.querySelector('[data-widget-name="'+n+'"]'),r=e?.getBoundingClientRect();return [n,{visible:!!e&&r.width>0&&getComputedStyle(e).visibility!=='hidden',x:r?.x,y:r?.y,w:r?.width,text:e?.textContent}];}));})()`);
     for(const name of ['SdLeft','SdRight','SdDivider','SdBladeFrame','BladeName','SpkName'])assert(layout[name].visible,'missing source-layout element '+name);
     assert(layout.BladeName.x<layout.SdDivider.x,'blade belongs at lower left');assert(layout.SpkName.y<100,'speaker belongs at upper left');assert(!layout.StageMsg.visible,'no centre numeric counter');
     for(let i=0;i<8;i++)assert(!layout['OptP'+i].visible,'right-hand card list removed');layoutChecked=true;
     await fs.writeFile(path.join(work,taskId+'-layout.json'),JSON.stringify(layout,null,2));
    }
    if(s.stage?.kind==='scrum'){
     if(s.scrumV4.entry<1){await probe.capture(taskId+'-start.png');const title=await probe.evaluate(`(()=>{const e=document.querySelector('[data-widget-name="ScBand"]');return e?.getAttribute('src')||e?.querySelector('img')?.src||'';})()`);assert(title.includes('scrum_start'),'provided Korean Scrum start title');}
     await delay(1250);s=await stats();assert(s.scrumV4.entry>=1);const selected=s.stage.selection,pair=s.scrumV4.pair,hp=s.trialHp;
     if(compiled[taskId].stage.pairs.length>1){await tap('s');let q=await stats();assert.notEqual(q.stage.selection,selected);assert.equal(q.scrumV4.pair,pair);assert.equal(q.trialHp,hp);assert(!q.taskQueue);await tap('w');assert.equal((await stats()).stage.selection,selected);}
     const layout=await probe.evaluate(`(()=>{const names=['ScVLP0','ScVRP0','ScVStatement',...Array.from({length:8},(_,i)=>'OptP'+i),'ScThemP','ScUsP'];return Object.fromEntries(names.map(n=>{const e=document.querySelector('[data-widget-name="'+n+'"]'),r=e?.getBoundingClientRect();return [n,{visible:!!e&&r.width>0&&getComputedStyle(e).visibility!=='hidden',x:r?.x,y:r?.y,w:r?.width,text:e?.textContent}];}));})()`);
     assert(layout.ScVLP0.visible&&layout.ScVRP0.visible&&layout.ScVStatement.visible);assert(layout.ScVLP0.x<0&&layout.ScVLP0.y>500);assert(layout.ScVRP0.x>700&&layout.ScVRP0.y>500);for(const id of ['ScThemP','ScUsP',...Array.from({length:8},(_,i)=>'OptP'+i)])assert(!layout[id].visible,'generic card remains '+id);
     await fs.writeFile(path.join(work,taskId+'-layout.json'),JSON.stringify(layout,null,2));layoutChecked=true;
    }
    if(s.stage?.kind==='anagram'){
     const layout=await probe.evaluate(`(()=>{const names=['AnaSlot0','AnaTime','AnaQuestion','AnaQuestionButton','AnaBackground','AnaSilhouette','AnaHeart0','AnaStar0','Question','QPlate','Slots'];return Object.fromEntries(names.map(n=>{const e=document.querySelector('[data-widget-name="'+n+'"]'),r=e?.getBoundingClientRect();return [n,{visible:!!e&&r.width>0&&getComputedStyle(e).visibility!=='hidden',x:r?.x,y:r?.y,w:r?.width,h:r?.height}];}));})()`);
     assert(layout.AnaSlot0.visible&&layout.AnaSlot0.y<100&&layout.AnaSlot0.x<100);assert(layout.AnaTime.visible&&layout.AnaTime.x<200&&layout.AnaTime.y>620);assert(layout.AnaBackground.visible&&layout.AnaSilhouette.visible&&layout.AnaHeart0.visible&&layout.AnaStar0.visible);for(const id of ['Question','QPlate','Slots'])assert(!layout[id].visible,'old question/answer panel remains '+id);
     if(compiled[taskId].stage.question){
      await key('Control','keyUp');await tap('q');let q=await stats();assert(q.anagramV4.question,'new press opens the question');await delay(450);let still=await stats();assert(still.anagramV4.question,'key release does not close a toggle');assert(still.anagramV4.time>q.anagramV4.time,'question does not pause time');assert.notDeepEqual(still.anagramV4.orb0,q.anagramV4.orb0,'question does not freeze spheres');assert.notEqual(still.anagramV4.light,q.anagramV4.light,'automatic wave continues');assert.equal(still.anagramV4.filled,q.anagramV4.filled);await probe.capture(taskId+'-question.png');await tap('q');assert(!(await stats()).anagramV4.question);await key('Control','keyDown');
     }
     await key('Control','keyUp');const beforePad=(await stats()).anagramV4;await tap('Tab');let padState=await stats();assert.equal(padState.mode,'pad');assert(await probe.evaluate(`(()=>{const e=document.querySelector('[data-widget-name="PdFloor"]');return !!e&&e.getBoundingClientRect().width>0&&getComputedStyle(e).visibility!=='hidden';})()`),'Pad is visible over the minigame');assert(await probe.evaluate(`(()=>{const e=document.querySelector('[data-widget-name="AnaBackground"]');return !e||e.getBoundingClientRect().width===0||getComputedStyle(e).visibility==='hidden';})()`),'opaque anagram cannot cover Pad');await probe.capture(taskId+'-pad.png');await delay(180);let paused=(await stats()).anagramV4;assert.equal(paused.time,padState.anagramV4.time,'menu time is excluded from minigame clock');assert.equal(paused.focus,padState.anagramV4.focus);await tap('Tab');let resumed=(await stats());assert.equal(resumed.mode,'trial');assert.equal(resumed.anagramV4.filled,beforePad.filled);assert.equal(resumed.anagramV4.hp,beforePad.hp);
     const beforeLight=resumed.anagramV4;
     await probe.cdp('Input.dispatchMouseEvent',{type:'mousePressed',x:640,y:360,button:'right',clickCount:1});await sampled(250);let spotState=(await stats()).anagramV4;
     assert.equal(spotState.lightMode,6,'right mouse admits the manual spot alone');assert(spotState.spotRadius>200*2/3&&spotState.spotRadius<600*2/3);assert(spotState.focus<beforeLight.focus,'manual spot consumes the shared mental resource');await probe.capture(taskId+'-spot.png');
     await probe.cdp('Input.dispatchMouseEvent',{type:'mouseReleased',x:640,y:360,button:'right',clickCount:1});await sampled(250);assert.equal((await stats()).anagramV4.lightMode,5);
     await key('Shift','keyDown');await sampled(180);const focusState=(await stats()).anagramV4;assert.equal(focusState.lightMode,7,'focus does not implicitly create a spot');assert.equal(focusState.spotRadius,0);await probe.capture(taskId+'-focus.png');await key('Shift','keyUp');await sampled(80);assert.equal((await stats()).anagramV4.lightMode,5);await key('Control','keyDown');
     anagramUiChecked=true;await fs.writeFile(path.join(work,taskId+'-layout.json'),JSON.stringify({...layout,lightInput:{beforeLight,spotState,focusState}},null,2));
    }
    await probe.capture(taskId+'.png');captured=true;
    if(s.stage?.kind==='climax'){
     await key('Control','keyUp');await noGenericStatus();await tap('d');let c=await stats();assert.equal(c.comicV4.placed,0,'stock selection must not place');assert(!c.taskQueue);
     await key('Space','keyDown');await delay(120);assert((await stats()).comicV4.zoom);await probe.capture(taskId+'-zoom.png');await tap('Enter');assert.equal((await stats()).comicV4.placed,0,'cannot place during held zoom');await key('Space','keyUp');await delay(80);assert(!(await stats()).comicV4.zoom);
     await tap('e');assert.equal((await stats()).comicV4.spread,1,'page forward');await probe.capture(taskId+'-next-page.png');await tap('q');assert.equal((await stats()).comicV4.spread,0,'page back');
     const first=compiled[taskId].stage.slots[0],answer=first.options.findIndex(o=>o.id===first.answer),wrong=answer===0?1:0;while((await stats()).comicV4.stock!==wrong)await tap('d');
     const beforePenalty=JSON.parse((await call('TrialResultStats')).outputs.result).ledger.current.gaffe;
     const beforeHp=(await stats()).trialHp;await click(359,273);c=await stats();assert(c.comicV4.placing,'placement has a visible flight before judgment');assert.equal(c.comicV4.placed,0);assert.equal(c.trialHp,beforeHp,'no damage before placement settles');await probe.capture(taskId+'-placing.png');
     const settling=Date.now();while(!(c=await stats()).taskQueue&&Date.now()-settling<2500)await delay(25);assert(c.taskQueue,'actual authored wrong placement response after flight');assert.equal(c.comicV4.placed,0,'wrong placement leaves holes empty');assert.equal(JSON.parse((await call('TrialResultStats')).outputs.result).ledger.current.gaffe,beforePenalty+1,'comic authored wrong response charges one gaffe');await noGenericStatus();await probe.capture(taskId+'-wrong-feedback.png');comicUiChecked=true;if(variant==='penalty')await savePenalty(beforePenalty+1);await key('Control','keyDown');
    }
   }
   if(!wrongChecked&&variant==='penalty'&&s.stage?.kind==='reasoning'&&!s.taskQueue){
    await key('Control','keyUp');const beforePenalty=JSON.parse((await call('TrialResultStats')).outputs.result).ledger.current.gaffe,beforeHp=s.trialHp,link=s.taskLink;
    const q=compiled[taskId].stage.questions[link],right=q.options.indexOf(q.answer),wrong=right===0?1:0;
    while((await stats()).stage.selection!==wrong)await tap('s');await tap('Enter');const qstate=await stats();assert.equal(qstate.node,node);assert.equal(qstate.taskLink,link);assert(qstate.trialHp<beforeHp);assert(qstate.taskQueue,'existing authored fallback or option-specific wrong dialogue must play');assert.equal(JSON.parse((await call('TrialResultStats')).outputs.result).ledger.current.gaffe,beforePenalty+1);
    await delay(250);assert.equal(JSON.parse((await call('TrialResultStats')).outputs.result).ledger.current.gaffe,beforePenalty+1,'displayed feedback never charges twice');await noGenericStatus();await probe.capture(taskId+'-wrong-feedback.png');await fs.writeFile(path.join(work,taskId+'-wrong-penalty.json'),JSON.stringify({beforePenalty,afterPenalty:beforePenalty+1,beforeHp,afterHp:qstate.trialHp,link,wrong},null,2));wrongChecked=true;await key('Control','keyDown');continue;
   }
   if(!wrongChecked&&taskId==='T1-ANSWER-A01'&&!s.taskQueue){
    await tap('Enter');let q=await stats();assert(q.taskQueue,'actual wrong dialogue');assert.equal(q.node,node);wrongChecked=true;continue;
   }
   if(s.taskQueue){await tap('Enter',35);continue;}
   const action=s.auto;
   if(action.kind==='debate'){
    const t=s.trial;
    if(!t||t.clearing||t.turning||t.shotRecovery?.ready===false||!['weak','agree'].includes(t.kind)||!t.weakPoint){if(focused){await key('Shift','keyUp');focused=false;}await delay(35);continue;}
    if(variant==='B'){
     const alternate=compiled[taskId].debate.lines[t.index]?.lieWeak;if(!alternate){await delay(35);continue;}
     if(t.bullet!==alternate.answer){await tap(resumeHead?bulletCycleKey(debateOptions,t.bullet,alternate.answer):'e',35);continue;}
     if(!focused){await key('Shift','keyDown');focused=true;await delay(60);continue;}
     const plan=trialAimPlan(t.weakPoint,JSON.parse((await call('AimStats')).outputs.result));if(plan.kind==='key'){await tap(plan.key,plan.ms);continue;}await move(...plan.point);await button(...plan.point,'mousePressed');await probe.until(async()=>{const q=await stats();return q.trial?.lie||q.taskQueue||q.node!==node;},'held lie conversion observed',6000);
     const charged=(await stats()).trial;assert(charged?.lie,'held conversion must actually be active');
     if(charged.index===t.index&&charged.weakPoint){const cursor=JSON.parse((await call('AimStats')).outputs.result),plan=trialAimPlan(charged.weakPoint,cursor);if(plan.kind==='key'){await tap(plan.key,plan.ms);await button(...cursor.physical,'mouseReleased');}else{await move(...plan.point,1);await button(...plan.point,'mouseReleased');}}
     else{await move(10,700,1);await button(10,700,'mouseReleased');}
     await delay(70);continue;
    }
    if(t.bullet!==t.answer){await tap(resumeHead?bulletCycleKey(debateOptions,t.bullet,t.answer):'e',35);continue;}
    if(!focused){await key('Shift','keyDown');focused=true;await delay(60);continue;}
    const cursor=JSON.parse((await call('AimStats')).outputs.result),plan=trialAimPlan(t.weakPoint,cursor);if(plan.kind==='key'){await tap(plan.key,plan.ms);continue;}await click(...plan.point,t.needLie?Math.ceil((t.chargeRequired??.45)*1000)+100:40);
   }else{
    if(focused){await key('Shift','keyUp');focused=false;}
    if(action.kind==='key')await tap(action.key,35);
    else if(action.kind==='rapid-key'){if(s.stage?.kind==='armament'){
     // Schedule real DOM keyboard events through the unchanged player handler.
     // Each down/up spans one completed Update from an idle boundary, with no transport roundtrip
     // between the ten mash presses. This does not mutate gameplay state.
     const code=keys[action.key][1];
     await probe.evaluate(`(async()=>{const target=document.querySelector('canvas'),options={key:${JSON.stringify(action.key)},code:${JSON.stringify(code)},bubbles:true,cancelable:true};const yieldFrame=()=>new Promise(resolve=>setTimeout(resolve,2)),edge=async type=>{while(window.hbPlayerDebug.lifecycle().busy)await yieldFrame();const frame=window.hbPlayerDebug.lifecycle().frame;target.dispatchEvent(new KeyboardEvent(type,options));while(window.hbPlayerDebug.lifecycle().frame<frame+1||window.hbPlayerDebug.lifecycle().busy)await yieldFrame();};try{for(let i=0;i<10;i++){await edge('keydown');await edge('keyup');}}finally{target.dispatchEvent(new KeyboardEvent('keyup',options));}})()`);
    }else await tap(action.key,20);}
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
  await key('Control','keyUp');await key('Shift','keyUp');s=await stats();assert.notEqual(s.node,node,`stalled ${taskId}: ${JSON.stringify(s)}`);assert(!s.error,s.error);
  if(compiled[taskId].stage.kind==='armament'){assert(armUiChecked,'complete four-piece UI checks');assert(armAnchors.size>=2,'different actual note anchors observed');if(variant==='exhaust')assert(armExhaustChecked,'a final whole-wrong order must cause a new exhausted-HP retry in this fixture');}
  if(variant==='penalty'&&compiled[taskId].stage.kind==='reasoning')assert(wrongChecked,'actual wrong reasoning input must be observed');
  if(variant==='B'){assert.equal(s.lastTaskOutcome?.judgment,'lie');assert.equal(s.lastTaskOutcome?.taskId,taskId);assert(Object.keys(s.lastTaskOutcome.sets).length>0);}
  const row={taskId,variant:variant||'normal',outcome:s.lastTaskOutcome,steps,seconds:(Date.now()-start)/1000,wrongChecked,lanesChecked,layoutChecked,comicUiChecked,comicFilled,comicReview,scrumPushCaptured,anagramUiChecked,armUiChecked,armWrongRounds,armExhaustChecked,armAnchors:[...armAnchors],nodeChanged:true,captured};results.push(row);console.log(JSON.stringify(row));await fs.writeFile(path.join(work,'progress.json'),JSON.stringify(results,null,2));
 }
 const missing=await probe.evaluate('Array.from(document.images).filter(i=>i.offsetWidth>0&&i.src&&i.complete&&i.naturalWidth===0).map(i=>i.src)');assert.deepEqual(missing,[]);assert.deepEqual(probe.errors,[]);
 const report={ok:true,executable,work,results,resume:resume||null,fixture:!resume,scope:resume?'Actual saved native task resumed through Continue and resolved by ordinary input; no task/evidence/HP fixture injection. Focused task only, not campaign traversal or every branch.':'Actual native authored input fixtures and exact result routing. Does not accept the unplayed campaign, every branch, final choreography, hearing or image gates.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({ok:true,work,fixtures:results.length}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,results,probeErrors:probe?.errors,ended:probe?.ended},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
