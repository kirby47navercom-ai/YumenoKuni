import assert from 'node:assert/strict';
import {validWidgetAsset} from '../../engineCreate/prototype/ui-assets.js';
import {emitV4ScrumUI} from '../Game/tools/v4-scrum-ui.mjs';
const output=new Map(),widget=await emitV4ScrumUI({body:'Assets/Fonts/pretendard/Pretendard-Medium.otf',head:'Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf',write:async(p,v)=>output.set(p,v)});
assert(validWidgetAsset(widget));assert(widget.nodes.length<256);
for(const node of widget.nodes.filter(n=>n.id!=='root')){assert.equal(node.properties.visible,false);assert.equal(node.properties.focusable,false);}
for(const side of ['L','R'])for(let i=0;i<10;i++)for(const p of ['P','F','T'])assert(widget.nodes.some(n=>n.id===`ScV${side}${p}${i}`));
const key=widget.nodes.find(n=>n.id==='ScVKey'),push=widget.nodes.find(n=>n.id==='ScVPush');assert(key&&push);assert.equal(key.slot.offset[0]+key.slot.offset[2]/2,push.slot.offset[0]+push.slot.offset[2]/2);assert(key.slot.offset[1]>=push.slot.offset[1]&&key.slot.offset[1]+key.slot.offset[3]<=push.slot.offset[1]+push.slot.offset[3]);
assert(!widget.nodes.some(n=>n.type==='Button'||n.id.startsWith('Opt')));
console.log(JSON.stringify({ok:true,nodes:widget.nodes.length,scope:'Official widget validity and two team ribbon queues; native input and visual review separate'}));
