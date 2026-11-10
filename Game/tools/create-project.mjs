import {emitTrialEntryUI} from './v4-trial-entry-ui.mjs';
import {emitV4PhaseStartSource} from './v4-phase-start-source.mjs';
import {emitCenteredSourceCanvases} from './v4-centered-source-canvases.mjs';
import {emitPanicShowdownSource} from './v4-panic-showdown-source.mjs';
import {applyTrialDialogueResponsive} from './v3-trial-dialogue-source.mjs';
import {emitNonstopSourceHud} from './v4-nonstop-source-hud.mjs';
import {applyKotodamaFlight,applyKotodamaScene} from './v4-kotodama-flight.mjs';
import {emitNonstopRefuteSource} from './v4-nonstop-refute-source.mjs';
import {publishComicPagesOnly} from './v4-comic-data.mjs';
import {publishInspectionArtOnly} from './v4-inspection-art.mjs';
import {emitSpotVisuals,applySpotStage} from './v4-spot-ui.mjs';
import {emitParkLevels} from './v4-park-levels.mjs';
import {publishMineObjectsOnly} from './v4-mine-objects.mjs';
import {emitVoteUI,finalizeVoteTVUI} from './v4-vote-ui.mjs';
import {emitTrialInputMotionUI} from './v4-trial-input-motion-ui.mjs';
import {applyScrumProfiles} from './v4-scrum-profiles.mjs';
import {emitArmamentScene} from './v4-armament-scene.mjs';
import {emitArmamentPresentation,refreshArmamentWords} from './v4-armament-presentation.mjs';
import {emitArmamentText,applyArmamentInkNode} from './v4-armament-text.mjs';
import {resultForeground,lieWorldGrade,emitLieLookup,emitResultForegroundOnly,emitNonstopResultPalette} from './v4-debate-result-foreground.mjs';
import {publishEvidenceArtOnly} from './v4-data.mjs';
import {applyReasoningStage,emitReasoningVisuals} from './v4-reasoning-ui.mjs';
import {emitPodiumMaterialAtlas,emitCourtRoomMaterialAtlas} from './v4-podium-material-atlas.mjs';
import {emitSurfaceMaterials} from './v4-surface-materials.mjs';
import {emitMineV4,emitMineVisuals,applyMineStage} from './v4-mine-ui.mjs';
import {emitExtraV4} from './v4-extra-ui.mjs';
import {emitDifficultyV4} from './v4-difficulty-ui.mjs';
import {emitTrialVitals} from './v4-trial-vitals.mjs';
import {applyTrialHudStyle,emitTrialHudStyleOnly,emitTrialNameOnly,emitTrialTimerOnly} from './v4-trial-hud-style.mjs';
// 유메노쿠니 HBEngine 프로젝트 생성기 : 각본 데이터·스프라이트·UI·장면·블루프린트를 Assets/ 아래에 만든다.
// node tools/create-project.mjs   (엔진 원본은 ../engineCreate 를 읽기만 한다)
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {randomUUID} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {makeStarterScene} from '../engineCreate/prototype/scene-templates.js';
import {makeSceneComponent} from '../engineCreate/prototype/scene-components.js';
import {environmentActorPreset} from '../engineCreate/prototype/scene-environment.js';
import {createAsset} from '../engineCreate/prototype/asset-documents.js';
import {makeNode,connect} from '../engineCreate/prototype/blueprint-model.js';
import {parseNativeHeader} from '../engineCreate/prototype/native-model.js';
import {createWidgetAsset,createWidgetNode} from '../engineCreate/prototype/ui-assets.js';
import {emitOptionsV4} from '../../tools/v4_options_widget.mjs';
import {installV4StoryUI} from './v4-story-ui.mjs';
import {publishV4Data} from './v4-data.mjs';
import {publishRevisedCampaign} from './revised-campaign-data.mjs';
import {emitScrumClaims} from './claude-scrum-text.mjs';
import {emitV4ComicUI} from './v4-comic-ui.mjs';
import {emitV4ScrumUI} from './v4-scrum-ui.mjs';
import {emitV4AnagramUI} from './v4-anagram-ui.mjs';
import {emitV4PadEvidenceUI} from './v4-pad-evidence-ui.mjs';
import {emitV4PadGiftUI} from './v4-pad-gift-ui.mjs';
import {emitV4PadReportUI} from './v4-pad-report-ui.mjs';
import {emitV4PadSkillUI} from './v4-pad-skill-ui.mjs';
import {emitV4PadRulesUI} from './v4-pad-rules-ui.mjs';
import {emitV4PadSystemUI} from './v4-pad-system-ui.mjs';
import {emitV4PadSystemPages} from './v4-pad-system-pages.mjs';
import {emitV4PadMapUI} from './v4-pad-map-ui.mjs';
import {emitV4DialogueChoice} from './v4-dialogue-choice-ui.mjs';
import {emitV4DialogueWindow} from './v4-dialogue-window-ui.mjs';
import {emitV4ExplorationHud} from './v4-exploration-hud-ui.mjs';
import {emitTrialAnswerUI} from './v4-trial-answer-ui.mjs';
import {emitTrialPickerUI} from './v4-trial-picker-ui.mjs';
import {emitTrialResultUI} from './v4-trial-result-ui.mjs';
import {emitTitleChapterUI} from './v4-title-chapter-ui.mjs';
import {emitArmamentHud,applyArmamentTextStyle,ARMAMENT_PLAYER_RECT} from './v4-armament-hud.mjs';
import {emitRuntimeScenes} from './v4-runtime-scenes.mjs';
import {emitNonstopSolidType} from './v4-nonstop-solid-type.mjs';
import {emitGpuTrialAssets,emitNonstopFont} from './v4-gpu-trial-assets.mjs';
import {emitGpuPanicAssets} from './v4-gpu-panic-assets.mjs';
import {emitGpuAnagramAssets} from './v4-gpu-anagram-assets.mjs';
import {emitGpuStageClock} from './v4-gpu-stage-clock.mjs';
import {emitGpuShowdownAssets} from './v4-gpu-showdown-assets.mjs';
import {emitScopedCourtScenes,emitPanicNoiseScope} from './v4-scoped-court-scenes.mjs';
import {emitGpuNoiseAssets} from './v4-gpu-noise-assets.mjs';
import {emitPanicCacheScene} from './v4-panic-cache-scenes.mjs';
import {applyExplorationMaterialLight} from './v4-exploration-material-light.mjs';

const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const repo=path.dirname(root);
let resultPlaneDefinitions=[];
const write=async(name,data)=>{
 const file=path.join(root,name),temporary=file+'.'+randomUUID()+'.tmp';await fs.mkdir(path.dirname(file),{recursive:true});
 const bytes=Buffer.isBuffer(data)?data:Buffer.from(typeof data==='string'?data:JSON.stringify(data,null,1)+'\n');
 const unchanged=async()=>fs.readFile(file).then(old=>old.equals(bytes),error=>{if(error.code==='ENOENT')return false;throw error;});
 if(await unchanged())return;
 // Publish complete files without opening an existing OneDrive-managed JSON for truncation.
 try{await fs.writeFile(temporary,bytes);for(let attempt=0;;attempt++){try{await fs.rename(temporary,file);break;}catch(error){if(!['EBUSY','EPERM','EACCES','UNKNOWN'].includes(error.code)||attempt>=5)throw error;if(await unchanged())break;await new Promise(resolve=>setTimeout(resolve,100*(attempt+1)));}}}
 finally{await fs.rm(temporary,{force:true});}
};
async function emitNativeHuds(){
 await emitPanicShowdownSource({write});
 console.log(JSON.stringify({gpuTrialHud:await emitGpuTrialAssets({output:root,source:root,write})}));
 for(const [key,emit] of [['gpuPanicHud',emitGpuPanicAssets],['gpuAnagramHud',emitGpuAnagramAssets],['gpuStageClock',emitGpuStageClock],['gpuShowdownHud',emitGpuShowdownAssets],['scopedCourt',emitScopedCourtScenes],['gpuNoiseHud',emitGpuNoiseAssets],['gpuPanicCache',emitPanicCacheScene]])console.log(JSON.stringify({[key]:await emit({output:root,write})}));
 console.log(JSON.stringify({armamentPresentation:await emitArmamentPresentation({write})}));
}
if(process.argv.includes('--trial-entry-only')){
 await emitTrialEntryUI({write});
 const panic='Assets/Scenes/PanicHud.hbscene.json';
 const read=async name=>JSON.parse(await fs.readFile(path.join(root,name),'utf8'));
 await write(panic,applyKotodamaScene(await read(panic),await read('Assets/Scenes/DebateHud.hbscene.json')));
 process.exit(0);
}
if(process.argv.includes('--armament-words-only')){console.log(JSON.stringify(await refreshArmamentWords({write,read:async file=>JSON.parse(await fs.readFile(path.join(root,file),'utf8'))})));process.exit(0);}
if(process.argv.includes('--armament-ui-only')){execFileSync('python',['-X','utf8',path.join(repo,'tools/build_v3_armament_charts.py')],{stdio:'inherit'});await emitArmamentScene(JSON.parse(await fs.readFile(path.join(root,'Assets/Scenes/Court.hbscene.json'),'utf8')),write);console.log(JSON.stringify(await emitArmamentPresentation({write})));process.exit(0);}
if(process.argv.includes('--trial-input-motion-only')){const bank=await emitTrialInputMotionUI({repo,write,read:async file=>JSON.parse(await fs.readFile(path.join(root,file),'utf8'))});await finalizeVoteTVUI({repo,write,read:async file=>JSON.parse(await fs.readFile(path.join(root,file),'utf8'))});console.log(JSON.stringify({trialInputMotionOnly:true,widgets:bank.widgets,storyChanged:false}));process.exit(0);}
if(process.argv.includes('--gpu-huds-only')){await emitNativeHuds();
await emitNonstopSourceHud({repo,root,write});console.log(JSON.stringify({gpuHudsOnly:true,storyChanged:false}));process.exit(0);}
if(process.argv.includes('--revised-campaign-runtime-only')){
 console.log(JSON.stringify({revisedCampaign:await publishRevisedCampaign({repo,write,runtimeSource:root})}));process.exit(0);
}
if(process.argv.includes('--park-levels-only')){console.log(JSON.stringify(await emitParkLevels({root,repo,write})));process.exit(0);}
if(process.argv.includes('--mine-objects-only')){console.log(JSON.stringify(await publishMineObjectsOnly({root,repo,write})));process.exit(0);}
if(process.argv.includes('--nonstop-source-hud-only')){console.log(JSON.stringify(await emitNonstopSourceHud({repo,root,write})));process.exit(0);}
if(process.argv.includes('--anagram-ui-only')){await emitV4AnagramUI({write,body:'Assets/Fonts/pretendard/Pretendard-Medium.otf',head:'Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf'});console.log(JSON.stringify(await emitGpuAnagramAssets({output:root,write})));process.exit(0);}
if(process.argv.includes('--mine-ui-only')){const assets=[];await emitMineVisuals({write:async(name,data)=>{await write(name,data);assets.push(name);}});await emitMineV4({write:async(name,data)=>{await write(name,data);assets.push(name);}});const name='Assets/UI/Stage.hbwidget.json',widget=applyMineStage(JSON.parse(await fs.readFile(path.join(root,name),'utf8')));await write(name,widget);assets.push(name);console.log(JSON.stringify({mineUiOnly:true,nodes:widget.nodes.length,assets,storyChanged:false}));process.exit(0);}
if(process.argv.includes('--trial-picker-ui-only')){const assets=[];const widget=await emitTrialPickerUI({repo,write:async(name,data)=>{await write(name,data);assets.push(name);},body:'Assets/Fonts/pretendard/Pretendard-Medium.otf',head:'Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf'});console.log(JSON.stringify({trialPickerUiOnly:true,nodes:widget.nodes.length,assets,storyChanged:false,scope:'Current supplied PNG bytes/affine retained, native SVG black-matte alpha adapter only; not a recovered source blend equation.'}));process.exit(0);}
if(process.argv.includes('--vote-ui-only')){const widget=await emitVoteUI({write,body:'Assets/Fonts/pretendard/Pretendard-Medium.otf',head:'Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf'});await emitTrialInputMotionUI({repo,write});await finalizeVoteTVUI({repo,write,read:async file=>JSON.parse(await fs.readFile(path.join(root,file),'utf8'))});console.log(JSON.stringify({voteUiOnly:true,nodes:widget.nodes.length,storyChanged:false}));process.exit(0);}
if(process.argv.includes('--armament-scene-only')){console.log(JSON.stringify(await emitArmamentScene(JSON.parse(await fs.readFile(path.join(root,'Assets/Scenes/Court.hbscene.json'),'utf8')),write)));process.exit(0);}
if(process.argv.includes('--armament-text-only')){const name='Assets/UI/Stage.hbwidget.json';await write(name,applyArmamentInkNode(applyArmamentTextStyle(JSON.parse(await fs.readFile(path.join(root,name),'utf8')))));console.log(JSON.stringify(await emitArmamentText({write})));process.exit(0);}
if(process.argv.includes('--comic-pages-only')){console.log(JSON.stringify(await publishComicPagesOnly({repo,root,write})));process.exit(0);}
if(process.argv.includes('--inspection-art-only')){console.log(JSON.stringify(await publishInspectionArtOnly({repo,root,write})));process.exit(0);}
if(process.argv.includes('--spot-ui-only')){await emitSpotVisuals({write});const file='Assets/UI/Stage.hbwidget.json';await write(file,applySpotStage(JSON.parse(await fs.readFile(path.join(root,file),'utf8'))));console.log(JSON.stringify({spotUiOnly:true,source:'official V3 manual p15',newNodes:0}));process.exit(0);}
if(process.argv.includes('--comic-ui-only')){console.log(JSON.stringify(await emitV4ComicUI({write,body:'Assets/Fonts/pretendard/Pretendard-Medium.otf',head:'Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf'})));process.exit(0);}
if(process.argv.includes('--trial-result-ui-only')){
 await emitTrialResultUI({repo,write,body:'Assets/Fonts/pretendard/Pretendard-Medium.otf'});
 process.exit(0);
}
if(process.argv.includes('--result-ink-only')){
 const folder=path.join(repo,'ui/v4/debate_feedback');
 for(const name of await fs.readdir(folder))if(/^result_(refute|agree|lie)_break[0-4]\.svg$/.test(name))await write('Assets/Art/ui/'+name,await fs.readFile(path.join(folder,name)));
 process.exit(0);
}
if(process.argv.includes('--debate-fx-only')){console.log(JSON.stringify(await emitResultForegroundOnly({root,repo,write})));process.exit(0);}
if(process.argv.includes('--evidence-art-only')){console.log(JSON.stringify(await publishEvidenceArtOnly({repo,write})));process.exit(0);}
if(process.argv.includes('--scrum-profiles-only')){const name='Assets/Data/court.json',court=JSON.parse(await fs.readFile(path.join(root,name),'utf8'));court.scrumFaces=await applyScrumProfiles({repo,write,figures:court.figures});await write(name,court);console.log(JSON.stringify({scrumProfilesOnly:true,keys:Object.keys(court.scrumFaces)}));process.exit(0);}
if(process.argv.includes('--scrum-ui-only')){const w=await emitV4ScrumUI({write,body:'Assets/Fonts/pretendard/Pretendard-Medium.otf',head:'Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf'});console.log(JSON.stringify({scrumUiOnly:true,nodes:w.nodes.length,storyChanged:false}));process.exit(0);}
if(process.argv.includes('--reasoning-ui-only')){
 await emitReasoningVisuals({write});const file='Assets/UI/Stage.hbwidget.json';await write(file,applyReasoningStage(JSON.parse(await fs.readFile(path.join(root,file),'utf8'))));console.log(JSON.stringify({reasoningUiOnly:true,storyChanged:false}));process.exit(0);
}
if(process.argv.includes('--trial-glyph-fonts-only')){
 const groups={'Stage':['AccArrows','AccArrowR'],'ComicV4':['PageLeft','PageRight'],'ScrumV4':['ScVKey']};
 for(const [widget,ids] of Object.entries(groups)){const name=`Assets/UI/${widget}.hbwidget.json`,data=JSON.parse(await fs.readFile(path.join(root,name),'utf8'));for(const id of ids){const node=data.nodes.find(n=>n.id===id);if(!node)throw Error('Missing font correction node '+id);node.properties.font='Assets/Fonts/pretendard/Pretendard-Medium.otf';}await write(name,data);}
 console.log(JSON.stringify({trialGlyphFontsOnly:true,nodes:5,storyChanged:false}));process.exit(0);
}
if(process.argv.includes('--trial-hud-only')){console.log(JSON.stringify(await emitTrialHudStyleOnly({repo,root,write})));process.exit(0);}
if(process.argv.includes('--trial-timer-only')){console.log(JSON.stringify(await emitTrialTimerOnly({root,write})));process.exit(0);}
if(process.argv.includes('--trial-name-only')){console.log(JSON.stringify(await emitTrialNameOnly({repo,root,write})));process.exit(0);}
// Fullscreen title art covers the client area while controls keep fit coordinates.
function stretchTitleBackdrop(widget){for(const id of ['Title','TitleBg']){const node=widget.nodes.find(n=>n.id===id);if(!node)throw Error('Missing title backdrop '+id);node.slot.anchors=[0,0,1,1];node.slot.offset=[0,0,0,0];}}
if(process.argv.includes('--title-background-only')){const file=path.join(root,'Assets/UI/Main.hbwidget.json'),widget=JSON.parse(await fs.readFile(file,'utf8'));stretchTitleBackdrop(widget);await write('Assets/UI/Main.hbwidget.json',widget);console.log(JSON.stringify({titleBackdropOnly:true}));process.exit(0);}
if(process.argv.includes('--noise-waves-only')){console.log(JSON.stringify({gpuNoiseHud:await emitGpuNoiseAssets({output:root,write})}));process.exit(0);}
if(process.argv.includes('--panic-noise-only')){console.log(JSON.stringify(await emitPanicNoiseScope({output:root,write})));process.exit(0);}
if(process.argv.includes('--panic-cache-only')){console.log(JSON.stringify(await emitPanicCacheScene({output:root,write})));process.exit(0);}
if(process.argv.includes('--dialogue-only')){await emitV4DialogueWindow({repo,write});const main=path.join(root,'Assets/UI/Main.hbwidget.json');try{await write('Assets/UI/Main.hbwidget.json',applyTrialDialogueResponsive(JSON.parse(await fs.readFile(main,'utf8'))));}catch(error){if(error.code!=='ENOENT')throw error;}console.log(JSON.stringify({dialogueOnly:true}));process.exit(0);}
if(process.argv.includes('--sculpted-environment-only')){
 const catalog=JSON.parse(await fs.readFile(path.join(repo,'art/space_v4/sculpted_v1/manifest.json'),'utf8'));
 const copies=JSON.parse(await fs.readFile(path.join(repo,'art/space_v4/runtime_v1/copy_manifest.json'),'utf8'));
 for(const asset of catalog.assets){await write(asset.runtime,await fs.readFile(path.join(repo,asset.file)));const row=copies.find(r=>r.to===asset.runtime);if(!row)throw Error('Unregistered sculpted model '+asset.runtime);row.from=asset.file;}
 await fs.writeFile(path.join(repo,'art/space_v4/runtime_v1/copy_manifest.json'),JSON.stringify(copies,null,1)+'\n');
 const file='Assets/Scenes/Explore.hbscene.json';await write(file,applyExplorationMaterialLight(JSON.parse(await fs.readFile(path.join(root,file),'utf8'))));
 const surfaces=await emitSurfaceMaterials({repo,write});console.log(JSON.stringify({sculptedEnvironmentOnly:true,renderAssets:catalog.assets.length,surfaces,gameplayMetadataUnchanged:true}));process.exit(0);
}
if(process.argv.includes('--surface-materials-only')){
 const result=await emitSurfaceMaterials({repo,write});
 const scene='Assets/Scenes/Explore.hbscene.json';await write(scene,applyExplorationMaterialLight(JSON.parse(await fs.readFile(path.join(root,scene),'utf8'))));
 console.log(JSON.stringify({...result,celestialShadowAlignment:true}));process.exit(0);
}
if(process.argv.includes('--exterior-finish-only')){
 const sculpted=await fs.readFile(path.join(repo,'art/space_v4/sculpted_v1/manifest.json'),'utf8').then(JSON.parse,e=>{if(e.code!=='ENOENT')throw e;return null;});
 if(sculpted){const assets=sculpted.assets.filter(a=>a.runtime.includes('/finish_'));for(const asset of assets)await write(asset.runtime,await fs.readFile(path.join(repo,asset.file)));console.log(JSON.stringify({exteriorFinishOnly:true,renderChunks:assets.length,sculpted:true,gameplayMetadataUnchanged:true}));process.exit(0);}
 const catalog=JSON.parse(await fs.readFile(path.join(repo,'art/space_v4/architecture_finish_v2/manifest.json'),'utf8'));
 for(const asset of [catalog.context,...Object.values(catalog.landmarks)])await write(asset.runtime,await fs.readFile(path.join(repo,asset.file)));
 console.log(JSON.stringify({exteriorFinishOnly:true,renderChunks:1+Object.keys(catalog.landmarks).length,gameplayMetadataUnchanged:true}));process.exit(0);
}
if(process.argv.includes('--gpu-trial-finalize')){
 // Resume the completed generation after font optimization, without replaying art exports.
 execFileSync('python',['-X','utf8',path.join(repo,'tools/optimize_assets.py')],{stdio:'inherit',windowsHide:true});
 const layout=JSON.parse(await fs.readFile(path.join(root,'Assets/Data/gpu_trial_layout.json'),'utf8')),widget=JSON.parse(await fs.readFile(path.join(root,'Assets/UI/Main.hbwidget.json'),'utf8')),parents=new Map(layout.parents.map(n=>[n.id,n]));
 for(const n of widget.nodes)if(/^(M[FB]|MS|N[FB])\d+$/.test(n.id)||['Aim','TimerPanel','Timer','CourtDim'].includes(n.id))n.properties.visible=parents.get(n.id).visible;
 const court=JSON.parse(await fs.readFile(path.join(root,'Assets/Scenes/Court.hbscene.json'),'utf8'));court.objects=court.objects.filter(o=>!o.id.startsWith('TrialGpu_')&&!o.id.startsWith('TrialBatch_'));
 await write('Assets/UI/Main.hbwidget.json',widget);await write('Assets/Scenes/Court.hbscene.json',court);
 console.log(JSON.stringify({gpuTrialHud:await emitGpuTrialAssets({output:root,source:root,write}),gpuPanicHud:await emitGpuPanicAssets({output:root,write}),gpuAnagramHud:await emitGpuAnagramAssets({output:root,write}),gpuStageClock:await emitGpuStageClock({output:root,write}),gpuShowdownHud:await emitGpuShowdownAssets({output:root,write}),scopedCourt:await emitScopedCourtScenes({output:root,write}),gpuNoiseHud:await emitGpuNoiseAssets({output:root,write}),gpuPanicCache:await emitPanicCacheScene({output:root,write}),resumed:true}));process.exit(0);
}
// Rebuild only scene ownership from the generated authored object rows.
if(process.argv.includes('--runtime-scenes-only')){
 const court=JSON.parse(await fs.readFile(path.join(root,'Assets/Scenes/Court.hbscene.json'),'utf8')),explore=JSON.parse(await fs.readFile(path.join(root,'Assets/Scenes/Explore.hbscene.json'),'utf8'));
 const skip=o=>o.id==='SceneRoot'||o.id.endsWith('Scene')||o.id.startsWith('UI_');
 court.objects=[...court.objects.filter(o=>!skip(o)),...explore.objects.filter(o=>!skip(o)&&o.id!=='Camera'&&!/^Court(?:Ambient|Key|Fill)$/.test(o.id))];
 for(const o of court.objects)if(o.parent==='SceneRoot')delete o.parent;
 console.log(JSON.stringify(await emitRuntimeScenes(court,write)));
 const project=JSON.parse(await fs.readFile(path.join(root,'YumenoKuni.hbproject'),'utf8'));project.gameInstance='Assets/Blueprints/BP_Yumeno.hbblueprint.json';await write('YumenoKuni.hbproject',project);process.exit(0);
}
// Refresh only native metadata after C++ edits; keep authored assets and graph IDs.
if(process.argv.includes('--native-source-only')){
 const file=path.join(root,'Assets/Blueprints/BP_Yumeno.hbblueprint.json'),bp=JSON.parse(await fs.readFile(file,'utf8'));
 if(bp.settings.parentClass!=='Yumeno'||!bp.native)throw Error('Existing Yumeno blueprint required');
 const header=await fs.readFile(path.join(root,'Source/Yumeno.h'),'utf8'),source=await fs.readFile(path.join(root,'Source/Yumeno.cpp'),'utf8');
 bp.native={...parseNativeHeader(header),header,source,headerPath:'Source/Yumeno.h',sourcePath:'Source/Yumeno.cpp'};
 await write('Assets/Blueprints/BP_Yumeno.hbblueprint.json',bp);console.log(JSON.stringify({nativeSourceOnly:true,graphIDsPreserved:true}));await emitNonstopRefuteSource({write});process.exit(0);
}
const copy=async(from,to)=>{await fs.mkdir(path.dirname(path.join(root,to)),{recursive:true});await fs.copyFile(path.join(repo,from),path.join(root,to));};
if(process.argv.includes('--trial-direction-only')){
 const direction=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/trial_direction.json'),'utf8'));
 await emitNonstopResultPalette(repo,write);await emitNonstopRefuteSource({write});
 await write('Assets/Data/v4_story/trial_direction.json',direction);console.log(JSON.stringify(await emitNonstopFont({output:root,write,direction})));console.log(JSON.stringify(await emitNonstopSolidType({output:root,write})));process.exit(0);
}
if(process.argv.includes('--story-only')){
 await publishV4Data({repo,copy,write});
 console.log(JSON.stringify({storyOnly:true,sceneOwnershipPreserved:true,artRegenerated:false}));process.exit(0);
}
if(process.argv.includes('--revised-campaign-only')){
 const folder=process.argv.find(arg=>arg.startsWith('--preview-content='))?.slice(18)||'content';
 if(!/^[a-z][a-z0-9-]*$/.test(folder))throw Error('Invalid revised preview folder');
 const writePreview=(name,data)=>write('Saved/campaign-revision/'+folder+'/'+name,data);
 console.log(JSON.stringify(await publishRevisedCampaign({repo,write:writePreview})));process.exit(0);
}

// Authored V4 spaces and the user's visually reviewed supplied UI components.
execFileSync('python',['-X','utf8',path.join(repo,'tools/build_v4_exploration.py')],{stdio:'inherit'});
const exploreRoot='art/space_v4/runtime_v1';
for(const c of JSON.parse(await fs.readFile(path.join(repo,exploreRoot,'copy_manifest.json'),'utf8')))await copy(c.from,c.to);
await copy(exploreRoot+'/world.json','Assets/Data/explore_world.json');
const suppliedUi=JSON.parse(await fs.readFile(path.join(repo,'ui/v3_authorized/manifest.json'),'utf8'));
for(const c of Object.values(suppliedUi.components))await copy(c.file,c.runtime);
const suppliedPad=JSON.parse(await fs.readFile(path.join(repo,'ui/v3_authorized/pad_home/manifest.json'),'utf8'));
for(const c of suppliedPad.files)await copy(c.file,c.runtime);

// 1) 각본 데이터 : data/scenes/{접두}_*.json → Assets/Data/scenes/{접두}.json
const sceneFiles=(await fs.readdir(path.join(repo,'data/scenes'))).filter(f=>f.endsWith('.json')).sort();
// source(원본 .md 이름)는 엔진 빌드가 파일 참조로 읽으므로 뺀다
for(const f of sceneFiles){const {source,...data}=JSON.parse(await fs.readFile(path.join(repo,'data/scenes',f),'utf8'));await write('Assets/Data/scenes/'+f.split('_')[0]+'.json',data);}
await write('Assets/Data/emotion.json',JSON.parse(await fs.readFile(path.join(repo,'data/emotion_map.json'),'utf8')));
// 진행 순서 : 프롤로그부터 (장이 늘면 여기 추가). 재판 : data/trials (tools/build_trial.py)
await write('Assets/Data/story.json',{chapters:['P','1','2','3','4','5','6'],trials:['11c','12c'],dead:{'11c':['taiga'],'12c':['taiga','sho','yuu']}});
// 장 진행표 (tools/build_flow.py) · 선물 · 언령 이름
for(const f of (await fs.readdir(path.join(repo,'data/flow'))).filter(f=>f.endsWith('.json')))await copy('data/flow/'+f,'Assets/Data/flow/'+f);
await copy('data/gifts.json','Assets/Data/gifts.json');await copy('data/hotspots.json','Assets/Data/hotspots.json');await copy('data/skills.json','Assets/Data/skills.json');await copy('data/reactions.json','Assets/Data/reactions.json');
await copy('data/kotodama.json','Assets/Data/kotodama.json'); // 이름·설명 : tools/build_trial.py · build_flow.py
for(const file of ['showdown_extra.json','showdown_pre.json','scrum_v3.json'])await copy('data/'+file,'Assets/Data/'+file);
for(const f of (await fs.readdir(path.join(repo,'data/trials'))).filter(f=>f.endsWith('.json')))await copy('data/trials/'+f,'Assets/Data/trials/'+f);

// 2) 교칙 : docs/spec/11 §2·§3 표
const rulesDoc=await fs.readFile(path.join(repo,'docs/spec/11_래피패드_교칙.md'),'utf8');
const rules=[...rulesDoc.matchAll(/^\| (교칙 \d+|[1-6]장) \| ([^|]+) \|/gm)].map(m=>({no:m[1],text:m[2].trim().replace(/\*\*/g,'')}));
await write('Assets/Data/rules.json',{rules});

// 3) 그림 : 스프라이트(WebP)·UI·글꼴 복사
// 스프라이트는 1024²로 줄여 넣는다(텍스처 메모리) : tools/game_sprites.py
execFileSync('python',[path.join(repo,'tools/game_sprites.py')],{stdio:'inherit'});
for(const f of ['dialog/frame.png','dialog/nameplate.png','trial/heart_full.png','trial/heart_empty.png','trial/cutin_objection.png','trial/focus_track.png','trial/focus_fill.png','trial/bullet_cylinder.png'])await copy('ui/'+f,'Assets/Art/ui/'+path.basename(f));
await write('Assets/Art/ui/aim.svg','<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><circle cx="32" cy="32" r="22" fill="none" stroke="#ff4fa3" stroke-width="4"/><circle cx="32" cy="32" r="3" fill="#ffffff"/><path d="M32 2v14M32 48v14M2 32h14M48 32h14" stroke="#ffffff" stroke-width="3"/></svg>');
await write('Assets/Art/ui/whip.svg','<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"><defs><linearGradient id="v" x2="1"><stop offset="0" stop-color="#ff4fa3" stop-opacity=".35"/><stop offset=".5" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#36c6e0" stop-opacity=".35"/></linearGradient></defs><rect width="1280" height="720" fill="url(#v)"/><rect x="463" y="154" width="664" height="2" fill="#ffffff" opacity="0.25"/><rect x="897" y="96" width="634" height="2" fill="#ffffff" opacity="0.4"/><rect x="-124" y="88" width="704" height="6" fill="#ffffff" opacity="0.25"/><rect x="292" y="92" width="824" height="6" fill="#ffffff" opacity="0.25"/><rect x="958" y="126" width="488" height="2" fill="#ffffff" opacity="0.8"/><rect x="-99" y="226" width="307" height="3" fill="#ffffff" opacity="0.6"/><rect x="658" y="147" width="813" height="2" fill="#ffffff" opacity="0.6"/><rect x="947" y="698" width="445" height="2" fill="#ffffff" opacity="0.4"/><rect x="562" y="99" width="820" height="2" fill="#ffffff" opacity="0.25"/><rect x="1067" y="210" width="768" height="6" fill="#ffffff" opacity="0.6"/><rect x="753" y="599" width="724" height="4" fill="#ffffff" opacity="0.6"/><rect x="308" y="184" width="509" height="2" fill="#ffffff" opacity="0.6"/><rect x="875" y="506" width="611" height="6" fill="#ffffff" opacity="0.6"/><rect x="1047" y="74" width="380" height="6" fill="#ffffff" opacity="0.4"/><rect x="500" y="155" width="760" height="6" fill="#ffffff" opacity="0.25"/><rect x="1168" y="79" width="831" height="4" fill="#ffffff" opacity="0.6"/><rect x="1223" y="358" width="868" height="6" fill="#ffffff" opacity="0.8"/><rect x="-60" y="95" width="536" height="6" fill="#ffffff" opacity="0.25"/><rect x="-76" y="718" width="577" height="6" fill="#ffffff" opacity="0.6"/><rect x="1267" y="395" width="615" height="2" fill="#ffffff" opacity="0.8"/><rect x="527" y="172" width="885" height="2" fill="#ffffff" opacity="0.8"/><rect x="-80" y="223" width="554" height="3" fill="#ffffff" opacity="0.4"/><rect x="614" y="400" width="768" height="2" fill="#ffffff" opacity="0.4"/><rect x="719" y="411" width="822" height="4" fill="#ffffff" opacity="0.4"/><rect x="681" y="563" width="545" height="6" fill="#ffffff" opacity="0.6"/><rect x="1198" y="389" width="496" height="3" fill="#ffffff" opacity="0.25"/><rect x="160" y="154" width="497" height="3" fill="#ffffff" opacity="0.25"/><rect x="793" y="603" width="446" height="4" fill="#ffffff" opacity="0.6"/><rect x="-192" y="149" width="689" height="4" fill="#ffffff" opacity="0.6"/><rect x="57" y="707" width="787" height="2" fill="#ffffff" opacity="0.8"/><rect x="1193" y="572" width="661" height="6" fill="#ffffff" opacity="0.8"/><rect x="607" y="106" width="753" height="6" fill="#ffffff" opacity="0.25"/><rect x="190" y="68" width="473" height="6" fill="#ffffff" opacity="0.4"/><rect x="25" y="348" width="875" height="2" fill="#ffffff" opacity="0.25"/><rect x="-200" y="580" width="414" height="2" fill="#ffffff" opacity="0.6"/><rect x="1056" y="26" width="332" height="3" fill="#ffffff" opacity="0.8"/><rect x="104" y="649" width="518" height="4" fill="#ffffff" opacity="0.6"/><rect x="771" y="125" width="378" height="6" fill="#ffffff" opacity="0.8"/><rect x="783" y="495" width="579" height="2" fill="#ffffff" opacity="0.4"/><rect x="9" y="350" width="531" height="6" fill="#ffffff" opacity="0.4"/><rect x="857" y="23" width="470" height="4" fill="#ffffff" opacity="0.4"/><rect x="1213" y="556" width="287" height="4" fill="#ffffff" opacity="0.25"/><rect x="1225" y="267" width="790" height="4" fill="#ffffff" opacity="0.4"/><rect x="528" y="228" width="805" height="4" fill="#ffffff" opacity="0.4"/><rect x="1055" y="199" width="505" height="6" fill="#ffffff" opacity="0.4"/><rect x="209" y="530" width="764" height="4" fill="#ffffff" opacity="0.25"/><rect x="-143" y="286" width="743" height="4" fill="#ffffff" opacity="0.4"/><rect x="1218" y="619" width="612" height="6" fill="#ffffff" opacity="0.6"/><rect x="546" y="82" width="485" height="2" fill="#ffffff" opacity="0.4"/><rect x="762" y="201" width="605" height="3" fill="#ffffff" opacity="0.8"/><rect x="1078" y="624" width="261" height="6" fill="#ffffff" opacity="0.6"/><rect x="1117" y="86" width="382" height="6" fill="#ffffff" opacity="0.4"/><rect x="779" y="182" width="704" height="4" fill="#ffffff" opacity="0.25"/><rect x="1278" y="405" width="734" height="6" fill="#ffffff" opacity="0.25"/><rect x="125" y="174" width="390" height="2" fill="#ffffff" opacity="0.4"/><rect x="1009" y="476" width="409" height="6" fill="#ffffff" opacity="0.6"/><rect x="119" y="561" width="821" height="3" fill="#ffffff" opacity="0.25"/><rect x="-171" y="665" width="365" height="3" fill="#ffffff" opacity="0.8"/><rect x="198" y="216" width="288" height="4" fill="#ffffff" opacity="0.4"/><rect x="399" y="513" width="506" height="4" fill="#ffffff" opacity="0.6"/><rect x="914" y="429" width="394" height="2" fill="#ffffff" opacity="0.6"/><rect x="738" y="678" width="857" height="6" fill="#ffffff" opacity="0.4"/><rect x="889" y="155" width="796" height="2" fill="#ffffff" opacity="0.8"/><rect x="175" y="623" width="264" height="3" fill="#ffffff" opacity="0.4"/><rect x="89" y="484" width="893" height="2" fill="#ffffff" opacity="0.25"/><rect x="467" y="698" width="790" height="6" fill="#ffffff" opacity="0.25"/><rect x="947" y="58" width="514" height="3" fill="#ffffff" opacity="0.6"/><rect x="-114" y="100" width="779" height="6" fill="#ffffff" opacity="0.25"/><rect x="-71" y="453" width="593" height="3" fill="#ffffff" opacity="0.6"/><rect x="726" y="520" width="806" height="6" fill="#ffffff" opacity="0.4"/></svg>'); // 휩 팬 속도선(V3 화자 전환)
await write('Assets/Art/ui/vpoint.svg','<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22"><circle cx="11" cy="11" r="9" fill="#ff2040" stroke="#ffffff" stroke-width="2"/></svg>');

// V3 논의 렌즈 : 가운데 투명, 가장자리 어둡게 + 동심원 + 흰·빨강 사각 조각 (docs/spec/16 §5-2)
await write('Assets/Art/ui/lens.svg','<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"><defs><radialGradient id="v" cx="50%" cy="50%" r="62%"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#05020a" stop-opacity=".92"/></radialGradient><mask id="hud"><rect width="1280" height="720" fill="#fff"/><rect x="926" y="636" width="350" height="80" rx="6" fill="#000"/><rect x="928" y="10" width="350" height="132" rx="6" fill="#000"/></mask></defs><rect width="1280" height="720" fill="url(#v)" mask="url(#hud)"/>'+[360,430,520].map((r,i)=>`<circle cx="640" cy="360" r="${r}" fill="none" stroke="#ffffff" stroke-opacity="${.22-i*.05}" stroke-width="${2+i}"/>`).join('')+[[40,70,34,'#fff'],[88,150,22,'#d81f2a'],[1180,120,30,'#fff'],[1210,200,44,'#d81f2a'],[60,520,26,'#fff'],[1150,560,20,'#fff'],[130,610,40,'#d81f2a'],[1220,470,24,'#fff']].map(([x,y,w,c])=>`<rect x="${x}" y="${y}" width="${w}" height="${w}" fill="none" stroke="${c}" stroke-opacity=".7" stroke-width="3"/><rect x="${x+6}" y="${y+6}" width="${w-12}" height="${w-12}" fill="${c}" fill-opacity=".35"/>`).join('')+'</svg>');
for(const [k,t,c] of [['nonstop','NON-STOP DEBATE','#ffe36e'],['panic','MASS PANIC DEBATE','#ff4fa3']])await write(`Assets/Art/ui/start_${k}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="200"><path d="M0 40L1280 0V160L0 200Z" fill="#0b0812" fill-opacity=".9"/><path d="M0 40L1280 0M0 200L1280 160" stroke="${c}" stroke-width="6"/><text x="640" y="128" text-anchor="middle" font-family="Arial Black,Arial" font-weight="900" font-style="italic" font-size="96" fill="#ffffff" stroke="${c}" stroke-width="4" transform="rotate(-1.8 640 100)">${t}</text></svg>`);
const hudSvg={
 name:'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="80"><path d="M28 6H414L392 74H6Z" fill="#0b1018" fill-opacity=".82" stroke="#36e3ff" stroke-width="2"/><path d="M40 12H300" stroke="#36e3ff" stroke-opacity=".6"/>'+Array.from({length:9},(_,i)=>`<circle cx="${48+i*12}" cy="62" r="2.6" fill="#ffffff" fill-opacity="${.9-i*.08}"/>`).join('')+'</svg>',
 status:'<svg xmlns="http://www.w3.org/2000/svg" width="330" height="116"><path d="M40 4H326L292 112H6Z" fill="#0b1018" fill-opacity=".8" stroke="#36e3ff" stroke-width="2"/><path d="M52 30H306" stroke="#ffffff" stroke-opacity=".35"/></svg>',
 bullet:'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="50"><path d="M18 3H417L402 47H3Z" fill="#0b1018" fill-opacity=".85" stroke="#ffffff" stroke-width="2.5"/><path d="M3 47L18 3" stroke="#36e3ff" stroke-width="5"/></svg>',
 timer:'<svg xmlns="http://www.w3.org/2000/svg" width="330" height="64"><path d="M26 3H327L304 61H3Z" fill="#0b1018" fill-opacity=".85" stroke="#36e3ff" stroke-width="2"/><path d="M28 20v28M28 20h22l-6 7 6 7H28" fill="#ffffff" stroke="#ffffff" stroke-width="2" stroke-linejoin="round"/></svg>',
 heartOn:'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><path d="M16 29C4 20 1 13 4 8s10-5 12 1c2-6 9-6 12-1s0 12-12 21z" fill="#ff4fa3" stroke="#ffd1e8" stroke-width="2"/></svg>',
 heartOff:'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><path d="M16 29C4 20 1 13 4 8s10-5 12 1c2-6 9-6 12-1s0 12-12 21z" fill="#2a2030" stroke="#6b5470" stroke-width="2"/></svg>',
 starOn:'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><path d="M16 2l4.2 9.3 10.1 1-7.6 6.8 2.2 10L16 24l-8.9 5.1 2.2-10L1.7 12.3l10.1-1z" fill="#6dff8f" stroke="#e5ffe9" stroke-width="1.6"/></svg>',
 starOff:'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><path d="M16 2l4.2 9.3 10.1 1-7.6 6.8 2.2 10L16 24l-8.9 5.1 2.2-10L1.7 12.3l10.1-1z" fill="#1c2a22" stroke="#4b6b55" stroke-width="1.6"/></svg>'};
for(const [k,v] of Object.entries(hudSvg))await write(`Assets/Art/ui/hud_${k}.svg`,v);
// 4차 HUD 그림이 있으면 임시 SVG 대신 쓴다
const hud=k=>['name','status','timer'].includes(k)?`Assets/Art/ui/own_hud_${k}.svg`:hudPng.has(k)?`Assets/Art/ui/hud_${k}.png`:`Assets/Art/ui/hud_${k}.svg`;
for(const name of await fs.readdir(path.join(repo,'ui/v4/debate_feedback')))if(/\.(svg|webp|png)$/.test(name))await copy('ui/v4/debate_feedback/'+name,'Assets/Art/ui/'+name);
const hudPng=new Set();for(const k of ['name','status','bullet','timer']){try{await copy(`ui/trial/hud_${k}.png`,`Assets/Art/ui/hud_${k}.png`);hudPng.add(k);}catch(e){if(e.code!=='ENOENT')throw e;}}
await copy('ui/trial/hud_name_reference.svg','Assets/Art/ui/hud_name_reference.svg');
for(const f of ['title_bg.png','title_logo.png','chapter_1.png','chapter_P.png'])try{await copy('ui/common/'+f,'Assets/Art/ui/'+f);}catch(e){if(e.code!=='ENOENT')throw e;}
// 글꼴 : 대화창 Pretendard + 논의용 인물·감정 글꼴(docs/spec/04 §4-3). 라이선스 파일도 같이 복사
const fontFiles={pretendard:['Pretendard-Medium.otf','LICENSE.txt'],blackhansans:['BlackHanSans-Regular.ttf','OFL.txt'],gothica1:['GothicA1-Light.ttf','GothicA1-Regular.ttf','GothicA1-Bold.ttf','OFL.txt'],songmyung:['SongMyung-Regular.ttf','OFL.txt'],jua:['Jua-Regular.ttf','OFL.txt'],notoserifkr:['NotoSerifKR[wght].ttf','OFL.txt'],gowundodum:['GowunDodum-Regular.ttf','OFL.txt'],gowunbatang:['GowunBatang-Regular.ttf','OFL.txt'],cutefont:['CuteFont-Regular.ttf','OFL.txt'],dohyeon:['DoHyeon-Regular.ttf','OFL.txt'],galmuri:['Galmuri11.ttf','LICENSE.txt'],dokdo:['Dokdo-Regular.ttf','OFL.txt'],eastseadokdo:['EastSeaDokdo-Regular.ttf','OFL.txt'],gugi:['Gugi-Regular.ttf','OFL.txt'],kiranghaerang:['KirangHaerang-Regular.ttf','OFL.txt'],gaegu:['Gaegu-Regular.ttf','OFL.txt'],nanumpenscript:['NanumPenScript-Regular.ttf','OFL.txt']};
for(const [dir,files] of Object.entries(fontFiles))for(const f of files)await copy(`fonts/${dir}/${f}`,`Assets/Fonts/${dir}/${f.replace('[wght]','-VF')}`);
// 배경·재판장 (4차 에셋이 있으면)
let bgs=[];try{bgs=(await fs.readdir(path.join(repo,'bg'))).filter(f=>f.endsWith('.webp'));}catch(e){if(e.code!=='ENOENT')throw e;}
for(const f of bgs)await copy('bg/'+f,'Assets/Art/bg/'+f);
// 언령 카드 그림 (있는 것만)
let icons=[];try{icons=(await fs.readdir(path.join(repo,'ui/kotodama'))).filter(f=>/^[ETMNR]\d?-\d+.*\.png$/.test(f));}catch(e){if(e.code!=='ENOENT')throw e;}
for(const f of icons)await copy('ui/kotodama/'+f,'Assets/Art/kotodama/'+f);
for(const f of ['frame_evidence','frame_testimony','frame_rule_magic','frame_memo'])await copy(`ui/kotodama/${f}.png`,`Assets/Art/ui/kotodama/${f}.png`);
// CG(사망·처형·이벤트)·선물·패드·장 제목 카드 (있는 것만)
const list=async(dir,re)=>{try{return (await fs.readdir(path.join(repo,dir))).filter(f=>re.test(f));}catch(e){if(e.code==='ENOENT')return [];throw e;}};
// Character cutins/portraits come exclusively from the curated V4 publisher above.
const cgs=(await list('art/cg',/\.webp$/)).filter(f=>!/_(bg|fg)\.webp$/.test(f));for(const f of cgs)await copy('art/cg/'+f,'Assets/Art/cg/'+f);
const giftIcons=await list('ui/gift',/^(G\d\d|P\d{3})\.png$/);for(const f of giftIcons)await copy('ui/gift/'+f,'Assets/Art/gift/'+f);
const padArt=await list('ui/pad',/^(coin|capsule_machine|map_\w+)\.png$/);for(const f of padArt)await copy('ui/pad/'+f,'Assets/Art/pad/'+f);
for(const slug of 'mio rin ken nana taiga ai rei sora haruka sho koto akari riku satsuki yuu kaede lappy'.split(' '))padArt.push('face_'+slug+'.webp');
const minigame=await list('ui/minigame',/\.png$/);for(const f of minigame)await copy('ui/minigame/'+f,'Assets/Art/ui/minigame/'+f);
const cards=await list('ui/common',/^(chapter_\w+|gameover|credits_bg|ending_\w+|broadcast_\w+)\.png$/);for(const f of cards)await copy('ui/common/'+f,'Assets/Art/ui/'+f);
// 소리 : audio/cues.json 에 파일이 적힌 것만
const cues=JSON.parse(await fs.readFile(path.join(repo,'audio/cues.json'),'utf8')),audio={};
// 파일 찾기 : cues.json 의 file 칸 → 없으면 audio/ 아래에서 큐 ID 와 같은 이름(bgm_title.ogg 등, 하위 폴더 포함)
const audioFiles=[];const walk=async d=>{for(const e of await fs.readdir(path.join(repo,d),{withFileTypes:true}).catch(()=>[])){const r=d+'/'+e.name;if(e.isDirectory())await walk(r);else if(/\.(ogg|mp3|wav|m4a|flac)$/i.test(e.name))audioFiles.push(r);}};await walk('audio');
// 반복 곡의 들어가는 부분은 <큐>_intro, 징글·들어가는 부분 길이(초)는 audioLen (tools/import_audio.py)
const audioLen={};await fs.rm(path.join(root,'Assets/Audio'),{recursive:true,force:true}); // 빠진 곡이 남지 않게
// Native Windows playback uses buffered decoding; HTMLAudio streaming is a
// separate browser path and is rejected by the native package validator.
// Approved compressed cues can overshoot full scale after decoding and mixer filters.
// Fixed -7.96 dB asset headroom keeps cue balance and the exposed 0..10/mute controls intact.
// Whole-bank WebView PCM comparison: Saved/v4-audio-bank-headroom-1793455395331/report.json.
const audioHeadroom=.4;
const put1=async(k,src)=>{try{const to='Assets/Audio/'+k+path.extname(src);await copy(src,to);
 const asset='Assets/Audio/S_'+k+'.hbaudioasset.json';
 await write(asset,{version:1,name:'S_'+k,priority:128,virtualize:false,streaming:false,clip:to,volume:audioHeadroom,pitch:1,loop:!!cues.sfx?.[k]?.loop_samples,spatial:false,autoplay:false,refDistance:1,maxDistance:100,rolloff:1,mixer:'Assets/Audio/MX_Yumeno.hbaudiomixer.json',bus:k.startsWith('ui_')?'ui':/^bgm_/.test(k)?'music':'sfx'});
 audio[k]=asset;return true;}catch(e){if(e.code!=='ENOENT')throw e;return false;}};
for(const group of ['bgm','jingle','sfx'])for(const [k0,v] of Object.entries(cues[group]||{})){
 const k=k0.replace(/_\*$/,''),src=v&&v.file?'audio/'+v.file:audioFiles.find(f=>path.basename(f).replace(/\.[^.]+$/,'').toLowerCase()===k.toLowerCase());
 if(!src||!await put1(k,src))continue;
 if(v&&v.intro&&v.introLen>.2&&await put1(k+'_intro','audio/'+v.intro))audioLen[k+'_intro']=v.introLen;
 if(v&&v.len)audioLen[k]=v.len;}
for(const [cue,fallback] of Object.entries(cues.fallbacks||{})){
 if(audio[cue])continue;
 if(!audio[fallback])throw Error('Missing audio fallback: '+fallback+' for '+cue);
 audio[cue]=audio[fallback];
 if(audioLen[fallback])audioLen[cue]=audioLen[fallback];
}
// 큐 목록 : 사용자가 파일 이름을 맞출 수 있게 (audio/CUES.md)
await write('../audio/CUES.md',['# 소리 파일 이름 표','','`audio/` 아래(하위 폴더도 됨)에 **아래 이름 그대로** 파일을 넣으면 다음 빌드부터 그 자리에서 나온다. 확장자는 .ogg .mp3 .wav .m4a .flac 아무거나.','','| 파일 이름 | 쓰는 곳 | 들어감 |','|---|---|---|',
 ...['bgm','jingle','sfx'].flatMap(g=>Object.entries(cues[g]||{}).map(([k0,v])=>{const k=k0.replace(/_\*$/,'');return `| ${k} | ${(v&&(v.use||v.name))||''} | ${audio[k]?'✓':''} |`;})),''].join('\n'));
await write('Assets/Data/art.json',{backgrounds:bgs.map(f=>f.slice(0,-5)),kotodama:icons.map(f=>f.slice(0,-4)),cg:cgs.map(f=>f.slice(0,-5)),gifts:giftIcons.map(f=>f.slice(0,-4)),pad:padArt.map(f=>f.replace(/\.[^.]+$/,'')),cards:cards.map(f=>f.slice(0,-4)),minigame:minigame.map(f=>f.slice(0,-4)),audio,audioLen});

// 4) UI 위젯 (1280×720 기준, V3식 대화창)
const body='Assets/Fonts/pretendard/Pretendard-Medium.otf',head='Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf';
await emitV4ComicUI({write,body,head});
await emitV4ScrumUI({write,body,head});
await emitV4AnagramUI({write,body,head});
await emitV4PadEvidenceUI({repo,write,body,head});
await emitV4PadGiftUI({repo,write,body});
await emitV4PadReportUI({repo,write,body});
await emitV4PadSkillUI({repo,write,body});
await emitTrialVitals({write});
await emitV4PadRulesUI({repo,write,body,legacyRules:rules});
await emitV4PadSystemUI({repo,write,body});
await emitV4PadSystemPages({repo,write,body});
await emitV4PadMapUI({repo,write,body});
await emitV4DialogueChoice({repo,write});
const dialogueLayout=await emitV4DialogueWindow({repo,write});
const explorationHudLayout=await emitV4ExplorationHud({repo,write});
const trialAnswerLayout=await emitTrialAnswerUI({repo,write});
await emitTrialPickerUI({repo,write,body,head});
await emitTrialResultUI({repo,write,body});
await emitTitleChapterUI({repo,write,copy,body,head});
const MAIN_GLYPHS=48,NOISE_GLYPHS=26;
const w=createWidgetAsset('W_Yumeno');w.scaleMode='scale';w.scaleRule='fit';
const add=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#f4f0f6',background:'#00000000',padding:0,focusable:false,...props});w.nodes.push(n);return n;};
add('Panel','Backdrop',[0,0,1280,720],{background:'#17121f'});
add('Image','Background',[-40,-24,1360,768],{texture:'',imageFit:'cover',visible:false});
// 논의 글자 : 글자 하나 = Text 하나. 정렬점 중심(.5,.5)이라 SetPosition 이 글자 중심, 배율·회전도 중심 기준
const glyph=(id,parent,size)=>{const n=add('Text',id,[0,0,size*1.6,size*1.6],{fontSize:size,align:'center',visible:false,wrap:false},parent);n.slot.alignment=[.5,.5];};
add('Panel','CourtDim',[0,0,1280,720],{background:'#12051f33',visible:false}); // 3D 위·화자 입상 아래 옅은 보라. V3 재판 화면은 밝고 색이 선명하다(영상 A 16:36) : 50% 는 너무 어두웠다
add('Image','Whip',[0,0,1280,720],{texture:'Assets/Art/ui/whip.svg',imageFit:'fill',visible:false}); // 화자 전환 속도선
add('Panel','TrialBack',[0,0,1280,720],{visible:false});
for(let i=0;i<MAIN_GLYPHS;i++)glyph('MB'+i,'TrialBack',50);for(let i=0;i<NOISE_GLYPHS;i++)glyph('NB'+i,'TrialBack',40);
add('Image','Portrait',[0,0,1280,1050],{texture:'',imageFit:'contain',visible:false});
add('Image','SpeakerPodium',[478,431,323,351],{texture:'',imageFit:'fill',visible:false}); // 화자 앞 증언대(3D 증언대와 같은 자리, 입상 위에 그림)
add('Image','DialogFrame',[80,512,1120,170],{texture:'Assets/Art/ui/frame.png',imageFit:'fill'});
add('Image','Nameplate',dialogueLayout.namebase.normal,{texture:'Assets/Art/ui/v3/dialogue/namebase.svg',imageFit:'fill'});
add('Image','DialogueOrnament',[0,0,1280,720],{texture:'Assets/Art/ui/v3/dialogue/source/frame1.png',imageFit:'fill',visible:false});
add('Image','Name',dialogueLayout.names.normal,{texture:'',imageFit:'fill'});
add('Text','NameHead',[0,0,0,0],{visible:false}); // Retained node ID for old hide paths; no first-letter layer.
add('Image','Next',dialogueLayout.next,{texture:'Assets/Art/ui/v3/dialogue/next.svg',imageFit:'fill',visible:false});
add('Text','Body',dialogueLayout.body,{fontSize:dialogueLayout.font,wrap:true});
// 논스톱 논의 (V3) HUD + 화자 앞쪽 글자층
add('Panel','Trial',[0,0,1280,720],{visible:false});
add('Image','Lens',[0,0,1280,720],{texture:'Assets/Art/ui/lens.svg',imageFit:'fill',visible:false},'Trial');
for(let i=0;i<MAIN_GLYPHS;i++){const n=add('Text','MS'+i,[0,0,80,80],{fontSize:50,align:'center',visible:false,wrap:false,color:'#05020a'},'Trial');n.slot.alignment=[.5,.5];}
for(let i=0;i<MAIN_GLYPHS;i++)glyph('MF'+i,'Trial',50);for(let i=0;i<NOISE_GLYPHS;i++)glyph('NF'+i,'Trial',40);
add('Image','NamePanel',[22,12,420,80],{texture:hud('name'),imageFit:'fill'},'Trial');
add('Text','TrialSpeaker',[66,20,300,34],{font:head,fontSize:24,color:'#ffffff'},'Trial');
add('Image','StatusPanel',[936,52,330,116],{texture:hud('status'),imageFit:'fill'},'Trial');
add('Text','StatusLabel',[994,58,180,22],{text:'발언력 / 집중',font:body,fontSize:15,color:'#e8d5a0'},'Trial');
// Hearts live in a separate widget so enlarged HP does not exceed Main's node limit.
for(let i=0;i<10;i++)add('Image','Star'+i,[978+i*25,128-i*1.6,24,24],{texture:'Assets/Art/ui/hud_starOn.svg',imageFit:'contain'},'Trial');
await copy('ui/v4/nonstop_intro/kotodama_cylinder.svg','Assets/Art/ui/kotodama_cylinder.svg');
await copy('ui/v4/nonstop_intro/kotodama_plate.svg','Assets/Art/ui/kotodama_plate.svg');
add('Image','Cylinder',[4,470,140,140],{texture:'Assets/Art/ui/kotodama_cylinder.svg',imageFit:'contain'},'Trial');
add('Image','BulletPlate',[122,560,420,50],{texture:'Assets/Art/ui/kotodama_plate.svg',imageFit:'fill',nineSlice:[24,0,24,0]},'Trial');
add('Text','Bullet',[156,567,370,36],{font:head,fontSize:25,color:'#102c46',wrap:false},'Trial');
add('Text','BulletLabel',[220,612,160,20],{text:'코토다마',font:body,fontSize:15,color:'#d9e7ee'},'Trial');
add('Image','TimerPanel',[938,644,330,64],{texture:hud('timer'),imageFit:'fill'},'Trial');
add('Text','Timer',[1040,653,176,36],{font:'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf',fontSize:27,color:'#ffb21f',align:'right'},'Trial');
add('Image','VPoint',[0,0,22,22],{texture:'Assets/Art/ui/vpoint.svg',imageFit:'contain',visible:false},'Trial').slot.alignment=[.5,.5];
for(let i=1;i<3;i++)add('Image','VPoint'+i,[0,0,22,22],{texture:'Assets/Art/ui/vpoint.svg',imageFit:'contain',visible:false},'Trial').slot.alignment=[.5,.5];
for(let i=0;i<3;i++)add('Image','SilenceShot'+i,[0,0,28,28],{texture:'Assets/Art/ui/impact.svg',imageFit:'contain',visible:false},'Trial').slot.alignment=[.5,.5];
add('Text','NoiseGain',[0,0,120,40],{font:head,fontSize:24,color:'#ffffff',align:'center',visible:false},'Trial');
add('Image','StartBand',[0,250,1280,200],{texture:'Assets/Art/ui/start_nonstop.svg',imageFit:'fill',visible:false},'Trial');
add('Text','TrialMsg',[0,300,1280,80],{font:head,fontSize:60,align:'center',color:'#ff8fc8',visible:false},'Trial');
add('Image','Cutin',[128,200,1024,342],{texture:'Assets/Art/ui/result_refute.svg',imageFit:'contain',visible:false},'Trial');
add('Image','Aim',[608,328,64,64],{texture:'Assets/Art/ui/aim.svg',imageFit:'contain'},'Trial');
add('Panel','Title',[0,0,1280,720],{background:'#0f0b16'});
add('Image','TitleBg',[0,0,1280,720],{texture:'Assets/Art/ui/title_bg.png',imageFit:'cover'},'Title');
add('Image','TitleLogo',[300,120,680,300],{texture:'Assets/Art/ui/title_logo.png',imageFit:'contain'},'Title');
add('Text','TitleSub',[0,470,1280,40],{text:'Enter  새로 시작          C  이어하기',fontSize:26,align:'center',color:'#efe6f4'},'Title');
stretchTitleBackdrop(w);applyTrialHudStyle(w);applyTrialDialogueResponsive(w);await write('Assets/UI/Main.hbwidget.json',w);
// Three concurrent panic voices stay in their own bounded widget.
{
 const p=createWidgetAsset('W_PanicV4');p.scaleMode='scale';p.scaleRule='fit';
 for(let lane=0;lane<3;lane++)for(let i=0;i<48;i++){
  const n=createWidgetNode('Text','P'+lane+'G'+i,'root');n.name=n.id;n.slot.offset=[0,0,58,58];n.slot.alignment=[.5,.5];
  Object.assign(n.properties,{text:'',font:body,fontSize:36,color:'#ffffff',padding:0,visible:false,wrap:false,align:'center',focusable:false,outlineColor:'#000000',outlineWidth:6});p.nodes.push(n); // V3 발언 글자는 굵은 검은 테두리
 }
 await write('Assets/UI/PanicV4.hbwidget.json',p);
}
// Native action feedback is isolated from the nearly-full Main widget.
{
 const fx=createWidgetAsset('W_DebateFX');fx.scaleMode='scale';fx.scaleRule='fit';
 const put=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:false,...props});fx.nodes.push(n);return n;};
 put('Image','FocusVeil',[0,0,1280,720],{texture:'Assets/Art/ui/focus_veil.svg',imageFit:'fill'});
 put('Image','ChargeRing',[0,0,96,96],{texture:'Assets/Art/ui/charge_ring.svg',imageFit:'contain'}).slot.alignment=[.5,.5];
 put('Text','ChargeState',[150,632,590,30],{fontSize:19,color:'#ecd8ff'});
 put('Image','ShotTrail',[0,0,280,18],{texture:'Assets/Art/ui/shot_normal.svg',imageFit:'fill'}).slot.alignment=[.5,.5];
 put('Image','ShotImpact',[0,0,160,160],{texture:'Assets/Art/ui/impact.svg',imageFit:'contain'}).slot.alignment=[.5,.5];
 put('Canvas','ResultRoot',[0,0,1280,720]);
 put('Panel','ResultWash',[0,0,1280,720],{background:'#ffffff'},'ResultRoot');
 put('Text','ResultClaim',[100,260,1080,180],{font:head,fontSize:64,align:'center',color:'#ffb51c'},'ResultRoot');
 put('Image','ResultBand',[0,0,1280,720],{texture:'Assets/Art/ui/result_scene_refute.svg',imageFit:'fill'},'ResultRoot');
 put('Image','ResultBolt',[0,0,1280,720],{texture:'Assets/Art/ui/result_bolt.svg',imageFit:'fill'},'ResultRoot');
 put('Image','ResultPartner',[30,120,490,580],{texture:'',imageFit:'contain'},'ResultRoot');
 put('Image','ResultHero',[580,90,700,650],{texture:'Assets/Art/ui/hero_refute.webp',imageFit:'contain'},'ResultRoot');
 put('Image','ResultWord',[90,100,360,360],{texture:'Assets/Art/ui/result_refute_glyph0.svg',imageFit:'contain'},'ResultRoot');
 put('Image','ResultWord2',[300,300,360,360],{texture:'Assets/Art/ui/result_refute_glyph1.svg',imageFit:'contain'},'ResultRoot');
 put('Image','ResultCrack',[0,0,1280,720],{texture:'Assets/Art/ui/result_crack_refute.svg',imageFit:'fill'},'ResultRoot');
 put('Image','ResultShard0',[0,0,1280,720],{texture:'Assets/Art/ui/result_shatter.svg',imageFit:'fill'},'ResultRoot');
 put('Image','ResultInk',[0,0,1280,720],{texture:'Assets/Art/ui/result_ink.svg',imageFit:'fill'},'ResultRoot');
 for(let i=0;i<5;i++)put('Image','ResultBreak'+i,[260+i*145,270,220,240],{texture:`Assets/Art/ui/result_refute_break${i}.svg`,imageFit:'contain'},'ResultRoot');
 put('Panel','ResultExit',[0,0,1280,720],{background:'#000000'},'ResultRoot');
 const resultNodes=fx.nodes.filter(n=>n.parent==='ResultRoot');
 const layers=['ResultWash','ResultBand','ResultBolt','ResultPartner','ResultHero','ResultWord','ResultWord2','ResultCrack','ResultShard0','ResultInk',...Array.from({length:5},(_,i)=>'ResultBreak'+i),'ResultExit'];
 resultPlaneDefinitions=layers.map((id,index)=>{const n=resultNodes.find(n=>n.id===id);return {id,rect:n.slot.offset,texture:n.properties.texture||`Assets/Art/ui/result_${id==='ResultWash'?'white':'black'}.svg`,depth:.24-index*.009,order:5000+index};});
 resultPlaneDefinitions.unshift({id:'ResultCourtDim',rect:[0,0,1280,720],texture:'Assets/Art/ui/result_court_dim.svg',depth:.28,order:4999});
 const textures={};for(const row of JSON.parse(await fs.readFile(path.join(repo,'ui/v4/debate_feedback/hero_manifest.json'),'utf8')).rows){textures['Assets/Art/ui/'+path.basename(row.file)]=[row.width,row.height];if(row.character)textures[`Assets/Art/ui/negative_${row.character}.webp`]=[row.width,row.height];}
 await write('Assets/Data/debate_fx.json',{planes:resultPlaneDefinitions,textures});
 resultForeground(fx,{planes:resultPlaneDefinitions});await emitLieLookup(write);await emitNonstopResultPalette(repo,write);await emitNonstopRefuteSource({write,widget:fx});
 for(const name of ['DebateScene','DebateCutin'])await fs.rm(path.join(root,`Assets/UI/${name}.hbwidget.json`),{force:true});
 applyKotodamaFlight(fx);
 await write('Assets/UI/DebateFX.hbwidget.json',fx);
}

// 4-2) 재판 단계 위젯 (객관식·언령 고르기·지점·인물 지목·투표·쇼다운·스크럼·이론 무장·애너그램·발굴·택시·클라이맥스). Main 위에 겹쳐 띄운다.
// 좌표는 Source/TrialRunner.hpp 의 상수와 같다.
{
 const v=createWidgetAsset('W_Stage');v.scaleMode='scale';v.scaleRule='fit';
 const put=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:false,...props});v.nodes.push(n);return n;};
 put('Panel','Shade',[0,0,1280,720],{background:'#05030acc'});
 put('Image','QPlate',[140,24,760,80],{texture:hud('bullet'),imageFit:'fill'});
 put('Text','Question',[180,28,680,72],{font:head,fontSize:28,align:'center',wrap:true});
 // V3 선택 화면 장식 (docs/spec/16 §5-2 재판) : 문장·ANSWER·모래시계·화자 이름표·아래 질문·조작 안내
 const svg=(name,body,w,h)=>write(`Assets/Art/ui/${name}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">${body}</svg>`);
 const black='font-family="Arial Black,Arial" font-weight="900" font-style="italic"';
 await svg('cls_emblem',`<path d="M10 92L46 8h34L44 92z" fill="#ff4fa3"/><text x="58" y="56" ${black} font-size="30" fill="#36e3ff">CLASS</text><text x="58" y="88" ${black} font-size="30" fill="#36e3ff">TRIAL</text>`,200,100);
 await svg('answer',`<text x="6" y="48" ${black} font-size="50" fill="none" stroke="#b6ff3d" stroke-width="3">ANSWER</text><text x="6" y="48" ${black} font-size="50" fill="#e9ffcf" opacity=".35">ANSWER</text>`,260,60);
 await svg('band_off','<path d="M14 2H1000V40H0z" fill="#0b1018" fill-opacity=".78"/><path d="M14 2H1000" stroke="#ffffff" stroke-opacity=".25"/>',1000,42);
 await svg('band_on','<path d="M14 2H1000V40H0z" fill="#1c6fd6" fill-opacity=".92"/><path d="M14 2H1000M0 40H1000" stroke="#9fe0ff" stroke-width="2"/>',1000,42);
 await svg('hourglass','<path d="M10 6h100M10 234h100" stroke="#36e3ff" stroke-width="8"/><path d="M20 12c0 70 80 70 80 108s-80 38-80 108" fill="none" stroke="#36e3ff" stroke-width="6"/><path d="M100 12c0 70-80 70-80 108s80 38 80 108" fill="none" stroke="#36e3ff" stroke-width="6"/><path d="M34 40h52c-6 30-26 44-26 70c0-26-20-40-26-70z" fill="#ff4fa3"/><path d="M60 150c-20 12-30 40-32 72h64c-2-32-12-60-32-72z" fill="#ff4fa3"/>',120,240);
 await svg('spk_tag','<path d="M18 0H300L282 56H0z" fill="#0b1018" fill-opacity=".9"/><path d="M18 0H300" stroke="#ff4fa3" stroke-width="4"/>',300,56);
 await svg('q_band','<path d="M0 0H1280V96H0z" fill="#05070c" fill-opacity=".86"/><path d="M0 1H1280" stroke="#36e3ff" stroke-opacity=".6" stroke-width="2"/>',1280,96);
 await svg('bul_line','<path d="M30 0V460" stroke="#ffffff" stroke-opacity=".7" stroke-width="3"/><circle cx="30" cy="8" r="7" fill="#ffffff"/><circle cx="30" cy="452" r="7" fill="#ff4fa3"/>',60,460);
 await svg('bul_cyl','<g fill="none" stroke="#36e3ff" stroke-opacity=".55" stroke-width="10"><circle cx="230" cy="230" r="200"/><circle cx="230" cy="230" r="60"/></g>'+[0,1,2,3,4,5].map(k=>{const a=k*Math.PI/3;return `<circle cx="${230+130*Math.cos(a)}" cy="${230+130*Math.sin(a)}" r="52" fill="#36e3ff" fill-opacity=".18" stroke="#36e3ff" stroke-opacity=".6" stroke-width="6"/>`;}).join(''),460,460);
 await svg('card_frame','<path d="M0 0H400V250H0z" fill="#0b1018" fill-opacity=".9"/><path d="M2 2H398V248H2z" fill="none" stroke="#ffffff" stroke-width="3"/>',400,250);
 await svg('desc_box','<path d="M20 0H440V260H0V20z" fill="#05070c" fill-opacity=".88"/><path d="M20 40H420" stroke="#36e3ff" stroke-width="2"/>',440,260);
 await svg('accuse',`<text x="40" y="64" ${black} font-size="58" fill="#ffffff" stroke="#ff2a6d" stroke-width="3">ACCUSE</text><path d="M4 78L30 10" stroke="#ff2a6d" stroke-width="10"/>`,320,90);
 await svg('acc_ring','<ellipse cx="240" cy="70" rx="230" ry="62" fill="none" stroke="#ff4fa3" stroke-width="14"/><ellipse cx="240" cy="70" rx="170" ry="40" fill="#ff4fa3" fill-opacity=".25"/>',480,140);
 await svg('acc_name','<path d="M20 0H560L540 80H0z" fill="#0b1018" fill-opacity=".85"/><path d="M20 0H560M0 80H540" stroke="#ffe36e" stroke-width="3"/>',560,80);
 await svg('spot_title',`<text x="30" y="58" ${black} font-size="44" fill="#ffffff">SPOT</text><text x="150" y="58" ${black} font-size="30" fill="#ff4fa3">SELECTION</text>`,380,80);
 await svg('spot_frame','<rect x="3" y="3" width="894" height="514" fill="none" stroke="#bfe6ff" stroke-width="6"/>',900,520);
 await svg('spot_mark','<circle cx="30" cy="30" r="22" fill="none" stroke="#7dff5a" stroke-width="4"/><circle cx="30" cy="30" r="5" fill="#7dff5a"/><path d="M30 0v14M30 46v14M0 30h14M46 30h14" stroke="#7dff5a" stroke-width="3"/>',60,60);
 put('Image','Emblem',[18,26,200,100],{texture:'Assets/Art/ui/cls_emblem.svg',imageFit:'contain'});
 put('Image','AnswerLbl',[236,176,260,60],{texture:'Assets/Art/ui/answer.svg',imageFit:'contain'});
 put('Image','Hourglass',[110,236,120,240],{texture:'Assets/Art/ui/hourglass.svg',imageFit:'contain'});
 put('Image','TaQuestionPlate',[0,0,1280,720],{texture:'Assets/Art/ui/v3/dialogue/trial_normal.svg',imageFit:'fill'});
 put('Text','TaQuestion',trialAnswerLayout.question,{fontSize:30,wrap:true});
 put('Image','TaFrame',[0,0,1280,720],{texture:'Assets/Art/ui/v3/trial_answer/frame.svg',imageFit:'fill'});
 put('Text','TaTitle',trialAnswerLayout.title,{font:head,fontSize:36,text:'정답 선택',color:'#ffffff'});
 put('Image','TaRows',[0,0,1280,720],{texture:trialAnswerLayout.wait[3].asset,imageFit:'fill'});
 for(let i=0;i<4;i++)put('Image','TaCheck'+i,[0,0,42.666667,42.666667],{texture:'Assets/Art/ui/v3/trial_answer/check.svg',imageFit:'contain'});
 for(let i=0;i<4;i++)put('Image','TaNumber'+i,[0,0,42.666667,42.666667],{texture:`Assets/Art/ui/v3/trial_answer/number_${i}.svg`,imageFit:'contain'});
 put('Image','SpkTag',[30,470,300,56],{texture:'Assets/Art/ui/spk_tag.svg',imageFit:'fill'});
 put('Text','SpkName',[52,478,250,40],{font:head,fontSize:26,color:'#ffffff'});
 put('Image','QBand',[0,604,1280,96],{texture:'Assets/Art/ui/q_band.svg',imageFit:'fill'});
 put('Text','QText',[110,616,1060,76],{fontSize:26,color:'#9fe6ff',wrap:true});
 put('Text','Hint',[900,560,360,30],{fontSize:18,color:'#ffffff',align:'right'});
 put('Image','BulCyl',[-140,190,460,460],{texture:'Assets/Art/ui/bul_cyl.svg',imageFit:'contain'});
 put('Image','BulLine',[40,136,60,440],{texture:'Assets/Art/ui/bul_line.svg',imageFit:'fill'});
 put('Image','CardFrame',[840,92,400,250],{texture:'Assets/Art/ui/card_frame.svg',imageFit:'fill'});
 put('Image','CardImg',[846,98,388,238],{texture:'',imageFit:'contain'});
 put('Image','DescBox',[820,350,440,250],{texture:'Assets/Art/ui/desc_box.svg',imageFit:'fill'});
 put('Text','CardTitle',[850,356,400,34],{font:head,fontSize:26,color:'#ffffff'});
 put('Text','CardText',[846,400,400,190],{fontSize:19,color:'#e6f2ff',wrap:true});
 put('Image','AccLbl',[20,20,320,90],{texture:'Assets/Art/ui/accuse.svg',imageFit:'contain'});
 put('Image','AccRing',[270,520,380,110],{texture:'Assets/Art/ui/acc_ring.svg',imageFit:'contain'});
 put('Image','AccFig',[210,40,500,600],{texture:'',imageFit:'contain'});
 put('Image','AccTag',[680,270,560,80],{texture:'Assets/Art/ui/acc_name.svg',imageFit:'fill'});
 put('Text','AccNo',[700,276,90,66],{font:'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf',fontSize:58,color:'#ffe36e'});
 put('Text','AccName',[790,282,430,60],{font:head,fontSize:40,color:'#ffffff'});
 put('Text','AccArrows',[150,300,80,80],{text:'◀',font:body,fontSize:56,align:'center',color:'#ff4fa3'});put('Text','AccArrowR',[690,300,80,80],{text:'▶',font:body,fontSize:56,align:'center',color:'#ff4fa3'});
 put('Image','SpotTitle',[18,20,380,80],{texture:'Assets/Art/ui/spot_title.svg',imageFit:'contain'});
 put('Image','SpotImg',[190,90,900,520],{texture:'',imageFit:'fill'});
 put('Image','SpotFrame',[190,90,900,520],{texture:'Assets/Art/ui/spot_frame.svg',imageFit:'fill'});
 put('Panel','CrossH',[190,0,900,2],{background:'#7dff5a'});put('Panel','CrossV',[0,90,2,520],{background:'#7dff5a'});
 for(let i=0;i<6;i++){const n=put('Image','Mark'+i,[0,0,60,60],{texture:'Assets/Art/ui/spot_mark.svg',imageFit:'contain'});n.slot.alignment=[.5,.5];}
 put('Text','MarkName',[190,560,900,44],{font:head,fontSize:28,align:'center',color:'#16121c',background:'#ffe36ee8'});
 // 보기 8칸 : V3 번호 띠(오른쪽 끝까지), 고른 띠만 파랗게. 좌표는 TrialRunner showOptions 가 정한다
 for(let i=0;i<8;i++){put('Image','OptP'+i,[300,250+i*46,980,42],{texture:'Assets/Art/ui/band_off.svg',imageFit:'fill'});put('Text','OptT'+i,[330,254+i*46,900,34],{fontSize:24});}
 // 클라이맥스 만화 칸 8 (4×2)
 for(let i=0;i<8;i++){const c=i%4,r=Math.floor(i/4);put('Panel','PanP'+i,[24+c*310,102+r*150,298,142],{background:'#f4f0e8',borderWidth:4,borderColor:'#16121c'});put('Image','PanI'+i,[28+c*310,106+r*150,290,134],{texture:'',imageFit:'cover'});put('Text','PanT'+i,[36+c*310,110+r*150,274,126],{fontSize:15,color:'#16121c',wrap:true});}
 // 발굴: 전용 20×11 위젯의 셀이 실제 아래 그림을 가린다.
 put('Image','MineBg',[160,130,960,420],{texture:'',imageFit:'cover'});
for(let i=0;i<3;i++){put('Image','MineIcon'+i,[180+i*320,272,280,136],{texture:'',imageFit:'contain'});put('Text','MineItem'+i,[180+i*320,376,280,32],{font:head,fontSize:20,align:'center',color:'#ffe9a8',background:'#1b1325d0'});}
 for(const [n,c,d] of [['w','#f4f2f8','#b9b4c8'],['p','#ff8cc8','#c9488c'],['y','#ffd95a','#c79a1c'],['b','#69d9ff','#2777ab']])await write(`Assets/Art/ui/mine_${n}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="80" height="70"><rect x="1" y="1" width="78" height="68" rx="6" fill="${d}"/><rect x="4" y="3" width="72" height="58" rx="5" fill="${c}"/><path d="M10 10h40" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".7"/></svg>`);
 // Cell0..241 belong to W_MineV4, shown after Stage to preserve draw order.
 // The shaded spheres/light/upper-left answer belong to AnagramV4.
 put('Text','Slots',[240,600,800,70],{font:head,fontSize:46,align:'center',color:'#ffe9a8'});
 // 브레인 드라이브 : 차선 3, 차
 put('Image','Road',[0,0,1280,720],{texture:'Assets/Art/ui/taxi_road.svg',imageFit:'fill'});
 for(let i=0;i<8;i++){const n=put('Panel','Dash'+i,[0,0,10,40],{background:'#ff4fa3'});n.slot.alignment=[.5,.5];}
 for(let i=0;i<3;i++){const n=put('Text','Cube'+i,[0,0,90,90],{font:head,fontSize:48,align:'center',color:'#16121c',background:'#7dfcff',radius:8});n.slot.alignment=[.5,.5];}
 for(let i=0;i<2;i++){const n=put('Image','Rival'+i,[0,0,160,110],{texture:'Assets/Art/ui/taxi_rival.svg',imageFit:'contain'});n.slot.alignment=[.5,.5];}
 for(let i=0;i<3;i++){const n=put('Text','Lane'+i,[0,0,260,120],{font:head,fontSize:24,align:'center',color:'#ffffff',background:'#ff4fa3d8',radius:10,wrap:true});n.slot.alignment=[.5,.5];}
 {const n=put('Image','Car',[0,0,240,150],{texture:'Assets/Art/ui/taxi_car.svg',imageFit:'contain'});n.slot.alignment=[.5,.5];}
 put('Text','TaxiQ',[160,96,960,52],{font:head,fontSize:30,align:'center',color:'#7dfcff',background:'#0b1018cc'});
 // 반론 쇼다운 : 날아오는 발언, 칼 이름
 put('Text','Blade',[0,0,1280,90],{font:head,fontSize:52,align:'center',color:'#ffffff'}).slot.alignment=[0,.5];
 put('Text','BladeName',[880,640,380,50],{font:head,fontSize:26,align:'right',color:'#7dff9a'});
 await copy('ui/v4/v3_reference/showdown_aim.svg','Assets/Art/ui/showdown_aim.svg');
 put('Image','Slash',[0,0,420,12],{texture:'Assets/Art/ui/showdown_aim.svg',imageFit:'fill'}).slot.alignment=[.5,.5];
 // 이론 무장 : 리듬 고리, 마지막 일격 조각 4
 await write('Assets/Art/ui/arm_ring.svg','<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><circle cx="100" cy="100" r="96" fill="none" stroke="#ff4fa3" stroke-width="6"/></svg>');
 await write('Assets/Art/ui/arm_core.svg','<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="50" fill="#ff4fa3" fill-opacity=".33"/></svg>');
 const ring=put('Image','Ring',[540,260,200,200],{texture:'Assets/Art/ui/arm_ring.svg',imageFit:'contain'});
 put('Image','RingCore',[590,310,100,100],{texture:'Assets/Art/ui/arm_core.svg',imageFit:'contain'});
 put('Text','ArmLine',[140,140,1000,104],{font:head,fontSize:26,align:'center',wrap:true});
 put('Text','ArmNoteKey',[0,0,59.7333,59.7333],{font:head,fontSize:32,align:'center',color:'#ffffff'});
 put('Text','ArmNoteType',[0,0,120,28],{fontSize:18,align:'center',color:'#ffffff'});
 // Original todome fl_wait plate/root/text transforms (1920 ->1280), not a compact card cross.
 const pieces=[
  {plate:[485.6667,116.6667,308.6667,56],text:[482.6333,125.7667,315.3333,92],icon:[588.8,33.3333,102.3984,102.3984],align:'center',color:'#53ff89',shape:'M128 25L229 210H27Z'},
  {plate:[852.9333,335,308.6823,56],text:[843.4669,347.5667,314.9644,46.6667],icon:[1144.2667,311.4667,102.3984,102.3984],align:'right',color:'#ff386a',shape:'M128 25A103 103 0 1 1 127.99 25Z'},
  {plate:[485.6667,552.6667,308.6667,56],text:[482.6333,561.7667,315.3333,46.6667],icon:[588.8,589.6,102.3984,102.3984],align:'center',color:'#25c9ff',shape:'M43 43L213 213M213 43L43 213'},
  {plate:[111.6667,334.6667,308.6667,56],text:[115.3,343.7667,315.3333,92],icon:[33.3333,311.4667,102.3984,102.3984],align:'left',color:'#f987d0',shape:'M36 36H220V220H36Z'}
 ];
 for(let i=0;i<4;i++){
  const p=pieces[i];await write('Assets/Art/ui/arm_piece_'+i+'.svg',`<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><defs><filter id="g" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="13"/></filter></defs><path d="${p.shape}" fill="none" stroke="${p.color}" stroke-width="24" filter="url(#g)"/><path d="${p.shape}" fill="none" stroke="${p.color}" stroke-width="13"/><text x="128" y="146" text-anchor="middle" fill="white" font-family="sans-serif" font-size="51">${i+1}</text></svg>`);
  put('Panel','ArmPieceBand'+i,p.plate,{background:'#09070d88'});
  put('Image','ArmPieceKey'+i,p.icon,{texture:'Assets/Art/ui/arm_piece_'+i+'.svg',imageFit:'contain'});
  put('Text','Piece'+i,p.text,{font:head,fontSize:30,align:p.align,color:'#ffffff'});
 }
 put('Text','ArmQuestion',[420,312,440,110],{font:head,fontSize:30,align:'center',color:'#ff4fa3'});
 put('Text','ArmJoined',[180,454,920,64],{font:head,fontSize:32,align:'center',color:'#ffffff'});
 // Measured V3 screenshots: red opponent half, blue grid half, moving gold
 // boundary, selected blade at lower left. No right-hand list or centre counter.
 for(const name of ['showdown_grid','showdown_divider','showdown_blade'])await copy('ui/v4/v3_reference/'+name+'.svg','Assets/Art/ui/'+name+'.svg');
 // V3(영상 A 50:05~50:20) : 오른쪽 절반은 파란 빛 속 주인공 클로즈업. 두 색 판 아래에 깔아 같은 빛을 받게 한다
 put('Image','SdFace',[12,65,490,575],{texture:'',imageFit:'contain',opacity:1});
 put('Panel','SdLeft',[0,0,640,720],{background:'#6b12434a'});
 put('Image','SdRight',[640,0,640,720],{texture:'Assets/Art/ui/showdown_grid.svg',imageFit:'fill'});
 put('Image','SdDivider',[616,0,48,720],{texture:'Assets/Art/ui/showdown_divider.svg',imageFit:'fill'});
 put('Image','SdBladeFrame',[8,535,550,183],{texture:'Assets/Art/ui/showdown_blade.svg',imageFit:'contain'});
 for(const id of ['BladeName','SpkName','Slash'])v.nodes.find(n=>n.id===id).slot.zIndex=30;
 await emitArmamentHud({write,put});
 put('Image','ArmFace',ARMAMENT_PLAYER_RECT,{texture:'',imageFit:'contain'}); // Face sits left of the source-aligned tension fan.
 // 패닉 논의(V3) : 열마다 카메라 하나, 화면은 대본 CDV 가 만든 세 영역(역분석 05 「패닉의 세 카메라」, v3_re/native/panic_pane_bindings_findings.json).
 // 1장 c01_206_000 CDV(-100,-150,35,-35,…,폭10) 를 네이티브 식으로 계산한 세 영역을 1280×720 으로 옮긴 것(경계 사이 틈 = 폭 10/1.5).
 // 배경은 실제 3D 재판장(패닉 카메라가 창·기둥을 비춘다), 화자 입상은 clipPolygon 으로 자기 영역 안에만 그린다.
 {const pw=createWidgetAsset('W_PanicPanes');pw.scaleMode='scale';pw.scaleRule='fit';
  const pput=(type,id,rect,props={})=>{const n=createWidgetNode(type,id,'root');n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:false,...props});pw.nodes.push(n);return n;};
  const panes=[[[0,0],[757,0],[249,720],[0,720]],[[765,0],[1280,0],[1280,720],[1230,720],[579,264]],[[575,269],[1222,720],[258,720]]];
  const figs=[[-10,-30,800,1640],[790,-40,620,1270],[580,290,560,1150]]; // 영역마다 머리~가슴만 들어오는 근접(V3 26:06), 몸은 화면·영역 밖으로
  const lines='<path d="M761 0L253 720" stroke="#ff2a3a" stroke-width="5"/><path d="M577 266L1226 720" stroke="#ff2a3a" stroke-width="5"/>';
  for(let i=0;i<3;i++){const pts=panes[i].map(p=>p.join(',')).join(' ');
   await write(`Assets/Art/ui/panic_${i}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"><polygon points="${pts}" fill="${['#ff4a1e','#ff7a2a','#ff2a5a'][i]}" fill-opacity=".13"/>${i===0?lines:''}</svg>`);
   const [fx,fy,fw,fh]=figs[i];
   pput('Image','PanicFig'+i,figs[i],{texture:'',imageFit:'contain',opacity:1,clipPolygon:panes[i].flatMap(([x,y])=>[x-fx,y-fy])});
   pput('Image','PanicFrame'+i,[0,0,1280,720],{texture:`Assets/Art/ui/panic_${i}.svg`,imageFit:'fill'});
   pput('Text','PanicName'+i,[[30,22,300,40],[790,22,140,40],[600,668,300,40]][i],{font:head,fontSize:26,color:'#ffffff',outlineColor:'#000000',outlineWidth:4});}
  // 영역 위젯은 게임 시작 때 메인 HUD 보다 먼저 표시된다(Yumeno.cpp) : 3D 바로 위, HUD·발언 글자 아래(V3 와 같은 겹침 순서)
  await write('Assets/UI/PanicPanes.hbwidget.json',pw);}
 // 투표 슬롯머신(V3) : 얼굴 세 칸이 돌다가 멈춘다
 await write('Assets/Art/ui/slot_frame.svg','<svg xmlns="http://www.w3.org/2000/svg" width="900" height="320"><rect x="6" y="6" width="888" height="308" rx="30" fill="#16121c" stroke="#ffd21f" stroke-width="12"/>'+[0,1,2].map(i=>`<rect x="${40+i*280}" y="40" width="260" height="240" rx="16" fill="#0b0812" stroke="#ff4fa3" stroke-width="6"/>`).join('')+'</svg>');
 put('Image','SlotFrame',[190,200,900,320],{texture:'Assets/Art/ui/slot_frame.svg',imageFit:'fill'});
 for(let i=0;i<3;i++)put('Image','Reel'+i,[236+i*280,246,252,232],{texture:'',imageFit:'cover'});
 put('Text','SlotTitle',[0,120,1280,70],{font:head,fontSize:52,align:'center',color:'#ffd21f',text:'투표 결과'});
 put('Text','StageMsg',[0,300,1280,90],{font:head,fontSize:60,align:'center',color:'#ff8fc8'});
 put('Text','StageTimer',[1040,656,220,48],{font:'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf',fontSize:40,color:'#ffb21f',align:'right'});
 await (await import('./v4-intro-explore-source-ui.mjs')).emitIntroExploreSourceUI({write});
 put('Panel','IntroTop',[0,-24,1280,24],{background:'#08060eff'});
 put('Panel','IntroBottom',[0,702,1280,18],{background:'#08060eff'});
 put('Image','IntroStreaks',[-190,280,1660,180],{texture:'Assets/Art/ui/nonstop_streaks.svg',imageFit:'fill'});
 // Separate blue afterimages and black letters: last character enters first.
 for(let i=0;i<5;i++){
  put('Image','IntroGlow'+i,[0,220,256,300],{texture:`Assets/Art/ui/nonstop_glow${i}.svg`,imageFit:'contain'});
  put('Image','IntroGlyph'+i,[0,220,256,300],{texture:`Assets/Art/ui/nonstop_glyph${i}.svg`,imageFit:'contain'});
 }
 put('Image','IntroHoop',[240,-40,800,800],{texture:'Assets/Art/ui/nonstop_hoop.svg',imageFit:'contain'});
 put('Image','IntroHoop2',[240,-40,800,800],{texture:'Assets/Art/ui/nonstop_hoop.svg',imageFit:'contain'});
 put('Image','IntroStartEcho',[360,230,560,240],{texture:'Assets/Art/ui/nonstop_start_echo.svg',imageFit:'contain'});
 put('Image','IntroStart',[360,230,560,240],{texture:'Assets/Art/ui/nonstop_start.svg',imageFit:'contain'});
 put('Panel','IntroFade',[0,0,1280,720],{background:'#08060eff'});
 put('Image','IntroGun',[-180,235,600,600],{texture:'Assets/Art/ui/kotodama_cylinder.svg',imageFit:'contain'});
 for(let i=0;i<6;i++){
  const color=['#36ddff','#ff57c9','#2179ff','#ffb534','#f45fca','#83ff4f'][i];
  await write(`Assets/Art/ui/intro_in_bullet${i}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="720" height="36"><title>Unnamed ambient round</title><path d="M0 14H590M110 24H590" stroke="${color}" stroke-width="2" opacity=".8"/><path d="M520 10H605Q625 10 630 18Q625 26 605 26H520Z" fill="${color}"/><path d="M527 11V25M534 11V25M602 12V24" fill="none" stroke="#e3faff" stroke-opacity=".8" stroke-width="2"/><path d="M539 12H599" stroke="#ffffff" stroke-width="2" opacity=".7"/></svg>`);
 }
 for(let i=0;i<32;i++)put('Image','IntroInBullet'+i,[-900,75+(i%8)*77,720,36],{texture:`Assets/Art/ui/intro_in_bullet${i%6}.svg`,imageFit:'fill'});
 await write('Assets/Art/ui/intro_round.svg','<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48"><circle cx="24" cy="24" r="18" fill="#41dff0" stroke="#ecfdff" stroke-width="3"/><circle cx="24" cy="24" r="8" fill="#102e42" stroke="#c5faff" stroke-width="2"/></svg>');
 for(let i=0;i<5;i++)put('Image','IntroRound'+i,[0,0,28,28],{texture:'Assets/Art/ui/intro_round.svg',imageFit:'contain'});
 const ammoList=put('Canvas','IntroAmmoList',[0,0,720,560]);ammoList.slot.alignment=[.5,.5];
 for(let i=0;i<9;i++){
  put('Canvas','IntroAmmoRow'+i,[0,i*62,720,50],{},'IntroAmmoList');
  put('Image','IntroAmmoPlate'+i,[0,0,420,50],{texture:'Assets/Art/ui/kotodama_plate.svg',imageFit:'fill',nineSlice:[24,0,24,0]},'IntroAmmoRow'+i);
  put('Text','IntroAmmoText'+i,[34,7,365,36],{font:head,fontSize:25,color:'#102c46',wrap:false},'IntroAmmoRow'+i);
 }
 put('Image','IntroSelectedPlate',[122,626,420,50],{texture:'Assets/Art/ui/kotodama_plate.svg',imageFit:'fill',nineSlice:[24,0,24,0]});
 put('Text','IntroSelectedText',[156,633,370,36],{font:head,fontSize:25,color:'#102c46',wrap:false});
 // All animated intro nodes stay on their small separate owner, not Stage/Driver.
 const intro=createWidgetAsset('W_Intro');intro.scaleMode='scale';intro.scaleRule='fit';
 intro.nodes.push(...v.nodes.filter(n=>n.name.startsWith('Intro')));
 v.nodes=v.nodes.filter(n=>!n.name.startsWith('Intro'));
 await write('Assets/UI/Intro.hbwidget.json',intro);
 await emitSpotVisuals({write});await emitReasoningVisuals({write});await emitArmamentText({write});await write('Assets/UI/Stage.hbwidget.json',applyArmamentInkNode(applyArmamentTextStyle(applyReasoningStage(applySpotStage(applyMineStage(v))))));
}
await emitPanicShowdownSource({write});
await emitVoteUI({write,body,head});
await emitTrialInputMotionUI({repo,write,read:async file=>JSON.parse(await fs.readFile(path.join(root,file),'utf8'))});await finalizeVoteTVUI({repo,write,read:async file=>JSON.parse(await fs.readFile(path.join(root,file),'utf8'))});
// 4-3) 진행 위젯 W_Flow : 장 제목 카드, 보기 목록, 인물·선물 칸, 알림, 코인, 크레딧. 좌표는 Source/Flow.hpp 와 같다.
{
 const f=createWidgetAsset('W_Flow');f.scaleMode='scale';f.scaleRule='fit';
 const put=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:false,...props});f.nodes.push(n);return n;};
 put('Panel','FCardBack',[0,0,1280,720],{background:'#0b0812'});
 put('Image','FCard',[0,0,1280,720],{texture:'',imageFit:'cover'});
 put('Text','FCardT',[0,250,1280,120],{font:head,fontSize:84,align:'center',color:'#ff8fc8'});
 put('Text','FCardS',[0,380,1280,50],{font:head,fontSize:30,align:'center',color:'#efe6f4'});
 put('Image','FHudImg',[0,0,1280,720],{texture:explorationHudLayout.variants.day0,imageFit:'fill'});
 put('Image','FHudGauge',[0,0,1280,720],{texture:'Assets/Art/ui/v3/exploration/gauge_0.svg',imageFit:'fill'});
 put('Text','FHud',explorationHudLayout.sourceLeaves.find(l=>l.path==='p_yazirusi/p_chapter/d1').rect,{font:head,fontSize:22});
 put('Text','FHudSub',explorationHudLayout.level,{fontSize:explorationHudLayout.ownReadableLevelFont,align:'left',color:'#ffffff'});
 put('Image','FLevelUp',[0,0,1280,720],{texture:'Assets/Art/ui/v3/level_up/in_0.svg',imageFit:'fill'});
 put('Panel','FShade',[0,0,1280,720],{background:'#05030a99'});
 put('Text','FMenuQ',[200,120,880,56],{font:head,fontSize:30,align:'center',background:'#0b1018e6'});
 for(let i=0;i<9;i++){put('Image','FOptP'+i,[730.66667,352,586.66667,50],{texture:'Assets/Art/ui/v3/choice_off.svg',imageFit:'fill',background:'#00000000'});put('Image','FOptA'+i,[731.33333,352,586.66667,50],{texture:'Assets/Art/ui/v3/choice_on.svg',imageFit:'fill',background:'#00000000'});put('Image','FOptC'+i,[740,358.66667,40,40],{texture:'Assets/Art/ui/v3/choice_check.svg',imageFit:'contain',background:'#00000000'});put('Text','FOptT'+i,[793.33333,363.33333,400,34.66667],{fontSize:26.66667,wrap:false});}
 put('Text','FGridHead',[160,40,960,50],{font:head,fontSize:32,align:'center',color:'#ff8fc8'});
 for(let i=0;i<16;i++){const x=150+(i%4)*250,y=110+Math.floor(i/4)*130;put('Panel','FCell'+i,[x,y,236,120],{background:'#0b1018e6',borderWidth:2,borderColor:'#36e3ff',radius:8});put('Image','FFace'+i,[x+6,y+6,108,108],{texture:'',imageFit:'cover'});put('Text','FName'+i,[x+118,y+14,112,94],{font:head,fontSize:20,wrap:true});}
 put('Text','FGridFoot',[160,640,960,40],{fontSize:22,align:'center',color:'#ffe9a8',background:'#0b1018cc'});
 put('Text','FToast',[340,24,600,46],{font:head,fontSize:24,align:'center',color:'#16121c',background:'#ffe36ee8',radius:8});
 put('Text','FCredits',[140,60,1000,600],{fontSize:26,align:'center',wrap:true,color:'#efe6f4'});
 await write('Assets/UI/Flow.hbwidget.json',f);
}
// 4-4) 탐색 위젯 W_Explore (docs/spec/16 §1-1·§5-2) : 1인칭 방 시점·조준점·이름표·장소 띠·미니맵 / 지도(이동) / 예·아니오 / 언령 획득 / 띠 연출
{
 const e=createWidgetAsset('W_Explore');e.scaleMode='scale';e.scaleRule='fit';
 const put=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:false,...props});e.nodes.push(n);return n;};
 const svg=(name,b,w,h)=>write(`Assets/Art/ui/${name}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">${b}</svg>`);
 // ex_cross is emitted from the admitted original ADV source family above.
 // ex_cross_on is emitted from the admitted original ADV source family above.
 await svg('ex_label','<path d="M22 0H749V84H0V22Z" fill="#000000" fill-opacity=".898438"/>',749,84);
 await svg('ex_area','<path d="M0 0H430L400 52H0z" fill="#ffd21f"/><path d="M0 52H400" stroke="#16121c" stroke-width="3"/>',430,56);
 await svg('ex_area_icon','<path d="M14 92V48h18V30h34v18h18v44z" fill="#16121c"/><path d="M48 4v18M24 14l8 12M72 14l-8 12" stroke="#ff7a1a" stroke-width="6" stroke-linecap="round"/><circle cx="48" cy="34" r="10" fill="#ff7a1a"/><path d="M22 60h12M44 60h12M66 60h12M22 76h12M44 76h12M66 76h12" stroke="#ffd21f" stroke-width="5"/>',96,96);
 await svg('ex_mini','<path d="M100 4L196 100L100 196L4 100z" fill="#0b1018" fill-opacity=".72" stroke="#ffffff" stroke-width="3"/><path d="M100 30L170 100L100 170L30 100z" fill="none" stroke="#36e3ff" stroke-opacity=".5" stroke-width="2"/>',200,200);
 await svg('ex_arrow','<path d="M4 30L40 4V56z" fill="#ffffff" fill-opacity=".55"/>',44,60);
 await svg('map_item','<path d="M16 0H520L504 54H0z" fill="#0b1018" fill-opacity=".86"/><path d="M16 1H520" stroke="#ff4fa3" stroke-width="3"/>',520,56);
 await svg('map_item_on','<path d="M16 0H520L504 54H0z" fill="#ff4fa3" fill-opacity=".92"/><path d="M16 1H520M0 53H504" stroke="#ffffff" stroke-width="3"/>',520,56);
 await svg('confirm','<path d="M30 0H720L690 200H0z" fill="#0b1018" fill-opacity=".94"/><path d="M30 2H718" stroke="#ffd21f" stroke-width="4"/><path d="M0 198H690" stroke="#ffd21f" stroke-width="2"/>',720,200);
 await svg('kget_glow','<defs><radialGradient id="g"><stop offset="0" stop-color="#fff6c8" stop-opacity=".9"/><stop offset=".6" stop-color="#ffd21f" stop-opacity=".25"/><stop offset="1" stop-color="#ffd21f" stop-opacity="0"/></radialGradient></defs><circle cx="300" cy="300" r="300" fill="url(#g)"/>'+Array.from({length:16},(_,i)=>{const a=i*Math.PI/8;return `<path d="M300 300L${300+300*Math.cos(a-.05)} ${300+300*Math.sin(a-.05)}L${300+300*Math.cos(a+.05)} ${300+300*Math.sin(a+.05)}z" fill="#fff6c8" fill-opacity=".25"/>`;}).join(''),600,600);
 await svg('kget_band','<path d="M0 0H1280V110H0z" fill="#0b1018" fill-opacity=".9"/><path d="M0 2H1280M0 108H1280" stroke="#ffd21f" stroke-width="4"/>',1280,110);
 for(const [k,t,c] of [['free','自由行動  ·  자유행동','#36e3ff'],['inv','捜査開始  ·  수사 개시','#ff2a6d'],['invend','捜査終了  ·  수사 종료','#ff2a6d'],['body','死体発見  ·  시체 발견','#d81f2a']])
  await svg('band_'+k,`<path d="M0 30L1280 0V130L0 160Z" fill="#05020a" fill-opacity=".92"/><path d="M0 30L1280 0M0 160L1280 130" stroke="${c}" stroke-width="6"/><text x="640" y="104" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-weight="900" font-size="64" fill="#ffffff" stroke="${c}" stroke-width="2" transform="rotate(-1.4 640 80)">${t}</text>`,1280,160);
 put('Image','ExBg',[-160,-90,1600,900],{texture:'',imageFit:'cover'});
 for(let i=0;i<6;i++){const n=put('Image','Fig'+i,[0,0,240,520],{texture:'',imageFit:'contain'});n.slot.alignment=[.5,1];}
 for(let i=0;i<10;i++){const n=put('Image','Spark'+i,[0,0,30,30],{texture:'Assets/Art/ui/vpoint.svg',imageFit:'contain',opacity:.7});n.slot.alignment=[.5,.5];}
 put('Image','ArL',[8,330,44,60],{texture:'Assets/Art/ui/ex_arrow.svg',imageFit:'contain'});
 {const n=put('Image','ArR',[1228,330,44,60],{texture:'Assets/Art/ui/ex_arrow.svg',imageFit:'contain',rotation:180});}
 put('Image','AreaBand',[0,20,430,56],{texture:'Assets/Art/ui/ex_area.svg',imageFit:'fill'});
 put('Image','AreaIcon',[8,4,90,90],{texture:'Assets/Art/ui/ex_area_icon.svg',imageFit:'contain'});
 put('Text','AreaName',[104,28,300,40],{font:head,fontSize:26,color:'#16121c'});
 put('Image','Mini',[1080,500,180,180],{texture:'Assets/Art/ui/ex_mini.svg',imageFit:'fill'});
 // The shipped native interface still addresses ExHint; retire its parent.
 {const retired=put('Canvas','RetiredExploreHints',[0,0,1280,720],{visible:false});const hint=put('Text','ExHint',[24,676,1080,30],{fontSize:16,color:'#00000000',visible:false});hint.parent=retired.id;}
 for(let i=0;i<10;i++){const n=put('Panel','MiniDot'+i,[0,0,12,12],{background:'#ffd21f',radius:6});n.slot.alignment=[.5,.5];}
 put('Image','LblBand',explorationHudLayout.target.name_backdrop_rect_1280,{texture:'Assets/Art/ui/ex_label.svg',imageFit:'fill'});
 put('Text','LblText',explorationHudLayout.target.target_name_text_rect_1280,{font:head,fontSize:30,align:'center',color:'#ffffff'});
 {const n=put('Image','Cross',[0,0,200,200],{texture:'Assets/Art/ui/ex_cross.svg',imageFit:'contain'});n.slot.alignment=[.5,.5];}
 // 지도 : 왼쪽 지도 그림, 오른쪽 장소 목록(얼굴 아이콘)
 put('Panel','MapBack',[0,0,1280,720],{background:'#08122af2'});
 put('Image','MapImg',[34,120,640,400],{texture:'',imageFit:'contain'});put('Text','MapPlace',[34,530,640,44],{font:head,fontSize:30,color:'#ffffff'});put('Text','MapWho',[34,578,640,60],{fontSize:20,color:'#cfe8ff',wrap:true});
 put('Text','MapHead',[30,24,700,56],{font:head,fontSize:40,color:'#ff4fa3',text:'MAP'});
 put('Text','MapSub',[34,78,640,30],{fontSize:20,color:'#cfe8ff'});
 for(let i=0;i<9;i++){const y=96+i*62;put('Image','MapP'+i,[700,y,520,56],{texture:'Assets/Art/ui/map_item.svg',imageFit:'fill'});put('Text','MapT'+i,[728,y+10,300,36],{font:head,fontSize:24});
  for(let k=0;k<4;k++)put('Image',`MapF${i}_${k}`,[1040+k*44,y+6,42,42],{texture:'',imageFit:'cover',radius:21});}
 put('Text','MapHint',[700,668,560,30],{fontSize:18,color:'#ffffff',align:'right'});
 // 예·아니오
 put('Panel','CfShade',[0,0,1280,720],{background:'#05030a99'});
 put('Image','CfBox',[280,240,720,200],{texture:'Assets/Art/ui/confirm.svg',imageFit:'fill'});
 put('Text','CfText',[320,268,640,70],{font:head,fontSize:30,align:'center',wrap:true});
 put('Image','CfYesP',[380,360,220,50],{texture:'Assets/Art/ui/map_item_on.svg',imageFit:'fill'});put('Text','CfYes',[380,366,220,38],{font:head,fontSize:26,align:'center',text:'예'});
 put('Image','CfNoP',[660,360,220,50],{texture:'Assets/Art/ui/map_item.svg',imageFit:'fill'});put('Text','CfNo',[660,366,220,38],{font:head,fontSize:26,align:'center',text:'아니오'});
 // 언령 획득 : 빛 + 카드 + 이름 띠
 put('Panel','KShade',[0,0,1280,720],{background:'#05030acc'});
 {const n=put('Image','KGlow',[340,60,600,600],{texture:'Assets/Art/ui/kget_glow.svg',imageFit:'contain'});}
 put('Image','KFrame',[490,130,300,410],{texture:'Assets/Art/ui/kotodama/frame_evidence.png',imageFit:'fill'});
 put('Image','KCard',[512,196,256,256],{texture:'',imageFit:'contain'});
 put('Image','KBand',[0,560,1280,110],{texture:'Assets/Art/ui/kget_band.svg',imageFit:'fill'});
 put('Text','KTitle',[0,570,1280,48],{font:head,fontSize:38,align:'center',color:'#ffd21f'});
 put('Text','KMsg',[0,620,1280,36],{fontSize:22,align:'center',color:'#ffffff'});
 // 띠 연출 (자유행동·수사 개시·수사 종료·시체 발견)
 put('Image','Band',[0,280,1280,160],{texture:'Assets/Art/ui/band_free.svg',imageFit:'fill'});
 put('Panel','Flash',[0,0,1280,720],{background:'#d81f2acc'});
 await write('Assets/UI/Explore.hbwidget.json',e);
}
console.log(JSON.stringify(await emitMineV4({write})));
await emitMineVisuals({write});
await installV4StoryUI({write,copy,body,head});
await emitOptionsV4({repo,copy,write});
await copy('art/sprites_nai_v4/lappy/lappy_L01.webp','Assets/Art/v4/lappy.webp');
// 4-5) 래피 패드 W_Pad (V3 모노패드 배치, docs/spec/16 §5-2) : 아래 둥근 아이콘 6, 위 머리 띠(얼굴·제목·말풍선·큰 아이콘), 오른쪽 세로 띠(코인·이름)
{
 const d=createWidgetAsset('W_Pad');d.scaleMode='scale';d.scaleRule='fit';
 const put=(type,id,rect,props={},parent='root')=>{const n=createWidgetNode(type,id,parent);n.name=id;n.slot.offset=rect;Object.assign(n.properties,{text:'',font:body,fontSize:24,color:'#ffffff',background:'#00000000',padding:0,focusable:false,visible:false,...props});d.nodes.push(n);return n;};
 const svg=(name,b,w,h)=>write(`Assets/Art/ui/${name}.svg`,`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">${b}</svg>`);
 const ring=(c,inner)=>`<circle cx="70" cy="70" r="64" fill="#16121c" stroke="#ffffff" stroke-width="5"/><circle cx="70" cy="70" r="52" fill="${c}" fill-opacity=".22" stroke="${c}" stroke-width="4"/>${inner}`;
 const ICONS={
  map:['#ff2a4d','<circle cx="70" cy="70" r="30" fill="none" stroke="#ff2a4d" stroke-width="6"/><path d="M40 70h60M70 40v60M48 52c14 8 30 8 44 0M48 88c14-8 30-8 44 0" stroke="#ff2a4d" stroke-width="4" fill="none"/>'],
  bullet:['#d8d8e0','<path d="M52 98V56l18-20 18 20v42z" fill="#d8d8e0"/><path d="M52 66h36" stroke="#16121c" stroke-width="4"/>'],
  gift:['#36b6ff','<rect x="42" y="58" width="56" height="40" fill="#36b6ff"/><rect x="38" y="48" width="64" height="14" fill="#9fe0ff"/><path d="M70 48v50" stroke="#ffffff" stroke-width="6"/><path d="M70 48c-10-14-26-10-20 0M70 48c10-14 26-10 20 0" stroke="#ffffff" stroke-width="5" fill="none"/>'],
  card:['#ff2a4d','<circle cx="56" cy="52" r="9" fill="#ff2a4d"/><path d="M44 98V70q12-10 24 0v28z" fill="#ff2a4d"/><circle cx="84" cy="52" r="9" fill="#ff8fc8"/><path d="M72 98V70q12-10 24 0v28z" fill="#ff8fc8"/>'],
  rules:['#36b6ff','<path d="M40 86l30-46 30 46z" fill="none" stroke="#36b6ff" stroke-width="6"/><path d="M48 70l16 10 26-30" stroke="#ffffff" stroke-width="6" fill="none"/>'],
  option:['#b0b8c8','<circle cx="80" cy="60" r="16" fill="none" stroke="#b0b8c8" stroke-width="8" stroke-dasharray="7 5"/><path d="M44 96l30-30" stroke="#36b6ff" stroke-width="10" stroke-linecap="round"/>']};
 for(const [k,[c,inner]] of Object.entries(ICONS))await svg('pad_'+k,ring(c,inner),140,140);
 await svg('pad_head','<path d="M0 0H1060V170H0z" fill="#0b0f1a" fill-opacity=".92"/><path d="M0 168H1060" stroke="#ffffff" stroke-opacity=".3" stroke-width="2"/>',1060,170);
 await svg('pad_bubble','<path d="M18 4H540Q556 4 556 20V120Q556 136 540 136H40L18 160V20Q18 4 34 4z" fill="#ffffff" stroke="#16121c" stroke-width="4"/>',560,164);
 await svg('pad_side','<path d="M0 0H140V720H0z" fill="#08070c"/><path d="M10 0V720M130 0V720" stroke="#ffffff" stroke-opacity=".5" stroke-width="2"/>',140,720);
 await svg('pad_floor','<defs><linearGradient id="f" x2="0" y2="1"><stop stop-color="#1a1030"/><stop offset="1" stop-color="#05030a"/></linearGradient></defs><rect width="1140" height="720" fill="url(#f)"/>'+Array.from({length:12},(_,i)=>`<path d="M${i*110-200} 720L${i*110+300} 300" stroke="#ffffff" stroke-opacity=".05" stroke-width="40"/>`).join(''),1140,720);
 await svg('pad_row','<path d="M14 0H720L706 40H0z" fill="#0b0f1a" fill-opacity=".86"/><path d="M14 1H720" stroke="#ffffff" stroke-opacity=".25"/>',720,42);
 await svg('pad_row_on','<path d="M14 0H720L706 40H0z" fill="#ff2a4d" fill-opacity=".9"/>',720,42);
 put('Image','PdFloor',[0,0,1280,720],{texture:'Assets/Art/ui/v3/pad_floor.png',imageFit:'fill'});
 put('Image','PdThemeHome',[0,0,1280,720],{texture:'',imageFit:'fill'});
 put('Panel','PdTint',[0,0,1140,720],{background:'#ff2a4d22'});
 put('Image','PdHead',[40,30,1060,170],{texture:'Assets/Art/ui/pad_head.svg',imageFit:'fill'});
 put('Image','PdFace',[52,38,190,154],{texture:'',imageFit:'contain'});
 put('Text','PdTitle',[262,44,600,60],{font:head,fontSize:42,color:'#ff2a4d'});
 put('Image','PdBubble',[256,92,560,164],{texture:'Assets/Art/ui/v3/pad_bubble.png',imageFit:'fill'});
 put('Text','PdDesc',[290,106,500,110],{fontSize:22,color:'#16121c',wrap:true});
 put('Image','PdBig',[880,40,160,160],{texture:'',imageFit:'contain'});
 for(let i=0;i<6;i++)put('Image','PdIcon'+i,[60+i*170,470,140,140],{texture:'',imageFit:'contain'});
 put('Image','PdSide',[1140,0,140,720],{texture:'Assets/Art/ui/pad_side.svg',imageFit:'fill'});
 put('Text','PdCoins',[1150,24,120,60],{font:'Assets/Fonts/dohyeon/DoHyeon-Regular.ttf',fontSize:22,align:'center',color:'#ffffff',wrap:true});
 put('Text','PdName',[1150,110,120,120],{font:head,fontSize:34,align:'center',color:'#ffffff',wrap:true,text:'래피\nPAD'});
 put('Text','PdSchool',[1150,240,120,80],{fontSize:14,align:'center',color:'#ffffff',wrap:true,text:'유메노쿠니\n전자 수첩'});
 put('Text','PdHintShadow',[761.5,677.5,370,30],{fontSize:18,color:'#000000',align:'right'});
 put('Text','PdHint',[760,676,370,30],{fontSize:18,color:'#ffffff',align:'right'});
 // 하위 화면 : 목록(왼쪽) + 그림·제목·설명(오른쪽) / 통신부 실루엣 줄
 for(let i=0;i<12;i++){put('Image','PdRowP'+i,[60,230+i*36,560,34],{texture:'Assets/Art/ui/pad_row.svg',imageFit:'fill'});put('Text','PdRowT'+i,[84,234+i*36,520,28],{fontSize:20});}
 put('Image','PdPic',[660,220,440,260],{texture:'',imageFit:'contain'});
 put('Text','PdPicTitle',[660,488,460,36],{font:head,fontSize:28,color:'#ffffff'});
 put('Text','PdPicText',[660,528,460,140],{fontSize:19,color:'#e6f2ff',wrap:true});
 for(let i=0;i<15;i++)put('Image','PdSil'+i,[60+i*70,220,64,64],{texture:'',imageFit:'cover',radius:32});
 put('Text','PdLevel',[60,300,560,360],{fontSize:21,color:'#ffffff',wrap:true});
 put('Image','PdStand',[690,390,175,240],{texture:'',imageFit:'cover'});
 await write('Assets/UI/Pad.hbwidget.json',d);
}
{ // 브레인 드라이브·스크럼 그림 (원근 네온 도로, 차, 띠)
 await write('Assets/Art/ui/taxi_road.svg','<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"><defs><linearGradient id="sky" x2="0" y2="1"><stop stop-color="#07021a"/><stop offset=".45" stop-color="#2a0b45"/><stop offset="1" stop-color="#05020f"/></linearGradient></defs><rect width="1280" height="720" fill="url(#sky)"/>'+Array.from({length:60},(_,i)=>`<circle cx="${(i*197)%1280}" cy="${(i*71)%230}" r="${1+i%3*.6}" fill="#fff" opacity=".7"/>`).join('')+'<path d="M600 250H680L1260 720H20Z" fill="#12082a"/><path d="M600 250L20 720M680 250L1260 720" stroke="#ff4fa3" stroke-width="8"/><path d="M627 250L407 720M653 250L873 720" stroke="#36e3ff" stroke-width="2" opacity=".35"/>'+Array.from({length:10},(_,i)=>{const y=250+Math.pow(i/10,1.8)*470;return `<path d="M0 ${y}H1280" stroke="#a46bff" stroke-opacity="${.08+i*.02}"/>`;}).join('')+'</svg>');
 await write('Assets/Art/ui/taxi_car.svg','<svg xmlns="http://www.w3.org/2000/svg" width="240" height="150"><path d="M30 120V80l30-40h120l30 40v40z" fill="#ff4fa3" stroke="#fff" stroke-width="4"/><path d="M70 48h100l20 30H50z" fill="#36e3ff" opacity=".7"/><rect x="95" y="20" width="50" height="22" rx="6" fill="#ffe9a8"/><text x="120" y="37" font-size="14" text-anchor="middle" fill="#16121c" font-family="sans-serif">TAXI</text><circle cx="65" cy="122" r="18" fill="#16121c"/><circle cx="175" cy="122" r="18" fill="#16121c"/></svg>');
 await write('Assets/Art/ui/taxi_rival.svg','<svg xmlns="http://www.w3.org/2000/svg" width="160" height="110"><path d="M15 95V60l25-30h80l25 30v35z" fill="#3b2a55" stroke="#a46bff" stroke-width="4"/><rect x="30" y="68" width="22" height="10" fill="#ff2040"/><rect x="108" y="68" width="22" height="10" fill="#ff2040"/></svg>');
}

// 5) 3D 학급 재판장 장면 (docs/spec/15 §2, Source/Courtroom.hpp 와 같은 수치) + 블루프린트 (Tick → Yumeno.Update)
const R=4.08,PODIUM_INSET=.13,SPRITE=2.3,SPRITE_Y=1.25,FOV=43.6;
const SEATS=['mio','rin','ken','nana','taiga','ai','rei','sora','haruka','sho','koto','akari','riku','satsuki','yuu','kaede'];
// 재판장 소품 : 4차 그림(art/trial3d/*.webp)이 있으면 쓰고, 없으면 임시 도형
const placeholder={
 podium:'<svg xmlns="http://www.w3.org/2000/svg" width="230" height="250"><defs><linearGradient id="g" x2="1"><stop stop-color="#0d6b6e" stop-opacity=".85"/><stop offset=".5" stop-color="#4fe0d6" stop-opacity=".55"/><stop offset="1" stop-color="#0d6b6e" stop-opacity=".85"/></linearGradient></defs><rect x="18" y="40" width="194" height="210" fill="url(#g)" stroke="#b9fff6" stroke-width="3"/><rect x="0" y="18" width="230" height="30" fill="#103c46" stroke="#b9fff6" stroke-width="3"/><rect x="70" y="24" width="90" height="18" fill="#e9fffb"/><path d="M40 60v170M115 60v170M190 60v170" stroke="#b9fff6" stroke-opacity=".5" stroke-width="2"/></svg>',
 floor:'<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024"><circle cx="512" cy="512" r="512" fill="#0b2335"/>'+[470,400,330,250,170,90].map((r,i)=>`<circle cx="512" cy="512" r="${r}" fill="none" stroke="${i%2?'#1d6f9e':'#36c6e0'}" stroke-width="${i%2?14:6}"/>`).join('')+'<circle cx="512" cy="512" r="60" fill="#36c6e0" fill-opacity=".25"/></svg>',
 wall:'<svg xmlns="http://www.w3.org/2000/svg" width="768" height="1024"><rect width="768" height="1024" fill="#0c1f27"/><rect x="0" y="880" width="768" height="144" fill="#081419"/><path d="M164 820V300a220 220 0 0 1 440 0v520z" fill="#2a1030" stroke="#3fb8b0" stroke-width="10"/>'+Array.from({length:18},(_,i)=>`<rect x="${190+(i%6)*66}" y="${330+Math.floor(i/6)*150}" width="60" height="140" fill="${['#ff6fb5','#a46bff','#ffd0f0','#6fd3ff','#ff9fd0','#c58bff'][i%6]}" fill-opacity=".55"/>`).join('')+'</svg>',
 throne:'<svg xmlns="http://www.w3.org/2000/svg" width="700" height="700"><rect x="80" y="430" width="540" height="270" fill="#2a1a20" stroke="#c9a24c" stroke-width="8"/><rect x="250" y="120" width="200" height="320" rx="20" fill="#9b1c2e" stroke="#c9a24c" stroke-width="8"/><rect x="230" y="380" width="240" height="70" fill="#7a1222"/><rect x="90" y="60" width="90" height="360" fill="#b3172f"/><rect x="520" y="60" width="90" height="360" fill="#b3172f"/><circle cx="135" cy="200" r="28" fill="#f2d27a"/><circle cx="565" cy="200" r="28" fill="#f2d27a"/></svg>',
 dead:'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400"><rect x="70" y="40" width="260" height="320" fill="#2c2c34" stroke="#d9d9e0" stroke-width="10"/><path d="M110 80l180 240M290 80L110 320" stroke="#ff4fa3" stroke-width="26" stroke-linecap="round"/></svg>'};
execFileSync('python',['-X','utf8',path.join(repo,'tools/court_figures.py')],{stdio:'inherit'});
execFileSync('python',['-X','utf8',path.join(repo,'tools/scrum_faces.py')],{stdio:'inherit'}); // 스크럼 탭 속 얼굴(옆모습 입상에서 머리만)
const figures=JSON.parse(await fs.readFile(path.join(root,'Assets/Art/court_figures/manifest.json'),'utf8'));
execFileSync('python',['-X','utf8',path.join(repo,'tools/build_court_memorials.py')],{stdio:'inherit'});
execFileSync('node',[path.join(repo,'tools/export_student_id_photos.mjs')],{stdio:'inherit'});
for(const slug of 'mio rin ken nana taiga ai rei sora haruka sho koto akari riku satsuki yuu kaede'.split(' ')){
 await copy(`art/trial3d/id_portraits_color_v1/runtime/${slug}.webp`,`Assets/Art/student_ids/${slug}.webp`);
 await copy(`art/trial3d/id_portraits_color_v1/runtime/${slug}_thumb.webp`,`Assets/Art/student_ids/thumb/${slug}.webp`);
}
const memorialCatalog=JSON.parse(await fs.readFile(path.join(repo,'art/trial3d/memorial_v3/manifest.json'),'utf8'));
const prop={figures,memorials:{}};
prop.scrumFaces=await applyScrumProfiles({repo,write,figures});
for(const [slug,m] of Object.entries(memorialCatalog.characters)){
 await copy(m.file,m.texture);
 await copy(m.file.replace('.webp','_back.webp'),m.back);
 prop.memorials[slug]={texture:m.texture,back:m.back,width:m.width,height:m.height,center:m.center};
}
for(const [name,svgText] of Object.entries(placeholder)){
 const real=path.join(repo,'art/trial3d',name==='dead'?'portrait_frame.webp':name+'.webp');
 try{await fs.access(real);await copy(path.relative(repo,real),`Assets/Art/trial3d/${name}.webp`);prop[name]=`Assets/Art/trial3d/${name}.webp`;}
 catch{await write(`Assets/Art/trial3d/${name}.svg`,svgText);prop[name]=`Assets/Art/trial3d/${name}.svg`;}
}
await write('Assets/Data/court.json',prop);
const scene=makeStarterScene('유메노쿠니','3d');scene.objects=[];
Object.assign(scene.environment,{mode:'actors',skyEnabled:false,sunEnabled:false,cloudsEnabled:false,fogEnabled:false,shadowEnabled:true});
scene.objects.push({id:'SceneAntialias',name:'가장자리 부드럽게',kind:'empty',position:[0,0,0],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[makeSceneComponent('PostProcessVolume',{unbound:true,enabled:true,antiAliasing:'fxaa',aaStrength:1,bloomEnabled:false,grainEnabled:false,grainIntensity:0,chromaticAberrationEnabled:false})]});
const sprite=(id,texture,position,w,h,extra={},rotation=[0,0,0])=>({id,name:id,kind:'sprite',position,rotation,scale:[1,1,1],visible:true,components:[makeSceneComponent('SpriteRenderer',{texture,width:w,height:h,color:[1,1,1,1],shading:'unlit',toneMapping:'display',...extra})]});
scene.objects.push({id:'Camera',name:'재판 카메라',kind:'camera',position:[0,1.5,-2.3],rotation:[0,180,0],scale:[1,1,1],visible:true,components:[makeSceneComponent('Camera',{projection:'perspective',fieldOfView:FOV,main:true,near:.05,far:200})]});
// V3 논스톱 외침(영상 A 16:44·17:08) : 화자 뒤로 보라 소용돌이가 돈다. 카메라에 붙인 판이라 화자(2~5 m) 뒤·벽 앞에 그려진다
await write('Assets/Art/ui/debate_swirl.svg','<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"><defs><radialGradient id="v"><stop offset=".15" stop-color="#1a0638" stop-opacity="0"/><stop offset="1" stop-color="#120428" stop-opacity=".55"/></radialGradient></defs><rect width="1280" height="720" fill="url(#v)"/><path d="M670 360 L678 361 L686 362 L694 364 L702 366 L710 368 L718 371 L725 374 L732 378 L739 381 L745 386 L751 390 L756 395 L762 400 L766 405 L770 411 L774 417 L777 423 L780 429 L782 436 L783 442 L784 449 L784 456 L784 464 L782 471 L781 478 L778 486 L775 493 L771 501 L766 508 L761 515 L754 523 L748 530 L740 537 L732 544 L723 551 L713 558 L702 565 L691 571 L679 577 L667 583 L654 589 L640 594 L625 599 L610 604 L595 608 L579 612 L562 615 L545 618 L527 621 L509 623 L491 624 L472 626 L452 626 L433 626 L413 626 L393 625 L373 623 L353 621 L332 618 L312 615 L291 611 L270 607 L250 602 L230 596 L209 589 L189 582 L170 575 L150 567 L131 558 L112 549 L94 539 L76 528 L59 517 L42 505 L26 493 L10 480 L-4 467 L-19 453 L-32 438 L-44 424 L-56 408 L-66 392 L-76 376 L-85 360 L-93 343 L-99 325 L-105 308 L-109 290 L-113 271 L-115 253 L-116 234 L-116 215 L-114 196 L-112 177 L-108 157 L-102 138 L-96 118 L-88 99 L-78 79 L-68 60 L-56 41 L-43 22 L-28 3 L-12 -16 L5 -34 L24 -53 L44 -71 L65 -88 L88 -105 L111 -122 L136 -138 L163 -154 L190 -169 L219 -184 L249 -198 L280 -211 L312 -224 L345 -236 L379 -248 L414 -258 L450 -268 L486 -277 L524 -286 L562 -293 L602 -299 L641 -305 L682 -310 L723 -313 L764 -316 L806 -318 L849 -318 L891 -318 L934 -317 L977 -314 L1020 -311 L1064 -306 L1107 -301 L1150 -294 L1193 -286" fill="none" stroke="#b45cff" stroke-opacity="0.55" stroke-width="6" stroke-linecap="round"/><path d="M663 372 L668 376 L673 380 L678 385 L682 389 L685 394 L688 399 L690 405 L692 410 L693 416 L694 421 L694 427 L693 433 L692 439 L690 445 L687 451 L684 457 L680 463 L675 469 L670 475 L664 480 L658 486 L651 491 L643 497 L634 502 L625 507 L616 511 L605 516 L594 520 L583 524 L571 527 L559 530 L546 533 L533 536 L519 538 L505 540 L490 541 L475 542 L460 542 L445 542 L429 542 L413 541 L397 539 L381 537 L365 535 L348 532 L332 528 L316 524 L299 520 L283 515 L267 509 L251 503 L236 496 L220 489 L205 481 L191 473 L176 464 L162 455 L149 445 L136 435 L124 424 L112 413 L101 402 L91 390 L81 377 L72 364 L64 351 L57 337 L50 323 L45 309 L40 294 L36 279 L34 264 L32 249 L31 233 L32 217 L33 201 L36 185 L39 169 L44 152 L50 136 L57 120 L65 103 L75 87 L85 71 L97 55 L110 39 L124 23 L139 7 L155 -8 L173 -23 L192 -38 L211 -52 L232 -66 L254 -80 L278 -93 L302 -106 L327 -118 L353 -130 L380 -141 L409 -152 L438 -162 L468 -171 L499 -180 L530 -188 L563 -195 L596 -202 L630 -207 L664 -212 L699 -217 L735 -220 L771 -222 L807 -224 L844 -225 L881 -225 L919 -223 L956 -221 L994 -218 L1032 -215 L1070 -210 L1108 -204 L1145 -197 L1183 -189 L1220 -181 L1257 -171 L1294 -160 L1330 -149 L1366 -136 L1401 -123 L1436 -108 L1470 -93 L1503 -77 L1535 -59 L1567 -41 L1597 -22 L1627 -2 L1655 18 L1683 40 L1709 62 L1734 85" fill="none" stroke="#6a2bd8" stroke-opacity="0.45" stroke-width="11" stroke-linecap="round"/><path d="M645 378 L645 384 L645 389 L643 394 L642 399 L639 404 L636 409 L632 414 L628 419 L623 424 L618 429 L612 433 L605 437 L598 441 L590 445 L582 448 L573 452 L564 455 L554 457 L544 460 L534 462 L523 463 L512 465 L500 466 L489 466 L477 466 L464 466 L452 465 L440 464 L427 463 L414 461 L401 458 L388 455 L376 452 L363 448 L350 444 L338 439 L326 434 L314 428 L302 422 L290 415 L279 408 L268 401 L258 393 L248 384 L238 375 L230 366 L221 357 L213 347 L206 336 L200 326 L194 315 L189 303 L185 292 L181 280 L178 268 L177 255 L176 243 L175 230 L176 217 L178 204 L180 191 L184 177 L189 164 L194 150 L201 137 L208 124 L217 110 L227 97 L237 84 L249 71 L261 58 L275 45 L290 32 L306 20 L322 8 L340 -4 L359 -15 L378 -26 L399 -37 L420 -47 L443 -56 L466 -66 L490 -74 L515 -83 L540 -90 L567 -97 L594 -104 L622 -110 L650 -115 L679 -120 L709 -123 L739 -127 L770 -129 L801 -131 L832 -132 L864 -132 L896 -131 L928 -130 L961 -127 L993 -124 L1026 -120 L1059 -116 L1091 -110 L1124 -103 L1156 -96 L1188 -88 L1220 -79 L1252 -69 L1283 -58 L1314 -46 L1344 -34 L1374 -21 L1403 -7 L1431 8 L1458 24 L1485 41 L1511 58 L1536 76 L1560 95 L1583 114 L1605 135 L1626 156 L1645 177 L1664 199 L1681 222 L1696 245 L1711 269 L1724 294 L1735 319 L1745 344 L1754 370 L1761 396 L1766 422 L1770 449 L1772 476 L1772 503 L1771 530 L1767 558 L1763 585" fill="none" stroke="#e26bff" stroke-opacity="0.35" stroke-width="16" stroke-linecap="round"/><path d="M625 376 L620 380 L614 384 L607 387 L601 391 L593 394 L586 396 L578 399 L569 401 L561 402 L552 404 L543 405 L533 405 L524 405 L514 405 L504 405 L494 404 L484 402 L473 401 L463 398 L453 396 L443 393 L433 389 L424 385 L414 381 L405 376 L396 371 L387 366 L378 360 L370 354 L363 347 L355 340 L349 333 L342 325 L337 317 L331 309 L327 300 L323 291 L319 282 L317 272 L315 263 L314 253 L313 243 L313 233 L315 222 L316 212 L319 201 L323 191 L327 180 L332 169 L338 158 L345 148 L353 137 L362 126 L372 116 L382 105 L394 95 L406 85 L419 75 L433 65 L448 56 L464 47 L480 38 L498 30 L516 22 L535 14 L555 7 L575 -0 L596 -6 L618 -12 L640 -18 L664 -23 L687 -27 L711 -31 L736 -34 L761 -36 L787 -38 L813 -39 L840 -40 L866 -40 L893 -39 L921 -38 L948 -36 L975 -33 L1003 -29 L1031 -25 L1058 -20 L1086 -14 L1113 -7 L1140 0 L1167 8 L1194 17 L1220 27 L1246 37 L1272 48 L1297 60 L1321 73 L1345 86 L1369 100 L1391 114 L1413 130 L1434 146 L1454 163 L1473 180 L1491 198 L1508 216 L1524 235 L1539 255 L1553 275 L1566 296 L1578 317 L1588 339 L1597 361 L1604 383 L1610 406 L1615 429 L1618 452 L1620 476 L1621 500 L1620 524 L1617 548 L1613 572 L1607 596 L1600 620 L1591 645 L1580 669 L1568 693 L1554 717 L1539 741 L1522 765 L1503 788 L1483 811 L1462 834 L1438 856 L1413 878 L1387 900 L1359 921 L1330 941 L1299 961 L1266 980" fill="none" stroke="#b45cff" stroke-opacity="0.55" stroke-width="6" stroke-linecap="round"/><path d="M612 366 L604 367 L595 368 L587 368 L578 368 L570 367 L561 366 L552 365 L544 363 L536 361 L527 358 L519 355 L511 352 L504 348 L496 344 L489 340 L483 335 L476 330 L470 325 L465 319 L460 313 L455 307 L451 300 L448 293 L445 286 L443 279 L441 271 L440 264 L440 256 L440 248 L441 240 L443 231 L445 223 L448 215 L452 206 L457 198 L462 189 L468 181 L475 172 L483 164 L492 156 L501 148 L511 140 L522 132 L533 125 L546 118 L559 110 L573 104 L587 97 L602 91 L618 85 L635 80 L652 75 L669 70 L688 66 L707 62 L726 59 L746 56 L766 54 L787 52 L808 51 L829 50 L851 50 L873 50 L896 51 L918 53 L941 55 L963 58 L986 62 L1009 66 L1032 71 L1055 76 L1077 82 L1100 89 L1122 97 L1144 105 L1165 114 L1187 123 L1208 133 L1228 144 L1248 155 L1267 167 L1286 180 L1304 193 L1321 207 L1338 221 L1354 236 L1369 251 L1383 267 L1396 284 L1409 301 L1420 318 L1430 336 L1439 354 L1447 373 L1454 392 L1460 411 L1465 431 L1468 451 L1470 471 L1471 492 L1470 512 L1468 533 L1465 554 L1460 575 L1454 596 L1447 617 L1438 638 L1428 659 L1416 680 L1403 701 L1388 721 L1372 742 L1355 762 L1336 782 L1316 801 L1294 821 L1271 839 L1247 858 L1221 876 L1194 893 L1166 910 L1136 926 L1105 942 L1073 957 L1040 971 L1006 985 L970 998 L934 1010 L896 1022 L858 1032 L818 1042 L778 1050 L737 1058 L695 1065 L653 1071 L610 1076 L566 1080 L522 1083 L477 1085" fill="none" stroke="#6a2bd8" stroke-opacity="0.45" stroke-width="11" stroke-linecap="round"/><path d="M612 354 L605 351 L598 348 L591 345 L585 341 L579 337 L573 333 L568 329 L563 324 L559 319 L555 314 L552 308 L550 303 L548 297 L546 291 L545 285 L545 278 L546 272 L547 265 L548 259 L551 252 L554 246 L558 239 L562 232 L567 226 L573 219 L580 213 L587 206 L595 200 L603 194 L612 188 L622 183 L633 177 L644 172 L656 167 L668 163 L681 158 L694 154 L708 151 L723 147 L738 145 L753 142 L769 140 L786 139 L802 137 L819 137 L837 136 L854 137 L872 138 L890 139 L908 141 L926 143 L945 146 L963 150 L981 154 L1000 158 L1018 164 L1036 169 L1054 176 L1072 183 L1089 190 L1107 198 L1123 207 L1140 216 L1156 225 L1171 236 L1186 246 L1201 258 L1214 270 L1228 282 L1240 295 L1252 308 L1263 322 L1273 336 L1282 350 L1290 365 L1298 381 L1304 396 L1310 412 L1315 429 L1318 445 L1320 462 L1322 479 L1322 497 L1321 514 L1319 532 L1316 549 L1311 567 L1305 585 L1298 603 L1290 621 L1281 639 L1270 657 L1258 674 L1245 692 L1231 709 L1215 726 L1198 743 L1180 760 L1160 776 L1140 792 L1118 807 L1095 823 L1071 837 L1045 852 L1019 865 L991 878 L963 891 L933 903 L903 914 L871 925 L838 935 L805 944 L771 953 L736 960 L700 967 L664 973 L626 979 L589 983 L550 987 L512 989 L472 991 L433 991 L393 991 L353 990 L312 988 L272 985 L231 980 L191 975 L150 969 L110 962 L70 953 L30 944 L-10 934 L-49 922 L-87 910 L-126 896 L-163 882 L-200 867 L-236 850" fill="none" stroke="#e26bff" stroke-opacity="0.35" stroke-width="16" stroke-linecap="round"/><path d="M625 344 L622 339 L620 334 L618 329 L617 324 L616 318 L617 313 L617 307 L619 302 L621 296 L623 291 L626 285 L630 280 L635 275 L640 270 L646 265 L652 260 L659 255 L667 250 L675 246 L684 242 L693 238 L703 234 L713 231 L724 228 L735 225 L746 223 L758 221 L771 220 L784 218 L797 218 L810 217 L824 217 L838 218 L852 219 L866 220 L880 222 L895 224 L909 227 L924 230 L938 234 L953 238 L967 243 L981 248 L995 254 L1009 260 L1022 267 L1035 274 L1048 282 L1061 290 L1073 299 L1084 308 L1095 318 L1106 328 L1115 338 L1125 349 L1133 360 L1141 372 L1148 384 L1155 396 L1160 409 L1165 422 L1169 435 L1172 449 L1175 462 L1176 476 L1176 491 L1175 505 L1174 520 L1171 534 L1167 549 L1163 564 L1157 579 L1150 594 L1142 608 L1133 623 L1123 638 L1111 653 L1099 667 L1085 681 L1071 696 L1055 709 L1039 723 L1021 736 L1002 749 L982 762 L961 774 L939 786 L916 798 L892 809 L868 819 L842 829 L815 838 L788 847 L760 855 L731 863 L701 870 L670 876 L639 881 L607 886 L575 890 L542 893 L509 896 L475 897 L441 898 L406 898 L372 897 L337 895 L302 893 L266 889 L231 885 L196 880 L161 873 L126 866 L91 858 L56 849 L22 839 L-12 829 L-45 817 L-78 804 L-111 791 L-142 776 L-173 761 L-204 745 L-233 728 L-262 710 L-289 692 L-316 672 L-342 652 L-366 631 L-390 610 L-412 587 L-433 564 L-452 540 L-470 516 L-487 491 L-503 466 L-516 440 L-529 413 L-539 386" fill="none" stroke="#b45cff" stroke-opacity="0.55" stroke-width="6" stroke-linecap="round"/><path d="M645 342 L648 337 L651 332 L656 327 L660 323 L665 319 L671 315 L677 311 L684 307 L691 304 L699 300 L707 297 L715 295 L724 293 L734 291 L743 289 L753 288 L764 287 L774 287 L785 287 L796 287 L807 288 L818 289 L829 290 L841 292 L852 295 L863 298 L875 301 L886 305 L897 309 L908 313 L918 318 L929 324 L939 330 L949 336 L958 343 L967 350 L976 357 L984 365 L992 374 L999 382 L1006 391 L1012 401 L1017 410 L1022 420 L1026 431 L1029 441 L1032 452 L1034 463 L1035 474 L1035 486 L1034 497 L1033 509 L1030 521 L1027 533 L1023 545 L1018 557 L1012 569 L1005 581 L997 593 L988 605 L978 617 L968 628 L956 640 L943 652 L930 663 L915 674 L900 685 L883 695 L866 705 L848 715 L829 724 L809 734 L788 742 L767 750 L744 758 L721 765 L698 772 L673 778 L648 784 L622 789 L596 793 L569 797 L541 800 L514 803 L485 804 L456 805 L427 806 L398 805 L368 804 L338 802 L308 800 L278 796 L248 792 L218 787 L188 781 L158 775 L128 767 L99 759 L70 750 L41 740 L12 730 L-16 718 L-43 706 L-70 693 L-97 679 L-122 665 L-147 649 L-172 633 L-195 617 L-217 599 L-239 581 L-259 562 L-279 543 L-297 523 L-314 502 L-330 481 L-345 459 L-359 437 L-371 414 L-382 391 L-391 367 L-399 343 L-406 319 L-411 294 L-414 269 L-416 244 L-416 218 L-415 193 L-412 167 L-408 141 L-401 115 L-393 89 L-384 63 L-373 37 L-360 11 L-345 -14 L-328 -40 L-310 -65 L-291 -90" fill="none" stroke="#6a2bd8" stroke-opacity="0.45" stroke-width="11" stroke-linecap="round"/><path d="M663 348 L670 345 L678 343 L686 341 L694 340 L702 338 L711 337 L720 337 L729 337 L738 337 L747 338 L756 339 L765 340 L774 342 L784 344 L793 347 L802 350 L810 353 L819 357 L827 361 L835 366 L843 371 L850 376 L857 382 L864 388 L870 394 L876 401 L881 408 L886 416 L890 423 L894 431 L896 439 L899 447 L900 456 L901 465 L902 474 L901 483 L900 492 L898 501 L895 511 L892 520 L888 530 L883 539 L877 549 L870 558 L862 568 L854 577 L845 587 L835 596 L824 605 L812 614 L800 622 L786 631 L772 639 L757 646 L742 654 L725 661 L708 668 L690 675 L672 681 L653 686 L633 691 L613 696 L592 700 L570 704 L548 707 L525 710 L502 712 L479 714 L455 715 L431 715 L407 714 L382 713 L357 712 L332 710 L307 707 L282 703 L257 699 L232 694 L207 688 L182 681 L157 674 L132 666 L108 658 L84 649 L61 639 L38 628 L15 617 L-7 605 L-29 592 L-50 579 L-70 565 L-89 550 L-108 535 L-126 519 L-143 503 L-159 486 L-174 468 L-188 450 L-201 431 L-213 412 L-224 393 L-234 373 L-242 353 L-249 332 L-255 311 L-260 289 L-263 268 L-265 246 L-266 224 L-265 202 L-262 179 L-259 157 L-253 134 L-247 111 L-238 89 L-229 66 L-217 43 L-205 21 L-190 -1 L-175 -24 L-157 -45 L-138 -67 L-118 -88 L-96 -109 L-73 -130 L-48 -150 L-22 -170 L5 -189 L34 -207 L65 -225 L96 -243 L129 -260 L164 -276 L199 -291 L236 -305 L274 -319 L313 -332 L352 -344 L393 -355" fill="none" stroke="#e26bff" stroke-opacity="0.35" stroke-width="16" stroke-linecap="round"/></svg>');
scene.objects.push({...sprite('DebateSwirl','Assets/Art/ui/debate_swirl.svg',[0,0,-6.5],11.6,6.6,{visible:false,billboard:false,blendMode:'translucent',castShadow:false}),parent:'Camera'});
lieWorldGrade(scene);
console.log(JSON.stringify({courtRoomMaterials:await emitCourtRoomMaterialAtlas({repo,write})}));
console.log(JSON.stringify({podiumMaterials:await emitPodiumMaterialAtlas({repo,write})}));
console.log(JSON.stringify({generatedSurfaces:await emitSurfaceMaterials({repo,write})}));
const model=(id,mesh,position,rotation=[0,0,0])=>({id,name:id,kind:'cube',position,rotation,scale:[1,1,1],visible:true,components:[makeSceneComponent('MeshRenderer',{mesh,castShadow:true,receiveShadow:true})]});
for(let i=0;i<2;i++){const prop=model('ExploreReaction'+i,'',[300,0,0]);prop.components[0].properties.visible=false;scene.objects.push(prop);}
const exploreGeometry=model('ExploreGeometry','',[300,0,0]);
exploreGeometry.components[0].properties.visible=false;scene.objects.push(exploreGeometry);
for(const phase of ['day','night','evening'])await copy((await fs.access(path.join(repo,'art/environment_v5/sky_'+phase+'.glb')).then(()=>true,()=>false)?'art/environment_v5/':'art/environment_v4/')+'sky_'+phase+'.glb','Assets/Art/environment/sky_'+phase+'.glb');
const skyDome=model('OutdoorSkyDome','Assets/Art/environment/sky_day.glb',[300,1.6,0]);skyDome.scale=[500,500,500];Object.assign(skyDome.components[0].properties,{visible:false,castShadow:false,receiveShadow:false,contributeGI:false});scene.objects.push(skyDome);
const finishedWorld=JSON.parse(await fs.readFile(path.join(repo,'art/space_v4/runtime_v1/world.json'),'utf8')).worldContext;
if(finishedWorld)for(const [id,mesh]of [['ExteriorContext',finishedWorld.mesh],...Object.entries(finishedWorld.landmarks).map(([id,mesh])=>['Exterior_'+id,mesh])]){const o=model(id,mesh,[300,0,0]);Object.assign(o.components[0].properties,{visible:false,contributeGI:false});scene.objects.push(o);}
for(let i=0;i<16;i++)scene.objects.push(sprite('ExplorePerson'+i,'Assets/Art/figure/rin.webp',[300,.9,0],.83,1.8,{visible:false,billboard:true,blendMode:'masked',alphaCutoff:.08,castShadow:false}));
scene.objects.push(model('CourtGeometry','Assets/Art/court3d/courtroom_stage.glb',[0,0,0]));
// V3 의논 스크럼(영상 A 1:18:36) : 재판장이 변형되어 벽이 검은 바탕 흰 원 무늬가 된다. 증언대 고리 바깥 원통(art/trial3d/scrum_backdrop, 블렌더로 만듦), 스크럼 동안만 보인다
await copy('art/trial3d/scrum_backdrop/scrum_backdrop.glb','Assets/Art/court3d/scrum_backdrop.glb');
// V3(1:18:36) : 통로 끝 붉은 왕좌에 모노쿠마(우리는 래피). 스크럼 동안만 통로 끝에 세운다
await copy('art/trial3d/throne.webp','Assets/Art/trial3d/scrum_throne.webp');
scene.objects.push(sprite('ScrumThrone','Assets/Art/trial3d/scrum_throne.webp',[0,1.45,-3.7],3.0,3.0,{visible:false,billboard:false,blendMode:'masked',alphaCutoff:.08,castShadow:false}));
{const backdrop=model('ScrumBackdrop','Assets/Art/court3d/scrum_backdrop.glb',[0,0,0]);Object.assign(backdrop.components[0].properties,{visible:false,castShadow:false,receiveShadow:false,contributeGI:false});scene.objects.push(backdrop);}
scene.objects.push({id:'CourtAmbient',name:'법정 간접광',kind:'skyLight',position:[0,0,0],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[makeSceneComponent('SkyLight',{color:[.55,.65,1,1],groundColor:[.16,.12,.28,1],intensity:1.7,realTimeCapture:false})]});
scene.objects.push({id:'CourtKey',name:'법정 상부광',kind:'directionalLight',position:[0,10,0],rotation:[-55,25,0],scale:[1,1,1],visible:true,components:[makeSceneComponent('DirectionalLight',{color:[.7,.8,1,1],intensity:2.6,castShadow:true})]});
scene.objects.push({id:'CourtFill',name:'법정 보조광',kind:'directionalLight',position:[0,7,0],rotation:[-35,-140,0],scale:[1,1,1],visible:true,components:[makeSceneComponent('DirectionalLight',{color:[.9,.55,.8,1],intensity:1.2,castShadow:false})]});
// Real scene atmosphere/cloud/sun actors, switched by the current exterior and authored phase.
for(const [phase,preset,light]of [[0,'day',3.2],[1,'night',.45],[2,'sunset',2.2]]){
 const env=environmentActorPreset({preset,skyEnabled:true,sunEnabled:true,cloudsEnabled:true,fogEnabled:true,cloudDensity:.42,shadowEnabled:true},{light},{idPrefix:'Outdoor'+phase});
 for(const o of env.objects){o.position[0]+=300;for(const c of o.components){if(c.type==='Transform')continue;c.properties.enabled=false;if(c.type==='VolumetricCloud')Object.assign(c.properties,{layerBottomHeight:38,layerHeight:10,radius:180,windSpeed:.12});if(c.type==='ExponentialHeightFog')Object.assign(c.properties,{density:.0018,heightFalloff:.02,maxOpacity:.4,startDistance:28,cutoffDistance:250});if(c.type==='SkyLight')c.properties.realTimeCapture=false;}scene.objects.push(o);}
}
// 왕좌는 증언대 머리 위로 높이 (V3 : 모노쿠마는 재판장을 내려다본다)
scene.objects.push(sprite('Host',`Assets/Art/sprites/lappy/lappy_L01.webp`,[0,4.6,-(R+2.4)],1.6,1.6,{billboard:false,blendMode:'masked',alphaCutoff:.08,castShadow:true}));
SEATS.forEach((slug,i)=>{
 const a=i*22.5*Math.PI/180;
 const f=figures[slug];
 scene.objects.push(sprite('Seat'+i,f.texture,[R*Math.sin(a),f.center,R*Math.cos(a)],f.width,f.height,{billboard:false,blendMode:'masked',alphaCutoff:.08,castShadow:true},[0,i*22.5+180,0]));
 scene.objects.push(sprite('SeatRear'+i,f.back,[(R+.004)*Math.sin(a),f.center,(R+.004)*Math.cos(a)],f.width,f.height,{billboard:false,blendMode:'masked',alphaCutoff:.08,castShadow:false},[0,i*22.5+180,0]));
 const podium=model('Podium'+i,'Assets/Art/court3d/trial_podium.glb',[(R-PODIUM_INSET)*Math.sin(a),.1,(R-PODIUM_INSET)*Math.cos(a)],[0,i*22.5+180,0]);podium.scale=[1,.82,1];scene.objects.push(podium);
});
console.log(JSON.stringify(await emitExtraV4({repo,root,write,body,head})));
await emitV4PhaseStartSource({repo,write});
await emitTrialEntryUI({write});
console.log(JSON.stringify(await emitDifficultyV4({repo,write})));
const header=await fs.readFile(path.join(root,'Source/Yumeno.h'),'utf8'),source=await fs.readFile(path.join(root,'Source/Yumeno.cpp'),'utf8');
const bp=createAsset('blueprint','BP_Yumeno');bp.settings.parentClass='Yumeno';bp.native={...parseNativeHeader(header),header,source,headerPath:'Source/Yumeno.h',sourcePath:'Source/Yumeno.cpp'};bp.nodes=[];bp.edges=[];
const tick=makeNode('tick',100,180),call=makeNode('nativeCall',400,180);call.nativeId='Yumeno.Update';bp.nodes.push(tick,call);
for(const [pin,input] of [['then','exec'],['delta','delta']]){const r=connect(bp,{node:tick.id,pin},{node:call.id,pin:input});if(!r.ok)throw Error(r.message);}
scene.objects.push({id:'Driver',name:'게임 진행',kind:'empty',position:[0,0,0],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[],blueprintAsset:'Assets/Blueprints/BP_Yumeno.hbblueprint.json'});
await write('Assets/Blueprints/BP_Yumeno.hbblueprint.json',bp);console.log(JSON.stringify(await emitRuntimeScenes(scene,write)));

let id=randomUUID();try{id=JSON.parse(await fs.readFile(path.join(root,'YumenoKuni.hbproject'),'utf8')).id;}catch(e){if(e.code!=='ENOENT')throw e;}
await write('YumenoKuni.hbproject',{version:1,engine:'HBEngine',engineVersion:'0.1.0',id,name:'YumenoKuni',startupScene:'Assets/Scenes/Title.hbscene.json',startupBlueprint:'Assets/Blueprints/BP_Yumeno.hbblueprint.json',gameInstance:'Assets/Blueprints/BP_Yumeno.hbblueprint.json'});
// Title has its own lightweight widget, independent of trial dialogue/glyph UI.
const titleSource=JSON.parse(await fs.readFile(path.join(root,'Assets/UI/Main.hbwidget.json'),'utf8'));
const titleIds=new Set(['root','Title']);let changed=true;while(changed){changed=false;for(const n of titleSource.nodes)if(titleIds.has(n.parent)&&!titleIds.has(n.id)&&n.parent!=='root'){titleIds.add(n.id);changed=true;}}
titleSource.nodes=titleSource.nodes.filter(n=>titleIds.has(n.id));titleSource.name='TitleShellV4';
for(const n of titleSource.nodes){if(n.id==='TitleLogo')n.slot.offset=[650,30,580,200];if(n.id==='TitleSub')n.properties.visible=false;}
await write('Assets/UI/TitleShellV4.hbwidget.json',titleSource);
await emitCenteredSourceCanvases({root,write});
// Publishing validates generated fonts and actor art even on the first build.
await publishV4Data({repo,copy,write});
const scrumTasks=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks;
await emitScrumClaims({tasks:Object.values(scrumTasks),source:root,write});
// 패키지 줄이기 : PNG → WebP, 글꼴 서브셋 (tools/optimize_assets.py)
execFileSync('python',['-X','utf8',path.join(repo,'tools/optimize_assets.py')],{stdio:'inherit'});
// Register raster fonts only after the optimizer has finished writing them.
await emitNativeHuds();
await emitNonstopSourceHud({repo,root,write});
const selectedCampaign=await fs.readFile(path.join(root,'Assets/Data/v4_story/revision/campaign.json'),'utf8')
 .then(JSON.parse,error=>{if(error.code==='ENOENT')return null;throw error;});
if(process.argv.includes('--revised-campaign')||selectedCampaign?.campaignRevision==='rewrite-v5'){
 console.log(JSON.stringify({revisedCampaign:await publishRevisedCampaign({repo,write,runtimeSource:root})}));
}
console.log(JSON.stringify({scenes:sceneFiles.length,rules:rules.length,widgets:w.nodes.length}));
