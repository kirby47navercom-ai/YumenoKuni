import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {createWidgetAsset,createWidgetNode,validWidgetAsset} from '../../../engineCreate/prototype/ui-assets.js';
import {emitVoteTally} from './v4-vote-tally.mjs';
import {emitVoteVerdict} from './v4-vote-verdict.mjs';
import {centerInputFrame} from './v4-trial-input-motion-ui.mjs';

// Observed V3 voting input: compact 4x4 portraits on the left, selected full
// figure and name on the right, countdown and separate commit at the bottom.
export async function emitVoteUI({write,body,head}){
 const base='Assets/Art/ui/vote_v4/';
 const svg=body=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" preserveAspectRatio="none">${body}</svg>`;
 const repo=path.resolve(import.meta.dirname,'../..'),source=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/trial_inputs_source/manifest.json'),'utf8'));
 const image=async name=>'data:image/png;base64,'+(await fs.readFile(path.join(repo,source.records[name].file))).toString('base64');
 const raster=async(name,target,w,h)=>write(base+target,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><image href="${await image(name)}" width="${w}" height="${h}" preserveAspectRatio="none"/></svg>`);
 await write(base+'stage.svg',svg(`<image href="${await image('vote_stage')}" width="1280" height="720"/><image href="${await image('vote_frame')}" width="1280" height="720"/>`));
 for(const on of [false,true])await raster('vote_portrait_'+(on?'on':'off'),'portrait_'+(on?'on':'off')+'.svg',110,110);
 await raster('vote_name','name.svg',570,76);await raster('vote_commit','commit.svg',180,64);
 await raster('vote_title','title.svg',433.333333,150);await raster('vote_time','time.svg',1280,720);
 // Public original voting footage gBNt-hmEBKA at1:30 shows two columns of
 // eight faces and one discrete red mark per ballot, not16 stacked rows.
 for(let count=0;count<=16;count++)await write(base+`count_${count}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 24">${Array.from({length:count},(_,i)=>`<path d="M${i*8+1} 3h5v18h-5Z" fill="#ef234b"/><path d="M${i*8+2} 4v14" stroke="#ff9caa"/>`).join('')}</svg>`);
 await write(base+'result_rows.svg',svg('')); // Original stage already owns the tally backdrop; no invented row cards.
 const widget=createWidgetAsset('VoteV4');widget.scaleMode='scale';widget.scaleRule='fit';
 const add=(type,id,rect,properties={},z=0)=>{const n=createWidgetNode(type,id,'root');n.name=id;n.slot.offset=rect;n.slot.zIndex=z;Object.assign(n.properties,{visible:false,focusable:false,text:'',padding:0,background:'#00000000',font:body,fontSize:22,color:'#ffffff',wrap:false,...properties});widget.nodes.push(n);};
 add('Image','VoteBackdrop',[0,0,1280,720],{texture:base+'stage.svg',imageFit:'fill'});
 add('Image','VoteResultRows',[0,0,1280,720],{texture:base+'result_rows.svg',imageFit:'fill'},4);
 add('Image','VotePortrait',[600,48,620,620],{texture:'',imageFit:'contain'},1);
 for(let i=0;i<16;i++){
  const x=104+(i%4)*116,y=157+Math.floor(i/4)*116;
  add('Image','VoteP'+i,[x,y,110,110],{texture:base+'portrait_off.svg',imageFit:'fill'},3);
  add('Image','VoteF'+i,[x+7,y+7,96,96],{texture:'',imageFit:'contain'},4);
 }
 add('Image','VoteNamePlate',[633,548,570,76],{texture:base+'name.svg',imageFit:'fill'},5);
 add('Text','VoteName',[684,572,480,42],{font:head,fontSize:31,align:'center'},6);
 add('Image','VoteTitleArt',[423.333333,2.666667,433.333333,150],{texture:base+'title.svg',imageFit:'fill'},7);
 add('Image','VoteTimeArt',[0,0,1280,720],{texture:base+'time.svg',imageFit:'fill'},6);
 add('Text','VoteTitle',[405,38,470,76],{font:head,fontSize:48,text:'VOTING TIME',align:'center',color:'#ffda67'},7);
 add('Text','VoteTimer',[475,642,350,52],{font:head,fontSize:36,align:'center',color:'#ffe16f'},7);
 add('Image','VoteCommit',[970,632,180,64],{texture:base+'commit.svg',imageFit:'fill'},7);
 add('Text','VoteCommitText',[997,644,125,38],{font:head,fontSize:27,text:'투 표',align:'center',color:'#b60c30'},8);
 add('Text','VoteGuide',[105,685,430,25],{fontSize:17,text:'W/A/S/D 선택 · Enter 투표'},7);
 for(let i=0;i<16;i++){
  const x=91+Math.floor(i/8)*306,y=145+(i%8)*58;
  add('Image','VoteRF'+i,[x,y-3,34,34],{texture:'',imageFit:'contain'},5);
  add('Text','VoteRN'+i,[x+40,y,104,28],{font:head,fontSize:17,color:'#e6d1a4'},6);
  add('Image','VoteRB'+i,[x+148,y+2,128,24],{texture:base+'count_0.svg',imageFit:'fill'},6);
  add('Text','VoteRC'+i,[x+148,y+3,128,24],{fontSize:17},6);
 }
 if(!validWidgetAsset(widget))throw Error('Invalid vote widget');
 await write('Assets/UI/Vote.hbwidget.json',widget);return widget;
}

// Run AFTER emitTrialInputMotionUI. It deliberately owns the final voting
// plane, so that the generic motion overlay cannot restore fullscreen local
// marquee/timer textures or move the own portrait outside the television.
export async function finalizeVoteTVUI({repo,write,read}){
 const meta=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/vote_tv_source/manifest.json'),'utf8')),base='Assets/Art/ui/vote_tv_source/';
 meta.screen=[0,0,1280,720];meta.scale=[1,1];
 for(const [name,row]of Object.entries(meta.records))await write(base+name+'.png',await fs.readFile(path.join(repo,row.file)));
 const vote=await read('Assets/UI/Vote.hbwidget.json'),bank=await read('Assets/Data/v4_story/trial_input_motion.json');
 const cardRect=([x,y,w,h])=>[x,40+(y-40)*.93,w,h*.93];
 bank.voteCards=bank.voteCards.map(cardRect);
 const {createCanvas,loadImage,GlobalFonts}=createRequire(path.join(repo,'../engineCreate/package.json'))('@napi-rs/canvas');
 // Eye midpoint and chin height measured on each source at 220×220.
 // Keep the entire pose proportional and pin facial scale independently of padding and props.
 const landmarks={
  ai:[101,94,116],akari:[129,98,126],haruka:[110,99,113],kaede:[105,94,107],
  ken:[128,81,95],koto:[110,91,108],mio:[96,97,121],nana:[110,70,98],
  rei:[93,63,86],riku:[118,103,119],rin:[103,102,122],satsuki:[103,78,108],
  sho:[118,76,95],sora:[112,98,118],taiga:[108,90,103],yuu:[110,94,108],
 };
 const [, ,width,height]=meta.portrait;
 for(const who of Object.keys(meta.portraits)){
  const texture=base+'profile_'+who+'.png';
  const [eyeX,eyeY,chinY]=landmarks[who];
  const image=await loadImage(await fs.readFile(path.join(repo,'art/character_delivery_v4/portraits',who+'.webp')));
  const scale=68/(chinY-eyeY);
  const canvas=createCanvas(width*2,height*2),ctx=canvas.getContext('2d');
  ctx.scale(2,2);
  ctx.drawImage(image,295-eyeX*scale,310-eyeY*scale,220*scale,220*scale);
  await write(texture,canvas.toBuffer('image/png'));
  meta.portraits[who]=texture;
 }
 meta.tally=await emitVoteTally({repo,write,base,createCanvas,loadImage});
 const sx=meta.scale[0],sy=meta.scale[1],map=r=>[meta.screen[0]+r[0]*sx,meta.screen[1]+r[1]*sy,r[2]*sx,r[3]*sy];
 const set=(id,rect,props,z)=>{let n=vote.nodes.find(n=>n.id===id);if(!n){n=createWidgetNode('Image',id,'root');vote.nodes.push(n);}n.name=id;n.slot.offset=rect;n.slot.zIndex=z;Object.assign(n.properties,{visible:false,focusable:false,padding:0,background:'#00000000',imageFit:'fill',...props});return n;};
 set('VoteBackdrop',[0,0,1280,720],{texture:base+'black.svg'},0);await write(base+'black.svg','<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"><rect width="1280" height="720" fill="black"/></svg>');
 set('VotePortrait',map(meta.portrait),{imageFit:'contain'},1);
 set('VoteNamePlate',meta.screen,{texture:bank.voteInputName},60);
 set('VoteName',map(meta.name),{font:'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf',fontSize:36*sx,rotation:meta.nameRotation,align:'left'},61);
 set('VoteTitleArt',map(meta.title),{texture:base+'title.png'},70);
 set('VoteTimeArt',map(meta.timerPlate),{texture:base+'timer_plate.png'},90);
 set('VoteTimerObi',map(meta.timerObi),{texture:base+'timer_obi.png'},62);
 set('VoteCommit',map(meta.commit),{texture:base+'commit.png'},95);
 set('VoteGuide',map([36,680,760,30]),{fontSize:17*sx,color:'#ffffff'},98);
 set('VoteTitle',map([405,38,470,76]),{fontSize:42*sx},72);
 const monitorBase='Assets/Art/ui/vote_tv_source/';
 await write(monitorBase+'monitor.svg',`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
 <defs><linearGradient id="metal" x2="0" y2="1"><stop stop-color="#647884"/><stop offset=".24" stop-color="#31434e"/><stop offset=".71" stop-color="#566673"/><stop offset="1" stop-color="#23303b"/></linearGradient><radialGradient id="speaker"><stop stop-color="#384753"/><stop offset="1" stop-color="#0b141b"/></radialGradient><pattern id="grain" width="3" height="4" patternUnits="userSpaceOnUse"><path d="M0 1h3" stroke="#a8c4ce" opacity=".14"/></pattern></defs>
 <path d="M16 105H1264L1280 720H0Z M129 143H1151V718H129Z" fill="#111922" fill-rule="evenodd"/><path d="M29 113H1251L1271 719H9Z M129 143H1151V718H129Z" fill="url(#metal)" fill-rule="evenodd"/>
 <path d="M29 113H1251L1271 719H9Z M129 143H1151V718H129Z" fill="url(#grain)" fill-rule="evenodd"/>
 <path d="M129 143H1151V718H129Z" stroke="#0c1318" stroke-width="10" fill="none"/>
 ${[73,1207].flatMap(x=>[[324,11],[410,35],[509,39]].map(([y,r])=>`<ellipse cx="${x}" cy="${y}" rx="${r}" ry="${r*.85}" fill="url(#speaker)" stroke="#16222a" stroke-width="5"/>`)).join('')}
 </svg>`);
 const slate=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/trial_inputs_motion/layout.json'),'utf8')).t_tosen_bg_US.frames[52];
 const sourceBackground=await fs.readFile(path.join(repo,'Game',bank.voteResultBack));
 const resultBackground=monitorBase+'monitor_tally.svg';
 await write(resultBackground,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"><path d="M0 0h1280v720H0Z" fill="#08090b"/><image width="1280" height="720" href="data:image/png;base64,${sourceBackground.toString('base64')}"/></svg>`);
 bank.voteResultBack=resultBackground;
 const layers=slate.filter(r=>r.texture&&/bg_rd|kuro_tx|tosen_tx/.test(r.resource));
 const slateImages=await Promise.all(layers.map(async r=>{
  const [x,y,w,h]=r.rect;
  const bytes=await fs.readFile(path.join(repo,r.texture));
  return `<image x="${x+640}" y="${y+360}" width="${w}" height="${h}" opacity="${r.opacity}" href="data:image/png;base64,${bytes.toString('base64')}"/>`;
 }));
 await write(monitorBase+'monitor_results.svg',`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"><rect width="1280" height="720" fill="#080200"/>${slateImages.join('')}</svg>`);
 set('VoteTVBezel',[0,0,1280,720],{texture:monitorBase+'monitor.svg'},900);
 set('VoteMonitorBlack',[129,143,1022,575],{texture:base+'black.svg'},890);
 set('VoteMonitorSlate',[129,143,1022,575],{texture:monitorBase+'monitor_results.svg'},895);
 const motion=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/trial_inputs_motion/manifest.json'),'utf8'));
 const deadName=path.basename(bank.voteDead);
 const deadFile=Object.values(motion.rasters).find(row=>path.basename(row.file)===deadName)?.file||motion.copies[deadName];
 if(!deadFile)throw Error('Missing original vote exclusion mark');
 const dead=await fs.readFile(path.join(repo,deadFile));
 for(let i=0;i<16;i++){
  const rect=map(bank.voteCards[i]),points=bank.cardPolygons[i].map(([x,y])=>[x*256,y*256]);
  const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
  const x=Math.min(...xs),y=Math.min(...ys),w=Math.max(...xs)-x,h=Math.max(...ys)-y;
  const texture=base+'dead_'+i+'.svg';
  await write(texture,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" preserveAspectRatio="none"><clipPath id="card"><polygon points="${points.map(p=>p.join(',')).join(' ')}"/></clipPath><image clip-path="url(#card)" href="data:image/png;base64,${dead.toString('base64')}" x="${x}" y="${y}" width="${w}" height="${h}" preserveAspectRatio="none"/></svg>`);
  set('VoteF'+i,rect,{},63);set('VoteP'+i,rect,{},64);set('VoteD'+i,rect,{texture},65);
 }
 const source=JSON.parse(await fs.readFile(path.join(repo,'ui/v3_authorized/trial_inputs/layout.json'),'utf8'));
 const original=source.t_tohyo_chara_US;
 const closing=original.frames.slice(original.labels.fl_ok-1,original.labels.fl_happyo-1);
 const wait=closing.flat().find(row=>row.resource==='t_tohyo_chara_tx_US.png');
 const waitTexture=base+'wait.png';await write(waitTexture,await fs.readFile(path.join(repo,wait.texture)));
 set('VoteWait',map(cardRect([wait.rect[0]+640,wait.rect[1]+360,...wait.rect.slice(2)])),{texture:waitTexture},68);
 for(let i=0;i<16;i++){
  const slot=String(i).padStart(3,'0');
  const blank=closing[0].find(row=>row.resource===`t_tohyo_chara_frame_${slot}_blank.png`);
  const texture=base+'shutter_'+i+'.png';await write(texture,await fs.readFile(path.join(repo,blank.texture)));
  set('VoteShutter'+i,map(bank.voteCards[i]),{texture},66);
 }
 const tracks=[];
 for(let i=0;i<closing.length;i+=12){
  const file=`Assets/Data/v4_story/vote_shutter_${i/12}.json`;
  await write(file,closing.slice(i,i+12).map(rows=>{
   const leaf=resource=>rows.find(row=>row.resource===resource);
   const cards=Array.from({length:16},(_,slot)=>{
    const key='t_tohyo_chara_frame_'+String(slot).padStart(3,'0');
    return ['.png','_blank.png'].map(suffix=>{
     const r=leaf(key+suffix);
     return r?[...cardRect([r.rect[0]+640,r.rect[1]+360,...r.rect.slice(2)]),r.opacity]:[0,0,0,0,0];
    });
   });
   return {cards,wait:leaf(wait.resource)?.opacity||0};
  }));
  tracks.push(file);
 }
 meta.shutters={frames:closing.length,tracks};
 const result=source.t_tohyo_chara_img_US;
 meta.resultPortraitIn=result.frames.slice(result.labels.fl_in-1,result.labels.fl_wait-1)
  .map(rows=>rows.find(r=>r.resource==='t_tohyo_dummy_chara.png')?.opacity||0);
 const confetti=result.frames.slice(result.labels.fl_happyo-1,result.labels.fl_out-1).map(rows=>rows.filter(r=>r.resource.includes('kamihubuki')));
 const effects=new Map();
 for(const row of confetti.flat())if(!effects.has(row.resource)){
  const texture=base+'result_'+row.resource;
  await write(texture,await fs.readFile(path.join(repo,row.texture)));effects.set(row.resource,texture);
 }
 const chunks=[];
 for(let i=0;i<confetti.length;i+=24){
  const file=`Assets/Data/v4_story/vote_result_fx_${i/24}.json`;
  await write(file,{frames:confetti.slice(i,i+24).map(rows=>rows.map(r=>[effects.get(r.resource),r.rect[0]+640,r.rect[1]+360,...r.rect.slice(2),r.rotation,r.opacity]))});
  chunks.push(file);
 }
 bank.tracks.resultFx={frames:confetti.length,chunks};
 for(let i=0;i<9;i++)set('VoteDigit'+i,map(bank.clocks.vote.rects[i]),{texture:bank.clocks.vote.digits['0']},92);
 for(let i=0;i<25;i++)set('VoteAnimation'+i,[0,0,1,1],{texture:''},100+i);
 vote.nodes=vote.nodes.filter(n=>!n.id.startsWith('VoteVerdict'));
 bank.tracks.close=await emitVoteVerdict({repo,write,set,createCanvas,loadImage,GlobalFonts,landmarks});
 for(let i=0;i<25;i++)vote.nodes.find(n=>n.id==='VoteAnimation'+i).slot.zIndex=190+i;
 bank.voteTV={...meta};delete bank.voteTV.records;
 if(!validWidgetAsset(vote)||vote.nodes.length>256)throw Error('Invalid final source voting plane');
 centerInputFrame(vote);
 for(const node of vote.nodes)if(/^(VoteTVBezel|VoteMonitor)/.test(node.id))node.parent='root';
 let matte=vote.nodes.find(n=>n.id==='VoteFullMatte');
 if(!matte){matte=createWidgetNode('Panel','VoteFullMatte','root');matte.name=matte.id;vote.nodes.push(matte);}
 matte.parent='root';matte.slot.anchors=[0,0,1,1];matte.slot.offset=[0,0,0,0];matte.slot.zIndex=-1;
 Object.assign(matte.properties,{background:'#000000ff',visible:true,focusable:false});
 if(!validWidgetAsset(vote))throw Error('Invalid fullscreen vote frame');
 await write('Assets/UI/Vote.hbwidget.json',vote);await write('Assets/Data/v4_story/trial_input_motion.json',bank);
 const presentation={};for(const key of ['voteInputName','voteResultName','voteResultBack','voteResultFaces','voteResultNames','voteCards','cards','cardCursors','clocks','tracks'])presentation[key]=bank[key];
 await write('Assets/Data/v4_story/vote_tv_source.json',{...bank.voteTV,presentation});
 return {nodes:vote.nodes.length,sourceUI:true,fullscreen:true,screen:meta.screen,requiresOrder:'emitVoteUI → emitTrialInputMotionUI → finalizeVoteTVUI'};
}
