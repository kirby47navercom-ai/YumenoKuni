// 논의 스크럼 V3 큰 발언 글(Claude 2026-11-06, 사양서 27a). 영상 1번 43~137초 : 흰 굵은 고딕, 왼쪽 맞춤 3~5줄, 맞물림 낱말은 노랑.
// 상대 발언(themText, 낱말 keyword)과 아군 응수(usText, 낱말 responseKeyword) 모두. 결과 : Assets/Art/ui/scrum_v3text/<해시>.png + Assets/Data/scrum_v3text.json
// node tools/claude-scrum-text.mjs
import fs from 'node:fs/promises';import path from 'node:path';import {createHash} from 'node:crypto';import {createRequire} from 'node:module';import {pathToFileURL} from 'node:url';import assert from 'node:assert/strict';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game);
const {createCanvas,GlobalFonts}=createRequire(path.join(repo,'Game/engineCreate/package.json'))('@napi-rs/canvas');
const W=700,H=330,S=2;
const draw=(text,kw)=>{
 const c=createCanvas(W*S,H*S),g=c.getContext('2d');g.scale(S,S);let size,lines;
 for(size=50;size>=34;size-=2){g.font=size+'px ScV3';lines=[];let line='';const words=text.replace(/([.?!,])(?=\S)/g,'$1 ').split(/\s+/).filter(Boolean);for(const wd of words){const t=line?line+' '+wd:wd;if(g.measureText(t).width>W-20&&line){lines.push(line);line=wd;}else line=t;}if(line)lines.push(line);if(lines.some(l=>g.measureText(l).width>W-20))continue;if(lines.length*size*1.28<=H-10)break;}
 // 낱말 위치(글자 단위)
 const all=[...text],hit=new Array(all.length).fill(false);const at=kw?text.indexOf(kw):-1;if(at>=0){const s=[...text.slice(0,at)].length;for(let i=0;i<[...kw].length;i++)hit[s+i]=true;}
 let k=0;const step=size*1.28,top=(H-lines.length*step)/2+size*.9;g.textBaseline='alphabetic';
 for(let li=0;li<lines.length;li++){let x=10;const y=top+li*step;
  // 줄이 원문에서 시작하는 위치 맞추기(줄바꿈에서 빠진 공백 건너뜀)
  for(const ch of [...lines[li]]){if(ch===' '){g.font=size+'px ScV3';x+=g.measureText(' ').width;if(all[k]===' ')k++;continue;}while(k<all.length&&all[k]!==ch)k++;g.font=size+'px ScV3';g.lineJoin='round';g.lineWidth=7;g.strokeStyle='rgba(8,6,18,.92)';g.strokeText(ch,x,y);g.fillStyle='rgba(0,0,0,.5)';g.fillText(ch,x+3,y+4);g.fillStyle=hit[k]?'#ffc31c':'#ffffff';g.fillText(ch,x,y);x+=g.measureText(ch).width;k++;}}
 return {png:c.toBuffer('image/png'),size,lines};
};
export async function emitScrumClaims({tasks,source,write,existing}){
 assert(GlobalFonts.registerFromPath(path.join(source,'Assets/Fonts/gothica1/GothicA1-Bold.ttf'),'ScV3'));
 const out=existing||{version:1,width:W,height:H,items:{}};
 let added=0;
 for(const task of tasks.filter(t=>t.stage?.kind==='scrum'))for(const pair of task.stage.pairs){
  const after=[...(pair.success||[]),...(pair.afterSuccess||[])].filter(row=>row.type==='say'&&row.text);
  const phrases=[[pair.themText,pair.claimKeyword||pair.keyword,true],
   [pair.usText,pair.claimKeyword?pair.responseKeyword:pair.keyword,false],
   ...after.map(row=>[row.text,'',false])];
  for(const [text,keyword,plain] of phrases){
   if(!text||out.items[text])continue;
   const key=createHash('sha256').update(text).update(keyword||'').update('scv3-700x330-v3').digest('hex').slice(0,24);
   const texture='Assets/Art/ui/scrum_v3text/'+key+'.png',r=draw(text,keyword);
   await write(texture,r.png);
   out.items[text]={texture,fontSize:r.size,lines:r.lines,keywordFound:!!keyword&&text.includes(keyword)};
   if(keyword&&plain){
    const hash=createHash('sha256').update(text).update('plain').update('scv3-700x330-v3').digest('hex').slice(0,24);
    out.items[text].plain='Assets/Art/ui/scrum_v3text/'+hash+'.png';
    await write(out.items[text].plain,draw(text,'').png);
   }
   added++;
  }
 }
 await write('Assets/Data/scrum_v3text.json',out);
 return {added,total:Object.keys(out.items).length};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const native=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8'));
 const result=await emitScrumClaims({tasks:Object.values(native.tasks),source:game,write:async(name,value)=>{
  const file=path.join(game,name);await fs.mkdir(path.dirname(file),{recursive:true});
  await fs.writeFile(file,Buffer.isBuffer(value)?value:JSON.stringify(value,null,1));
 }});
 console.log(result);
}
