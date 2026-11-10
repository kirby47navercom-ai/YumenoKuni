import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {createOwnedNativePackage} from './native-owned-package.mjs';
const root=path.resolve(import.meta.dirname,'..'),build=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8')),work=path.join(root,'Saved/native-widget-snapshot-'+Date.now());
const baseline=path.join(root,'Builds/windows/2026-11-01T13-56-29-441Z-0fce033a'),{WidgetSystem:Original}=await import(pathToFileURL(path.join(baseline,'prototype/ui-runtime.js')));
const prepared=await createOwnedNativePackage({source:build.output,work,uiRuntimeCandidate:path.join(import.meta.dirname,'ui-runtime-snapshot.candidate.mjs')});
const {WidgetSystem:Candidate}=await import(pathToFileURL(path.join(prepared.output,'prototype/ui-runtime.js')));
const actual=JSON.parse(await fs.readFile(path.join(root,'Saved/native-all-tasks-1793541469758/session-1793541481899/task-t3-ns-a11.ui.json'),'utf8')).widgets;
const hooks={localization:{format:(table,key,args,fallback)=>key+':'+JSON.stringify(args)+':'+fallback}},old=new Original(hooks),candidate=new Candidate(hooks),left={id:'owner'},right={id:'owner'},vm1={object:()=>left},vm2={object:()=>right},state={owner:'owner',instance:'test',data:{nodes:structuredClone(actual.find(w=>w.nodes.length>10).nodes)}};
let oldMS=0,newMS=0,prior,priorJSON,checks=0;
for(let i=0;i<100;i++){
 const node=state.data.nodes[i%state.data.nodes.length];node.properties.rotation=i;node.properties.opacity=i/100;node.slot.offset[0]=i*3;node.properties.scale=[1+i*.01,1];node.properties.text='한글 상태 '+i;
 if(i===3)Object.assign(node.properties,{stringTable:'Assets/Test.hbstrings.json',textKey:'localized',textArguments:'{"x":3}'});
 let at=performance.now();old.sync(state,vm1);oldMS+=performance.now()-at;at=performance.now();candidate.sync(state,vm2);newMS+=performance.now()-at;
 assert.deepEqual(right.gameplayDebug,left.gameplayDebug);if(prior)assert.equal(JSON.stringify(prior),priorJSON,'Earlier immutable snapshot must not change');prior=right.gameplayDebug.ui.test;priorJSON=JSON.stringify(prior);assert(Object.isFrozen(prior));checks++;
}
const last=right.gameplayDebug.ui.test;candidate.sync(state,vm2);assert.equal(right.gameplayDebug.ui.test,last,'Unchanged snapshots reuse exact immutable identity');
state.data.nodes.pop();old.sync(state,vm1);candidate.sync(state,vm2);assert.deepEqual(right.gameplayDebug,left.gameplayDebug);checks++;
state.data.nodes.reverse();old.sync(state,vm1);candidate.sync(state,vm2);assert.equal(JSON.stringify(right.gameplayDebug),JSON.stringify(left.gameplayDebug));checks++;
const states=[old,candidate].map(system=>{const value={owner:'owner',instance:'batch',data:{nodes:structuredClone(actual.find(w=>w.nodes.length>10).nodes)}};system.instances.set(system.key('owner','batch'),value);return value;});
for(let frame=0;frame<30;frame++){
 const name=states[0].data.nodes.find(n=>n.type==='Text').name;
 const ops=[['uiSetPosition',{position:[frame,frame*2]}],['uiSetRotation',{rotation:frame*3}],['uiSetOpacity',{opacity:.25+frame*.01}],['uiSetText',{text:'상태 '+frame}],['uiSetVisible',{visible:frame%2===0}],['uiSetEnabled',{enabled:frame%3!==0}]];
 for(const [system,index,vm]of [[old,0,vm1],[candidate,1,vm2]])await system.writeBatch(async()=>{for(const[key,args]of ops)for(let repeat=0;repeat<2;repeat++)await system.operation(key,{instance:'batch',element:name,...args},{self:'owner'},vm);},vm);
 assert.deepEqual(right.gameplayDebug,left.gameplayDebug);checks++;
 const other=states[0].data.nodes.find(n=>n.name!==name);for(const s of states)s.data.nodes.find(n=>n.name===other.name).properties.text='external '+frame;
 old.refresh(states[0],vm1);candidate.refresh(states[1],vm2);assert.deepEqual(right.gameplayDebug,left.gameplayDebug);checks++;
}
const report={ok:true,checks,oldMS:oldMS/100,newMS:newMS/100,nodes:state.data.nodes.length,exactSnapshots:true,immutableHistory:true,removedRowsDropped:true,scope:'Actual large trial widget, repeated property/slot/text/locale changes and node removal; no gameplay execution.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({work,...report}));
