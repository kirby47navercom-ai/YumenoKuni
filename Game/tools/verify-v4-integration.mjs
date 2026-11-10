import {padSystemAction} from './v4-pad-test-input.mjs';
// Own-game native/UI integration, isolated player profile; never runs V3.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const {executable}=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/v4-integration-'+Date.now());await fs.mkdir(work,{recursive:true});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const keys={Enter:[13,'Enter'],Escape:[27,'Escape'],Backspace:[8,'Backspace'],Tab:[9,'Tab'],Control:[17,'ControlLeft'],w:[87,'KeyW'],s:[83,'KeyS'],a:[65,'KeyA'],d:[68,'KeyD'],l:[76,'KeyL'],c:[67,'KeyC'],m:[77,'KeyM'],o:[79,'KeyO']};
process.env.HB_PLAYER_SOAK_HOURS='1';let probe;const checks=[];const padOnly=process.argv.includes('--pad-only');
try{
 probe=await editorWindowProbe({work,mode:'player',executable});
 await probe.until(()=>probe.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);await delay(700);
 const call=(name,args={})=>probe.evaluate(`window.hbPlayerDebug.call("Driver",${JSON.stringify('Yumeno.'+name)},${JSON.stringify(args)})`);
 const stats=async()=>JSON.parse((await call('Stats')).outputs.result);
 const key=async(k,type)=>{const [windowsVirtualKeyCode,code]=keys[k];await probe.cdp('Input.dispatchKeyEvent',{type,key:k,code,windowsVirtualKeyCode});};
 const sampled=async()=>{const frame=await probe.evaluate('window.hbPlayerDebug.lifecycle().frame');await delay(90);await probe.until(async()=>(await probe.evaluate('window.hbPlayerDebug.lifecycle().frame'))>=frame+2,'input edge sampled',10000);};
 const tap=async k=>{await key(k,'keyDown');await sampled();await key(k,'keyUp');await sampled();};
 const imageErrors=()=>probe.evaluate(`Array.from(document.images).filter(i=>i.offsetWidth>0&&i.src&&i.complete&&i.naturalWidth===0).map(i=>i.src)`);
 const padAction=id=>padSystemAction(stats,tap,id);
 assert.equal((await stats()).mode,'title');await probe.capture('01-title-supplied-ui.png');
 await tap('o');assert.equal((await stats()).options.open,true);await probe.capture('02-options.png');
 const before=(await stats()).options.values.music;await tap('d');assert.notEqual((await stats()).options.values.music,before);await tap('a');
 await call('DebugFastRead'); // QA pacing is not a source option row.
 await tap('Backspace');assert.equal((await stats()).mode,'title');checks.push('title options consume input and update real settings');
 await call('DebugV4Chapter',{index:0});await delay(700);
 let s=await stats();assert.equal(s.contentVersion,'v4');assert.equal(s.world.active,true);assert.equal(s.audioV4.ready,true);assert.equal(s.error,undefined);
 await probe.capture('03-v4-native-dialogue.png');
 await tap('l');await probe.capture('04-backlog.png');assert.equal((await stats()).node,s.node);await tap('Backspace');checks.push('backlog preserves authored node');
 await tap('Tab');
 const menus=['map','bullet','gift','card','rules','option'];
 for(let i=0;i<menus.length;i++){
  const layout=await probe.evaluate(`(()=>{const names=['PdFloor','PdThemeHome','PdHead','PdFace','PdTitle','PdBig','PdBubble','PdDesc',...Array.from({length:6},(_,i)=>'PdIcon'+i)];return Object.fromEntries(names.map(n=>{const e=document.querySelector('[data-widget-name="'+n+'"]'),r=e?.getBoundingClientRect(),im=e?.tagName==='IMG'?e:e?.querySelector('img');return [n,{visible:!!e&&r.width>0&&getComputedStyle(e).visibility!=='hidden',x:r?.x,y:r?.y,w:r?.width,h:r?.height,asset:im?.dataset.asset,src:im?.src}];}));})()`);
  await fs.writeFile(path.join(work,'pad-home-'+menus[i]+'.json'),JSON.stringify(layout,null,2));
  assert.equal(layout.PdFloor.asset,'Assets/Art/ui/v3/themes/type_000.svg');assert.equal(layout.PdThemeHome.asset,'Assets/Art/ui/v3/pad_home/'+menus[i]+'_overlay.svg','separate supplied menu header over selected source background');for(const id of ['PdHead','PdTitle','PdBig'])assert(!layout[id].visible,'invented header element remains '+id);
  assert(Math.abs(layout.PdBubble.x-380)<2&&Math.abs(layout.PdBubble.y-153.33)<2&&Math.abs(layout.PdBubble.w-468.67)<2,'supplied SFL shape bounds and description transform');assert(layout.PdFace.visible);
  for(let j=0;j<6;j++){const b=layout['PdIcon'+j];assert(Math.abs(b.w-132)<2&&Math.abs(b.h-136)<2,'common SFL button retains its size');assert(Math.abs(b.y-(i===j?383.3333:436.6667))<2,'selection lifts the button without enlarging it');}
  await probe.capture('pad-home-'+menus[i]+'.png');await fs.writeFile(path.join(work,'pad-home-'+menus[i]+'.json'),JSON.stringify(layout,null,2));
  if(i<5)await tap('d');
 }
 checks.push('six supplied Korean pad menu backgrounds/titles and SFL description positions, without invented header/card tile');
 if(!padOnly){await tap('Enter');
 await padAction('save');const savedNode=(await stats()).node;await padAction('title');await padAction('title_yes');assert.equal((await stats()).mode,'title');
 await tap('c');s=await stats();assert.equal(s.contentVersion,'v4');assert.equal(s.node,savedNode);assert.equal(s.error,undefined);checks.push('V4 save restores stable node in separate content slot');
 await key('Control','keyDown');let menus=0,documents=0,lastType='',chapter1=false;
 for(let tick=0;tick<2500;tick++){
  s=await stats();if(s.error)throw new Error(s.error);
  if(s.chapter===1){chapter1=true;break;}
  if(s.v4Kind==='menu'){
   await key('Control','keyUp');menus++;await probe.capture('choice-'+menus+'.png');await tap('Enter');await key('Control','keyDown');
  }else if(s.v4Kind==='document'){
   if(lastType!=='document'){documents++;await probe.capture('document-'+documents+'.png');}
   await key('Control','keyUp');await tap('Enter');await key('Control','keyDown');
  }
  lastType=s.v4Kind;await delay(45);
 }
 await key('Control','keyUp');assert.equal(chapter1,true);assert.equal(menus,2);assert.equal(documents,2);checks.push('native prologue executes exclusive choices and two actual notebook pages into next chapter');
 await probe.capture('06-next-chapter.png');}
 const missing=await imageErrors();assert.deepEqual(missing,[]);
 const report={ok:true,checks,work,executable,chapter:s.chapter,node:s.node,errors:probe.errors,scope:padOnly?'Native title/options/log and six supplied Korean pad home menus. Subpages, material blending, full campaign and user visual approval remain separate.':'Native prologue path + UI/audio request/settings/save integration. Full campaign, every choice, listening and authored scene choreography are not accepted here.'};
 assert.equal(probe.errors.length,0);await fs.writeFile(path.join(work,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}catch(error){await fs.writeFile(path.join(work,'failure.json'),JSON.stringify({ok:false,checks,error:error.stack},null,2));try{await probe?.capture('failure.png');}catch{}throw error;}
finally{await probe?.stop?.();}
