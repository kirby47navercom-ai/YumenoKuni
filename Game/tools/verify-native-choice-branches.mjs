// Authored option edges via owned native saves and real Win32 menu input.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {prepareTaskFixtures} from './native-task-fixtures.mjs';
import {caseSaveCatalogue,publishCaseSave} from './native-case-saves.mjs';
import {padSystemAction} from './v4-pad-test-input.mjs';
const root=path.resolve(import.meta.dirname,'..'),build=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const arg=p=>process.argv.find(a=>a.startsWith(p))?.slice(p.length),resume=arg('--resume='),limit=Number(arg('--limit=')||Infinity),only=arg('--only=')?.split(',');
const catalogue=await caseSaveCatalogue(),cases=(await fs.readFile(path.join(catalogue.fixtureRoot,'menu-fixtures.jsonl'),'utf8')).trim().split('\n').map(JSON.parse);
const work=resume?path.resolve(resume):path.join(root,'Saved/native-all-choices-'+Date.now());await fs.mkdir(work,{recursive:true});
const prior=await fs.readFile(path.join(work,'progress.json'),'utf8').then(JSON.parse,()=>null);if(prior)assert.equal(prior.build,build.id);
const results=prior?.results||[],passed=new Set(results.filter(r=>r.ok).map(r=>r.key)),key=c=>c.node+'#'+c.option;
const prepared=await fs.access(path.join(work,'package/game.hbpack.json')).then(async()=>{const manifest=JSON.parse(await fs.readFile(path.join(work,'package/game.hbpack.json'),'utf8'));return {output:path.join(work,'package'),manifest,executable:path.join(work,'package',manifest.windowsApplication.executable)};},()=>prepareTaskFixtures(build.output,work));
const session=path.join(work,'session-'+Date.now()),started=Date.now();let probe;
const save=extra=>fs.writeFile(path.join(work,'progress.json'),JSON.stringify({build:build.id,work,session,passed:passed.size,total:cases.length,seconds:(Date.now()-started)/1000,results,...extra},null,2));
try{
 probe=await nativeWindowProbe({source:build.output,work:session,prepared,maxFrames:null,heartbeatTimeoutMs:120000});let count=0;
 if(only)assert(only.every(k=>cases.some(c=>key(c)===k)),'Unknown focused choice key');
 for(const c of cases){if(passed.has(key(c))||only&&!only.includes(key(c)))continue;if(count++>=limit)break;let last;const began=Date.now();
  try{
   if((await probe.stats()).mode!=='title'){
    await probe.tap('Tab');assert.equal((await probe.stats()).mode,'pad');await probe.click(1047,480);await padSystemAction(probe.stats,probe.tap,'title');await padSystemAction(probe.stats,probe.tap,'title_yes');await probe.until(async()=>(await probe.stats()).mode==='title','choice case title');
   }
   const fixture=await publishCaseSave({work,session,catalogue,branch:c});await probe.tap('s');await probe.tap('w');await probe.tap('c');
   let entry=await probe.until(async()=>{const s=await probe.stats();assert(!s.error,s.error);assert(!s.routeBlocked,'Blocked restored choice');return s.node===c.node&&s.mode==='menu'?s:false;},'actual authored menu '+c.node,120000);
   await probe.sampled(3); // Complete the normal deferred presentation restore before input.
   const ordinal=c.eligible.indexOf(c.option);assert(ordinal>=0);const page=Math.floor(ordinal/7),row=ordinal%7;
   for(let p=0;p<page;p++){
    const next=7+(p>0?1:0);for(let n=0;n<10&&(await probe.stats()).choice.hover!==next;n++)await probe.tap('s');
    assert.equal((await probe.stats()).choice.hover,next);await probe.tap('Enter');await probe.until(async()=>{const s=await probe.stats();return s.choice.pending<0&&s.choice.hover===0;},'choice next page');
   }
   for(let n=0;n<10&&(await probe.stats()).choice.hover!==row;n++)await probe.tap('s');assert.equal((await probe.stats()).choice.hover,row);
   if(only)await probe.capture('focused-menu-'+count);
   const commits=(await probe.stats()).choice.commits;await probe.tap('Enter');
   last=await probe.until(async()=>{const s=await probe.stats();assert(!s.error,s.error);assert(!s.routeBlocked,'Blocked selected route');return s.node!==c.node?s:false;},'physical option commit '+key(c),30000);
   assert(c.trail.includes(last.node),'Unexpected selected route '+last.node);assert(!last.choice||last.choice.commits>commits);
   // Route flags have an exhaustive source interpreter proof in the linked coverage report.
   // This test adds native input/paint/commit and the actual resulting node.
   const result={key:key(c),chapter:c.chapter,node:c.node,option:c.option,ok:true,resultNode:last.node,resultMode:last.mode,seconds:(Date.now()-began)/1000,setsStructurallyVerified:c.sets,fixture};results.push(result);passed.add(result.key);await save();
   if(passed.size%20===0)console.log(JSON.stringify({passed:passed.size,total:cases.length,chapter:c.chapter,seconds:(Date.now()-started)/1000}));
   if(c.option===0&&results.filter(r=>r.chapter===c.chapter&&r.option===0).length===1)await probe.capture('choice-chapter-'+c.chapter.toLowerCase());
  }catch(error){results.push({key:key(c),ok:false,error:error.stack,last});await save();await probe.capture('choice-failure').catch(()=>{});throw error;}
 }
 const runtime=await probe.close();probe=null;await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,build:build.id,work,results,passed:passed.size,total:cases.length,complete:passed.size===cases.length,wallSeconds:(Date.now()-started)/1000,runtime,structuralCoverage:path.join(catalogue.fixtureRoot,'choice-route-coverage.json'),scope:'779 authored option edges from explicit reachable preconditions, using Win32 selection and native commit/target checks. Upstream task success was injected only in the separately linked structural fixture generator. No native current choice result is injected. Human timing and natural campaign traversal are separate.'},null,2));await save({closed:true});console.log(JSON.stringify({work,passed:passed.size,complete:passed.size===cases.length}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,session},null,2));throw error;}finally{await probe?.close().catch(()=>{});}
