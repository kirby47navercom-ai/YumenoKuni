import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {beginOwnedMovie} from './native-window-recording.mjs';
const root=path.resolve(import.meta.dirname,'..'),output=path.join(root,'Saved/native-panic-views-1793690486425/package'),work=path.join(root,'Saved/native-freetime-world-'+Date.now());await fs.mkdir(work,{recursive:true});
const read=async p=>JSON.parse(await fs.readFile(p,'utf8')),manifest=await read(path.join(output,'game.hbpack.json'));
const moduleArg=process.argv.find(a=>a.startsWith('--game-module='))?.slice(14);
if(moduleArg){const source=path.resolve(root,moduleArg);assert(source.startsWith(path.join(root,'Saved')+path.sep));const bytes=await fs.readFile(source),target=path.join(output,manifest.nativeModules[0].binary);await fs.writeFile(target+'.fte.tmp',bytes);await fs.rename(target+'.fte.tmp',target);Object.assign(manifest.files.find(r=>r.path===manifest.nativeModules[0].binary),{bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest));}
const record=process.argv.includes('--record');
if(record)process.env.YUMENO_NATIVE_QA_RECORD='1';
const node='v4:1:F1-A',fixture=path.join(work,'fixture.json'),state={schemaVersion:1,contentVersion:'v4',chapter:'1',node,generation:0,flags:{},evidence:{},read:[],stack:[],log:[],coins:10,bonds:{},gifts:{},cards:[],documents:{},presentation:{},world:{},worldId:'plaza',court:{active:false},trialResultOpen:false};
await fs.writeFile(fixture,JSON.stringify({version:1,items:{['hbengine.savegame.json.yumeno-progress-v4.project.'+manifest.id]:JSON.stringify(state)}}));
const report={work,fixture:true,shipping:false,movies:[],scope:'Isolated authored F1-A, physical walking/talk/cancel/accept and exact FTE return. Not full campaign.'};let p,recording;
const action=async a=>{if(record&&a?.kind==='key'&&a.key==='Enter')await new Promise(r=>setTimeout(r,2000));if(recording&&Date.now()-recording.started>260000){const held=await p.stats();report.movies.push(await recording.finish());recording=null;recording=await beginOwnedMovie(p,'free-world-meeting-'+(report.movies.length+1),{seconds:300});assert.equal((await p.stats()).node,held.node,'No narrative input or node jump between recording parts');}if(a?.kind==='click')await p.click(a.x,a.y);else if(a?.kind==='key')await p.tap(a.key,6);else await p.sampled(3);};
try{
 p=await nativeWindowProbe({source:output,prepared:{output,manifest,executable:path.join(output,manifest.windowsApplication.executable)},work,resume:fixture,maxFrames:null,heartbeatTimeoutMs:120000});await p.hiddenBorderless();await p.resize(record?1280:1920,record?720:1080);if(record)recording=await beginOwnedMovie(p,'free-world-meeting',{seconds:300});await p.tap('c');
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.node===node&&s.mode==='explore'&&!s.scenes.loading;},'free world entrance',120000);await p.sampled(30);report.entrance=await p.stats();await p.capture('world');
 const approach=async()=>{for(let i=0;i<500;i++){const s=await p.stats();assert(!s.error,s.error);assert.equal(s.node,node);if(s.mode==='menu')return s;await action(s.auto);}throw Error('Cannot physically approach an NPC');};
 report.confirm=await approach();assert([2,3].includes(report.confirm.choice.count));await p.capture('confirm');
 for(let i=1;i<report.confirm.choice.count;i++)await p.tap('s');await p.tap('Enter');await p.until(async()=>(await p.stats()).mode==='explore','cancel stays in world');assert.equal((await p.stats()).node,node);report.cancelVerified=true;
 await approach();await p.tap('Enter');await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.node!==node;},'accepted actual FTE',30000);report.accepted=await p.stats();await p.sampled(60);await p.capture('meeting');
 const prefix=report.accepted.node.split(':')[1];assert.equal(prefix,'20','Approaching the shop door must not select a nearby different NPC');
 for(let i=0;i<2200;i++){
  const s=await p.stats();assert(!s.error,s.error);if(!s.node.startsWith('v4:'+prefix+':')&&s.node!==node){report.after=s;break;}await action(s.auto);
 }
 assert(report.after,'Actual FTE must return to its authored chapter continuation');if(recording){await new Promise(r=>setTimeout(r,2500));report.movies.push(await recording.finish());recording=null;}report.runtime=await p.close();p=null;report.ok=true;
}catch(error){report.error=error.stack;report.last=await p?.stats().catch(()=>null);await p?.capture('failure').catch(()=>{});process.exitCode=1;}
finally{if(recording)report.partialMovie=await recording.finish().catch(e=>({error:e.message}));await p?.close().catch(()=>{});await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({work,ok:report.ok,error:report.error?.split('\n')[0]}));}
