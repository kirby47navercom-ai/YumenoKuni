// Candidate only. Install as engine tools/native-save-migration.mjs after approval.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {parseGameJson} from '../../../engineCreate/prototype/game-json.js';
export async function migrateLegacyGameSaves(directory,projectId){
 const source=path.join(directory,'savegames.json'),destination=path.join(directory,'Saves');
 const existing=await fs.lstat(destination).catch(e=>{if(e.code!=='ENOENT')throw e;return null;});
 if(existing){if(!existing.isDirectory()||existing.isSymbolicLink())throw Error('저장 폴더를 확인하세요.');if((await fs.readdir(destination)).length)return {state:'native-present',imported:0};}
 const stat=await fs.lstat(source).catch(e=>{if(e.code!=='ENOENT')throw e;return null;});if(!stat)return {state:'none',imported:0};
 if(!stat.isFile()||stat.isSymbolicLink()||stat.size>256*1024*1024)throw Error('이전 저장 파일의 형식·크기를 확인하세요. 원본은 보존돼요.');
 const bytes=await fs.readFile(source),legacy=JSON.parse(bytes.toString('utf8'));if(legacy.version!==1||!legacy.items||typeof legacy.items!=='object'||Array.isArray(legacy.items))throw Error('이전 저장 형식을 읽지 못했어요. 원본은 보존돼요.');
 const prefix='hbengine.savegame.json.',suffix='.project.'+encodeURIComponent(projectId),entries=[];
 for(const[key,text]of Object.entries(legacy.items))if(key.startsWith(prefix)&&key.endsWith(suffix)){
  const slot=key.slice(prefix.length,-suffix.length);if(!slot||slot.length>80||/[\\/\x00-\x1f]/.test(slot)||['.','..'].includes(slot)||typeof text!=='string')throw Error('이전 저장 슬롯을 확인하세요. 원본은 보존돼요.');parseGameJson(text,{object:false});entries.push([encodeURIComponent(slot)+'.json',text]);
 }
 if(!entries.length)return {state:'no-project-slots',imported:0};
 const stage=await fs.mkdtemp(path.join(directory,'.native-save-import-'));
 try{
  for(const[name,text]of entries)await fs.writeFile(path.join(stage,name),text,{flag:'wx',flush:true});
  const receipt={version:1,source:'savegames.json',sourceSha256:createHash('sha256').update(bytes).digest('hex'),imported:entries.length};await fs.writeFile(path.join(stage,'.legacy-import.json'),JSON.stringify(receipt),{flag:'wx',flush:true});
  // Only remove an empty placeholder; a raced native write makes rmdir fail safely.
  if(existing)await fs.rmdir(destination);
  await fs.rename(stage,destination);return {state:'imported',...receipt};
 }catch(error){await fs.writeFile(path.join(stage,'failure.json'),JSON.stringify({message:error.message,sourcePreserved:true})).catch(()=>{});throw error;}
}
