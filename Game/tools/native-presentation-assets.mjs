// Explicit game-owned candidates only; publish atomically into one retained QA.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
export async function publishPresentationAssets(root,output,manifest,assets){
 assert(path.resolve(output).startsWith(path.join(root,'Saved/native-panic-views-')));
 const receipt=[],fileRows=new Map(manifest.files.map(r=>[r.path,r])),entryPaths=new Set(manifest.entries.map(r=>r.path));
 for(const relative of [...new Set(assets)]){
  assert(/^Assets\/(Art|UI|Data|Scenes)\//.test(relative)&&!relative.includes('..')&&!relative.includes('\\'));
  const bytes=await fs.readFile(path.join(root,relative)),name='Content/'+relative,target=path.join(output,name);
  const digest=createHash('sha256').update(bytes).digest('hex');let row=fileRows.get(name);
  const unchanged=row?.sha256===digest&&row.bytes===bytes.length&&await fs.stat(target).then(s=>s.size===bytes.length,e=>{if(e.code==='ENOENT')return false;throw e;});
  if(!unchanged){await fs.mkdir(path.dirname(target),{recursive:true});await fs.writeFile(target+'.presentation.tmp',bytes);await fs.rename(target+'.presentation.tmp',target);}
  if(!row){row={path:name};manifest.files.push(row);fileRows.set(name,row);}Object.assign(row,{bytes:bytes.length,sha256:digest});
  if(!entryPaths.has(relative)){entryPaths.add(relative);manifest.entries.push({path:relative,name:path.basename(relative),kind:relative.startsWith('Assets/Data/')?'data':relative.startsWith('Assets/UI/')?'widget':relative.startsWith('Assets/Scenes/')?'scene':'texture'});}
  receipt.push({path:relative,sha256:digest,bytes:bytes.length,reused:!!unchanged});
 }
 await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest));return receipt;
}
