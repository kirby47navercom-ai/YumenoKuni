import assert from 'node:assert/strict';
import {trialAimInput,trialAimPlan} from '../Game/tools/v4-aim-test-input.mjs';
let vectors=0;
for(const gain of [.8,1,1.2])for(const offset of [[-32,0],[32,0],[0,-32],[0,32],[-16,-8],[0,0]])for(const initialized of [false,true]){
 const cursor={active:true,initialized,gain,desired:[500,300],actual:[500+offset[0],300+offset[1]],physical:[640,360]},before=JSON.stringify(cursor),target=[700,420];
 const input=trialAimInput(target,cursor),desired=input.map((v,i)=>initialized&&gain!==1?cursor.desired[i]+(v-cursor.physical[i])*gain:v),actual=desired.map((v,i)=>v+offset[i]);
 assert(actual.every((v,i)=>Math.abs(v-target[i])<1e-6));assert.equal(JSON.stringify(cursor),before);vectors++;
}
assert.deepEqual(trialAimInput([0,0],null),[0,0]);assert.deepEqual(trialAimInput([2,3],{active:false}),[2,3]);
assert.throws(()=>trialAimInput([NaN,0],null));assert.throws(()=>trialAimInput([0,0],{active:true}));assert.throws(()=>trialAimInput([0,0],{active:true,desired:[0,0],actual:[0,0],physical:[0,0],gain:0}));
const edge={active:true,initialized:true,gain:.8,desired:[640,360],actual:[640,360],physical:[640,360]};assert.deepEqual(trialAimPlan([80,360],edge),{kind:'key',key:'ArrowLeft',ms:100});assert.equal(trialAimPlan([1200,360],edge).key,'ArrowRight');assert.equal(trialAimPlan([640,40],edge).key,'ArrowUp');assert.equal(trialAimPlan([640,700],edge).key,'ArrowDown');assert.deepEqual(trialAimPlan([600,360],edge),{kind:'mouse',point:[590,360]});
console.log(JSON.stringify({status:'PASS',vectors,scope:'Inverse of own desired/actual displacement and physical SHIFT gain; read-only pure QA helper. No player launch; moving-target, timing and compositor accuracy untested.'}));
