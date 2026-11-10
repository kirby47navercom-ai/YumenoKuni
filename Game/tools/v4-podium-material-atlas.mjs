// Consolidate materials inside ONE podium asset. All sixteen independently
// moving podium actors, their geometry and their transforms stay separate.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const require=createRequire(path.resolve(import.meta.dirname,'../engineCreate/package.json'));
const {Matrix4,Quaternion,Vector3}=require('three'),{createCanvas,loadImage}=require('@napi-rs/canvas');
const srgb=v=>v<=.0031308?v*12.92:1.055*Math.pow(v,1/2.4)-.055;
const linear=v=>v<=.04045?v/12.92:Math.pow((v+.055)/1.055,2.4);
async function emitMaterialAtlas({repo,write,sourceName,outputName,label}){
 const input=await fs.readFile(path.join(repo,'art/space_v4/court_intro_v1',sourceName+'.glb'));
 assert.equal(input.readUInt32LE(0),0x46546c67);const length=input.readUInt32LE(12),source=JSON.parse(input.subarray(20,20+length)),binary=input.subarray(28+length);
 assert(!source.skins&&!source.animations&&!source.textures,'Only current own untextured, unskinned models are eligible');
 assert(source.materials.every(m=>m.doubleSided===true&&(!m.alphaMode||m.alphaMode==='OPAQUE')&&!m.extensions));
 const components={SCALAR:1,VEC2:2,VEC3:3},widths={5123:2,5125:4,5126:4},reads={5123:'readUInt16LE',5125:'readUInt32LE',5126:'readFloatLE'};
 const read=id=>{const a=source.accessors[id],v=source.bufferViews[a.bufferView],n=components[a.type],size=widths[a.componentType];assert(n&&size&&!a.sparse&&!a.normalized);return Array.from({length:a.count},(_,i)=>Array.from({length:n},(_,k)=>binary[reads[a.componentType]]((v.byteOffset||0)+(a.byteOffset||0)+i*(v.byteStride||size*n)+k*size)));};
 const positions=[],normals=[],uv=[],indices=[];let triangles=0;
 const surfaceRoot=path.join(repo,'art/space_v4/materials_v2'),hasSurfaces=await fs.access(path.join(surfaceRoot,'bake-manifest.json')).then(()=>true,()=>false),tile=512,gutter=64;
 const visit=(id,parent)=>{const n=source.nodes[id],local=n.matrix?new Matrix4().fromArray(n.matrix):new Matrix4().compose(new Vector3(...(n.translation||[0,0,0])),new Quaternion(...(n.rotation||[0,0,0,1])),new Vector3(...(n.scale||[1,1,1]))),world=parent.clone().multiply(local),normal=world.clone().invert().transpose();
  assert(world.determinant()>0,'Reflected models need index winding conversion');if(n.mesh!==undefined)for(const p of source.meshes[n.mesh].primitives){assert((p.mode??4)===4);assert(Object.keys(p.attributes).every(k=>['POSITION','NORMAL','TEXCOORD_0'].includes(k)));const pos=read(p.attributes.POSITION),nor=read(p.attributes.NORMAL),idx=read(p.indices).flat(),base=positions.length/3;
   const worldPos=pos.map(v=>new Vector3(...v).applyMatrix4(world)),bounds=[0,1,2].map(k=>[Math.min(...worldPos.map(v=>v.getComponent(k))),Math.max(...worldPos.map(v=>v.getComponent(k)))]);
   pos.forEach((v,i)=>{const point=worldPos[i],nrm=new Vector3(...nor[i]).transformDirection(normal);positions.push(...point.toArray());normals.push(...nrm.toArray());
    if(hasSurfaces){const axis=[Math.abs(nrm.x),Math.abs(nrm.y),Math.abs(nrm.z)].indexOf(Math.max(Math.abs(nrm.x),Math.abs(nrm.y),Math.abs(nrm.z))),axes=axis===1?[0,2]:axis===0?[2,1]:[0,1],coords=axes.map(k=>(point.getComponent(k)-bounds[k][0])/Math.max(.001,bounds[k][1]-bounds[k][0])),inner=1-2*gutter/tile;uv.push((p.material+gutter/tile+coords[0]*inner)/source.materials.length,gutter/tile+coords[1]*inner);}else uv.push((p.material+.5)/source.materials.length,.5);
   });indices.push(...idx.map(i=>i+base));triangles+=idx.length/3;
  }for(const child of n.children||[])visit(child,world);
 };for(const n of source.scenes[source.scene||0].nodes)visit(n,new Matrix4());
 const doc={asset:{version:'2.0',generator:'YumenoKuni single model material bake'},scene:0,scenes:[{nodes:[0]}],nodes:[{name:label,mesh:0}],meshes:[{primitives:[]}],materials:[{name:'material_palette',doubleSided:true,pbrMetallicRoughness:{baseColorFactor:[1,1,1,1],metallicFactor:1,roughnessFactor:1,baseColorTexture:{index:0},metallicRoughnessTexture:{index:1}},emissiveFactor:[1,1,1],emissiveTexture:{index:2}}],textures:[0,1,2].map(source=>({source,sampler:0})),samplers:[{magFilter:9728,minFilter:9728,wrapS:33071,wrapT:33071}],images:[],bufferViews:[],accessors:[],buffers:[{byteLength:0}]},chunks=[];let offset=0,maxPaletteError=0;
 const append=(data,target)=>{const view=doc.bufferViews.length;doc.bufferViews.push({buffer:0,byteOffset:offset,byteLength:data.length,...target?{target}:{}});const pad=Buffer.alloc((4-data.length%4)%4);chunks.push(data,pad);offset+=data.length+pad.length;return view;};
 const accessor=(values,type,index=false)=>{const array=index?Uint32Array.from(values):Float32Array.from(values),a={bufferView:append(Buffer.from(array.buffer),index?34963:34962),componentType:index?5125:5126,count:values.length/components[type],type};if(type==='VEC3'){a.min=Array.from({length:3},(_,k)=>array.reduce((v,x,i)=>i%3===k?Math.min(v,x):v,Infinity));a.max=Array.from({length:3},(_,k)=>array.reduce((v,x,i)=>i%3===k?Math.max(v,x):v,-Infinity));}doc.accessors.push(a);return doc.accessors.length-1;};
 doc.meshes[0].primitives.push({attributes:{POSITION:accessor(positions,'VEC3'),NORMAL:accessor(normals,'VEC3'),TEXCOORD_0:accessor(uv,'VEC2')},indices:accessor(indices,'SCALAR',true),material:0});
 for(const channel of ['base','metalRough','emission']){const canvas=createCanvas(source.materials.length,1),ctx=canvas.getContext('2d'),image=ctx.createImageData(canvas.width,1);source.materials.forEach((m,i)=>{const p=m.pbrMetallicRoughness||{},values=channel==='base'?(p.baseColorFactor||[1,1,1,1]):channel==='emission'?[...(m.emissiveFactor||[0,0,0]),1]:[1,p.roughnessFactor??1,p.metallicFactor??1,1];values.forEach((v,k)=>{assert(Number.isFinite(v)&&v>=0&&v<=1);const encoded=Math.round(255*(channel!=='metalRough'&&k<3?srgb(v):v));image.data[i*4+k]=encoded;const decoded=channel!=='metalRough'&&k<3?linear(encoded/255):encoded/255;maxPaletteError=Math.max(maxPaletteError,Math.abs(decoded-v));});});ctx.putImageData(image,0,0);doc.images.push({bufferView:append(canvas.toBuffer('image/png')),mimeType:'image/png'});}
 if(hasSurfaces){
  // Bake generated surfaces into the existing ONE material atlas. This is asset
  // packing; never restore the former many-material draw calls or merge actors.
  const loaded={};for(const family of ['metal'])for(const kind of ['color','normal']){const file=path.join(surfaceRoot,kind==='color'?'masters':'maps',family+(kind==='color'?'':'_normal')+'.png'),c=createCanvas(tile,tile),cx=c.getContext('2d');cx.drawImage(await loadImage(file),0,0,tile,tile);loaded[family+'_'+kind]=cx.getImageData(0,0,tile,tile).data;}
  const atlas=[];
  for(const channel of ['base','metalRough','emission','normal']){const c=createCanvas(tile*source.materials.length,tile),cx=c.getContext('2d'),out=cx.createImageData(c.width,c.height);
   source.materials.forEach((m,mi)=>{const p=m.pbrMetallicRoughness||{},base=p.baseColorFactor||[1,1,1,1],em=m.emissiveFactor||[0,0,0],optical=Math.max(...em)>.01,family='metal',tex=loaded[family+'_color'],normal=loaded[family+'_normal'];
    for(let y=0;y<tile;y++)for(let x=0;x<tile;x++){const sx=Math.max(0,Math.min(tile-1,Math.round((x-gutter)/(tile-2*gutter)*(tile-1)))),sy=Math.max(0,Math.min(tile-1,Math.round((y-gutter)/(tile-2*gutter)*(tile-1)))),si=(sy*tile+sx)*4,di=(y*c.width+mi*tile+x)*4,grain=optical?1:Math.max(.88,Math.min(1.12,1+((tex[si]+tex[si+1]+tex[si+2])/765-.5)*.24));
     const values=channel==='base'?base.slice(0,3).map(v=>Math.round(255*srgb(Math.min(1,v*grain)))):channel==='emission'?em.map(v=>Math.round(255*srgb(v))):channel==='normal'?(optical?[128,128,255]:[normal[si],normal[si+1],normal[si+2]]):[255,Math.round(255*Math.min(1,(p.roughnessFactor??1)*(2-grain))),Math.round(255*(p.metallicFactor??1))];for(let k=0;k<3;k++)out.data[di+k]=values[k];out.data[di+3]=255;
    }
   });cx.putImageData(out,0,0);atlas.push({bufferView:append(c.toBuffer('image/png')),mimeType:'image/png',name:'generated_court_'+channel});
  }
  doc.images=atlas;doc.textures=[0,1,2,3].map(source=>({source,sampler:0}));doc.materials[0].normalTexture={index:3,scale:.18};doc.materials[0].extras={generatedSurfaceFamilies:['metal'],atlasGutterPixels:gutter};doc.samplers=[{magFilter:9729,minFilter:9987,wrapS:33071,wrapT:33071}];
 }
 assert(maxPaletteError<.005,'Palette quantization must stay within normal8bit texture precision');assert.equal(indices.length/3,triangles);doc.buffers[0].byteLength=offset;
 let json=Buffer.from(JSON.stringify(doc));json=Buffer.concat([json,Buffer.alloc((4-json.length%4)%4,32)]);const bin=Buffer.concat(chunks),head=Buffer.alloc(20),tail=Buffer.alloc(8);head.writeUInt32LE(0x46546c67);head.writeUInt32LE(2,4);head.writeUInt32LE(28+json.length+bin.length,8);head.writeUInt32LE(json.length,12);head.writeUInt32LE(0x4e4f534a,16);tail.writeUInt32LE(bin.length);tail.writeUInt32LE(0x004e4942,4);
 const output=Buffer.concat([head,json,tail,bin]);await write('Assets/Art/court3d/'+outputName+'.glb',output);
 return {sourceName,outputName,sourceSHA256:createHash('sha256').update(input).digest('hex'),outputSHA256:createHash('sha256').update(output).digest('hex'),generatedSurfaces:hasSurfaces,materialsBefore:source.materials.length,materialsAfter:1,separatePodiumActors:16,triangles,geometryPreserved:true,maxLinearPaletteError:maxPaletteError,scope:'Material atlas within one model only; generated microrelief and UV added when available. Position/normal/index values, actor transforms, animation, scene ownership and16 podium actors unchanged.'};
}
export const emitPodiumMaterialAtlas=options=>emitMaterialAtlas({...options,sourceName:'debate_podium',outputName:'trial_podium',label:'MovablePodium'});
export const emitCourtRoomMaterialAtlas=options=>emitMaterialAtlas({...options,sourceName:'courtroom_stage',outputName:'courtroom_stage',label:'CourtRoom'});
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){const game=path.resolve(import.meta.dirname,'..'),repo=path.dirname(game),index=path.join(game,'Saved/game-trial-work-20261102/gpu-chapter-batches/overrides.json'),overrides=JSON.parse(await fs.readFile(index,'utf8')),options={repo,write:async(name,bytes)=>{const file=path.join(game,name);await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file,bytes);overrides['Content/'+name]=file;}},report={podium:await emitPodiumMaterialAtlas(options),room:await emitCourtRoomMaterialAtlas(options)};await fs.writeFile(index,JSON.stringify(overrides));await fs.writeFile(path.join(game,'Saved/game-trial-work-20261102/court-material-bake.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));}
