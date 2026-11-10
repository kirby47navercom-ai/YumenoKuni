import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const layout=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/v4_story/dialogue_layout.json'),'utf8'));
const work=path.join(root,'Saved/v4-dialogue-window-'+Date.now());await fs.mkdir(work,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms)),checks=[];let probe;process.env.HB_PLAYER_SOAK_HOURS='1';
try{
 probe=await editorWindowProbe({work,mode:'player',executable});await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);await delay(700);
 const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
 const stats=async()=>{const s=JSON.parse((await call('Stats')).outputs.result);assert(!s.error,JSON.stringify(s));return s;},dialogue=async()=>JSON.parse((await call('DialogueStats')).outputs.result);
 const keys={Enter:[13,'Enter'],Tab:[9,'Tab'],Backspace:[8,'Backspace'],s:[83,'KeyS']};
 const sample=async()=>{const f=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(65);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=f+2,'input sampled',10000);};
 const key=async(k,type)=>{const [windowsVirtualKeyCode,code]=keys[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});};
 const tap=async k=>{await key(k,'keyDown');await sample();await key(k,'keyUp');await sample();};
 const ui=()=>probe.evaluate(`(()=>{const names=['Body','DialogFrame','Name','Nameplate','NameHead','Next','Portrait','DialogueOrnament'];return Object.fromEntries(names.map(n=>{const e=document.querySelector('[data-widget-name="'+n+'"]'),r=e?.getBoundingClientRect(),s=e?getComputedStyle(e):null,im=e?.querySelector('img'),range=document.createRange();let lines=[];if(n==='Body'&&e?.firstChild){range.selectNodeContents(e);lines=Array.from(range.getClientRects(),x=>({x:x.x,y:x.y,w:x.width,h:x.height}));}return[n,{visible:!!r?.width&&s.visibility!=='hidden',rect:r?[r.x,r.y,r.width,r.height]:null,text:e?.textContent,font:s?parseFloat(s.fontSize):null,lineHeight:s?parseFloat(s.lineHeight):null,type:e?.className,asset:im?.dataset.asset,loaded:!!im&&im.complete&&im.naturalWidth>0,lines}];}));})()`);
 const close=(a,b)=>a.forEach((v,i)=>assert(Math.abs(v-b[i])<.1,JSON.stringify({a,b})));
 const reveal=async()=>{const q=await dialogue();if(q.shown<q.length)await tap('Enter');};
 const fit=async()=>{const u=await ui();for(const r of u.Body.lines){assert(r.w<=u.Body.rect[2]+.2);assert(r.y+r.h<=u.Body.rect[1]+u.Body.rect[3]+.2);}return u;};
 await call('DebugV4Chapter',{index:1});await delay(400);let initial=await ui();const reference=await dialogue();assert.equal(reference.speaker,layout.portrait.referenceSpeaker);close(initial.Portrait.rect,[0,0,1280,layout.portrait.referenceImageHeight]);assert(initial.Portrait.visible&&initial.Portrait.loaded);assert(!initial.DialogueOrnament.visible);await reveal();await probe.capture('00-user-reference-larger-standing.png');checks.push('user reference Haruka uses1050px ADV standing height with own160cm reference and preserved stature ratios; whole-body fit-to700 policy removed');
 for(const kind of [0,1,2]){
  await call('DebugV4DialogueFixture',{kind});await delay(300);const q=await dialogue();assert.equal(q.trial,false);assert.equal(q.hero,kind===1);let u=await ui();close(u.Body.rect,layout.body);assert(Math.abs(u.Body.font-layout.font)<.01);assert(!u.NameHead.visible);assert(u.Name.type.includes('hb-ui-Image'));
  if(kind===2){assert(!u.Name.visible&&!u.Nameplate.visible);}else{assert(u.Name.loaded&&u.Name.visible);close(u.Name.rect,layout.names[kind===1?'hero':'normal']);close(u.Nameplate.rect,layout.namebase[kind===1?'hero':'normal']);}
  assert(!u.Next.visible);await reveal();u=await fit();assert(u.Next.loaded);await probe.capture('0'+(kind+1)+'-'+['normal','current-protagonist','nameless'][kind]+'.png');
 }
 checks.push('actual authored normal/current-protagonist/nameless ADV lines use composed body/font and separate full-name image; no duplicated colored first glyph or stale anonymous name');
 await call('DebugV4DialogueFixture',{kind:3});await delay(250);let q=await dialogue();assert(q.pages>=2);const node=(await stats()).node,raw=q.raw,pages=[];
 for(let page=0;page<q.pages;page++){
  await reveal();const current=await dialogue();assert.equal(current.page,page);assert.equal((await stats()).node,node);pages.push(current.text);const u=await fit();assert(u.Body.text===current.text);assert(u.Next.visible);close(u.Next.rect,layout.next);
  await probe.capture('page-'+page+'.png');
  if(page===0){await tap('Tab');const paused=(await dialogue()).shown;await delay(250);assert.equal((await dialogue()).shown,paused);await tap('Tab');assert.equal((await dialogue()).page,page);assert.equal((await stats()).node,node);}
  await tap('Enter');
 }
 assert.notEqual((await stats()).node,node);await fs.writeFile(path.join(work,'long-pages.json'),JSON.stringify({raw,pages,sourceNode:node},null,2));checks.push('actual longest authored line retains same node across bounded pages; Pad pauses/returns to same page; only final page advances graph, no shrinking or text rewrite');
 await call('DebugV4DialogueFixture',{kind:4});await delay(500);q=await dialogue();assert(q.trial&&!q.hero);assert.equal(q.speaker,layout.ownPlayer.displayName);await reveal();let trial=await fit();close(trial.Body.rect,layout.trial.body);assert.equal(trial.Body.font,30);close(trial.Name.rect,layout.trial.name);close(trial.Nameplate.rect,layout.trial.icon);assert(trial.Name.asset.includes('trial_name_'));assert(trial.Nameplate.asset.includes('trial_portrait_mio.svg'));assert(trial.DialogueOrnament.visible&&trial.DialogueOrnament.loaded);assert(trial.DialogueOrnament.asset.includes('trial_frame_1.svg'));assert(!trial.NameHead.visible);close(trial.Next.rect,layout.trial.next);assert(trial.Next.asset.includes('trial_next.svg'));await probe.capture('04-separate-trial-panel-name-next.png');checks.push('actual authored trial speaker uses separate pl/frame-name/icon/next carriers and30px body; explicit own Normal/Down/Center/in and2-line policy, no ADV hero plate reuse');
 await call('DebugV4ChoiceFixture',{count:3});await delay(300);let u=await ui();assert(!u.Name.visible&&!u.Nameplate.visible&&!u.NameHead.visible&&!u.Next.visible);close(u.Body.rect,layout.body);await probe.capture('04-choice-question-no-name.png');checks.push('actual choice question returns to source ADV body and clears every name/check-next owner');
 assert.deepEqual(await probe.evaluate('Array.from(document.images).filter(i=>i.offsetWidth>0&&i.src&&i.complete&&i.naturalWidth===0).map(i=>i.src)'),[]);assert.deepEqual(probe.errors,[]);
 const report={ok:true,work,executable,checks,fixture:true,scope:'Own native actual authored ADV/trial line fixtures, retained source body/font/name/icon/next carriers and own full-name images/day ink/pagination/PC advance. Explicit own absent-WIN Normal/Down/Center/in; original implicit default unknown. Source19 frame-line carriers restored with own public-reference pink ink; portrait uses own public-reference angular polygon inside retained source clip carrier. Original alpha/glow/masks, missing-raster pixels/glyph baselines/palette/transition timing and trial4ab210(80,10) final transform unresolved. Not whole campaign acceptance.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,checks,probeErrors:probe?.errors},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}finally{await probe?.stop?.();}
