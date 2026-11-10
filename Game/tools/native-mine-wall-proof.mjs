// Read the rendered board, then exercise the unchanged rules with real input.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
export async function proveMineWall(probe,session){
 const beforeStats=await probe.stats(),{width,height}=beforeStats.mineV4;
 const [left,top,boardWidth,boardHeight]=beforeStats.mineV4.boardRect;assert(Math.abs(boardWidth/width-boardHeight/height)<.001,"Square tiles at actual difficulty");
 const count=width*height,letters=['w','p','y','b'];
 const prefix=beforeStats.taskId.toLowerCase()+'-';const capture=async name=>{name=prefix+name;await probe.capture(name);return JSON.parse(await fs.readFile(path.join(session,name+'.ui.json'),'utf8'));};
 const nodes=j=>j.widgets.find(w=>w.instance==='minev4').nodes;
 const cellNodes=j=>new Map(nodes(j).filter(n=>/^Cell\d+$/.test(n.id)).map(n=>[Number(n.id.slice(4)),n]));
 const board=j=>{const map=cellNodes(j);return Array.from({length:count},(_,i)=>{const n=map.get(i);if(!n.properties.visible||n.properties.opacity===0)return -1;const color=n.properties.texture.match(/mine_([wpyb])(?:_edge\d+)?\.svg$/)?.[1];assert(color,'Actual mine color texture '+i);return letters.indexOf(color);});};
 const adjacent=k=>[k%width?k-1:-1,k%width+1<width?k+1:-1,k>=width?k-width:-1,k+width<count?k+width:-1].filter(n=>n>=0);
 const group=(b,k)=>{if(b[k]<0)return [];const found=new Set([k]),queue=[k];for(let n=0;n<queue.length;n++)for(const a of adjacent(queue[n]))if(b[a]===b[k]&&!found.has(a)){found.add(a);queue.push(a);}return [...found];};
 const point=k=>[left+(k%width+.5)*boardWidth/width,top+(Math.floor(k/width)+.5)*boardHeight/height];
 const initial=await capture('wall-before'),b=board(initial);
 const hud=initial.widgets.find(w=>w.instance==='minehudv4');
 const digits=hud.nodes.filter(n=>/^MineClock\d+$/.test(n.id));
 assert.equal(digits.length,9);assert(digits.every(n=>n.properties.visible&&/mine_digit_g/.test(n.properties.texture)));
 assert.equal(hud.nodes.find(n=>n.id==='MineEntryTitle').properties.visible,false);
 assert.equal(initial.widgets.find(w=>w.instance==='stage').nodes.find(n=>n.id==='MineTimer').properties.visible,false);

 const question=j=>j.widgets.find(w=>w.instance==='minehudv4').nodes.find(n=>n.id==='MineQuestionText').properties.visible;
 assert.equal((await probe.stats()).mineV4.questionVisible,false);assert.equal(question(initial),false);
 await probe.tap('Space');const shown=await capture('wall-question-shown');assert.equal((await probe.stats()).mineV4.questionVisible,true);assert.equal(question(shown),true);assert.deepEqual(board(shown),b);
 await probe.tap('Space');const hidden=await capture('wall-question-hidden');assert.equal(question(hidden),false);assert.deepEqual(board(hidden),b);
 const joined=Array.from({length:count},(_,i)=>group(b,i)).find(g=>g.length>=2&&g.length<=8);assert(joined,'Real connected group');const selected=new Set(joined);
 // Hidden Win32 windows admit a targeted pointer sample with a button message.
 // Focus makes this a normal non-removing input, never a debug cursor write.
 await probe.key('Shift',true);await probe.click(...point(joined[0]));await probe.sampled(3);const hover=await capture('wall-hover');
 assert(hover.widgets.find(w=>w.instance==='minehudv4').nodes.find(n=>n.id==='MineCursor').properties.texture.endsWith('mine_cursor_2.svg'),'Connected group cursor');
 const edgeMasks={};for(const [k,n]of cellNodes(hover)){const mask=Number(n.properties.texture.match(/_edge(\d+)\.svg$/)?.[1]||0);if(mask)edgeMasks[k]=mask;
 const connected=k<count&&b[k]>=0&&adjacent(k).some(a=>b[a]===b[k]);
 const outer=k<count&&(k<width||k>=count-width||k%width===0||k%width===width-1||adjacent(k).some(a=>b[a]!==b[k]));
 assert.equal(mask>0,connected&&outer,'Every removable group has an outline during focus');}
 assert.deepEqual(board(hover),b,'Focus input must not remove tiles');
 const elsewhere=Object.keys(edgeMasks).map(Number).find(k=>!selected.has(k));assert.notEqual(elsewhere,undefined);
 assert(cellNodes(hover).get(elsewhere).properties.opacity<1,'A separate group also pulses');
 await probe.key('Shift',false);
 await probe.click(...point(joined[0]));await probe.sampled(80);const removed=await capture('wall-group-removed'),after=board(removed),boundary=new Set(joined.flatMap(adjacent).filter(k=>!selected.has(k)&&b[k]>=0));
 // Compare palette rotation separately from board dimensions.
 const colors=Math.max(...b)+1;for(let k=0;k<count;k++)assert.equal(after[k],selected.has(k)?-1:boundary.has(k)?(b[k]+1)%colors:b[k],'No gravity; boundary rotates exactly once');
 let lone=after.findIndex((color,k)=>color>=0&&group(after,k).length===1);assert(lone>=0,'Actual isolated tile');
 await probe.click(...point(lone));assert.equal((await probe.stats()).mineV4.clicks,1);
 await probe.click(...point(joined[0]));const emptyReset=await probe.stats();assert.equal(emptyReset.mineV4.last,-1);assert.equal(emptyReset.mineV4.clicks,0,'An empty hole clears the repeated-hit counter');
 const otherLone=after.findIndex((color,k)=>k!==lone&&color>=0&&group(after,k).length===1);assert(otherLone>=0);
 await probe.click(...point(lone));await probe.click(...point(otherLone));const switched=await probe.stats();assert.equal(switched.mineV4.last,otherLone);assert.equal(switched.mineV4.clicks,1,'A different isolated tile starts its own counter');
 await probe.click(...point(lone));const first=await probe.stats();assert.equal(first.mineV4.last,lone);assert.equal(first.mineV4.clicks,1);
 await probe.click(...point(lone));const second=await probe.stats();assert.equal(second.mineV4.clicks,2);const cracks=await capture('wall-lone-two-hits');assert(nodes(cracks).find(n=>n.id==='MineHintHit').properties.texture.endsWith('mine_hit_2.svg'));
 const hp=second.trialHp;const [x,y]=point(lone);
 await probe.move(x,y);await probe.button(x,y,true);
 let penalty;try{penalty=await capture('wall-time-penalty');}finally{await probe.button(x,y,false);}
 const label=penalty.widgets.find(w=>w.instance==='stage').nodes.find(n=>n.id==='MinePenalty');
 assert(label.properties.visible&&label.properties.text==='−10초','Single tile time penalty is visible in Korean');
 const third=await probe.stats();assert.equal(third.mineV4.clicks,0);assert.equal(third.trialHp,hp);assert(second.mineV4.time-third.mineV4.time>=600,'Single tile costs ten seconds plus elapsed time');await probe.sampled(80);const loneRemoved=await capture('wall-lone-removed');assert.equal(board(loneRemoved)[lone],-1);
 const proof={ok:true,scope:'Real own Win32 inputs and rendered UI; no board/timer/answer injection. Original runtime never used.',width,height,boardRect:[left,top,boardWidth,boardHeight],squareTiles:true,questionToggle:true,colors,joined,boundary:[...boundary],edgeMasks,focusBlocksRemoval:true,noGravity:true,boundaryChangesOnce:true,emptyResetsHits:true,changingTileResetsHits:true,lone,clickSequence:[first.mineV4.clicks,second.mineV4.clicks,third.mineV4.clicks],timeLoss:second.mineV4.time-third.mineV4.time,hpPreserved:true};
 await fs.writeFile(path.join(session,prefix+'mine-wall-proof.json'),JSON.stringify(proof,null,2));return proof;
}
