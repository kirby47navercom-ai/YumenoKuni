// Engine sources are read-only. Test the exact candidate in an owned module copy.
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {openNativePackage,installNativeAssets} from '../../../engineCreate/tools/native-game-platform.mjs';
import {loadHeadlessModel,disposeHeadlessModel} from '../../../engineCreate/tools/headless-model.mjs';
const root=path.resolve(import.meta.dirname,'..'),engine=path.resolve(root,'../../engineCreate');
const built=JSON.parse(await fs.readFile(path.join(root,'build-result.json'),'utf8'));
const work=path.join(root,'Saved/native-model-compat-'+Date.now());await fs.mkdir(work,{recursive:true});
const sourceFile=path.join(engine,'tools/headless-model.mjs'),source=await fs.readFile(sourceFile,'utf8'),hash=s=>createHash('sha256').update(s).digest('hex');
const before="const loader=new GLTFLoader(manager);loader.register(parser=>({name:'HB_HEADLESS_POSE',";
const after="const loader=new GLTFLoader(manager);\n  // Native texture decoding must also own the WebP extension path.\n  if(loadTexture)loader.register(parser=>({name:'EXT_texture_webp',loadTexture:index=>parser.json.textures?.[index]?.extensions?.EXT_texture_webp?parser.plugins.HB_HEADLESS_POSE.loadTexture(index):null}));\n  loader.register(parser=>({name:'HB_HEADLESS_POSE',";
assert(source.includes(before));const imageBefore='image=json.images?.[definition?.source]',imageAfter='image=json.images?.[definition?.extensions?.EXT_texture_webp?.source??definition?.source]';assert(source.includes(imageBefore));
const candidate=source.replace(before,after).replace(imageBefore,imageAfter);await fs.writeFile(path.join(work,'headless-model.candidate.txt'),candidate);
let owned=candidate.replaceAll("from '../prototype/",`from '${pathToFileURL(path.join(engine,'prototype')).href}/`);
owned=owned.replace("from 'three';",`from '${pathToFileURL(path.join(engine,'node_modules/three/build/three.module.js')).href}';`).replace("from 'three/addons/loaders/GLTFLoader.js';",`from '${pathToFileURL(path.join(engine,'node_modules/three/examples/jsm/loaders/GLTFLoader.js')).href}';`);
const moduleFile=path.join(work,'headless-model.owned-probe.mjs');await fs.writeFile(moduleFile,owned);const patched=await import(pathToFileURL(moduleFile));
const pack=await openNativePackage(built.output),assets=installNativeAssets(pack);
const scene=JSON.parse(await fs.readFile(await pack.resolve(pack.manifest.startupScene),'utf8'));let model;
for(const o of scene.objects){for(const c of o.components||[])if(c.type==='MeshRenderer'&&c.properties.mesh?.endsWith('.glb')){const name=c.properties.mesh,bytes=await fs.readFile(await pack.resolve(name)),j=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString('utf8'));if(j.textures?.some(t=>t.extensions?.EXT_texture_webp)){model=name;break;}}if(model)break;}
assert(model,'actual initial scene must contain the failing WebP extension model');let baseline,loaded;
try{
 try{loaded=await loadHeadlessModel(pack.project,model,{geometry:true,loadTexture:assets.texture});baseline={unexpectedPass:true};}catch(error){baseline={error:error.message,stack:error.stack};}finally{if(loaded)disposeHeadlessModel(loaded.object);loaded=null;}
 assert.match(baseline.error||'',/self is not defined/);
 loaded=await patched.loadHeadlessModel(pack.project,model,{geometry:true,loadTexture:assets.texture});let meshes=0,mapped=0,pixels=0;loaded.object.traverse(o=>{if(o.isMesh){meshes++;for(const m of Array.isArray(o.material)?o.material:[o.material])if(m.map?.image?.data){mapped++;pixels+=m.map.image.width*m.map.image.height;}}});assert(meshes>0&&mapped>0&&pixels>0);
 assert.equal(hash(await fs.readFile(sourceFile)),hash(source));
 const result={ok:true,work,build:built.id,model,baseline,patched:{meshes,mapped,pixels},engineSource:sourceFile,engineSourceSHA256:hash(source),candidateSHA256:hash(candidate),candidate:path.join(work,'headless-model.candidate.txt'),engineOriginalUnchanged:true,scope:'Original loader vs owned candidate on the same actual packaged embedded-WebP GLB; no model/texture removals, browser fallback or engine original edits. Full native package still requires the engine fix.'};await fs.writeFile(path.join(work,'report.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({ok:true,work,baseline:baseline.error,meshes,mapped,pixels}));
}finally{if(loaded)patched.disposeHeadlessModel(loaded.object);assets.restore();pack.host.close();}
