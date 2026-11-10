#include "../Game/Source/Debate.hpp"
#include <cassert>
#include <iostream>
int main() {
 using namespace debate;
 Line claim{"","A second statement supports part of the story.","weak","supports","card"};
 claim.start=19;claim.readable=true;claim.yaw=20;
 int checked=0;
 for(auto composition:{"reason","infer","qualify","compare","question","recall","correct","deny","insist","drop","hesitate","regret","suspect","tease","address","still"})for(int motion=0;motion<12;++motion)for(int lane=0;lane<3;++lane)for(float t:{.5f,.65f,.78f}){
  claim.composition=composition;claim.motion=static_cast<Motion>(motion);
  auto letters=place(claim,t,lane,54);
  float lo=900,hi=0;int targets=0;
  for(const auto& g:letters){
   assert(g.front&&g.opacity>.99f);
   if(!(g.x-g.halfW>=94.f&&g.x+g.halfW<=1186.f)){std::cerr<<composition<<" lane "<<lane<<" t "<<t<<" x "<<g.x<<" half "<<g.halfW<<"\n";return 1;}
   assert(g.y-g.halfH>=129.f&&g.y+g.halfH<=551.f);
   lo=std::min(lo,g.depth);hi=std::max(hi,g.depth);
   targets+=g.weak;
  }
  assert(targets==8);++checked;
 }
 Line solid;solid.text=u8"가";solid.kind="weak";solid.word=solid.text;solid.readable=true;solid.performance="assertive";solid.yaw=28;
 for(float t:{.5f,.65f,.78f})for(const auto& g:place(solid,t,1,54)){assert(g.solid&&g.yaw!=0&&g.pitch!=0);assert(inside(g,g.x,g.y,0));assert(!inside(g,g.x+500,g.y+500,0));}
 Line speech=solid;speech.text=u8"가 가";speech.word=speech.text;speech.composition="reason";speech.performance="measured";
 auto early=place(speech,.30f/duration(speech,54),1,54);assert(early.front().opacity>.9f&&early.back().opacity==0);
 auto held=place(speech,.55f,1,54);for(const auto& g:held)assert(g.opacity>.99f);
 // Neither the old .48 fit gate nor the .94 restoration may move a word.
 for(auto cue:{"reason","infer","qualify","compare","question","recall","correct","deny","insist","drop","hesitate","regret","suspect","tease","address","still"}){
  claim.composition=cue;
  for(float t:{.4799f,.8099f,.9399f}){auto a=place(claim,t,1,54),b=place(claim,t+.0002f,1,54);for(size_t i=0;i<a.size();++i)assert(std::hypot(a[i].x-b[i].x,a[i].y-b[i].y)<.2f);}
 }
 Line fake=claim;fake.answer="decoy:none";fake.decoy=true;
 Line noise{"","Wait a second!","noise"};noise.motion=Motion::Wave;noise.noiseFor=0;
 State s;s.lines={claim,fake,noise};s.restartRows();s.noisePool=true;
 s.time=1.8f;
 auto over=s.noise();
 assert(!over.empty());for(const auto& g:over){assert(g.front&&g.depth<SPEAKER_Z);if(g.text!=" "){assert(g.opacity>.9f);assert(s.noiseHit(g.x,g.y));}}
 s.lines[2].text=u8"당연히 무리";s.lines[2].id=NOISE_BINDINGS[0].id;s.time=noiseCue(s.lines[2].id,"").delay+1;over=s.noise();assert(over.size()>2);assert(over.front().x<over.back().x);
 auto stable=over;s.time+=.5f;auto later=s.noise();assert(stable.size()==later.size());for(size_t k=0;k<stable.size();++k){assert(stable[k].x==later[k].x&&stable[k].y==later[k].y&&stable[k].rotation==later[k].rotation);}
 // Impact retains contact glyphs, then expires. Debris cannot block a shot.
 s.shatterNoise(2);s.silenced[2]=true;assert(!s.noiseDebris.empty());
 assert(!s.noiseHit(over.front().x,over.front().y));assert(!s.noise().empty());
 s.tickNoiseDebris(.33f);assert(s.noiseDebris.empty());s.silenced[2]=false;s.shatterNoise(2);assert(!s.noiseDebris.empty());s.restartRows();assert(s.noiseDebris.empty());
 assert(!s.cleared());s.broken[0]=true;assert(s.cleared());
 s.broken[0]=false;s.index=1;s.next();assert(s.passes==1&&s.index==0);
 std::cout<<checked<<" readable depth samples; foreground noise, decoy and wrap PASS\n";
}
