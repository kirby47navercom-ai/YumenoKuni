// Targeted real native views/input for reviewed facility geometry; own QA only.
import fs from'node:fs/promises';import path from'node:path';import assert from'node:assert/strict';import{createHash}from'node:crypto';import{nativeWindowProbe}from'./native-window-probe.mjs';
const r=path.resolve(import.meta.dirname,'../..'),w=path.join(r,'Game/Saved/park-architecture-v6'),output=path.join(w,'package'),manifest=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8')),prepared={output,manifest,executable:path.join(output,manifest.windowsApplication.executable)},qa=JSON.parse(await fs.readFile(path.join(w,'qa-package.json'),'utf8')),sha=b=>createHash('sha256').update(b).digest('hex'),source=path.join(r,'Game/Saved/native-outdoor-checkpoint-1793680307759/actual-native-savegames.json'),original=await fs.readFile(source);
const asset=process.argv.find(a=>a.startsWith('--asset='))?.slice(8)||'clinic';
const placements={
 fairytale_west_walk:[{id:'garden-west-covered-walk',world:'plaza',chapter:1,level:'ParkFairytale',pose:[-50,1.6,-15,-104,10],phase:0}],
 fairytale_east_walk:[{id:'garden-east-covered-walk',world:'plaza',chapter:1,level:'ParkFairytale',pose:[22,1.6,14,12.5,10],phase:0}],
 carnival_covered_walk:[{id:'festival-striped-covered-walk',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[-43,1.6,46,12.1,9],phase:0}],
 mirrors_covered_walk:[{id:'mirrors-faceted-covered-walk',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[-33,1.6,17,-26.6,11],phase:0}],
 clockwork_covered_walk:[{id:'clockwork-folded-covered-walk',world:'clockwork_midway',chapter:4,level:'ParkClockwork',pose:[-50,1.6,30,-45,10],phase:0}],
 starlight_covered_walk:[{id:'starlight-ribbon-covered-walk',world:'starlight_midway',chapter:5,level:'ParkStarlight',pose:[-24,1.6,38,-49.4,10],phase:0}],
 mirrors_arcade_panels:[{id:'mirrors-framed-panels-under-roof',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[-31,1.6,12,0,1],phase:0,probeArcadeEdge:true}],
 fairytale_prize_kiosk:[{id:'garden-prize-display',world:'plaza',chapter:1,level:'ParkFairytale',pose:[-11,1.6,29.2,78.69,2],phase:0}],
 fairytale_ring_kiosk:[{id:'garden-ring-lane',world:'plaza',chapter:1,level:'ParkFairytale',pose:[11,1.6,27.8,-101.31,2],phase:0}],
 carnival_can_kiosk:[{id:'festival-can-target-alley',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[-43,1.6,28.2,81.47,2],phase:0}],
 carnival_prize_kiosk:[{id:'festival-west-prize-display',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[-45,1.6,19.2,78.69,2],phase:0}],
 carnival_prize_kiosk_east:[{id:'festival-east-prize-display',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[-36,1.6,41.2,78.69,2],phase:0}],
 carnival_ring_kiosk:[{id:'festival-west-ring-lane',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[-45,1.6,36,90,2],phase:0}],
 carnival_ring_kiosk_east:[{id:'festival-east-ring-lane',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[-14.8,1.6,49,11.31,2],phase:0}],
 mirrors_mask_kiosk:[{id:'mirrors-west-mask-display',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[-32,1.6,36.2,78.69,2],phase:0}],
 mirrors_mask_kiosk_east:[{id:'mirrors-east-mask-display',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[-22,1.6,37.8,-101.31,2],phase:0}],
 clockwork_demo_kiosk:[{id:'clockwork-west-geared-demo',world:'clockwork_midway',chapter:4,level:'ParkClockwork',pose:[-35,1.6,38.2,78.69,2],phase:0}],
 clockwork_demo_kiosk_east:[{id:'clockwork-east-geared-demo',world:'clockwork_midway',chapter:4,level:'ParkClockwork',pose:[-23,1.6,38.8,-101.31,2],phase:0}],
 starlight_orbit_kiosk:[{id:'starlight-west-planet-display',world:'starlight_midway',chapter:5,level:'ParkStarlight',pose:[-30,1.6,37.8,101.31,2],phase:0}],
 starlight_orbit_kiosk_east:[{id:'starlight-east-planet-display',world:'starlight_midway',chapter:5,level:'ParkStarlight',pose:[-19,1.6,47.4,-68.2,2],phase:0}],
 public_gear_tower_view:[{id:'public-gear-tower-front',world:'clockwork_midway',chapter:4,level:'ParkClockwork',pose:[-32,1.6,16,35,26],phase:0}],
 garden_ring_clear_view:[{id:'garden-ring-lane-clear',world:'plaza',chapter:1,level:'ParkFairytale',pose:[13,1.6,29,-90,4],phase:0}],
 carnival_walk_clear_view:[{id:'festival-striped-walk-clear',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[-46,1.6,43,0,10],phase:0}],
 public_ride_review:[
  {id:'public-carousel',world:'plaza',chapter:1,level:'ParkFairytale',pose:[-33,1.6,39,0,8],phase:0},
  {id:'public-teacups',world:'plaza',chapter:1,level:'ParkFairytale',pose:[40,1.6,42,28.1,2],phase:0},
  {id:'public-big-top',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[-29,1.6,37,0,11],phase:0},
  {id:'public-swing',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[39,1.6,52,19.4,8],phase:0},
  {id:'public-coaster-station',world:'clockwork_midway',chapter:4,level:'ParkClockwork',pose:[-5,1.6,34,-31.4,7],phase:0},
  {id:'public-gear-tower',world:'clockwork_midway',chapter:4,level:'ParkClockwork',pose:[-45,1.6,23,-19.4,16],phase:0},
  {id:'public-orbit-ride',world:'starlight_midway',chapter:5,level:'ParkStarlight',pose:[35,1.6,51,0,4],phase:0},
  {id:'public-space-theatre',world:'starlight_midway',chapter:5,level:'ParkStarlight',pose:[-26,1.6,25,21.8,8],phase:0},
  {id:'public-wheel',world:'starlight_midway',chapter:5,level:'ParkStarlight',pose:[9,1.6,2,15.6,16],phase:0},
 ],
 fairytale_castle_gateway:[{id:'fairytale-castle-approach',world:'plaza',chapter:1,level:'ParkFairytale',pose:[4,1.6,18,169.7,10]}],
 perimeter_service_gateway:[{id:'perimeter-gateway-and-continuing-road',world:'outside_threshold',chapter:6,level:'ParkPerimeter',pose:[0,1.6,6,0,6]},{id:'perimeter-looking-along-outbound-road',world:'outside_threshold',chapter:6,level:'ParkPerimeter',pose:[0,1.6,-6.6,0,0]}],
 mirror_continuing_road:[{id:'mirrors-walk-the-continuing-road',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[-28,1.6,44.5,172,0],walkPastGate:true}],
 carnival_return_threshold:[{id:'carnival-canvas-connection',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[-27,1.6,34.5,167,12]},{id:'carnival-canvas-return',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[-30,1.6,46.5,180,-21.8],returnToGarden:true}],
 mirrors_return_threshold:[{id:'mirrors-reflector-connection',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[-31,1.6,32.5,-167,12]},{id:'mirrors-reflector-return',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[-28,1.6,44.5,180,-21.8],returnToGarden:true}],
 starlight_return_threshold:[{id:'starlight-orbit-connection',world:'starlight_midway',chapter:5,level:'ParkStarlight',pose:[-27,1.6,32.5,-167,12]},{id:'starlight-orbit-return',world:'starlight_midway',chapter:5,level:'ParkStarlight',pose:[-24,1.6,44.5,180,-21.8],returnToGarden:true}],
 mirror_observatory_support:[{id:'observatory-clear-stair',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[30.6,1.6,-3.5,90,14],walkToDeck:true}],
 mirror_maze:[{id:'mirror-maze-facade-quarter',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[0,1.6,33,24.8,10]},{id:'mirror-maze-existing-entry',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[-6,1.6,21.5,0,-15.95],arrive:'mirror_maze'}],
 mirror_waiting:[{id:'mirror-waiting-pavilion-quarter',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[9,1.6,9,-32,8]},{id:'mirror-waiting-existing-entry',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[14,1.6,3.5,0,-15.95],arrive:'mirror_waiting'}],
 clockwork_return_threshold:[{id:'clockwork-signal-bridge',world:'clockwork_midway',chapter:4,level:'ParkClockwork',pose:[-27,1.6,35,165.4,12]},{id:'clockwork-signal-bridge-return',world:'clockwork_midway',chapter:4,level:'ParkClockwork',pose:[-30,1.6,45.5,180,-21.8],returnToGarden:true}],
 archive_room:[{id:'archive-front-quarter',world:'clockwork_midway',chapter:4,level:'ParkClockwork',pose:[-50,1.6,-29,-43,7]}],
 exhibition_room:[{id:'exhibition-front-quarter',world:'clockwork_midway',chapter:4,level:'ParkClockwork',pose:[-22,1.6,13,-37.6,6]}],
 inspection_hall_normal:[{id:'inspection-front-quarter',world:'clockwork_midway',chapter:4,level:'ParkClockwork',pose:[19,1.6,-8,52.4,7]}],
 loading_gate:[{id:'loading-front-quarter',world:'clockwork_midway',chapter:4,level:'ParkClockwork',pose:[20,1.6,-55,36.4,5]},{id:'loading-along-service-approach',world:'clockwork_midway',chapter:4,level:'ParkClockwork',pose:[6,1.6,-61,0,5]}],
 maintenance_workshop:[{id:'workshop-front-quarter',world:'clockwork_midway',chapter:4,level:'ParkClockwork',pose:[19,1.6,15,40.9,7]}],
 reading_room:[{id:'reading-loggia',world:'clockwork_midway',chapter:4,level:'ParkClockwork',pose:[-36,1.6,-12,0,6]}],
 central_control:[{id:'central-control-quarter',world:'starlight_midway',chapter:5,level:'ParkStarlight',pose:[22,1.6,31,37.9,8]},{id:'central-control-front',world:'starlight_midway',chapter:5,level:'ParkStarlight',pose:[8,1.6,27,0,10]}],
 service_lodge:[{id:'service-lodge-road-quarter',world:'outside_threshold',chapter:6,level:'ParkPerimeter',pose:[3,1.6,0,53,5]},{id:'service-lodge-observation-bow',world:'outside_threshold',chapter:6,level:'ParkPerimeter',pose:[1,1.6,-3,61.5,3]}],
 screening_room:[{id:'screening-rear-quarter-wide',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[-18,1.6,-78,146.3,6]},{id:'screening-hall-side',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[-49,1.6,-51,-78.7,8]},{id:'screening-projection-end',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[-23,1.6,-66,137.5,10]}],record_room:[{id:'record-vault-front-wide',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[36,1.6,-4,0,6]},{id:'record-vault-reading-window',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[31.57,1.6,-17.8,0,0]}],dream_lobby:[{id:'dream-lobby-front',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[-34,1.6,-26,0,8]},{id:'dream-lobby-quarter',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[-24,1.6,-26,54.2,8]}],mirror_workbay:[{id:'mirror-workbay-rear-quarter',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[-9,1.6,-12,-136.7,8]},{id:'mirror-workbay-quarter',world:'mirror_midway',chapter:3,level:'ParkMirrors',pose:[8,1.6,-10,127,8]}],refreshment_store:[{id:'refreshment-front',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[-12,1.6,-12,0,8]},{id:'refreshment-counter',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[-14.85,1.6,-15.4,0,0]}],theatre_preparation:[{id:'theatre-preparation-paired-door',room:'performance_stage',chapter:2,pose:[0,1.6,6.12,0,-1.52],arrive:'theatre_preparation'},{id:'theatre-preparation-left-quarter',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[-10,1.6,-5,-135,12]},{id:'theatre-preparation-quarter',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[10,1.6,-2,125,12]}],performance_stage:[{id:'stage-front',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[0,1.6,44,0,9]},{id:'stage-proscenium',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[0,1.6,29.5,0,5]}],cold_store:[{id:'cold-store-front',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[0,1.6,-13,0,12]},{id:'cold-store-fan-quarter',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[6,1.6,-17,56.3,5]},{id:'cold-store-readable-quarter',world:'carnival_midway',chapter:2,level:'ParkCarnival',pose:[10,1.6,-9,39.8,8]}],supply_store:[{id:'supply-front',pose:[-24,1.6,-42,0,9]},{id:'supply-quarter',pose:[-17,1.6,-42,49.4,9]}],service_lounge:[{id:'lounge-quarter',pose:[29,1.6,-25.4,44.1,8]}],hotel_multiuse:[{id:'hall-front',pose:[-38,1.6,-42,0,15]},{id:'hall-readable-quarter',pose:[-30.2,1.6,-41.8,51.5,12]}],management_office:[{id:'management-front',pose:[20,1.6,-15,0,8]},{id:'management-quarter',pose:[27,1.6,-15,37.9,8]}],ticket_booth:[{id:'ticket-front',pose:[-10,1.6,42,0,8]},{id:'ticket-quarter',pose:[-4,1.6,42,36.9,8]},{id:'ticket-readable-quarter',pose:[-16,1.6,40,-45,9]},{id:'ticket-window-close',pose:[-10,1.6,39.1,0,8]},{id:'ticket-counter-readable',pose:[-11.6,1.6,39,-17.7,3]}],clinic:[{id:'clinic-front',pose:[-38,1.6,-30.4,0,5]},{id:'clinic-quarter',pose:[-31,1.6,-31,57.8,8]},{id:'clinic-authored-hotel-door',room:'hotel_lobby',pose:[-5.8,1.55,0,90,-19.65],enter:true}],dining_room:[{id:'dining-front',pose:[-38,1.6,-12,0,-7]},{id:'dining-front-wide',pose:[-38,1.6,-10,0,8]}],kitchen:[{id:'kitchen-front',pose:[-24,1.6,-12,0,-7]},{id:'kitchen-quarter',pose:[-17,1.6,-12,30.3,8]}],electrical_room:[{id:'electrical-front',pose:[34,1.6,-15.5,0,-8]},{id:'electrical-quarter',pose:[40,1.6,-15.5,35.2,8]}],laundry_room:[{id:'laundry-front',pose:[-24,1.6,-30.4,0,-5]},{id:'laundry-quarter',pose:[-17,1.6,-30.4,51.3,-4]},{id:'laundry-workroom-window',pose:[-26.48,1.6,-30.4,0,-18]}]};assert(placements[asset],'Add the next authored placement explicitly');
const only=process.argv.find(a=>a.startsWith('--cases='))?.slice(8).split(',');const cases=placements[asset].filter(c=>!only||only.includes(c.id));assert(cases.length,'No requested known cases');const sceneNames=[...new Set(cases.map(c=>'Content/Assets/Scenes/'+(c.level|| (c.room?'Explore':'ParkFairytale'))+'.hbscene.json'))],sceneSHA256=sha(Buffer.from(JSON.stringify(await Promise.all(sceneNames.map(async name=>[name,sha(await fs.readFile(path.join(output,name)))])))));const checkpoint=path.join(w,asset+'-native-progress.json'),prior=await fs.readFile(checkpoint,'utf8').then(JSON.parse,e=>{if(e.code!=='ENOENT')throw e;return null;}),rows=prior?.geometryManifestSHA256===qa.geometryManifestSHA256&&prior?.gameModuleSHA256===qa.nativeSHA256&&prior?.sceneSHA256===sceneSHA256?prior.rows:[];let p;
try{for(const c of cases){if(rows.some(a=>a.id===c.id))continue;const run=path.join(w,c.id+'-'+Date.now()),save=JSON.parse(original),key=Object.keys(save.items).find(k=>k.startsWith('hbengine.savegame.json.yumeno-progress-v4.project.')),s=JSON.parse(save.items[key]),chapter=String(c.chapter||1),graph=JSON.parse(await fs.readFile(path.join(r,'data/v4_story/chapters/'+chapter+'.json'),'utf8')),hub=Object.values(graph.nodes).find(n=>n.type==='investigate'&&(!c.arrive||n.spots?.some(a=>a.space_id===c.arrive&&!a.requiresFlags&&!a.requiresCards))&&(chapter!=='1'||n.spots?.some(a=>a.space_id==='clinic'&&!a.requiresFlags&&!a.requiresCards)));assert(hub,'Use an existing eligible investigation hub for explicit exterior-view fixtures');s.chapter=chapter;s.node=hub.id;s.flags={};s.stack=[];s.court.active=false;for(const k of['taskResume','pendingTaskResume'])delete s[k];s.worldId=c.world||c.room||'plaza';s.world[s.worldId]=c.pose;if(c.phase!==undefined)s.playerProgress.skyPhase=c.phase;save.items[key]=JSON.stringify(s);save.fixture=true;await fs.mkdir(run);const resume=path.join(run,'fixture.json');await fs.writeFile(resume,JSON.stringify(save));
 p=await nativeWindowProbe({source:output,prepared,work:run,resume,sparse:true,unprofiled:true,maxFrames:null});await p.hiddenBorderless();await p.resize(2560,1440);await p.tap('c');await p.sampled(400);await p.capture('before');let ui=JSON.parse(await fs.readFile(path.join(run,'before.ui.json'),'utf8'));assert.equal(ui.scene,c.level?'Assets/Scenes/'+c.level+'.hbscene.json':c.room?'Assets/Scenes/Explore.hbscene.json':'Assets/Scenes/ParkFairytale.hbscene.json');assert(ui.world.some(o=>o.id===(c.room?'ExploreGeometry':'ParkGeometry')&&o.meshVisible));const camera=ui.world.find(o=>o.id==='Camera');assert(camera.position.every((v,k)=>Math.abs(v-[300+c.pose[0],c.pose[1],c.pose[2]][k])<.12),'Saved camera must actually restore outside existing collisions');
 if(c.phase!==undefined){
   const phase=['day','night','evening'][c.phase];
   assert(ui.world.some(o=>o.id==='OutdoorSkyDome'&&o.mesh?.endsWith('/sky_'+phase+'.glb')),'The authored sky phase must actually render in the requested view');
 }
 if(c.enter){await p.move(manifest.width/2,manifest.height/2);await p.tap('e');await p.sampled(350);await p.capture('entered');ui=JSON.parse(await fs.readFile(path.join(run,'entered.ui.json'),'utf8'));assert(ui.world.some(o=>o.id==='ExploreGeometry'&&o.mesh?.endsWith('/clinic.glb')),'Actual E must reach the authored clinic interior');assert(!ui.world.some(o=>o.id==='ParkGeometry'),'Outdoor geometry must unload on clinic entry');}
 if(c.arrive){await p.move(manifest.width/2,manifest.height/2);await p.tap('e');await p.sampled(350);await p.capture('entered');ui=JSON.parse(await fs.readFile(path.join(run,'entered.ui.json'),'utf8'));assert(ui.world.some(o=>o.id==='ExploreGeometry'&&o.mesh?.endsWith('/'+c.arrive+'.glb')),'Actual E must preserve the existing paired room door');assert(!ui.world.some(o=>o.id==='ParkGeometry'));}
 if(c.returnToGarden){
   const districtMesh=ui.world.find(o=>o.id==='ParkGeometry'&&o.meshVisible).mesh;
   await p.move(manifest.width/2,manifest.height/2);await p.tap('e');await p.sampled(450);await p.capture('entered');
   ui=JSON.parse(await fs.readFile(path.join(run,'entered.ui.json'),'utf8'));
   assert.equal(ui.scene,'Assets/Scenes/ParkFairytale.hbscene.json');
   assert(ui.world.some(o=>o.id==='ParkGeometry'&&o.mesh?.endsWith('/fairytale.glb')&&o.meshVisible));
   assert(!ui.world.some(o=>o.mesh===districtMesh),'Previous district mesh must unload on exit');
 }
 if(c.walkToDeck){
   await p.key('w',true);
   try{await p.sampled(600);}finally{await p.key('w',false);}
   await p.capture('upper-deck');
   const deck=JSON.parse(await fs.readFile(path.join(run,'upper-deck.ui.json'),'utf8'));
   const [x,y,z]=deck.world.find(o=>o.id==='Camera').position;
   assert.equal(deck.scene,ui.scene);
   assert(x>307&&x<320.4&&Math.abs(y-7.45)<.12&&Math.abs(z+3.5)<.12,'Actual walk must cross the former middle column and reach the upper deck');
 }
 if(c.walkPastGate){
   await p.key('w',true);
   try{await p.sampled(520);}finally{await p.key('w',false);}
   await p.capture('beyond-gate');
   const far=JSON.parse(await fs.readFile(path.join(run,'beyond-gate.ui.json'),'utf8'));
   assert.equal(far.scene,ui.scene);
   assert(far.world.find(o=>o.id==='Camera').position[2]>52.4,'The existing hedge wall must no longer block the continuing road');
 }
 if(c.probeArcadeEdge){
   await p.key('a',true);
   try{await p.sampled(220);}finally{await p.key('a',false);}
   await p.capture('arcade-edge');
   const edge=JSON.parse(await fs.readFile(path.join(run,'arcade-edge.ui.json'),'utf8'));
   const x=edge.world.find(o=>o.id==='Camera').position[0];
   assert(x>265.7&&x<268.9,'Actual side movement must approach the mirror panel and stop within the retained arcade collision');
 }
 await p.close();p=null;rows.push({id:c.id,run,enteredClinic:!!c.enter,arrived:c.arrive||null,...(c.returnToGarden?{returnedToGarden:true}:{}),...(c.walkToDeck?{walkedToDeck:true}:{}),...(c.walkPastGate?{walkedPastGate:true}:{}),...(c.probeArcadeEdge?{arcadeCollision:true}:{}),fixture:true});await fs.writeFile(checkpoint,JSON.stringify({rows,sceneSHA256,geometryManifestSHA256:qa.geometryManifestSHA256,gameModuleSHA256:qa.nativeSHA256},null,2));console.log(JSON.stringify(rows.at(-1)));}
 assert((await fs.readFile(source)).equals(original));await fs.writeFile(path.join(w,asset+'-native.json'),JSON.stringify({ok:true,asset,rows,sceneSHA256,gameModuleSHA256:qa.nativeSHA256,geometryManifestSHA256:qa.geometryManifestSHA256,noStats:true,noProfile:true,sourceSaveUnchanged:true,scope:rows.some(row=>row.returnedToGarden)?'Native exterior fixture and actual E return to ParkFairytale with the source district unloaded.':asset==='clinic'?'Native exterior views and existing authored hotel_lobby__clinic E entrance.':'Native fixture views scoped to the recorded cases.'},null,2));
}finally{await p?.close().catch(()=>{});}
