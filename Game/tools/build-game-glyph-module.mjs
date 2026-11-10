// Compile only the game's C++ against the existing SDK; no engine source changes.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/game-trial-work-20261102');
const currentSource=process.argv.includes('--current-source');
const sourceRootArgument=process.argv.find(v=>v.startsWith('--source-root='))?.slice(14);
const buildResultArgument=process.argv.find(v=>v.startsWith('--build-result='))?.slice(15);
assert(!sourceRootArgument||currentSource);
const sourceOverridesFile=process.argv.find(v=>v.startsWith('--source-overrides='))?.slice(19);
const outputTag=process.argv.find(v=>v.startsWith('--output-tag='))?.slice(13);assert(!outputTag||/^[a-z0-9-]{1,48}$/.test(outputTag));assert(!sourceOverridesFile||currentSource);
const diagnosticHostRate=Number(process.argv.find(v=>v.startsWith('--diagnostic-host-rate='))?.slice(23)||0);assert(!diagnosticHostRate||(currentSource&&outputTag&&diagnosticHostRate===240));
const engineRoot=process.argv.find(v=>v.startsWith('--engine-root='))?.slice(14)||path.resolve(root,'../../engineCreate');
const qaBuildTimeout=Number(process.argv.find(v=>v.startsWith('--qa-build-timeout='))?.slice(19)||0);
assert(!qaBuildTimeout||(currentSource&&outputTag&&qaBuildTimeout>=60000&&qaBuildTimeout<=300000));
let hostFile=path.join(engineRoot,'tools/native-host.mjs');
if(qaBuildTimeout){
 // A local compiler deadline only. No SDK or shipped runtime is modified.
 let source=await fs.readFile(hostFile,'utf8');
 const deadline='performance.now()+nativeBuildTimeoutMs(generated.sourceFiles.length)';assert(source.includes(deadline));
 source=source.replace(deadline,`performance.now()+Math.max(${qaBuildTimeout},nativeBuildTimeoutMs(generated.sourceFiles.length))`);
 const rootExpression="path.resolve(import.meta.dirname,'..')";assert(source.includes(rootExpression));source=source.replace(rootExpression,JSON.stringify(engineRoot));
 source=source.replace(/from (['"])(\.\.?\/[^'"]+)\1/g,(_,q,relative)=>'from '+JSON.stringify(pathToFileURL(path.resolve(path.dirname(hostFile),relative)).href));
 source="import {appendFileSync as qaCompilerLog} from 'node:fs';\n"+source;
 const spawnNeedle='const child=spawn(compiler,args,{env,cwd,windowsHide:true});';assert(source.includes(spawnNeedle));source=source.replace(spawnNeedle,'qaCompilerLog('+JSON.stringify(path.join(work,'compiler-steps-'+(outputTag||'default')+'.jsonl'))+',JSON.stringify({time:Date.now(),args})+"\\n");'+spawnNeedle);
 await fs.mkdir(work,{recursive:true});hostFile=path.join(work,'qa-native-host-build-'+(outputTag||'default')+'.mjs');await fs.writeFile(hostFile,source);
}
const {NativeHost}=await import(pathToFileURL(hostFile));
const before=process.argv.includes('--before');
const activeRoots=process.argv.includes('--active-roots');assert(!(before&&activeRoots));
const freezeMain=process.argv.includes('--main-freeze');assert(!freezeMain||activeRoots);
const mainParts=process.argv.includes('--main-parts');assert(!mainParts||(activeRoots&&!freezeMain));
const gpuRigProbe=process.argv.includes('--gpu-rig-probe'),gpuProbe=gpuRigProbe||process.argv.includes('--gpu-probe');assert(!gpuProbe||(activeRoots&&!freezeMain&&!mainParts));
const liveOnly=process.argv.includes('--live-ui-only');assert(!liveOnly||(activeRoots&&!gpuProbe&&!freezeMain&&!mainParts));
const project=currentSource?(sourceRootArgument?path.resolve(root,sourceRootArgument):root):path.join(work,'frozen-project'),build=JSON.parse(await fs.readFile(buildResultArgument?path.resolve(root,buildResultArgument):currentSource?path.join(root,'build-result.json'):path.join(work,'build-result.json'),'utf8'));
const manifest=JSON.parse(await fs.readFile(path.join(build.output,'game.hbpack.json'),'utf8'));
const files=[];
for(const entry of await fs.readdir(path.join(project,'Source'),{withFileTypes:true})){
 assert(entry.isFile(),'Frozen game Source must be flat');
 const name='Source/'+entry.name,file=entry.name==='GlyphDisplayV4.hpp'&&!sourceRootArgument?path.join(root,name):path.join(project,name);
 files.push({path:name,content:await fs.readFile(file,'utf8')});
}
if(activeRoots){
 const current=await fs.readFile(path.join(root,'Source/V4Tasks.hpp'),'utf8'),frozen=files.find(f=>f.path==='Source/V4Tasks.hpp');
 const method=s=>{const start=s.indexOf('void Yumeno::v4TaskRoot('),end=s.indexOf('\nint Yumeno::v4TaskHp()',start);assert(start>=0&&end>start);return {start,end,text:s.slice(start,end)};};
 const old=method(frozen.content),next=method(current);frozen.content=frozen.content.slice(0,old.start)+next.text+frozen.content.slice(old.end);
 const runner=files.find(f=>f.path==='Source/TrialRunner.hpp'),needle=' auto& k=stageKind;';assert(runner.content.includes(needle));
 runner.content=runner.content.replace(needle,needle+'\n if(v4TaskActive)v4TaskRoot(!v4QueueActive);');
}
if(before){
 const h=files.find(f=>f.path==='Source/Yumeno.h'),cpp=files.find(f=>f.path==='Source/Yumeno.cpp');
 h.content=h.content.replace(/^#include "GlyphDisplayV4.hpp"\r?\n/m,'').replace(/^ glyphdisplayv4::Batch glyphDisplay;\r?\n/m,'');
 const start=cpp.content.indexOf('void Yumeno::drawGlyphs('),end=cpp.content.indexOf('\n// 줄이 바뀔 때',start);assert(start>0&&end>start);
 cpp.content=cpp.content.slice(0,start)+await fs.readFile(path.join(work,'drawGlyphs.before.cpp'),'utf8')+cpp.content.slice(end);
 files.splice(files.findIndex(f=>f.path==='Source/GlyphDisplayV4.hpp'),1);
}
if(freezeMain){
 const ui=files.find(f=>f.path==='Source/WidgetOwnersV4.hpp'),cpp=files.find(f=>f.path==='Source/Yumeno.cpp');
 ui.content=ui.content.replace('struct UI : hb::UI {','struct UI : hb::UI {\n inline static bool freezeMain=false;').replace(/(static void Set\w+[^\n]*\{)(hb::UI::)/g,'$1if(i=="main"&&freezeMain)return;$2');
 assert.equal((ui.content.match(/if\(i=="main"&&freezeMain\)return;/g)||[]).length,11);
 const needle=' sampleInput();++rhythmUpdates;';assert(cpp.content.includes(needle));cpp.content=cpp.content.replace(needle,needle+'\n if(mode==Mode::Trial&&pressed("F1"))UI::freezeMain=true;');
}
if(mainParts){
 files.find(f=>f.path==='Source/WidgetOwnersV4.hpp').content=await fs.readFile(path.join(work,'main-parts/WidgetOwnersV4.hpp'),'utf8');
 files.push({path:'Source/MainWidgetLayoutV4.hpp',content:await fs.readFile(path.join(work,'main-parts/MainWidgetLayoutV4.hpp'),'utf8')});
}
if(gpuProbe){
 files.find(f=>f.path==='Source/WidgetOwnersV4.hpp').content=await fs.readFile(path.join(work,gpuRigProbe?'gpu-rig-probe/WidgetOwnersV4.hpp':'gpu-probe/WidgetOwnersV4.hpp'),'utf8');
 const cpp=files.find(f=>f.path==='Source/Yumeno.cpp'),needle=' sampleInput();++rhythmUpdates;';assert(cpp.content.includes(needle));cpp.content=cpp.content.replace(needle,needle+'\n if(mode==Mode::Trial&&pressed("F1"))UI::Freeze();');
}
if(liveOnly){
 const ui=files.find(f=>f.path==='Source/WidgetOwnersV4.hpp');
 ui.content=ui.content.replace('struct UI : hb::UI {','struct UI : hb::UI {\n inline static bool liveOnly=false;\n static bool Dropped(const std::string& i){return liveOnly&&(i=="explore"||i=="flow"||i=="pad"||i=="v4story"||i=="titlemenuv4"||i=="stage"||i=="minev4"||i=="vote"||i=="debatefx"||i=="panicv4"||i=="comicv4"||i=="scrumv4"||i=="anagramv4"||i=="trialpickerv4"||i=="panes"||i=="intro");}').replace(/(static void Set\w+[^\n]*\{)(hb::UI::)/g,'$1if(Dropped(i))return;$2');
 assert.equal((ui.content.match(/if\(Dropped\(i\)\)return;/g)||[]).length,11);
 const cpp=files.find(f=>f.path==='Source/Yumeno.cpp'),needle=' sampleInput();++rhythmUpdates;';assert(cpp.content.includes(needle));
 cpp.content=cpp.content.replace(needle,needle+'\n if(mode==Mode::Trial&&pressed("F1")&&!UI::liveOnly){for(auto i:{"explore","flow","pad","v4story","titlemenuv4","stage","minev4","vote","debatefx","panicv4","comicv4","scrumv4","anagramv4","trialpickerv4","panes"})UI::Remove(this,i);UI::Remove(actor("IntroOwner"),"intro");UI::liveOnly=true;}');
}
if(sourceOverridesFile){for(const [name,file] of Object.entries(JSON.parse(await fs.readFile(sourceOverridesFile,'utf8')))){const target=files.find(f=>f.path===name);assert(target&&path.isAbsolute(file));target.content=await fs.readFile(file,'utf8');}}
if(diagnosticHostRate){const options=files.find(f=>f.path==='Source/OptionsV4.hpp'),from='state["runtimeSettings"]["frameRate"]=s.values.frameRate;';assert(options.content.includes(from));options.content=options.content.replace(from,'state["runtimeSettings"]["frameRate"]='+diagnosticHostRate+';');}
const header=files.find(f=>f.path==='Source/Yumeno.h').content,source=files.find(f=>f.path==='Source/Yumeno.cpp').content;
const host=new NativeHost();
try{
 const result=await host.build(header,source,{configuration:'development',files,headerPath:'Source/Yumeno.h',sourcePath:'Source/Yumeno.cpp'});
 assert.deepEqual(result.metadata,manifest.nativeModules[0].metadata,'Game API must match the completed package');
 const binary=path.join(work,outputTag?'game-'+outputTag+'.exe':currentSource?'game-blank-glyphs.exe':liveOnly?'game-live-ui-only.exe':gpuRigProbe?'game-gpu-rig-probe.exe':gpuProbe?'game-gpu-probe.exe':mainParts?'game-main-parts.exe':freezeMain?'game-main-freeze.exe':before?'game-glyph-before.exe':activeRoots?'game-active-roots.exe':'game-glyph-current.exe');await fs.copyFile(host.sessions.get(result.token).binary,binary);
 const helper=files.find(f=>f.path==='Source/GlyphDisplayV4.hpp')?.content||'';
 const receipt={binary,baseBuild:build.id,baseOutput:build.output,gameSourceOnly:true,engineModified:false,helperSHA256:createHash('sha256').update(helper).digest('hex'),binarySHA256:createHash('sha256').update(await fs.readFile(binary)).digest('hex'),sdk:result.sdk,sdkUsed:result.sdkUsed,cacheKey:result.cacheKey,scope:'Diagnostic game module against an unchanged completed flat package; not a full shipping build.'};
 if(qaBuildTimeout)receipt.qaCompilerDeadlineMS=qaBuildTimeout;
 if(sourceOverridesFile)receipt.sourceOverridesFile=path.resolve(sourceOverridesFile);
 if(currentSource){receipt.scope='Current game source against the identified unchanged packed package; candidate game module only, not a completed full build.';receipt.engineSDKRoot=engineRoot;receipt.sourceSHA256=Object.fromEntries(files.map(f=>[f.path,createHash('sha256').update(f.content).digest('hex')]));}
 if(diagnosticHostRate){receipt.diagnosticOnly=true;receipt.diagnosticHostRate=diagnosticHostRate;receipt.scope='DIAGNOSTIC ONLY: bound host240 instead of selected120 to separate raw throughput from frame pacing. All gameplay, original text/camera/timer/input and native surface remain active. Never ship or accept as the requested120 option.';}
 if(activeRoots)receipt.activeRootsSourceSHA256=createHash('sha256').update(files.find(f=>f.path==='Source/V4Tasks.hpp').content).digest('hex');
 if(freezeMain)receipt.scope='DIAGNOSTIC ONLY: F1 freezes Main display writes after normal trial entry. Gameplay/camera/timers continue. Never a shipping candidate or performance acceptance.';
 if(mainParts)receipt.mainPartsPlan=JSON.parse(await fs.readFile(path.join(work,'main-parts/plan.json'),'utf8'));
 if(gpuProbe)receipt.scope='DIAGNOSTIC ONLY: F1 freezes Main and substitutes glyph display with synthetic existing-texture GPU sprites. No shipping/performance acceptance.';
 if(liveOnly)receipt.scope='DIAGNOSTIC ONLY: F1 unmounts inactive non-debate widget trees. Main glyphs, timer, aim and actual game logic continue normally. Modal/other-stage restoration is not implemented in this cost test; never ship.';
 await fs.writeFile(path.join(work,outputTag?'game-module-'+outputTag+'.json':currentSource?'game-module-blank-glyphs.json':liveOnly?'game-module-live-ui-only.json':gpuRigProbe?'game-module-gpu-rig-probe.json':gpuProbe?'game-module-gpu-probe.json':mainParts?'game-module-main-parts.json':freezeMain?'game-module-main-freeze.json':before?'game-module-before.json':activeRoots?'game-module-active-roots.json':'game-module.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify({...receipt,sourceSHA256:undefined,mainPartsPlan:mainParts?{parts:receipt.mainPartsPlan.parts.length}:undefined}));
}finally{await host.close();}
