// Actual asset paths + engine mixer state math, with no player/audio execution.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {MixerState,dbGain,validAudioMixer} from '../Game/engineCreate/prototype/audio-mixer.js';
import {validWidgetAsset} from '../Game/engineCreate/prototype/ui-assets.js';
import {emitOptionsV4} from './v4_options_widget.mjs';
const repo=path.dirname(path.dirname(fileURLToPath(import.meta.url))),files=new Map(),copied=[];
const report=await emitOptionsV4({repo,
  copy:async(source,target)=>{assert.ok((await fs.stat(path.join(repo,source))).isFile());copied.push({source,target});},
  write:async(target,value)=>files.set(target,value)});
const widget=files.get(report.widget),mixer=files.get(report.mixer);
assert.ok(validWidgetAsset(widget));assert.ok(validAudioMixer(mixer));
assert.equal(widget.nodes.filter(n=>/^Row\d+$/.test(n.name)).length,8);
assert.ok(widget.nodes.length<=256);assert.equal(widget.nodes.filter(n=>/^FPS\d+_\d$/.test(n.name)).length,24);
const root=widget.nodes.find(n=>n.name==='OptionsRoot');assert.equal(root.properties.visible,false);
const ids=new Set(widget.nodes.map(n=>n.id));
for(const n of widget.nodes){
  assert.ok(!n.parent||ids.has(n.parent));
  if(n.id==='root')continue;
  const [x,y,w,h]=n.slot.offset;assert.ok([x,y,w,h].every(Number.isFinite)&&w>0&&h>0,n.name+' invalid source carrier');
}
for(const n of widget.nodes.filter(n=>n.type==='Image'&&n.properties.texture))
  assert.ok(copied.some(c=>c.target===n.properties.texture)||files.has(n.properties.texture)||(["DisplayKeep","DisplayRevert"].includes(n.id)&&await fs.stat(path.join(repo,"Game",n.properties.texture)).then(s=>s.isFile())),n.name+' not copied');
assert.deepEqual(mixer.buses.map(b=>b.id),['master','music','sfx','ui','voice']);
assert.ok(mixer.buses.every(b=>b.volumeDb===0));
const state=new MixerState(mixer);
for(const name of ['Master','Music','SFX','UI','Voice'])assert.equal(dbGain(state.get(name)),1);
state.set('Music',20*Math.log10(.5));assert.ok(Math.abs(dbGain(state.get('Music'))-.5)<1e-9);
assert.equal(dbGain(state.get('SFX')),1);assert.equal(dbGain(state.get('UI')),1);
state.set('Music',-80);assert.equal(dbGain(state.get('Music')),0);
state.set('Master',-80);assert.equal(dbGain(state.get('Master')),0);
const contract=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/options_ui_contract.json'),'utf8'));for(let i=0;i<8;i++){const node=widget.nodes.find(n=>n.id==='Label'+i),r=[...contract.key_first_row_geometry.label_text];r[1]+=i*contract.coordinate_contract.row_gap_1280;node.slot.offset.forEach((v,j)=>assert(Math.abs(v-r[j])<.002));assert.equal(node.properties.fontSize,30);}assert.equal([...files.keys()].filter(k=>k.includes('/v3row/')&&k.endsWith('.svg')).length,58);assert.equal(report.totalSettings,15);
console.log(JSON.stringify({status:'pass',gameFilesWritten:0,audioPlayed:false,mixerMathOnly:true,copiedAssets:copied.length,...report}));
