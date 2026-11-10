// Source bank integrity and entry visibility. Actual input/visual QA stays native.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';import {fileURLToPath} from 'node:url';
import {validWidgetAsset} from '../../engineCreate/prototype/ui-assets.js';import {validGameJson} from '../../engineCreate/prototype/game-json.js';
import {emitV4ComicUI} from '../Game/tools/v4-comic-ui.mjs';
const repo=path.dirname(path.dirname(fileURLToPath(import.meta.url))),outputs=new Map();
const report=await emitV4ComicUI({body:'Assets/Fonts/pretendard/Pretendard-Medium.otf',head:'Assets/Fonts/blackhansans/BlackHanSans-Regular.ttf',write:async(p,v)=>outputs.set(p,v)}),widget=outputs.get(report.widget),bank=outputs.get('Assets/Data/climax_ui_v3.json');
assert(validWidgetAsset(widget));assert(widget.nodes.length<=256);assert(validGameJson(bank));
for(const n of widget.nodes)if(n.id!=='root'){assert.equal(n.properties.visible,false,n.id+' visible before entry');assert.equal(n.properties.focusable,false);if(/^(SlotI|CandidateI|StockI)\d+$/.test(n.id)||n.id==='CompletePage')assert.equal(n.properties.texture,'','future answer art must be bound only by task state');}
const from='ui/v4/climax_original_20261106/',to='Assets/Art/ui/climax_v3/';let copies=0;
for(const [name,bytes]of outputs)if(name.startsWith(to)&&name!==to+'own_halftone.svg'){assert((await fs.readFile(path.join(repo,from+name.slice(to.length)))).equals(bytes),name);copies++;}
for(const id of ['V3PageBar','V3PageWord','V3StockBase','V3SelectedFrame','V3Cursor','V3PlaceOK','V3PlaceNG','V3Unlock','ReplayCaption','ZoomImage','HoleHintPlate'])assert(widget.nodes.some(n=>n.id===id),id);
assert.equal(bank.timerDigits.length,10);assert.equal(bank.timerSlots.length,7);assert.equal(bank.stockSlots.length,14);assert.equal(bank.sequences.unlock.durationFrames,64);assert.equal(bank.sequences.unlock.frames.at(-1).tile,null);
assert.equal(outputs.get('Assets/Audio/S_v3se_464.hbaudioasset.json').clip,'Assets/Audio/v3se_464.ogg');
console.log(JSON.stringify({ok:true,nodes:widget.nodes.length,sourceCopies:copies,originalMangaIncluded:report.originalMangaIncluded,scope:'Source pixels, native JSON limits, entry visibility, runtime roles and source unlock sequence; geometry and gameplay use separate native tests'}));
