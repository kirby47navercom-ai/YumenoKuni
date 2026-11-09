#pragma once
#include "Debate.hpp"
#include <algorithm>
#include <array>
namespace silencerv4 {
enum class Mode {None=-1,Normal=0,Rapid=1,Spread=2,Blast=3,Remote=4};
struct State {
 struct Pulse {int life=0;float x=0,y=0;Mode mode=Mode::None;};std::array<Pulse,3> pulses{};
 int charge=0,cooldown=0,lastSlot=-1;bool armed=true,remotePending=false;float fraction=0;
 void reset(bool requireRelease=false){*this={};armed=!requireRelease;}
 Mode tick(bool held,bool machine,bool shotgun,bool grenade,bool remote=false,bool enabled=true){
  for(auto& p:pulses)if(p.life>0)--p.life;lastSlot=-1;
  auto launch=[&](Mode mode){for(int i=0;i<3;i++)if(pulses[i].life==0){pulses[i].life=10;pulses[i].mode=mode;lastSlot=i;cooldown=mode==Mode::Rapid?5:10;return mode;}return Mode::None;};
  if(cooldown>0)--cooldown;if(!enabled){charge=0;return Mode::None;}
  if(!armed){if(!held)armed=true;return Mode::None;}
  if(remote&&cooldown==0){charge=0;return launch(Mode::Remote);}
  if(grenade){if(held){charge=std::min(60,charge+1);return Mode::None;}if(charge>0&&cooldown==0){auto result=charge>=60?Mode::Blast:Mode::Normal;charge=0;return launch(result);}if(!held)charge=0;return Mode::None;}
  if(!held||cooldown>0)return Mode::None;return launch(machine?Mode::Rapid:shotgun?Mode::Spread:Mode::Normal);
 }
};
inline bool overlap(const std::vector<debate::Glyph>& glyphs,float x,float y,bool spread){
 for(const auto& g:glyphs){if(g.opacity<=.3f)continue;if(!spread){auto target=g;target.halfW*=1.4f;target.halfH*=1.4f;if(debate::inside(target,x,y,0))return true;}else{float dx=std::max(0.f,std::abs(x-g.x)-g.halfW),dy=std::max(0.f,std::abs(y-g.y)-g.halfH);if(std::hypot(dx,dy)<=200)return true;}}return false;
}
inline std::vector<int> targets(const debate::State& debate,Mode mode,float x,float y){
 if(mode==Mode::None)return {};
 const int forced=debate.panicForcedNoise();
 std::vector<int> out;auto pool=debate.noiseIndices();for(int slot=0;slot<int(pool.size());slot++){int at=pool[slot];if(forced>=0&&at!=forced)continue;auto gs=debate.noiseGlyphs(at,slot);if(!std::any_of(gs.begin(),gs.end(),[](const auto& g){return g.opacity>.3f&&g.text!=" "&&g.x+g.halfW>0&&g.x-g.halfW<1280&&g.y+g.halfH>0&&g.y-g.halfH<720;}))continue;if(mode==Mode::Blast||mode==Mode::Remote||overlap(debate.noiseGlyphs(at,slot),x,y,mode==Mode::Spread)){out.push_back(at);if(mode==Mode::Remote||mode==Mode::Normal||mode==Mode::Rapid)break;}}return out;
}
struct Break {bool changed=false;int reward=0;bool damaged=false;};
// Own authored loud roles adapt the native gated glyph31 branch. Native
// activation authorship is unresolved; ordinary noise never enters this path.
inline std::vector<int> advanceLoud(debate::State& state,float seconds,bool equipped){
 if(!state.panic())return {};if(state.loudElapsed.size()!=state.lines.size()){state.loudElapsed.assign(state.lines.size(),0);state.loudChecked.assign(state.lines.size(),false);}
 std::vector<int> out;auto pool=state.noiseIndices();for(int slot=0;slot<int(pool.size());slot++){int at=pool[slot];if(!state.lines[at].noiseLoud||state.loudChecked[at])continue;auto glyphs=state.noiseGlyphs(at,slot);bool visible=std::any_of(glyphs.begin(),glyphs.end(),[](const auto& g){return g.opacity>.3f&&g.x+g.halfW>=0&&g.x-g.halfW<=1280&&g.y+g.halfH>=0&&g.y-g.halfH<=720;});if(!visible)continue;
  state.loudElapsed[at]+=std::max(0.f,seconds)*60;if(state.loudElapsed[at]>=30){state.loudChecked[at]=true;if(equipped)out.push_back(at);}
 }return out;
}
inline Break clear(debate::State& debate,int at,float& timer,float initial,int power=1){
 if(at<0||at>=int(debate.lines.size())||debate.lines[at].kind!="noise"||debate.silenced[at])return {};
 if(debate.noiseDamage.size()!=debate.lines.size())debate.noiseDamage.assign(debate.lines.size(),0);
 debate.noiseDamage[at]+=std::max(1,power);
 if(debate.noiseDamage[at]<std::max(1,debate.lines[at].noiseDurability))return {false,0,true};
 const auto group=debate.lines[at].noiseGroup;int reward=debate.lines[at].noiseLoud?0:std::max(0,debate.lines[at].noiseRewardSeconds);debate.silenced[at]=true;
 if(!group.empty())for(int i=0;i<int(debate.lines.size());i++)if(debate.lines[i].kind=="noise"&&debate.lines[i].noiseGroup==group)debate.silenced[i]=true;
 if(initial>0)timer=std::min(initial,timer+reward);else reward=0;return {true,reward};
}
}
