#pragma once
#include <HBEngine/Game.hpp>
#include "GpuTrialHudV4.hpp"
#include "GpuPanicHudV4.hpp"
#include "GpuNoiseHudV4.hpp"
#include <map>
#include <array>
#include <variant>

namespace widgetownersv4 {
// Scene-owned hosts die on travel; closed widgets release their UI immediately.
struct UI : hb::UI {
 inline static std::map<std::string,hb::Actor*> owners;
 using Value=std::variant<bool,float,std::string,std::array<float,2>,std::array<float,4>>;
 inline static std::map<std::string,std::map<std::string,Value>> applied;
 static std::string G(const std::string& i,const std::string& e){return i=="panicv4"&&gputrialhudv4::showdown&&e.rfind("P0G",0)==0?"SDG"+e.substr(3):e;}
 static bool GPU(const std::string& i,const std::string& e){return (i=="stage"&&gputrialhudv4::owns(e)&&(e.rfind("Arm",0)==0||e.rfind("Ar",0)==0||e.rfind("Piece",0)==0||e=="Ring"||e=="RingCore"))||(i=="panicv4"&&gputrialhudv4::showdown&&e.rfind("P0G",0)==0)||(i=="stage"&&gputrialhudv4::showdown&&(e.rfind("Sd",0)==0||e=="Slash"))||i=="main"||(i=="stage"&&e=="StageTimer")||(i=="panes"&&e!="root")||(i=="anagramv4"&&e!="root"&&gputrialhudv4::hasAnagram());}
 static bool Mounted(const std::string& i){return owners.count(i)!=0;}
 static hb::Actor* Owner(hb::Actor*,const std::string& i){auto at=owners.find(i);return at==owners.end()?nullptr:at->second;}
 static bool Changed(const std::string& i,const std::string& e,const char* property,const Value& value){
  if(!Mounted(i))return false;auto key=e+":"+property;auto& cache=applied[i];auto at=cache.find(key);if(at!=cache.end()&&at->second==value)return false;cache[key]=value;return true;
 }
 static void Show(hb::Actor* a,const std::string& asset,const std::string& i){
  auto* owner=Owner(a,i);if(!owner){owner=hb::Scene::FindActorById("UI_"+i);if(!owner)owner=hb::Scene::FindActorById("UI_modal");if(!owner)owner=a;if(!owner)throw std::runtime_error("Cannot create widget host: "+i);owners.emplace(i,owner);}applied.erase(i);hb::UI::Show(owner,asset,i);if(i=="main"){gputrialhudv4::mount();gpupanichudv4::mount();gpunoisehudv4::mount();}if(i=="stage")gputrialhudv4::setVisible("StageClockRoot",true);if(i=="panes")gputrialhudv4::setVisible("PanicPanesRoot",true);if(i=="anagramv4")gputrialhudv4::setVisible("AnagramRoot",true);if(i=="panicv4"){if(gputrialhudv4::showdown)gputrialhudv4::setVisible("ShowdownRoot",true);gpupanichudv4::rootVisible=true;gpupanichudv4::rootAlpha=1;}
 }
 static void Remove(hb::Actor* a,const std::string& i){if(i=="stage")gputrialhudv4::setVisible("StageClockRoot",false);if(i=="anagramv4")gputrialhudv4::releaseAnagram();auto* owner=Owner(a,i);if(!owner)return;if(i=="main"){gpunoisehudv4::hide();gpunoisehudv4::reset();gpupanichudv4::hide();gpupanichudv4::release();gpupanichudv4::reset();gputrialhudv4::hide();}if(i=="panes")gputrialhudv4::setVisible("PanicPanesRoot",false);if(i=="panicv4"){gputrialhudv4::setVisible("ShowdownRoot",false);gpupanichudv4::hide();}hb::UI::Remove(owner,i);owners.erase(i);applied.erase(i);}
 static void SetText(hb::Actor* a,const std::string& i,const std::string& e,const std::string& v){if(Changed(i,e,"text",v))if(!GPU(i,e)||!gputrialhudv4::setText(G(i,e),v))hb::UI::SetText(Owner(a,i),i,e,v);}
 static void SetVisible(hb::Actor* a,const std::string& i,const std::string& e,bool v){if(i=="stage"&&e=="root"&&gputrialhudv4::visible.count("SolutionSceneRoot")&&gputrialhudv4::parents["SolutionSceneRoot"].empty())gputrialhudv4::setVisible("SolutionSceneRoot",v);if(i=="stage"&&e=="root"&&gputrialhudv4::visible.count("ArmSceneRoot"))gputrialhudv4::setVisible("ArmSceneRoot",v);if(i=="stage"&&e=="root")gputrialhudv4::setVisible("StageClockRoot",v);if(i=="anagramv4"&&e=="root")gputrialhudv4::setVisible("AnagramRoot",v);if(i=="panes"&&e=="root")gputrialhudv4::setVisible("PanicPanesRoot",v);if(i=="panicv4"&&e=="root"){gputrialhudv4::setVisible("ShowdownRoot",v);gpupanichudv4::rootVisible=v;gputrialhudv4::setVisible("PanicPanesRoot",v);}if(Changed(i,e,"visible",v))if(!GPU(i,e)||!gputrialhudv4::setVisible(G(i,e),v))hb::UI::SetVisible(Owner(a,i),i,e,v);}
 static void SetTexture(hb::Actor* a,const std::string& i,const std::string& e,const std::string& v){if(i=="pad"&&e=="PdFloor"&&Mounted(i))hb::UI::SetTexture(Owner(a,i),i,"PdOutsideFloor",v);if(Changed(i,e,"texture",v))if(!GPU(i,e)||!gputrialhudv4::setTexture(G(i,e),v))hb::UI::SetTexture(Owner(a,i),i,e,v);}
 static void SetPosition(hb::Actor* a,const std::string& i,const std::string& e,const hb::Vec2& v){if(Changed(i,e,"position",std::array<float,2>{v.x,v.y}))if(!GPU(i,e)||!gputrialhudv4::setPosition(G(i,e),v))hb::UI::SetPosition(Owner(a,i),i,e,v);}
 static void SetSize(hb::Actor* a,const std::string& i,const std::string& e,const hb::Vec2& v){if(Changed(i,e,"size",std::array<float,2>{v.x,v.y}))if(!GPU(i,e)||!gputrialhudv4::setSize(G(i,e),v))hb::UI::SetSize(Owner(a,i),i,e,v);}
 static void SetScale(hb::Actor* a,const std::string& i,const std::string& e,const hb::Vec2& v){if(Changed(i,e,"scale",std::array<float,2>{v.x,v.y}))if(!GPU(i,e)||!gputrialhudv4::setScale(G(i,e),v))hb::UI::SetScale(Owner(a,i),i,e,v);}
 static void SetColor(hb::Actor* a,const std::string& i,const std::string& e,const hb::Color& v){if(Changed(i,e,"color",std::array<float,4>{v.r,v.g,v.b,v.a}))if(!GPU(i,e)||!gputrialhudv4::setColor(G(i,e),v))hb::UI::SetColor(Owner(a,i),i,e,v);}
 static void SetRotation(hb::Actor* a,const std::string& i,const std::string& e,float v){if(Changed(i,e,"rotation",v))if(!GPU(i,e)||!gputrialhudv4::setRotation(G(i,e),v))hb::UI::SetRotation(Owner(a,i),i,e,v);}
 static void SetOpacity(hb::Actor* a,const std::string& i,const std::string& e,float v){if(i=="stage"&&e=="root")gputrialhudv4::setOpacity("StageClockRoot",v);if(i=="anagramv4"&&e=="root")gputrialhudv4::setOpacity("AnagramRoot",v);if(i=="panicv4"&&e=="root"){gputrialhudv4::setOpacity("ShowdownRoot",v);gpupanichudv4::rootAlpha=v;}if(i=="panes"&&e=="root")gputrialhudv4::setOpacity("PanicPanesRoot",v);if(Changed(i,e,"opacity",v))if(!GPU(i,e)||!gputrialhudv4::setOpacity(G(i,e),v))hb::UI::SetOpacity(Owner(a,i),i,e,v);}
 static void SetFont(hb::Actor* a,const std::string& i,const std::string& e,const std::string& v){if(Changed(i,e,"font",v))if(!GPU(i,e)||!gputrialhudv4::setFont(G(i,e),v))hb::UI::SetFont(Owner(a,i),i,e,v);}
 static void SetFontSize(hb::Actor* a,const std::string& i,const std::string& e,float v){if(Changed(i,e,"fontSize",v))if(!GPU(i,e)||!gputrialhudv4::setFontSize(G(i,e),v))hb::UI::SetFontSize(Owner(a,i),i,e,v);}
};
}
