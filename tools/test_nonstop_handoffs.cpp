
#include "../Game/Source/GlyphDisplayV4.hpp"
#include <cassert>
#include <iostream>
using namespace glyphdisplayv4;
void glyphHandoff(){Batch b;std::map<std::string,Values> rendered;int texts=0;
auto flush=[&]{b.flush([&](const auto& id,const Values& v,unsigned f){auto& r=rendered[id];if(f&Visible)r.visible=v.visible;if(f&Text){r.text=v.text;++texts;}});};
auto show=[&](std::string prefix,int n){for(int i=0;i<n;i++){auto id=prefix+std::to_string(i);b.visible(id,true);b.text(id,"ink");}flush();};
show("NF",18);show("MF",32);assert(texts==50);
// A font handoff empties backend M text outside Batch. Only M needs a resend.
for(auto& [id,v]:rendered)if(id[0]=='M')v.text="";
b.invalidatePrefix("M");show("MF",32);assert(texts==82);
for(int i=8;i<18;i++)b.visible("NF"+std::to_string(i),false);flush();
int live=0;for(auto& [id,v]:rendered)if(id[0]=='N'&&v.visible)live++;assert(live==8);
for(int i=0;i<32;i++)assert(rendered["MF"+std::to_string(i)].text=="ink");
// Repeated handoffs may neither suppress same-text new fonts nor lose noise hide state.
for(int n:{26,3,19,0,8}){show("NF",n);b.invalidatePrefix("M");show("MF",32);for(int i=n;i<26;i++)b.visible("NF"+std::to_string(i),false);flush();live=0;for(auto& [id,v]:rendered)if(id[0]=='N'&&v.visible)live++;assert(live==n);}
std::cout<<"font resend + 18->8,26->3,19->0 noise tails PASS\n";
}


#include "../Game/Source/LieV4.hpp"
#include <cassert>
#include <iostream>
void lieRelease(){for(float dt:{1.f/120,1.f/60,.04f,.2f}){liev4::State s;float fraction=0;int transforms=0,shots=0;
for(float t=0;t<2;t+=dt){auto e=s.advance(dt,true,false,true,fraction);transforms+=e==liev4::Event::Transformed;shots+=liev4::isShot(e);}
assert(transforms==1&&shots==0&&s.transformed&&s.phase==liev4::Phase::Hold);
auto e=s.advance(dt,false,false,true,fraction);assert(e==liev4::Event::LieShot&&liev4::isShot(e));assert(s.settle(true)==0&&s.phase==liev4::Phase::Idle);
assert(s.advance(dt,false,false,true,fraction)==liev4::Event::None);
s.advance(.1f,true,false,true,fraction);e=s.advance(.01f,false,false,true,fraction);assert(e==liev4::Event::NormalShot&&liev4::isShot(e));}
assert(!liev4::isShot(liev4::Event::Transformed)&&!liev4::isShot(liev4::Event::None));std::cout<<"held conversion never fires; release fires exactly once at120/60/25/5Hz PASS\n";}

#include "../Game/Source/ShotRecoveryV4.hpp"
void namedProjectile(){for(auto target:{std::pair<float,float>{90,120},{1190,120},{90,560},{1190,560}}){
 auto a=shotv4::WordFlight::make(target.first,target.second,false,137),b=shotv4::WordFlight::make(target.first,target.second,true,137);
 assert(std::abs(a.duration*.5f-b.duration)<.0001f&&std::abs(a.prepare*.5f-b.prepare)<.0001f);
 for(auto size:{std::pair<float,float>{1280,720},{2560,1440},{3440,1440},{1024,768}}){
  float lastZ=0;for(int k=0;k<=120;k++){auto p=shotv4::WordFlight::letter(k/120.f,0,19,target.first,target.second,a.originY,size.first,size.second);assert(p.z<=lastZ&&std::isfinite(p.x)&&std::isfinite(p.y)&&p.scale>0);lastZ=p.z;}
  auto end=shotv4::WordFlight::letter(1,18,19,target.first,target.second,a.originY,size.first,size.second);assert(!end.visible);
 }
 }std::cout<<"named closed-mesh flight: distinct depth, toward frozen aim, laser timing, four viewport aspects PASS\n";}

int main(){glyphHandoff();lieRelease();namedProjectile();}
