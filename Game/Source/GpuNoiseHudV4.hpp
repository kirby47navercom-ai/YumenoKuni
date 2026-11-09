#pragma once
#include "GpuTrialHudV4.hpp"
#include <array>
namespace gpunoisehudv4 {
struct Row {
 hb::Actor* actor=nullptr;std::string key,applied;float time=0,x=0,y=0,scale=1,alpha=0,depth=1250;
 int start=0,count=0,width=0,height=0;bool visible=false,shown=false;float appliedScale=-1;hb::Color color{-1,-1,-1,-1};
};
inline std::array<Row,3> rows;inline std::map<std::string,hb::Json> bank;inline hb::Json data;
inline bool ready=false;inline std::string error;inline int warmFrames=0;inline size_t warmAt=0;inline std::vector<std::string> warmKeys;
inline void clear(){for(auto& row:rows)row.visible=false;gputrialhudv4::noiseOwned.clear();}
inline void reset(){rows={};bank.clear();data=hb::Json();ready=false;error.clear();warmFrames=0;warmAt=0;warmKeys.clear();gputrialhudv4::noiseOwned.clear();}
inline void mount(){
 reset();if(!hb::Scene::FindActorById("TrialBatch_Noise0"))return;
 data=hb::Data::Get("Assets/Data/gpu_noise_layout.json");for(const auto& spec:data.at("bank"))bank.emplace(spec.at("key").get<std::string>(),spec);
 for(int i=0;i<3;i++){rows[i].actor=hb::Scene::FindActorById("TrialBatch_Noise"+std::to_string(i));if(!rows[i].actor){error="Noise row actor missing";return;}}ready=true;
}
inline void hide(){if(ready)for(auto& row:rows)if(row.shown){hb::Components::SetBool(row.actor,"SpriteRenderer","visible",false);row.shown=false;}clear();}
inline bool set(int slot,const std::string& key,float time,float x,float y,float scale,float alpha,float depth,int start,int count){
 if(!ready||slot<0||slot>=3||!bank.count(key)||bank.at(key).at("count").get<int>()!=count)return false;
 auto& row=rows[slot];row.key=key;row.time=time;row.x=x;row.y=y;row.scale=scale;row.alpha=alpha;row.depth=depth;row.start=start;row.count=count;row.visible=true;
 for(int i=start;i<start+count;i++)for(const auto* face:{"NF","NB"})gputrialhudv4::noiseOwned.insert(std::string(face)+std::to_string(i));return true;
}
inline bool warmup(const std::vector<std::string>& keys){
 if(!ready)return false;warmKeys.clear();for(const auto& key:keys)if(bank.count(key)&&std::find(warmKeys.begin(),warmKeys.end(),key)==warmKeys.end())warmKeys.push_back(key);
 warmAt=0;warmFrames=warmKeys.empty()?0:int(warmKeys.size())+2;return warmFrames>0;
}
inline void advance(){
 if(!ready||warmFrames<=0)return;if(warmAt<warmKeys.size()){const auto& spec=bank.at(warmKeys[warmAt++]);for(auto& row:rows){hb::Sprites::SetSprite(row.actor,spec.at("sprite").get<std::string>());hb::Components::SetString(row.actor,"SpriteSkin","rig",spec.at("rig").get<std::string>());row.applied.clear();}}--warmFrames;
}
inline void flush(){
 if(!ready)return;const float w=gputrialhudv4::width,h=gputrialhudv4::height;if(w<=0||h<=0)return;
 const float fit=std::min(w/1280.f,h/720.f),unit=2*.2f*std::tan(43.6f*3.14159265358979323846f/360)/h;
 const float units=data.at("units").get<float>(),size=data.at("size").get<float>(),amplitude=data.at("amplitude").get<float>(),frequency=data.at("frequency").get<float>();
 for(auto& row:rows){
  bool show=row.visible&&warmFrames<=0&&bank.count(row.key);float inherited=1;hb::Color color{1,1,1,1};
  auto node=gputrialhudv4::nodes.find("NF"+std::to_string(row.start));
  if(node==gputrialhudv4::nodes.end())show=false;else{color=node->second.color;auto parent=node->second.parent;for(int i=0;i<16&&!parent.empty();i++){show=show&&gputrialhudv4::visible[parent];inherited*=gputrialhudv4::opacity[parent];parent=gputrialhudv4::parents[parent];}}
  color.a*=row.alpha*inherited;show=show&&color.a>0;
  bool onscreen=false;if(show)for(int i=row.start;i<row.start+row.count;i++){auto n=gputrialhudv4::nodes.find("NF"+std::to_string(i));if(n!=gputrialhudv4::nodes.end()&&gputrialhudv4::inView(n->second)){onscreen=true;break;}}show=show&&onscreen;
  if(show){
   const auto& spec=bank.at(row.key);if(row.applied!=row.key){hb::Sprites::SetSprite(row.actor,spec.at("sprite").get<std::string>());hb::Components::SetString(row.actor,"SpriteSkin","rig",spec.at("rig").get<std::string>());row.applied=row.key;row.appliedScale=-1;}
   const float projection=900.f/row.depth,ratio=row.depth/900.f,x=row.x-spec.at("firstLocal").get<float>()*row.scale,y=row.y-amplitude*projection*std::sin(frequency*row.time);
   hb::Scene::SetPosition(row.actor,{(x*fit-w*.5f)*unit*ratio,(h*.5f-y*fit)*unit*ratio,-.2f*ratio});
   if(row.width!=int(w)||row.height!=int(h)||row.appliedScale!=row.scale){hb::Scene::SetScale(row.actor,{units*row.scale*fit*unit*ratio,units*row.scale*fit*unit*ratio,1});row.width=int(w);row.height=int(h);row.appliedScale=row.scale;}
   if(row.color.r!=color.r||row.color.g!=color.g||row.color.b!=color.b||row.color.a!=color.a){hb::Sprites::SetColor(row.actor,gputrialhudv4::linearTint(color));row.color=color;}
   const float a=-2*amplitude/size/units*std::sin(frequency*row.time),b=-2*amplitude/size/units*std::cos(frequency*row.time);
   hb::SpriteSkin::SetBonePosition(row.actor,"cp",{0,a});hb::SpriteSkin::SetBonePosition(row.actor,"cn",{0,-a});hb::SpriteSkin::SetBonePosition(row.actor,"sp",{0,b});hb::SpriteSkin::SetBonePosition(row.actor,"sn",{0,-b});
  }
  if(show!=row.shown){hb::Components::SetBool(row.actor,"SpriteRenderer","visible",show);row.shown=show;}
 }
}
struct Frame {Frame(){clear();}~Frame(){try{flush();advance();}catch(const std::exception& e){error=e.what();}}};
}
