// Actual engine storage service with filesystem data, without any player/scene.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {validGameJson} from '../../engineCreate/prototype/game-json.js';
import {createPersistentQueries} from '../../engineCreate/prototype/runtime-storage.js';
import {V4_DATA_PACKS,packV4Data,activeV4DataPaths,validateV4DataBudget} from '../Game/tools/v4-data-pack.mjs';
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const digest=v=>createHash('sha256').update(JSON.stringify(canonical(v))).digest('hex');
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));let logical=0,maxChars=0;
const cpp=await fs.readFile('Game/Source/StoryGraphV4.hpp','utf8');
for(const [family,count] of Object.entries(V4_DATA_PACKS))assert(cpp.includes('prefix=="Assets/Data/v4_story/'+family+'/"?'+count+':'),'Runtime/producer pack count mismatch: '+family);
const baselineFlag=process.argv.indexOf('--baseline'),baseline=baselineFlag<0?null:await read(process.argv[baselineFlag+1]);
for(const [family,count]of [['native_tasks',64],['gallery_map',128],['gallery_records',64]]){
 const shards=Array(count),actual=[];
 for(let file=0;file<V4_DATA_PACKS[family];file++){
  const pack=await read('Game/Assets/Data/v4_story/'+family+'/pack_'+file+'.json');assert(validGameJson(pack));maxChars=Math.max(maxChars,JSON.stringify(pack).length);actual.push(pack);
  for(const [index,body]of Object.entries(pack.buckets)){assert.equal(Number(index)%V4_DATA_PACKS[family],file);assert.equal(shards[index],undefined);shards[index]=body;}
 }
 assert.equal(shards.filter(Boolean).length,count);assert.deepEqual(packV4Data(family,shards),actual);
 if(baseline)assert.deepEqual(shards.map(digest),baseline.families[family],family+' logical data changed');logical+=count;
 assert(!(await fs.readdir('Game/Assets/Data/v4_story/'+family)).some(f=>/^\d+\.json$/.test(f)),family+' obsolete generated leaves not archived');
}
// Inspect current emitted paths; old audit inventories may name retired packs.
const paths=new Set(await activeV4DataPaths(path.resolve('Game')));
for(const family of Object.keys(V4_DATA_PACKS))assert(!(await fs.readdir('Game/Assets/Data/v4_story/'+family)).some(file=>/^pack_(\d+)\.json$/.test(file)&&Number(file.match(/^pack_(\d+)\.json$/)[1])>=V4_DATA_PACKS[family]),family+' excess physical pack still active');
let reads=0;const query=createPersistentQueries({readAsset:async asset=>{reads++;return read(path.join('Game',asset));}});
for(const asset of paths){const returned=JSON.parse(await query('dataJsonRead',{path:asset}));assert(returned!==null);const at=reads;assert.deepEqual(JSON.parse(await query('dataJsonRead',{path:asset})),returned);assert.equal(reads,at);}
const validated=await validateV4DataBudget(path.resolve('Game'));assert.equal(validated.paths,paths.size);assert(validated.cacheEntries<=256&&validated.cacheBytes<=32*1024*1024);
// 256 bounds retained entries, not the number of files read over a game session.
let overflowReads=0;const overflow=createPersistentQueries({readAsset:async asset=>{overflowReads++;return {asset};}});
for(let i=0;i<257;i++)assert.equal(JSON.parse(await overflow('dataJsonRead',{path:'Assets/Data/cache-fixture/'+i+'.json'})).asset,'Assets/Data/cache-fixture/'+i+'.json');
assert.equal(overflowReads,257);assert(overflow.inspect().entries<=256);assert.equal(JSON.parse(await overflow('dataJsonRead',{path:'Assets/Data/cache-fixture/0.json'})).asset,'Assets/Data/cache-fixture/0.json');assert.equal(overflowReads,258);
const report={status:'PASS',logicalShards:logical,baselineLogicalDataExact:!!baseline,engineQueries:reads,paths:paths.size,cache:validated,maxPackedJSONCodeUnits:maxChars,immediateRepeatCached:true,moreThan256PathsReadable:true,evictedPathReloaded:true,scope:'Actual engine createPersistentQueries; bounded LRU retention does not impose a total path limit. Every active game JSON is validated and all logical bucket values compared to baseline.',playerLaunch:false};
await fs.writeFile('Game/Saved/data-pack-20261031.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
