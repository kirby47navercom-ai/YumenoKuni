// node tools/build.mjs [--check] [--release]
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';
import {installBuildSharing} from './build-share.mjs';
import {validateV4DataBudget} from './v4-data-pack.mjs';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const engineArgument=process.argv.find(v=>v.startsWith('--engine-root='))?.slice(14);
const engineRoot=await fs.realpath(path.resolve(root,engineArgument||'engineCreate'));
// Panic uses the already approved three-camera bridge. A newer SDK without
// that extension must fail here rather than ship an empty single-camera view.
const viewRunner=await fs.readFile(path.join(engineRoot,'tools/native-game-runner.mjs'),'utf8');
const viewRenderer=await fs.readFile(path.join(engineRoot,'prototype/native-scene-renderer.js'),'utf8');
if(!viewRunner.includes('gameRenderViews')||!viewRenderer.includes('renderer.hbViews'))throw Error('SDK에 패닉 3카메라 연결이 없어요. 프로젝트의 prepare-collaborator-sdk.mjs로 준비한 SDK를 사용하세요.');
const playerArgument=process.argv.find(v=>v.startsWith('--native-player='))?.slice(16);
const nativeSnapshotArgument=process.argv.find(v=>v.startsWith('--native-snapshot='))?.slice(18);
const compileMs=Number(process.argv.find(v=>v.startsWith('--native-compile-ms='))?.slice(20)||0);
if(compileMs&&(!playerArgument||!Number.isInteger(compileMs)||compileMs<60000||compileMs>300000))throw Error('Invalid owned native build deadline');
const playerAdapter=playerArgument?await (await import('./approved-panic-build.mjs')).approvedPanicBuilder({root,engineRoot,player:path.resolve(root,playerArgument),compileMs}):null;
if(nativeSnapshotArgument&&!playerAdapter)throw Error('--native-snapshot에는 검증된 --native-player가 필요해요.');
if(!playerAdapter){const candidate=await fs.access(path.join(engineRoot,'HBNativePlayer.exe')).then(()=>path.join(engineRoot,'HBNativePlayer.exe'),()=>path.join(engineRoot,'dist/HBEngine/HBNativePlayer.exe'));if(!(await fs.readFile(candidate)).includes(Buffer.from('renderViews')))throw Error('엔진 스크립트와 실행기의 패닉 렌더 프로토콜이 달라요. 검증된 실행기를 --native-player=Saved/... 로 지정하세요.');}
const {readProjectManifest}=await import(pathToFileURL(path.join(engineRoot,'tools/project-manifest.mjs')));
const {buildGame,readBuildProfiles}=await import(pathToFileURL(path.join(engineRoot,'tools/build-game.mjs')));
const release=process.argv.includes('--release'),check=process.argv.includes('--check');
// Blueprint native code is generated metadata. Refresh only that copy so its
// API metadata and recorded source cannot lag behind source-only edits.
const nativeAsset=JSON.parse(await fs.readFile(path.join(root,'Assets/Blueprints/BP_Yumeno.hbblueprint.json'),'utf8'));
const nativeHeader=await fs.readFile(path.join(root,'Source/Yumeno.h'),'utf8'),nativeSource=await fs.readFile(path.join(root,'Source/Yumeno.cpp'),'utf8');
const nativeSourceRefreshed=nativeAsset.native?.header!==nativeHeader||nativeAsset.native?.source!==nativeSource;
if(nativeSourceRefreshed&&!nativeSnapshotArgument){
 if(check)throw Error('C++ 코드 사본이 오래됐어요. node tools/create-project.mjs --native-source-only 를 실행하세요.');
 execFileSync(process.execPath,[path.join(root,'tools/create-project.mjs'),'--native-source-only'],{cwd:root,stdio:'inherit',windowsHide:true});
 const refreshed=JSON.parse(await fs.readFile(path.join(root,'Assets/Blueprints/BP_Yumeno.hbblueprint.json'),'utf8'));
 if(refreshed.native?.header!==nativeHeader||refreshed.native?.source!==nativeSource)throw Error('C++ 코드 사본 갱신을 확인할 수 없어요.');
}
let previousExecutable='';try{previousExecutable=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8')).executable||'';}catch(error){if(error.code!=='ENOENT')throw error;}
const record=await readProjectManifest(path.join(root,'YumenoKuni.hbproject'));
const profile=(await readBuildProfiles(record)).profiles[0];
Object.assign(profile,{gameName:'YumenoKuni',productName:'유메노쿠니',configuration:'development',targetFrameRate:120,framePacing:'fixed',width:1280,height:720,windowsRuntime:'native',windowsRenderer:'d3d11',scenes:[{path:record.manifest.startupScene,enabled:true},...['Court','Explore','DebateHud','PanicHud','AnagramHud','ShowdownHud','ArmamentHud'].map(name=>({path:'Assets/Scenes/'+name+'.hbscene.json',enabled:true}))]});
const parkManifest=await fs.readFile(path.join(root,'../art/space_v4/park_levels_v1/manifest.json'),'utf8').then(JSON.parse,e=>{if(e.code!=='ENOENT')throw e;return null;});
if(parkManifest?.geometryComplete){const plan=JSON.parse(await fs.readFile(path.join(root,'../art/space_v4/park_levels_v1/plan.json'),'utf8'));profile.scenes.push(...plan.districts.map(d=>({path:'Assets/Scenes/'+d.scene+'.hbscene.json',enabled:true})));}
if(release)Object.assign(profile,{id:'windows-release',name:'Windows Release',configuration:'release'});
console.log(JSON.stringify({v4DataBudget:await validateV4DataBudget(root)}));
const sharing=check?null:await installBuildSharing({root,profile:profile.id,previous:previousExecutable?path.dirname(previousExecutable):'',projectId:record.manifest.id});
let result;try{const options={dryRun:check,onProgress:p=>console.log(p)};if(playerAdapter){options.onProgress('검증');const {inspectBuild}=await import(pathToFileURL(path.join(engineRoot,'tools/build-game.mjs')));const inspectionRecord=nativeSnapshotArgument?await (await import('./verified-native-snapshot.mjs')).snapshotInspectionRecord(record,{root,engineRoot,file:nativeSnapshotArgument}):record;let payload=await inspectBuild(inspectionRecord,profile);if(nativeSnapshotArgument)payload=await (await import('./verified-native-snapshot.mjs')).applyVerifiedNativeSnapshot(payload,{root,engineRoot,file:nativeSnapshotArgument});result=await playerAdapter.build(record,profile,payload,options);result.approvedPanicRuntime=playerAdapter.provenance;}else result=await buildGame(record,profile,options);result.engineSDKRoot=engineRoot;result.nativeSourceRefreshed=nativeSourceRefreshed;}finally{sharing?.restore();}
if(sharing){result.contentSharing=sharing.stats;console.log(JSON.stringify({contentSharing:sharing.stats}));}
if(!check)await fs.writeFile(path.join(root,'build-result.json'),JSON.stringify(result,null,2)+'\n');
// Archive obsolete builds/closed test caches; retain current, previous, live players and all saves/reports.
if(!check&&process.platform==='win32')execFileSync('powershell.exe',['-NoProfile','-ExecutionPolicy','Bypass','-File',path.join(root,'tools/prune-builds.ps1'),'-CurrentExecutable',result.executable,...(previousExecutable?['-PreviousExecutable',previousExecutable]:[])],{stdio:'inherit',windowsHide:true});
if(check&&nativeSnapshotArgument){const report=path.join(root,'Saved/build-check-verified-native.json');await fs.writeFile(report,JSON.stringify(result,null,2));console.log(JSON.stringify({checkReport:report,files:result.files,bytes:result.bytes,nativeModules:result.nativeModules,snapshot:result.verifiedNativeSnapshot?.sourceRoot}));}else console.log(JSON.stringify(check?result:{executable:result.executable},null,2));
