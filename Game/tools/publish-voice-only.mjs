// Regenerate the reviewed dialogue layer without replacing concurrent game work.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {voiceReviser} from './v4-voice-revisions.mjs';
import {validGameJson} from '../../../engineCreate/prototype/game-json.js';
const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game),work=path.join(game,'Saved/voice-rewrite-20261107'),root=path.join(game,'Assets/Data/v4_story');
const voice=await voiceReviser(repo),files=[],sha=b=>createHash('sha256').update(b).digest('hex');
for(const relative of await fs.readdir(root,{recursive:true})){
 if(!relative.endsWith('.json'))continue;
 const file=path.join(root,relative),before=await fs.readFile(file),a=JSON.parse(before),b=voice.revise(structuredClone(a));
 if(JSON.stringify(a)===JSON.stringify(b))continue;
 assert(validGameJson(b),'Native bounds: '+relative);
 files.push({file,before,after:Buffer.from(JSON.stringify(b,null,1)+'\n')});
}
// Preflight all files before any write; never overwrite intervening edits.
for(const row of files)assert.equal(sha(await fs.readFile(row.file)),sha(row.before));
for(const row of files){
 const backup=path.join(work,'assets-before',path.relative(game,row.file));await fs.mkdir(path.dirname(backup),{recursive:true});
 await fs.writeFile(backup,row.before,{flag:'wx'});
 const temp=row.file+'.voice-tmp';await fs.writeFile(temp,row.after);await fs.rename(temp,row.file);
}
const report={...voice.report(),files:files.map(r=>({path:path.relative(game,r.file),before:sha(r.before),after:sha(r.after)})),policy:'Exact source/text matches only; concurrent Source/Assets work preserved. The publisher calls the same source-owned voice layer. This is not a full regeneration/build or editor visual acceptance.'};
await fs.writeFile(path.join(work,'editor-assets-layer.json'),JSON.stringify(report,null,1));
console.log(JSON.stringify({files:files.length,changed:report.changed,manualSources:report.manualSources.length}));
