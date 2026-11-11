import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
function applyTrialNameStyle(widget){
 const panel=widget.nodes.find(n=>n.id==='NamePanel'),speaker=widget.nodes.find(n=>n.id==='TrialSpeaker');assert(panel&&speaker);
 panel.properties.texture='Assets/Art/ui/hud_name_reference.svg';panel.slot.offset=[18,12,320,72];
 speaker.slot.offset=[42,30,270,34];Object.assign(speaker.properties,{font:'Assets/Fonts/pretendard/Pretendard-Medium.otf',fontSize:23,color:'#ffffff'});
 return widget;
}
export async function emitTrialNameOnly({repo,root,write}){
 await write('Assets/Art/ui/hud_name_reference.svg',await fs.readFile(path.join(repo,'ui/trial/hud_name_reference.svg')));
 const file='Assets/UI/Main.hbwidget.json';await write(file,applyTrialNameStyle(JSON.parse(await fs.readFile(path.join(root,file),'utf8'))));
 return {trialNameOnly:true,newIllustrations:0,reference:'Dk_JjYZEzdg 02:42; subdued horizontal name carrier',visualAcceptance:false};
}
export function applyTrialHudStyle(widget){
 const node=id=>{const n=widget.nodes.find(n=>n.id===id);assert(n,'Missing trial HUD '+id);return n;};
 for(const [id,name]of [['NamePanel','name'],['StatusPanel','status'],['TimerPanel','timer']])node(id).properties.texture=`Assets/Art/ui/hud_${name}.png`;
 node('NamePanel').slot.offset=[18,12,320,72];node('TrialSpeaker').slot.offset=[60,32,244,34];
 node('StatusPanel').slot.offset=[936,18,330,116];node('StatusLabel').slot.offset=[972,26,180,20];
 for(let i=0;i<10;i++)node('Star'+i).slot.offset=[972+i*22.5,94,21,21]; /* 판의 기운 오른쪽 끝 안으로(Claude 2026-11-05) */
 node('Timer').slot.offset=[1040,653,176,36];node('Timer').properties.fontSize=27;
 node('Cylinder').slot.offset=[12,554,140,140];node('BulletPlate').slot.offset=[122,626,420,50];
 Object.assign(node('StatusLabel').properties,{text:'STATUS',fontSize:14,color:'#ffffff'});
 Object.assign(node('BulletLabel').properties,{text:'코토다마',fontSize:18,color:'#e9ffff'});
 node('BulletLabel').slot.offset=[155,678,260,25];
 node('Bullet').properties.fontSize=27;node('Bullet').slot.offset=[156,631,370,40];
 return applyTrialNameStyle(widget);
}
export async function emitTrialHudStyleOnly({repo,root,write}){
 await write('Assets/Art/ui/hud_name_reference.svg',await fs.readFile(path.join(repo,'ui/trial/hud_name_reference.svg')));
 for(const name of ['name','status','timer'])await write(`Assets/Art/ui/hud_${name}.png`,await fs.readFile(path.join(repo,`ui/trial/hud_${name}.png`)));
 const main=JSON.parse(await fs.readFile(path.join(root,'Assets/UI/Main.hbwidget.json'),'utf8'));
 await write('Assets/UI/Main.hbwidget.json',applyTrialHudStyle(main));
 const intro=JSON.parse(await fs.readFile(path.join(root,'Assets/UI/Intro.hbwidget.json'),'utf8'));
 for(const id of ['IntroSelectedPlate','IntroSelectedText']){const n=intro.nodes.find(n=>n.id===id);assert(n);n.slot.offset[1]=id==='IntroSelectedPlate'?626:633;}
 await write('Assets/UI/Intro.hbwidget.json',intro);
 const vitals=JSON.parse(await fs.readFile(path.join(root,'Assets/UI/TrialVitalsV4.hbwidget.json'),'utf8'));
 for(const n of vitals.nodes.filter(n=>/^Heart\d+$/.test(n.id)))n.slot.offset[1]=56-Number(n.id.slice(5))*.84;
 await write('Assets/UI/TrialVitalsV4.hbwidget.json',vitals);
 const layout=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/gpu_trial_layout.json'),'utf8'));
 const timer=layout.nodes.find(n=>n.id==='TimerPanel');assert(timer);timer.texture='Assets/Art/ui/hud_timer.png';await write('Assets/Data/gpu_trial_layout.json',layout);
 return {trialHudOnly:true,storyDataChanged:false};
}

export async function emitTrialTimerOnly({root,write}){
 const file='Assets/UI/Main.hbwidget.json',widget=JSON.parse(await fs.readFile(path.join(root,file),'utf8'));
 const timer=widget.nodes.find(n=>n.id==='Timer');assert(timer);timer.slot.offset=[1040,653,176,36];timer.properties.fontSize=27;
 await write(file,widget);
 // The GPU uses existing 34px glyphs scaled to .8; the UI fallback uses 27px.
 const layoutFile='Assets/Data/gpu_trial_layout.json',layout=JSON.parse(await fs.readFile(path.join(root,layoutFile),'utf8'));
 const digits=layout.nodes.filter(n=>/^Timer[0-8]$/.test(n.id));assert.equal(digits.length,9);
 assert(layout.styles.some(s=>s.font===digits[0].font&&s.size===34&&s.w===80&&s.h===38));
 for(const digit of digits)digit.fontSize=34;
 await write(layoutFile,layout);return{trialTimerOnly:true,gpuGlyphSize:34,fallbackSize:27};
}
