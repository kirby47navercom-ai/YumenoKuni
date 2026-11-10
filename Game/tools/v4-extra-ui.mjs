import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {emitGalleryMaterial} from './v4-gallery-material.mjs';
import {sourceRows,sourceSvg} from './v3-source-svg.mjs';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../engineCreate/prototype/ui-assets.js';
import {validGameJson} from '../engineCreate/prototype/game-json.js';
import {emitV4DataPacks} from './v4-data-pack.mjs';
const hash=s=>createHash('sha256').update(s).digest('hex').slice(0,16);
const bucket=(s,n)=>{let h=2166136261;for(const b of Buffer.from(s)){h^=b;h=Math.imul(h,16777619)>>>0;}return h%n;};
export async function emitExtraV4({repo,root,write:output,body,head}){
 const write=async (file,data)=>{if(data&&typeof data==='object'&&(!validGameJson(data)||Buffer.byteLength(JSON.stringify(data))>262144))throw Error('Extra native JSON bounds: '+file);await output(file,data);};
 const read=async p=>JSON.parse(await fs.readFile(path.join(repo,p),'utf8'));
 const make=name=>{let w=createWidgetAsset(name);w.scaleMode='scale';w.scaleRule='fit';return w;};
 const add=(w,type,id,r,props={})=>{const n=createWidgetNode(type,id,'root');n.name=id;n.slot.offset=r;Object.assign(n.properties,{font:body,fontSize:26,text:'',color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:true,...props});w.nodes.push(n);};
 const machine=await read('docs/analysis/v3_rebuild/gift_machine_remaining_contract.json'),geo=machine.UI_reference.geometry;
 const find=(family,name)=>{const row=geo[family].leaves.find(l=>l.path===name);if(!row)throw Error('Missing machine source carrier '+name);return row.rect1280;};
 const machineBase='Assets/Art/ui/v3/machine_source/',effectAdapters=await read('ui/v4/machine_source/manifest.json');
 const sourcePart=async(name,rows,bounds=[0,0,1280,720])=>{if(!rows.length)throw Error('Missing original machine carrier '+name);const file=machineBase+name+'.svg';rows=structuredClone(rows);if(name!=='background')for(const row of rows)if(effectAdapters[row.texture])row.texture=effectAdapters[row.texture].file;await write(file,await sourceSvg(rows,{bounds}));return file;};
 const originalMachine=await sourceRows('m_machine_US','fl_wait_1'),right=await sourceRows('m_right'),left=await sourceRows('m_left_US'),result=await sourceRows('m_get_US','fl_wait','machine_result_source');
 const w=make('MachineV4');
 const srcImage=async(id,name,rows,rect=[0,0,1280,720],visible=true)=>add(w,'Image',id,rect,{texture:await sourcePart(name,rows,rect),imageFit:'fill',visible});
 await srcImage('McBackground','background',await sourceRows('m_bg'));
 await srcImage('McRightChrome','right',right.filter(r=>!r.path.startsWith('p_shoji/p_shoji_')&&!r.path.startsWith('p_bet/')&&!r.path.startsWith('p_yazirusi_')));
 await srcImage('McLeftChrome','left',left.filter(r=>r.path==='i_base/1'||r.path==='23'));
 await srcImage('McBody','body',originalMachine.filter(r=>!r.path.startsWith('i_rever/')));
 const handle=find('machine_body_normal_wait','i_rever/d1');await srcImage('McHandle','handle',originalMachine.filter(r=>r.path.startsWith('i_rever/')),handle);
 for(let d=0;d<3;d++){add(w,'Text','McWallet'+d,find('right_amount_wallet',`p_shoji/p_shoji_${d}/d1`),{fontSize:21.84446,align:'center',color:'#ffffff'});add(w,'Text','McBet'+d,find('right_amount_wallet',`p_bet/p_bet_${d}/d1`),{fontSize:27.30599,align:'center',color:'#171421'});}
 add(w,'Text','McBetLabel',find('right_amount_wallet','p_bet_text_00/_f_m_bet_text_00'),{text:'투입 코인',color:'#171421',fontSize:26.66667});
 add(w,'Text','McWalletLabel',[935,44,180,30],{text:'보유 코인',fontSize:20,color:'#ffffff'});
 for(let d=0;d<5;d++)add(w,'Text','McRepeat'+d,find('left_duplicate_percentage',`p_juhuku_number/p_juhuku_number_${d}/d1`),{fontSize:27.73307,color:'#171421',align:'center'});
 await srcImage('McPercent','percent',left.filter(r=>r.path==='p_juhuku_number/i_par/1'),find('left_duplicate_percentage','p_juhuku_number/i_par/d1'));
 await srcImage('McDot','decimal_dot',left.filter(r=>r.path==='p_juhuku_number/i_num_parts_dot/1'),find('left_duplicate_percentage','p_juhuku_number/i_num_parts_dot/d1'));
 add(w,'Text','McRepeatLabel',[180,45,260,30],{text:'중복률',fontSize:21,color:'#ffffff'});
 const up=find('right_amount_wallet','p_yazirusi_up/d1'),down=find('right_amount_wallet','p_yazirusi_down/d1');
 await srcImage('McUp','up',right.filter(r=>r.path==='p_yazirusi_up/1'),up);await srcImage('McDown','down',right.filter(r=>r.path==='p_yazirusi_down/1'),down);
 await srcImage('McResultShade','result',result.filter(r=>!['i_black/1','p_present_icon/1','p_new/i_new/1','p_pre_base/1','_a_pre_ef/i_pre_ef/1','_a_pre_ef/i_pre_ef_2/1'].includes(r.path)),[0,0,1280,720],false);
 const caption=await read('ui/v4/machine_source/localized-caption.json');add(w,'Text','McResultCaption',caption.captionRect1280,{text:caption.localizedText,font:head,fontSize:caption.fontHeight1280,align:'center',color:'#ef7f80',outlineColor:'#ffffff',outlineWidth:3,visible:false});
 await srcImage('McPrizePlate','prize_plate',result.filter(r=>r.path==='i_black/1'),find('result_item','i_black/d1'),false);
 add(w,'Image','McPrize',find('result_item','p_present_icon/d1'),{imageFit:'contain',visible:false});add(w,'Text','McPrizeName',find('result_item','p_present_name/_f_present_name'),{align:'center',fontSize:26.66667,visible:false});
 await srcImage('McNew','new',result.filter(r=>r.path==='p_new/i_new/1'),[0,0,1280,720],false);
 await srcImage('McLucky','lucky',(await sourceRows('m_lucky_US','fl_in')).filter(r=>r.path==='p_lucky/i_lucky_base/1'),[0,0,1280,720],false);
 add(w,'Text','McHint',[32,672,1216,38],{fontSize:18,color:'#ffffff',align:'center'});
 await srcImage('McHelpShade','help_window',(await sourceRows('common_window','fl_wait_2_2','pad_system_source')).filter(r=>['i_beta/1','p_color_01/1','p_color_00/1','i_base/1'].includes(r.path)),[0,0,1280,720],false);add(w,'Text','McHelp',[155,145,970,430],{fontSize:29,wrap:true,text:'코인을 넣고 손잡이를 돌리면 선물을 얻을 수 있어요.\n투입량을 늘리면 같은 선물이 나올 확률이 낮아져요.\n운이 좋으면 코인 소모 없이 한 번 더 돌아가요.\n\nW/S 투입량 · Enter 결정 · Enter를 누른 채 W/S 10개씩\nF1 패드 · F3 도움말 · Esc 돌아가기\n\nEnter / Esc  닫기',visible:false});
 if(!validWidgetAsset(w))throw Error('Invalid machine widget');await write('Assets/UI/MachineV4.hbwidget.json',w);await write('Assets/Data/v4_story/machine_layout.json',{handle,up,down,scope:'Original seven machine families plus narrowly imported m_get_US bitmap/affine chrome. Own Korean live counters, prizes and input/backend preserved. Original GPU additive shader and timeline/handle-phase parity remain unclaimed.'});
 const source=await read('docs/analysis/v3_rebuild/gallery_remaining_contract.json');
 const bounds=l=>{const r=l.text_lrtb||l.shape_rects?.[0]?.slice(1);if(!r)return null;let [x,b,y,d]=r;const m=l.svg_matrix,pts=[[x,y],[b,y],[b,d],[x,d]].map(([x,y])=>[(m[0]*x+m[2]*y+m[4])*2/3,(m[1]*x+m[3]*y+m[5])*2/3]);let xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]);return [Math.min(...xs),Math.min(...ys),Math.max(...xs)-Math.min(...xs),Math.max(...ys)-Math.min(...ys)];};
 const family=name=>source.geometry.find(g=>g.family===name).first_local_child_leaves;
 const textRect=(f,p)=>{const l=family(f).find(l=>l.path===p);if(!l)throw Error('Missing gallery text carrier '+p);return bounds(l);};
 const material=await emitGalleryMaterial({repo,write,source});
 const gal=make('GalleryV4');add(gal,'Image','GaShade',[0,0,1280,720],{texture:material.backgrounds.top,imageFit:'fill'});
 add(gal,'Image','GaCursor',[0,0,1280,720],{texture:material.cursors.top[0],imageFit:'fill'});
 add(gal,'Image','GaTitle',[0,0,1280,720],{texture:material.title,imageFit:'fill'});
 const categories=source.categories.filter(c=>c.included);const top=[];for(let i=0;i<categories.length;i++){let c=categories[i],r=textRect('g_topmenu_US',`${c.caption_root}/_f_extra_main_on_${String(c.native_top_index).padStart(3,'0')}`);top.push(r);add(gal,'Text','GaTop'+i,r,{fontSize:29.33333,color:'#666666',visible:false});}
 const rows=[],prices=[];for(let i=0;i<11;i++){let r=textRect('g_menu_US',`p_extra_on_${String(i).padStart(3,'0')}/_f_extra_on_${String(i).padStart(3,'0')}`);rows.push(r);add(gal,'Text','GaRow'+i,r,{fontSize:29.33333,color:'#666666',visible:false});const digits=family('g_menu_US').filter(l=>l.path.startsWith('p_cost_'+String(i).padStart(3,'0')+'/')).map(bounds);if(digits.length!==2)throw Error('Gallery source cost digits '+i);const left=Math.min(...digits.map(r=>r[0])),topY=Math.min(...digits.map(r=>r[1]));let cost=[left,topY,Math.max(...digits.map(r=>r[0]+r[2]))-left,Math.max(...digits.map(r=>r[1]+r[3]))-topY];prices.push(cost);add(gal,'Text','GaPrice'+i,cost,{fontSize:21.33333,color:'#666666',align:'right',visible:false});}
 for(let i=0;i<categories.length;i++)add(gal,'Image','GaTopNew'+i,[0,0,1280,720],{texture:material.badgeTextures.top[categories[i].native_top_index],imageFit:'fill',visible:false});
 for(let i=0;i<11;i++){add(gal,'Image','GaRowNew'+i,[0,0,1280,720],{texture:material.badgeTextures.list[i],imageFit:'fill',visible:false});add(gal,'Image','GaPlaying'+i,[0,0,1280,720],{texture:material.playing[i],imageFit:'fill',visible:false});}
 for(let i=0;i<3;i++)add(gal,'Image','GaCoin'+i,[0,0,1280,720],{texture:material.coinDigits[i][0],imageFit:'fill',visible:false});
 add(gal,'Image','GaPreview',[778,173,444,310],{imageFit:'contain',visible:false});add(gal,'Text','GaStatus',[778,500,444,100],{fontSize:24,wrap:true,color:'#17141b'});add(gal,'Text','GaHint',[40,674,1200,34],{fontSize:18,color:'#ffffff'});add(gal,'Image','GaViewer',[0,0,1280,720],{imageFit:'contain',visible:false});
 if(!validWidgetAsset(gal))throw Error('Invalid gallery widget');await write('Assets/UI/GalleryV4.hbwidget.json',gal);await write('Assets/Data/v4_story/gallery_layout.json',{top,rows,prices,categories,material,scope:'Normal-stop source text/carrier positions and authored black/gray font44*2/3; explicit own material reconstruction, provided JP title sign locale reuse. No Casino; MonoMono retained.'});
 // Curate explicit authored presentation ranges, not every file under art/audio.
 const presentation=await read('data/presentation/v4_scenes.json'),growth=await read('tools/v4_growth_contract.json'),cues=await read('audio/cues.json');
 const records={},order={event:[],movie:[],artwork:[],bgm:[],intimacy:[]},maps=Array.from({length:128},()=>({}));
 const put=(id,row)=>{if(records[id])return;records[id]={id,...row};order[row.category].push(id);};
 const asset=raw=>'Assets/Art/v4_story/'+hash(raw)+path.extname(raw),imageID=raw=>'image:'+hash(raw);
 for(let i=0;i<presentation.cgRanges.length;i++){let range=presentation.cgRanges[i],id=imageID(range.image.replaceAll('\\','/'));put(id,{category:'artwork',label:'일러스트 '+String(i+1).padStart(3,'0'),price:5,image:asset(range.image.replaceAll('\\','/'))});}
 for(const [cue,row]of Object.entries(cues.bgm))put('bgm:'+cue,{category:'bgm',label:row.use||cue,price:5,cue});
 const events=presentation.sceneRanges.map((r,i)=>{const id='event:'+hash(r.source.file+':'+r.startLine+':'+r.endLineExclusive);put(id,{category:'event',label:'장면 기록 '+String(i+1).padStart(3,'0'),price:3,space:r.space,nodes:[]});return {...r,id};});
 for(const file of await fs.readdir(path.join(repo,'data/v4_story/chapters'))){if(!file.endsWith('.json'))continue;let graph=await read('data/v4_story/chapters/'+file);for(const node of Object.values(graph.nodes)){if(node.type!=='say'||!node.source)continue;let src=node.source;const range=events.find(r=>r.source.file===src.file&&src.line>=r.startLine&&src.line<r.endLineExclusive),ids=[];if(range){records[range.id].nodes.push({id:node.id,line:src.line});ids.push(range.id);}for(const r of presentation.cgRanges)if(r.source.file===src.file&&src.line>=r.startLine&&src.line<r.endLineExclusive)ids.push(imageID(r.image.replaceAll('\\','/')));let music=(node.music||'').split('>').find(x=>x.startsWith('bgm_'));if(music&&records['bgm:'+music])ids.push('bgm:'+music);if(ids.length)maps[bucket(node.id,128)][node.id]=[...new Set(ids)];}}
 for(const row of Object.values(records))if(row.nodes){row.nodes.sort((a,b)=>a.line-b.line||a.id.localeCompare(b.id));row.nodes=[...new Set(row.nodes.map(n=>n.id))];}
 for(const [key,row]of Object.entries(growth.entries)){let nodes=[];for(const flag of row.completionFlags){const prefix=flag.split(':')[1],graph=await read('data/v4_story/freetime/'+prefix+'.json');for(const n of Object.values(graph.nodes))if(n.type==='say')nodes.push({id:n.id,line:n.source?.line||0});}nodes.sort((a,b)=>a.line-b.line||a.id.localeCompare(b.id));put('fte:'+key,{category:'intimacy',label:'자유행동 기록 · '+key,price:0,actor:row.actor,episode:row.episode,completion:key,nodes:[...new Set(nodes.map(n=>n.id))]});}
 const recordBuckets=Array.from({length:64},()=>({}));for(const [id,row]of Object.entries(records))recordBuckets[bucket(id,64)][id]=row;
 await emitV4DataPacks({repo,write,family:'gallery_records',shards:recordBuckets.map(records=>({records}))});
 await emitV4DataPacks({repo,write,family:'gallery_map',shards:maps.map(nodes=>({nodes}))});
 await write('Assets/Data/v4_story/gallery_catalog.json',{order,scope:'Own149 explicit scene ranges, own CG presentation bindings, imported BGM cues and actual completed FTE records. No loose-file unlocks. Own eventprice3/artwork5/BGM5; no fake movie rows when no authored movie exists. Event/FTE viewer replays only saved-read lines without route/reward mutation.'});
 return {machine:w.nodes.length,gallery:gal.nodes.length,records:Object.keys(records).length,order:Object.fromEntries(Object.entries(order).map(([k,v])=>[k,v.length]))};
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const repo=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),root=path.join(repo,'Game');
 const write=async(file,data)=>{const target=path.join(root,file);await fs.mkdir(path.dirname(target),{recursive:true});const temporary=target+'.tmp';await fs.writeFile(temporary,typeof data==='string'?data:JSON.stringify(data,null,1)+'\n');await fs.rename(temporary,target);};
 console.log(JSON.stringify(await emitExtraV4({repo,root,write,body:'Assets/Fonts/pretendard/Pretendard-Medium.otf',head:'Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf'})));
}
