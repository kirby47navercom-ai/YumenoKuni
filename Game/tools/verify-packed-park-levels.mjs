// Verify the actual compressed full package without loose content/Stats overrides.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),architecture=process.argv.includes('--architecture-v6'),work=path.join(root,architecture?'Saved/park-architecture-v6':'Saved/park-levels-20261104');
const materialCurrent=process.argv.includes('--material-current'),materialWork=path.join(root,'Saved/park-materials-20261104');
const packed=architecture?JSON.parse(await fs.readFile(path.join(work,'packed-build.json'),'utf8')):null;
const build=packed?.build??JSON.parse(await fs.readFile(path.join(materialCurrent?root:work,'build-result.json'),'utf8'));
const independent=materialCurrent?JSON.parse(await fs.readFile(path.join(materialWork,'independent-current.json'),'utf8')):null;
if(materialCurrent)assert(independent.allSixMaterialsExact&&independent.build===build.id,'Current material archive identity must be checked before runtime');
const manifest=JSON.parse(await fs.readFile(path.join(build.output,'game.hbpack.json'),'utf8'));
assert(manifest.contentArchive);const rows=[];let p;
const sha=b=>createHash('sha256').update(b).digest('hex');
const performance=JSON.parse(await fs.readFile(path.join(work,'native-performance.json'),'utf8'));
if(architecture)assert(packed.receipt.ok&&performance.rows.length===6);
else assert(performance.ok);
const expectedModule=packed?.receipt.gameModuleSHA256??JSON.parse(await fs.readFile(path.join(work,'game-module.json'),'utf8')).binarySHA256;
assert.equal(performance.gameModuleSHA256,expectedModule);
if(architecture)assert.equal(performance.geometryManifestSHA256,packed.receipt.geometryManifestSHA256);
const cases=[
 {id:'normal-ch3',resume:path.join(root,'Saved/ui-checkpoints/normal-ch3-latest/savegames.json'),scene:'Assets/Scenes/DebateHud.hbscene.json',fixture:false},
 {id:'carnival',resume:path.join(performance.rows.find(r=>r.id==='carnival-ultrawide').run,'fixture.json'),scene:'Assets/Scenes/ParkCarnival.hbscene.json',fixture:true},
 {id:architecture?'mirrors':'hotel',resume:path.join(performance.rows.find(r=>r.id===(architecture?'mirrors-4k':'fairytale-hotel-quarter')).run,'fixture.json'),scene:architecture?'Assets/Scenes/ParkMirrors.hbscene.json':'Assets/Scenes/ParkFairytale.hbscene.json',fixture:true},
];
try{for(const c of cases){
 const original=await fs.readFile(c.resume),run=path.join(work,'packed-'+c.id+'-'+Date.now());
 p=await nativeWindowProbe({source:build.output,work:run,resume:c.resume,sparse:true,maxFrames:null});
 await p.hiddenBorderless();await p.resize(3440,1440);await p.sampled(120);await p.capture('title');
 let ui=JSON.parse(await fs.readFile(path.join(run,'title.ui.json'),'utf8'));
 assert(!ui.world.some(o=>o.mesh?.includes('/park_levels/')||o.id==='CourtGeometry'));
 await p.tap('c');
 await p.until(async()=>{await p.capture('restored');ui=JSON.parse(await fs.readFile(path.join(run,'restored.ui.json'),'utf8'));return ui.scene===c.scene?ui:false;},'Packed continue '+c.id,60000,250);
 assert.equal(ui.width,3440);assert.equal(ui.height,1440);
 if(c.id==='carnival')assert.equal(ui.world.find(o=>o.id==='ExploreGeometry')?.meshVisible,false,'The final archive must contain the no-fallback-cube game fix');
 if(c.id==='normal-ch3'){assert.equal(ui.world.filter(o=>/^Podium\d+$/.test(o.id)&&o.mesh).length,16);assert(!ui.world.some(o=>o.id==='ParkGeometry'));}
 else{const district=c.id==='hotel'?'fairytale':c.id;assert.equal(ui.world.find(o=>o.id==='ParkGeometry')?.mesh,'Assets/Art/park_levels/'+district+'.glb');assert.equal(ui.world.filter(o=>o.meshVisible&&o.mesh?.includes('/park_levels/')&&!o.mesh.endsWith('/gate.glb')).length,1);await p.key('ArrowRight',true);await p.sampled(60);await p.key('ArrowRight',false);await p.capture('camera-moved');const moved=JSON.parse(await fs.readFile(path.join(run,'camera-moved.ui.json'),'utf8'));assert.notDeepEqual(moved.world.find(o=>o.id==='Camera').rotation,ui.world.find(o=>o.id==='Camera').rotation);}
 await p.tap('Tab');await p.sampled(30);await p.capture('pad');
 assert(JSON.parse(await fs.readFile(path.join(run,'pad.ui.json'),'utf8')).rects.some(r=>r.id==='PdFloor'));
 await p.tap('Tab');await p.sampled(30);await p.capture('pad-closed');
 ui=JSON.parse(await fs.readFile(path.join(run,'pad-closed.ui.json'),'utf8'));assert.equal(ui.scene,c.scene);assert(!ui.rects.some(r=>r.id==='PdFloor'));
 const runtime=await p.close();p=null;assert((await fs.readFile(c.resume)).equals(original));
 rows.push({id:c.id,run,scene:c.scene,fixture:c.fixture,width:ui.width,height:ui.height,audioErrors:runtime.audio.errors,sourceSaveSHA256:sha(original)});
 }
 const moduleSHA256=materialCurrent?independent.binarySHA256:expectedModule;assert.equal(sha(await fs.readFile(path.join(build.output,manifest.nativeModules[0].binary))),moduleSHA256);
 await fs.writeFile(path.join(materialCurrent?materialWork:work,materialCurrent?'current-packed-smoke.json':'final-packed-smoke.json'),JSON.stringify({ok:true,build:build.id,gameModuleSHA256:moduleSHA256,rows,compressedPackage:true,noContentOrModuleOverrides:true,noStats:true,sourceSavesUnchanged:true,existingIndependentBuild:materialCurrent,scope:'Actual full package: title unload, unchanged normal chapter3 restore, park fixture restore/camera, pad open/close, empty local renderer hidden, audio error report. Not a whole-campaign playthrough. Fixture locations from prior performance evidence do not prove the new module performance.'},null,2));
 console.log(JSON.stringify({ok:true,build:build.id,checks:rows.length}));
}finally{await p?.close().catch(()=>{});}
