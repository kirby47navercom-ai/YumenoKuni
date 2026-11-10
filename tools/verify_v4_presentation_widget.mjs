// In-memory generator verification: no Game/Assets writes, build or player.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {emitPresentationV4} from './v4_presentation_widget.mjs';
const repo=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const original=await fs.readFile(path.join(repo,'data/presentation/v4.json'),'utf8');
const copies=new Map(),outputs=new Map();
const result=await emitPresentationV4({repo,
  copy:async(source,target)=>{assert.ok((await fs.stat(path.join(repo,source))).isFile());copies.set(target,source);},
  write:async(target,value)=>{outputs.set(target,value);}});
const widget=outputs.get('Assets/UI/PresentationV4.hbwidget.json');
assert.deepEqual(widget.nodes.filter(n=>n.type==='Image').map(n=>n.name),['FxFocus','FxNoise','FxImpact','FxTransition']);
assert.ok(widget.nodes.length<=256);
assert.ok(widget.nodes.filter(n=>n.type==='Image').every(n=>n.properties.visible===false&&n.properties.focusable===false));
const contract=outputs.get('Assets/Data/presentation/v4.json');
assert.equal(Object.keys(contract.sequences).length,14);
for(const seq of Object.values(contract.sequences))for(const frame of seq.frames)assert.ok(copies.has(frame));
assert.equal(await fs.readFile(path.join(repo,'data/presentation/v4.json'),'utf8'),original);
assert.equal(copies.size,144);
console.log(JSON.stringify({status:'pass',inMemory:true,gameFilesWritten:0,...result}));
