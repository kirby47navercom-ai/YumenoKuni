import fs from'node:fs/promises';import assert from'node:assert/strict';
// Read-only proof from an actual held/flight state, never a transformed-state fixture.
export async function proveLieHud(probe,taskId,label,phase){
 await probe.sampled(2);const name=taskId.toLowerCase()+'-lie-hud-'+phase,file=await probe.capture(name),frame=JSON.parse(await fs.readFile(file.replace(/\.png$/,'.ui.json'),'utf8')),hud=frame.widgets.find(w=>w.instance==='nonstophud'),node=id=>hud?.nodes.find(n=>n.id===id);
 assert(node('root')?.properties.visible,'Active Nonstop HUD required');assert.equal(node('Bullet').properties.text,label,'Transformed name must remain on the cartridge');
 assert(node('BulletPlate').properties.texture.endsWith('ammoPlateLieLeft.png'));assert(node('Status').properties.texture.endsWith('statusLie.png'));assert(node('Clock').properties.texture.endsWith('clockLie.png'));
 const digits=Array.from({length:9},(_,i)=>node('Clock'+i));assert(digits.every(n=>n.properties.visible&&/digitLie\d+\.png$/.test(n.properties.texture)),'All nine ungraded source lie digits must render');
 assert(!frame.world.some(o=>/^TrialGpu_Timer\d+$/.test(o.id)&&o.sprite?.visible),'The world-graded clock must stay hidden');
 if(phase==='flight'){const word=frame.world.filter(o=>o.id?.startsWith('KotodamaWord')&&o.meshVisible);assert(word.length>1,'Actual solid name flight required');}
 return {phase,label,file,clock:digits.map(n=>n.properties.texture.match(/digitLie(\d+)\.png$/)[1]).join(','),worldClockHidden:true};
}
