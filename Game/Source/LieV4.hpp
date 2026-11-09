#pragma once
#include <algorithm>
#include <limits>
namespace liev4 {
enum class Phase {Idle,Charge,Convert,Hold};
enum class Event {None,NormalShot,Transformed,LieShot};
inline bool isShot(Event e){return e==Event::NormalShot||e==Event::LieShot;}
struct State {
 Phase phase=Phase::Idle;int charge=0,pending=0;bool transformed=false;
 void cancel(){phase=Phase::Idle;charge=pending=0;transformed=false;}
 // One admitted own60Hz tick. State19 conversion has its own free tick,
 // following60 charge ticks; only state1a accumulates, including release.
 Event tick(bool held,bool whiteLie,bool permitted=true){
  if(phase==Phase::Idle){if(!held)return Event::None;phase=Phase::Charge;}
  if(phase==Phase::Charge){if(!held){cancel();return Event::NormalShot;}if(!permitted){charge=0;return Event::None;}if(++charge>=60)phase=Phase::Convert;return Event::None;}
  if(phase==Phase::Convert){phase=Phase::Hold;transformed=true;pending=0;return Event::Transformed;}
  int step=whiteLie?3:7;pending=pending>std::numeric_limits<int>::max()-step?std::numeric_limits<int>::max():pending+step;
  return held?Event::None:Event::LieShot;
 }
 // Physical edges are immediate; only sustained charge/cost uses the 60Hz clock.
 Event advance(float delta,bool held,bool whiteLie,bool permitted,float& fraction){
  fraction+=std::max(0.f,delta)*60;int ticks=int(fraction+1e-5f);fraction=std::max(0.f,fraction-ticks);
  if(held&&phase==Phase::Idle)phase=Phase::Charge;
  if(!held&&(phase==Phase::Charge||phase==Phase::Hold))return tick(false,whiteLie,permitted);
  Event event=Event::None;
  for(int i=0;i<ticks;i++){auto next=tick(held,whiteLie,permitted);if(next!=Event::None)event=next;if(next==Event::NormalShot||next==Event::LieShot)break;}
  return event;
 }
 int settle(bool correct){int cost=correct?0:pending;cancel();return cost;}
 int settleHp(int hp,bool correct){int cost=settle(correct);return cost>=hp?0:std::max(0,hp-cost);}
};
}
