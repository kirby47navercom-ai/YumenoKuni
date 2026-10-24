// 유메노쿠니 HBEngine 프로젝트 생성기 : 각본 데이터·스프라이트·UI·장면·블루프린트를 Assets/ 아래에 만든다.
// node tools/create-project.mjs   (엔진 원본은 ../../../engineCreate 를 읽기만 한다)
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {randomUUID} from 'node:crypto';
import {makeStarterScene} from '../../../engineCreate/prototype/scene-templates.js';
import {makeSceneComponent} from '../../../engineCreate/prototype/scene-components.js';
import {createAsset} from '../../../engineCreate/prototype/asset-documents.js';
import {makeNode,connect} from '../../../engineCreate/prototype/blueprint-model.js';
import {parseNativeHeader} from '../../../engineCreate/prototype/native-model.js';
import {createWidgetAsset,createWidgetNode} from '../../../engineCreate/prototype/ui-assets.js';

const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const repo=path.dirname(root);
const write=async(name,data)=>{const file=path.join(root,name);await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file,typeof data==='string'||Buffer.isBuffer(data)?data:JSON.stringify(data,null,1)+'\n');};
const copy=async(from,to)=>{await fs.mkdir(path.dirname(path.join(root,to)),{recursive:true});await fs.copyFile(path.join(repo,from),path.join(root,to));};

// 1) 각본 데이터 : data/scenes/{접두}_*.json → Assets/Data/scenes/{접두}.json
const sceneFiles=(await fs.readdir(path.join(repo,'data/scenes'))).filter(f=>f.endsWith('.json')).sort();
// source(원본 .md 이름)는 엔진 빌드가 파일 참조로 읽으므로 뺀다
for(const f of sceneFiles){const {source,...data}=JSON.parse(await fs.readFile(path.join(repo,'data/scenes',f),'utf8'));await write('Assets/Data/scenes/'+f.split('_')[0]+'.json',data);}
await write('Assets/Data/emotion.json',JSON.parse(await fs.readFile(path.join(repo,'data/emotion_map.json'),'utf8')));
// 진행 순서 : 프롤로그부터 (장이 늘면 여기 추가). 재판 : data/trials (tools/build_trial.py)
await write('Assets/Data/story.json',{files:['10'],trials:['11c'],dead:{'11c':['taiga']}});
for(const f of (await fs.readdir(path.join(repo,'data/trials'))).filter(f=>f.endsWith('.json')))await copy('data/trials/'+f,'Assets/Data/trials/'+f);

// 2) 교칙 : docs/spec/11 §2·§3 표
const rulesDoc=await fs.readFile(path.join(repo,'docs/spec/11_래피패드_교칙.md'),'utf8');
const rules=[...rulesDoc.matchAll(/^\| (교칙 \d+|[1-6]장) \| ([^|]+) \|/gm)].map(m=>({no:m[1],text:m[2].trim().replace(/\*\*/g,'')}));
await write('Assets/Data/rules.json',{rules});

// 3) 그림 : 스프라이트(WebP)·UI·글꼴 복사
for(const slug of await fs.readdir(path.join(repo,'art/sprites'))){
 for(const f of await fs.readdir(path.join(repo,'art/sprites',slug)))if(f.endsWith('.webp')&&!f.startsWith('sheet'))await copy(`art/sprites/${slug}/${f}`,`Assets/Art/sprites/${slug}/${f}`);
}
for(const f of ['dialog/frame.png','dialog/nameplate.png','trial/heart_full.png','trial/heart_empty.png','trial/cutin_objection.png','trial/focus_track.png','trial/focus_fill.png','trial/bullet_cylinder.png'])await copy('ui/'+f,'Assets/Art/ui/'+path.basename(f));
await write('Assets/Art/ui/aim.svg','<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><circle cx="32" cy="32" r="22" fill="none" stroke="#ff4fa3" stroke-width="4"/><circle cx="32" cy="32" r="3" fill="#ffffff"/><path d="M32 2v14M32 48v14M2 32h14M48 32h14" stroke="#ffffff" stroke-width="3"/></svg>');
await write('Assets/Art/ui/vpoint.svg','<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22"><circle cx="11" cy="11" r="9" fill="#ff2040" stroke="#ffffff" stroke-width="2"/></svg>');

const hudSvg={
 name:'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="80"><path d="M28 6H414L392 74H6Z" fill="#0b1018" fill-opacity=".82" stroke="#36e3ff" stroke-width="2"/><path d="M40 12H300" stroke="#36e3ff" stroke-opacity=".6"/>'+Array.from({length:9},(_,i)=>`<circle cx="${48+i*12}" cy="62" r="2.6" fill="#ffffff" fill-opacity="${.9-i*.08}"/>`).join('')+'</svg>',
 status:'<svg xmlns="http://www.w3.org/2000/svg" width="330" height="116"><path d="M40 4H326L292 112H6Z" fill="#0b1018" fill-opacity=".8" stroke="#36e3ff" stroke-width="2"/><path d="M52 30H306" stroke="#ffffff" stroke-opacity=".35"/></svg>',
 bullet:'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="50"><path d="M18 3H417L402 47H3Z" fill="#0b1018" fill-opacity=".85" stroke="#ffffff" stroke-width="2.5"/><path d="M3 47L18 3" stroke="#36e3ff" stroke-width="5"/></svg>',
 timer:'<svg xmlns="http://www.w3.org/2000/svg" width="330" height="64"><path d="M26 3H327L304 61H3Z" fill="#0b1018" fill-opacity=".85" stroke="#36e3ff" stroke-width="2"/><path d="M28 20v28M28 20h22l-6 7 6 7H28" fill="#ffffff" stroke="#ffffff" stroke-width="2" stroke-linejoin="round"/></svg>',
 heartOn:'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><path d="M16 29C4 20 1 13 4 8s10-5 12 1c2-6 9-6 12-1s0 12-12 21z" fill="#ff4fa3" stroke="#ffd1e8" stroke-width="2"/></svg>',
 heartOff:'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><path d="M16 29C4 20 1 13 4 8s10-5 12 1c2-6 9-6 12-1s0 12-12 21z" fill="#2a2030" stroke="#6b5470" stroke-width="2"/></svg>',
 starOn:'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><path d="M16 2l4.2 9.3 10.1 1-7.6 6.8 2.2 10L16 24l-8.9 5.1 2.2-10L1.7 12.3l10.1-1z" fill="#6dff8f" stroke="#e5ffe9" stroke-width="1.6"/></svg>',
 starOff:'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><path d="M16 2l4.2 9.3 10.1 1-7.6 6.8 2.2 10L16 24l-8.9 5.1 2.2-10L1.7 12.3l10.1-1z" fill="#1c2a22" stroke="#4b6b55" stroke-width="1.6"/></svg>'};
for(const [k,v] of Object.entries(hudSvg))await write(`Assets/Art/ui/hud_${k}.svg`,v);
// 글꼴 : 대화창 Pretendard + 논의용 인물·감정 글꼴(docs/spec/04 §4-3). 라이선스 파일도 같이 복사
const fontFiles={pretendard:['Pretendard-Medium.otf','LICENSE.txt'],blackhansans:['BlackHanSans-Regular.ttf','OFL.txt'],gothica1:['GothicA1-Light.ttf','GothicA1-Regular.ttf','GothicA1-Bold.ttf','OFL.txt'],songmyung:['SongMyung-Regular.ttf','OFL.txt'],jua:['Jua-Regular.ttf','OFL.txt'],notoserifkr:['NotoSerifKR[wght].ttf','OFL.txt'],gowundodum:['GowunDodum-Regular.ttf','OFL.txt'],gowunbatang:['GowunBatang-Regular.ttf','OFL.txt'],cutefont:['CuteFont-Regular.ttf','OFL.txt'],dohyeon:['DoHyeon-Regular.ttf','OFL.txt'],galmuri:['Galmuri11.ttf','LICENSE.txt'],dokdo:['Dokdo-Regular.ttf','OFL.txt'],eastseadokdo:['EastSeaDokdo-Regular.ttf','OFL.txt'],gugi:['Gugi-Regular.ttf','OFL.txt'],kiranghaerang:['KirangHaerang-Regular.ttf','OFL.txt'],gaegu:['Gaegu-Regular.ttf','OFL.txt'],nanumpenscript:['NanumPenScript-Regular.ttf','OFL.txt']};
for(const [dir,files] of Object.entries(fontFiles))for(const f of files)await copy(`fonts/${dir}/${f}`,`Assets/Fonts/${dir}/${f.replace('[wght]','-VF')}`);
// 배경·재판장 (4차 에셋이 있으면)
let bgs=[];try{bgs=(await fs.readdir(path.join(repo,'bg'))).filter(f=>f.endsWith('.webp'));}catch(e){if(e.code!=='ENOENT')throw e;}
for(const f of bgs)await copy('bg/'+f,'Assets/Art/bg/'+f);
await write('Assets/Data/art.json',{backgrounds:bgs.map(f=>f.slice(0,-5))});

// 4) UI 위젯 (1280×720 기준, V3식 대화창)
const body='Assets/Fonts/pretendard/Pretendard-Medium.otf',head='Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf';
const MAIN_GLYPHS=48,NOISE_GLYPHS=26;
const w=createWidgetAsset('W_Yumeno');w.scaleMode='scale';w.scaleRule='fit';
const add=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#f4f0f6',background:'#00000000',padding:0,focusable:false,...props});w.nodes.push(n);return n;};
add('Panel','Backdrop',[0,0,1280,720],{background:'#17121f'});
add('Image','Background',[-40,-24,1360,768],{texture:'',imageFit:'cover',visible:false});
// 논의 글자 : 글자 하나 = Text 하나. 정렬점 중심(.5,.5)이라 SetPosition 이 글자 중심, 배율·회전도 중심 기준
const glyph=(id,parent,size)=>{const n=add('Text',id,[0,0,size*1.6,size*1.6],{fontSize:size,align:'center',visible:false,wrap:false},parent);n.slot.alignment=[.5,.5];};
add('Panel','TrialBack',[0,0,1280,720],{visible:false});
for(let i=0;i<MAIN_GLYPHS;i++)glyph('MB'+i,'TrialBack',50);for(let i=0;i<NOISE_GLYPHS;i++)glyph('NB'+i,'TrialBack',34);
add('Image','Portrait',[290,0,700,700],{texture:'',imageFit:'contain',visible:false});
add('Image','SpeakerPodium',[478,431,323,351],{texture:'',imageFit:'fill',visible:false}); // 화자 앞 증언대(3D 증언대와 같은 자리, 입상 위에 그림)
add('Image','DialogFrame',[80,512,1120,170],{texture:'Assets/Art/ui/frame.png',imageFit:'fill'});
add('Image','Nameplate',[104,486,220,44],{texture:'Assets/Art/ui/nameplate.png',imageFit:'fill'});
add('Text','Name',[118,490,196,36],{font:head,fontSize:26,align:'center',color:'#ffffff'});
add('Text','Body',[136,548,1010,120],{fontSize:25,wrap:true});
// 논스톱 논의 (V3) HUD + 화자 앞쪽 글자층
add('Panel','Trial',[0,0,1280,720],{visible:false});
for(let i=0;i<MAIN_GLYPHS;i++)glyph('MF'+i,'Trial',50);for(let i=0;i<NOISE_GLYPHS;i++)glyph('NF'+i,'Trial',34);
add('Image','NamePanel',[22,12,420,80],{texture:'Assets/Art/ui/hud_name.svg',imageFit:'fill'},'Trial');
add('Text','TrialSpeaker',[66,20,300,34],{font:head,fontSize:24,color:'#ffffff'},'Trial');
add('Image','StatusPanel',[936,52,330,116],{texture:'Assets/Art/ui/hud_status.svg',imageFit:'fill'},'Trial');
add('Text','StatusLabel',[994,58,140,22],{text:'STATUS',font:body,fontSize:15,color:'#ffffff'},'Trial');
for(let i=0;i<10;i++)add('Image','Heart'+i,[990+i*25,90-i*1.6,26,26],{texture:'Assets/Art/ui/hud_heartOn.svg',imageFit:'contain'},'Trial');
for(let i=0;i<10;i++)add('Image','Star'+i,[978+i*25,128-i*1.6,24,24],{texture:'Assets/Art/ui/hud_starOn.svg',imageFit:'contain'},'Trial');
add('Image','Cylinder',[4,470,140,140],{texture:'Assets/Art/ui/bullet_cylinder.png',imageFit:'contain'},'Trial');
add('Image','BulletPlate',[122,560,420,50],{texture:'Assets/Art/ui/hud_bullet.svg',imageFit:'fill'},'Trial');
add('Text','Bullet',[156,567,370,36],{font:head,fontSize:25,color:'#ffffff'},'Trial');
add('Text','BulletLabel',[220,612,160,20],{text:'언령',font:body,fontSize:15,color:'#d9e7ee'},'Trial');
add('Image','TimerPanel',[938,644,330,64],{texture:'Assets/Art/ui/hud_timer.svg',imageFit:'fill'},'Trial');
add('Text','Timer',[1004,652,240,48],{font:'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf',fontSize:42,color:'#ffb21f',align:'right'},'Trial');
add('Image','VPoint',[0,0,22,22],{texture:'Assets/Art/ui/vpoint.svg',imageFit:'contain',visible:false},'Trial').slot.alignment=[.5,.5];
add('Text','TrialMsg',[0,300,1280,80],{font:head,fontSize:60,align:'center',color:'#ff8fc8',visible:false},'Trial');
add('Image','Cutin',[128,200,1024,342],{texture:'Assets/Art/ui/cutin_objection.png',imageFit:'contain',visible:false},'Trial');
add('Image','Aim',[608,328,64,64],{texture:'Assets/Art/ui/aim.svg',imageFit:'contain'},'Trial');
add('Panel','Title',[0,0,1280,720],{background:'#0f0b16'});
add('Text','TitleLogo',[0,220,1280,110],{text:'夢の国  유메노쿠니',font:head,fontSize:84,align:'center',color:'#ff8fc8'},'Title');
add('Text','TitleSub',[0,350,1280,40],{text:'Enter  새로 시작      C  이어하기      T  1장 재판 체험',fontSize:26,align:'center',color:'#efe6f4'},'Title');
add('Panel','Pad',[0,0,1280,720],{background:'#120d1af2',visible:false});
add('Text','PadHead',[120,48,1040,60],{text:'래피 패드  ·  교칙',font:head,fontSize:40,color:'#ff8fc8'},'Pad');
add('Text','PadBody',[120,120,1040,560],{fontSize:21,wrap:true},'Pad');
add('Text','PadHint',[120,676,1040,30],{text:'Tab 닫기',fontSize:18,color:'#b9a9c6'},'Pad');
await write('Assets/UI/Main.hbwidget.json',w);

// 5) 3D 학급 재판장 장면 (docs/spec/15 §2, Source/Courtroom.hpp 와 같은 수치) + 블루프린트 (Tick → Yumeno.Update)
const R=5.5,PODIUM_INSET=.25,SPRITE=2.3,SPRITE_Y=1.25,PODIUM_W=1.15,PODIUM_H=1.25,FOV=43.6;
const SEATS=['mio','rin','ken','nana','taiga','ai','rei','sora','haruka','sho','koto','akari','riku','satsuki','yuu','kaede'];
// 재판장 소품 : 4차 그림(art/trial3d/*.webp)이 있으면 쓰고, 없으면 임시 도형
const placeholder={
 podium:'<svg xmlns="http://www.w3.org/2000/svg" width="230" height="250"><defs><linearGradient id="g" x2="1"><stop stop-color="#0d6b6e" stop-opacity=".85"/><stop offset=".5" stop-color="#4fe0d6" stop-opacity=".55"/><stop offset="1" stop-color="#0d6b6e" stop-opacity=".85"/></linearGradient></defs><rect x="18" y="40" width="194" height="210" fill="url(#g)" stroke="#b9fff6" stroke-width="3"/><rect x="0" y="18" width="230" height="30" fill="#103c46" stroke="#b9fff6" stroke-width="3"/><rect x="70" y="24" width="90" height="18" fill="#e9fffb"/><path d="M40 60v170M115 60v170M190 60v170" stroke="#b9fff6" stroke-opacity=".5" stroke-width="2"/></svg>',
 floor:'<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024"><circle cx="512" cy="512" r="512" fill="#0b2335"/>'+[470,400,330,250,170,90].map((r,i)=>`<circle cx="512" cy="512" r="${r}" fill="none" stroke="${i%2?'#1d6f9e':'#36c6e0'}" stroke-width="${i%2?14:6}"/>`).join('')+'<circle cx="512" cy="512" r="60" fill="#36c6e0" fill-opacity=".25"/></svg>',
 wall:'<svg xmlns="http://www.w3.org/2000/svg" width="768" height="1024"><rect width="768" height="1024" fill="#0c1f27"/><rect x="0" y="880" width="768" height="144" fill="#081419"/><path d="M164 820V300a220 220 0 0 1 440 0v520z" fill="#2a1030" stroke="#3fb8b0" stroke-width="10"/>'+Array.from({length:18},(_,i)=>`<rect x="${190+(i%6)*66}" y="${330+Math.floor(i/6)*150}" width="60" height="140" fill="${['#ff6fb5','#a46bff','#ffd0f0','#6fd3ff','#ff9fd0','#c58bff'][i%6]}" fill-opacity=".55"/>`).join('')+'</svg>',
 throne:'<svg xmlns="http://www.w3.org/2000/svg" width="700" height="700"><rect x="80" y="430" width="540" height="270" fill="#2a1a20" stroke="#c9a24c" stroke-width="8"/><rect x="250" y="120" width="200" height="320" rx="20" fill="#9b1c2e" stroke="#c9a24c" stroke-width="8"/><rect x="230" y="380" width="240" height="70" fill="#7a1222"/><rect x="90" y="60" width="90" height="360" fill="#b3172f"/><rect x="520" y="60" width="90" height="360" fill="#b3172f"/><circle cx="135" cy="200" r="28" fill="#f2d27a"/><circle cx="565" cy="200" r="28" fill="#f2d27a"/></svg>',
 dead:'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400"><rect x="70" y="40" width="260" height="320" fill="#2c2c34" stroke="#d9d9e0" stroke-width="10"/><path d="M110 80l180 240M290 80L110 320" stroke="#ff4fa3" stroke-width="26" stroke-linecap="round"/></svg>'};
const prop={};
for(const [name,svgText] of Object.entries(placeholder)){
 const real=path.join(repo,'art/trial3d',name==='dead'?'portrait_frame.webp':name+'.webp');
 try{await fs.access(real);await copy(path.relative(repo,real),`Assets/Art/trial3d/${name}.webp`);prop[name]=`Assets/Art/trial3d/${name}.webp`;}
 catch{await write(`Assets/Art/trial3d/${name}.svg`,svgText);prop[name]=`Assets/Art/trial3d/${name}.svg`;}
}
await write('Assets/Data/court.json',prop);
const scene=makeStarterScene('유메노쿠니','3d');scene.objects=[];
Object.assign(scene.environment,{skyEnabled:false,sunEnabled:false,cloudsEnabled:false,fogEnabled:false,shadowEnabled:false});
const sprite=(id,texture,position,w,h,extra={},rotation=[0,0,0])=>({id,name:id,kind:'sprite',position,rotation,scale:[1,1,1],visible:true,components:[makeSceneComponent('SpriteRenderer',{texture,width:w,height:h,color:[1,1,1,1],shading:'unlit',toneMapping:'display',...extra})]});
scene.objects.push({id:'Camera',name:'재판 카메라',kind:'camera',position:[0,1.5,-2.3],rotation:[0,180,0],scale:[1,1,1],visible:true,components:[makeSceneComponent('Camera',{projection:'perspective',fieldOfView:FOV,main:true,near:.05,far:200})]});
scene.objects.push(sprite('Floor',prop.floor,[0,0,0],15,15,{},[-90,0,0]));
for(let i=0;i<12;i++){const b=i*30*Math.PI/180;scene.objects.push(sprite('Wall'+i,prop.wall,[13*Math.sin(b),3.4,13*Math.cos(b)],7.2,9.6,{},[0,i*30+180,0]));}
scene.objects.push(sprite('Throne',prop.throne,[0,1.9,-(R+3.4)],4,4,{billboard:true}));
scene.objects.push(sprite('Host',`Assets/Art/sprites/lappy/lappy_L01.webp`,[0,3.15,-(R+3.3)],1.3,1.3,{billboard:true}));
SEATS.forEach((slug,i)=>{
 const a=i*22.5*Math.PI/180;
 scene.objects.push(sprite('Seat'+i,`Assets/Art/sprites/${slug}/${slug}_C01.webp`,[R*Math.sin(a),SPRITE_Y,R*Math.cos(a)],SPRITE,SPRITE,{billboard:true}));
 scene.objects.push(sprite('Podium'+i,prop.podium,[(R-PODIUM_INSET)*Math.sin(a),PODIUM_H/2,(R-PODIUM_INSET)*Math.cos(a)],PODIUM_W,PODIUM_H,{billboard:true}));
});
const header=await fs.readFile(path.join(root,'Source/Yumeno.h'),'utf8'),source=await fs.readFile(path.join(root,'Source/Yumeno.cpp'),'utf8');
const bp=createAsset('blueprint','BP_Yumeno');bp.settings.parentClass='Yumeno';bp.native={...parseNativeHeader(header),header,source,headerPath:'Source/Yumeno.h',sourcePath:'Source/Yumeno.cpp'};bp.nodes=[];bp.edges=[];
const tick=makeNode('tick',100,180),call=makeNode('nativeCall',400,180);call.nativeId='Yumeno.Update';bp.nodes.push(tick,call);
for(const [pin,input] of [['then','exec'],['delta','delta']]){const r=connect(bp,{node:tick.id,pin},{node:call.id,pin:input});if(!r.ok)throw Error(r.message);}
scene.objects.push({id:'Driver',name:'게임 진행',kind:'empty',position:[0,0,0],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[],blueprintAsset:'Assets/Blueprints/BP_Yumeno.hbblueprint.json'});
await write('Assets/Blueprints/BP_Yumeno.hbblueprint.json',bp);await write('Assets/Scenes/Main.hbscene.json',scene);

let id=randomUUID();try{id=JSON.parse(await fs.readFile(path.join(root,'YumenoKuni.hbproject'),'utf8')).id;}catch(e){if(e.code!=='ENOENT')throw e;}
await write('YumenoKuni.hbproject',{version:1,engine:'HBEngine',engineVersion:'0.1.0',id,name:'YumenoKuni',startupScene:'Assets/Scenes/Main.hbscene.json',startupBlueprint:'Assets/Blueprints/BP_Yumeno.hbblueprint.json'});
console.log(JSON.stringify({scenes:sceneFiles.length,rules:rules.length,widgets:w.nodes.length}));
