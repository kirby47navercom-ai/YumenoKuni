import fs from 'node:fs/promises';import path from 'node:path';
import{applyExplorationMaterialLight}from'./v4-exploration-material-light.mjs';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/facility-form-20261104'),file=path.join(work,'unlabelled-camera-overrides.json');
const base=JSON.parse(await fs.readFile(path.join(root,'Saved/game-trial-work-20261102/sculpted-overrides.json'),'utf8')),specific=JSON.parse(await fs.readFile(file,'utf8'));
const scene=path.join(work,'test-only-camera-scene.json');await fs.writeFile(scene,JSON.stringify(applyExplorationMaterialLight(JSON.parse(await fs.readFile(path.join(root,'Assets/Scenes/Explore.hbscene.json'),'utf8')))));
await fs.writeFile(file,JSON.stringify({...base,...specific,'Content/Assets/Scenes/Explore.hbscene.json':scene},null,2));
console.log('Explicit art camera scope: packed art plus named unlabelled model, plaza bucket and scene far plane. Production world files unchanged.');
