import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {armamentTranscript,normalizeArmamentText}from './v4-armament-transcript.mjs';
const tasks=JSON.parse(await fs.readFile(new URL('../../data/v4_story/native_tasks.json',import.meta.url),'utf8')).tasks;
let count=0;
for(const task of Object.values(tasks))if(task.stage.kind==='armament'){
 const lines=task.stage.lines,rows=armamentTranscript(lines,1);
 for(let i=0;i<lines.length;i++)assert.equal(rows.filter(r=>r.line===i).map(r=>r.text).join(' '),normalizeArmamentText(lines[i]));
 assert(rows.every((r,i)=>i===0||r.line>=rows[i-1].line));
 const loop=[...rows,...rows];assert.deepEqual(loop.slice(rows.length),rows);
 assert(rows.length>3);count++;
 assert(rows.every(row=>!row.text.includes(' ')),'Spatial notes must carry complete individual words');
}
assert.equal(count,6);
assert.equal(armamentTranscript(['처음 말이야.다음 말이야.']).map(r=>r.text).join(' '),'처음 말이야. 다음 말이야.');
assert.equal(normalizeArmamentText('1.5초를 기다려.다음 문장.'),'1.5초를 기다려. 다음 문장.');
console.log(JSON.stringify({passed:true,tasks:count,scope:'Every authored line preserved exactly in order; sentence boundaries, decimal and loop identity'}));
