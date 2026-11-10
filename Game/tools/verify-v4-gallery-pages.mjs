// An explicit source fixture earns a real read record through story input,
// saves it through the Pad, then replays it. No injected gallery/read unlocks.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),baseline=process.argv.includes('--baseline'),room=process.argv.includes('--room');
const earned=process.argv.find(v=>v.startsWith('--earned='))?.slice(9);assert(!earned||room);
const id=room?'v4:43:F-AI01-B2:e:139f350b70f2:1':'v4:40:h-ac49e8223a:e:146e319602d7:1',record=room?'event:5c9059ace173aae8':'event:f3bb9998fc10a16e';
const entry=room?'v4:43:F-AI02-A:menu':id;
const graph=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/chapters/1.json'),'utf8'));
const seed=JSON.parse(await fs.readFile(earned||path.join(root,'Saved/editorial-fixtures-20261101/chapter-1.json'),'utf8'));
const headKey=Object.keys(seed.items).find(k=>k.includes('yumeno-progress-v4.project.')),head=JSON.parse(seed.items[headKey]);
if(!earned){head.node=entry;head.snapshot=room?'2026110118-2':'2026110118-1';head.court.active=false;head.court.dead=[];head.flags=room?{'F-AI01-B':'B2'}:{};head.stack=[];head.world={};head.worldId='park_garden';head.presentation={};seed.items[headKey]=JSON.stringify(head);}
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/v4-gallery-pages-'+Date.now());await fs.mkdir(path.join(work,'UserData'),{recursive:true});await fs.writeFile(path.join(work,'UserData/savegames.json'),JSON.stringify(seed));
const title=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/v4_story/title_chapter_layout.json'),'utf8'));
const layout=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/v4_story/gallery_layout.json'),'utf8'));
const catalog=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/v4_story/gallery_catalog.json'),'utf8'));
const keys={c:[67,'KeyC'],Enter:[13,'Enter'],Tab:[9,'Tab'],Backspace:[8,'Backspace'],a:[65,'KeyA'],d:[68,'KeyD'],s:[83,'KeyS'],e:[69,'KeyE']};
const delay=ms=>new Promise(r=>setTimeout(r,ms));let probe,last;
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
 const call=n=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+n)},{})`);
 const stats=async()=>{last=JSON.parse((await call('Stats')).outputs.result);assert(!last.error&&!last.routeBlocked,JSON.stringify(last));return last;};
 const dialogue=async()=>JSON.parse((await call('DialogueStats')).outputs.result);
 const sample=async()=>{const f=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(70);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=f+2,'sampled input',10000);};
 const tap=async k=>{const[windowsVirtualKeyCode,code]=keys[k];for(const type of ['keyDown','keyUp']){await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});await sample();}};
 const click=async r=>{for(const type of ['mouseMoved','mousePressed','mouseReleased']){await probe.cdp('Input.dispatchMouseEvent',{type,x:r[0]+r[2]/2,y:r[1]+r[3]/2,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})});await sample();}};
 const text=async n=>probe.evaluate(`document.querySelector('[data-widget-name="'+${JSON.stringify(n)}+'"]')?.textContent`);
 let original=null;
 if(!earned){
 await tap('c');await probe.until(async()=>{const s=await stats();return s.node===entry&&(room?!!s.choice:s.mode==='story');},'existing authored entry',60000);await call('DebugFastRead');
 if(room){
  await tap('s');await tap('Enter');
  for(let n=0;(await stats()).node!=='v4:43:F-AI02-B:menu'&&n<200;n++)await tap('Enter');assert.equal((await stats()).node,'v4:43:F-AI02-B:menu');
  await tap('s');await tap('Enter');for(let n=0;(await stats()).node!==id&&n<200;n++)await tap('Enter');assert.equal((await stats()).node,id);assert.equal((await stats()).world.space,'hotel_corridor');
 }
 original=await dialogue();assert.equal(original.raw,graph.nodes[id].text);if(!room)assert(original.pages>=2);
 // Real reading inputs, including the second page, earn the saved read ID.
 for(let tries=0;(await stats()).node===id&&tries<12;tries++)await tap('Enter');assert.notEqual((await stats()).node,id);
 await tap('Tab');await click([1000,460,90,40]);await padSystemAction(stats,tap,'save');
 const disk=JSON.parse(await fs.readFile(path.join(work,'UserData/savegames.json'),'utf8')),saved=JSON.parse(disk.items[headKey]);
 assert(saved.gallery.available.includes(record));const read=new Set(saved.read||[]);for(const[k,v]of Object.entries(disk.items))if(k.includes('yumeno-v4-'+saved.snapshot+'-read-'))for(const n of JSON.parse(v).rows)read.add(n);assert(read.has(id));if(room){assert.equal(saved.flags['F-AI02-A'],'A2');assert.equal(saved.flags['F-AI02-B'],'B2');}
 await fs.copyFile(path.join(work,'UserData/savegames.json'),path.join(work,'actual-earned-read-savegames.json'));
 await padSystemAction(stats,tap,'title');await padSystemAction(stats,tap,'title_yes');
 }else{assert.equal(head.flags['F-AI02-A'],'A2');assert.equal(head.flags['F-AI02-B'],'B2');assert(head.gallery.available.includes(record));}
 await click(title.mainRects[4]);await probe.until(async()=>!(await text('GaStatus')).includes('준비 중'),'earned gallery read ready',60000);
 await click(layout.top[0]);const index=catalog.order.event.indexOf(record);assert(index>=0);for(let n=0;n<Math.floor(index/11);n++)await tap('e');for(let n=0;n<index%11;n++)await tap('s');await tap('Enter');await tap('a');await tap('Enter');await tap('Enter');
 await probe.until(async()=>(await stats()).gallery.replay,'newly earned record opens',10000);
 // The saved read set may contain another real line in the same record.
 for(let n=0;(await stats()).gallery.node!==id&&n<200;n++)await tap('Enter');assert.equal((await stats()).gallery.node,id);
 const first=await dialogue();assert(first.page===0&&first.shown===first.length);await probe.capture('page-one.png');let second=first;
 if(!room){assert(first.pages>=2);await tap('Enter');await delay(500);second=await dialogue();assert.equal(second.page,1);assert.equal(second.raw,graph.nodes[id].text);}
 const body=await text('Body'),replay=await stats();
 if(room){assert.equal(replay.gallery.space,baseline?'hotel_rest_lounge':'hotel_corridor');assert.equal(second.raw,graph.nodes[id].text);}
 else if(baseline){assert.equal(second.shown,0);assert.equal(body,'');}
 else{assert.equal(second.shown,second.length);assert.equal(body,second.text);assert(body.length>0);}
 await probe.capture(room?'actual-choice-room.png':'page-two.png');await tap('Backspace');assert(!(await stats()).gallery.replay);assert.deepEqual(probe.errors,[]);
 const report={ok:true,baseline,room,fixture:true,fixtureOrigin:earned?'Exact actual-earned-read save from the earlier declared source/prior-memory fixture; no repeated story or modified flags.':room?'Existing chapter1 source entry with prior-episode B2 memory fixture. Current A2/B2 selected through real native inputs; no injected read/availability.':'Existing chapter1 source entry; no injected read/availability/choice flags',earnedResume:earned||null,executable,work,node:id,record,original,first,second,body,replay,actuallyReadAndSaved:true,scope:room?'Actual source A2/B2 choices -> corridor -> real read/Pad save -> Gallery same line/room. Explicit source/prior-memory fixture, not full normal campaign.':'Real story input earns the long line, real Pad save and Title Gallery replay verify page2. Explicit entry fixture, not full normal campaign or duration proof.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({ok:true,baseline,room,work,page:second.page,shown:second.shown,length:second.length,space:replay.gallery.space}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,last,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
