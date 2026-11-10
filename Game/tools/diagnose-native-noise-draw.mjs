// A/B/A diagnostic only: hide noise draws, never its model or gameplay.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createOwnedNativePackage} from './native-owned-package.mjs';
import {nativeWindowProbe} from './native-window-probe.mjs';
const root=path.resolve(import.meta.dirname,'..'),base=path.join(root,'Saved/game-trial-work-20261102');
const build=JSON.parse(await fs.readFile(path.join(base,'current-flat-build-result.json'),'utf8'));
const module=path.join(base,'game-noise-draw-diagnostic.exe'),receipt=JSON.parse(await fs.readFile(path.join(base,'game-module-noise-draw-diagnostic.json'),'utf8'));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
assert(receipt.diagnosticOnly&&receipt.productSourceUnchanged&&!receipt.engineModified);
assert.equal(receipt.baseBuild,build.id);assert.equal(hash(await fs.readFile(module)),receipt.binarySHA256);
const work=path.join(root,'Saved/native-trial-cost-'+Date.now());await fs.mkdir(work);
const source=path.join(root,'Saved/ui-checkpoints/normal-ch3-latest/savegames.json'),sourceBytes=await fs.readFile(source);
const prepared=await createOwnedNativePackage({source:build.output,work,gameModuleCandidate:module});
const save=JSON.parse(sourceBytes),key=Object.keys(save.items).find(k=>k.startsWith('hbengine.savegame.json.YumenoKuni-options-v4.project.'));
assert(key);save.items[key]=JSON.stringify({...JSON.parse(save.items[key]),frameRate:120});
const resume=path.join(work,'resume.json');await fs.writeFile(resume,JSON.stringify(save));
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms)),phases=[],glyphs=new Map();let p;
const glyph=async asset=>{if(!glyphs.has(asset))glyphs.set(asset,JSON.parse(await fs.readFile(path.join(prepared.output,'Content',asset),'utf8')).glyph);return glyphs.get(asset);};
const inspect=async name=>{
 await p.capture(name);const ui=JSON.parse(await fs.readFile(path.join(work,name+'.ui.json'),'utf8'));
 assert.equal(ui.scene,'Assets/Scenes/DebateHud.hbscene.json');assert.equal(ui.hostFrameRate,120);
 assert.equal(ui.width,2560);assert.equal(ui.height,1440);
 assert.equal(ui.world.filter(o=>/^Podium\d+$/.test(o.id)).length,16);
 const shown=ui.world.filter(o=>o.sprite?.visible&&o.sprite.enabled!==false);
 const noise=shown.filter(o=>/^TrialGpu_N[FB]\d+$/.test(o.id)).length;
 const main=shown.filter(o=>/^TrialGpu_M|^TrialBatch_M/.test(o.id)).length;
 let timer='';for(const o of shown.filter(o=>/^TrialGpu_Timer\d+$/.test(o.id)).sort((a,b)=>a.id.localeCompare(b.id)))timer+=await glyph(o.sprite.sprite);
 return {name,noise,main,timer,width:ui.width,height:ui.height};
};
const seconds=text=>{const parts=/^(\d+):(\d+):(\d+)$/.exec(text);assert(parts,'Real countdown must render');return +parts[1]*60+(+parts[2])+(+parts[3])/1000;};
try{
 p=await nativeWindowProbe({source:build.output,work,prepared,resume,sparse:true,unprofiled:true,maxFrames:null});
 await p.hiddenBorderless();await p.resize(2560,1440);await p.tap('c');await delay(22000);
 for(const [name,hidden,toggle]of [['normal',false,false],['noise-draws-hidden',true,true],['normal-restored',false,true]]){
  if(toggle)await p.tap('F1');let before;
  for(let i=0;i<12;i++){before=await inspect(name+'-before-'+i);if(before.main&&before.timer.length===9&&(hidden?before.noise===0:before.noise>0))break;await p.sampled(30);}
  assert(before.main&&before.timer.length===9);assert(hidden?before.noise===0:before.noise>0,'Diagnostic switch must affect only actual noise rendering');
  const at=Date.now(),first=await p.until(async()=>{const row=await p.frameSample();return row.time>at?row:false;},'fresh diagnostic heartbeat',5000,25);
  for(let i=0;i<30;i++){await delay(1000);const window=await p.windowState();assert.deepEqual(window,[false,false,false],'Keep diagnostic hidden, unminimized and unfocused');}
  const last=await p.frameSample(),after=await inspect(name+'-after');const duration=(last.time-first.time)/1000;
  assert(duration>=28);assert(after.main&&after.timer.length===9);
  if(hidden)assert.equal(after.noise,0);const timerDelta=seconds(before.timer)-seconds(after.timer);assert(timerDelta>25&&timerDelta<36,'Model countdown must continue');
  phases.push({name,diagnosticOnly:true,noiseHidden:hidden,first,last,seconds:duration,fps:(last.sequence-first.sequence)/duration,before,after,timerDelta});
 }
 const runtime=await p.close();p=null;assert.equal(hash(await fs.readFile(source)),hash(sourceBytes));
 const proof=JSON.parse(await fs.readFile(path.join(work,'owned-package.json'),'utf8'));assert.deepEqual(proof.alterations.map(a=>a.name),[prepared.manifest.nativeModules[0].binary]);
 const report={ok:true,diagnosticOnly:true,shippingAcceptance:false,build:build.id,moduleSHA256:receipt.binarySHA256,work,sourceSHA256:hash(sourceBytes),phases,runtime,scope:'Actual hidden1440p native A/B/A, same process and120setting,30seconds each. Only the diagnostic game module toggles N renderer visibility via physical F1 input. Original model, inputs, timer, main text, 16 independent podiums, engine, base package, source and save remain unchanged. Hidden-display FPS is causal isolation, never an accepted optimization or shipping performance.'};
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({ok:true,work,diagnosticOnly:true,phases:phases.map(r=>({name:r.name,fps:r.fps}))}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:error.stack,phases},null,2));throw error;}finally{await p?.close().catch(()=>{});}
