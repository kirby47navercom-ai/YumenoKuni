// 유메노쿠니 HBEngine 프로젝트 생성기 : 각본 데이터·스프라이트·UI·장면·블루프린트를 Assets/ 아래에 만든다.
// node tools/create-project.mjs   (엔진 원본은 ../../../engineCreate 를 읽기만 한다)
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {randomUUID} from 'node:crypto';
import {execFileSync} from 'node:child_process';
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
await write('Assets/Data/story.json',{chapters:['P','1','2','3','4','5','6'],trials:['11c','12c'],dead:{'11c':['taiga'],'12c':['taiga','sho','yuu']}});
// 장 진행표 (tools/build_flow.py) · 선물 · 언령 이름
for(const f of (await fs.readdir(path.join(repo,'data/flow'))).filter(f=>f.endsWith('.json')))await copy('data/flow/'+f,'Assets/Data/flow/'+f);
await copy('data/gifts.json','Assets/Data/gifts.json');await copy('data/reactions.json','Assets/Data/reactions.json');
await copy('data/kotodama.json','Assets/Data/kotodama.json'); // 이름·설명 : tools/build_trial.py · build_flow.py
for(const f of (await fs.readdir(path.join(repo,'data/trials'))).filter(f=>f.endsWith('.json')))await copy('data/trials/'+f,'Assets/Data/trials/'+f);

// 2) 교칙 : docs/spec/11 §2·§3 표
const rulesDoc=await fs.readFile(path.join(repo,'docs/spec/11_래피패드_교칙.md'),'utf8');
const rules=[...rulesDoc.matchAll(/^\| (교칙 \d+|[1-6]장) \| ([^|]+) \|/gm)].map(m=>({no:m[1],text:m[2].trim().replace(/\*\*/g,'')}));
await write('Assets/Data/rules.json',{rules});

// 3) 그림 : 스프라이트(WebP)·UI·글꼴 복사
// 스프라이트는 1024²로 줄여 넣는다(텍스처 메모리) : tools/game_sprites.py
execFileSync('python',[path.join(repo,'tools/game_sprites.py')],{stdio:'inherit'});
for(const f of ['dialog/frame.png','dialog/nameplate.png','trial/heart_full.png','trial/heart_empty.png','trial/cutin_objection.png','trial/focus_track.png','trial/focus_fill.png','trial/bullet_cylinder.png'])await copy('ui/'+f,'Assets/Art/ui/'+path.basename(f));
await write('Assets/Art/ui/aim.svg','<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><circle cx="32" cy="32" r="22" fill="none" stroke="#ff4fa3" stroke-width="4"/><circle cx="32" cy="32" r="3" fill="#ffffff"/><path d="M32 2v14M32 48v14M2 32h14M48 32h14" stroke="#ffffff" stroke-width="3"/></svg>');
await write('Assets/Art/ui/vpoint.svg','<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22"><circle cx="11" cy="11" r="9" fill="#ff2040" stroke="#ffffff" stroke-width="2"/></svg>');

// V3 논의 렌즈 : 가운데 투명, 가장자리 어둡게 + 동심원 + 흰·빨강 사각 조각 (docs/spec/16 §5-2)
await write('Assets/Art/ui/lens.svg','<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"><defs><radialGradient id="v" cx="50%" cy="50%" r="62%"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#05020a" stop-opacity=".92"/></radialGradient></defs><rect width="1280" height="720" fill="url(#v)"/>'+[360,430,520].map((r,i)=>`<circle cx="640" cy="360" r="${r}" fill="none" stroke="#ffffff" stroke-opacity="${.22-i*.05}" stroke-width="${2+i}"/>`).join('')+[[40,70,34,'#fff'],[88,150,22,'#d81f2a'],[1180,120,30,'#fff'],[1210,200,44,'#d81f2a'],[60,520,26,'#fff'],[1150,560,20,'#fff'],[130,610,40,'#d81f2a'],[1220,470,24,'#fff']].map(([x,y,w,c])=>`<rect x="${x}" y="${y}" width="${w}" height="${w}" fill="none" stroke="${c}" stroke-opacity=".7" stroke-width="3"/><rect x="${x+6}" y="${y+6}" width="${w-12}" height="${w-12}" fill="${c}" fill-opacity=".35"/>`).join('')+'</svg>');
for(const [k,t,c] of [['nonstop','NON-STOP DEBATE','#ffe36e'],['panic','MASS PANIC DEBATE','#ff4fa3']])await write(`Assets/Art/ui/start_${k}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="200"><path d="M0 40L1280 0V160L0 200Z" fill="#0b0812" fill-opacity=".9"/><path d="M0 40L1280 0M0 200L1280 160" stroke="${c}" stroke-width="6"/><text x="640" y="128" text-anchor="middle" font-family="Arial Black,Arial" font-weight="900" font-style="italic" font-size="96" fill="#ffffff" stroke="${c}" stroke-width="4" transform="rotate(-1.8 640 100)">${t}</text></svg>`);
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
// 4차 HUD 그림이 있으면 임시 SVG 대신 쓴다
const hud=k=>{return hudPng.has(k)?`Assets/Art/ui/hud_${k}.png`:`Assets/Art/ui/hud_${k}.svg`;};
const hudPng=new Set();for(const k of ['name','status','bullet','timer']){try{await copy(`ui/trial/hud_${k}.png`,`Assets/Art/ui/hud_${k}.png`);hudPng.add(k);}catch(e){if(e.code!=='ENOENT')throw e;}}
for(const f of ['title_bg.png','title_logo.png','chapter_1.png','chapter_P.png'])try{await copy('ui/common/'+f,'Assets/Art/ui/'+f);}catch(e){if(e.code!=='ENOENT')throw e;}
// 글꼴 : 대화창 Pretendard + 논의용 인물·감정 글꼴(docs/spec/04 §4-3). 라이선스 파일도 같이 복사
const fontFiles={pretendard:['Pretendard-Medium.otf','LICENSE.txt'],blackhansans:['BlackHanSans-Regular.ttf','OFL.txt'],gothica1:['GothicA1-Light.ttf','GothicA1-Regular.ttf','GothicA1-Bold.ttf','OFL.txt'],songmyung:['SongMyung-Regular.ttf','OFL.txt'],jua:['Jua-Regular.ttf','OFL.txt'],notoserifkr:['NotoSerifKR[wght].ttf','OFL.txt'],gowundodum:['GowunDodum-Regular.ttf','OFL.txt'],gowunbatang:['GowunBatang-Regular.ttf','OFL.txt'],cutefont:['CuteFont-Regular.ttf','OFL.txt'],dohyeon:['DoHyeon-Regular.ttf','OFL.txt'],galmuri:['Galmuri11.ttf','LICENSE.txt'],dokdo:['Dokdo-Regular.ttf','OFL.txt'],eastseadokdo:['EastSeaDokdo-Regular.ttf','OFL.txt'],gugi:['Gugi-Regular.ttf','OFL.txt'],kiranghaerang:['KirangHaerang-Regular.ttf','OFL.txt'],gaegu:['Gaegu-Regular.ttf','OFL.txt'],nanumpenscript:['NanumPenScript-Regular.ttf','OFL.txt']};
for(const [dir,files] of Object.entries(fontFiles))for(const f of files)await copy(`fonts/${dir}/${f}`,`Assets/Fonts/${dir}/${f.replace('[wght]','-VF')}`);
// 배경·재판장 (4차 에셋이 있으면)
let bgs=[];try{bgs=(await fs.readdir(path.join(repo,'bg'))).filter(f=>f.endsWith('.webp'));}catch(e){if(e.code!=='ENOENT')throw e;}
for(const f of bgs)await copy('bg/'+f,'Assets/Art/bg/'+f);
// 언령 카드 그림 (있는 것만)
let icons=[];try{icons=(await fs.readdir(path.join(repo,'ui/kotodama'))).filter(f=>/^[ETMNR]\d?-\d+.*\.png$/.test(f));}catch(e){if(e.code!=='ENOENT')throw e;}
for(const f of icons)await copy('ui/kotodama/'+f,'Assets/Art/kotodama/'+f);
for(const f of ['frame_evidence','frame_testimony','frame_rule_magic','frame_memo'])await copy(`ui/kotodama/${f}.png`,`Assets/Art/ui/kotodama/${f}.png`);
// CG(사망·처형·이벤트)·선물·패드·장 제목 카드 (있는 것만)
const list=async(dir,re)=>{try{return (await fs.readdir(path.join(repo,dir))).filter(f=>re.test(f));}catch(e){if(e.code==='ENOENT')return [];throw e;}};
for(const f of await list('art/cutin',/\.webp$/))await copy('art/cutin/'+f,'Assets/Art/cutin/'+f);
const cgs=(await list('art/cg',/\.webp$/)).filter(f=>!/_(bg|fg)\.webp$/.test(f));for(const f of cgs)await copy('art/cg/'+f,'Assets/Art/cg/'+f);
const giftIcons=await list('ui/gift',/^G\d\d\.png$/);for(const f of giftIcons)await copy('ui/gift/'+f,'Assets/Art/gift/'+f);
const padArt=await list('ui/pad',/^(coin|capsule_machine|face_\w+|map_\w+)\.png$/);for(const f of padArt)await copy('ui/pad/'+f,'Assets/Art/pad/'+f);
const cards=await list('ui/common',/^(chapter_\w+|gameover|credits_bg|ending_\w+)\.png$/);for(const f of cards)await copy('ui/common/'+f,'Assets/Art/ui/'+f);
// 소리 : audio/cues.json 에 파일이 적힌 것만
const cues=JSON.parse(await fs.readFile(path.join(repo,'audio/cues.json'),'utf8')),audio={};
for(const group of ['bgm','sfx'])for(const [k,v] of Object.entries(cues[group]||{}))if(v&&v.file){try{await copy('audio/'+v.file,'Assets/Audio/'+v.file);audio[k]='Assets/Audio/'+v.file;}catch(e){if(e.code!=='ENOENT')throw e;}}
await write('Assets/Data/art.json',{backgrounds:bgs.map(f=>f.slice(0,-5)),kotodama:icons.map(f=>f.slice(0,-4)),cg:cgs.map(f=>f.slice(0,-5)),gifts:giftIcons.map(f=>f.slice(0,-4)),pad:padArt.map(f=>f.slice(0,-4)),cards:cards.map(f=>f.slice(0,-4)),audio});

// 4) UI 위젯 (1280×720 기준, V3식 대화창)
const body='Assets/Fonts/pretendard/Pretendard-Medium.otf',head='Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf';
const MAIN_GLYPHS=48,NOISE_GLYPHS=26;
const w=createWidgetAsset('W_Yumeno');w.scaleMode='scale';w.scaleRule='fit';
const add=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#f4f0f6',background:'#00000000',padding:0,focusable:false,...props});w.nodes.push(n);return n;};
add('Panel','Backdrop',[0,0,1280,720],{background:'#17121f'});
add('Image','Background',[-40,-24,1360,768],{texture:'',imageFit:'cover',visible:false});
// 논의 글자 : 글자 하나 = Text 하나. 정렬점 중심(.5,.5)이라 SetPosition 이 글자 중심, 배율·회전도 중심 기준
const glyph=(id,parent,size)=>{const n=add('Text',id,[0,0,size*1.6,size*1.6],{fontSize:size,align:'center',visible:false,wrap:false},parent);n.slot.alignment=[.5,.5];};
add('Panel','CourtDim',[0,0,1280,720],{background:'#12051f80',visible:false}); // V3 법정은 어둡고 보라빛 : 3D 위·화자 입상 아래
add('Panel','TrialBack',[0,0,1280,720],{visible:false});
for(let i=0;i<MAIN_GLYPHS;i++)glyph('MB'+i,'TrialBack',50);for(let i=0;i<NOISE_GLYPHS;i++)glyph('NB'+i,'TrialBack',34);
add('Image','Portrait',[290,0,700,700],{texture:'',imageFit:'contain',visible:false});
add('Image','SpeakerPodium',[478,431,323,351],{texture:'',imageFit:'fill',visible:false}); // 화자 앞 증언대(3D 증언대와 같은 자리, 입상 위에 그림)
add('Image','DialogFrame',[80,512,1120,170],{texture:'Assets/Art/ui/frame.png',imageFit:'fill'});
add('Image','Nameplate',[104,486,220,44],{texture:'Assets/Art/ui/nameplate.png',imageFit:'fill'});
add('Text','Name',[126,490,190,36],{font:head,fontSize:26,color:'#ffffff'});
add('Text','NameHead',[126,490,40,36],{font:head,fontSize:26,color:'#ff8fc8'}); // V3 : 이름 첫 글자만 인물 색
add('Text','Next',[1136,640,40,32],{text:'≫',font:head,fontSize:30,color:'#ffd21f',visible:false}); // 다 읽으면 깜빡이는 넘김 표시
add('Text','Body',[136,548,1010,120],{fontSize:25,wrap:true});
// 논스톱 논의 (V3) HUD + 화자 앞쪽 글자층
add('Panel','Trial',[0,0,1280,720],{visible:false});
add('Image','Lens',[0,0,1280,720],{texture:'Assets/Art/ui/lens.svg',imageFit:'fill',visible:false},'Trial');
for(let i=0;i<MAIN_GLYPHS;i++){const n=add('Text','MS'+i,[0,0,80,80],{fontSize:50,align:'center',visible:false,wrap:false,color:'#05020a'},'Trial');n.slot.alignment=[.5,.5];}
for(let i=0;i<MAIN_GLYPHS;i++)glyph('MF'+i,'Trial',50);for(let i=0;i<NOISE_GLYPHS;i++)glyph('NF'+i,'Trial',34);
add('Image','NamePanel',[22,12,420,80],{texture:hud('name'),imageFit:'fill'},'Trial');
add('Text','TrialSpeaker',[66,20,300,34],{font:head,fontSize:24,color:'#ffffff'},'Trial');
add('Image','StatusPanel',[936,52,330,116],{texture:hud('status'),imageFit:'fill'},'Trial');
add('Text','StatusLabel',[994,58,140,22],{text:'STATUS',font:body,fontSize:15,color:'#ffffff'},'Trial');
for(let i=0;i<10;i++)add('Image','Heart'+i,[990+i*25,90-i*1.6,26,26],{texture:'Assets/Art/ui/hud_heartOn.svg',imageFit:'contain'},'Trial');
for(let i=0;i<10;i++)add('Image','Star'+i,[978+i*25,128-i*1.6,24,24],{texture:'Assets/Art/ui/hud_starOn.svg',imageFit:'contain'},'Trial');
add('Image','Cylinder',[4,470,140,140],{texture:'Assets/Art/ui/bullet_cylinder.png',imageFit:'contain'},'Trial');
add('Image','BulletPlate',[122,560,420,50],{texture:hud('bullet'),imageFit:'fill'},'Trial');
add('Text','Bullet',[156,567,370,36],{font:head,fontSize:25,color:'#ffffff'},'Trial');
add('Text','BulletLabel',[220,612,160,20],{text:'언령',font:body,fontSize:15,color:'#d9e7ee'},'Trial');
add('Image','TimerPanel',[938,644,330,64],{texture:hud('timer'),imageFit:'fill'},'Trial');
add('Text','Timer',[1004,652,240,48],{font:'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf',fontSize:42,color:'#ffb21f',align:'right'},'Trial');
add('Image','VPoint',[0,0,22,22],{texture:'Assets/Art/ui/vpoint.svg',imageFit:'contain',visible:false},'Trial').slot.alignment=[.5,.5];
add('Image','StartBand',[0,250,1280,200],{texture:'Assets/Art/ui/start_nonstop.svg',imageFit:'fill',visible:false},'Trial');
add('Text','TrialMsg',[0,300,1280,80],{font:head,fontSize:60,align:'center',color:'#ff8fc8',visible:false},'Trial');
add('Image','Cutin',[128,200,1024,342],{texture:'Assets/Art/ui/cutin_objection.png',imageFit:'contain',visible:false},'Trial');
add('Image','Aim',[608,328,64,64],{texture:'Assets/Art/ui/aim.svg',imageFit:'contain'},'Trial');
add('Panel','Title',[0,0,1280,720],{background:'#0f0b16'});
add('Image','TitleBg',[0,0,1280,720],{texture:'Assets/Art/ui/title_bg.png',imageFit:'cover'},'Title');
add('Image','TitleLogo',[300,120,680,300],{texture:'Assets/Art/ui/title_logo.png',imageFit:'contain'},'Title');
add('Text','TitleSub',[0,470,1280,40],{text:'Enter  새로 시작          C  이어하기',fontSize:26,align:'center',color:'#efe6f4'},'Title');
add('Panel','Pad',[0,0,1280,720],{background:'#120d1af2',visible:false});
add('Text','PadHead',[120,48,1040,60],{text:'래피 패드',font:head,fontSize:40,color:'#ff8fc8'},'Pad');
add('Text','PadBody',[120,120,1040,560],{fontSize:21,wrap:true},'Pad');
add('Text','PadHint',[120,676,1040,30],{text:'Q / E  탭 넘기기      Tab  닫기',fontSize:18,color:'#b9a9c6'},'Pad');
await write('Assets/UI/Main.hbwidget.json',w);

// 4-2) 재판 단계 위젯 (객관식·언령 고르기·지점·인물 지목·투표·쇼다운·스크럼·이론 무장·애너그램·발굴·택시·클라이맥스). Main 위에 겹쳐 띄운다.
// 좌표는 Source/TrialRunner.hpp 의 상수와 같다.
{
 const v=createWidgetAsset('W_Stage');v.scaleMode='scale';v.scaleRule='fit';
 const put=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:false,...props});v.nodes.push(n);return n;};
 put('Panel','Shade',[0,0,1280,720],{background:'#05030acc'});
 put('Image','QPlate',[140,28,1000,64],{texture:hud('bullet'),imageFit:'fill'});
 put('Text','Question',[180,38,930,46],{font:head,fontSize:28,align:'center'});
 // V3 선택 화면 장식 (docs/spec/16 §5-2 재판) : 문장·ANSWER·모래시계·화자 이름표·아래 질문·조작 안내
 const svg=(name,body,w,h)=>write(`Assets/Art/ui/${name}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">${body}</svg>`);
 const black='font-family="Arial Black,Arial" font-weight="900" font-style="italic"';
 await svg('cls_emblem',`<path d="M10 92L46 8h34L44 92z" fill="#ff4fa3"/><text x="58" y="56" ${black} font-size="30" fill="#36e3ff">CLASS</text><text x="58" y="88" ${black} font-size="30" fill="#36e3ff">TRIAL</text>`,200,100);
 await svg('answer',`<text x="6" y="48" ${black} font-size="50" fill="none" stroke="#b6ff3d" stroke-width="3">ANSWER</text><text x="6" y="48" ${black} font-size="50" fill="#e9ffcf" opacity=".35">ANSWER</text>`,260,60);
 await svg('band_off','<path d="M14 2H1000V40H0z" fill="#0b1018" fill-opacity=".78"/><path d="M14 2H1000" stroke="#ffffff" stroke-opacity=".25"/>',1000,42);
 await svg('band_on','<path d="M14 2H1000V40H0z" fill="#1c6fd6" fill-opacity=".92"/><path d="M14 2H1000M0 40H1000" stroke="#9fe0ff" stroke-width="2"/>',1000,42);
 await svg('hourglass','<path d="M10 6h100M10 234h100" stroke="#36e3ff" stroke-width="8"/><path d="M20 12c0 70 80 70 80 108s-80 38-80 108" fill="none" stroke="#36e3ff" stroke-width="6"/><path d="M100 12c0 70-80 70-80 108s80 38 80 108" fill="none" stroke="#36e3ff" stroke-width="6"/><path d="M34 40h52c-6 30-26 44-26 70c0-26-20-40-26-70z" fill="#ff4fa3"/><path d="M60 150c-20 12-30 40-32 72h64c-2-32-12-60-32-72z" fill="#ff4fa3"/>',120,240);
 await svg('spk_tag','<path d="M18 0H300L282 56H0z" fill="#0b1018" fill-opacity=".9"/><path d="M18 0H300" stroke="#ff4fa3" stroke-width="4"/>',300,56);
 await svg('q_band','<path d="M0 0H1280V96H0z" fill="#05070c" fill-opacity=".86"/><path d="M0 1H1280" stroke="#36e3ff" stroke-opacity=".6" stroke-width="2"/>',1280,96);
 await svg('bul_line','<path d="M30 0V460" stroke="#ffffff" stroke-opacity=".7" stroke-width="3"/><circle cx="30" cy="8" r="7" fill="#ffffff"/><circle cx="30" cy="452" r="7" fill="#ff4fa3"/>',60,460);
 await svg('bul_cyl','<g fill="none" stroke="#36e3ff" stroke-opacity=".55" stroke-width="10"><circle cx="230" cy="230" r="200"/><circle cx="230" cy="230" r="60"/></g>'+[0,1,2,3,4,5].map(k=>{const a=k*Math.PI/3;return `<circle cx="${230+130*Math.cos(a)}" cy="${230+130*Math.sin(a)}" r="52" fill="#36e3ff" fill-opacity=".18" stroke="#36e3ff" stroke-opacity=".6" stroke-width="6"/>`;}).join(''),460,460);
 await svg('card_frame','<path d="M0 0H400V250H0z" fill="#0b1018" fill-opacity=".9"/><path d="M2 2H398V248H2z" fill="none" stroke="#ffffff" stroke-width="3"/>',400,250);
 await svg('desc_box','<path d="M20 0H440V260H0V20z" fill="#05070c" fill-opacity=".88"/><path d="M20 40H420" stroke="#36e3ff" stroke-width="2"/>',440,260);
 await svg('accuse',`<text x="40" y="64" ${black} font-size="58" fill="#ffffff" stroke="#ff2a6d" stroke-width="3">ACCUSE</text><path d="M4 78L30 10" stroke="#ff2a6d" stroke-width="10"/>`,320,90);
 await svg('acc_ring','<ellipse cx="240" cy="70" rx="230" ry="62" fill="none" stroke="#ff4fa3" stroke-width="14"/><ellipse cx="240" cy="70" rx="170" ry="40" fill="#ff4fa3" fill-opacity=".25"/>',480,140);
 await svg('acc_name','<path d="M20 0H560L540 80H0z" fill="#0b1018" fill-opacity=".85"/><path d="M20 0H560M0 80H540" stroke="#ffe36e" stroke-width="3"/>',560,80);
 await svg('spot_title',`<text x="30" y="58" ${black} font-size="44" fill="#ffffff">SPOT</text><text x="150" y="58" ${black} font-size="30" fill="#ff4fa3">SELECTION</text>`,380,80);
 await svg('spot_frame','<rect x="3" y="3" width="894" height="514" fill="none" stroke="#bfe6ff" stroke-width="6"/>',900,520);
 await svg('spot_mark','<circle cx="30" cy="30" r="22" fill="none" stroke="#7dff5a" stroke-width="4"/><circle cx="30" cy="30" r="5" fill="#7dff5a"/><path d="M30 0v14M30 46v14M0 30h14M46 30h14" stroke="#7dff5a" stroke-width="3"/>',60,60);
 put('Image','Emblem',[18,26,200,100],{texture:'Assets/Art/ui/cls_emblem.svg',imageFit:'contain'});
 put('Image','AnswerLbl',[236,176,260,60],{texture:'Assets/Art/ui/answer.svg',imageFit:'contain'});
 put('Image','Hourglass',[110,236,120,240],{texture:'Assets/Art/ui/hourglass.svg',imageFit:'contain'});
 put('Image','SpkTag',[30,470,300,56],{texture:'Assets/Art/ui/spk_tag.svg',imageFit:'fill'});
 put('Text','SpkName',[52,478,250,40],{font:head,fontSize:26,color:'#ffffff'});
 put('Image','QBand',[0,604,1280,96],{texture:'Assets/Art/ui/q_band.svg',imageFit:'fill'});
 put('Text','QText',[110,616,1060,76],{fontSize:26,color:'#9fe6ff',wrap:true});
 put('Text','Hint',[900,560,360,30],{fontSize:18,color:'#ffffff',align:'right'});
 put('Image','BulCyl',[-140,190,460,460],{texture:'Assets/Art/ui/bul_cyl.svg',imageFit:'contain'});
 put('Image','BulLine',[40,136,60,440],{texture:'Assets/Art/ui/bul_line.svg',imageFit:'fill'});
 put('Image','CardFrame',[840,92,400,250],{texture:'Assets/Art/ui/card_frame.svg',imageFit:'fill'});
 put('Image','CardImg',[846,98,388,238],{texture:'',imageFit:'contain'});
 put('Image','DescBox',[820,350,440,250],{texture:'Assets/Art/ui/desc_box.svg',imageFit:'fill'});
 put('Text','CardTitle',[850,356,400,34],{font:head,fontSize:26,color:'#ffffff'});
 put('Text','CardText',[846,400,400,190],{fontSize:19,color:'#e6f2ff',wrap:true});
 put('Image','AccLbl',[20,20,320,90],{texture:'Assets/Art/ui/accuse.svg',imageFit:'contain'});
 put('Image','AccRing',[270,520,380,110],{texture:'Assets/Art/ui/acc_ring.svg',imageFit:'contain'});
 put('Image','AccFig',[210,40,500,600],{texture:'',imageFit:'contain'});
 put('Image','AccTag',[680,270,560,80],{texture:'Assets/Art/ui/acc_name.svg',imageFit:'fill'});
 put('Text','AccNo',[700,276,90,66],{font:'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf',fontSize:58,color:'#ffe36e'});
 put('Text','AccName',[790,282,430,60],{font:head,fontSize:40,color:'#ffffff'});
 put('Text','AccArrows',[150,300,80,80],{text:'◀',font:head,fontSize:56,align:'center',color:'#ff4fa3'});put('Text','AccArrowR',[690,300,80,80],{text:'▶',font:head,fontSize:56,align:'center',color:'#ff4fa3'});
 put('Image','SpotTitle',[18,20,380,80],{texture:'Assets/Art/ui/spot_title.svg',imageFit:'contain'});
 put('Image','SpotImg',[190,90,900,520],{texture:'',imageFit:'cover'});
 put('Image','SpotFrame',[190,90,900,520],{texture:'Assets/Art/ui/spot_frame.svg',imageFit:'fill'});
 put('Panel','CrossH',[190,0,900,2],{background:'#7dff5a'});put('Panel','CrossV',[0,90,2,520],{background:'#7dff5a'});
 for(let i=0;i<6;i++){const n=put('Image','Mark'+i,[0,0,60,60],{texture:'Assets/Art/ui/spot_mark.svg',imageFit:'contain'});n.slot.alignment=[.5,.5];}
 put('Text','MarkName',[190,560,900,44],{font:head,fontSize:28,align:'center',color:'#16121c',background:'#ffe36ee8'});
 // 보기 8칸 : V3 번호 띠(오른쪽 끝까지), 고른 띠만 파랗게. 좌표는 TrialRunner showOptions 가 정한다
 for(let i=0;i<8;i++){put('Image','OptP'+i,[300,250+i*46,980,42],{texture:'Assets/Art/ui/band_off.svg',imageFit:'fill'});put('Text','OptT'+i,[330,254+i*46,900,34],{fontSize:24});}
 // 클라이맥스 만화 칸 8 (4×2)
 for(let i=0;i<8;i++){const c=i%4,r=Math.floor(i/4);put('Panel','PanP'+i,[24+c*310,102+r*150,298,142],{background:'#f4f0e8',borderWidth:4,borderColor:'#16121c'});put('Text','PanT'+i,[36+c*310,110+r*150,274,126],{fontSize:15,color:'#16121c',wrap:true});}
 // 발굴 이매지네이션 블록 12×6 아래에 보물 3개
 put('Image','MineBg',[160,130,960,420],{texture:'',imageFit:'cover'});
for(let i=0;i<3;i++){put('Image','MineIcon'+i,[180+i*320,272,280,136],{texture:'',imageFit:'contain'});put('Text','MineItem'+i,[180+i*320,376,280,32],{font:head,fontSize:20,align:'center',color:'#ffe9a8',background:'#1b1325d0'});}
 for(const [n,c,d] of [['w','#f4f2f8','#b9b4c8'],['p','#ff8cc8','#c9488c'],['y','#ffd95a','#c79a1c']])await write(`Assets/Art/ui/mine_${n}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="80" height="70"><rect x="1" y="1" width="78" height="68" rx="6" fill="${d}"/><rect x="4" y="3" width="72" height="58" rx="5" fill="${c}"/><path d="M10 10h40" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".7"/></svg>`);
 for(let i=0;i<72;i++){const c=i%12,r=Math.floor(i/12);put('Image','Cell'+i,[160+c*80,130+r*70,80,70],{texture:'Assets/Art/ui/mine_w.svg',imageFit:'fill'});}
 // 섬광 애너그램 : 글자 구슬 10, 빈칸 줄, 빛
 put('Panel','Light',[0,0,260,720],{background:'#fff6c840'});
 for(let i=0;i<10;i++){const n=put('Text','Orb'+i,[0,0,84,84],{font:head,fontSize:40,align:'center',background:'#2b2140',radius:42,color:'#2b2140'});n.slot.alignment=[.5,.5];}
 put('Text','Slots',[240,600,800,70],{font:head,fontSize:46,align:'center',color:'#ffe9a8'});
 // 브레인 드라이브 : 차선 3, 차
 put('Image','Road',[0,0,1280,720],{texture:'Assets/Art/ui/taxi_road.svg',imageFit:'fill'});
 for(let i=0;i<8;i++){const n=put('Panel','Dash'+i,[0,0,10,40],{background:'#ff4fa3'});n.slot.alignment=[.5,.5];}
 for(let i=0;i<3;i++){const n=put('Text','Cube'+i,[0,0,90,90],{font:head,fontSize:48,align:'center',color:'#16121c',background:'#7dfcff',radius:8});n.slot.alignment=[.5,.5];}
 for(let i=0;i<2;i++){const n=put('Image','Rival'+i,[0,0,160,110],{texture:'Assets/Art/ui/taxi_rival.svg',imageFit:'contain'});n.slot.alignment=[.5,.5];}
 for(let i=0;i<3;i++){const n=put('Text','Lane'+i,[0,0,260,120],{font:head,fontSize:24,align:'center',color:'#ffffff',background:'#ff4fa3d8',radius:10,wrap:true});n.slot.alignment=[.5,.5];}
 {const n=put('Image','Car',[0,0,240,150],{texture:'Assets/Art/ui/taxi_car.svg',imageFit:'contain'});n.slot.alignment=[.5,.5];}
 put('Text','TaxiQ',[160,96,960,52],{font:head,fontSize:30,align:'center',color:'#7dfcff',background:'#0b1018cc'});
 // 반론 쇼다운 : 날아오는 발언, 칼 이름
 put('Text','Blade',[0,0,1280,90],{font:head,fontSize:52,align:'center',color:'#ffffff'}).slot.alignment=[0,.5];
 put('Text','BladeName',[880,640,380,50],{font:head,fontSize:26,align:'right',color:'#7dff9a'});
 put('Panel','Slash',[0,0,10,6],{background:'#ffffff'});
 // 이론 무장 : 리듬 고리, 마지막 일격 조각 4
 await write('Assets/Art/ui/arm_ring.svg','<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><circle cx="100" cy="100" r="96" fill="none" stroke="#ff4fa3" stroke-width="6"/></svg>');
 await write('Assets/Art/ui/arm_core.svg','<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="50" fill="#ff4fa3" fill-opacity=".33"/></svg>');
 const ring=put('Image','Ring',[540,260,200,200],{texture:'Assets/Art/ui/arm_ring.svg',imageFit:'contain'});
 put('Image','RingCore',[590,310,100,100],{texture:'Assets/Art/ui/arm_core.svg',imageFit:'contain'});
 put('Text','ArmLine',[140,140,1000,80],{font:head,fontSize:40,align:'center'});
 for(let i=0;i<4;i++)put('Text','Piece'+i,[[540,840,540,240][i],[440,330,560,330][i],200,64],{font:head,fontSize:28,align:'center',background:'#0b1018e6',color:'#ffe9a8'});
 put('Image','ScBand',[0,300,1280,110],{texture:'Assets/Art/ui/scrum_band.svg',imageFit:'fill'});
 put('Panel','ScThemP',[30,110,720,120],{background:'#0b1018e6',borderWidth:3,borderColor:'#ff4fa3'});
 put('Text','ScThemN',[46,118,300,30],{font:head,fontSize:22,color:'#ff8fc8'});
 put('Text','ScThemT',[46,150,690,74],{font:head,fontSize:30,wrap:true});
 put('Panel','ScUsP',[530,436,720,110],{background:'#0b1018e6',borderWidth:3,borderColor:'#36e3ff'});
 put('Text','ScUsN',[546,444,300,30],{font:head,fontSize:22,color:'#7dfcff'});
 put('Text','ScUsT',[546,476,690,66],{font:head,fontSize:28,wrap:true});
 put('Image','SdFace',[-60,60,620,620],{texture:'',imageFit:'contain',opacity:.95}); // 반론 : 상대 큰 얼굴(V3)
 put('Image','ArmFace',[1010,470,260,240],{texture:'',imageFit:'cover'}); // 이론 무장 : 미오 얼굴
 put('Text','StageMsg',[0,300,1280,90],{font:head,fontSize:60,align:'center',color:'#ff8fc8'});
 put('Text','StageTimer',[1040,656,220,48],{font:'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf',fontSize:40,color:'#ffb21f',align:'right'});
 await write('Assets/UI/Stage.hbwidget.json',v);
}
// 4-3) 진행 위젯 W_Flow : 장 제목 카드, 보기 목록, 인물·선물 칸, 알림, 코인, 크레딧. 좌표는 Source/Flow.hpp 와 같다.
{
 const f=createWidgetAsset('W_Flow');f.scaleMode='scale';f.scaleRule='fit';
 const put=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:false,...props});f.nodes.push(n);return n;};
 put('Panel','FCardBack',[0,0,1280,720],{background:'#0b0812'});
 put('Image','FCard',[0,0,1280,720],{texture:'',imageFit:'cover'});
 put('Text','FCardT',[0,250,1280,120],{font:head,fontSize:84,align:'center',color:'#ff8fc8'});
 put('Text','FCardS',[0,380,1280,50],{font:head,fontSize:30,align:'center',color:'#efe6f4'});
 await write('Assets/Art/ui/hud_chapter.svg','<svg xmlns="http://www.w3.org/2000/svg" width="300" height="76"><path d="M40 6H296L282 40H26z" fill="#ffd21f"/><path d="M26 40H282" stroke="#16121c" stroke-width="2"/><path d="M60 50H290L282 70H52z" fill="#16121c" fill-opacity=".8"/><circle cx="34" cy="26" r="22" fill="#ffd21f" stroke="#16121c" stroke-width="3"/><path d="M22 10l6 10M46 10l-6 10" stroke="#ff4fa3" stroke-width="5" stroke-linecap="round"/><circle cx="28" cy="28" r="3" fill="#16121c"/><circle cx="40" cy="28" r="3" fill="#d81f2a"/></svg>');
 put('Image','FHudImg',[966,10,300,76],{texture:'Assets/Art/ui/hud_chapter.svg',imageFit:'fill',visible:true});
 put('Text','FHud',[1000,14,250,30],{font:head,fontSize:22,align:'right',color:'#16121c',visible:true});
 put('Text','FHudSub',[1030,58,220,22],{fontSize:15,align:'right',color:'#ffe9a8',visible:true});
 put('Panel','FShade',[0,0,1280,720],{background:'#05030a99'});
 put('Text','FMenuQ',[200,120,880,56],{font:head,fontSize:30,align:'center',background:'#0b1018e6'});
 for(let i=0;i<9;i++){put('Panel','FOptP'+i,[340,200+i*58,600,50],{background:'#0b1018e6',borderWidth:2,borderColor:'#ff4fa3',radius:6});put('Text','FOptT'+i,[360,208+i*58,560,36],{fontSize:22});}
 put('Text','FGridHead',[160,40,960,50],{font:head,fontSize:32,align:'center',color:'#ff8fc8'});
 for(let i=0;i<16;i++){const x=150+(i%4)*250,y=110+Math.floor(i/4)*130;put('Panel','FCell'+i,[x,y,236,120],{background:'#0b1018e6',borderWidth:2,borderColor:'#36e3ff',radius:8});put('Image','FFace'+i,[x+6,y+6,108,108],{texture:'',imageFit:'cover'});put('Text','FName'+i,[x+118,y+14,112,94],{font:head,fontSize:20,wrap:true});}
 put('Text','FGridFoot',[160,640,960,40],{fontSize:22,align:'center',color:'#ffe9a8',background:'#0b1018cc'});
 put('Text','FToast',[340,24,600,46],{font:head,fontSize:24,align:'center',color:'#16121c',background:'#ffe36ee8',radius:8});
 put('Text','FCredits',[140,60,1000,600],{fontSize:26,align:'center',wrap:true,color:'#efe6f4'});
 await write('Assets/UI/Flow.hbwidget.json',f);
}
// 4-4) 탐색 위젯 W_Explore (docs/spec/16 §1-1·§5-2) : 1인칭 방 시점·조준점·이름표·장소 띠·미니맵 / 지도(이동) / 예·아니오 / 언령 획득 / 띠 연출
{
 const e=createWidgetAsset('W_Explore');e.scaleMode='scale';e.scaleRule='fit';
 const put=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:false,...props});e.nodes.push(n);return n;};
 const svg=(name,b,w,h)=>write(`Assets/Art/ui/${name}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">${b}</svg>`);
 await svg('ex_cross','<circle cx="40" cy="40" r="16" fill="none" stroke="#ffd21f" stroke-width="4"/><circle cx="40" cy="40" r="3" fill="#ffd21f"/>',80,80);
 await svg('ex_cross_on','<circle cx="40" cy="40" r="28" fill="#ffd21f" fill-opacity=".18" stroke="#ffd21f" stroke-width="5"/><path d="M40 4v16M40 60v16M4 40h16M60 40h16" stroke="#ffd21f" stroke-width="4"/><circle cx="40" cy="40" r="5" fill="#ffd21f"/>',80,80);
 await svg('ex_label','<path d="M24 0H560L536 50H0z" fill="#ffd21f"/><path d="M30 6H548" stroke="#16121c" stroke-opacity=".35" stroke-width="2"/>',560,50);
 await svg('ex_area','<path d="M0 0H430L400 52H0z" fill="#ffd21f"/><path d="M0 52H400" stroke="#16121c" stroke-width="3"/>',430,56);
 await svg('ex_area_icon','<path d="M14 92V48h18V30h34v18h18v44z" fill="#16121c"/><path d="M48 4v18M24 14l8 12M72 14l-8 12" stroke="#ff7a1a" stroke-width="6" stroke-linecap="round"/><circle cx="48" cy="34" r="10" fill="#ff7a1a"/><path d="M22 60h12M44 60h12M66 60h12M22 76h12M44 76h12M66 76h12" stroke="#ffd21f" stroke-width="5"/>',96,96);
 await svg('ex_mini','<path d="M100 4L196 100L100 196L4 100z" fill="#0b1018" fill-opacity=".72" stroke="#ffffff" stroke-width="3"/><path d="M100 30L170 100L100 170L30 100z" fill="none" stroke="#36e3ff" stroke-opacity=".5" stroke-width="2"/>',200,200);
 await svg('ex_arrow','<path d="M4 30L40 4V56z" fill="#ffffff" fill-opacity=".55"/>',44,60);
 await svg('map_item','<path d="M16 0H520L504 54H0z" fill="#0b1018" fill-opacity=".86"/><path d="M16 1H520" stroke="#ff4fa3" stroke-width="3"/>',520,56);
 await svg('map_item_on','<path d="M16 0H520L504 54H0z" fill="#ff4fa3" fill-opacity=".92"/><path d="M16 1H520M0 53H504" stroke="#ffffff" stroke-width="3"/>',520,56);
 await svg('confirm','<path d="M30 0H720L690 200H0z" fill="#0b1018" fill-opacity=".94"/><path d="M30 2H718" stroke="#ffd21f" stroke-width="4"/><path d="M0 198H690" stroke="#ffd21f" stroke-width="2"/>',720,200);
 await svg('kget_glow','<defs><radialGradient id="g"><stop offset="0" stop-color="#fff6c8" stop-opacity=".9"/><stop offset=".6" stop-color="#ffd21f" stop-opacity=".25"/><stop offset="1" stop-color="#ffd21f" stop-opacity="0"/></radialGradient></defs><circle cx="300" cy="300" r="300" fill="url(#g)"/>'+Array.from({length:16},(_,i)=>{const a=i*Math.PI/8;return `<path d="M300 300L${300+300*Math.cos(a-.05)} ${300+300*Math.sin(a-.05)}L${300+300*Math.cos(a+.05)} ${300+300*Math.sin(a+.05)}z" fill="#fff6c8" fill-opacity=".25"/>`;}).join(''),600,600);
 await svg('kget_band','<path d="M0 0H1280V110H0z" fill="#0b1018" fill-opacity=".9"/><path d="M0 2H1280M0 108H1280" stroke="#ffd21f" stroke-width="4"/>',1280,110);
 for(const [k,t,c] of [['free','自由行動  ·  자유행동','#36e3ff'],['inv','捜査開始  ·  수사 개시','#ff2a6d'],['invend','捜査終了  ·  수사 종료','#ff2a6d'],['body','死体発見  ·  시체 발견','#d81f2a']])
  await svg('band_'+k,`<path d="M0 30L1280 0V130L0 160Z" fill="#05020a" fill-opacity=".92"/><path d="M0 30L1280 0M0 160L1280 130" stroke="${c}" stroke-width="6"/><text x="640" y="104" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-weight="900" font-size="64" fill="#ffffff" stroke="${c}" stroke-width="2" transform="rotate(-1.4 640 80)">${t}</text>`,1280,160);
 put('Image','ExBg',[-160,-90,1600,900],{texture:'',imageFit:'cover'});
 for(let i=0;i<6;i++){const n=put('Image','Fig'+i,[0,0,240,520],{texture:'',imageFit:'contain'});n.slot.alignment=[.5,1];}
 for(let i=0;i<10;i++){const n=put('Image','Spark'+i,[0,0,30,30],{texture:'Assets/Art/ui/vpoint.svg',imageFit:'contain',opacity:.0});n.slot.alignment=[.5,.5];}
 put('Image','ArL',[8,330,44,60],{texture:'Assets/Art/ui/ex_arrow.svg',imageFit:'contain'});
 {const n=put('Image','ArR',[1228,330,44,60],{texture:'Assets/Art/ui/ex_arrow.svg',imageFit:'contain',rotation:180});}
 put('Image','AreaBand',[0,20,430,56],{texture:'Assets/Art/ui/ex_area.svg',imageFit:'fill'});
 put('Image','AreaIcon',[8,4,90,90],{texture:'Assets/Art/ui/ex_area_icon.svg',imageFit:'contain'});
 put('Text','AreaName',[104,28,300,40],{font:head,fontSize:26,color:'#16121c'});
 put('Image','Mini',[1080,500,180,180],{texture:'Assets/Art/ui/ex_mini.svg',imageFit:'contain'});
 for(let i=0;i<10;i++){const n=put('Panel','MiniDot'+i,[0,0,12,12],{background:'#ffd21f',radius:6});n.slot.alignment=[.5,.5];}
 put('Text','ExHint',[24,676,700,30],{fontSize:18,color:'#ffffff'});
 put('Image','LblBand',[360,610,560,50],{texture:'Assets/Art/ui/ex_label.svg',imageFit:'fill'});
 put('Text','LblText',[390,616,500,38],{font:head,fontSize:26,align:'center',color:'#16121c'});
 {const n=put('Image','Cross',[0,0,80,80],{texture:'Assets/Art/ui/ex_cross.svg',imageFit:'contain'});n.slot.alignment=[.5,.5];}
 // 지도 : 왼쪽 지도 그림, 오른쪽 장소 목록(얼굴 아이콘)
 put('Panel','MapBack',[0,0,1280,720],{background:'#08122af2'});
 put('Image','MapImg',[34,120,640,400],{texture:'',imageFit:'cover'});put('Text','MapPlace',[34,530,640,44],{font:head,fontSize:30,color:'#ffffff'});put('Text','MapWho',[34,578,640,60],{fontSize:20,color:'#cfe8ff',wrap:true});
 put('Text','MapHead',[30,24,700,56],{font:head,fontSize:40,color:'#ff4fa3',text:'MAP'});
 put('Text','MapSub',[34,78,640,30],{fontSize:20,color:'#cfe8ff'});
 for(let i=0;i<9;i++){const y=96+i*62;put('Image','MapP'+i,[700,y,520,56],{texture:'Assets/Art/ui/map_item.svg',imageFit:'fill'});put('Text','MapT'+i,[728,y+10,300,36],{font:head,fontSize:24});
  for(let k=0;k<4;k++)put('Image',`MapF${i}_${k}`,[1040+k*44,y+6,42,42],{texture:'',imageFit:'cover',radius:21});}
 put('Text','MapHint',[700,668,560,30],{fontSize:18,color:'#ffffff',align:'right'});
 // 예·아니오
 put('Panel','CfShade',[0,0,1280,720],{background:'#05030a99'});
 put('Image','CfBox',[280,240,720,200],{texture:'Assets/Art/ui/confirm.svg',imageFit:'fill'});
 put('Text','CfText',[320,268,640,70],{font:head,fontSize:30,align:'center',wrap:true});
 put('Image','CfYesP',[380,360,220,50],{texture:'Assets/Art/ui/map_item_on.svg',imageFit:'fill'});put('Text','CfYes',[380,366,220,38],{font:head,fontSize:26,align:'center',text:'예'});
 put('Image','CfNoP',[660,360,220,50],{texture:'Assets/Art/ui/map_item.svg',imageFit:'fill'});put('Text','CfNo',[660,366,220,38],{font:head,fontSize:26,align:'center',text:'아니오'});
 // 언령 획득 : 빛 + 카드 + 이름 띠
 put('Panel','KShade',[0,0,1280,720],{background:'#05030acc'});
 {const n=put('Image','KGlow',[340,60,600,600],{texture:'Assets/Art/ui/kget_glow.svg',imageFit:'contain'});}
 put('Image','KFrame',[490,130,300,410],{texture:'Assets/Art/ui/kotodama/frame_evidence.png',imageFit:'fill'});
 put('Image','KCard',[512,196,256,256],{texture:'',imageFit:'contain'});
 put('Image','KBand',[0,560,1280,110],{texture:'Assets/Art/ui/kget_band.svg',imageFit:'fill'});
 put('Text','KTitle',[0,570,1280,48],{font:head,fontSize:38,align:'center',color:'#ffd21f'});
 put('Text','KMsg',[0,620,1280,36],{fontSize:22,align:'center',color:'#ffffff'});
 // 띠 연출 (자유행동·수사 개시·수사 종료·시체 발견)
 put('Image','Band',[0,280,1280,160],{texture:'Assets/Art/ui/band_free.svg',imageFit:'fill'});
 put('Panel','Flash',[0,0,1280,720],{background:'#d81f2acc'});
 await write('Assets/UI/Explore.hbwidget.json',e);
}
// 4-5) 래피 패드 W_Pad (V3 모노패드 배치, docs/spec/16 §5-2) : 아래 둥근 아이콘 6, 위 머리 띠(얼굴·제목·말풍선·큰 아이콘), 오른쪽 세로 띠(코인·이름)
{
 const d=createWidgetAsset('W_Pad');d.scaleMode='scale';d.scaleRule='fit';
 const put=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:false,...props});d.nodes.push(n);return n;};
 const svg=(name,b,w,h)=>write(`Assets/Art/ui/${name}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">${b}</svg>`);
 const ring=(c,inner)=>`<circle cx="70" cy="70" r="64" fill="#16121c" stroke="#ffffff" stroke-width="5"/><circle cx="70" cy="70" r="52" fill="${c}" fill-opacity=".22" stroke="${c}" stroke-width="4"/>${inner}`;
 const ICONS={
  map:['#ff2a4d','<circle cx="70" cy="70" r="30" fill="none" stroke="#ff2a4d" stroke-width="6"/><path d="M40 70h60M70 40v60M48 52c14 8 30 8 44 0M48 88c14-8 30-8 44 0" stroke="#ff2a4d" stroke-width="4" fill="none"/>'],
  bullet:['#d8d8e0','<path d="M52 98V56l18-20 18 20v42z" fill="#d8d8e0"/><path d="M52 66h36" stroke="#16121c" stroke-width="4"/>'],
  gift:['#36b6ff','<rect x="42" y="58" width="56" height="40" fill="#36b6ff"/><rect x="38" y="48" width="64" height="14" fill="#9fe0ff"/><path d="M70 48v50" stroke="#ffffff" stroke-width="6"/><path d="M70 48c-10-14-26-10-20 0M70 48c10-14 26-10 20 0" stroke="#ffffff" stroke-width="5" fill="none"/>'],
  card:['#ff2a4d','<circle cx="56" cy="52" r="9" fill="#ff2a4d"/><path d="M44 98V70q12-10 24 0v28z" fill="#ff2a4d"/><circle cx="84" cy="52" r="9" fill="#ff8fc8"/><path d="M72 98V70q12-10 24 0v28z" fill="#ff8fc8"/>'],
  rules:['#36b6ff','<path d="M40 86l30-46 30 46z" fill="none" stroke="#36b6ff" stroke-width="6"/><path d="M48 70l16 10 26-30" stroke="#ffffff" stroke-width="6" fill="none"/>'],
  option:['#b0b8c8','<circle cx="80" cy="60" r="16" fill="none" stroke="#b0b8c8" stroke-width="8" stroke-dasharray="7 5"/><path d="M44 96l30-30" stroke="#36b6ff" stroke-width="10" stroke-linecap="round"/>']};
 for(const [k,[c,inner]] of Object.entries(ICONS))await svg('pad_'+k,ring(c,inner),140,140);
 await svg('pad_head','<path d="M0 0H1060V170H0z" fill="#0b0f1a" fill-opacity=".92"/><path d="M0 168H1060" stroke="#ffffff" stroke-opacity=".3" stroke-width="2"/>',1060,170);
 await svg('pad_bubble','<path d="M18 4H540Q556 4 556 20V120Q556 136 540 136H40L18 160V20Q18 4 34 4z" fill="#ffffff" stroke="#16121c" stroke-width="4"/>',560,164);
 await svg('pad_side','<path d="M0 0H140V720H0z" fill="#ff2a4d"/><path d="M10 0V720M130 0V720" stroke="#ffffff" stroke-opacity=".5" stroke-width="2"/>',140,720);
 await svg('pad_floor','<defs><linearGradient id="f" x2="0" y2="1"><stop stop-color="#1a1030"/><stop offset="1" stop-color="#05030a"/></linearGradient></defs><rect width="1140" height="720" fill="url(#f)"/>'+Array.from({length:12},(_,i)=>`<path d="M${i*110-200} 720L${i*110+300} 300" stroke="#ffffff" stroke-opacity=".05" stroke-width="40"/>`).join(''),1140,720);
 await svg('pad_row','<path d="M14 0H720L706 40H0z" fill="#0b0f1a" fill-opacity=".86"/><path d="M14 1H720" stroke="#ffffff" stroke-opacity=".25"/>',720,42);
 await svg('pad_row_on','<path d="M14 0H720L706 40H0z" fill="#ff2a4d" fill-opacity=".9"/>',720,42);
 put('Image','PdFloor',[0,0,1140,720],{texture:'Assets/Art/ui/pad_floor.svg',imageFit:'fill'});
 put('Panel','PdTint',[0,0,1140,720],{background:'#ff2a4d22'});
 put('Image','PdHead',[40,30,1060,170],{texture:'Assets/Art/ui/pad_head.svg',imageFit:'fill'});
 put('Image','PdFace',[52,38,190,154],{texture:'',imageFit:'cover'});
 put('Text','PdTitle',[262,44,600,60],{font:head,fontSize:42,color:'#ff2a4d'});
 put('Image','PdBubble',[256,92,560,164],{texture:'Assets/Art/ui/pad_bubble.svg',imageFit:'fill'});
 put('Text','PdDesc',[290,106,500,110],{fontSize:22,color:'#16121c',wrap:true});
 put('Image','PdBig',[880,40,160,160],{texture:'',imageFit:'contain'});
 for(let i=0;i<6;i++)put('Image','PdIcon'+i,[60+i*170,470,140,140],{texture:'',imageFit:'contain'});
 put('Image','PdSide',[1140,0,140,720],{texture:'Assets/Art/ui/pad_side.svg',imageFit:'fill'});
 put('Text','PdCoins',[1150,24,120,60],{font:'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf',fontSize:22,align:'center',color:'#ffffff',wrap:true});
 put('Text','PdName',[1150,110,120,120],{font:head,fontSize:34,align:'center',color:'#ffffff',wrap:true,text:'래피\nPAD'});
 put('Text','PdSchool',[1150,240,120,80],{fontSize:14,align:'center',color:'#ffffff',wrap:true,text:'유메노쿠니\n전자 수첩'});
 put('Text','PdHint',[760,676,370,30],{fontSize:18,color:'#ffffff',align:'right'});
 // 하위 화면 : 목록(왼쪽) + 그림·제목·설명(오른쪽) / 통신부 실루엣 줄
 for(let i=0;i<12;i++){put('Image','PdRowP'+i,[60,230+i*36,560,34],{texture:'Assets/Art/ui/pad_row.svg',imageFit:'fill'});put('Text','PdRowT'+i,[84,234+i*36,520,28],{fontSize:20});}
 put('Image','PdPic',[660,220,440,260],{texture:'',imageFit:'contain'});
 put('Text','PdPicTitle',[660,488,460,36],{font:head,fontSize:28,color:'#ffffff'});
 put('Text','PdPicText',[660,528,460,140],{fontSize:19,color:'#e6f2ff',wrap:true});
 for(let i=0;i<15;i++)put('Image','PdSil'+i,[60+i*70,220,64,64],{texture:'',imageFit:'cover',radius:32});
 put('Text','PdLevel',[60,300,560,360],{fontSize:21,color:'#ffffff',wrap:true});
 put('Image','PdStand',[700,150,420,560],{texture:'',imageFit:'contain'});
 await write('Assets/UI/Pad.hbwidget.json',d);
}
{ // 브레인 드라이브·스크럼 그림 (원근 네온 도로, 차, 띠)
 await write('Assets/Art/ui/taxi_road.svg','<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"><defs><linearGradient id="sky" x2="0" y2="1"><stop stop-color="#07021a"/><stop offset=".45" stop-color="#2a0b45"/><stop offset="1" stop-color="#05020f"/></linearGradient></defs><rect width="1280" height="720" fill="url(#sky)"/>'+Array.from({length:60},(_,i)=>`<circle cx="${(i*197)%1280}" cy="${(i*71)%230}" r="${1+i%3*.6}" fill="#fff" opacity=".7"/>`).join('')+'<path d="M600 250H680L1260 720H20Z" fill="#12082a"/><path d="M600 250L20 720M680 250L1260 720" stroke="#ff4fa3" stroke-width="8"/><path d="M627 250L407 720M653 250L873 720" stroke="#36e3ff" stroke-width="2" opacity=".35"/>'+Array.from({length:10},(_,i)=>{const y=250+Math.pow(i/10,1.8)*470;return `<path d="M0 ${y}H1280" stroke="#a46bff" stroke-opacity="${.08+i*.02}"/>`;}).join('')+'</svg>');
 await write('Assets/Art/ui/taxi_car.svg','<svg xmlns="http://www.w3.org/2000/svg" width="240" height="150"><path d="M30 120V80l30-40h120l30 40v40z" fill="#ff4fa3" stroke="#fff" stroke-width="4"/><path d="M70 48h100l20 30H50z" fill="#36e3ff" opacity=".7"/><rect x="95" y="20" width="50" height="22" rx="6" fill="#ffe9a8"/><text x="120" y="37" font-size="14" text-anchor="middle" fill="#16121c" font-family="sans-serif">TAXI</text><circle cx="65" cy="122" r="18" fill="#16121c"/><circle cx="175" cy="122" r="18" fill="#16121c"/></svg>');
 await write('Assets/Art/ui/taxi_rival.svg','<svg xmlns="http://www.w3.org/2000/svg" width="160" height="110"><path d="M15 95V60l25-30h80l25 30v35z" fill="#3b2a55" stroke="#a46bff" stroke-width="4"/><rect x="30" y="68" width="22" height="10" fill="#ff2040"/><rect x="108" y="68" width="22" height="10" fill="#ff2040"/></svg>');
 await write('Assets/Art/ui/scrum_band.svg','<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="110"><path d="M0 30L1280 0V80L0 110Z" fill="#16121c" fill-opacity=".85"/><path d="M0 30L1280 0M0 110L1280 80" stroke="#36e3ff" stroke-width="4"/><text x="640" y="72" font-size="54" text-anchor="middle" fill="#fff" font-family="sans-serif" font-weight="900" transform="rotate(-1.3 640 60)">논의 스크럼 START!</text></svg>');
}

// 5) 3D 학급 재판장 장면 (docs/spec/15 §2, Source/Courtroom.hpp 와 같은 수치) + 블루프린트 (Tick → Yumeno.Update)
const R=5.5,PODIUM_INSET=.25,SPRITE=2.3,SPRITE_Y=1.25,PODIUM_W=1.7,PODIUM_H=1.45,FOV=43.6;
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
scene.objects.push(sprite('Floor',prop.floor,[0,0,0],15,15,{color:[.5,.42,.62,1]},[-90,0,0]));
for(let i=0;i<12;i++){const b=i*30*Math.PI/180;scene.objects.push(sprite('Wall'+i,prop.wall,[13*Math.sin(b),3.4,13*Math.cos(b)],7.2,9.6,{color:[.42,.32,.52,1]},[0,i*30+180,0]));}
// 왕좌는 증언대 머리 위로 높이 (V3 : 모노쿠마는 재판장을 내려다본다)
scene.objects.push(sprite('Throne',prop.throne,[0,4.2,-(R+3.4)],4,4,{billboard:true,color:[.7,.6,.75,1]}));
scene.objects.push(sprite('Host',`Assets/Art/sprites/lappy/lappy_L01.webp`,[0,4.6,-(R+2.4)],1.6,1.6,{billboard:true,sortingOrder:10})); // 왕좌보다 1m 앞
SEATS.forEach((slug,i)=>{
 const a=i*22.5*Math.PI/180;
 scene.objects.push(sprite('Seat'+i,`Assets/Art/sprites/${slug}/${slug}_C01.webp`,[R*Math.sin(a),SPRITE_Y,R*Math.cos(a)],SPRITE,SPRITE,{billboard:true}));
 scene.objects.push(sprite('Podium'+i,prop.podium,[(R-PODIUM_INSET)*Math.sin(a),PODIUM_H/2,(R-PODIUM_INSET)*Math.cos(a)],PODIUM_W,PODIUM_H,{billboard:true,color:[.72,.66,.85,1]}));
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
