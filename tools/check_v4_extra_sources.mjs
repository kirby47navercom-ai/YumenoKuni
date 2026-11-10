// Generated-data check only. Never launches a game or modifies generated assets.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {validGameJson} from '../../engineCreate/prototype/game-json.js';
import {validWidgetAsset} from '../../engineCreate/prototype/ui-assets.js';
import {emitExtraV4} from '../Game/tools/v4-extra-ui.mjs';
import {emitDifficultyV4} from '../Game/tools/v4-difficulty-ui.mjs';
import {emitMineV4} from '../Game/tools/v4-mine-ui.mjs';
const repo=path.dirname(path.dirname(fileURLToPath(import.meta.url))),root=path.join(repo,'Game');
const outputs=[];const expected=await emitExtraV4({repo,root,body:'unused',head:'unused',write:async(file)=>outputs.push(file)});
const difficulty=await emitDifficultyV4({repo,write:async(file)=>outputs.push(file)});
const mine=await emitMineV4({write:async(file)=>outputs.push(file)});
const refs=new Set(),read=async file=>JSON.parse(await fs.readFile(path.join(root,file),'utf8'));
const walk=value=>{if(typeof value==='string'&&value.startsWith('Assets/'))refs.add(value);else if(Array.isArray(value))value.forEach(walk);else if(value&&typeof value==='object')Object.values(value).forEach(walk);};
const widgets={};let jsonCount=0;
for(const file of outputs){await fs.access(path.join(root,file));if(!file.endsWith('.json'))continue;const j=await read(file);if(file.endsWith('.hbwidget.json')){assert(validWidgetAsset(j),file);assert(j.nodes.length<=256);assert.equal(new Set(j.nodes.map(n=>n.id)).size,j.nodes.length);widgets[file]=j.nodes.length;}else assert(validGameJson(j),file);walk(j);jsonCount++;}
for(const ref of refs)await fs.access(path.join(root,ref));
const catalog=await read('Assets/Data/v4_story/gallery_catalog.json');assert.deepEqual(Object.fromEntries(Object.entries(catalog.order).map(([key,rows])=>[key,rows.length])),expected.order);
assert.equal(new Set(Object.values(catalog.order).flat()).size,expected.records);
const machine=await read('Assets/Data/v4_story/machine_layout.json'),gallery=await read('Assets/Data/v4_story/gallery_layout.json');assert.equal(machine.handle.length,4);assert.equal(gallery.top.length,7);assert.equal(gallery.rows.length,11);
const art=await read('Assets/Data/art.json');for(const cue of ['sfx_coin','sfx_capsule','sfx_capsule_open','sfx_capsule_bonus']){assert(art.audio[cue],cue);await fs.access(path.join(root,art.audio[cue]));}
const growth=await read('Assets/Data/v4_story/growth.json');const skillData=JSON.parse(await fs.readFile(path.join(repo,'data/skills.json'),'utf8'));
for(const effect of ['undo_enable','safety_first','showdown_tug_half']){assert(growth.supportedEffects.includes(effect));assert(skillData.items.some(r=>r.effect===effect&&r.sourceLabel&&!r.legacyOnly));}
const remaining=JSON.parse(await fs.readFile(path.join(repo,'docs/analysis/v3_rebuild/remaining_main_skills_contract.json'),'utf8'));
for(const row of remaining.remaining_rows.filter(r=>r.classification===1)){const skill=skillData.items.find(s=>s.sourceLabel===row.label);assert(skill,row.label);assert.equal(skill.fp,row.purchaseFP);assert.equal(skill.sp,row.SP);assert.equal(skill.sourceSaveNo,row.saveNo);assert.equal(skill.sourceGroup,row.group);assert(growth.supportedEffects.includes(skill.effect));}
assert.equal(skillData.items.filter(s=>s.sourceLabel).length,43);assert.equal(widgets['Assets/UI/GalleryV4.hbwidget.json'],66);assert.equal(gallery.material.cursors.top.length,8);assert.equal(gallery.material.cursors.list.length,11);assert.equal(gallery.material.receipts.length,2);assert.deepEqual(gallery.material.text,{on:'#000000',off:'#666666'});assert(gallery.prices.every(r=>r[0]+r[2]<700));
assert(growth.supportedEffects.includes('two_dimensional_love'));const two=skillData.items.find(s=>s.sourceLabel==='TWO_DIMENSIONAL_LOVE');assert(two&&two.fp===0&&two.sp===6&&two.sourceSaveNo===46);assert(growth.supportedEffects.includes('white_lie'));const white=skillData.items.find(s=>s.sourceLabel==='WHITE_LIE');assert(white&&white.fp===0&&white.sp===6&&white.sourceSaveNo===25);
for(const effect of ['paranormal','robot_eye','laser_beam','triger_happy','intuition_of_god','wild_awakening','spark_it','roller_strategy','murder_smash','machine_gun','shotgun','grenade','zero_distance_shooting','ones_minds_eye','shift_down','shift_up','head_start_punch','swap_limit','silent_voice','mieru_goggles','abracadabra','calm_down_lv1','calm_down_lv2'])assert(growth.supportedEffects.includes(effect));
const difficultyLayout=await read('Assets/Data/v4_story/difficulty_layout.json');assert.equal(difficultyLayout.rows.length,3);assert.equal(difficultyLayout.values.flat().length,6);assert.equal(difficultyLayout.receipts.length,26);assert.equal(new Set(difficultyLayout.variants.flat(2)).size,27);
assert.equal(widgets['Assets/UI/MineV4.hbwidget.json'],253);for(const name of ['w','p','y','b'])await fs.access(path.join(root,'Assets/Art/ui/mine_'+name+'.svg'));
const report={status:'PASS',scope:'generated Extra/difficulty/mine JSON/widget bounds, unique widget IDs, optimized references, catalog identity, source cost/header/effect carriers, four machine cues, forty-three source skills including normal Nonstop lie cost, eligible climax auto-placement and focus/idle aim helpers and projectile/recovery skills and source minigame skills; no player launch or pixel acceptance',...expected,difficulty,mine,jsonCount,widgets,assetReferences:refs.size};
const file=path.join(root,'Saved','extra-source-check-'+Date.now()+'.json');await fs.writeFile(file,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({...report,report:file}));
