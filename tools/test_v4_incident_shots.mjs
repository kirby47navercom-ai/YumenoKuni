import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {incidentShots} from '../Game/tools/v4-incident-shots.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const read=async p=>JSON.parse(await fs.readFile(path.join(root,p),'utf8'));
const graphs={};for(let chapter=1;chapter<=6;chapter++)graphs[`chapters/${chapter}.json`]=await read(`data/v4_story/chapters/${chapter}.json`);
const selected=await read('art/v4_production/forensic_repair/selected.json');
const result=incidentShots(graphs,selected);
assert.equal(result.events.length,6);
assert.equal(result.events.filter(e=>e.logical.startsWith('incident_c3')).length,2);
for(const event of result.events){
 await fs.access(path.join(root,event.image));
 const graph=Object.values(graphs).find(g=>g.nodes[event.event]);
 assert.equal(graph.nodes[event.heldReaction].type,'say');
 for(const id of event.nodes){assert.ok(['stage','say'].includes(graph.nodes[id].type));assert.equal(result.byNode.get(id).knowledgeGrant,false);}
 const after=graph.nodes[event.heldReaction].next;
 assert.equal(result.byNode.has(after),false,'CG must clear after its bounded reaction');
 const sourceLine=graph.nodes[event.event].source.line;
 for(const node of Object.values(graph.nodes))if(node.source?.file===graph.nodes[event.event].source.file&&node.source.line<sourceLine)assert.equal(result.byNode.has(node.id),false,'No reveal before discovery');
}
const broken=structuredClone(graphs);const first=result.events[0];
const brokenGraph=Object.values(broken).find(g=>g.nodes[first.event]);
brokenGraph.nodes[first.event].next='missing';
assert.throws(()=>incidentShots(broken,selected),/held authored reaction/);
assert.throws(()=>incidentShots(graphs,{overrides:{}}),/Selected incident art missing/);
const report={status:'source-contract-passed-not-runtime-tested',events:result.events,checks:['six discoveries','separate sequential chapter-three discoveries','selected delivery files exist','no early reveal','held authored reaction','clear before subsequent interaction','missing chain and art rejected'],runtimeVerified:false};
await fs.writeFile(path.join(root,'docs/analysis/v3_rebuild/사건_CG_연결_소스검증_20261103.json'),JSON.stringify(report,null,2)+'\n');
console.log('PASS: six discovery CGs, held reactions, no early reveal, bounded clear, invalid bindings rejected');
