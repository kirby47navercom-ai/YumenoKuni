// Own-game runtime proof: camera motion, input/time gate, interruption and replay.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const built=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const stages=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/trials/11c.json'),'utf8')).stages;
const scene=JSON.parse(await fs.readFile(path.join(root,'Assets/Scenes/Main.hbscene.json'),'utf8'));
assert(scene.objects.find(o=>o.id==='CourtGeometry').components.some(c=>c.type==='MeshRenderer'));
for(let i=0;i<16;i++){
 const p=scene.objects.find(o=>o.id==='Podium'+i),s=scene.objects.find(o=>o.id==='Seat'+i);
 assert(p.components.some(c=>c.type==='MeshRenderer'));assert(!p.components.some(c=>c.type==='SpriteRenderer'));
 const sprite=s.components.find(c=>c.type==='SpriteRenderer');assert(sprite);assert.equal(sprite.properties.billboard,false);
 const rear=scene.objects.find(o=>o.id==='SeatRear'+i);assert(rear);assert(rear.components.find(c=>c.type==='SpriteRenderer').properties.texture.endsWith('_back.webp'));
}
const nonstop=stages.findIndex(s=>s.kind==='nonstop');
const choice=stages.findIndex(s=>s.kind==='choice');
const panic=stages.findIndex(s=>s.kind==='panic');
const scrum=stages.findIndex(s=>s.kind==='scrum');
const courtData=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/court.json'),'utf8')),figures=courtData.figures;
const dead=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/story.json'),'utf8')).dead['11c'];
assert(nonstop>=0&&choice>=0);
const work=path.join(root,'Saved/nonstop-intro-'+Date.now());await fs.mkdir(work,{recursive:true});
const wait=ms=>new Promise(r=>setTimeout(r,ms));
process.env.HB_PLAYER_SOAK_HOURS='1';
let probe;const checks=[],samples=[],uiSamples=[];
try{
 probe=await editorWindowProbe({work,mode:'player',executable:built.executable});
 await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'player ready',60000);await wait(500);
 const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call("Driver",${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
 const stats=async()=>{const s=JSON.parse((await call('Stats')).outputs.result);if(s.presentation)Object.assign(s.presentation,JSON.parse((await call('CourtStats')).outputs.result));return s;};
 const key=(key,code,vk,type)=>probe.cdp('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode:vk});
 const tap=async(k,c,v)=>{await key(k,c,v,'keyDown');await wait(90);await key(k,c,v,'keyUp');await wait(90);};
 const mouse=type=>probe.cdp('Input.dispatchMouseEvent',{type,x:640,y:360,button:'left',clickCount:1});
 const visible=name=>probe.evaluate(`(()=>{const e=document.querySelector('[data-widget-name="${name}"]');return !!e&&e.getBoundingClientRect().width>0&&getComputedStyle(e).visibility!=='hidden';})()`);
 await tap('t','KeyT',84);assert.equal((await stats()).mode,'trial');
 await call('DebugJump',{index:nonstop});
 await key('Shift','ShiftLeft',16,'keyDown');await mouse('mousePressed');
 const initial=await stats();assert.equal(initial.presentation.nonstopIntro,true);
 const baseline={timer:initial.presentation.timer,focus:initial.trial.focus,hearts:initial.trial.hearts};
 const introDuration=initial.presentation.duration;
 let frame=0;const captures=[.2,1.5,2.65,3.8,5.05,6.1,7.2,8.45,9.2];
 const deadline=Date.now()+introDuration*1000+7000;
 while(Date.now()<deadline){
  const s=await stats();assert(!s.error,s.error);const p=s.presentation;
  if(!p.nonstopIntro)break;
  assert.equal(s.auto.kind,'wait');assert.equal(p.timer,baseline.timer);assert.equal(p.statementTime,0);
  assert.equal(s.trial.focus,baseline.focus);assert.equal(s.trial.hearts,baseline.hearts);assert.equal(s.trial.broken,0);
  assert.equal(await visible('Trial'),false);assert.equal(await visible('Portrait'),false);
  assert.equal(await visible('FHudImg'),false);assert.equal(await visible('FHudSub'),false);
  assert.equal(await visible('Cylinder'),false,'regular ammunition HUD waits for the cinematic handoff');
  if(p.introPhase==='sweep'){assert.equal(p.loaded,0);assert.equal(await visible('IntroGun'),false);}
  if(p.introPhase==='focus'||p.elapsed>p.loadStart+.7)assert.equal(await visible('IntroGun'),true);
  if(p.introPhase==='focus')assert.equal(p.loaded,p.ammoCount,'all actual stage bullets load before first-speaker travel');
  const ui=await probe.evaluate(`(()=>{const names=[...Array.from({length:5},(_,i)=>'IntroGlyph'+i),...Array.from({length:5},(_,i)=>'IntroGlow'+i),'IntroStart','IntroStartEcho','IntroHoop','IntroHoop2','IntroAmmoList',...Array.from({length:32},(_,i)=>'IntroInBullet'+i),...Array.from({length:9},(_,i)=>'IntroAmmoPlate'+i),...Array.from({length:9},(_,i)=>'IntroAmmoText'+i)];return Object.fromEntries(names.map(name=>{const e=document.querySelector('[data-widget-name="'+name+'"]'),r=e?.getBoundingClientRect();return [name,{visible:!!e&&r.width>0&&getComputedStyle(e).visibility!=='hidden',width:r?.width??0,height:r?.height??0,x:r?.x??0,y:r?.y??0,parent:e?.parentElement?.dataset.widgetName??'',left:e?.offsetLeft??0,top:e?.offsetTop??0,text:e?.textContent??''}];}));})()`);
  uiSamples.push({elapsed:p.elapsed,ui});
  for(const a of p.cast){
   assert(Math.abs(a.rotation[1]-(a.seat*22.5+180))<.001,'characters face their own podium, never track the camera');
   const front=scene.objects.find(o=>o.id==='Seat'+a.seat).components.find(c=>c.type==='SpriteRenderer').properties.texture;
   const slug=front.match(/court_figures\/([^/.]+)/)[1];
   assert(a.rear,'permanent rear plane exists');
   const normal=a.rotation[1]*Math.PI/180;
   assert(Math.abs(a.rear[0]-a.position[0]+.004*Math.sin(normal))<.0002&&Math.abs(a.rear[2]-a.position[2]+.004*Math.cos(normal))<.0002,'rear stays4mm behind fixed front plane');
   if(!dead.includes(slug)){
    assert(a.blackRear,'actual rear texture is the black alpha-matched image');
    const angle=a.rotation[1]*Math.PI/180,dot=(p.camera[0]-a.position[0])*Math.sin(angle)+(p.camera[2]-a.position[2])*Math.cos(angle);
    if(Math.abs(dot)>.001)assert.equal(a.texture.endsWith('_back.webp'),dot<0,'rear of standing character is black silhouette');
    assert(Math.abs(a.position[1]-figures[slug].height/2-.1)<.001,'full-body feet remain on the floor');
   }else{
    assert(a.blackRear,'memorial rear is a black alpha-matched plane');
    assert([courtData.memorials[slug].texture,courtData.memorials[slug].back].map(p=>path.basename(p)).includes(a.texture),'each deceased seat uses that character portrait, not the old empty frame');
    assert(Math.abs(a.position[1]-1.85)<.001,'memorial portrait is above the desk rim');
   }
  }
  assert.equal(p.desks.length,16);
  for(let i=0;i<16;i++)for(let j=i+1;j<16;j++){
   const a=p.desks[i].position,b=p.desks[j].position;
   assert(Math.hypot(a[0]-b[0],a[2]-b[2])-1.36>.17,'curved desks retain physical clearance even during opposed radial movement');
  }

  for(const desk of p.desks){
   const person=p.cast.find(a=>a.seat===desk.seat),next=p.desks.find(d=>d.seat===(desk.seat%2?desk.seat-1:desk.seat+1));
   const offset=Math.hypot(desk.position[0],desk.position[2])-3.95;
   assert(Math.abs(Math.hypot(person.position[0],person.position[2])-4.08-offset)<.001,'person and own podium share the same world displacement');
   assert(Math.abs(offset+Math.hypot(next.position[0],next.position[2])-3.95)<.001,'odd/even podiums move in opposite radial directions');
   assert(Math.abs(desk.rotation[1]-person.rotation[1])<.001,'podium and standing plane retain matching facing');
   assert(Math.hypot(person.position[0]-desk.position[0],person.position[2]-desk.position[2])<.14,'all16 body/foot anchors lie inside the .42m-radius station interior, not behind its outer edge');
  }
  samples.push({elapsed:p.elapsed,phase:p.introPhase,loaded:p.loaded,ammoCount:p.ammoCount,camera:p.camera,sceneRotation:p.sceneRotation,cast:p.cast,desks:p.desks,timer:p.timer,statementTime:p.statementTime});
  if(frame<captures.length&&p.elapsed>=captures[frame]){await probe.capture(`intro-${frame++}.png`);}
  await wait(85);
 }
 let s=await stats();assert.equal(s.presentation.nonstopIntro,false);assert(samples.length>=5);
 const podiumOffsets=samples.map(p=>Math.hypot(p.desks[0].position[0],p.desks[0].position[2])-3.95);
 assert(Math.max(...podiumOffsets)>.65&&Math.min(...podiumOffsets)<-.65,'actual 3D podiums translate outward and inward, independently of camera movement');
 for(const desk of s.presentation.desks)assert(Math.abs(Math.hypot(desk.position[0],desk.position[2])-3.95)<.001,'completion restores normal podium ring');
 checks.push('reference-adapted odd/even radial motion, fixed slot attachment, physical clearance and completion restoration');
 const phases=[...new Set(samples.map(p=>p.phase))];assert.deepEqual(phases,['sweep','load','focus']);
 const loading=samples.filter(p=>p.phase==='load'),focusing=samples.filter(p=>p.phase==='focus');
 assert(loading.length>=6&&focusing.length>=2);
 assert(Math.max(...loading.map(p=>p.loaded))===initial.presentation.ammoCount);
 assert(loading.some(p=>p.loaded>0&&p.loaded<initial.presentation.ammoCount),'real ammunition is loaded sequentially');
 for(let i=1;i<loading.length;i++){
  assert(loading[i].loaded>=loading[i-1].loaded);
  assert(Math.abs(loading[i].camera[1]-1.57)<.001,'charge camera scans the ring at eye level');
 }
 const chargeTravel=loading.slice(1).reduce((sum,p,i)=>sum+Math.abs((p.camera[3]-loading[i].camera[3]+540)%360-180),0);
 assert(chargeTravel>130&&chargeTravel<175,'camera continues scanning other desks while the large cylinder loads');
 const focusTurn=Math.abs((focusing.at(-1).camera[3]-loading.at(-1).camera[3]+540)%360-180);
 assert(focusTurn>45&&focusTurn<80,'dedicated first-speaker turn occurs after all bullets have loaded');
 checks.push('reference video order: court sweep -> large cylinder and sequential persistent names with eye-level charge scan -> cylinder retract/first-speaker turn -> statement/input');
 const motion=samples.filter(p=>p.elapsed>1.0&&p.phase==='sweep');let travel=0,peakYaw=0,peakSeat=0;
 for(let i=1;i<motion.length;i++){
  const a=motion[i-1],b=motion[i],dt=b.elapsed-a.elapsed;
  assert(dt>0);const yaw=Math.abs((b.camera[3]-a.camera[3]+540)%360-180);
  travel+=yaw;peakYaw=Math.max(peakYaw,yaw/dt);
  peakSeat=Math.max(peakSeat,Math.abs(Math.hypot(...[b.desks[0].position[0],b.desks[0].position[2]])-Math.hypot(...[a.desks[0].position[0],a.desks[0].position[2]]))/dt);
 }
 assert(travel<300&&travel>230,'substantial270degree court sweep before the first-speaker approach');
 assert(peakYaw<175,'sampled camera yaw has no former fast direction flip');
 assert(peakSeat<2.1,'larger1.4m row exchange retains bounded speed through reversals');
 checks.push('compact circular clearance, substantial orbit and bounded actual camera/podium speed');
 const firstGlyph=Array.from({length:5},(_,i)=>uiSamples.find(s=>s.ui['IntroGlyph'+i].visible)?.elapsed);
 assert(firstGlyph.every(Number.isFinite));
 assert(firstGlyph[4]<firstGlyph[3]&&firstGlyph[3]<firstGlyph[2]&&firstGlyph[2]<=firstGlyph[1]&&firstGlyph[1]<=firstGlyph[0],'reverse Korean letter entrance: 의 -> 논 -> 톱 -> 스 -> 논 (50ms pair gaps may share a sampled frame)');
 assert(uiSamples.some(s=>Array.from({length:5},(_,i)=>s.ui['IntroGlyph'+i].visible).every(Boolean)),'full Korean title settles before exit');
 const startSamples=uiSamples.filter(s=>s.ui.IntroStart.visible);assert(startSamples.length>=2);assert(startSamples.some(s=>s.ui.IntroHoop.visible&&s.ui.IntroHoop2.visible));
 for(const s of startSamples){for(const name of ['IntroStart','IntroStartEcho','IntroHoop','IntroHoop2']){const e=s.ui[name];if(!e.visible)continue;assert(Math.abs(e.x+e.width/2-640)<1&&Math.abs(e.y+e.height/2-360)<1,'START and both circular waves retain one screen centre at all scales');}}
 assert(uiSamples.find(s=>s.ui.IntroInBullet0.visible).elapsed>startSamples.at(-1).elapsed,'ordinary unnamed rounds follow START');
 assert(Math.max(...uiSamples.map(s=>Array.from({length:32},(_,i)=>s.ui['IntroInBullet'+i].visible).filter(Boolean).length))>=16,'dense multi-wave volley, not six isolated rounds');
 const plates=uiSamples.flatMap(s=>Array.from({length:9},(_,i)=>s.ui['IntroAmmoText'+i].visible?{length:[...s.ui['IntroAmmoText'+i].text].length,width:s.ui['IntroAmmoPlate'+i].width}:null).filter(Boolean));
 const byLength=new Map(plates.map(p=>[p.length,p.width]));assert(byLength.size>1);const lengths=[...byLength.keys()].sort((a,b)=>a-b);assert(byLength.get(lengths.at(-1))>byLength.get(lengths[0]),'longer actual names have longer cartridge bodies');
 checks.push('Korean reverse glyph entrance with blue afterimages, impact START/hoop, unnamed color rounds, then text-length cartridge loading');
 for(const sample of uiSamples){
  const present=Array.from({length:9},(_,i)=>({i,plate:sample.ui['IntroAmmoPlate'+i],label:sample.ui['IntroAmmoText'+i]})).filter(r=>r.plate.visible&&r.label.visible);
  for(const r of present){assert.equal(r.plate.parent,'IntroAmmoRow'+r.i);assert.equal(r.label.parent,r.plate.parent);assert.equal(r.label.left,34);assert.equal(r.label.top,7);}
  const scale=Math.hypot(sample.ui.IntroAmmoList.width,sample.ui.IntroAmmoList.height)>0?Math.min(1,420/(62*initial.presentation.ammoCount)):1;
  for(let k=1;k<present.length;k++){
   const a=present[k-1].plate,b=present[k].plate,nx=Math.sin(Math.PI/18),ny=Math.cos(Math.PI/18);
   const gap=((b.x+b.width/2)-(a.x+a.width/2))*nx+((b.y+b.height/2)-(a.y+a.height/2))*ny;
   assert(gap>58*scale&&gap<66*scale,'adjacent cartridge normal spacing stays62px before list scaling, independent of name lengths');
  }
 }
 checks.push('common cartridge/text transform origin and62px perpendicular row pitch; no overlapping name-length rows');


 const wide=samples.filter(p=>p.elapsed>=.95&&p.elapsed<3.5);
 assert(wide.length>=5);
 const radii=wide.map(p=>Math.hypot(p.camera[0],p.camera[2]));
 assert(radii.every(r=>r>=1.47&&r<=6.81)&&Math.max(...radii)-Math.min(...radii)>3,'positive-radius spiral moves from the upper near side into the ring without passing through the court centre');
 for(const p of wide){const [x,y,z,yaw,pitch]=p.camera,angle=yaw*Math.PI/180,dot=-x*Math.sin(angle)-z*Math.cos(angle),r=Math.hypot(x,z),distance=-dot+Math.sqrt(Math.max(0,dot*dot+4.08**2-r*r));assert(Math.abs(y+distance*Math.tan(pitch*Math.PI/180)-1.57)<.01,'view follows a point on the visible desk ring instead of swinging toward a fixed seat from the wrong side');}
 assert(wide[0].camera[1]-wide.at(-1).camera[1]>4,'crane descends to the charge scan before the first-speaker handoff');
 for(const p of wide){
  const [x,y,z]=p.sceneRotation.map(d=>d*Math.PI/180),sx=Math.sin(x),cx=Math.cos(x),sy=Math.sin(y),cy=Math.cos(y),sz=Math.sin(z),cz=Math.cos(z);
  const forward=[-sy,sx*cy,-cx*cy],yaw=p.camera[3]*Math.PI/180,pitch=p.camera[4]*Math.PI/180;
  const logical=[-Math.sin(yaw)*Math.cos(pitch),Math.sin(pitch),-Math.cos(yaw)*Math.cos(pitch)];
  assert(forward.reduce((sum,v,i)=>sum+v*logical[i],0)>.9999,'actual engine XYZ orientation matches logical track');
  assert(Math.abs(cx*sz+sx*sy*cz)<.001,'actual camera right vector stays level across all yaw angles');
 }
 assert(samples.every(p=>Math.abs(p.camera[5])<.01),'horizon remains level instead of rolling the screen');
 assert(Math.abs(s.presentation.camera[5])<.65,'normal dialogue drift resumes after the level-horizon intro');
 assert.equal(s.presentation.inputArmed,false);assert.equal(s.trial.hearts,baseline.hearts);assert.equal(s.trial.focus,baseline.focus);
 await wait(600);s=await stats();assert.equal(s.presentation.inputArmed,false);assert.equal(s.trial.hearts,baseline.hearts);
 assert(s.presentation.timer<baseline.timer);checks.push('variable-radius crane/orbit, level horizon and timer/statement/resource freeze during intro');
 checks.push('podium-facing full-body placement, feet on floor and black rear silhouettes throughout the camera track');
 checks.push('held mouse and Shift cannot charge, fire or consume focus at handoff');
 await mouse('mouseReleased');await key('Shift','ShiftLeft',16,'keyUp');await wait(250);
 s=await stats();assert.equal(s.presentation.inputArmed,true);assert.equal(s.trial.hearts,baseline.hearts);
 assert.equal(await visible('Trial'),true);assert.equal(await visible('Lens'),true);assert.equal(await visible('IntroTitle'),false);
 assert.equal(await visible('FHudImg'),false);
 await probe.capture('active.png');checks.push('release arms controls, restores HUD and starts normal statements');
 await call('DebugJump',{index:nonstop});await wait(1800);assert.equal((await stats()).presentation.nonstopIntro,true);
 await call('DebugJump',{index:choice});await wait(250);s=await stats();assert.equal(s.stage.kind,'choice');assert.equal(s.presentation.nonstopIntro,false);
 for(const name of ['IntroTop','IntroBottom','IntroFade','IntroStreaks','IntroStart','IntroStartEcho','IntroHoop','IntroHoop2','IntroAmmoList',...Array.from({length:9},(_,i)=>'IntroAmmoRow'+i),'IntroGun','IntroSelectedPlate','IntroSelectedText',...Array.from({length:5},(_,i)=>'IntroGlyph'+i),...Array.from({length:5},(_,i)=>'IntroGlow'+i),...Array.from({length:32},(_,i)=>'IntroInBullet'+i),...Array.from({length:9},(_,i)=>'IntroAmmoPlate'+i),...Array.from({length:9},(_,i)=>'IntroAmmoText'+i),...Array.from({length:5},(_,i)=>'IntroRound'+i)])assert.equal(await visible(name),false);
 for(const desk of s.presentation.desks)assert(Math.abs(Math.hypot(desk.position[0],desk.position[2])-3.95)<.001,'interrupt restores moved podiums immediately');
 checks.push('stage interruption clears cinematic layers and restores displaced desks');
 if(scrum>=0){
  await call('DebugJump',{index:scrum});await wait(900);
  await call('DebugJump',{index:nonstop});
  await probe.until(async()=>{
   try{
    await probe.evaluate('window.hbPlayerDebug.report()');
    const snapshot=JSON.parse(await fs.readFile(path.join(work,'UserData/runtime-report.json'),'utf8'));
    const objects=new Map(snapshot.objects.map(o=>[o.id,o]));
    return Array.from({length:16},(_,i)=>{
     const actor=objects.get('Seat'+i),podium=objects.get('Podium'+i),rear=objects.get('SeatRear'+i);
     const slug=scene.objects.find(o=>o.id==='Seat'+i).components.find(c=>c.type==='SpriteRenderer').properties.texture.match(/court_figures\/([^/.]+)/)[1];
     return actor&&podium&&rear&&Math.abs(rear.position[1]-actor.position[1])<.001&&Math.abs(Math.hypot(actor.position[0],actor.position[2])-4.08)<.001&&Math.abs(actor.position[1]-(dead.includes(slug)?1.85:figures[slug].center))<.001&&Math.abs(Math.hypot(podium.position[0],podium.position[2])-3.95)<.001&&Math.abs(podium.position[1]-.1)<.001&&Math.abs(actor.rotation[1]-(i*22.5+180))<.001;
    }).every(Boolean);
   }catch{return false;}
  },'3D podiums, upright actors and memorial heights restored after interrupted scrum',6000);
  checks.push('interrupted scrum restores all 3D podiums and 2D actor/memorial positions');
 }
 if(panic>=0){await call('DebugJump',{index:panic});await wait(200);s=await stats();assert.equal(s.presentation.nonstopIntro,false);assert.equal(s.stage.kind,'panic');checks.push('existing panic entrance retained');}
 await call('DebugJump',{index:nonstop});s=await stats();assert.equal(s.presentation.nonstopIntro,true);assert.equal(s.presentation.statementTime,0);
 // Measure an uninterrupted warm entry separately: no screenshots, Stats or CourtStats polling.
 await probe.evaluate('window.hbPlayerDebug.resetProfile()');
 await wait(introDuration*1000+200);
 const uninterruptedProfile=await probe.evaluate('window.hbPlayerDebug.profile()');
 await call('DebugJump',{index:nonstop});
 const preview=[];const replayDeadline=Date.now()+12000;
 while(Date.now()<replayDeadline){
  s=await stats();if(!s.presentation.nonstopIntro)break;
  if(s.presentation.elapsed<.04){await wait(40);continue;}
  const name=`preview-${String(preview.length).padStart(3,'0')}.jpg`;
  const capture=await probe.cdp('Page.captureScreenshot',{format:'jpeg',quality:85});
  await fs.writeFile(path.join(work,name),Buffer.from(capture.data,'base64'));
  preview.push({file:name,elapsed:s.presentation.elapsed});await wait(40);
 }
 assert.equal((await stats()).presentation.nonstopIntro,false);assert(preview.length>=12);
 assert(!(await stats()).error);assert.equal(probe.errors.length,0);checks.push('re-entering nonstop restarts and completes the cinematic');
 const seatInspections=[];
 for(let i=0;i<16;i++){
  await call('DebugCourtSeat',{index:i});await wait(140);
  const s=await stats();const a=s.presentation.cast[i],d=s.presentation.desks[i];
  assert(Math.abs(Math.hypot(a.position[0]-d.position[0],a.position[2]-d.position[2])-.13)<.001,'inspected body anchor is inside own station');
  const file=`seat-${String(i).padStart(2,'0')}.jpg`,capture=await probe.cdp('Page.captureScreenshot',{format:'jpeg',quality:88});
  await fs.writeFile(path.join(work,file),Buffer.from(capture.data,'base64'));seatInspections.push({seat:i,file,actor:a,desk:d});
 }
 checks.push('all16 individual front views captured with body/foot anchors inside own station');
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,executable:built.executable,checks,samples,uiSamples,preview,seatInspections,uninterruptedProfile,viewport:[1280,720],scope:'own HBEngine game, normal nonstop entry; no V3 runtime execution'},null,2));
 console.log(JSON.stringify({ok:true,checks,work}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:String(error),checks,samples,uiSamples},null,2));throw error;}
finally{await probe?.stop?.();}
