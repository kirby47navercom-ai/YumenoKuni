// Physical input into a hidden owned native package; graph reads choose authored
// answers, never write runtime outcomes. Initial saves isolate reported states.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {nativeWindowProbe} from './native-window-probe.mjs';
const read=async f=>JSON.parse((await fs.readFile(f,'utf8')).replace(/^\uFEFF/,''));
const b=await read(process.argv[2]),campaign=await read(process.argv[3]),graph=campaign.chapters['1'],nodes=graph.nodes,hub=nodes['rev:01:investigate'];
const work=path.resolve(process.argv[4]),prepared={output:b.output,executable:b.executable,manifest:await read(path.join(b.output,'game.hbpack.json'))};await fs.mkdir(work,{recursive:true});
const records=new Map(Object.values(nodes).filter(n=>n.type==='evidence').map(n=>[n.evidenceId,{name:n.name,text:n.text}]));
const norm=t=>(t||'').replace(/\s/g,'');const prop=(f,i,id)=>f.widgets.find(w=>w.instance===i)?.nodes.find(n=>n.id===id)?.properties;
const completeFlags=Object.fromEntries(hub.requiredSpotIds.map(id=>['spot:'+id+':complete',true]));
let p,dir,spoken=0,menus=0;const checks=[];
const frame=async(name='frame',pixels=false)=>{await p.capture(name,{pixels});const f=await read(path.join(dir,name+'.ui.json'));assert(!f.widgets.some(w=>w.instance==='investigationguidev4'),'unrequested checklist must never appear');return f;};
const wait=async(fn,label)=>p.until(async()=>{const f=await frame();return fn(f)&&f;},label,45000,80);
const launch=async(name,node,flags,missing=[],legacyCards=false)=>{
 dir=path.join(work,name);await fs.mkdir(path.join(dir,'State/Saves'),{recursive:true});
 await fs.writeFile(path.join(dir,'State/Saves/rewrite-v5-yumeno-progress-v4.json'),JSON.stringify({schemaVersion:1,contentVersion:'v4',campaignRevision:'rewrite-v5',chapter:'1',node,flags,stack:[],log:[],read:[],evidence:Object.fromEntries(hub.requiredCards.filter(id=>!missing.includes(id)).map(id=>[id,records.get(id)])),cards:legacyCards?[]:hub.requiredCards.filter(id=>!missing.includes(id)),coins:10,worldId:'service_lounge',court:{active:false,dead:[]}}));
 await fs.writeFile(path.join(dir,'State/Saves/YumenoKuni-options-v4.json'),JSON.stringify({version:2,textSpeed:10,frameRate:120}));
 p=await nativeWindowProbe({source:b.output,prepared,work:dir,sparse:true,unprofiled:true,maxFrames:null});await p.hiddenBorderless();await p.resize(1920,1080);await p.tap('c');
};
const distanceTo=goal=>{const reverse=new Map();for(const n of Object.values(nodes)){const edges=['next','target','default'].filter(k=>n[k]).map(k=>n[k]);for(const o of n.options||[])edges.push(o.to);for(const o of n.cases||[])edges.push(o.to);for(const to of edges){if(!reverse.has(to))reverse.set(to,[]);reverse.get(to).push(n.id);}}const d=new Map([[goal,0]]),q=[goal];for(let i=0;i<q.length;i++)for(const from of reverse.get(q[i])||[])if(!d.has(from)){d.set(from,d.get(q[i])+1);q.push(from);}return d;};
async function play(current,goal,flags){
 const distances=distanceTo(goal);
 for(let step=0;current!==goal&&step<700;step++){
  const n=nodes[current];assert(n,current);Object.assign(flags,n.set||{});
  if(n.type==='stage'){current=n.next;continue;}
  if(n.type==='branch'){current=(n.cases.find(c=>flags[c.flag]===c.equals)||{to:n.default}).to;continue;}
  if(n.type==='say'){
   const all=norm(n.text);let final=false;
   for(let page=0;!final&&page<12;page++){
    const f=await wait(f=>{const body=prop(f,'main','Body');return body?.visible&&prop(f,'main','Next')?.visible&&all.includes(norm(body.text));},'authored spoken line '+n.id);
    const piece=norm(prop(f,'main','Body').text);assert(piece,n.id);final=all.endsWith(piece);await p.tap('Enter',1);
   }
   assert(final,'all pages of '+n.id);spoken++;current=n.next;
  }else if(n.type==='menu'){
   await wait(f=>norm(prop(f,'main','Body')?.text)===norm(n.q),'authored choice '+n.id);
   const eligible=n.options.filter(o=>Object.entries(o.requires||{}).every(([key,value])=>(flags[key]??false)===value));
   const best=[...eligible].sort((a,b)=>(distances.get(a.to)??1e9)-(distances.get(b.to)??1e9))[0];assert(best&&distances.has(best.to),n.id);
   const index=eligible.indexOf(best);assert(index<9);await p.tap(String(index+1),1);Object.assign(flags,best.set||{});menus++;current=best.to;
  }else if(n.type==='evidence'||n.type==='document'){
   let f=await wait(f=>prop(f,'v4story','DocumentTitle')?.visible,'record '+n.id);const title=prop(f,'v4story','DocumentTitle').text;let closed=false;for(let page=0;page<16&&!closed;page++){await p.tap('Enter');f=await frame();closed=!prop(f,'v4story','DocumentTitle')?.visible||prop(f,'v4story','DocumentTitle')?.text!==title;}assert(closed,'all document pages '+n.id);current=n.next;
  }else throw Error('Unexpected node before goal: '+n.id+' '+n.type);
 }
 assert.equal(current,goal);return current;
}
try{
 // All ten inspections completed, but the earlier public application was absent.
 await launch('missing-prior',hub.id,{...completeFlags},['v4:E1-APP']);
 let f=await wait(f=>norm(prop(f,'main','Body')?.text)===norm(nodes['rev:01:application-reminder'].text),'natural missing-record reminder');
 await play('rev:01:application-reminder',hub.id,{...completeFlags});
 await wait(f=>prop(f,'explore','AreaName')?.visible,'back to investigation without a checklist');
 await p.tap('m');await p.tap('8');await p.tap('4');await wait(f=>prop(f,'explore','AreaName')?.visible,'move to document location');
 await p.tap('m');await p.tap('4');await wait(f=>prop(f,'v4story','DocumentTitle')?.text.includes(records.get('v4:E1-APP').name),'public record can be recovered');await p.tap('Enter');
 f=await wait(f=>norm(prop(f,'main','Body')?.text)===norm(nodes['rev:01:investigation-ended'].text),'immediate investigation-ended broadcast');await frame('deadline-broadcast',true);
 const flags={...completeFlags};await play('rev:01:investigation-ended','rev:01:trial-gather',flags);
 f=await wait(f=>prop(f,'explore','AreaName')?.visible&&!prop(f,'main','Body')?.visible,'walk to the destination stated in the broadcast');assert.notEqual(prop(f,'explore','AreaName')?.text,'재판 엘리베이터');assert(!f.widgets.some(w=>w.instance==='trialentryv4'),'no court before arrival');await frame('go-to-elevator',true);
 await p.tap('m');await p.tap('Enter');f=await wait(f=>prop(f,'explore','AreaName')?.text==='재판 엘리베이터','actual elevator room loaded');await frame('elevator',true);
 // The target is the existing cabin, not an invisible fictional call button.
 await p.move(640,360+900*.7/2.72);await wait(f=>prop(f,'explore','LblText')?.visible&&prop(f,'explore','LblText')?.text==='재판 엘리베이터 탑승','physical cabin target');await p.tap('e');
 await play('rev:01:trial-gather:enter','rev:01:trial-gather:return',flags);
 await wait(f=>prop(f,'trialentryv4','PrepTitle')?.visible&&f.scene?.includes('/Court')&&!f.widgets.some(w=>w.instance==='loadingv4'),'authored boarding reaches trial preparation');await frame('trial-preparation',true);
 checks.push({missingPriorRecoverable:true,immediateDeadlineBroadcast:true,reviewDialoguePlayed:spoken,reviewChoices:menus,arrivalRequired:true,physicalCabinInteraction:true,trialPreparation:true,exit:(await p.close()).exitCode});p=null;
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:false,build:b.id,checks},null,2));
 // The first chapter ends on its authored necessary records; stale auxiliary
 // visit flags must not force an extra checklist or another round of inspection.
 const pending=hub.requiredSpotIds.at(-1),flags2={...completeFlags,['spot:'+pending+':complete']:false};
 await launch('all-records-stale-visit',hub.id,flags2);
 await wait(f=>norm(prop(f,'main','Body')?.text)===norm(nodes['rev:01:investigation-ended'].text),'all records trigger completion despite stale visit flag');
 checks.push({allNecessaryEvidenceSufficient:true,noChecklist:true,exit:(await p.close()).exitCode});p=null;
 await launch('legacy-card-index',hub.id,{...completeFlags},[],true);
 await wait(f=>norm(prop(f,'main','Body')?.text)===norm(nodes['rev:01:investigation-ended'].text),'owned evidence rebuilds the saved card index');
 checks.push({legacyCardIndexRebuiltFromOwnedEvidence:true,noChecklist:true,exit:(await p.close()).exitCode});p=null;
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,build:b.id,checks,scope:'Seeded isolated saves; ordinary physical reading, choices, investigation and cabin interaction. Not a full daily-to-verdict playthrough.'},null,2));console.log(JSON.stringify({ok:true,checks}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,spoken,menus,checks},null,2));throw error;}finally{await p?.close().catch(()=>{});}
