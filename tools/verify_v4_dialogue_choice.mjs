import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {emitV4DialogueChoice} from '../Game/tools/v4-dialogue-choice-ui.mjs';
import {validGameJson} from '../../engineCreate/prototype/game-json.js';
const repo=path.dirname(path.dirname(fileURLToPath(import.meta.url))),files=new Map();
const layout=await emitV4DialogueChoice({repo,write:async(k,v)=>files.set(k,v)});
const c=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/dialogue_choice_ui_contract.json'),'utf8'));
assert.deepEqual(layout.source,c.ordinary_geometry.own_projection);assert.equal(layout.tracks.length,9);
for(const track of layout.tracks){const source=c.selection_confirm.tracks.find(t=>t.count===track.count&&t.selected_index===track.index);assert.equal(track.frames.length,source.select_track.length);for(let i=0;i<track.frames.length;i++)for(const [key,original]of [['base','base_xy'],['text','text_xy'],['active','active_xy']]){if(source.select_track[i][original]===null)assert.equal(track.frames[i][key],null);else track.frames[i][key].forEach((n,j)=>assert(Math.abs(n-source.select_track[i][original][j]*2/3)<.0001));}}
assert(Math.abs(layout.source.font_height-40*2/3)<.0001);assert(Math.abs(layout.source.base_x+layout.source.base_w-1976*2/3)<.0001);
const advances=Object.assign({},...layout.advances);for(const g of ['가','A','W',' '])assert(advances[g]>0);assert(advances.W>advances[' ']);assert(validGameJson(layout));
assert(JSON.stringify(layout).length<400000);assert.equal(files.size,5);
console.log(JSON.stringify({ok:true,sourceCounts:[2,3,4],exactFocusTracks:9,font:layout.source.font_height,glyphs:Object.keys(advances).length,metricBuckets:layout.advances.length,generatedBytes:Buffer.byteLength(JSON.stringify(layout)),gameFilesWritten:0,runtimeAccepted:false}));
