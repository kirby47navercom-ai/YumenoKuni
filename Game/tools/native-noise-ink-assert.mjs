import assert from 'node:assert/strict';
export function assertNoiseInk(ui){
 const wanted=ui.trialSnapshot?.noiseGlyphInk;
 assert(Array.isArray(wanted),'Noise renderer proof requires the candidate ink snapshot');
 const actual=ui.world.filter(o=>/^TrialGpu_N[FB]\d+$/.test(o.id)&&o.visible!==false&&o.sprite?.visible&&o.sprite.color?.[3]>.01).map(o=>o.id.slice('TrialGpu_'.length));
 assert.deepEqual(actual.sort(),[...wanted].sort(),'Rendered pink letters must match this frame; no stale previous response');
 return {expected:wanted.length,rendered:actual.length};
}
