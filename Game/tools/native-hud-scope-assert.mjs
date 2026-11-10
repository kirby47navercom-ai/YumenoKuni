import assert from'node:assert/strict';
export function assertHudScope(ui,scope){
 const world=ui.world,has=p=>world.some(o=>p.test(o.id));if(ui.scene==='Assets/Scenes/Title.hbscene.json'){assert(!has(/^TrialGpu_|^TrialBatch_|^Podium\d+$/),'Title must not retain court graphics');return;}
 assert.equal(ui.gpuSnapshot?.scope,scope,'The actual renderer must bind only the current mode');assert.equal(world.filter(o=>/^Podium\d+$/.test(o.id)).length,16,'Scoped scenes must preserve all independently moving podiums');
 if(process.argv.includes('--single-seat-faces')){
  const cam=world.find(o=>o.id==='Camera');
  for(let i=0;i<16;i++){const front=world.find(o=>o.id==='Seat'+i),back=world.find(o=>o.id==='SeatRear'+i);assert(front?.sprite&&back?.sprite,'Both original face resources must remain owned');const a=front.rotation[1]*Math.PI/180,rear=/court_figures\/|memorials\//.test(front.sprite.texture)&&((cam.position[0]-front.position[0])*Math.sin(a)+(cam.position[2]-front.position[2])*Math.cos(a)<0);assert.equal(front.sprite.enabled,!rear,'Front face must follow the actual camera side');assert.equal(back.sprite.enabled,rear,'Rear face must follow the actual camera side');}
 }
 if(scope!=='debate')assert(!has(/^TrialGpu_M[FSB]\d+$|^TrialBatch_(?:MF|MS|MB)|^TrialGlyphMotion$|^TrialSpeakerDepth$/),'Other modes must not create nonstop glyphs or rigs');
 if(!['debate','panic'].includes(scope))assert(!has(/^TrialGpu_N[FB]\d+$/),'Only debate and panic own interrupting noise glyphs');
 if(scope!=='panic')assert(!has(/^TrialGpu_Panic|^TrialBatch_Panic/),'Other modes must not create panic graphics');
 if(!['debate','panic'].includes(scope))assert(!has(/^TrialGpu_(?:Aim|Whip|TimerPanel|Timer\d+)$/),'Other modes must not create the debate HUD');
 if(!['basic','showdown'].includes(scope))assert(!has(/^TrialGpu_StageClockDigit/),'Modes with their own clock must not create an unused stage clock');
}
