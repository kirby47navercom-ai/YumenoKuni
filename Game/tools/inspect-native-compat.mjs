// Validation only: no player launch, engine changes or generated asset writes.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {readProjectManifest} from '../../../engineCreate/tools/project-manifest.mjs';
import {buildGame,readBuildProfiles} from '../../../engineCreate/tools/build-game.mjs';
import {activeInstalledVersions} from '../../../engineCreate/tools/install-editor.mjs';
const root=path.resolve(import.meta.dirname,'..'),engine=path.resolve(root,'../../engineCreate');
const record=await readProjectManifest(path.join(root,'YumenoKuni.hbproject'));
const profile={...(await readBuildProfiles(record)).profiles[0],windowsRuntime:'native',windowsRenderer:'d3d11',configuration:'development',targetFrameRate:60,framePacing:'fixed',width:1280,height:720,scenes:[{path:record.manifest.startupScene,enabled:true}]};
const hashes={};for(const file of ['tools/build-native-game.mjs','tools/native-game-runner.mjs','tools/native-widget-layer.mjs','tools/windows-package-signing.mjs','prototype/build-profile.js','dist/HBEngine/HBNativePlayer.exe'])hashes[file]=createHash('sha256').update(await fs.readFile(path.join(engine,file))).digest('hex');
let report;try{const result=await buildGame(record,profile,{dryRun:true});report={ok:true,profile,renderer:result.renderer,renderBackend:result.renderBackend,hashes};}catch(error){report={ok:false,profile,error:error.message,hashes};}
report.activeInstalledVersions=await activeInstalledVersions('C:/Users/kirby/HBEngine');
const destination=path.join(root,'Saved/native-compat-'+Date.now()+'.json');await fs.writeFile(destination,JSON.stringify(report,null,2));console.log(JSON.stringify({report:destination,...report}));if(!report.ok)process.exitCode=1;
