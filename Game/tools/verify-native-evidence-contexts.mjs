// Actual owned inventory selections, using a retained normal chapter-six save.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {caseSaveCatalogue,publishCaseSave} from './native-case-saves.mjs';
import {createHash} from 'node:crypto';
const root=path.resolve(import.meta.dirname,'..'),output=path.join(root,'Saved/native-panic-views-1793690486425/package'),work=path.join(root,'Saved/native-evidence-contexts-'+Date.now());await fs.mkdir(work,{recursive:true});
const manifest=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8')),prepared={output,manifest,executable:path.join(output,manifest.windowsApplication.executable)};
const task='T6-EVIDENCE-A01',ids=process.argv.find(a=>a.startsWith('--ids='))?.slice(6).split(',')||['v4:E1-01','v4:E2-01','v4:3:knowledge:file-first','v4:3:knowledge:file-second','v4:4:knowledge:death-file','v4:E5-01'];
const sourceTask=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/native_tasks.json'),'utf8')).tasks[task];
const evidenceArt=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/v4_story/evidence_art.json'),'utf8')).items;
const width=Number(process.argv.find(a=>a.startsWith('--width='))?.slice(8)||3840),height=Number(process.argv.find(a=>a.startsWith('--height='))?.slice(9)||2160);assert(Number.isInteger(width)&&Number.isInteger(height)&&width>=640&&height>=360);
// Only the declared evidence map and its referenced images enter the owned QA.
for(const asset of new Set(['Assets/Data/v4_story/evidence_art.json',...Object.values(evidenceArt).flat().map(v=>v.image)])){
 const file=path.resolve(root,asset);assert(file.startsWith(path.join(root,'Assets')+path.sep));
 const relative='Content/'+asset,destination=path.resolve(output,relative);assert(destination.startsWith(output+path.sep));
 const bytes=await fs.readFile(file);await fs.mkdir(path.dirname(destination),{recursive:true});await fs.writeFile(destination,bytes);
 const row=manifest.files.find(r=>r.path===relative)||{path:relative};if(!manifest.files.includes(row))manifest.files.push(row);Object.assign(row,{bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
 if(!manifest.entries.some(r=>r.path===asset))manifest.entries.push({path:asset,name:path.basename(asset),kind:asset.endsWith('.json')?'data':'texture'});
}
await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest));
const report={work,task,shipping:false,resolution:[width,height],images:[],scope:'Explicitly acquired reviewed contexts, actual native selection and return. No new evidence grants or extra medical facts.'};let p;
try{
 p=await nativeWindowProbe({source:output,prepared,work,maxFrames:null,heartbeatTimeoutMs:120000});await p.hiddenBorderless();await p.resize(width,height);
 report.precondition=await publishCaseSave({work,session:work,catalogue:await caseSaveCatalogue(),taskId:task});
 assert(ids.every(id=>report.precondition.evidence.includes(id)),'All displayed contexts must already be owned');
 const owned=new Set(report.precondition.evidence),choices=sourceTask.stage.options.filter(row=>!sourceTask.stage.filterOwnedEvidence||owned.has(row.id));
 await p.tap('s');await p.tap('w');await p.tap('c');await p.until(async()=>(await p.stats()).taskId===task,'saved evidence task',120000);
 await p.tap('F2');await p.key('Control',true);
 const entrance=Date.now();let armed=false;
 while(Date.now()-entrance<120000){const s=await p.stats();assert(!s.error,s.error);if(!s.taskQueue&&s.taskInputArmed){armed=true;break;}if(s.taskQueue)await p.tap('Enter');else await p.sampled(3);}
 assert(armed,'Evidence entry dialogue must finish before inventory navigation');
 for(let i=0;i<ids.length;i++){
  const id=ids[i],index=choices.findIndex(row=>row.id===id);assert(index>=0);let found=false;
  for(let n=0;n<choices.length+2;n++){const s=await p.stats();assert(!s.error,s.error);const selected=s.stage.selection;if(selected===index){found=true;break;}assert(Number.isInteger(selected));const forward=(index-selected+choices.length)%choices.length,back=(selected-index+choices.length)%choices.length;await p.tap(forward<=back?'s':'w');}
  assert(found,'Acquired evidence must remain selectable: '+id);await p.sampled(45);
  const name='context-'+(i+1);await p.capture(name);const ui=JSON.parse(await fs.readFile(path.join(work,name+'.ui.json'),'utf8')),picker=ui.widgets.find(w=>w.instance==='trialpickerv4'),nodes=new Map(picker.nodes.map(n=>[n.id,n]));
  assert(nodes.get('PkEvidenceImage').properties.visible);assert(/\.(png|webp|svg)$/.test(nodes.get('PkEvidenceImage').properties.texture));
  assert.equal(nodes.get('PkEvidenceTitle').properties.text,choices[index].name,'Actual UI selection agrees with owned authored evidence order');
  const r=nodes.get('PkEvidenceImage').slot.offset;assert(r[1]>=140&&r[1]+r[3]<=400,'Evidence image reserves the live status and title areas');
  report.images.push({id,capture:name,texture:nodes.get('PkEvidenceImage').properties.texture,title:nodes.get('PkEvidenceTitle').properties.text});
  const expected=evidenceArt[id];assert.equal(nodes.get('PkEvidenceImage').properties.texture,expected[0].image);
  for(let page=1;page<expected.length;page++){
   await p.tap('d');await p.sampled(30);const pageName=name+'-page-'+(page+1);await p.capture(pageName);
   const snapshot=JSON.parse(await fs.readFile(path.join(work,pageName+'.ui.json'),'utf8')),pageNodes=new Map(snapshot.widgets.find(w=>w.instance==='trialpickerv4').nodes.map(n=>[n.id,n]));
   assert.equal(pageNodes.get('PkEvidenceImage').properties.texture,expected[page].image);assert.equal(pageNodes.get('PkEvidencePage').properties.text,(page+1)+' / '+expected.length);
   report.images.push({id,page:page+1,capture:pageName,texture:expected[page].image});
  }
  if(expected.length>1){await p.tap('d');await p.sampled(3);}
 }
 for(let n=0;n<300;n++){const s=await p.stats();assert(!s.error,s.error);if(s.lastTaskOutcome?.taskId===task&&s.taskId!==task){report.after=s.node;break;}if(s.taskQueue){await p.tap('Enter');continue;}const a=s.auto;if(a?.kind==='key')await p.tap(a.key);else if(a?.kind==='click')await p.click(a.x,a.y);else await p.sampled(2);}
 assert(report.after,'Actual existing correct answer must return');await p.key('Control',false);report.runtime=await p.close();p=null;report.ok=true;
}catch(error){report.error=error.stack;report.last=await p?.stats().catch(()=>null);await p?.capture('failure').catch(()=>{});process.exitCode=1;
}finally{await p?.close().catch(error=>{report.shutdownError=error.stack;report.ok=false;process.exitCode=1;});await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({work,ok:report.ok,images:report.images.length,error:report.error?.split('\n')[0]}));}
