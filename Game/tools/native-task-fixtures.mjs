import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {makeNode,connect} from '../../../engineCreate/prototype/blueprint-model.js';
import {createOwnedNativePackage} from './native-owned-package.mjs';
export async function prepareTaskFixtures(source,work,{gameModuleCandidate,gameContentOverrides}={}){
 const prepared=await createOwnedNativePackage({source,work,stats:true,gameModuleCandidate,gameContentOverrides}),name='Content/Assets/Blueprints/BP_Yumeno.hbblueprint.json',file=path.join(prepared.output,name),bp=JSON.parse(await fs.readFile(file,'utf8'));
 const link=(a,ap,b,bpPin)=>{const r=connect(bp,{node:a.id,pin:ap},{node:b.id,pin:bpPin});assert(r.ok,r.reason);};
 for(const[key,fn,inputs]of [['F2','Yumeno.DebugFastRead',{}]]){
  const input=makeNode('input',100,600),call=makeNode('nativeCall',400,600);input.options={key};call.nativeId=fn;call.inputValues=inputs;bp.nodes.push(input,call);link(input,'then',call,'exec');
 }
 const update=bp.nodes.find(n=>n.nativeId==='Yumeno.Update'),statsEdge=bp.edges.find(e=>e.from.node===update.id&&e.from.pin==='then'),statsPrint=bp.nodes.find(n=>n.id===statsEdge?.to.node),aim=makeNode('nativeCall',700,700),print=makeNode('print',1000,700);assert.equal(statsPrint?.key,'print');aim.nativeId='Yumeno.AimStats';bp.nodes.push(aim,print);link(statsPrint,'then',print,'exec');link(aim,'result',print,'message');
 const bytes=Buffer.from(JSON.stringify(bp));await fs.writeFile(file,bytes);const row=prepared.manifest.files.find(r=>r.path===name);Object.assign(row,{bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});await fs.writeFile(path.join(prepared.output,'game.hbpack.json'),JSON.stringify(prepared.manifest,null,2));
 const receipt=JSON.parse(await fs.readFile(path.join(work,'owned-package.json'),'utf8'));receipt.fixtureEntry='Task entry uses isolated actual saves or explicit reachable-state fixtures through ordinary Continue. F2 only enables unread Control skip. Task success and timers are never injected. Actual actions use Win32 input.';receipt.alterations.push({name,after:{bytes:row.bytes,sha256:row.sha256},scope:receipt.fixtureEntry});await fs.writeFile(path.join(work,'owned-package.json'),JSON.stringify(receipt,null,2));return prepared;
}
