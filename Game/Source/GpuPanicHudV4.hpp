#pragma once
#include "GpuTrialHudV4.hpp"
#include "Debate.hpp"
#include <array>
namespace gpupanichudv4 {
struct Lane {hb::Actor* actor=nullptr;std::string key;float time=0,alpha=0;bool visible=false;};
struct Cached {hb::Actor* actor=nullptr;std::string key;int index=0,lane=-1,width=0,height=0;float appliedAlpha=-1;bool shown=false;};
inline std::array<Lane,3> lanes;inline std::vector<Cached> cache;inline hb::Json data;inline std::map<std::string,hb::Json> bank;
inline bool ready=false,rootVisible=true,fallback=false;inline float rootAlpha=1;inline std::string error;inline int warmFrames=0;inline size_t warmAt=0;inline std::vector<std::pair<int,std::string>> warmKeys;
inline void release(){if(ready)for(auto& c:cache)if(c.actor&&hb::Scene::FindActorById("TrialBatch_PanicSlot"+std::to_string(c.index))==c.actor){hb::Components::SetBool(c.actor,"SpriteRenderer","visible",false);hb::Components::SetString(c.actor,"SpriteSkin","rig","");hb::Components::SetString(c.actor,"SpriteRenderer","sprite","");}}
inline void reset(){lanes={};cache.clear();data=hb::Json();bank.clear();ready=false;rootVisible=true;fallback=false;rootAlpha=1;error.clear();warmFrames=0;warmAt=0;warmKeys.clear();}
inline void mount(){
 release();reset();if(!hb::Scene::FindActorById("TrialBatch_PanicSlot0"))return;
 data=hb::Data::Get("Assets/Data/gpu_panic_layout.json");for(auto& row:data["bank"])bank.emplace(row["key"].get<std::string>(),row);
 const int capacity=data.at("cacheSlots").get<int>();if(capacity<1||capacity>16){error="Invalid panic cache capacity";return;}
 for(int i=0;i<capacity;i++){Cached c;c.index=i;c.actor=hb::Scene::FindActorById("TrialBatch_PanicSlot"+std::to_string(i));if(!c.actor){error="Panic statement cache actor missing";return;}cache.push_back(c);}ready=true;
}
inline void hide(){if(ready)for(auto& c:cache)if(c.shown){hb::Components::SetBool(c.actor,"SpriteRenderer","visible",false);c.shown=false;}for(auto& lane:lanes)lane.visible=false;rootVisible=false;}
inline std::string key(const std::string& font,const std::string& text,const std::string& kind,int start,const std::string& word){return gputrialhudv4::hash(font+"|"+text+"|"+kind+"|"+std::to_string(start)+"|"+word);}
inline void set(int i,const std::string& k,float time,float alpha,bool visible){auto& lane=lanes[i];lane.key=k;lane.time=time;lane.alpha=alpha;lane.visible=visible;}
inline bool warmup(const std::vector<std::pair<int,std::string>>& keys){
 if(!ready)return false;release();fallback=false;error.clear();warmAt=0;warmFrames=0;lanes={};warmKeys.clear();for(const auto& k:keys){if(!bank.count(k.second)||k.first<0||k.first>2){fallback=true;return false;}if(std::find(warmKeys.begin(),warmKeys.end(),k)==warmKeys.end())warmKeys.push_back(k);}
 if(warmKeys.size()>cache.size()){fallback=true;return false;}
 for(size_t i=0;i<cache.size();i++){auto& c=cache[i];c.key=i<warmKeys.size()?warmKeys[i].second:"";c.lane=i<warmKeys.size()?warmKeys[i].first:-1;c.width=c.height=0;c.appliedAlpha=-1;c.shown=false;}
 // A new task replaces the cache keys. Retire the previous task's lane keys
 // before the last warmup frame can flush them against the new cache.
 lanes={};warmAt=0;warmFrames=warmKeys.empty()?0:int(warmKeys.size())+3;return warmFrames>0;
}
inline void place(Cached& c,float w,float h){
 if(c.width==int(w)&&c.height==int(h))return;
 const float fit=std::min(w/1280.f,h/720.f),unit=2*.2f*std::tan(43.6f*3.14159265358979323846f/360)/h,units=data.at("units").get<float>();const auto& pose=data.at("lanes").at(c.lane);
 const auto type=debate::PANIC_TYPE[c.lane];
 hb::Scene::SetPosition(c.actor,{((pose.at("x").get<float>()+type.x)*fit-w*.5f)*unit,(h*.5f-(pose.at("y").get<float>()+type.y)*fit)*unit,-.2f});
 hb::Scene::SetScale(c.actor,{units*unit*fit*type.scale,units*unit*fit*type.scale,1});hb::Scene::SetRotation(c.actor,{0,0,-pose.at("angle").get<float>()});hb::Components::Set(c.actor,"SpriteRenderer","sortingOrder",850+c.lane);c.width=int(w);c.height=int(h);
}
inline void advance(){
 if(!ready||warmFrames<=0)return;const float w=gputrialhudv4::width,h=gputrialhudv4::height;if(w<=0||h<=0)return;
 if(warmAt<warmKeys.size()){
  auto& c=cache[warmAt++];const auto& spec=bank.at(c.key);hb::Sprites::SetSprite(c.actor,spec.at("sprite").get<std::string>());hb::Components::SetString(c.actor,"SpriteSkin","rig",spec.at("rigs").at(c.lane).get<std::string>());place(c,w,h);hb::Sprites::SetColor(c.actor,{1,1,1,1});c.appliedAlpha=1;hb::Components::SetBool(c.actor,"SpriteRenderer","visible",true);c.shown=true;
 }
 // The loading cover stays up until every current-task texture has actually rendered.
 if(warmFrames==1)for(auto& c:cache)if(c.shown){hb::Components::SetBool(c.actor,"SpriteRenderer","visible",false);c.shown=false;}
 --warmFrames;
}
inline void flush(){
 if(!ready||fallback||warmFrames>0||!error.empty())return;const float w=gputrialhudv4::width,h=gputrialhudv4::height;if(w<=0||h<=0)return;const float units=data.at("units").get<float>(),frequency=data.at("frequency").get<float>(),amplitude=data.at("amplitude").get<float>();
 float inherited=1;auto parent=std::string("Trial");for(int i=0;i<16&&!parent.empty();i++){if(!gputrialhudv4::visible[parent]){inherited=0;break;}inherited*=gputrialhudv4::opacity[parent];parent=gputrialhudv4::parents[parent];}
 std::vector<bool> shown(cache.size(),false);
 for(int i=0;i<3;i++){
  auto& lane=lanes[i];lane.actor=nullptr;const float alpha=lane.alpha*rootAlpha*inherited;if(!rootVisible||!lane.visible||alpha<=0||lane.key.empty())continue;
  auto found=std::find_if(cache.begin(),cache.end(),[&](const Cached& c){return c.lane==i&&c.key==lane.key;});if(found==cache.end()){error="Panic statement not prepared: "+lane.key+" lane="+std::to_string(i)+" cache=";for(const auto& c:cache)if(!c.key.empty())error+=std::to_string(c.lane)+":"+c.key+",";continue;}auto& c=*found;lane.actor=c.actor;shown[c.index]=true;place(c,w,h);
  if(c.appliedAlpha!=alpha){hb::Sprites::SetColor(c.actor,{1,1,1,alpha});c.appliedAlpha=alpha;}
  const float a=-2*amplitude*std::sin(frequency*lane.time)/units,b=-2*amplitude*std::cos(frequency*lane.time)/units;
  hb::SpriteSkin::SetBonePosition(c.actor,"cp",{0,a});hb::SpriteSkin::SetBonePosition(c.actor,"cn",{0,-a});hb::SpriteSkin::SetBonePosition(c.actor,"sp",{0,b});hb::SpriteSkin::SetBonePosition(c.actor,"sn",{0,-b});
 }
 for(auto& c:cache)if(c.shown!=shown[c.index]){hb::Components::SetBool(c.actor,"SpriteRenderer","visible",shown[c.index]);c.shown=shown[c.index];}
}
inline hb::Json slots(){auto out=hb::Json::array();for(const auto& lane:lanes){int slot=-1;for(const auto& c:cache)if(c.actor==lane.actor&&c.shown)slot=c.index;out.push_back(slot);}return out;}
struct Frame {~Frame(){try{flush();advance();}catch(const std::exception& e){error=e.what();}}};
}
