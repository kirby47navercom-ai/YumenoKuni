#include "../Game/Source/GrowthV4.hpp"
#include <fstream>
#include <cassert>
#include <iostream>
int main(){using namespace growthv4;J skills;std::ifstream("data/skills.json")>>skills;State s;s.skills=skills.at("items");std::vector<std::string> ids,effects{"missing"};for(const auto& r:s.skills){ids.push_back(r.at("id"));effects.push_back(r.value("effect",std::string()));}int cases=0;
 for(size_t seed=0;seed<32;seed++){s.equipped.clear();s.owned.clear();for(size_t i=0;i<ids.size();i++){if((i+seed)%3==0)s.equipped.insert(ids[i]);if((i+seed)%5!=0)s.owned.insert(ids[i]);}for(const auto& effect:effects){bool expected=false;for(const auto& row:Equipped(s))if(row.value("effect",std::string())==effect)expected=true;assert(Effect(s,effect)==expected);++cases;}}
 std::cout<<"PASS: "<<cases<<" skill effect comparisons including owned/equipped mismatches and unknown effect\n";}
