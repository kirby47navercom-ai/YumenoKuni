// Isolated visual preconditions, not normal campaign progression evidence.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {incidentShots} from './v4-incident-shots.mjs';
import {v4Bucket} from './v4-data.mjs';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root);
const output=path.join(root,'Saved/native-panic-views-1793690486425/package');
const work=path.join(root,'Saved/native-incident-shots-'+Date.now());
await fs.mkdir(work,{recursive:true});
const read=async p=>JSON.parse(await fs.readFile(p,'utf8')),sha=b=>createHash('sha256').update(b).digest('hex');
const graphsRoot=process.argv.find(x=>x.startsWith('--graphs-root='))?.slice(14)||path.join(repo,'data/v4_story');
const only=process.argv.find(x=>x.startsWith('--only='))?.slice(7).split(',');
const graphs={};for(let c=1;c<=6;c++)graphs[`chapters/${c}.json`]=await read(path.join(graphsRoot,`chapters/${c}.json`));
const selection=await read(path.join(repo,'art/v4_production/forensic_repair/selected.json'));
const shots=incidentShots(graphs,selection),manifest=await read(path.join(output,'game.hbpack.json'));
assert(!manifest.contentArchive,'Only the existing loose, owned QA package may be patched');
const report={work,fixture:true,shipping:false,scope:'Six isolated discovery visual preconditions. No canonical saves, flags, evidence, original engine files or shipping assets changed. No campaign completion claim.',events:[],changes:[]};
const put=async(relative,bytes)=>{
 const file=path.join(output,relative);assert(path.resolve(file).startsWith(output+path.sep));
 await fs.mkdir(path.dirname(file),{recursive:true});
 const temp=file+'.incident.tmp';await fs.writeFile(temp,bytes);await fs.rename(temp,file);
 let row=manifest.files.find(r=>r.path===relative);
 report.changes.push({path:relative,before:row?.sha256,after:sha(bytes)});
 if(!row){row={path:relative};manifest.files.push(row);}
 row.bytes=bytes.length;row.sha256=sha(bytes);
 const asset=relative.slice('Content/'.length);
 if(!manifest.entries.some(e=>e.path===asset))manifest.entries.push({path:asset,name:path.basename(asset),kind:'texture'});
};
const packets=new Map();
// Reusing one owned package must not retain an older discovery image binding.
for(let bucket=0;bucket<128;bucket++){
 const name=`Content/Assets/Data/v4_story/nodes/${bucket}.json`,packet=await read(path.join(output,name));let changed=false;
 for(const node of Object.values(packet.nodes))if(node.shot?.incident){delete node.shot;changed=true;}
 if(changed)packets.set(name,packet);
}
// Two reviewed stage nodes changed only the announcement/confirmation order.
if(process.argv.some(x=>x.startsWith('--graphs-root=')))for(const id of ['v4:13b2:I3-22:e:eae0cd0fde5a:1','v4:13b2:I3-24:e:b101f8ca7f30:1']){
 const source=graphs['chapters/3.json'].nodes[id];assert(source);
 const name=`Content/Assets/Data/v4_story/nodes/${v4Bucket(id,128)}.json`;
 if(!packets.has(name))packets.set(name,await read(path.join(output,name)));
 const node=packets.get(name).nodes[id];assert(node);
 for(const key of ['direction','presentation','music','sfx']){if(key in source)node[key]=source[key];else delete node[key];}
}
for(const event of shots.events){
 const asset='Assets/Art/v4_story/'+sha(event.image).slice(0,16)+path.extname(event.image);
 await put('Content/'+asset,await fs.readFile(path.join(repo,event.image)));
 for(const id of event.nodes){
  const name=`Content/Assets/Data/v4_story/nodes/${v4Bucket(id,128)}.json`;
  if(!packets.has(name))packets.set(name,await read(path.join(output,name)));
  const node=packets.get(name).nodes[id];assert(node,'Stable discovery node is absent in the candidate: '+id);
  node.shot={...shots.byNode.get(id),image:asset};
 }
 event.asset=asset;
}
for(const [name,packet]of packets)await put(name,Buffer.from(JSON.stringify(packet)));
await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest));
const prepared={output,manifest,executable:path.join(output,manifest.windowsApplication.executable)};
let p;
try{
 for(const event of shots.events.filter(e=>!only||only.includes(e.logical))){
  const graph=Object.values(graphs).find(g=>g.nodes[event.event]);let before=graph.nodes[event.event];
  for(let i=0;i<32;i++){
   const previous=Object.values(graph.nodes).filter(n=>n.next===before.id);assert.equal(previous.length,1);
   before=previous[0];if(before.type==='say')break;assert.equal(before.type,'stage');
  }
  assert.equal(before.type,'say');
  const directory=path.join(work,event.logical),fixture=path.join(directory,'fixture.json');await fs.mkdir(directory,{recursive:true});
  const state={schemaVersion:1,contentVersion:'v4',chapter:graph.chapter,node:before.id,generation:0,flags:{},evidence:{},read:[],stack:[],log:[],coins:10,bonds:{},gifts:{},cards:[],documents:{},presentation:{},world:{},worldId:'plaza',court:{active:false},trialResultOpen:false};
  const key='hbengine.savegame.json.yumeno-progress-v4.project.'+manifest.id;
  await fs.writeFile(fixture,JSON.stringify({version:1,items:{[key]:JSON.stringify(state)}}));
  p=await nativeWindowProbe({source:output,prepared,work:directory,resume:fixture,maxFrames:null,heartbeatTimeoutMs:120000});
  await p.hiddenBorderless();await p.resize(1280,720);await p.tap('c');
  await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.node===before.id;},'before discovery',120000);
  await p.capture('before');
  for(let i=0;i<12&&(await p.stats()).node!==event.heldReaction;i++)await p.tap('Enter');
  await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.node===event.heldReaction;},'held discovery reaction',30000);
  await p.sampled(3);await p.capture('discovery');
  if(event.logical==='incident_c3a'){
   const entered=Date.now();await p.until(async()=>Date.now()-entered>=2500,'discovery effect settling',5000);
   await p.capture('discovery-settled');
  }
  const view=await read(path.join(directory,'discovery.ui.json'));
  const main=view.widgets.find(w=>w.instance==='main');
  const background=main.nodes.find(n=>n.id==='Background').properties;
  assert.equal(background.visible,true);assert.equal(background.texture,event.asset);
  const beforeView=await read(path.join(directory,'before.ui.json'));
  assert.equal(beforeView.widgets.find(w=>w.instance==='main').nodes.find(n=>n.id==='Background').properties.visible,false);
  const observed=await p.stats();
  for(let i=0;i<12&&(await p.stats()).node===event.heldReaction;i++)await p.tap('Enter');
  await p.sampled(3);await p.capture('after');
  const after=await p.stats();assert.notEqual(after.node,event.heldReaction);
  const afterView=await read(path.join(directory,'after.ui.json'));
  assert.equal(afterView.widgets.find(w=>w.instance==='main').nodes.find(n=>n.id==='Background').properties.visible,false);
  const runtime=await p.close();p=null;
  report.events.push({logical:event.logical,before:before.id,reaction:observed.node,after:after.node,asset:event.asset,captures:directory,runtime,widgetSchema:main?Object.keys(main):null});
  await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));
  console.log(event.logical+' actual before / reveal / return captured');
 }
 report.ok=true;
}catch(error){report.error=error.stack;report.last=await p?.stats().catch(()=>null);await p?.capture('failure').catch(()=>{});process.exitCode=1;}
finally{await p?.close().catch(()=>{});await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({work,ok:report.ok,events:report.events.length,error:report.error?.split('\n')[0]}));}
