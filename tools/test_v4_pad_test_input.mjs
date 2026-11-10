import assert from 'node:assert/strict';
import {padSystemAction} from '../Game/tools/v4-pad-test-input.mjs';

async function scenario(parts,stuck=false){
 let clock=0,ticks=0;const p={view:0,column:0,confirm:0,busy:false,savePhase:2,savePart:0,saveClean:0};
 const now=Date.now,timer=globalThis.setTimeout;
 Date.now=()=>clock;globalThis.setTimeout=fn=>{fn();return 0;};
 const stats=async()=>{if(p.busy){clock+=1000;++ticks;if(!stuck)p.savePart=ticks;if(ticks>=parts)p.busy=false;}return {padPage:5,padActions:['log','save'],padSystem:{...p}};};
 const tap=async k=>{if(k==='d')p.column=1;else if(k==='Backspace')p.view=0;else if(k==='Enter'){if(p.view===0)p.view=1;else if(p.view===1)p.view=6;else if(p.view===6){p.view=1;p.busy=true;}}};
 try{await padSystemAction(stats,tap,'save');return clock;}finally{Date.now=now;globalThis.setTimeout=timer;}
}
assert(await scenario(40)>15000,'forward-progress saves may exceed the old total deadline');
await assert.rejects(()=>scenario(100,true),/native manual save progress/);
await assert.rejects(()=>scenario(200),/native manual save progress/);
console.log(JSON.stringify({ok:true,checks:['40-second advancing save completes','15-second stalled save fails','120-second hard limit still fails'],scope:'QA helper clock simulation; not a native save claim'}));
