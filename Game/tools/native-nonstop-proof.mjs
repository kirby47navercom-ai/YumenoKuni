// Observe real input/runtime state; never changes a task, timer or outcome.
import assert from 'node:assert/strict';
import {assertNoiseInk} from './native-noise-ink-assert.mjs';
export function nonstopProof(taskId,task,direction,validateInk=null){
 const expected=task.debate.lines.length+(direction.extra[taskId]||[]).length;
 const quiet=['T1-NS-A01','T1-NS-A02','T1-NS-A03'].includes(taskId);
 const proof={expected,quiet,utterances:{},turnSamples:0,loop:null,wrong:null,result:null};
 let pending=null,lastSignature='';
 return {proof,
  async observe(s,probe){
   const tr=s.trial;
   const signature=JSON.stringify([s.taskQueue,s.queueAfter,tr?.index,!!s.taskInputArmed]);
   if(signature!==lastSignature){lastSignature=signature;if(s.taskQueue&&s.queueAfter!=='start')console.log(JSON.stringify({proofTask:taskId,queue:s.queueAfter,index:tr?.index}));}
   if(s.taskQueue&&['nonstop-loop','nonstop-wrong'].includes(s.queueAfter)&&!pending){
    pending={phase:s.queueAfter,hp:s.trialHp,timer:s.presentation.timer,bullet:tr?.bullet};
    proof[pending.phase==='nonstop-loop'?'loop':'wrong']={...pending};
   }
   if(pending&&!s.taskQueue&&s.taskInputArmed&&tr&&!s.presentation?.nonstopIntro){
    assert.equal(tr.index,0,'Reaction must restart at the first utterance');
    assert.equal(s.trialHp,pending.hp,'Restart must preserve HP');
    assert(s.presentation.timer<=pending.timer+.1&&s.presentation.timer>=pending.timer-2,'Restart must preserve remaining time');
    assert.equal(tr.bullet,pending.bullet,'Restart must preserve evidence selection');
    proof[pending.phase==='nonstop-loop'?'loop':'wrong'].restarted=true;pending=null;
   }
   if(tr?.resultTime>0&&!proof.result){proof.result={kind:tr.result};await new Promise(resolve=>setTimeout(resolve,1800));await probe.capture(taskId.toLowerCase()+'-result');}
   if(!tr||s.taskQueue||!s.taskInputArmed||s.presentation?.nonstopIntro||tr.clearing)return;
   if(taskId.startsWith('T1-'))assert.notEqual(tr.kind,'agree','Chapter 1 agreement is prohibited');
   if(quiet)assert(!(tr.noiseRows||[]).length,'Noise before its introduction');
   if(tr.turning){proof.turnSamples++;return;}
   const pink=(s.gpuNoiseHud?.modelPoints||[]).some(p=>p[4]>.9);
   if(s.presentation.statementTime>=1.3&&tr.glyphsFront>0){
    const entry=proof.utterances[tr.index]??={kind:tr.kind,seat:tr.speakerSeat,pink:false,camera:s.presentation.camera};
    entry.pink ||=pink;
    if(!entry.capture&&(quiet||pink)){
     entry.capture=taskId.toLowerCase()+'-line-'+tr.index;
     await probe.capture(entry.capture);
     if(validateInk)entry.ink=assertNoiseInk(await validateInk(entry.capture));
    }
   }
  },
  get observing(){return !proof.loop?.restarted;},
  get wrongNeeded(){return !proof.wrong?.restarted;},
  finish(){
   assert.equal(Object.keys(proof.utterances).length,expected,'Every utterance must actually render');
   assert(Object.values(proof.utterances).every(r=>r.capture&&(quiet||r.pink)),'Every introduced utterance must visibly carry its noise');
   assert(proof.loop?.restarted,'Authored monologue and loop restart required');
   assert(proof.wrong?.restarted,'Wrong response and restart required');
   assert(proof.wrong.hp<proof.loop.hp,'Wrong hit must actually reduce HP');
   assert(proof.turnSamples>0,'Actual camera turns must be observed');
   assert(proof.result,'Actual result cutin required');
   return proof;
  }
 };
}
