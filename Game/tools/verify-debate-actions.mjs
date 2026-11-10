// Actual mouse/key tests. Authored routes and isolated fixture routes are labelled separately.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const built=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/debate-actions-'+Date.now());await fs.mkdir(work,{recursive:true});
const wait=ms=>new Promise(r=>setTimeout(r,ms));const checks=[],cases=[];let probe;
const record=process.env.HB_DEBATE_RECORD==='1';
const profileMode=process.env.HB_DEBATE_PROFILE==='1';assert(!(record&&profileMode),'Record and uncaptured performance measurements are separate runs.');
const suppressUi=profileMode&&process.env.HB_DEBATE_SUPPRESS_UI==='1';
process.env.HB_PLAYER_SOAK_HOURS='1';
async function run(key,entries){
 await fs.mkdir(path.join(work,key),{recursive:true});
 probe=await editorWindowProbe({work:path.join(work,key),mode:'player',executable:built.executable});
 let socket,send,recorded=[];
 try{
  await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
  if(suppressUi)await probe.evaluate(`(()=>{const p=window.hbPlayerDebug.runtimePrototype(),original=p.applyNativeOperations;p.applyNativeOperations=function(ops,b){return original.call(this,window.__suppressOutcomeUi?ops.filter(o=>!o.key.startsWith('uiSet')):ops,b);};})()`);
  if(profileMode&&process.env.HB_DEBATE_DIAG==='1')await probe.evaluate(`(()=>{const p=window.hbPlayerDebug.runtimePrototype(),original=p.applyNativeOperations;window.__outcomeOps=[];p.applyNativeOperations=async function(ops,b){const start=performance.now();try{return await original.call(this,ops,b);}finally{if(window.__outcomeStart&&window.__outcomeOps.length<1000)window.__outcomeOps.push({at:start-window.__outcomeStart,ms:performance.now()-start,keys:ops.map(o=>o.key),workerMs:this.nativeTiming?.workerMs,rpcMs:this.nativeTiming?.rpcMs});}};})()`);
  const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
  const stats=async()=>{const s=JSON.parse((await call('Stats')).outputs.result);assert(!s.error,s.error);return s;};
  const keyboard=(k,down)=>probe.cdp('Input.dispatchKeyEvent',{type:down?'keyDown':'keyUp',key:k,code:k==='Shift'?'ShiftLeft':'Key'+k.toUpperCase(),windowsVirtualKeyCode:k==='Shift'?16:k.toUpperCase().charCodeAt(0)});
  const tap=async k=>{await keyboard(k,true);await wait(65);await keyboard(k,false);await wait(65);};
  const mouse=(type,x=640,y=360,button='left')=>probe.cdp('Input.dispatchMouseEvent',{type,x,y,button,clickCount:1});
  const fxState=async()=>JSON.parse((await call('FxStats')).outputs.result);
  const plane=name=>name.startsWith('Result')&&!['ResultRoot','ResultClaim'].includes(name);
  const visible=async name=>plane(name)?!!(await fxState())[name]?.visible:probe.evaluate(`(()=>{let e=document.querySelector('[data-widget-name="${name}"]');return !!e&&e.getBoundingClientRect().width>0&&getComputedStyle(e).visibility!=='hidden';})()`);
  const until=async(pred,label,ms=20000)=>{const end=Date.now()+ms;while(Date.now()<end){let s=await stats();if(pred(s))return s;await wait(45);}throw Error('Timeout: '+label);};
  await tap(key);assert.equal((await stats()).mode,'trial');
  if(record&&key==='t'){
   const targets=await(await fetch(`http://127.0.0.1:${probe.debuggingPort}/json/list`)).json(),target=targets.find(t=>t.type==='page'&&new URL(t.url).origin===probe.base);assert(target);
   socket=new WebSocket(target.webSocketDebuggerUrl);await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j;});
   let serial=0;const pending=new Map();
   send=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
   socket.onmessage=({data})=>{const m=JSON.parse(data);if(m.id){const p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);}return;}if(m.method==='Page.screencastFrame'){const p=m.params;socket.send(JSON.stringify({id:++serial,method:'Page.screencastFrameAck',params:{sessionId:p.sessionId}}));recorded.push({timestamp:p.metadata.timestamp,bytes:Buffer.from(p.data,'base64')});}};
   await send('Page.enable');
  }
  for(const entry of entries){
   console.log('case',entry.name);
   await keyboard('Shift',false);await mouse('mouseReleased');
   await call('DebugJump',{index:entry.stage});
   await until(s=>!s.presentation.nonstopIntro&&s.trial&&!s.trial.turning&&s.presentation.inputArmed,'entry');
   if(entry.fixture!==undefined)await call('DebugDebateFixture',{outcome:entry.fixture});
   if(entry.measureFocus){
    let a=await stats();await wait(350);let b=await stats();
    await keyboard('Shift',true);let c=await stats();await wait(700);let d=await stats();
    const normalRate=(a.presentation.timer-b.presentation.timer)/.35,slowRate=(c.presentation.timer-d.presentation.timer)/.7;
    if(a.trial.index===b.trial.index&&c.trial.index===d.trial.index){
     const normalStatement=(b.presentation.statementTime-a.presentation.statementTime)/.35,slowStatement=(d.presentation.statementTime-c.presentation.statementTime)/.7;
     assert(slowStatement<normalStatement*.65,{normalStatement,slowStatement});
    }
    assert(d.trial.focus<c.trial.focus-12);assert(await visible('FocusVeil'));
    assert(slowRate<normalRate*.65,{normalRate,slowRate});
    await probe.capture(entry.name+'-focus.png');await keyboard('Shift',false);const recoverStart=await stats();await wait(500);
    const recovered=await stats();assert(recovered.trial.focus>recoverStart.trial.focus+2,{recoverStart:recoverStart.trial.focus,recovered:recovered.trial.focus});assert.equal(await visible('FocusVeil'),false);
    checks.push({name:entry.name+' focus slows timer / drains / recovers',normalRate,slowRate});
   }
   if(entry.exhaust){
    await keyboard('Shift',true);await until(s=>s.trial.focusExhausted,'focus exhausted',6000);await wait(500);
    assert.equal(await visible('FocusVeil'),false,'held depleted focus stays off until release');
    await keyboard('Shift',false);await wait(450);await keyboard('Shift',true);await wait(90);
    assert.equal(await visible('FocusVeil'),true);await keyboard('Shift',false);checks.push({name:'depleted focus release/rearm'});
   }
   let before=await until(s=>s.trial?.kind===entry.target&&s.trial.answer&&s.trial.weakPoint&&!s.trial.turning&&s.presentation.statementTime>2.1,'settled target',45000);
   const wanted=before.trial.answer;
   for(let i=0;i<6&&(await stats()).trial.bullet!==wanted;i++)await tap('e');
   assert.equal((await stats()).trial.bullet,wanted);
   if(entry.wrong){await tap('e');before=await stats();}
   await keyboard('Shift',true);await wait(90);
   before=await until(s=>s.trial?.kind===entry.target&&s.trial.weakPoint&&!s.trial.turning,'aim');
   let [x,y]=before.trial.weakPoint;
   // Clear only noise genuinely intersecting this target through its actual silencer input.
   await mouse('mousePressed',x,y,'right');await wait(35);await mouse('mouseReleased',x,y,'right');
   if(send){recorded=[];await send('Page.startScreencast',{format:'jpeg',quality:85,maxWidth:960,maxHeight:540,everyNthFrame:1});}
   await mouse('mouseMoved',x,y);await mouse('mousePressed',x,y);
   if(entry.lie){
    const end=Date.now()+620;
    while(Date.now()<end){let s=await stats();if(s.trial?.weakPoint){[x,y]=s.trial.weakPoint;await mouse('mouseMoved',x,y);}await wait(25);}
    const charged=await stats();assert(charged.trial.lie);assert(charged.trial.hearts<=before.trial.hearts);
    assert(await visible('ChargeRing'));await probe.capture(entry.name+'-charged.png');
   }else await wait(45);
   let current=await stats();if(current.trial?.weakPoint)[x,y]=current.trial.weakPoint;
   await mouse('mousePressed',x,y,'right');await wait(30);await mouse('mouseReleased',x,y,'right');
   current=await stats();if(current.trial?.weakPoint)[x,y]=current.trial.weakPoint;
   await mouse('mouseMoved',x,y);await mouse('mouseReleased',x,y);await wait(65);
   const after=await stats(),observedAt=Date.now()/1000;await fs.writeFile(path.join(work,key,entry.name+'-attempt.json'),JSON.stringify({before,current,after},null,2));assert(after.trial.shots>before.trial.shots,'release fired an actual round');
   if(entry.wrong){assert.equal(after.trial.broken,before.trial.broken);assert(after.trial.hearts<before.trial.hearts);assert.equal(after.trial.result,'');checks.push({name:entry.name+' incorrect answer rejected'});}
   else{
    assert.equal(after.trial.result,entry.outcome);assert(after.trial.broken>before.trial.broken);assert(after.trial.resultTime>0);
    if(profileMode){
     await probe.evaluate(`window.__suppressOutcomeUi=${suppressUi};window.__outcomeOps=[];window.__outcomeStart=performance.now();window.hbPlayerDebug.resetProfile()`);
     await wait(5900); // No screenshot, stats polling, screencast or other player during this window.
     const profile=await probe.evaluate('window.hbPlayerDebug.profile()');
     await probe.evaluate('window.__suppressOutcomeUi=false');
     if(process.env.HB_DEBATE_DIAG==='1')await fs.writeFile(path.join(work,entry.outcome+'-operations.json'),JSON.stringify(await probe.evaluate('({operations:window.__outcomeOps})')));
     cases.push({name:entry.name,mode:entry.mode,source:'authored trial route',outcome:entry.outcome,diagnosticSuppressedUi:suppressUi,profile});
     await keyboard('Shift',false);await mouse('mouseReleased');continue;
    }
    assert(await visible('ResultRoot'));assert.equal(await visible('Cutin'),false);
    const texture=(await fxState()).ResultWord.texture;
    assert(texture.includes('result_'+entry.outcome+'_glyph0.svg'));
    await probe.capture(entry.name+'-success.png');
    const a=await stats();await wait(300);const b=await stats();assert.equal(a.presentation.timer,b.presentation.timer,'success pauses the limit');assert.equal(a.presentation.statementTime,b.presentation.statementTime,'success pauses testimony');
    if(entry.lie)assert(after.trial.hearts>=before.trial.hearts,'correct perjury returns wager');
    cases.push({name:entry.name,mode:entry.mode,source:entry.fixture===undefined?'authored trial route':'isolated QA fixture: first target rule changed in memory only',outcome:entry.outcome,before,after,screenshot:path.join(key,entry.name+'-success.png')});
    await until(s=>s.trial.resultTime<4.1,'main cutin');
    assert(await visible('ResultBand'));assert(await visible('ResultWord'));assert(await visible('ResultHero'));
    assert.equal(await visible('ResultPartner'),entry.outcome==='agree');
    const cutinPlanes=await fxState();
    for(const id of ['ResultHero','ResultWord','ResultWord2',...(entry.outcome==='agree'?['ResultPartner']:[])]){
     const [left,top,right,bottom]=cutinPlanes[id].bounds;
     assert(left>=11.9&&top>=11.9&&right<=1268.1&&bottom<=708.1,`${entry.name} ${id} complete pose/glyph within safe frame: ${JSON.stringify(cutinPlanes[id].bounds)}`);
    }
    cases.at(-1).cutinBounds={hero:cutinPlanes.ResultHero.bounds,...(entry.outcome==='agree'?{partner:cutinPlanes.ResultPartner.bounds}:{})};
    if(entry.outcome==='agree'){
     const partner=(await fxState()).ResultPartner.texture;
     const slug=after.portrait.match(/sprites\/([^/]+)\//)?.[1];assert(slug&&partner.includes('partner_'+slug+'.webp'),'agreement uses the actual speaker portrait');
    }
    await probe.capture(entry.name+'-cutin.png');
    await until(s=>s.trial.resultTime<2.5,'crack or ink');
    assert(await visible(entry.outcome==='lie'?'ResultInk':'ResultCrack'));
    await probe.capture(entry.name+'-transition.png');
    await until(s=>s.trial.resultTime<1.4,'Break');assert(await visible('ResultBreak0'));
    await probe.capture(entry.name+'-break.png');
    await until(s=>s.trial.resultTime===0,'complete success sequence');assert.equal(await visible('ResultRoot'),false);assert(Object.values(await fxState()).every(n=>!n.visible));
    if(send){
     await send('Page.stopScreencast');
     // Retain the complete actual presentation for QA. Public preview omits the initial claim.
     const start=observedAt-(5.8-after.trial.resultTime);
     const frames=recorded.filter(f=>f.timestamp>=start&&f.timestamp<start+5.8);assert(frames.length>60);
     const folder=path.join(work,'media',entry.outcome);await fs.mkdir(folder,{recursive:true});const listing=['ffconcat version 1.0'],rows=[];
     for(let i=0;i<frames.length;i++){const file=`frame-${String(i).padStart(4,'0')}.jpg`;await fs.writeFile(path.join(folder,file),frames[i].bytes);listing.push(`file '${file}'`,`duration ${Math.max(.001,(frames[i+1]?.timestamp??frames[i].timestamp+1/60)-frames[i].timestamp).toFixed(6)}`);rows.push({file,elapsed:frames[i].timestamp-start});}
     listing.push(`file '${rows.at(-1).file}'`);await fs.writeFile(path.join(folder,'frames.ffconcat'),listing.join('\n')+'\n');await fs.writeFile(path.join(folder,'capture.json'),JSON.stringify({source:'actual own-game compositor frames; cropped to success time, no motion interpolation',frames:rows},null,2));
    }
   }
   await keyboard('Shift',false);await mouse('mouseReleased');
  }
  if(profileMode){assert.equal(probe.errors.length,0);return;}
  // Leaving a charged shot must not leave a hidden result or a latched charge in another stage.
  await call('DebugJump',{index:entries[0].stage});await until(s=>!s.presentation.nonstopIntro&&s.presentation.inputArmed,'reentry');
  await mouse('mousePressed');await wait(540);assert((await stats()).trial.lie);
  await call('DebugJump',{index:entries[0].stage});await mouse('mouseReleased');await keyboard('Shift',false);
  assert.equal(await visible('ChargeRing'),false);assert.equal(await visible('ResultRoot'),false);assert(Object.values(await fxState()).every(n=>!n.visible));
  const s=await stats();assert.equal(s.trial.charge,-1);assert.equal(s.trial.shots,0);
  // Interrupt a real successful cutin, then re-enter: no stale HUD, camera lock or result layers.
  await until(s=>!s.presentation.nonstopIntro&&s.presentation.inputArmed,'cutin interruption entry');
  const target=await until(s=>s.trial.kind==='weak'&&!s.trial.needLie&&s.trial.weakPoint&&!s.trial.turning&&s.presentation.statementTime>2.1,'interrupt target',45000);
  for(let i=0;i<6&&(await stats()).trial.bullet!==target.trial.answer;i++)await tap('e');
  await keyboard('Shift',true);await wait(80);let a=await stats();let [x,y]=a.trial.weakPoint;
  await mouse('mousePressed',x,y,'right');await wait(30);await mouse('mouseReleased',x,y,'right');
  await mouse('mousePressed',x,y);await wait(45);a=await stats();[x,y]=a.trial.weakPoint;await mouse('mouseMoved',x,y);await mouse('mouseReleased',x,y);
  await until(s=>s.trial.resultTime>0,'interrupt actual result');await until(s=>s.trial.resultTime<4.1,'interrupt main cutin');
  assert(await visible('ResultHero'));await probe.capture('interrupted-cutin.png');await call('DebugJump',{index:0});
  assert.equal(await visible('ResultRoot'),false);assert(Object.values(await fxState()).every(n=>!n.visible));assert.equal(await visible('FocusVeil'),false);assert.equal(await visible('ChargeRing'),false);
  await keyboard('Shift',false);await mouse('mouseReleased');await call('DebugJump',{index:entries[0].stage});
  const restored=await until(s=>!s.presentation.nonstopIntro&&s.presentation.inputArmed,'after cutin interruption');
  assert.equal(restored.trial.resultTime,0);assert.equal(restored.trial.shots,0);assert(await visible('Trial'));
  checks.push({name:key+' actual successful cutin interruption / HUD and camera resume'});
  assert.equal(probe.errors.length,0);checks.push({name:key+' cancellation and reentry'});
  await probe.evaluate('window.hbPlayerDebug.report()');
 }finally{socket?.close();await probe?.stop?.();probe=null;}
}
try{
 await run('t',[
  {name:'nonstop-refute',mode:'nonstop',stage:1,target:'weak',outcome:'refute',measureFocus:true},
  {name:'nonstop-perjury',mode:'nonstop',stage:6,target:'weak',outcome:'lie',lie:true},
  {name:'nonstop-agree',mode:'nonstop',stage:10,target:'agree',outcome:'agree'},
 ].map(e=>profileMode?{...e,measureFocus:false}:e));
 if(!profileMode)await run('y',[
  {name:'panic-wrong',mode:'panic',stage:5,target:'weak',wrong:true,measureFocus:true,exhaust:true},
  {name:'panic-refute',mode:'panic',stage:5,target:'weak',outcome:'refute'},
  {name:'panic-perjury',mode:'panic',stage:5,target:'weak',outcome:'lie',lie:true,fixture:1},
  {name:'panic-agree',mode:'panic',stage:5,target:'agree',outcome:'agree',fixture:2},
 ]);
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,executable:built.executable,profileMode,diagnosticSuppressedUi:suppressUi,cases,checks,limits:suppressUi?'Controlled diagnostic ONLY: UI operations suppressed after the actual successful shot. Not normal gameplay/visual/FPS acceptance.':profileMode?'Three uncaptured normal nonstop outcome windows; no performance claim for video capture.':'Authored panic scripts have no perjury/answer-linked agreement targets; those two success rules use explicitly labelled in-memory QA fixtures, not invented story content.'},null,2));
 console.log(JSON.stringify({ok:true,work,outcomes:cases.length,checks:checks.length}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:String(error),cases,checks},null,2));throw error;}
