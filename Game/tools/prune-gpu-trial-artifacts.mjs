// Move obsolete generated aliases/statement rigs out of the active asset tree.
// Source art, current glyphs and current statement batches are never removed.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game);
export async function archiveGpuTrialArtifacts({output,aliases,batches}){
 const base=path.resolve(output,'Assets/Art/ui/gpu_trial');
 assert(base.startsWith(game+path.sep),'Archive only game-owned generated GPU assets');
 const keepAliases=new Set(aliases),keepSprites=new Set(batches.map(b=>path.basename(b.sprite))),keepRigs=new Set(batches.map(b=>path.basename(b.rig)));
 const names=await fs.readdir(base),stale=names.filter(n=>/^a_[0-9a-f]{8}\.hbsprite\.json$/.test(n)?!keepAliases.has(n):/^g_[0-9a-f]{8}_line\.hbsprite\.json$/.test(n)?!keepSprites.has(n):/^g_[0-9a-f]{8}\.hbspriterig\.json$/.test(n)?!keepRigs.has(n):false);
 if(!stale.length)return {moved:0};
 const archive=path.resolve(repo,'삭제 대기','오래된_GPU_문자_'+Date.now());assert(archive.startsWith(path.join(repo,'삭제 대기')+path.sep));await fs.mkdir(archive,{recursive:true});const rows=[];
 for(const name of stale){const from=path.resolve(base,name),to=path.resolve(archive,name);assert(from.startsWith(base+path.sep)&&to.startsWith(archive+path.sep));const bytes=await fs.readFile(from);await fs.rename(from,to);rows.push({from:path.relative(repo,from),to:path.relative(repo,to),bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});}
 await fs.writeFile(path.join(archive,'receipt.json'),JSON.stringify({rows,freedBytes:0,scope:'Only aliases and statement rigs absent from the newly generated lookup/batch sets. Original art and current assets preserved.'},null,2));return {moved:rows.length,archive,freedBytes:0};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){const layout=JSON.parse(await fs.readFile(path.join(game,'Assets/Data/gpu_trial_layout.json'),'utf8')),header=await fs.readFile(path.join(game,'Source/GpuTrialAtlasDataV4.hpp'),'utf8'),parts=await Promise.all([...header.matchAll(/#include "(GpuTrialAtlasRows[0-9]+\.inl)"/g)].map(m=>fs.readFile(path.join(game,'Source',m[1]),'utf8'))),aliases=[...[header,...parts].join('\n').matchAll(/\{0x([0-9a-f]+)u,/g)].map(m=>'a_'+m[1].padStart(8,'0')+'.hbsprite.json');assert(aliases.length>0&&layout.batches.length>0);console.log(JSON.stringify(await archiveGpuTrialArtifacts({output:game,aliases,batches:layout.batches})));}
