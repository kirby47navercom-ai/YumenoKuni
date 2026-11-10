#include "../Game/Source/GrowthV4.hpp"
#include "../Game/Source/MineOpeningV4.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
int main(){
 using namespace trialv4;
 for(int d=0;d<3;d++)for(auto rating:{Rating::Critical,Rating::Hit,Rating::Miss,Rating::MashSuccess,Rating::MashFailure}){
  Arming base,wild;base.difficulty=wild.difficulty=d;wild.wildAwakening=true;int damage=base.apply(rating),changed=wild.apply(rating);assert(damage==changed&&base.tension==wild.tension&&base.combo==wild.combo&&base.hp==wild.hp);assert(100-wild.opponent==(100-base.opponent)*(rating==Rating::Critical?2:1));
 }
 Arming hold;hold.wildAwakening=true;Note n;n.type=NoteType::Hold;n.held=0;assert(hold.release(n,0,0)==Rating::Critical&&hold.opponent==80);
 AnagramLight plain,intuition;plain.configure(false);intuition.configure(true);plain.reset();intuition.reset();for(int i=0;i<120;i++){plain.tick(true,false);intuition.tick(true,false);}assert(intuition.radius>plain.radius&&intuition.radius<700&&plain.radius<600&&plain.mental==intuition.mental);
 float before=intuition.radius;intuition.tick(false,false);assert(std::abs(intuition.radius-(before-2048.f/60))<.01f);intuition.configure(false);intuition.reset();assert(intuition.radiusMax==600&&intuition.growth==256&&intuition.radius==0);
 for(bool spark:{false,true}){AnagramLight light;light.configure(false,spark);light.reset();int cycles=0;for(int i=0;i<1201;i++){int prior=light.waveMode;light.tick(false,false);if(prior==1&&light.waveMode==2)++cycles;}assert(cycles==(spark?4:2));assert(light.wavePeriod==(spark?5:10));}
 AnagramLight paused;paused.configure(false,true);paused.reset();paused.tick(false,false);float elapsed=paused.waveTime,position=paused.waveOffset;for(int i=0;i<120;i++)paused.tick(false,false,false,true);assert(paused.waveTime==elapsed&&paused.waveOffset==position);
 AnagramLight normal,fast,focus;normal.configure(false);fast.configure(false);focus.configure(false);normal.reset();fast.reset();focus.reset();for(int i=0;i<60;i++){normal.tick(false,false);fast.tick(false,false,true);focus.tick(false,true);}assert(std::abs(normal.waveTime-1)<.001f&&std::abs(fast.waveTime-2)<.001f&&std::abs(focus.waveTime-.5f)<.001f);
 for(int width:{18,20,22})for(unsigned seed=0;seed<97;seed++){
  int total=width*11,count=(total*10+99)/100;auto selected=mineopeningv4::choose(width,11,10,seed);assert(int(selected.size())==count&&std::set<int>(selected.begin(),selected.end()).size()==selected.size());assert(selected==mineopeningv4::choose(width,11,10,seed));
  auto board=mineBoard(width,11,3,seed);Mine mine;mine.reset(width,11,3,board);mineopeningv4::State start;start.start(width,11,10,seed);int removed=0;
  for(int i=0;i<count*3+59;i++){if(start.tick(mine)>=0)++removed;assert(start.active());}assert(removed==count&&mine.time==18000&&mine.hp==10000&&mine.history.empty());start.tick(mine);assert(!start.active());int blank=0;for(int i=0;i<total;i++){if(mine.cells[i]<0)++blank;else assert(mine.cells[i]==board[i]);}assert(blank==count);assert(mine.undo()==Result::None);start.reset();assert(!start.active());
 }
 using namespace growthv4;J contract,skills;std::ifstream("tools/v4_growth_contract.json")>>contract;std::ifstream("data/skills.json")>>skills;growthv4::State s;Init(s,contract,skills);std::map<std::string,int> bonds;int coins=0;
 for(auto actor:{"ai","sho","ken"})for(int i=1;i<=3;i++){auto flag=contract["entries"][std::string(actor)+":"+std::to_string(i)]["completionFlags"][0].get<std::string>();Observe(s,{{flag,true}},bonds,coins);}
 for(auto id:{"v3_intuition_of_god","v3_wild_awakening","v3_roller_strategy"}){assert(s.owned.count(id));assert(Toggle(s,id,99,true).changed);}s.fp=4;assert(Purchase(s,"v3_spark_it",true,true).changed&&s.fp==0);assert(Toggle(s,"v3_spark_it",99,true).changed);growthv4::State restored;Init(restored,contract,skills);assert(Restore(restored,Save(s),99)&&Effect(restored,"spark_it")&&Effect(restored,"roller_strategy")&&Effect(restored,"intuition_of_god")&&Effect(restored,"wild_awakening"));
 std::cout<<"minigame skills PASS:critical-only damage,spotlight table/growth/cost,5/10 cycle incl sweep,fast/focus,3widths x97seeds roller unique cells/timing/no penalty/neighbors,actual acquisition/equip/save\n";
}
