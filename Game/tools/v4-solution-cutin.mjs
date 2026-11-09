// Legacy static fallback only; current success uses authored SFL source layers.
// Fullscreen coverage was user-rejected on 2026-11-06. Do not restore this as the live result.
import fs from 'node:fs/promises';import path from 'node:path';
const repo=path.resolve(import.meta.dirname,'../..');
export async function solutionCutin(){
 const uri=async file=>'data:image/png;base64,'+(await fs.readFile(path.join(repo,file))).toString('base64');
 const base='ui/v3_authorized/armament/t_kai_cutin_boushi_JP/';
 const bg=await uri(base+'t_kai_bg.png.png'),word=await uri(base+'t_kai_tx_JP.png.png'),hero=await uri('ui/v4/debate_feedback/hero_lie_deduction.png');
 const svg=(w,h,body)=>`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${body}</svg>`;
 const background=`<image href="${bg}" x="0" y="0" width="1280" height="720" preserveAspectRatio="none"/>`;
 const tint='<defs><filter id="solutionBlue" color-interpolation-filters="sRGB"><feColorMatrix values=".12 .24 .04 0 .08 .18 .36 .06 0 .18 .20 .40 .07 0 .28 0 0 0 1 0"/></filter></defs>';
 const face=`${tint}<image filter="url(#solutionBlue)" href="${hero}" x="-325" y="-274" width="1560" height="1875"/>`;
 const lettering=`<image href="${word}" width="1024" height="1024"/>`;
 const combined=`${background}${tint}<defs><clipPath id="solutionFace"><rect x="440" y="0" width="840" height="720"/></clipPath></defs><g clip-path="url(#solutionFace)" filter="url(#solutionBlue)"><image href="${hero}" x="115" y="-274" width="1560" height="1875"/></g><image href="${word}" x="20" y="30" width="660" height="660"/>`;
 return{background:svg(1280,720,background),word:svg(1024,1024,lettering),face:svg(840,720,face),combined:svg(1280,720,combined)};
}
