#include "../Game/Source/LieV4.hpp"
#include "../Game/Source/GrowthV4.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
int main(){
 using namespace liev4;State plain,white;
 for(int i=0;i<59;i++)assert(plain.tick(true,false)==Event::None);assert(plain.charge==59&&plain.pending==0&&!plain.transformed);
 assert(plain.tick(true,false)==Event::None&&plain.phase==Phase::Convert&&plain.pending==0);assert(plain.tick(true,false)==Event::Transformed&&plain.pending==0);assert(plain.tick(true,false)==Event::None&&plain.pending==7);
 for(int i=0;i<61;i++)white.tick(true,true);assert(white.transformed&&white.pending==0);assert(white.tick(true,true)==Event::None&&white.pending==3);
 for(int i=0;i<8;i++){plain.tick(true,false);white.tick(true,true);}assert(plain.tick(false,false)==Event::LieShot&&plain.pending==70);assert(white.tick(false,true)==Event::LieShot&&white.pending==30);
 assert(plain.settleHp(100,false)==30&&plain.settleHp(30,false)==30);assert(white.settleHp(100,false)==70);
 State success;for(int i=0;i<71;i++)success.tick(true,false);assert(success.pending==70&&success.settleHp(100,true)==100&&success.pending==0);
 State low;for(int i=0;i<61;i++)low.tick(true,true);low.tick(false,true);assert(low.settleHp(1,false)==0);assert(low.settleHp(0,false)==0);
 State early;for(int i=0;i<59;i++)early.tick(true,false);assert(early.tick(false,false)==Event::NormalShot&&early.pending==0&&!early.transformed);
 State permission;for(int i=0;i<300;i++)permission.tick(true,true,false);assert(permission.charge==0&&!permission.transformed&&permission.pending==0&&permission.tick(false,true,false)==Event::NormalShot);
 // A one-render-frame press/release works above and below the 60Hz charge clock.
 for(float hz:{30.f,60.f,120.f,240.f}){State quick;float fraction=0;assert(quick.advance(1/hz,true,false,true,fraction)==Event::None);assert(quick.advance(1/hz,false,false,true,fraction)==Event::NormalShot);assert(quick.phase==Phase::Idle);assert(quick.advance(1/hz,false,false,true,fraction)==Event::None);}
 {State quick;float fraction=0;quick.advance(.001f,true,false,true,fraction);assert(quick.advance(.001f,false,false,true,fraction)==Event::NormalShot);}
 for(float hz:{30.f,60.f,120.f,240.f}){State held;float fraction=0;for(int i=0;i<int(hz*1.1f);++i)held.advance(1/hz,true,false,true,fraction);assert(held.transformed);assert(held.advance(.001f,false,false,true,fraction)==Event::LieShot);}
 // Menu/timeout cancellation discards unpaid debt, without debit or refund.
 for(int i=0;i<71;i++)early.tick(true,false);assert(early.pending==70);early.cancel();assert(early.settleHp(100,false)==100);
 growthv4::J contract,skills;std::ifstream("tools/v4_growth_contract.json")>>contract;std::ifstream("data/skills.json")>>skills;growthv4::State learned;growthv4::Init(learned,contract,skills);std::map<std::string,int> bonds;int coins=0;
 assert(growthv4::Purchase(learned,"v3_white_lie",true,true).reason=="event-acquisition-only");for(int episode=1;episode<=3;episode++){auto flag=contract["entries"]["haruka:"+std::to_string(episode)]["completionFlags"][0].get<std::string>();growthv4::Observe(learned,{{flag,true}},bonds,coins);}assert(learned.owned.count("v3_white_lie")&&!learned.equipped.count("v3_white_lie"));assert(!growthv4::Toggle(learned,"v3_white_lie",5,true).changed&&growthv4::Toggle(learned,"v3_white_lie",6,true).changed);
 growthv4::State restored;growthv4::Init(restored,contract,skills);assert(growthv4::Restore(restored,growthv4::Save(learned),6)&&growthv4::Effect(restored,"white_lie"));State active;for(int i=0;i<71;i++)active.tick(true,growthv4::Effect(restored,"white_lie"));assert(active.pending==30);
 std::cout<<"lie PASS:60+1 free setup,7/3 per admitted/release tick, failed/success/timeout/cancel, exact HP/idempotence/one-HP, permission, actual acquisition/equip/save\n";
}
