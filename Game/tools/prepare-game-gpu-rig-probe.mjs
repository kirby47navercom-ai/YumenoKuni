// Cost test for batching the game's moving glyph quads; supplied placeholder texture only.
import fs from 'node:fs/promises';import path from 'node:path';import assert from 'node:assert/strict';
import {makeSceneComponent} from '../../../engineCreate/prototype/scene-components.js';import {validSpriteRig} from '../../../engineCreate/prototype/sprite-rig-assets.js';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/game-trial-work-20261102'),out=path.join(work,'gpu-rig-probe');await fs.mkdir(out,{recursive:true});const overrides={};
const write=async(asset,data)=>{const file=path.join(out,asset);await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file,JSON.stringify(data));overrides['Content/'+asset]=file;};
const sprite='Assets/Art/ui/GlyphProbe.hbsprite.json';await write(sprite,{version:1,name:'GlyphProbe',texture:'Assets/Art/ui/aim.svg',normalTexture:'',pixelsPerUnit:100,rect:[0,0,64,64],pivot:[.5,.5],filter:'linear',border:[0,0,0,0]});
const scene=JSON.parse(await fs.readFile(path.join(work,'frozen-project/Assets/Scenes/Main.hbscene.json'),'utf8'));
for(const [layer,count]of [['MB',48],['NB',26],['MS',48],['MF',48],['NF',26]]){
 const rig={version:1,name:'Glyph '+layer,sprite,bones:[{id:'root',name:'Root',parent:'',position:[0,0],rotation:0,scale:[1,1],length:1}],vertices:[],triangles:[],clips:[],solvers:[]};
 for(let i=0;i<count;i++){const bone='g'+i;rig.bones.push({id:bone,name:bone,parent:'root',position:[0,0],rotation:0,scale:[1,1],length:1});const at=rig.vertices.length;for(const [x,y,u,v]of [[-40,-40,0,0],[40,-40,1,0],[-40,40,0,1],[40,40,1,1]])rig.vertices.push({position:[x*.4/900,y*.4/900],uv:[u,v],weights:[{bone,weight:1}]});rig.triangles.push(at,at+1,at+3,at,at+3,at+2);}
 assert(validSpriteRig(rig));const asset='Assets/Art/ui/GlyphProbe_'+layer+'.hbspriterig.json';await write(asset,rig);
 scene.objects.push({id:'GlyphRig_'+layer,name:layer,kind:'sprite',parent:'Camera',position:[0,0,-.4],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[makeSceneComponent('SpriteRenderer',{sprite,shading:'unlit',toneMapping:'display',billboard:false,visible:false,blendMode:'translucent',sortingOrder:1000+scene.objects.length,castShadow:false}),makeSceneComponent('SpriteSkin',{rig:asset})]});
}
await write('Assets/Scenes/Main.hbscene.json',scene);await fs.writeFile(path.join(out,'overrides.json'),JSON.stringify(overrides,null,2));
let source=await fs.readFile(path.join(work,'gpu-probe/WidgetOwnersV4.hpp'),'utf8');
const start=source.indexOf(' static void apply('),end=source.indexOf('\n static void Show(',start);assert(start>=0&&end>start);
source=source.slice(0,start)+` static void apply(const std::string& e,unsigned fields){if(!frozen)return;auto* a=hb::Scene::FindActorById("GlyphRig_"+e.substr(0,2));if(!a)return;const auto& g=glyphs[e];auto bone="g"+e.substr(2);const bool show=g.visible&&g.opacity>0;if((fields&3)||!show)hb::SpriteSkin::SetBonePosition(a,bone,show?hb::Vec2{(g.position.x-640)*.4f/900,(360-g.position.y)*.4f/900}:hb::Vec2{-9999,-9999});if(show&&(fields&4))hb::SpriteSkin::SetBoneScale(a,bone,g.scale);if(show&&(fields&8))hb::SpriteSkin::SetBoneRotation(a,bone,-g.rotation);}
 static void Freeze(){frozen=true;for(auto p:{"MB","NB","MS","MF","NF"})if(auto* a=hb::Scene::FindActorById(std::string("GlyphRig_")+p))hb::Components::Set(a,"SpriteRenderer","visible",true);for(const auto& p:glyphs)apply(p.first,31);}
`+source.slice(end);
await fs.writeFile(path.join(out,'WidgetOwnersV4.hpp'),source);console.log(JSON.stringify({actors:5,glyphs:196,scope:'Synthetic GPU rig cost probe; no per-glyph alpha or product art acceptance'}));
