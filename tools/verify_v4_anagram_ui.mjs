import assert from 'node:assert/strict';
import {validWidgetAsset} from '../../engineCreate/prototype/ui-assets.js';
import {emitV4AnagramUI} from '../Game/tools/v4-anagram-ui.mjs';
const output=new Map(),widget=await emitV4AnagramUI({body:'Assets/Fonts/pretendard/Pretendard-Medium.otf',head:'Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf',write:async(p,v)=>output.set(p,v)});
assert(validWidgetAsset(widget));assert(widget.nodes.length<256);
for(const node of widget.nodes.filter(n=>n.id!=='root'))assert.equal(node.properties.visible,false);
for(let i=0;i<20;i++){assert(widget.nodes.some(n=>n.id==='AnaBall'+i));assert(widget.nodes.some(n=>n.id==='Orb'+i));assert.equal(widget.nodes.find(n=>n.id==='AnaSlot'+i).slot.offset[1],24);}
const question=widget.nodes.find(n=>n.id==='AnaQuestion');assert.deepEqual(question.slot.offset,[680.6667,552,533.3333,38.6667]);assert(!widget.nodes.some(n=>n.id==='AnaQuestionShade'));
assert(widget.nodes.find(n=>n.id==='AnaTime').slot.offset[0]<300);assert(widget.nodes.some(n=>n.id==='AnaHeart11'));assert(widget.nodes.some(n=>n.id==='AnaStar9'));
console.log(JSON.stringify({ok:true,nodes:widget.nodes.length,scope:'Widget validity, upper-left answer, independent sphere/glyph layers, lower-left time and source question anchor; native toggle/input separate'}));
