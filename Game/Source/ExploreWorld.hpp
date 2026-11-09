#pragma once
// Authored 3D exploration. REA informs free movement/fixed-eye separation; coordinates
// and velocities belong to this game's authored GLBs, not measured original values.
#include <HBEngine/Game.hpp>
#include "Courtroom.hpp"
#include "RuntimeScenesV4.hpp"
#include "DisplayV4.hpp"
#include "GameInputV4.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <map>
#include <queue>
#include <set>
#include <string>
#include <vector>
namespace exworld {
using J=hb::Json;
constexpr float ORIGIN=300.f, PI=3.14159265f, RADIUS=.27f;
struct Viewport {float width=1280,height=720,fit=1;};inline Viewport viewport;
inline void refreshViewport(){
#ifdef _WIN32
 static HWND ownWindow=nullptr;if(!ownWindow||!IsWindow(ownWindow))ownWindow=displayv4::Window();RECT r{};displayv4::DpiScope dpi;if(ownWindow&&GetClientRect(ownWindow,&r)&&r.right>0&&r.bottom>0){viewport.width=float(r.right);viewport.height=float(r.bottom);viewport.fit=std::min(viewport.width/1280.f,viewport.height/720.f);}
#endif
}
inline bool canvasMouse(hb::Vec2& p){refreshViewport();bool available=hb::Input::GetMousePosition(p);p.x/=viewport.fit;p.y/=viewport.fit;return available;}
struct Point {float x=0,y=0,z=0;};
struct Target {Point p;int hot=-1,room=-1;bool person=false,located=false;std::string label,slug;int reaction=-1;};
struct Pose {float x=0,y=1.6f,z=0,yaw=0,pitch=0;};
struct CctvHead {std::string id;float x,z,yaw,phase=0;};
struct State {
 J data;std::string id,space,mesh;Pose pose;bool loaded=false,active=false,free=false,visible=false,geometryVisible=false;
 mutable int autoGoal=-1;mutable std::vector<Point> autoPath;
 std::vector<std::string> roomIds;std::vector<Target> targets;std::map<std::string,Pose> history;
 float mouseX=-1,mouseY=-1,footTime=0;int footstep=0,doorOver=-1;
 int audioHover=-1;
 float hoverSoundCooldown=0;
 float v4StepPhase=0, v4StepSpeed=0;
 float cursorX=640,cursorY=360,bobPhase=0,bobOffset=0;
 std::map<std::string,std::array<float,2>> uiCache;
 int environmentPhase=0,accessChapter=0;std::string environmentStamp;
 std::vector<CctvHead> cctvHeads;
 float cctvElapsed=0;
 const J& spec()const{
  const auto& entry=data["spaces"][space];if(!entry.contains("bucket"))return entry;
  static std::map<std::string,J> pages;auto path=entry["bucket"].get<std::string>();
  auto found=pages.find(path);if(found==pages.end())found=pages.emplace(path,hb::Data::Get(path)).first;
  return found->second.at("spaces").at(space);
 }
 void remember(){if(active&&!id.empty())history[id]=pose;}
};
inline Point point(const J& j){return {j[0].get<float>(),j[1].get<float>(),j[2].get<float>()};}
inline Pose entryPose(const J& spec){
 auto p=point(spec["spawn"]);
 return {p.x,p.y,p.z,std::clamp(spec.value("entry_yaw",0.f),spec["yaw_limits"][0].get<float>(),spec["yaw_limits"][1].get<float>()),std::clamp(spec.value("entry_pitch",0.f),spec["pitch_limits"][0].get<float>(),spec["pitch_limits"][1].get<float>())};
}
inline float wrap(float a){return std::fmod(a+540.f,360.f)-180.f;}
inline void load(State& s){if(s.loaded)return;s.data=hb::Data::Get("Assets/Data/explore_world.json");s.loaded=s.data.is_object()&&s.data.contains("spaces");}
inline bool accessible(const State& s,const std::string& id){
 if(!s.data["instances"].contains(id))return false;if(id==s.id||!s.data.contains("parkLevels"))return true;
 auto group=s.data["instances"][id].value("district",std::string("residence"));return s.accessChapter>=s.data["parkLevels"]["minimumChapter"].value(group,0);
}
inline std::string resolve(const State& s,const std::string& name,const std::string& bg,const std::string& explicitId=""){
 if(!s.loaded)return "";
 if(!explicitId.empty()&&s.data["instances"].contains(explicitId))return explicitId;
 if(s.data["instances"].contains(name))return name;
 // Longest authored name first, so e.g. 운영 기록실 is not shortened to 기록실.
 std::string result;size_t best=0;
 for(auto& [id,i]:s.data["instances"].items()) {auto label=i.value("label","");if(!label.empty()&&name.find(label)!=std::string::npos&&label.size()>best){best=label.size();result=id;}}
 for(auto& a:s.data["aliases"]){auto term=a[0].get<std::string>();if(term.size()>best&&name.find(term)!=std::string::npos){result=a[1].get<std::string>();best=term.size();}}
 if(!result.empty())return result;
 if(s.data["backgrounds"].contains(bg))return s.data["backgrounds"][bg].get<std::string>();
 return "";
}
inline float floorAt(const State& s,float x,float z){
 float current=s.pose.y-s.spec().value("eye_height",1.6f),height=-1e6f;
 if(s.spec().contains("walk_surfaces"))for(auto& p:s.spec()["walk_surfaces"])
  if(x>=p[0].get<float>()-.02f&&x<=p[2].get<float>()+.02f&&z>=p[1].get<float>()-.02f&&z<=p[3].get<float>()+.02f&&p[4].get<float>()<=current+.28f)height=std::max(height,p[4].get<float>());
 return height>-1e5f?height:s.spec().value("floor",0.f);
}
inline bool solid(const State& s,float x,float z,float radius=RADIUS){
 if(!s.active)return false;auto& d=s.spec();auto& b=d["bounds"];
 if(x<b[0].get<float>()+radius||x>b[2].get<float>()-radius||z<b[1].get<float>()+radius||z>b[3].get<float>()-radius)return true;
 if(s.id=="plaza"&&s.data.contains("parkLevels"))for(const auto& gate:s.data["connections"])if(gate.value("kind",std::string())=="park_gate"&&gate.value("minimumChapter",0)>s.accessChapter){auto p=point(gate["a_p"]);if(std::abs(x-p.x)<3.5f+radius&&std::abs(z-p.z)<.25f+radius)return true;}
 float floor=s.pose.y-d.value("eye_height",1.6f);
 for(auto& c:d["collision"])if((c.size()<6||(c[4].get<float>()<floor+1.6f&&c[5].get<float>()>floor+.34f))&&x>c[0].get<float>()-radius&&x<c[2].get<float>()+radius&&z>c[1].get<float>()-radius&&z<c[3].get<float>()+radius)return true;
 return false;
}
inline Point stand(const State& s,Point p){
 for(int r=0;r<50;r++)for(int k=0;k<(r?24:1);k++){float a=k*PI/12,x=p.x+r*.15f*std::cos(a),z=p.z+r*.15f*std::sin(a);if(!solid(s,x,z))return{x,floorAt(s,x,z),z};}
 return{s.pose.x,s.pose.y-s.spec().value("eye_height",1.6f),s.pose.z};
}
inline void environment(State& s,int phase){
 s.environmentPhase=std::clamp(phase,0,2);bool outside=s.active&&s.visible&&s.spec().value("outdoor",false);auto stamp=std::to_string(outside)+":"+std::to_string(s.environmentPhase)+":"+s.id+":"+std::to_string(s.accessChapter);if(stamp==s.environmentStamp)return;s.environmentStamp=stamp;
 static const char* suffix[]{"sky","ambient","sun","clouds","fog"};static const char* type[]{"SkyAtmosphere","SkyLight","DirectionalLight","VolumetricCloud","ExponentialHeightFog"};
 for(int p=0;p<3;p++)for(int k=0;k<5;k++)if(auto* a=scenesv4::find("Outdoor"+std::to_string(p)+"_"+suffix[k]))hb::Components::Set(a,type[k],"enabled",outside&&p==s.environmentPhase&&k!=3);
 if(auto* a=scenesv4::find("OutdoorSkyDome")){hb::Components::Set(a,"MeshRenderer","visible",outside);if(!outside)hb::Components::SetString(a,"MeshRenderer","mesh","");if(outside){static const char* phaseName[]{"day","night","evening"};hb::Components::SetString(a,"MeshRenderer","mesh","Assets/Art/environment/sky_"+std::string(phaseName[s.environmentPhase])+".glb");hb::Scene::SetPosition(a,{ORIGIN+s.pose.x,s.pose.y,s.pose.z});}}
 if(auto* a=scenesv4::find("Camera"))hb::Components::Set(a,"Camera","far",outside?1500.f:200.f);
 if(s.data.contains("worldContext")){
  auto origin=outside?point(s.data["instances"][s.id].value("p",J::array({0,0,0}))):Point{};
  auto set=[&](const std::string& id,bool on,const std::string& mesh){if(auto* a=scenesv4::find(id)){hb::Components::SetString(a,"MeshRenderer","mesh",on?mesh:std::string());hb::Components::Set(a,"MeshRenderer","visible",on);if(on)hb::Scene::SetPosition(a,{ORIGIN-origin.x,-origin.y,-origin.z});}};
  set("ExteriorContext",outside,s.data["worldContext"].value("mesh",std::string()));for(const auto& [id,mesh]:s.data["worldContext"]["landmarks"].items())set("Exterior_"+id,outside&&id!=s.space,mesh.get<std::string>());
 }
 if(auto* a=scenesv4::find("ParkGeometry")){
  hb::Components::Set(a,"MeshRenderer","visible",outside);
  if(outside){auto origin=point(s.data["instances"][s.id].value("p",J::array({0,0,0})));hb::Scene::SetPosition(a,{ORIGIN-origin.x,-origin.y,-origin.z});}
 }
 if(s.data.contains("parkLevels"))for(const auto& gate:s.data["connections"])if(gate.value("kind",std::string())=="park_gate")if(auto* a=scenesv4::find("ParkGate_"+gate["b"].get<std::string>())){
  bool closed=outside&&gate.value("minimumChapter",0)>s.accessChapter;hb::Components::Set(a,"MeshRenderer","visible",closed);
  hb::Components::SetString(a,"MeshRenderer","mesh",closed?"Assets/Art/park_levels/gate.glb":std::string());
  if(closed){auto origin=point(s.data["instances"][s.id].value("p",J::array({0,0,0}))),p=point(gate["a_p"]);hb::Scene::SetPosition(a,{ORIGIN-origin.x+p.x,-origin.y,-origin.z+p.z});}
 }
 for(auto id:{"CourtAmbient","CourtKey","CourtFill"})if(auto* a=scenesv4::find(id))hb::Components::Set(a,std::string(id)=="CourtAmbient"?"SkyLight":"DirectionalLight","enabled",!outside);
}
inline void visible(State& s,bool on){
 bool changed=s.visible!=on;s.visible=on;environment(s,s.environmentPhase);
 bool local=on&&s.active&&!(s.data.contains("parkLevels")&&s.spec().value("outdoor",false)&&s.spec().value("mode",std::string())!="fixed_pan")&&!s.spec().value("mesh",std::string()).empty();
 if(changed||s.geometryVisible!=local){s.geometryVisible=local;if(auto* a=scenesv4::find("ExploreGeometry"))hb::Components::Set(a,"MeshRenderer","visible",local);}
 if(!changed)return;
 if(!on)for(int i=0;i<2;i++)if(auto* a=scenesv4::find("ExploreReaction"+std::to_string(i)))hb::Components::Set(a,"MeshRenderer","visible",false);
 if(!on)for(int i=0;i<10;i++)if(auto* a=scenesv4::find("ExploreTarget"+std::to_string(i)))hb::Components::Set(a,"SpriteRenderer","visible",false);
 for(int k=0;k<16;k++)if(auto* a=scenesv4::find("ExplorePerson"+std::to_string(k)))hb::Components::Set(a,"SpriteRenderer","visible",false);
}
inline void begin(State& s,const std::string& id,bool resume=false,bool freeTime=false){
 auto previous=s.id;s.remember();s.active=false;if(!s.loaded||!s.data["instances"].contains(id)){visible(s,false);return;}
 if(previous!=id){s.cctvHeads.clear();s.cctvElapsed=0;}
 s.id=id;s.space=s.data["instances"][id].value("space","");s.active=true;s.free=freeTime||s.spec().value("mode","")=="free_walk";
 auto p=point(s.spec()["spawn"]);s.pose=entryPose(s.spec());if(resume&&s.history.count(id)){auto saved=s.history[id];if(std::isfinite(saved.x)&&std::isfinite(saved.y)&&std::isfinite(saved.z)&&std::isfinite(saved.yaw)&&std::isfinite(saved.pitch)){if(!s.free){saved.x=p.x;saved.y=p.y;saved.z=p.z;}s.pose=saved;if(s.free&&solid(s,s.pose.x,s.pose.z))s.pose={p.x,p.y,p.z,saved.yaw,saved.pitch};}}
 if(s.free&&previous!=id&&!previous.empty())for(auto& e:s.data["connections"]){bool a=e["a"]==id&&e["b"]==previous,b=e["b"]==id&&e["a"]==previous;if(!a&&!b)continue;auto door=point(e[a?"a_p":"b_p"]);float n=std::max(.01f,std::hypot(door.x,door.z));
  s.pose.x=door.x-door.x/n*.9f;s.pose.z=door.z-door.z/n*.9f;s.pose.y=door.y-1.2f+s.spec().value("eye_height",1.6f);s.pose.yaw=std::atan2(door.x,door.z)*180/PI;
  auto safe=stand(s,{s.pose.x,0,s.pose.z});s.pose.x=safe.x;s.pose.z=safe.z;s.pose.y=safe.y+s.spec().value("eye_height",1.6f);break;}
 if(!scenesv4::exploreReady(s.spec().value("levelScene",std::string("Explore")))){s.visible=false;return;}
 auto mesh=s.spec().value("mesh","");if(mesh!=s.mesh){s.mesh=mesh;if(auto* a=scenesv4::find("ExploreGeometry"))hb::Components::SetString(a,"MeshRenderer","mesh",s.data.contains("parkLevels")&&s.spec().value("outdoor",false)&&s.spec().value("mode",std::string())!="fixed_pan"?std::string():mesh);}
 if(auto* a=scenesv4::find("ExploreGeometry"))hb::Scene::SetPosition(a,{ORIGIN,0,0});
 s.targets.clear();s.autoGoal=-1;s.autoPath.clear();s.uiCache.clear();s.mouseX=s.mouseY=-1;s.bobOffset=s.bobPhase=0;visible(s,true);
}
inline void updateParkCctv(State& s,float delta){
 if(!s.active||!s.free||!s.visible||!scenesv4::explore.loaded)return;
 constexpr float interval=1.f/30,rangeSquared=18.f*18.f;
 s.cctvElapsed+=delta;
 if(s.cctvElapsed<interval)return;
 const float remainder=std::fmod(s.cctvElapsed,interval);
 const float elapsed=std::min(s.cctvElapsed-remainder,.1f);
 s.cctvElapsed=remainder;
 if(s.cctvHeads.empty()){
  if(!scenesv4::find("ParkBackground"))return;
  for(int i=0;;++i){
   auto id="ParkCctv"+std::to_string(i);
   auto* actor=scenesv4::find(id);
   if(!actor)break;
   const auto p=hb::Scene::GetLocalPosition(actor);
   s.cctvHeads.push_back({std::move(id),p.x,p.z,hb::Scene::GetRotation(actor).y});
  }
 }
 // Only the nearest two heads can issue transform writes. Distance uses the
 // player pose, so turning the view or opening a free camera cannot activate one.
 std::array<CctvHead*,2> nearest{};
 std::array<float,2> distances{rangeSquared,rangeSquared};
 for(auto& head:s.cctvHeads){
  const float dx=head.x-s.pose.x,dz=head.z-s.pose.z,distance=dx*dx+dz*dz;
  if(distance<distances[0]){
   nearest[1]=nearest[0];distances[1]=distances[0];
   nearest[0]=&head;distances[0]=distance;
  }else if(distance<distances[1]){
   nearest[1]=&head;distances[1]=distance;
  }
 }
 for(auto* head:nearest){
  if(!head)continue;
  auto* actor=scenesv4::find(head->id);
  if(!actor)continue;
  head->phase=std::fmod(head->phase+elapsed*(2*PI/6.f),2*PI);
  hb::Scene::SetRotation(actor,{0,head->yaw+55.f*std::sin(head->phase),0});
 }
}
inline void camera(State& s){
 if(!s.active)return;court::Cam c{ORIGIN+s.pose.x,s.pose.y+s.bobOffset,s.pose.z,s.pose.yaw,s.pose.pitch,0};auto rot=court::engineRotation(c);
 if(auto* a=scenesv4::find("Camera")){hb::Scene::SetPosition(a,{c.x,c.y,c.z});hb::Scene::SetRotation(a,{rot.x,rot.y,rot.z});if(hb::Components::GetFloat(a,"Camera","fieldOfView")!=court::FIELD_OF_VIEW)hb::Components::SetFloat(a,"Camera","fieldOfView",court::FIELD_OF_VIEW);}
 if(s.visible&&s.spec().value("outdoor",false))if(auto* a=scenesv4::find("OutdoorSkyDome"))hb::Scene::SetPosition(a,{c.x,c.y,c.z});
}
inline bool project(const State& s,Point p,float& x,float& y,float& depth){
 if(!court::screen({s.pose.x,s.pose.y+s.bobOffset,s.pose.z,s.pose.yaw,s.pose.pitch,0},p.x,p.y,p.z,x,y,depth))return false;
 float scale=viewport.height/(720.f*viewport.fit);x=(x-640)*scale+viewport.width/(2*viewport.fit);y=(y-360)*scale+viewport.height/(2*viewport.fit);
 return x>-150&&x<viewport.width/viewport.fit+150&&y>-200&&y<viewport.height/viewport.fit+200;
}
inline bool occluded(const State& s,Point target){
 // Eye-to-point segment against the authored obstruction boxes, not screen-radius selection.
 float dx=target.x-s.pose.x,dz=target.z-s.pose.z,dist=std::hypot(dx,dz);
 for(auto& c:s.spec()["collision"]){if(c.size()>=6&&(c[4].get<float>()>std::max(s.pose.y,target.y)||c[5].get<float>()<std::min(s.pose.y,target.y)))continue;if(target.x>=c[0].get<float>()-.01f&&target.x<=c[2].get<float>()+.01f&&target.z>=c[1].get<float>()-.01f&&target.z<=c[3].get<float>()+.01f)continue;float lo=0,hi=1;bool hit=true;
  for(int k=0;k<2;k++){float start=k?s.pose.z:s.pose.x,step=k?dz:dx,a=c[k].get<float>(),b=c[k+2].get<float>();
   if(std::abs(step)<.0001f){if(start<a||start>b){hit=false;break;}}
   else{float t0=(a-start)/step,t1=(b-start)/step;if(t0>t1)std::swap(t0,t1);lo=std::max(lo,t0);hi=std::min(hi,t1);if(lo>hi){hit=false;break;}}}
  // Last .38m contains the selected object's own collision box. Do not hide its face.
  if(hit&&hi>0&&lo>0&&lo*dist<dist-.38f)return true;
 }
 return false;
}
inline int at(const State& s,float x,float y,bool doorsOnly=false){
 int best=-1;float score=1e9f;
 for(int k=0;k<int(s.targets.size());k++){auto& t=s.targets[k];if(doorsOnly&&t.room<0)continue;
  float u,v,d;if(!project(s,t.p,u,v,d))continue;if(s.free&&std::hypot(t.p.x-s.pose.x,t.p.z-s.pose.z)>4.8f)continue;
  if(t.located&&occluded(s,t.p))continue;
  float w=t.person?std::clamp(900.f*.38f/d,22.f,140.f):42.f;
  float z=t.person?(std::abs(u-x)<w&&std::abs(v-y)<std::min(220.f,900.f*.9f/d)?std::abs(u-x):1e9f):std::hypot(u-x,v-y);
  if(z<(t.person?w:48.f)&&z<score){score=z;best=k;}}
 return best;
}
inline void reticle(State& s,hb::Vec2 mouse,bool looking,float scale){
 refreshViewport();float width=viewport.width/viewport.fit,height=viewport.height/viewport.fit;
 if(s.mouseX<0){s.cursorX=std::clamp(mouse.x,0.f,width);s.cursorY=std::clamp(mouse.y,0.f,height);return;}
 if(looking)return;float x=mouse.x-s.mouseX,y=mouse.y-s.mouseY;
 // Own mouse-pixel normalization; native pad/mouse magnitude and deadzone
 // units are separate. Reticle slowdown affects no camera or OS cursor.
 if(std::hypot(x,y)<7.f&&at(s,s.cursorX,s.cursorY)>=0)scale/=6;
 s.cursorX=std::clamp(s.cursorX+x*scale,0.f,width);s.cursorY=std::clamp(s.cursorY+y*scale,0.f,height);
}
inline bool bob(State& s,float distance,bool enabled){
 float old=s.bobOffset;s.bobPhase+=distance*8.f;s.bobOffset=enabled&&distance>0?std::sin(s.bobPhase)*.035f:0;
 return std::abs(old-s.bobOffset)>.00001f;
}
inline Point locate(const State& s,const std::string& name,int ordinal,int total,bool& located){
 located=false;size_t longest=0;std::string term;
 for(auto& t:s.data["terms"]){auto k=t[0].get<std::string>();if(name.find(k)!=std::string::npos&&k.size()>longest){longest=k.size();term=t[1].get<std::string>();}}
 if(!term.empty()){
  for(auto& t:s.spec()["targets"])if(t.value("id","").find(term)!=std::string::npos){located=true;return point(t["p"]);}
  // Prefer the largest matching existing object; tiny trim/lettering is not a clue object.
  float best=0;Point chosen;
  for(auto& t:s.spec()["nodes"])if(t.value("id","").find(term)!=std::string::npos){auto a=point(t["box"][0]),b=point(t["box"][1]);float area=std::abs((a.x-b.x)*(a.y-b.y)*(a.z-b.z));if(area>best){best=area;chosen=point(t["p"]);}}
  if(best>0){located=true;return chosen;}
 }
 // The manuscript may describe a photo/document rather than a 3D prop. Keep its
 // inspection entry near the fixed eye, explicitly marked unlocated in debug data.
 float a=(-55.f+110.f*(ordinal+.5f)/std::max(total,1))*PI/180;
 return {s.pose.x+std::sin(a)*2.4f,s.pose.y-.2f,s.pose.z-std::cos(a)*2.4f};
}
inline void addPerson(State& s,int hot,const std::string& slug,int index,int count){
 float a=(-62+124.f*(index+.5f)/std::max(count,1))*PI/180;
 Point foot=stand(s,{s.pose.x+std::sin(a)*3.1f,0,s.pose.z-std::cos(a)*3.1f});
 // Free-walk characters stand on reachable floor. Fixed rooms keep the same fixed eye.
 Point center{foot.x,foot.y+.9f,foot.z};s.targets.push_back({center,hot,-1,true,true,"",slug});
 if(index<16)if(auto* actor=scenesv4::find("ExplorePerson"+std::to_string(index))){
  hb::Scene::SetPosition(actor,{ORIGIN+center.x,center.y,center.z});
  hb::Components::SetString(actor,"SpriteRenderer","texture","Assets/Art/figure/"+slug+".webp");
  hb::Components::Set(actor,"SpriteRenderer","visible",true);
 }
}
inline std::vector<std::string> route(const State& s,const std::string& from,const std::string& to){
 std::queue<std::string> q;q.push(from);std::map<std::string,std::string> prev;prev[from]="";
 while(!q.empty()){auto at=q.front();q.pop();if(at==to)break;for(auto& e:s.data["connections"]){if(e.value("minimumChapter",0)>s.accessChapter)continue;std::string next;if(e["a"]==at)next=e["b"].get<std::string>();else if(e["b"]==at)next=e["a"].get<std::string>();if(!next.empty()&&accessible(s,next)&&!prev.count(next)){prev[next]=at;q.push(next);}}}
 if(!prev.count(to))return{};std::vector<std::string> out;for(auto at=to;!at.empty();at=prev[at])out.push_back(at);std::reverse(out.begin(),out.end());return out;
}
inline void addDoors(State& s){
 for(auto& e:s.data["connections"]){bool a=e["a"]==s.id,b=e["b"]==s.id;if(!a&&!b)continue;auto dest=e[a?"b":"a"].get<std::string>();
  if(e.value("kind",std::string())=="park_gate"&&e.value("minimumChapter",0)>s.accessChapter){s.targets.push_back({point(e[a?"a_p":"b_p"]),-1,-2,false,true,e.value("label",std::string())+" · 아직 개방되지 않았어요",""});continue;}
  auto found=std::find(s.roomIds.begin(),s.roomIds.end(),dest);if(found==s.roomIds.end())continue;
  auto p=point(e[a?"a_p":"b_p"]);s.targets.push_back({p,-1,int(found-s.roomIds.begin()),false,true,s.data["instances"][dest].value("label",dest),""});}
}
inline bool move(State& s,float dt,float fwd,float side,bool run){
 if(!s.active||!s.free)return false;float norm=std::hypot(fwd,side);if(norm<.01f)return false;fwd/=norm;side/=norm;
 float a=s.pose.yaw*PI/180,speed=(run?5.4f:2.4f),total=std::min(dt,.1f)*speed;
 float dx=(-std::sin(a)*fwd+std::cos(a)*side)*total,dz=(-std::cos(a)*fwd-std::sin(a)*side)*total;
 int steps=std::max(1,int(std::ceil(std::hypot(dx,dz)/.09f)));bool changed=false;
 for(int k=0;k<steps;k++){float x=s.pose.x+dx/steps,z=s.pose.z+dz/steps;
  if(!solid(s,x,s.pose.z)){s.pose.x=x;changed=true;}if(!solid(s,s.pose.x,z)){s.pose.z=z;changed=true;}}
 if(changed)s.pose.y=floorAt(s,s.pose.x,s.pose.z)+s.spec().value("eye_height",1.6f);s.remember();return changed;
}
inline void look(State& s,float yaw,float pitch){
 auto& d=s.spec();s.pose.yaw=wrap(s.pose.yaw+yaw);
 if(!s.free)s.pose.yaw=std::clamp(s.pose.yaw,d["yaw_limits"][0].get<float>(),d["yaw_limits"][1].get<float>());
 s.pose.pitch=std::clamp(s.pose.pitch+pitch,d["pitch_limits"][0].get<float>(),d["pitch_limits"][1].get<float>());s.remember();
}
inline J autoTarget(const State& s,int target){
 if(target<0||target>=int(s.targets.size()))return J{{"kind","key"},{"key","m"}};
 auto& t=s.targets[target];Point aim=t.p;float distance=std::hypot(aim.x-s.pose.x,aim.z-s.pose.z);
 // Once the actual target is visible and in interaction range, stop following
 // stale waypoints. Otherwise QA walks past a doorway until it is underfoot.
 if(s.free&&distance<3.2f&&(!t.located||!occluded(s,aim)))s.autoPath.clear();
 if(s.free&&(distance>4.1f||(t.located&&occluded(s,aim)))){
  // Local navigation only uses the same authored collision bounds as manual walking.
  // It is QA input guidance, never a teleport or normal player auto-solve feature.
  if(s.autoGoal!=target||s.autoPath.empty()){
   s.autoGoal=target;s.autoPath.clear();auto& b=s.spec()["bounds"];float x0=b[0].get<float>()+.3f,z0=b[1].get<float>()+.3f,step=.45f;
   int w=std::max(1,int((b[2].get<float>()-x0-.3f)/step)),h=std::max(1,int((b[3].get<float>()-z0-.3f)/step));
   auto pos=[&](int k){return Point{x0+(k%w)*step,s.pose.y,z0+(k/w)*step};};
   int sx=std::clamp(int(std::round((s.pose.x-x0)/step)),0,w-1),sz=std::clamp(int(std::round((s.pose.z-z0)/step)),0,h-1),start=sz*w+sx;
   std::vector<int> prev(w*h,-2);std::queue<int> queue;queue.push(start);prev[start]=-1;int goal=-1,closest=start;float best=1e9f;
   while(!queue.empty()){int k=queue.front();queue.pop();auto p=pos(k);float d=std::hypot(p.x-t.p.x,p.z-t.p.z);if(d<best){best=d;closest=k;}if(d<1.5f){goal=k;break;}
    for(auto offset:std::array<std::array<int,2>,4>{{{{1,0}},{{-1,0}},{{0,1}},{{0,-1}}}}){int x=k%w+offset[0],z=k/w+offset[1];if(x<0||x>=w||z<0||z>=h)continue;int n=z*w+x;auto p=pos(n);if(prev[n]!=-2||solid(s,p.x,p.z,.31f))continue;prev[n]=k;queue.push(n);}}
   if(goal<0)goal=closest;for(int k=goal;k>=0&&k!=start;k=prev[k])s.autoPath.push_back(pos(k));std::reverse(s.autoPath.begin(),s.autoPath.end());
  }
  while(!s.autoPath.empty()&&std::hypot(s.autoPath.front().x-s.pose.x,s.autoPath.front().z-s.pose.z)<.28f)s.autoPath.erase(s.autoPath.begin());
  if(!s.autoPath.empty())aim=s.autoPath.front();
 }
 float dx=aim.x-s.pose.x,dz=aim.z-s.pose.z,flat=std::hypot(dx,dz);
 float yaw=std::atan2(-dx,-dz)*180/PI,diff=wrap(yaw-s.pose.yaw);
 if(std::abs(diff)>3.f)return J{{"kind","key"},{"key",diff>0?"ArrowRight":"ArrowLeft"}};
 if(s.free&&!s.autoPath.empty())return J{{"kind","key"},{"key","w"}};
 float pitch=std::atan2(t.p.y-s.pose.y,std::max(.1f,distance))*180/PI;
 auto& lim=s.spec()["pitch_limits"];pitch=std::clamp(pitch,lim[0].get<float>(),lim[1].get<float>());
 if(std::abs(pitch-s.pose.pitch)>3)return J{{"kind","key"},{"key",pitch>s.pose.pitch?"ArrowUp":"ArrowDown"}};
 float x,y,depth;if(project(s,t.p,x,y,depth)&&x>0&&x<1280&&y>0&&y<720)return J{{"kind","click"},{"x",x},{"y",y}};
 return J{{"kind","key"},{"key","m"}};
}
inline J stats(const State& s){
 if(!s.active)return J{{"active",false}};int unlocated=0;for(auto& t:s.targets)if(!t.located)++unlocated;
 return J{{"active",true},{"space",s.id},{"level",s.spec().value("levelScene",std::string("Explore"))},{"district",s.data["instances"][s.id].value("district",std::string())},{"accessChapter",s.accessChapter},{"canvas",{viewport.width,viewport.height,viewport.fit}},{"control",s.free?"free_walk":"fixed_eye"},
 {"position",{s.pose.x,s.pose.y,s.pose.z}},{"yaw",s.pose.yaw},{"pitch",s.pose.pitch},{"cursor",{s.cursorX,s.cursorY}},{"bob",s.bobOffset},{"collision",s.spec()["collision"].size()},{"targets",s.targets.size()},{"unlocated",unlocated}};
}
inline J save(const State& s){J out=J::object();for(auto& [id,p]:s.history)out[id]={p.x,p.y,p.z,p.yaw,p.pitch};if(s.active&&!s.id.empty()){const auto& p=s.pose;out[s.id]={p.x,p.y,p.z,p.yaw,p.pitch};}return out;}
inline void restore(State& s,const J& data){if(!data.is_object())return;for(auto& [id,v]:data.items())if(v.is_array()&&v.size()==5)s.history[id]={v[0].get<float>(),v[1].get<float>(),v[2].get<float>(),v[3].get<float>(),v[4].get<float>()};}
} // namespace exworld
