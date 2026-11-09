// QA input inverse only: read state, then issue normal mouse input. Never changes gameplay.
export function trialAimInput(target,cursor){
 if(!Array.isArray(target)||target.length!==2||!target.every(Number.isFinite))throw Error('Invalid trial aim target');
 if(!cursor?.active)return [...target];
 for(const key of ['desired','actual','physical'])if(!Array.isArray(cursor[key])||cursor[key].length!==2||!cursor[key].every(Number.isFinite))throw Error('Incomplete trial cursor '+key);
 if(!Number.isFinite(cursor.gain)||cursor.gain<=0)throw Error('Invalid trial cursor gain');
 const desired=target.map((v,i)=>v-(cursor.actual[i]-cursor.desired[i]));
 return !cursor.initialized||cursor.gain===1?desired:desired.map((v,i)=>cursor.physical[i]+(v-cursor.desired[i])/cursor.gain);
}
export function trialAimPlan(target,cursor){
 const point=trialAimInput(target,cursor);if(point[0]>=0&&point[0]<=1280&&point[1]>=0&&point[1]<=720)return {kind:'mouse',point};
 if(!cursor?.active)throw Error('Trial aim target outside viewport');
 const delta=target.map((v,i)=>v-cursor.actual[i]),axis=Math.abs(delta[0])>=Math.abs(delta[1])?0:1;
 return {kind:'key',key:axis===0?(delta[0]<0?'ArrowLeft':'ArrowRight'):(delta[1]<0?'ArrowUp':'ArrowDown'),ms:Math.max(1,Math.min(100,Math.abs(delta[axis])/(400*cursor.gain)*1000))};
}
