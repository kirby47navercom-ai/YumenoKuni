// Isolated precondition fixtures. Never writes user/canonical saves or success outcomes.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const root=path.resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex'),prefix='hbengine.savegame.json.',headKey=prefix+'yumeno-progress-v4.project.004a6371-3a84-4fc3-8b54-31a5001740dd';
export async function caseSaveCatalogue(){
 const actual=new Map(),templates=new Map();
 for(const e of await fs.readdir(path.join(root,'Saved'),{withFileTypes:true}))if(e.isDirectory()&&/^v4-flow-\d+$/.test(e.name)){
  const dir=path.join(root,'Saved',e.name);
  for(const name of await fs.readdir(dir))if(/^(?:chapter-\d+|task-T[1-6]-[A-Z0-9-]+)-savegames\.json$/.test(name)){
   const file=path.join(dir,name),raw=JSON.parse(await fs.readFile(file,'utf8'));if(!raw.items?.[headKey])continue;const head=JSON.parse(raw.items[headKey]);templates.set(head.chapter,file);
   if(name.startsWith('task-')&&!head.taskResume){const id=name.slice(5,-15);if(head.node==='v4:input:'+id)actual.set(id,file);}
  }
 }
 const canonical=path.join(root,'Saved/ui-checkpoints/normal-ch3-latest/savegames.json');
 const normal=await fs.readFile(canonical);assert.equal(sha(normal),'d43c126c6df61cb9f96b312cb65fdcf9992605368617f23c572fc5c6e9850fe7');
 actual.set('T3-NS-A11',canonical);
 const coverage=JSON.parse(await fs.readFile(path.join(root,'Saved/native-coverage-fixtures-latest.json'),'utf8'));
 const fixtureRoot=path.resolve(root,'..',coverage.work),snapshots=new Map((await fs.readFile(path.join(fixtureRoot,'task-fixtures.jsonl'),'utf8')).trim().split('\n').map(line=>{const j=JSON.parse(line);return [j.taskId,j.state];}));
 return {actual,templates,snapshots,fixtureRoot};
}
export async function publishCaseSave({work,session,catalogue,taskId,branch}){
 const original=taskId?catalogue.actual.get(taskId):null,snapshot=branch?.state||catalogue.snapshots.get(taskId);assert(original||snapshot,'Task has no real save or reachable-state snapshot');
 const source=original||path.join(catalogue.fixtureRoot,branch?'menu-fixtures.jsonl':'task-fixtures.jsonl');const bytes=await fs.readFile(source),flat=original?JSON.parse(bytes):{items:{}};
 if(!original){
  // Fresh supported optional defaults; do not inherit unrelated chapter progress.
  const head={...snapshot,coins:10,bonds:{},gifts:{},documents:{},presentation:{},world:{},worldId:'plaza',trialResultOpen:false,trialChoice:{},cards:Object.keys(snapshot.evidence),court:{active:!!taskId}};
  if(taskId){const full=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/chapters',snapshot.chapter+'.json'),'utf8'));head.court.dead=full.nodes[snapshot.node].trialDead||full.trialRoster?.dead||[];}
  flat.items[headKey]=JSON.stringify(head);
 }
 const destination=path.resolve(session,'State/Saves');assert(destination.startsWith(path.resolve(work)+path.sep));await fs.mkdir(destination,{recursive:true});const suffix='.project.004a6371-3a84-4fc3-8b54-31a5001740dd',slots=[];
 for(const[key,text]of Object.entries(flat.items))if(key.startsWith(prefix)&&key.endsWith(suffix)){const slot=key.slice(prefix.length,-suffix.length);assert(slot&&!/[\\/\x00-\x1f]/.test(slot)&&!['.','..'].includes(slot));slots.push([slot,text]);}
 slots.sort((a,b)=>(a[0]==='yumeno-progress-v4')-(b[0]==='yumeno-progress-v4'));
 for(const[slot,text]of slots){JSON.parse(text);const file=path.join(destination,encodeURIComponent(slot)+'.json'),temporary=file+'.fixture.tmp';await fs.writeFile(temporary,text);await fs.rename(temporary,file);}
 assert.equal(sha(await fs.readFile(source)),sha(bytes));const head=JSON.parse(flat.items[headKey]);return {source,sourceSHA256:sha(bytes),fixture:!original,entry:head.node,evidence:Object.keys(head.evidence||{}),scope:original?'Unchanged actual prior task checkpoint copied to owned native slots.':'Explicit reachable structural precondition with supported fresh optional defaults. Current gameplay outcomes are never injected.'};
}
