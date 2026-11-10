import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const root=path.resolve(import.meta.dirname,'..'),sourceFile=path.resolve(root,'../../engineCreate/tools/native-game-runner.mjs'),source=await fs.readFile(sourceFile,'utf8'),work=path.join(root,'Saved/native-visual-candidate-'+Date.now());await fs.mkdir(work,{recursive:true});
const anchor="const ambientLight=new THREE.HemisphereLight",old='prepareVisual:visual.build,update:visual.syncSprite,services:';assert(source.includes(anchor)&&source.includes(old));
const replacement=`// Sync all native component changes, including runtime mesh/visibility swaps.
    const signature=object=>visualComponentSignature(object),slowSignature=value=>JSON.stringify(JSON.parse(value).filter(c=>c.type!=='SpriteRenderer').map(c=>c.type==='MeshRenderer'?{...c,properties:{...c.properties,visible:undefined}}:c));
    const disposeVisual=group=>{for(const model of models){let at=model;while(at&&at!==group)at=at.parent;if(at===group){disposeHeadlessModel(model);models.delete(model);}}visual.dispose(group);};
    const updateVisual=async(object,group)=>{
     const before=group.userData.componentSignature;if(before===undefined)return;
     const next=signature(object);if(before===next)return visual.syncSprite(object);
     if(slowSignature(before)===slowSignature(next)){const p=object.components?.find(c=>c.type==='MeshRenderer')?.properties;if(p)group.traverse(child=>{if(child.isMesh&&!child.userData.sprite&&child.userData.objectId===object.id)child.visible=(child.userData.hbModelOverrides?.visible??child.userData.hbNativeModelVisible??true)&&p.visible!==false&&p.enabled!==false;});const result=await visual.syncSprite(object);group.userData.componentSignature=next;return result;}
     if(visual.meshRendererProperties(object))return visual.syncSprite(object);
     const replacement=primitives.build(object);replacement.userData.objectId=object.id;replacement.position.copy(group.position);replacement.rotation.copy(group.rotation);replacement.scale.copy(group.scale);replacement.visible=group.visible;
     const parent=group.parent,children=group.children.filter(c=>meshes.get(c.userData.objectId)===c);meshes.set(object.id,replacement);parent?.add(replacement);
     try{await visual.build(object,replacement);}catch(error){meshes.set(object.id,group);replacement.removeFromParent();disposeVisual(replacement);throw error;}
     for(const child of children)replacement.add(child);group.removeFromParent();disposeVisual(group);
    };
    `;
let candidate=source.replace("import {sceneRendering} from '../prototype/scene-rendering.js';","import {sceneRendering,visualComponentSignature} from '../prototype/scene-rendering.js';").replace('const models=[],primitives=','const models=new Set(),primitives=').replace('models.push(loaded.object);return loaded;','loaded.object.traverse(node=>{node.userData.hbNativeModelVisible=node.visible;});models.add(loaded.object);return loaded;').replace(anchor,replacement+anchor).replace(old,'prepareVisual:visual.build,update:updateVisual,services:');
const file=path.join(work,'native-game-runner.candidate.mjs');await fs.writeFile(file,candidate);const sha=b=>createHash('sha256').update(b).digest('hex');await fs.writeFile(path.join(work,'report.json'),JSON.stringify({source:sourceFile,original:sha(source),candidate:sha(candidate),file,engineOriginalModified:false,scope:'Candidate native component-signature synchronization. Rebuild changes outside sprite updates/in-place mesh properties; preserve child actor groups and rollback on load failure.'},null,2));console.log(JSON.stringify({file}));
