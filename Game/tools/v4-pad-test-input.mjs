import assert from 'node:assert/strict';
// Native-input helper shared by the existing probes. Saving now traverses the
// real slot picker and overwrite modal; it never calls the save API directly.
export async function padSystemAction(stats,tap,id){
 let s=await stats();assert.equal(s.padPage,5);
 if(id==='title_yes'){
  assert.equal(s.padSystem.view,5);if(s.padSystem.confirm!==0)await tap('a');await tap('Enter');return;
 }
 assert.equal(s.padSystem.view,0,'system columns must be visible');
 const to=s.padActions.indexOf(id);assert(to>=0,'system action '+id);
 for(let n=0;n<6&&(s=await stats()).padSystem.column!==to;n++)await tap(s.padSystem.column<to?'d':'a');
 assert.equal((await stats()).padSystem.column,to);await tap('Enter');
 if(id!=='save')return;
 assert.equal((await stats()).padSystem.view,1);await tap('Enter');
 s=await stats();if(s.padSystem.view===6){await tap('a');await tap('Enter');}
 const end=Date.now()+120000;let progress='',advanced=Date.now();
 while((s=await stats()).padSystem.busy){
  const p=s.padSystem,next=JSON.stringify([p.savePhase,p.savePart,p.saveClean]);
  if(next!==progress){progress=next;advanced=Date.now();}
  assert(Date.now()-advanced<15000&&Date.now()<end,'native manual save progress '+JSON.stringify(p));await new Promise(r=>setTimeout(r,100));
 }
 assert.equal((await stats()).padSystem.view,1);await tap('Backspace');assert.equal((await stats()).padSystem.view,0);
}
