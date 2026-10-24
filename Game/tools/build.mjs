// node tools/build.mjs [--check] [--release]
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {readProjectManifest} from '../../../engineCreate/tools/project-manifest.mjs';
import {buildGame,readBuildProfiles} from '../../../engineCreate/tools/build-game.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const release=process.argv.includes('--release'),check=process.argv.includes('--check');
const record=await readProjectManifest(path.join(root,'YumenoKuni.hbproject'));
const profile=(await readBuildProfiles(record)).profiles[0];
Object.assign(profile,{gameName:'YumenoKuni',productName:'유메노쿠니',configuration:'development',targetFrameRate:60,framePacing:'fixed',width:1280,height:720,windowsRenderer:'scene',scenes:[{path:record.manifest.startupScene,enabled:true}]});
if(release)Object.assign(profile,{id:'windows-release',name:'Windows Release',configuration:'release'});
const result=await buildGame(record,profile,{dryRun:check,onProgress:p=>console.log(p)});
if(!check)await fs.writeFile(path.join(root,'build-result.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(check?result:{executable:result.executable},null,2));
