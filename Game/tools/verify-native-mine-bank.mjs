// Reuse the single owned QA package for one explicitly reviewed mine bank.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),arg=p=>process.argv.find(x=>x.startsWith(p))?.slice(p.length);
const task=arg('--task='),module=arg('--game-module=');assert(task&&module,'Provide a task and an already compiled game-only candidate');
const bank=path.join(repo,'art/v4_production/mine_objects_20261104'),entries=JSON.parse(await fs.readFile(path.join(bank,'banks.json'),'utf8')),assets=new Set(['Assets/UI/Stage.hbwidget.json','Assets/Art/ui/mine_cursor.svg']),known=new Set();
for(const row of entries){assets.add(row.target);const s=JSON.parse(await fs.readFile(path.join(bank,row.selection),'utf8'));known.add(s.taskId);}
assert(known.has(task),'Task is not in the reviewed object bank');
// Use actual generated references: the full optimizer may losslessly convert
// the source PNGs to WebP. QA must exercise the same assets as the full build.
for(let i=0;i<32;i++){const name=`Assets/Data/v4_story/native_tasks/pack_${i}.json`,p=JSON.parse(await fs.readFile(path.join(root,name),'utf8'));for(const bucket of Object.values(p.buckets))for(const [id,t]of Object.entries(bucket.tasks))if(known.has(id)){assets.add(name);assert(t.stage.mineObjects?.length);for(const o of t.stage.mineObjects){assets.add(o.texture);assets.add(o.maskAsset);if(o.hintOutline)assets.add(o.hintOutline);}}}
for(const name of await fs.readdir(path.join(root,'Assets/UI')))if(/^Mine.*\.hbwidget\.json$/.test(name))assets.add('Assets/UI/'+name);
const child=spawn(process.execPath,[path.join(root,'tools/verify-native-all-tasks.mjs'),'--only='+task,'--mine-object-task='+task,'--mine-object-proof','--width=3840','--height=2160','--reuse-package=Saved/native-panic-views-1793690486425/package','--game-module='+module,'--candidate-assets='+[...assets].sort().join(',')],{cwd:repo,windowsHide:true,stdio:'inherit'});
process.exitCode=await new Promise((resolve,reject)=>{child.once('error',reject);child.once('close',resolve);});
