#include "../Game/Source/ShotRecoveryV4.hpp"
#include "../Game/Source/GrowthV4.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
int main(){
 using namespace shotv4;
 for(bool laser:{false,true})for(bool trigger:{false,true}){
  State s;s.fire(laser,trigger);int flight=laser?7:14;
  for(int i=0;i<flight;i++){assert(!s.ready());s.advance(1.f/60,false);}
  assert(s.phase==Phase::Recovery);int wait=trigger?1:60;
  for(int i=0;i<wait-1;i++){s.advance(1.f/60,false);assert(!s.ready());}
  s.advance(1.f/60,false);assert(s.ready());
  s.fire(laser,trigger);s.wrong();for(int i=0;i<59;i++)s.tick(false);assert(!s.ready());s.tick(false);assert(s.ready());
  s.fire(laser,trigger);for(int i=0;i<flight+wait;i++)s.tick(true);assert(s.phase==Phase::Release);s.tick(true);assert(!s.ready());s.tick(false);assert(s.ready());
  s.fire(laser,trigger);s.advance(0,true);assert(s.frames==flight);s.reset();assert(s.ready()&&!s.laser);
 }
 State a,b;a.fire(false,false);b.fire(false,false);for(int i=0;i<74;i++)a.advance(1.f/60,false);for(int i=0;i<148;i++)b.advance(1.f/120,false);assert(a.ready()&&b.ready());
 growthv4::J contract,skills;std::ifstream("tools/v4_growth_contract.json")>>contract;std::ifstream("data/skills.json")>>skills;growthv4::State s;growthv4::Init(s,contract,skills);std::map<std::string,int> bonds;int coins=0;
 for(int i=1;i<=3;i++){auto flag=contract["entries"]["satsuki:"+std::to_string(i)]["completionFlags"][0].get<std::string>();growthv4::Observe(s,{{flag,true}},bonds,coins);}
 assert(s.owned.count("v3_laser_beam"));s.fp=8;assert(growthv4::Purchase(s,"v3_triger_happy",true,true).changed&&s.fp==0);assert(growthv4::Toggle(s,"v3_laser_beam",16,true).changed&&growthv4::Toggle(s,"v3_triger_happy",16,true).changed);
 growthv4::State restored;growthv4::Init(restored,contract,skills);assert(growthv4::Restore(restored,growthv4::Save(s),16)&&growthv4::Effect(restored,"laser_beam")&&growthv4::Effect(restored,"triger_happy"));
 std::cout<<"shot skills PASS:flight14/7 then60/0 recovery,independent wrong60,release rearm,pause/reset,60/120Hz,actual acquisition/equip/save\n";
}
