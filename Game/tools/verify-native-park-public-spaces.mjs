// New/changed public-space behavior only; do not replay already passed chapters.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import {createHash} from 'node:crypto';
import {makeNode,connect} from '../../../engineCreate/prototype/blueprint-model.js';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/park-levels-20261104'),output=path.join(work,'native-review/package');
const manifestFile=path.join(output,'game.hbpack.json'),originalManifest=await fs.readFile(manifestFile),manifest=JSON.parse(originalManifest),prepared={output,manifest,executable:path.join(output,manifest.windowsApplication.executable)};
const bpName='Content/Assets/Blueprints/BP_Yumeno.hbblueprint.json',bpFile=path.join(output,bpName),originalBP=await fs.readFile(bpFile),bp=JSON.parse(originalBP),update=bp.nodes.find(n=>n.nativeId==='Yumeno.Update');assert(!bp.nodes.some(n=>n.nativeId==='Yumeno.Stats'));
const read=makeNode('nativeCall',700,180),print=makeNode('print',1000,180);read.nativeId='Yumeno.Stats';bp.nodes.push(read,print);
for(const[from,to]of [[{node:update.id,pin:'then'},{node:print.id,pin:'exec'}],[{node:read.id,pin:'result'},{node:print.id,pin:'message'}]])assert(connect(bp,from,to).ok);
const put=async(file,bytes)=>{await fs.writeFile(file+'.finish.tmp',bytes);await fs.rename(file+'.finish.tmp',file);};
const bytes=Buffer.from(JSON.stringify(bp));await put(bpFile,bytes);Object.assign(manifest.files.find(r=>r.path===bpName),{bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});await fs.writeFile(manifestFile,JSON.stringify(manifest));
const source=path.join(root,'Saved/native-outdoor-checkpoint-1793680307759/actual-native-savegames.json'),original=await fs.readFile(source),rows=[];let p;
const cases=[{id:'covered-carnival',chapter:2,room:'carnival_midway',pose:[-29,1.6,28,0,0],key:'w',frames:300},{id:'mirror-arcade',chapter:3,room:'mirror_midway',pose:[-31,1.6,12,0,0],key:'a',frames:220},{id:'planetarium-entry',chapter:5,room:'starlight_midway',pose:[-34,1.6,20,0,0],key:'w',frames:180},{id:'funhouse-door',chapter:3,room:'mirror_midway',pose:[-6,1.6,21.5,0,-16],arrive:'mirror_maze'},{id:'hotel-door',chapter:1,room:'plaza',pose:[0,1.6,-14.7,0,-10.3],arrive:'hotel_lobby'}];
try{for(const c of cases){
 const run=path.join(work,'public-'+c.id+'-'+Date.now()),save=JSON.parse(original),key=Object.keys(save.items).find(k=>k.startsWith('hbengine.savegame.json.yumeno-progress-v4.project.')),s=JSON.parse(save.items[key]),graph=JSON.parse(await fs.readFile(path.join(root,'../data/v4_story/chapters/'+c.chapter+'.json'),'utf8'));
 const hub=Object.values(graph.nodes).find(n=>n.type==='investigate'&&(!c.arrive||n.spots?.some(s=>s.space_id===c.arrive&&!s.requiresFlags&&!s.requiresCards)));assert(hub,'An authored eligible investigation must actually expose this door');
 s.chapter=String(c.chapter);s.node=hub.id;s.flags={};s.stack=[];s.court.active=false;for(const k of ['taskResume','pendingTaskResume'])delete s[k];s.worldId=c.room;s.world[c.room]=c.pose;save.items[key]=JSON.stringify(s);save.fixture=true;await fs.mkdir(run);const resume=path.join(run,'fixture.json');await fs.writeFile(resume,JSON.stringify(save));
 p=await nativeWindowProbe({source:output,prepared,work:run,resume,maxFrames:null});await p.hiddenBorderless();await p.resize(3440,1440);await p.tap('c');await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.mode==='explore'&&s.world?.space===c.room&&!s.scenes.loading?s:false;},c.id,60000);
 // A one-shot entrance input must follow the native asset-loading overlay;
 // game scene ownership becomes ready before the first presented park frame.
 if(c.arrive)await p.sampled(400);
 await p.capture('before');const before=await p.stats();
 if(c.arrive){await p.move(860,360);await p.tap('e');await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.mode==='explore'&&s.world?.space===c.arrive&&!s.scenes.loading?s:false;},'Actual entrance '+c.arrive,30000);}
 else{await p.key(c.key,true);await p.sampled(c.frames);await p.key(c.key,false);}
 const after=await p.stats();await p.capture('after');
 const ui=JSON.parse(await fs.readFile(path.join(run,'after.ui.json'),'utf8'));assert.equal(ui.world.find(o=>o.id==='ExploreGeometry')?.meshVisible,!!c.arrive);
 assert.equal(after.world.space,c.arrive||c.room);assert(after.world.position.every(Number.isFinite));
 if(c.arrive){assert(!ui.world.some(o=>o.id==='ParkGeometry'));assert.equal(ui.scene,'Assets/Scenes/Explore.hbscene.json');}
 if(c.id==='covered-carnival')assert(after.world.position[2]<23,'The former solid full-canopy box must no longer fence off the public floor');
 if(c.id==='mirror-arcade')assert(after.world.position[0]>-34.3,'The actual arcade side panel must block side movement');
 if(c.id==='planetarium-entry')assert(after.world.position[2]>=15.25,'Closed architectural landmark entrance must remain solid');
 const runtime=await p.close();p=null;rows.push({id:c.id,run,before:before.world,after:after.world,chapter:c.chapter,audioErrors:runtime.audio.errors,fixture:true});
 }
 const bank=JSON.parse(await fs.readFile(path.join(root,'../art/space_v4/park_levels_v1/manifest.json'),'utf8'));
 assert((await fs.readFile(source)).equals(original));await fs.writeFile(path.join(work,'public-space-finish/native.json'),JSON.stringify({ok:true,rows,testedAssetSHA256:Object.fromEntries(rows.map(r=>[r.before.district,bank.assets.find(a=>a.id===r.before.district).sha256])),geometryManifestSHA256:createHash('sha256').update(await fs.readFile(path.join(root,'../art/space_v4/park_levels_v1/manifest.json'))).digest('hex'),moduleSHA256:JSON.parse(await fs.readFile(path.join(work,'game-module.json'),'utf8')).binarySHA256,sourceSaveUnchanged:true,scope:'Changed covered public floor, arcade panel collision and closed decorative landmark approach; explicit fixtures. Not a full chapter playthrough.'},null,2));console.log(JSON.stringify({ok:true,checks:rows.length}));
}catch(error){await fs.writeFile(path.join(work,'public-space-finish/native-failure.json'),JSON.stringify({error:error.stack,rows,last:await p?.stats().catch(()=>null)},null,2));await p?.capture('failure').catch(()=>{});throw error;}
finally{await p?.close().catch(()=>{});await put(bpFile,originalBP);await fs.writeFile(manifestFile,originalManifest);}
