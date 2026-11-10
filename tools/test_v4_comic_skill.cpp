#include "../Game/Source/ComicProgressV4.hpp"
#include "../Game/Source/GrowthV4.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
int main(){
 comicprogressv4::State s;for(unsigned seed=0;seed<97;seed++)for(int total:{6,8}){
  s.reset(total,{0},0,seed);assert(s.automatic.empty()&&!s.filled(0,0));s.reset(total,{0},20,seed);assert(s.automatic==std::set<int>{0});assert(s.filled(0,0)&&!s.filled(1,0));assert(s.consumeResponse(0)&&!s.consumeResponse(0)&&!s.consumeResponse(1));assert(s.filled(1,2));
 }
 // Selection respects actual eligible indices, never a guessed firstN prefix.
 // A later hole can be solved first; the unfilled earlier holes stay empty.
 s.reset(6,{},0,1);assert(s.place(5,6));assert(s.completed()==1&&s.filled(5)&&!s.filled(0)&&s.next(6)==0);assert(!s.place(5,6)&&!s.place(-1,6)&&!s.place(6,6));
 for(int i:{2,0,4,1,3})assert(s.place(i,6));assert(s.completed()==6&&s.next(6)==-1);
 s.reset(8,{3},20,1);assert(!s.place(3,8)&&s.completed()==1);assert(s.place(7,8)&&s.completed()==2&&s.next(8)==0);
 s.reset(8,{3,6},20,1);assert(s.automatic.size()==1&&!s.automatic.count(0));s.reset(8,{},20,1);assert(s.automatic.empty());bool bad=false;try{s.reset(8,{0,8},20,1);}catch(const std::invalid_argument&){bad=true;}assert(bad);
 growthv4::J tasks;std::ifstream("data/v4_story/native_tasks.json")>>tasks;int chapters=0,slots=0,spoken=0;
 for(const auto& [id,bundle]:tasks.at("tasks").items())if(bundle.at("stage").value("kind",std::string())=="climax"){
  const auto& rows=bundle["stage"]["slots"];s.reset(int(rows.size()),{0},20,1);assert(s.automatic==std::set<int>{0});int prefix=0;std::set<int> heard;
  while(prefix<int(rows.size())){const auto& slot=rows[prefix];int correct=0;for(const auto& option:slot["options"])if(option["id"]==slot["answer"]){correct++;assert(!option.at("response").empty());if(s.automatic.count(prefix))assert(s.consumeResponse(prefix)&&!s.consumeResponse(prefix));assert(heard.insert(prefix).second);for(const auto& line:option["response"])if(line.value("type",std::string())=="say")spoken++;}assert(correct==1);prefix++;}assert(heard.size()==rows.size());chapters++;slots+=int(rows.size());
 }
 assert(chapters==6&&slots==38&&spoken>0);
 growthv4::J contract,skills;std::ifstream("tools/v4_growth_contract.json")>>contract;std::ifstream("data/skills.json")>>skills;growthv4::State learned;growthv4::Init(learned,contract,skills);std::map<std::string,int> bonds;int coins=0;
 assert(growthv4::Purchase(learned,"v3_two_dimensional_love",true,true).reason=="event-acquisition-only");for(int episode=1;episode<=3;episode++){auto flag=contract["entries"]["rei:"+std::to_string(episode)]["completionFlags"][0].get<std::string>();growthv4::Observe(learned,{{flag,true}},bonds,coins);}assert(learned.owned.count("v3_two_dimensional_love")&&growthv4::Toggle(learned,"v3_two_dimensional_love",6,true).changed);growthv4::State copy;growthv4::Init(copy,contract,skills);assert(growthv4::Restore(copy,growthv4::Save(learned),6)&&growthv4::Effect(copy,"two_dimensional_love"));
 std::cout<<"climax skill PASS:6actual tasks/38slots, eligible-only20%, no unearned later panels, actual correct response once/in order, acquisition/equip/save\n";
}
