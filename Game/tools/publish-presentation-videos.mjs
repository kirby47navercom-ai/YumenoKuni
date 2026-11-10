// A small index referencing existing native recordings: no duplicate MP4 cache.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game),out=path.join(repo,'검토 영상/20261104');
const read=async p=>JSON.parse(await fs.readFile(path.join(game,p),'utf8'));
const selected=new Map();
const extra=process.argv.filter(a=>a.startsWith('--suite=')).map(a=>a.slice(8));
assert(extra.every(s=>/^complete-presentation-suite-\d+$/.test(s)));
for(const suite of ['complete-presentation-suite-1793797459631','complete-presentation-suite-1793798993116','complete-presentation-suite-1793800409186','complete-presentation-suite-1793801960372',...extra]){
 const report=await read('Saved/'+suite+'/report.json');
 for(const item of report.results||[])if(item.sequenceCompleted)selected.set(item.label,item.work);
}
const titles=[['nonstop','논스톱 논의'],['panic','패닉 논의'],['showdown','반론 쇼다운'],['mine-wall','발굴 이매지네이션 · 벽과 물건'],['physical-statement','발굴 이매지네이션 · 실물 자료'],['anagram','섬광 애너그램'],['scrum','논의 스크럼'],['armament','이론무장'],['climax','클라이맥스 추리'],['vote','범인 투표'],['person','인물 지목'],['culprit','범인 지목'],['spot','지점 지목'],['evidence','증거 선택'],['choice','정답 선택'],['reasoning','추리 연결'],['lie','거짓말 논파']];
const clips=[];
async function add(title,work,movie,index=0,fixture=true){
 assert(movie?.movie&&movie.audioPeak>0);
 assert(movie.streams.some(s=>s.type==='video')&&movie.streams.some(s=>s.type==='audio'));
 const file=path.resolve(movie.movie);assert(file.startsWith(path.join(game,'Saved')+path.sep));
 const bytes=await fs.readFile(file);assert(bytes.length>1024);
 const proof=JSON.parse(await fs.readFile(path.join(work,'report.json'),'utf8'));
 clips.push({title,src:path.relative(out,file).replaceAll('\\','/'),duration:movie.duration,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex'),gameModuleSHA256:proof.gameModuleSHA256,packageExecutableSHA256:proof.packageExecutableSHA256,report:path.relative(out,path.join(work,'report.json')).replaceAll('\\','/'),part:index+1,fixture,review:'Actual native inputs and game mixer. Sampled frames reviewed; no claim that every frame/audio sample or every story branch was inspected.'});
}
for(const [label,title]of titles){
 const work=selected.get(label);assert(work,'Missing complete representative '+label);
 const report=JSON.parse(await fs.readFile(path.join(work,'report.json'),'utf8'));assert(report.sequenceCompleted&&!report.error);
 await add(title,work,report.movie,0,report.precondition.fixture);
}
for(const [folder,title]of [['complete-discovery-movie-1793801630860','발견 · 증거 획득 · 조사 진입'],['complete-discovery-movie-1793798789988','현장 이동 · 물건 조사'],['native-freetime-world-1793800006198','자유행동 · 직접 접근과 대화']]){
 const work=path.join(game,'Saved',folder),report=await read('Saved/'+folder+'/report.json');
 const complete=folder.startsWith('native-freetime-world-')?report.ok&&report.cancelVerified&&report.after:report.sequenceCompleted;
 assert(complete&&!report.error);
 for(const [index,movie]of report.movies.entries())await add(title+(report.movies.length>1?' '+(index+1):''),work,movie,index,report.fixture);
}
await fs.mkdir(out,{recursive:true});
const build=await read('build-result.json');
await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify({build:build.id,clips,scope:'17 representative trial sequences and4 daily/discovery/investigation parts, not every branch or whole-game completion. Earlier clips retain their recorded module provenance; final regression supersedes only the corresponding cases. No duplicate video files created.'},null,2));
const data=JSON.stringify(clips).replaceAll('<','\\u003c');
await fs.writeFile(path.join(out,'index.html'),`<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>유메노쿠니 · 연출 검토 영상</title><style>
*{box-sizing:border-box}body{margin:0;background:#111218;color:#eee;font:16px system-ui}header{padding:22px 28px;border-bottom:1px solid #343541}h1{font-size:22px;margin:0 0 7px}p{margin:0;color:#b8bac6}main{display:grid;grid-template-columns:280px 1fr;min-height:85vh}nav{padding:14px;overflow:auto;max-height:85vh;border-right:1px solid #343541}button{display:block;width:100%;text-align:left;border:0;background:transparent;color:#ddd;padding:12px;border-radius:4px;font:inherit;cursor:pointer}button:hover,button[aria-current=true]{background:#352c40;color:#ffe469}article{padding:24px;min-width:0}h2{font-size:20px;margin:0 0 15px}video{width:100%;max-height:72vh;background:#000}small{display:block;color:#b8bac6;line-height:1.7;margin-top:12px}a{color:#e1c7ff}@media(max-width:800px){main{display:block}nav{max-height:220px;border-bottom:1px solid #343541}article{padding:12px}}
</style><header><h1>유메노쿠니 · 연출 검토 영상</h1><p>실제 게임 입력과 게임 소리를 담은 구간별 영상이에요. 영상에는 스토리 내용이 포함돼요.</p></header><main><nav aria-label="영상 선택"></nav><article><h2></h2><video controls preload="metadata" playsinline></video><small id="info"></small><small>준비된 저장 지점에서 시작한 대표 구간이에요. 전편·전분기 검사나 모든 연출 완료를 뜻하지 않아요.</small><a id="direct">영상 파일 직접 열기</a></article></main><script>
const clips=${data},nav=document.querySelector('nav'),video=document.querySelector('video');
const buttons=clips.map((c,i)=>{const b=document.createElement('button');b.textContent=String(i+1).padStart(2,'0')+' · '+c.title;b.onclick=()=>select(i);nav.append(b);return b});
function select(i){const c=clips[i];buttons.forEach((b,k)=>b.setAttribute('aria-current',k===i));document.querySelector('h2').textContent=c.title;video.src=c.src;document.querySelector('#direct').href=c.src;document.querySelector('#info').textContent='길이 '+Math.round(c.duration)+'초 · 실제 게임 음향 포함'+(c.fixture?' · 도달 가능한 진행 상태를 사용한 촬영':' · 정상 진행 저장으로 시작');location.hash=String(i+1)}
select(Math.max(0,Math.min(clips.length-1,Number(location.hash.slice(1)||1)-1)));
</script></html>`);
console.log(JSON.stringify({index:path.join(out,'index.html'),clips:clips.length,seconds:clips.reduce((n,c)=>n+c.duration,0),duplicateVideoBytes:0}));
