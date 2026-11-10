// Own second-trial runtime: actual memorial selection and readable front portraits.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const built=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const court=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/court.json'),'utf8'));
const scene=JSON.parse(await fs.readFile(path.join(root,'Assets/Scenes/Main.hbscene.json'),'utf8'));
const dead=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/story.json'),'utf8')).dead['12c'];
assert(dead?.length>1);
const work=path.join(root,'Saved/court-memorials-'+Date.now());await fs.mkdir(work,{recursive:true});
const wait=ms=>new Promise(r=>setTimeout(r,ms));let probe;
process.env.HB_PLAYER_SOAK_HOURS='1';
try{
 probe=await editorWindowProbe({work,mode:'player',executable:built.executable});
 await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
 for(const type of ['keyDown','keyUp']){await probe.cdp('Input.dispatchKeyEvent',{type,key:'y',code:'KeyY',windowsVirtualKeyCode:89});await wait(100);}
 const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call('Driver',${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
 const state=JSON.parse((await call('Stats')).outputs.result);assert.equal(state.mode,'trial');
 const inspected=[];
 for(let i=0;i<16;i++){
  const slug=scene.objects.find(o=>o.id==='Seat'+i).components.find(c=>c.type==='SpriteRenderer').properties.texture.match(/court_figures\/([^/.]+)/)[1];
  await call('DebugCourtSeat',{index:i});await wait(140);
  const a=JSON.parse((await call('CourtStats')).outputs.result).cast[i];
  assert(a.blackRear);
  if(dead.includes(slug)){
   assert.equal(a.texture,path.basename(court.memorials[slug].texture));assert(Math.abs(a.position[1]-1.85)<.001);
   const file=`memorial-seat-${String(i).padStart(2,'0')}.png`;await probe.capture(file);
   inspected.push({seat:i,slug,texture:a.texture,file});
  }else assert(!a.texture.includes('back'),'front-facing living actors remain visible');
 }
 assert.equal(inspected.length,dead.length);assert(new Set(inspected.map(x=>x.texture)).size===dead.length);
 assert.equal(probe.errors.length,0);
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({ok:true,executable:built.executable,inspected,scope:'second trial in our game; every deceased seat uses its own portrait, other seats remain living actors'},null,2));
 console.log(JSON.stringify({ok:true,memorials:inspected.length,work}));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({error:String(error)}));throw error;}
finally{await probe?.stop?.();}
