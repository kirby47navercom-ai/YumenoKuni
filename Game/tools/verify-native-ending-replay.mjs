// Fresh native Continue of the two existing actual ending saves; no campaign replay.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createOwnedNativePackage} from './native-owned-package.mjs';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),build=JSON.parse(await fs.readFile(process.argv.find(v=>v.startsWith('--build-result='))?.slice(15)||path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/native-ending-replay-'+Date.now());await fs.mkdir(work,{recursive:true});
const prepared=await createOwnedNativePackage({source:build.output,work,stats:true}),results=[];
const hash=b=>createHash('sha256').update(b).digest('hex'),headPrefix='hbengine.savegame.json.yumeno-progress-v4.project.';
for(const [index,name] of ['v4-flow-1793429459362','v4-flow-1793453765826'].entries()){
 const source=path.join(root,'Saved',name,'final-ending-savegames.json'),before=await fs.readFile(source),flat=JSON.parse(before),head=JSON.parse(Object.entries(flat.items).find(([k])=>k.startsWith(headPrefix))[1]);
 assert.equal(head.chapter,'6');assert(head.trialResults.best['6'].paid&&head.trialResults.best['6'].complete);
 let probe;const row={source,sourceSHA256:hash(before),expectedNode:head.node,expectedCoins:head.coins,ok:false};
 try{
  probe=await nativeWindowProbe({source:build.output,work:path.join(work,'ending-'+index),prepared,resume:source});await probe.tap('c');
  let s=await probe.until(async()=>{const s=await probe.stats();assert(!s.error,s.error);return s.mode==='credits'&&s.node===head.node?s:false;},'actual saved ending credits',120000);
  await probe.sampled(process.argv.includes('--settle-capture')?60:3);assert.equal(s.coins,head.coins);row.normalLoaded={node:s.node,mode:s.mode,coins:s.coins};await probe.capture('credits');
  await new Promise(r=>setTimeout(r,1800));await probe.tap('Enter');await probe.until(async()=>(await probe.stats()).mode==='title','ending return to title');
  // The actual saves have capped999 wallets, which would mask duplicate payout.
  // Change only the owned wallet to500; preserve all ending/result flags and parts.
  const ownHead=path.join(work,'ending-'+index,'State/Saves/yumeno-progress-v4.json'),owned=JSON.parse(await fs.readFile(ownHead,'utf8'));owned.coins=500;await fs.writeFile(ownHead+'.wallet.tmp',JSON.stringify(owned));await fs.rename(ownHead+'.wallet.tmp',ownHead);row.walletProbe={fixture:true,coins:500,scope:'Only the isolated wallet is lowered to avoid the999 cap hiding duplicate payout. Original ending/result flags and source save remain unchanged.'};
  await probe.tap('c');s=await probe.until(async()=>{const s=await probe.stats();assert(!s.error,s.error);return s.mode==='credits'&&s.node===head.node?s:false;},'same paid ending replay',120000);assert.equal(s.coins,500,'Continue must not repay an already paid trial/ending');
  row.loaded={node:s.node,chapter:s.chapter,mode:s.mode,coins:s.coins};row.runtime=await probe.close();probe=null;assert.equal(hash(await fs.readFile(source)),hash(before));row.ok=true;
 }catch(error){row.error=error.stack;row.last=await probe?.stats().catch(()=>null);}finally{await probe?.close().catch(()=>{});}
 results.push(row);await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:results.every(r=>r.ok),build:build.id,work,results,scope:'Two unchanged actual normal-route ending saves; native credits, title, repeat Continue and no duplicate payout. No task success or ending flag injection.'},null,2));console.log(JSON.stringify({ending:index,ok:row.ok,work,error:row.error?.split('\n')[0]}));if(!row.ok){process.exitCode=1;break;}
}
