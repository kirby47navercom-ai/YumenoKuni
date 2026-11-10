// Existing V4 publisher for source-text iterations after a complete project generation.
import fs from 'node:fs/promises';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import {publishV4Data} from './v4-data.mjs';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root);
await fs.access(path.join(root,'Assets/Blueprints/BP_Yumeno.hbblueprint.json'));
const write=async(name,value)=>{const target=path.join(root,name),temporary=target+'.'+randomUUID()+'.tmp';await fs.mkdir(path.dirname(target),{recursive:true});try{await fs.writeFile(temporary,typeof value==='string'||Buffer.isBuffer(value)?value:JSON.stringify(value,null,1)+'\n');await fs.rename(temporary,target);}finally{await fs.rm(temporary,{force:true});}};
const copy=async(from,to)=>{await fs.mkdir(path.dirname(path.join(root,to)),{recursive:true});await fs.copyFile(path.join(repo,from),path.join(root,to));};
await publishV4Data({repo,write,copy});
console.log(JSON.stringify({ok:true,publisher:'publishV4Data',scope:'Authored V4 data/presentation only; no actor/map/font/audio regeneration or native build.'}));
