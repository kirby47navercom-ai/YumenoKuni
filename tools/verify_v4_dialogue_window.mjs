import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {emitV4DialogueWindow} from '../Game/tools/v4-dialogue-window-ui.mjs';
import {validGameJson} from '../../engineCreate/prototype/game-json.js';
const repo=path.dirname(path.dirname(fileURLToPath(import.meta.url))),files=new Map();
const layout=await emitV4DialogueWindow({repo,write:async(k,v)=>files.set(k,v)});
assert(layout.nameAssets['???'],'First encounter needs an outlined unknown-name carrier');
const c=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/dialogue_window_ui_contract.json'),'utf8'));
assert(validGameJson(layout));assert.deepEqual(layout.body,c.families.ordinary_window.snapshots.fl_nomal_wait.find(x=>x.text_header).own_projection_rect_1280);
assert.equal(layout.font,c.text_and_color.normal_window_font_axis_height_own_1280);assert.equal(layout.ownWrap.rows,3);assert(layout.ownWrap.width<layout.body[2]);
for(const branch of ['normal','hero']){assert.deepEqual(layout.names[branch],c.name_content_and_first_glyph.source_name_rects[branch].map(n=>n*2/3));assert.deepEqual(layout.namebase[branch],c.name_content_and_first_glyph.source_namebase_rects[branch].map(n=>n*2/3));}
assert.deepEqual(layout.next,c.families.page_indicator.snapshots.fl_wait[0].own_projection_rect_1280);
assert.deepEqual(layout.trial.body,c.trial_dialogue_binding.line_capacity_and_art_limits.body_bottom_center_own);assert.equal(layout.trial.font,30);assert.equal(layout.trial.rows,2);assert.deepEqual(layout.trial.ownWIN,[0,1,1,1]);
assert.deepEqual(layout.trial.name,c.families.trial_frame_name.snapshots.fl_wait_d.find(x=>x.path==='p_t_kaiwa_chara_name_000_jp/depth1').own_projection_rect_1280);
assert.deepEqual(layout.trial.nextBar,c.trial_next_indicator.manual_wait_summary.bar_own_rect);assert.deepEqual(layout.trial.nextHand,c.trial_next_indicator.manual_wait_summary.hand_own_rect);
for(const [name,asset] of Object.entries(layout.nameAssets)){const svg=files.get(asset);assert(svg.includes('<path')&&svg.includes('0 0 455 65'),name);assert(!svg.includes('<text')&&!svg.includes('<script'),name);}
console.log(JSON.stringify({ok:true,sourceADV:true,font:layout.font,names:Object.keys(layout.nameAssets).length,generatedBytes:Buffer.byteLength(JSON.stringify(layout)),noFirstGlyphOverlay:true,gameFilesWritten:0,runtimeAccepted:false}));
