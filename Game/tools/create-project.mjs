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
// 진행 순서 : 프롤로그부터 (장이 늘면 여기 추가)
await write('Assets/Data/story.json',{files:['10']});

// 2) 교칙 : docs/spec/11 §2·§3 표
const rulesDoc=await fs.readFile(path.join(repo,'docs/spec/11_래피패드_교칙.md'),'utf8');
const rules=[...rulesDoc.matchAll(/^\| (교칙 \d+|[1-6]장) \| ([^|]+) \|/gm)].map(m=>({no:m[1],text:m[2].trim().replace(/\*\*/g,'')}));
await write('Assets/Data/rules.json',{rules});

// 3) 그림 : 스프라이트(WebP)·UI·글꼴 복사
for(const slug of await fs.readdir(path.join(repo,'art/sprites'))){
 for(const f of await fs.readdir(path.join(repo,'art/sprites',slug)))if(f.endsWith('.webp')&&!f.startsWith('sheet'))await copy(`art/sprites/${slug}/${f}`,`Assets/Art/sprites/${slug}/${f}`);
}
for(const f of ['dialog/frame.png','dialog/nameplate.png'])await copy('ui/'+f,'Assets/Art/ui/'+path.basename(f));
await copy('fonts/pretendard/Pretendard-Medium.otf','Assets/Fonts/Pretendard-Medium.otf');
await copy('fonts/pretendard/LICENSE.txt','Assets/Fonts/Pretendard-LICENSE.txt');
await copy('fonts/blackhansans/BlackHanSans-Regular.ttf','Assets/Fonts/BlackHanSans-Regular.ttf');
await copy('fonts/blackhansans/OFL.txt','Assets/Fonts/BlackHanSans-OFL.txt');

// 4) UI 위젯 (1280×720 기준, V3식 대화창)
const body='Assets/Fonts/Pretendard-Medium.otf',head='Assets/Fonts/BlackHanSans-Regular.ttf';
const w=createWidgetAsset('W_Yumeno');w.scaleMode='scale';w.scaleRule='fit';
const add=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#f4f0f6',background:'#00000000',padding:0,focusable:false,...props});w.nodes.push(n);return n;};
add('Panel','Backdrop',[0,0,1280,720],{background:'#17121f'});
add('Image','Portrait',[290,0,700,700],{texture:'',imageFit:'contain',visible:false});
add('Image','DialogFrame',[80,512,1120,170],{texture:'Assets/Art/ui/frame.png',imageFit:'fill'});
add('Image','Nameplate',[104,486,220,44],{texture:'Assets/Art/ui/nameplate.png',imageFit:'fill'});
add('Text','Name',[118,490,196,36],{font:head,fontSize:26,align:'center',color:'#ffffff'});
add('Text','Body',[136,548,1010,120],{fontSize:25,wrap:true});
add('Text','Hint',[760,690,500,26],{text:'Enter·클릭 다음   Ctrl 빨리감기   Tab 래피 패드',fontSize:16,color:'#b9a9c6',align:'right'});
add('Text','SceneTitle',[24,16,800,30],{fontSize:18,color:'#d9b8e8'});
add('Panel','Title',[0,0,1280,720],{background:'#0f0b16'});
add('Text','TitleLogo',[0,220,1280,110],{text:'夢の国  유메노쿠니',font:head,fontSize:84,align:'center',color:'#ff8fc8'},'Title');
add('Text','TitleSub',[0,350,1280,40],{text:'Enter  새로 시작        C  이어하기',fontSize:26,align:'center',color:'#efe6f4'},'Title');
add('Panel','Pad',[0,0,1280,720],{background:'#120d1af2',visible:false});
add('Text','PadHead',[120,48,1040,60],{text:'래피 패드  ·  교칙',font:head,fontSize:40,color:'#ff8fc8'},'Pad');
add('Text','PadBody',[120,120,1040,560],{fontSize:21,wrap:true},'Pad');
add('Text','PadHint',[120,676,1040,30],{text:'Tab 닫기',fontSize:18,color:'#b9a9c6'},'Pad');
await write('Assets/UI/Main.hbwidget.json',w);

// 5) 장면 + 블루프린트 (Tick → Yumeno.Update)
const scene=makeStarterScene('유메노쿠니','2d');scene.objects=[];Object.assign(scene.environment,{skyEnabled:false,sunEnabled:false,groundColor:'#17121f'});
scene.objects.push({id:'Camera',name:'카메라',kind:'camera',position:[0,0,12],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[makeSceneComponent('Camera',{projection:'orthographic',orthographicSize:4.5,main:true,near:.1,far:200})]});
const header=await fs.readFile(path.join(root,'Source/Yumeno.h'),'utf8'),source=await fs.readFile(path.join(root,'Source/Yumeno.cpp'),'utf8');
const bp=createAsset('blueprint','BP_Yumeno');bp.settings.parentClass='Yumeno';bp.native={...parseNativeHeader(header),header,source,headerPath:'Source/Yumeno.h',sourcePath:'Source/Yumeno.cpp'};bp.nodes=[];bp.edges=[];
const tick=makeNode('tick',100,180),call=makeNode('nativeCall',400,180);call.nativeId='Yumeno.Update';bp.nodes.push(tick,call);
for(const [pin,input] of [['then','exec'],['delta','delta']]){const r=connect(bp,{node:tick.id,pin},{node:call.id,pin:input});if(!r.ok)throw Error(r.message);}
scene.objects.push({id:'Driver',name:'게임 진행',kind:'empty',position:[0,0,0],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[],blueprintAsset:'Assets/Blueprints/BP_Yumeno.hbblueprint.json'});
await write('Assets/Blueprints/BP_Yumeno.hbblueprint.json',bp);await write('Assets/Scenes/Main.hbscene.json',scene);

let id=randomUUID();try{id=JSON.parse(await fs.readFile(path.join(root,'YumenoKuni.hbproject'),'utf8')).id;}catch(e){if(e.code!=='ENOENT')throw e;}
await write('YumenoKuni.hbproject',{version:1,engine:'HBEngine',engineVersion:'0.1.0',id,name:'YumenoKuni',startupScene:'Assets/Scenes/Main.hbscene.json',startupBlueprint:'Assets/Blueprints/BP_Yumeno.hbblueprint.json'});
console.log(JSON.stringify({scenes:sceneFiles.length,rules:rules.length,widgets:w.nodes.length}));
