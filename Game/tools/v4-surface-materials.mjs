// Publish owner-generated PBR models; no gameplay/source/save changes.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
import {emitLowpolyMaterials} from './v4-lowpoly-materials.mjs';
import {emitRebuiltEnvironment} from './v4-rebuilt-environment.mjs';
import {emitRebuiltDedicated} from './v4-rebuilt-dedicated.mjs';
export async function emitSurfaceMaterials({repo,write}){
 const manifest=await fs.readFile(path.join(repo,'art/space_v4/materials_v2/manifest.json'),'utf8').then(JSON.parse,e=>{if(e.code==='ENOENT')return null;throw e;});if(!manifest)return {models:0};
 const file=path.join(repo,'art/space_v4/runtime_v1/copy_manifest.json'),copies=JSON.parse(await fs.readFile(file,'utf8'));
 for(const a of manifest.assets){const b=await fs.readFile(path.join(repo,a.file));assert.equal(createHash('sha256').update(b).digest('hex'),a.sha256,a.file);await write(a.runtime,b);const row=copies.find(r=>r.to===a.runtime);if(row)row.from=a.file;}
 await fs.writeFile(file,JSON.stringify(copies,null,1)+'\n');const lowpoly=await emitLowpolyMaterials({repo,write});const rebuilt=await emitRebuiltEnvironment({repo,write});const dedicated=await emitRebuiltDedicated({repo,write});return {models:manifest.assets.length,seatingCorrections:manifest.assets.reduce((n,a)=>n+(a.seatCorrections?.length||0),0),lowpoly,rebuilt,dedicated,gameplayMetadataUnchanged:true,geometryUnchanged:lowpoly.models===0&&rebuilt.models===0&&dedicated.models===0};
}
