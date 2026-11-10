// Override only the two actual StartBand paths; all mode-specific intros stay owned.
import fs from'node:fs/promises';import path from'node:path';import{createWidgetAsset,createWidgetNode,validWidgetAsset}from'../engineCreate/prototype/ui-assets.js';
export async function emitV4PhaseStartSource({repo,write}){
 const dir=path.join(repo,'ui/v4/phase_start_source'),manifest=JSON.parse(await fs.readFile(path.join(dir,'manifest.json'),'utf8'));
 const wrap=async(file,rect)=>{const b=await fs.readFile(file);return`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"><image x="${rect[0]}" y="${rect[1]}" width="${rect[2]}" height="${rect[3]}" href="data:image/png;base64,${b.toString('base64')}"/></svg>`;};
 await write('Assets/Art/ui/start_panic.webp',await fs.readFile(path.join(dir,'panic_start.webp')));
 await write('Assets/Art/ui/start_panic.svg',await wrap(path.join(dir,'panic_settled.png'),[0,0,1280,720]));
 // beginDebateIntro synchronously hides this legacy fallback before painting.
 // It still must never be an invented English strip if another old path exposes it.
 const intro=JSON.parse(await fs.readFile(path.join(repo,'ui/v4/intro_explore_source/manifest.json'),'utf8')).records.nonstop_title;
 await write('Assets/Art/ui/start_nonstop.svg',await wrap(path.join(repo,intro.file),intro.rect));
 const audit={...manifest,runtimeHook:{widget:'Main_UI/Trial/StartBand',rect:[0,0,1280,720],panicTexture:'Assets/Art/ui/start_panic.webp',nonstopFallback:'Assets/Art/ui/start_nonstop.svg',preserveCPPSeconds:1.6},liveAudit:{genericCreated:['start_nonstop.svg','start_panic.svg'],panic:'Yumeno.cpp hides legacy GPU StartBand; after warm-up the first active update creates the animated native phase owner for the existing1.6s interval. Remove on expiry or trial-hide.',nonstop:'Same entry selects then immediately beginDebateIntro→debateHud(false)/Trial(false), using existing original Intro; fallback replaced without replacing Intro.',otherPhases:'Anagram/Mine/Armament/Showdown/Scrum use their own intro owners and none references generic start_* paths. Unchanged; their full source fidelity is outside this focused live-path audit.'}};
 const w=createWidgetAsset('PanicPhaseStartV4');w.scaleMode='scale';w.scaleRule='fit';const n=createWidgetNode('Image','PanicSourcePhase','root');n.name=n.id;n.slot.anchors=[.5,.5,.5,.5];n.slot.offset=[-640,-360,1280,720];Object.assign(n.properties,{texture:'Assets/Art/ui/start_panic.webp',imageFit:'fill',color:'#ffffff',background:'#00000000',padding:0,radius:0,borderWidth:0,focusable:false});w.nodes.push(n);if(!validWidgetAsset(w))throw Error('Invalid Panic source phase widget');await write('Assets/UI/PanicPhaseStartV4.hbwidget.json',w);audit.runtimeHook.widget='Assets/UI/PanicPhaseStartV4.hbwidget.json';return audit;
}
