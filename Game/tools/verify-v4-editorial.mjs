// Isolated existing saved IDs only; no normal campaign or duration claim.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root);
const manifestPath=process.argv.find(arg=>arg.startsWith('--manifest='))?.slice('--manifest='.length)||'Saved/editorial-fixtures-20261101/manifest.json';
const manifest=JSON.parse(await fs.readFile(path.resolve(root,manifestPath),'utf8'));
assert(manifest.fixture&&!manifest.normalRoute);
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/v4-editorial-'+Date.now()),runs=[];
const selected=process.argv.find(arg=>arg.startsWith('--chapters='))?.slice('--chapters='.length).split(',');
if(selected)assert(selected.length>0&&new Set(selected).size===selected.length&&selected.every(c=>manifest.fixtures.some(f=>f.chapter===c)));
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const keys={c:[67,'KeyC'],Enter:[13,'Enter'],Tab:[9,'Tab'],s:[83,'KeyS'],a:[65,'KeyA'],d:[68,'KeyD'],Backspace:[8,'Backspace']};
for(const fixture of manifest.fixtures.filter(f=>!selected||selected.includes(f.chapter))){
 const folder=path.join(work,'chapter-'+fixture.chapter);await fs.mkdir(path.join(folder,'UserData'),{recursive:true});
 const seeded=JSON.parse(await fs.readFile(path.join(repo,fixture.file),'utf8'));
 const head=JSON.parse(Object.entries(seeded.items).find(([key])=>key.includes('yumeno-progress-v4.project.'))[1]);
 assert(/^[0-9-]{1,40}$/.test(head.snapshot),'fixture must obey the actual SaveV4 snapshot contract');
 await fs.copyFile(path.join(repo,fixture.file),path.join(folder,'UserData/savegames.json'));
 let probe,last;
 try{
  probe=await editorWindowProbe({work:folder,mode:'player',executable});
  await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
  await delay(700);
  const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
  const stats=async()=>{last=JSON.parse((await call('Stats')).outputs.result);assert(!last.error&&!last.routeBlocked,JSON.stringify(last));return last;};
  const dialogue=async()=>JSON.parse((await call('DialogueStats')).outputs.result);
  const sample=async()=>{const frame=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(60);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=frame+2,'input frames',10000);};
  const tap=async key=>{const[windowsVirtualKeyCode,code]=keys[key];for(const type of ['keyDown','keyUp']){await probe.cdp('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode});await sample();}};
  const click=async(x,y)=>{for(const type of ['mouseMoved','mousePressed','mouseReleased']){await probe.cdp('Input.dispatchMouseEvent',{type,x,y,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})});await sample();}};
  await tap('c');await probe.until(async()=>{const s=await stats();return s.chapter===Number(fixture.chapter)&&s.node===fixture.entry;},'same published saved event ID',60000);
  await call('DebugFastRead');const first=await dialogue();
  assert.equal(first.raw,fixture.expectedText);assert.notEqual(first.raw,fixture.oldText);assert.equal(first.speaker,fixture.speaker);assert(first.trial);
  const checkPose=async()=>{
   if(!fixture.expectedPose)return null;
   let court;await probe.until(async()=>{court=JSON.parse((await call('CourtStats')).outputs.result);return court.cast.some(row=>row.seat===fixture.seat&&[fixture.expectedPose+'.webp',fixture.expectedPose+'_back.webp'].includes(row.texture));},'authored pose on the same physical court seat',30000);
   const s=await stats();if(fixture.actor!=='mio')assert(s.portrait.endsWith('/'+fixture.expectedPose+'.webp'),s.portrait);
   return court.cast.find(row=>row.seat===fixture.seat);
  };
  let actualPose=null;const pages=[];
  for(let i=0;i<first.pages;i++){
   let d=await dialogue();assert.equal(d.page,i);assert.equal(d.raw,fixture.expectedText);
   // Cold Continue finishes court construction and entry before accepting
   // dialogue input. Observe the actual page completing instead of assuming
   // an early Enter edge already belonged to this page.
   await probe.until(async()=>{d=await dialogue();assert.equal(d.raw,fixture.expectedText);assert.equal(d.page,i);return d.shown>=d.length;},'actual page reveal complete',30000);
   const ui=await probe.evaluate(`(()=>{const e=document.querySelector('[data-widget-name="Body"]'),r=e.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(e);return{text:e.textContent,box:[r.x,r.y,r.width,r.height],lines:Array.from(range.getClientRects(),x=>[x.x,x.y,x.width,x.height]),font:getComputedStyle(e).fontFamily};})()`);
   assert.equal(ui.text,d.text);for(const r of ui.lines){assert(r[2]<=ui.box[2]+.5);assert(r[1]+r[3]<=ui.box[1]+ui.box[3]+.5);}
   pages.push({page:i,text:d.text,ui});if(i===0){actualPose=await checkPose();await delay(1000);await probe.capture('revised-first-page.png');}
   if(i+1<first.pages)await tap('Enter');
  }
  let manualSaveContinue=false;
  if(fixture.chapter==='2'){
   await tap('Tab');await click(1047,480);await padSystemAction(stats,tap,'save');
   const disk=JSON.parse(await fs.readFile(path.join(folder,'UserData/savegames.json'),'utf8'));
   const head=JSON.parse(Object.entries(disk.items).find(([key])=>key.includes('yumeno-progress-v4.project.'))[1]);
   assert.equal(head.node,fixture.entry);await fs.copyFile(path.join(folder,'UserData/savegames.json'),path.join(folder,'actual-manual-savegames.json'));
   await padSystemAction(stats,tap,'title');await padSystemAction(stats,tap,'title_yes');await tap('c');
   await probe.until(async()=>(await stats()).node===fixture.entry,'actual Save/Continue same edited ID',60000);
   assert.equal((await dialogue()).raw,fixture.expectedText);manualSaveContinue=true;await checkPose();await delay(1000);await probe.capture('actual-save-continue.png');
  }
  assert.deepEqual(probe.errors,[]);
  const result={ok:true,executable,chapter:fixture.chapter,savedEventId:fixture.entry,speaker:first.speaker,revisedRaw:first.raw,oldWordsAbsent:first.raw!==fixture.oldText,pages,actualManualSaveContinue:manualSaveContinue,expectedPose:fixture.expectedPose,actualPose};
  await fs.writeFile(path.join(folder,'report.json'),JSON.stringify(result,null,2));runs.push(result);
 }catch(error){await fs.writeFile(path.join(folder,'failure.json'),JSON.stringify({error:error.stack,last,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}
 finally{await probe?.stop?.();}
}
await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,fixture:true,normalRoute:false,executable,runs,scope:'Selected revised existing saved IDs and actual displayed pages. Chapter2 also performs real manual Save/Continue. Seeded prior flags/evidence/court; not a full campaign, normal acquisition, quality or five-hour certificate.'},null,2));
console.log(JSON.stringify({ok:true,work,chapters:runs.map(r=>r.chapter)}));
