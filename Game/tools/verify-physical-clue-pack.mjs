// Verify the selected physical art in the final archive without changing saves,
// source registrations, original images or prior native acceptance records.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game);
const json=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const build=await json(path.join(game,'build-result.json'));
const manifest=await json(path.join(build.output,'game.hbpack.json'));
const {openGameResources}=await import(pathToFileURL(path.join(build.output,'tools/game-resource-archive.mjs')));
const archive=await openGameResources(path.join(build.output,manifest.contentArchive.path));
const checked=new Set();
async function same(name){
 if(checked.has(name))return;
 assert(!name.includes('..')&&name.startsWith('Assets/'));
 const packed=await archive.read(name),source=await fs.readFile(path.join(game,name));
 if(name.endsWith('.json'))assert.deepEqual(JSON.parse(packed.toString('utf8')),JSON.parse(source.toString('utf8')),name);
 else assert.equal(sha(packed),sha(source),name);
 checked.add(name);
}
try{
 let sourceFiles=0;
 for(const [name]of archive.entries)if(name.startsWith('Source/')){
  assert.equal(sha(await archive.read(name)),sha(await fs.readFile(path.join(game,name))),name+' changed since full build');sourceFiles++;
 }
 const artPath='Assets/Data/v4_story/evidence_art.json';await same(artPath);
 const art=JSON.parse((await archive.read(artPath)).toString('utf8'));
 const images=new Set(Object.values(art.items).flat().map(x=>x.image));
 for(const image of images)await same(image);
 let originals=0;
 for(const name of ['manifest.json','followup_manifest.json']){
  const list=await json(path.join(repo,'art/inspection_v4/physical_clues_20261104',name));
  for(const row of list.rows){
   assert.equal(sha(await fs.readFile(path.join(repo,row.original))),row.originalSha256);
   assert.equal(sha(await fs.readFile(path.join(repo,row.runtime))),row.runtimeSha256);
   originals++;
  }
 }
 const bank=await json(path.join(repo,'art/v4_production/mine_objects_20261104/reviewed-additions.json'));
 // The three formerly flat document banks contain eleven generated originals.
 let mineOriginals=0;
 for(const id of ['T1-MM-A03','T6-MM-A03','T6-MM-A02'])for(const item of bank[id].objects){
  assert((await fs.stat(item.source)).size>0);mineOriginals++;
 }
 const picker='Assets/Data/v4_story/trial_picker_layout.json';await same(picker);
 for(const title of Object.values(JSON.parse((await archive.read(picker)).toString('utf8')).titles))await same(title);
 assert(manifest.entries.some(x=>x.path==='Assets/Scenes/ArmamentHud.hbscene.json'));
 assert((await fs.readFile(path.join(build.output,manifest.windowsApplication.executable))).includes(Buffer.from('Render view count invalid')));
 const report={build:build.id,currentSourceFiles:sourceFiles,evidenceIds:Object.keys(art.items).length,uniqueSelectedImages:images.size,physicalEvidenceOriginals:originals,physicalMineOriginals:mineOriginals,checkedPackedAssets:checked.size,scope:'Current source matches packed source; selected evidence images, immutable originals, optimized picker titles, Armament scene and approved native render-view protocol. Not whole-game or every-branch visual acceptance.'};
 await fs.writeFile(path.join(game,'Saved/game-trial-work-20261102/final-clue-pack-20261104.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report));
}finally{await archive.close();}
