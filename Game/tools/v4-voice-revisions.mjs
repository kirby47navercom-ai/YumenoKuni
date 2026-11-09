// Exact source-addressed dialogue revisions. Never replace arbitrary JSON strings.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const clean=s=>s.split(']').slice(1).join(']').trim().replaceAll('**','').replace(/^["“”]+|["“”]+$/g,'');
const unmark=s=>s.replace(/[【】〔〕]/g,'');
export async function voiceReviser(repo){
 const rows=JSON.parse(await fs.readFile(path.join(repo,'tools/v4_voice_revisions_20261107.json'),'utf8')).revisions;
 const index=new Map(rows.map(r=>[r.file+':'+r.line,{...r,old:clean(r.before),versions:[r.before,...(r.beforeVersions||[])].map(clean),next:clean(r.after)}]));
 const stats={changed:0,manualSources:new Set(),sourceKeys:new Set(),boundedStageChanges:0,skippedAdaptations:0};
 const direction=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/trial_direction.json'),'utf8'));
 const manual=new Set(rows.filter(r=>r.manual).map(r=>r.file+':'+r.line));
 function revise(value){
  if(Array.isArray(value)){for(const v of value)revise(v);return value;}
  if(!value||typeof value!=='object')return value;
  const source=value.source&&typeof value.source==='object'?value.source:value.provenance;
  const key=source?.file+':'+source?.line,row=index.get(key);
  if(row&&typeof value.text==='string'&&(value.speaker||value.actor)&&!String(value.id||'').startsWith('v4:noise:')){
   let next;if(row.versions.includes(value.text))next=row.next;else if(row.versions.some(v=>value.text===unmark(v)))next=unmark(row.next);
   if(next!==undefined&&next!==value.text){
    const original=value.text;
    const decoy=direction.debate?.[value.id]?.decoy?.word;
    if(decoy&&original.includes(decoy))assert(next.includes(decoy),'Authored decoy phrase must survive: '+value.id);
    // Weak/lie target phrases stay exact; only their measured start can move.
    const moved=[];
    function target(t){if(!t||typeof t.word!=='string')return;assert(original.slice(t.start,t.start+t.word.length)===t.word,'Old target offset is stale');const at=next.indexOf(t.word);assert(at>=0&&next.indexOf(t.word,at+1)<0,'Revised target missing/ambiguous');moved.push([t,at]);}
    for(const k of ['weak','lieWeak'])target(value[k]);
    for(const t of value.targets||[])target(t.weak||t);
    if(value.kind&&['plain','weak','agree','noise'].includes(value.kind)&&!value.splitCount){
     assert(next.length<=48,'Revised native stage needs authored reflow: '+value.id);++stats.boundedStageChanges;
    }
    value.text=next;for(const[t,at]of moved)t.start=at;
    ++stats.changed;stats.sourceKeys.add(key);if(manual.has(key))stats.manualSources.add(key);
   }else if(next===undefined)++stats.skippedAdaptations;
  }
  for(const[k,v]of Object.entries(value))if(!['source','provenance'].includes(k))revise(v);
  return value;
 }
 return {revise,report:()=>({...stats,manualSources:[...stats.manualSources],sourceKeys:[...stats.sourceKeys]})};
}
