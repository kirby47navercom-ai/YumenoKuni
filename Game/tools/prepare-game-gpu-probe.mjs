// Synthetic game-content cost test, never production: dynamic glyph quads use one supplied texture.
import fs from 'node:fs/promises';import path from 'node:path';import {makeSceneComponent} from '../../../engineCreate/prototype/scene-components.js';
const root=path.resolve(import.meta.dirname,'..'),work=path.join(root,'Saved/game-trial-work-20261102'),out=path.join(work,'gpu-probe');await fs.mkdir(out,{recursive:true});
const scene=JSON.parse(await fs.readFile(path.join(work,'frozen-project/Assets/Scenes/Main.hbscene.json'),'utf8'));
const ids=[...Array.from({length:48},(_,i)=>'MB'+i),...Array.from({length:26},(_,i)=>'NB'+i),...Array.from({length:48},(_,i)=>'MS'+i),...Array.from({length:48},(_,i)=>'MF'+i),...Array.from({length:26},(_,i)=>'NF'+i)];
for(const [index,id]of ids.entries())scene.objects.push({id:'GlyphProbe_'+id,name:id,kind:'sprite',parent:'Camera',position:[0,0,-.4],rotation:[0,0,0],scale:[1,1,1],visible:true,components:[makeSceneComponent('SpriteRenderer',{texture:'Assets/Art/ui/aim.svg',width:80*.4/900,height:80*.4/900,color:[1,1,1,1],shading:'unlit',toneMapping:'display',billboard:false,visible:false,blendMode:'translucent',sortingOrder:1000+index,useCustomSize:true,castShadow:false})]});
const file=path.join(out,'Main.hbscene.json');await fs.writeFile(file,JSON.stringify(scene));await fs.writeFile(path.join(out,'overrides.json'),JSON.stringify({'Content/Assets/Scenes/Main.hbscene.json':file},null,2));
const source=`#pragma once
#include <HBEngine/Game.hpp>
#include <map>
#include <string>
namespace widgetownersv4 {
struct UI:hb::UI {
 struct G {bool visible=false;hb::Vec2 position{},scale{1,1};float rotation=0,opacity=1;};
 inline static std::map<std::string,G> glyphs;inline static bool frozen=false;
 static bool glyph(const std::string& e){return e.size()>2&&(e[0]=='M'||e[0]=='N')&&(e[1]=='B'||e[1]=='F'||e[1]=='S')&&e[2]>='0'&&e[2]<='9';}
 static hb::Actor* Owner(hb::Actor* a,const std::string& i){auto* o=hb::Scene::FindActorById("UI_"+i);return o?o:a;}
 static void apply(const std::string& e,unsigned fields){if(!frozen)return;auto* a=hb::Scene::FindActorById("GlyphProbe_"+e);if(!a)return;const auto& g=glyphs[e];if(fields&1)hb::Components::Set(a,"SpriteRenderer","visible",g.visible&&g.opacity>0);if(fields&2)hb::Scene::SetPosition(a,{(g.position.x-640)*.4f/900,(360-g.position.y)*.4f/900,-.4f});if(fields&4)hb::Scene::SetScale(a,{g.scale.x,g.scale.y,1});if(fields&8)hb::Scene::SetRotation(a,{0,0,-g.rotation});if(fields&16)hb::Components::SetColor(a,"SpriteRenderer","color",{1,1,1,g.opacity});}
 static void Freeze(){frozen=true;for(const auto& p:glyphs)if(p.second.visible&&p.second.opacity>0)apply(p.first,31);}
 static void Show(hb::Actor* a,const std::string& s,const std::string& i){hb::UI::Show(Owner(a,i),s,i);}static void Remove(hb::Actor* a,const std::string& i){hb::UI::Remove(Owner(a,i),i);}
 static void SetVisible(hb::Actor* a,const std::string& i,const std::string& e,bool v){if(i=="main"&&glyph(e)){glyphs[e].visible=v;apply(e,v?31:1);}if(i=="main"&&frozen)return;hb::UI::SetVisible(Owner(a,i),i,e,v);}
 static void SetPosition(hb::Actor* a,const std::string& i,const std::string& e,const hb::Vec2& v){if(i=="main"&&glyph(e)){glyphs[e].position=v;apply(e,2);}if(i=="main"&&frozen)return;hb::UI::SetPosition(Owner(a,i),i,e,v);}
 static void SetScale(hb::Actor* a,const std::string& i,const std::string& e,const hb::Vec2& v){if(i=="main"&&glyph(e)){glyphs[e].scale=v;apply(e,4);}if(i=="main"&&frozen)return;hb::UI::SetScale(Owner(a,i),i,e,v);}
 static void SetRotation(hb::Actor* a,const std::string& i,const std::string& e,float v){if(i=="main"&&glyph(e)){glyphs[e].rotation=v;apply(e,8);}if(i=="main"&&frozen)return;hb::UI::SetRotation(Owner(a,i),i,e,v);}
 static void SetOpacity(hb::Actor* a,const std::string& i,const std::string& e,float v){if(i=="main"&&glyph(e)){glyphs[e].opacity=v;apply(e,17);}if(i=="main"&&frozen)return;hb::UI::SetOpacity(Owner(a,i),i,e,v);}
`;
const rest=[['SetText','const std::string&'],['SetTexture','const std::string&'],['SetSize','const hb::Vec2&'],['SetColor','const hb::Color&'],['SetFont','const std::string&'],['SetFontSize','float']].map(([f,t])=>` static void ${f}(hb::Actor* a,const std::string& i,const std::string& e,${t} v){if(i=="main"&&frozen)return;hb::UI::${f}(Owner(a,i),i,e,v);}`).join('\n');
await fs.writeFile(path.join(out,'WidgetOwnersV4.hpp'),source+rest+'\n};\n}\n');console.log(JSON.stringify({actors:ids.length,scope:'Synthetic game GPU glyph cost probe; not product visuals or performance acceptance'}));
