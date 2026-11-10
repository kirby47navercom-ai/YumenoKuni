// Regression repro: a script-advance click must not charge/fire on panic entry.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';import {editorWindowProbe} from '../../../engineCreate/tools/editor-window-probe.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url))),build=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/panic-held-'+Date.now());await fs.mkdir(work,{recursive:true});
const wait=ms=>new Promise(r=>setTimeout(r,ms));let p;process.env.HB_PLAYER_SOAK_HOURS='1';
try{
 p=await editorWindowProbe({work,mode:'player',executable:build.executable});await p.until(()=>p.evaluate('window.hbPlayerDebug?.ready?.()'),'ready',60000);
 for(const type of ['keyDown','keyUp']){await p.cdp('Input.dispatchKeyEvent',{type,key:'y',code:'KeyY',windowsVirtualKeyCode:89});await wait(70);}
 await p.cdp('Input.dispatchKeyEvent',{type:'keyDown',key:'Shift',code:'ShiftLeft',windowsVirtualKeyCode:16});
 await p.cdp('Input.dispatchMouseEvent',{type:'mousePressed',x:640,y:360,button:'left',clickCount:1});
 await p.evaluate("window.hbPlayerDebug.call('Driver','Yumeno.DebugJump',{index:5})");await wait(650);
 const held=await p.evaluate("window.hbPlayerDebug.call('Driver','Yumeno.Stats',{}).then(r=>JSON.parse(r.outputs.result))");
 await p.cdp('Input.dispatchMouseEvent',{type:'mouseReleased',x:640,y:360,button:'left',clickCount:1});
 await p.cdp('Input.dispatchKeyEvent',{type:'keyUp',key:'Shift',code:'ShiftLeft',windowsVirtualKeyCode:16});await wait(100);
 const released=await p.evaluate("window.hbPlayerDebug.call('Driver','Yumeno.Stats',{}).then(r=>JSON.parse(r.outputs.result))");
 const gated=!held.presentation.inputArmed&&!held.trial.lie&&held.trial.shots===0&&released.presentation.inputArmed&&released.trial.shots===0;
 await fs.writeFile(path.join(work,'report.json'),JSON.stringify({executable:build.executable,gated,held,released},null,2));
 if(process.argv.includes('--expect-gated'))assert(gated,'held entry must wait for release without charging/firing');
 console.log(JSON.stringify({work,gated,held:{armed:held.presentation.inputArmed,lie:held.trial.lie,shots:held.trial.shots},releasedShots:released.trial.shots}));
}finally{await p?.stop?.();}
