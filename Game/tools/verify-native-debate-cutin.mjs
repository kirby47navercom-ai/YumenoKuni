import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {nativeWindowProbe} from './native-window-probe.mjs';
import {trialAimPlan} from './v4-aim-test-input.mjs';
import {makeNode,connect} from '../../../engineCreate/prototype/blueprint-model.js';
const root=path.resolve(import.meta.dirname,'..'),repo=path.dirname(root),output=path.join(root,'Saved/native-panic-views-1793690486425/package'),work=path.join(root,'Saved/native-debate-cutin-'+Date.now());await fs.mkdir(work,{recursive:true});
const manifest=JSON.parse(await fs.readFile(path.join(output,'game.hbpack.json'),'utf8'));
async function put(relative,bytes,kind){const file=path.resolve(output,relative);assert(file.startsWith(output+path.sep));await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file+'.cutin.tmp',bytes);await fs.rename(file+'.cutin.tmp',file);const r=manifest.files.find(r=>r.path===relative)||{path:relative};if(!manifest.files.includes(r))manifest.files.push(r);Object.assign(r,{bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});const asset=relative.slice(8);if(kind&&!manifest.entries.some(e=>e.path===asset))manifest.entries.push({path:asset,name:path.basename(asset),kind});}
const fx=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/debate_fx.json'),'utf8'));
const widget=JSON.parse(await fs.readFile(path.join(root,'Assets/UI/DebateFX.hbwidget.json'),'utf8'));
const sceneFiles=['Court','DebateHud','PanicHud'].map(n=>'Assets/Scenes/'+n+'.hbscene.json');
const textures=[...Object.keys(fx.textures),...fx.planes.map(p=>p.texture),...widget.nodes.map(n=>n.properties?.texture)].filter(p=>typeof p==='string'&&p.startsWith('Assets/'));
for(const name of sceneFiles){const scene=JSON.parse(await fs.readFile(path.join(root,name),'utf8'));for(const actor of scene.objects)for(const c of actor.components||[])if(c.type==='PostProcessVolume'&&c.properties.colorLookup)textures.push(c.properties.colorLookup);}
const files=[...new Set(['Assets/UI/DebateFX.hbwidget.json','Assets/Data/debate_fx.json',...textures,...sceneFiles])];
const candidate=process.argv.find(a=>a.startsWith('--game-module='))?.slice(14);
if(candidate){const file=path.resolve(root,candidate);assert(file.startsWith(path.join(root,'Saved')+path.sep));await put(manifest.nativeModules[0].binary,await fs.readFile(file));}
for(const f of files)await put('Content/'+f,await fs.readFile(path.join(root,f)),f.endsWith('.hbscene.json')?'scene':f.endsWith('.hbwidget.json')?'widget':f.endsWith('.json')?'data':'texture');
const bpName='Content/Assets/Blueprints/BP_Yumeno.hbblueprint.json',bp=JSON.parse(await fs.readFile(path.join(output,bpName),'utf8'));
if(!bp.nodes.some(n=>n.nativeId==='Yumeno.AimStats')){const stats=bp.nodes.find(n=>n.nativeId==='Yumeno.Stats'),print=bp.nodes.find(n=>bp.edges.some(e=>e.from?.node===stats?.id&&e.to?.node===n.id));assert(print,'Existing diagnostic Stats print');const aim=makeNode('nativeCall',700,700),write=makeNode('print',1000,700);aim.nativeId='Yumeno.AimStats';bp.nodes.push(aim,write);for(const [from,to] of [[{node:print.id,pin:'then'},{node:write.id,pin:'exec'}],[{node:aim.id,pin:'result'},{node:write.id,pin:'message'}]]){const r=connect(bp,from,to);assert(r.ok,r.reason);}await put(bpName,Buffer.from(JSON.stringify(bp)));}
await fs.writeFile(path.join(output,'game.hbpack.json'),JSON.stringify(manifest));
const checkpoints=JSON.parse(await fs.readFile(path.join(root,'Saved/native-task-checkpoints.json'),'utf8')),report={work,shipping:false,engineModified:false,cases:[]};let p;
process.env.YUMENO_NATIVE_QA_SVG_ERRORS='1';
try{for(const kind of ['lie','nonstop']){
 const c=checkpoints[kind],dir=path.join(work,kind),row={kind,task:c.task};report.cases.push(row);
 p=await nativeWindowProbe({source:output,prepared:{output,manifest,executable:path.join(output,manifest.windowsApplication.executable)},work:dir,resume:path.resolve(repo,c.file),maxFrames:null,heartbeatTimeoutMs:120000});await p.hiddenBorderless();await p.resize(1920,1080);await p.tap('c');
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.taskId===c.task;},'exact saved '+kind,120000);
 for(let i=0;i<80&&(await p.stats()).taskQueue;i++)await p.tap('Enter');
 await p.until(async()=>{const s=await p.stats();assert(!s.error,s.error);return s.taskInputArmed&&!s.taskQueue&&!s.scenes.loading&&!s.presentation?.nonstopIntro;},'active debate',120000);
 const began=Date.now();let held=false,charged=false;
 while(Date.now()-began<150000){const s=await p.stats();assert(!s.error,s.error);const t=s.trial||s.lieV4;if(s.taskId!==c.task||s.taskQueue){row.return=s;break;}if(t?.resultTime>0){row.result=t.result;row.resultTime=t.resultTime;if(t.resultTime<4.15&&t.resultTime>2.65){await p.capture('cutin');row.cutin=JSON.parse(await fs.readFile(path.join(dir,'cutin.ui.json'),'utf8'));break;}await p.sampled(1);continue;}
  if(kind==='lie'){if(!held){await p.key('Space',true);held=true;}if(!s.lieV4?.transformed){await p.sampled(2);continue;}if(!charged){charged=true;await p.capture('charged-world');assert.equal(s.presentation.worldNegative,1,'Actual world grade switches on for the transformed bullet');row.charged=true;}const a=s.auto;if(a.kind==='hold-target'){await p.click(a.x,a.y);await p.key('Space',false);held=false;}else await p.sampled(2);continue;}
  if(!t||t.turning||!t.weakPoint||!['weak','agree'].includes(t.kind)||!t.shotRecovery?.ready){await p.key('Shift',false);await p.sampled(2);continue;}await p.key('Shift',true);
  if(t.bullet!==t.answer){await p.tap('e');continue;}
  if(kind==='lie'&&!held){await p.key('Space',true);held=true;continue;}
  if(kind==='lie'&&!t.lie){await p.sampled(2);continue;}
  if(kind==='lie'&&!charged){charged=true;await p.capture('charged-world');row.charged=JSON.parse(await fs.readFile(path.join(dir,'charged-world.ui.json'),'utf8'));continue;}
  const plan=trialAimPlan(t.weakPoint,await p.aim());if(plan.kind==='key'){await p.tap(plan.key,2);continue;}
  await p.move(...plan.point);await p.button(...plan.point,true);await p.sampled(3);await p.button(...plan.point,false);if(held){await p.key('Space',false);held=false;}
 }
 assert(row.cutin,'Actual hit must reach the complete cutin phase');const nodes=row.cutin.widgets.find(w=>w.instance==='debatefx').nodes,hero=nodes.find(n=>n.id==='ResultHero'),partner=nodes.find(n=>n.id==='ResultPartner');assert(hero.properties.visible,'Cutin is native foreground UI');assert(!partner.properties.visible,'No arbitrary central negative portrait');assert(!row.cutin.world.some(n=>n.id.startsWith('ResultFx_')),'No duplicate graded world cutin sprites');assert(row.cutin.world.some(n=>n.id==='LieWorldGrade'),'Scoped world grade exists');row.hero={texture:hero.properties.texture,rect:hero.slot.offset};assert(kind!=='lie'||hero.properties.texture===Object.keys(fx.textures).find(p=>p.startsWith('Assets/Art/ui/hero_lie_deduction.')));assert(kind!=='nonstop'||hero.slot.offset[2]>=1300,'Refutation intentionally crops to a face closeup');delete row.cutin;delete row.charged;
 await p.key('Space',false);await p.key('Shift',false);await p.until(async()=>{const s=await p.stats();return (s.trial?.resultTime||s.lieV4?.resultTime||0)<=0&&s.presentation?.worldNegative!==1;},'cutin restores world',20000);await p.capture('restored');row.restored=true;row.runtime=await p.close();p=null;
 }report.ok=true;}catch(e){report.error=e.stack;report.last=await p?.stats().catch(()=>null);await p?.capture('failure').catch(()=>{});process.exitCode=1;}finally{await p?.close().catch(()=>{});await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({work,ok:report.ok,error:report.error?.split('\n')[0]}));}
