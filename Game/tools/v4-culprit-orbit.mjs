import fs from 'node:fs/promises';
import path from 'node:path';

export async function mirrorCulpritSweep(bytes,{createCanvas,loadImage}){
 const source=await loadImage(bytes);
 const canvas=createCanvas(source.width,source.height),ctx=canvas.getContext('2d');
 ctx.translate(source.width,0);
 ctx.scale(-1,1);
 ctx.drawImage(source,0,0);
 return canvas.toBuffer('image/png');
}

export async function emitCulpritOrbit({repo,write,base,createCanvas,loadImage,focus,plate}){
 const textures=new Map();
 async function texture(row){
  if(textures.has(row.texture))return textures.get(row.texture);
  const image=await loadImage(await fs.readFile(path.join(repo,row.texture)));
  const canvas=createCanvas(image.width,image.height),g=canvas.getContext('2d');
  g.drawImage(image,0,0);
  const pixels=g.getImageData(0,0,image.width,image.height);
  const bar=row.resource.includes('_bar_');
  for(let i=0;i<pixels.data.length;i+=4){
   const level=Math.max(pixels.data[i],pixels.data[i+1],pixels.data[i+2])/255;
   const white=bar?Math.max(0,(level-.62)/.38):level**5*.62;
   pixels.data[i]=255;
   pixels.data[i+1]=27+228*white;
   pixels.data[i+2]=68+187*white;
   pixels.data[i+3]*=level;
  }
  g.putImageData(pixels,0,0);textures.set(row.texture,canvas);
  return canvas;
 }
 async function draw(g,row){
  const [x,y,w,h]=row.rect;
  g.save();g.translate(x+w/2,y+h/2);g.rotate(row.rotation*Math.PI/180);
  g.globalAlpha=row.opacity;g.drawImage(await texture(row),-w/2,-h/2,w,h);g.restore();
 }
 const ring=[];
 for(let i=0;i<focus.frames.length;i++){
  const canvas=createCanvas(1024,432),g=canvas.getContext('2d');
  g.save();g.translate(512,216);g.scale(1.65,.72);
  for(const row of focus.frames[i])if(row.texture&&row.opacity)await draw(g,row);
  g.restore();
  // Remove the rear arc across the torso. The front pass stays intact.
  g.globalCompositeOperation='destination-out';
  g.beginPath();g.moveTo(455,70);g.bezierCurveTo(468,32,553,32,570,70);
  g.lineTo(607,215);g.quadraticCurveTo(512,258,417,215);g.closePath();g.fill();
  const asset=base+'culprit_source_ring_'+i+'.png';
  await write(asset,canvas.toBuffer('image/png'));ring.push(asset);
 }
 const sweep=[];
 for(let i=plate.labels.fl_next-1;i<plate.labels.fl_out-1;i++){
  const canvas=createCanvas(1280,720),g=canvas.getContext('2d');
  for(const row of plate.frames[i])if(row.texture&&row.opacity&&row.resource.includes('_bar_'))await draw(g,row);
  const asset=base+'culprit_source_sweep_'+sweep.length+'.png';
  const bytes=canvas.toBuffer('image/png');
  await write(asset,bytes);
  await write(asset.replace('.png','_left.png'),await mirrorCulpritSweep(bytes,{createCanvas,loadImage}));
  sweep.push(asset);
 }
 return {ring,sweep,labels:focus.labels};
}

export const worldOrbitTexture='Assets/Art/ui/v3/trial_picker/culprit_world_orbit.svg';

export async function emitCulpritWorldOrbit(court,write){
 const seat=court.objects.find(o=>o.id==='Seat0');
 const ring=structuredClone(seat);
 Object.assign(ring,{id:'CulpritWorldOrbit',name:'Culprit selection orbit',rotation:[-90,0,0]});
 const sprite=ring.components.find(c=>c.type==='SpriteRenderer');
 sprite.id='c1f124fe-b6bf-4b87-9fcb-b2251e8f1e95';
 Object.assign(sprite.properties,{texture:worldOrbitTexture,width:1.7,height:1.7,visible:false,
  blendMode:'translucent',alphaCutoff:0,castShadow:false,receiveShadow:false});
 court.objects.push(ring);
 await write(worldOrbitTexture,`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
 <g fill="none" stroke-linecap="round">
 <circle cx="256" cy="256" r="210" stroke="#ff1947" stroke-opacity=".18" stroke-width="31"/>
 <circle cx="256" cy="256" r="210" stroke="#ff395e" stroke-opacity=".4" stroke-width="12"/>
 <circle cx="256" cy="256" r="210" stroke="#ff8194" stroke-opacity=".63" stroke-width="3"/>
 <path d="M 466,256 A 210,210 0 0 1 189,455 M 46,256 A 210,210 0 0 1 323,57" stroke="#ff234d" stroke-width="18" opacity=".6"/>
 <path d="M 466,256 A 210,210 0 0 1 189,455 M 46,256 A 210,210 0 0 1 323,57" stroke="#ff9ba6" stroke-width="7"/>
 <path d="M 466,256 A 210,210 0 0 1 393,415 M 46,256 A 210,210 0 0 1 119,97" stroke="#fff1f2" stroke-width="3"/>
 </g></svg>`);
}
