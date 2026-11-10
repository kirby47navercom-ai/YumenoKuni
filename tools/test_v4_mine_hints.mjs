import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {emitMineV4,mineHintSvg} from '../Game/tools/v4-mine-ui.mjs';
import {validWidgetAsset} from '../../engineCreate/prototype/ui-assets.js';
const native=JSON.parse(await fs.readFile(new URL('../data/v4_story/native_tasks.json',import.meta.url),'utf8'));
let regions=0,tasks=0;
for(const task of Object.values(native.tasks))if(task.stage?.kind==='mindmine'){
 ++tasks;assert(task.stage.regions.length<=10);
 for(const region of task.stage.regions){const svg=mineHintSvg(region.polygon);assert(svg.includes('preserveAspectRatio="none"')&&svg.includes('viewBox="0 0 740 420"')&&!svg.includes('<text')&&!svg.includes('NaN')&&!svg.includes('undefined'));++regions;}
}
for(const invalid of [[],[[0,0],[1,1]],[[0,0],[1,1],[2,0]],[[0,0],[.5,.5],[1,1]],[[0,0],[1,0],[NaN,1]]])assert.throws(()=>mineHintSvg(invalid));
const outputs=new Map();await emitMineV4({write:async(name,value)=>outputs.set(name,value)});
const widget=outputs.get('Assets/UI/MineV4.hbwidget.json'),hud=outputs.get('Assets/UI/MineHUDV4.hbwidget.json');
assert(validWidgetAsset(widget)&&validWidgetAsset(hud)&&widget.nodes.length<=256&&new Set(widget.nodes.map(n=>n.id)).size===widget.nodes.length);
assert.equal(widget.nodes.filter(n=>/^Cell\d+$/.test(n.id)).length,242);
assert.equal(widget.nodes.find(n=>n.id==='MineHintHit').properties.visible,false);
assert.equal(hud.nodes.find(n=>n.id==='MineQuestionText').properties.visible,false);
const hints=widget.nodes.filter(n=>/^MineHint\d+$/.test(n.name));assert(hints.length===10&&hints.every(n=>n.properties.visible===false&&n.properties.focusable===false&&n.slot.offset.join(',')==='270,180,740,420'));
console.log(JSON.stringify({status:'PASS',tasks,authoredPolygons:regions,nodes:widget.nodes.length,invalidPolygonsRejected:5,noAnswerText:true,playerLaunch:false}));
