import assert from 'node:assert/strict';
import {Vector3} from '../../engineCreate/node_modules/three/build/three.module.js';
import {gameRenderViews} from '../../engineCreate/prototype/game-render-views.js';
const cache=new Map(),view={eye:[0,0,4],target:[0,0,0],fov:43,focus:[.3,.4],polygon:[[0,0],[1,0],[0,1]]};
for(const aspect of [4/3,16/9,21/9,32/9]){
 const camera=gameRenderViews([view],aspect,cache)[0].camera,p=new Vector3().project(camera);
 assert(Math.abs((p.x+1)/2-.3)<1e-6);assert(Math.abs((1-p.y)/2-.4)<1e-6);
 const before=camera.position.clone();gameRenderViews([view],aspect,cache,{remaining:.2,duration:.3,intensity:.05});assert(before.distanceTo(camera.position)>0,'Damage shakes the actual view camera');
}
assert.throws(()=>gameRenderViews([{...view,polygon:[[0,0],[1,0],[.2,.2],[1,1],[0,1]]}],1));
assert.throws(()=>gameRenderViews([{...view,target:view.eye}],1));
assert.throws(()=>gameRenderViews([view,view,view,view],1));
assert.throws(()=>gameRenderViews([{...view,eye:[NaN,0,0]}],1));
gameRenderViews(null,1,cache);assert.equal(cache.size,0);
console.log('Multiview projection at four aspect ratios, real camera shake, malformed input rejection, teardown PASS');
