import fs from'node:fs/promises';import path from'node:path';import assert from'node:assert/strict';
export async function proveAgreementCast(probe,taskId,expected){
 const game=path.resolve(import.meta.dirname,'..'),assets=JSON.parse(await fs.readFile(path.join(game,'Saved/nonstop-guidance-20261106/agreement-cast/generated-assets.json'),'utf8')),anchors=JSON.parse(await fs.readFile(path.join(game,'../ui/v4/debate_feedback/agreement/manifest.json'),'utf8'));
 const file=await probe.capture(taskId.toLowerCase()+'-agreement-pair'),frame=JSON.parse(await fs.readFile(file.replace('.png','.ui.json'),'utf8')),widget=frame.widgets.find(w=>w.instance==='endingsourcev4');assert(widget,'Actual original agreement timeline must be mounted');
 const visible=widget.nodes.filter(n=>n.properties.visible&&n.properties.opacity>.8),by=texture=>visible.find(n=>n.properties.texture===texture),hero=by(assets.heroNormal),partner=by(assets.files[expected][0]);
 assert(hero&&partner,'Both actual own-character agreement images must render');assert(by(assets.heroShadow)&&by(assets.files[expected][1]),'Original pink silhouettes need dedicated matching alpha, not duplicated colored faces');
 const measured=(node,target)=>{assert.deepEqual(node.properties.scale,[1,1]);assert.equal(node.properties.rotation,0);const[x,y,w,h]=node.slot.offset;return {height:h*target.head/1024,eyeY:y+360+h*target.eye/1024,rect:[x,y,w,h]};};
 const h=measured(hero,anchors.hero),p=measured(partner,anchors.partner);assert(Math.abs(h.height-p.height)<.1,'Two screen head sizes must match');assert(Math.abs(h.eyeY-p.eyeY)<.1,'Two screen eye levels must match');
 const legacy=frame.widgets.find(w=>w.instance==='debatefx');for(const id of ['ResultHero','ResultPartner'])assert(!legacy?.nodes.find(n=>n.id===id)?.properties.visible,'No old generic pose underneath source cutin');
 for(const node of [hero,partner])assert.deepEqual(node.slot.anchors,[.5,.5,.5,.5]);
 const wide=visible.filter(n=>/^EndingWide\d+$/.test(n.id));assert(wide.length>=2,'Source background strips fill the viewport');for(const node of wide)assert.deepEqual(node.slot.anchors,[0,.5,1,.5]);
 return {taskId,partner:expected,viewport:[frame.width,frame.height],centeredSourceCanvas:true,wideBackgroundStrips:wide.length,hero:h,ally:p,headDifference:Math.abs(h.height-p.height),eyeDifference:Math.abs(h.eyeY-p.eyeY),normalTextures:[hero.properties.texture,partner.properties.texture],matchingPinkSilhouettes:true,legacyHidden:true,file};
}
