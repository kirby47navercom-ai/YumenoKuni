import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {validGameJson} from '../../../engineCreate/prototype/game-json.js';
export async function publishComicPagesOnly({repo,root,write}){
 const code='import json,sys;sys.path.insert(0,"tools");from v4_comic_presentation import build_comic,bind_task;from pathlib import Path;n=json.loads(Path("data/v4_story/native_tasks.json").read_text(encoding="utf-8"))["tasks"];c=build_comic();print(json.dumps({k:{"presentation":bind_task(n[k],c)["stage"]["comicPresentation"],"slots":bind_task(n[k],c)["stage"]["slots"]} for k in c["tasks"]},ensure_ascii=False))';
 const metadata=JSON.parse(execFileSync('python',['-X','utf8','-c',code],{cwd:repo,encoding:'utf8',maxBuffer:4*1024*1024})),assets=new Set();
 const map=async v=>{if(typeof v==='string'&&/^(art|ui)\/.*\.(png|svg|webp)$/.test(v)){const dest='Assets/Art/v4_story/'+createHash('sha256').update(v).digest('hex').slice(0,16)+path.extname(v);if(!assets.has(dest)){assets.add(dest);const bytes=await fs.readFile(path.join(repo,v)),existing=await fs.readFile(path.join(root,dest)).catch(e=>{if(e.code!=='ENOENT')throw e;return null;});if(!existing||!existing.equals(bytes))await write(dest,bytes);}return dest;}if(Array.isArray(v)){const a=[];for(const x of v)a.push(await map(x));return a;}if(v&&typeof v==='object'){const o={};for(const [k,x] of Object.entries(v))o[k]=await map(x);return o;}return v;};
 const changed=[],found=new Set();
 for(let i=0;i<32;i++){const name=`Assets/Data/v4_story/native_tasks/pack_${i}.json`,pack=JSON.parse(await fs.readFile(path.join(root,name),'utf8'));let dirty=false;for(const bucket of Object.values(pack.buckets))for(const [id,task] of Object.entries(bucket.tasks))if(metadata[id]){assert(!found.has(id));found.add(id);assert.equal(task.stage.kind,'climax');assert.deepEqual(task.stage.slots.map(s=>s.id),metadata[id].presentation.slots.map(s=>s.id));task.stage.comicPresentation=await map(metadata[id].presentation);for(let j=0;j<task.stage.slots.length;j++){const actual=task.stage.slots[j],bound=metadata[id].slots[j];assert.equal(actual.id,bound.id);for(const option of actual.options){const source=bound.options.find(o=>o.id===option.id);assert(source&&source.label===option.label);option.image=await map(source.image);}}dirty=true;}if(dirty){assert(validGameJson(pack),name);await write(name,pack);changed.push(name);}}
 assert.equal(found.size,6);return {comicPagesOnly:true,tasks:[...found],changed,assets:[...assets],answersChanged:false,dialogueChanged:false,runtimeVisualAcceptance:false};
}
