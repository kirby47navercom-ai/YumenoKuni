import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {validGameJson} from '../engineCreate/prototype/game-json.js';
import {createPersistentQueries} from '../engineCreate/prototype/runtime-storage.js';

// Logical hash buckets and stable IDs stay unchanged. Only physical reads shrink.
export const V4_DATA_PACKS={native_tasks:32,gallery_map:4,gallery_records:5};
export function packV4Data(family,shards){
 const count=V4_DATA_PACKS[family];if(!count||!Array.isArray(shards)||!shards.length)throw Error('Unknown V4 data pack family');
 const packs=Array.from({length:count},()=>({buckets:{}}));
 for(let i=0;i<shards.length;i++)packs[i%count].buckets[i]=shards[i];
 for(let i=0;i<packs.length;i++)if(!validGameJson(packs[i]))throw Error('V4 physical pack exceeds engine JSON bounds: '+family+'/'+i);
 return packs;
}
export async function activeV4DataPaths(root){
 const paths=new Set();
 for(const file of await fs.readdir(path.join(root,'Assets/Data'),{recursive:true}))if(file.endsWith('.json')){
  const name=file.replaceAll('\\','/');
  if(/^(flow|trials|scenes|explore3d)\//.test(name)||name.startsWith('v4_story/freetime/'))continue;
  paths.add('Assets/Data/'+name);
 }
 const layout=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/v4_story/trial_answer_layout.json'),'utf8'));
 for(const asset of Object.values(layout.tracks))paths.add(asset);
 return [...paths];
}
export async function validateV4DataBudget(root){
 const paths=await activeV4DataPaths(root);
 const query=createPersistentQueries({readAsset:async asset=>JSON.parse(await fs.readFile(path.join(root,asset),'utf8'))});
 for(const asset of paths)await query('dataJsonRead',{path:asset});
 const retained=query.inspect();
 return {paths:paths.length,cacheEntries:retained.entries,cacheBytes:retained.bytes,cacheEntryLimit:256,cacheByteLimit:32*1024*1024};
}
const batch='data-packing-'+new Date().toISOString().replace(/[:.]/g,'-');const moved=[];
export async function emitV4DataPacks({repo,write,family,shards}){
 const packs=packV4Data(family,shards),prefix='Assets/Data/v4_story/'+family+'/';
 for(let i=0;i<packs.length;i++)await write(prefix+'pack_'+i+'.json',packs[i]);
 const root=path.resolve(repo),directory=path.join(root,'Game',prefix),archive=path.join(root,'삭제 대기',batch);
 const inside=(base,target)=>{const relative=path.relative(base,target);return relative&&!relative.startsWith('..')&&!path.isAbsolute(relative);};
 for(const file of await fs.readdir(directory))if(/^\d+\.json$/.test(file)||(/^pack_(\d+)\.json$/.test(file)&&Number(file.match(/^pack_(\d+)\.json$/)[1])>=packs.length)){
  const source=path.resolve(directory,file),target=path.resolve(archive,path.relative(root,source));
  if(!inside(path.join(root,'Game','Assets'),source)||!inside(archive,target)||!(await fs.lstat(source)).isFile())throw Error('Unsafe generated data archive target');
  const bytes=await fs.readFile(source);await fs.mkdir(path.dirname(target),{recursive:true});await fs.rename(source,target);
  moved.push({source,target,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
 }
 if(moved.length)await fs.writeFile(path.join(root,'Game/Saved',batch+'.json'),JSON.stringify({policy:'obsolete generated numeric leaves or excess physical packs only; move to project-root deletion-pending folder; no deletion',archive,moved,deleted:0},null,2)+'\n');
 return packs.length;
}

// Regroup existing published logical buckets without reauthoring their values.
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)&&process.argv.includes('--repack-gallery-records')){
 const repo=path.resolve(import.meta.dirname,'../..'),directory=path.join(repo,'Game/Assets/Data/v4_story/gallery_records'),shards=[];
 for(const file of await fs.readdir(directory))if(/^pack_\d+\.json$/.test(file)){
  const pack=JSON.parse(await fs.readFile(path.join(directory,file),'utf8'));
  for(const [index,body]of Object.entries(pack.buckets)){if(shards[index]!==undefined)throw Error('Duplicate gallery bucket '+index);shards[index]=body;}
 }
 if(shards.length!==64||shards.filter(Boolean).length!==64)throw Error('Expected every existing gallery record bucket');
 const write=async(file,value)=>{const target=path.join(repo,'Game',file);await fs.mkdir(path.dirname(target),{recursive:true});await fs.writeFile(target,JSON.stringify(value,null,2)+'\n');};
 console.log(JSON.stringify({galleryRecordPacks:await emitV4DataPacks({repo,write,family:'gallery_records',shards}),logicalBuckets:shards.length}));
}
