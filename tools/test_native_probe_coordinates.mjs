import assert from 'node:assert/strict';
import {canvasClientPoint} from '../Game/tools/native-window-probe.mjs';
for(const size of [[1280,720],[1920,1080],[2560,1440],[3840,2160],[3440,1440],[1024,768],[1080,1920],[800,600]]){
 const scale=Math.min(size[0]/1280,size[1]/720);
 for(const point of [[0,0],[640,360],[1100,463.67],[1279,719]]){
  const actual=canvasClientPoint(point,size,[1280,720]);assert.deepEqual(actual,point.map(v=>Math.round(v*scale)));assert(Math.abs(actual[0]/scale-point[0])<=.5/scale+1e-9);assert(Math.abs(actual[1]/scale-point[1])<=.5/scale+1e-9);
 }
}
assert.deepEqual(canvasClientPoint([640,360],[3440,1440],[1280,720]),[1280,720]);
assert.throws(()=>canvasClientPoint([1,1],[0,720],[1280,720]));
assert.throws(()=>canvasClientPoint([NaN,1],[1280,720],[1280,720]));
console.log('QA fit-coordinate mapping: 32 points / 8 sizes including ultrawide, portrait and 4K PASS');
