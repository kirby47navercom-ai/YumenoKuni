import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {validScene} from '../../engineCreate/prototype/model.js';
import {validAsset} from '../../engineCreate/prototype/asset-documents.js';
const root=path.resolve(import.meta.dirname,'../Game');
const read=async file=>JSON.parse(await fs.readFile(path.join(root,file),'utf8'));
const title=await read('Assets/Scenes/Title.hbscene.json'),court=await read('Assets/Scenes/Court.hbscene.json'),explore=await read('Assets/Scenes/Explore.hbscene.json');
for(const s of [title,court,explore])assert(validScene(s),s.sceneName);
assert(title.objects.some(o=>o.id==='TitleScene'));assert(!title.objects.some(o=>o.id==='Driver'||o.components?.some(c=>['MeshRenderer','SpriteRenderer'].includes(c.type))));
for(const [s,yes,no] of [[court,'CourtGeometry','ExploreGeometry'],[explore,'ExploreGeometry','CourtGeometry']]){assert(s.objects.some(o=>o.id===yes));assert(!s.objects.some(o=>o.id===no));assert(!s.objects.some(o=>o.blueprintAsset));const ids=new Set(s.objects.map(o=>o.id));for(const o of s.objects)if(o.parent)assert(ids.has(o.parent));}
for(const f of ['TitleShellV4','LoadingV4'])assert(validAsset('widget',await read('Assets/UI/'+f+'.hbwidget.json')),f);
const shell=await read('Assets/UI/TitleShellV4.hbwidget.json');assert(shell.nodes.length<10);assert(!shell.nodes.some(n=>n.id==='Trial'));

for(const s of [court,explore]){const p=s.objects.find(o=>o.id==='SceneAntialias')?.components.find(c=>c.type==='PostProcessVolume')?.properties;assert(p&&p.antiAliasing==='fxaa'&&!p.bloomEnabled&&!p.grainEnabled&&!p.chromaticAberrationEnabled);}
const project=await read('YumenoKuni.hbproject');assert.equal(project.startupScene,'Assets/Scenes/Title.hbscene.json');assert.equal(project.gameInstance,'Assets/Blueprints/BP_Yumeno.hbblueprint.json');
console.log(JSON.stringify({ok:true,titleObjects:title.objects.length,courtObjects:court.objects.length,exploreObjects:explore.objects.length,titleNodes:shell.nodes.length}));
