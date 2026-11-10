#include "../Game/Source/EvidenceHintV4.hpp"
#include "../Game/Source/GrowthV4.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
using J=hb::Json;
int main(){
 J task={{"stage",{{"kind","nonstop"}}},{"debate",{{"lines",J::array({{{"kind","weak"},{"weak",{{"answer","first"}}}},{{"kind","weak"},{"weak",{{"answer","last"}}}},{{"kind","weak"},{"weak",{{"answer","converted"},{"lie",true}}}},{{"kind","agree"},{"agree","alternate"}},{{"kind","plain"},{"weak",{{"answer","not-a-primary"}}}}})}}}};
 std::set<std::string> owned{"first","last","converted","alternate","not-a-primary"};assert(evidencehintv4::primary(task,owned)=="last");owned.erase("last");assert(evidencehintv4::primary(task,owned).empty());owned.insert("last");assert(evidencehintv4::primary(J(),owned).empty());auto other=task;other["stage"]["kind"]="bullet";assert(evidencehintv4::primary(other,owned).empty());
 debate::State s;s.lines={{"a","first","weak"},{"b","second","plain"},{"n","noise","noise"}};s.broken.assign(3,false);s.silenced.assign(3,false);s.restartRows();int hearts=s.hearts;float focus=s.focus;
 assert(!evidencehintv4::visible("last","last",true,true,s));s.next();assert(s.index==1&&s.passes==0);s.next();assert(s.index==0&&s.passes==1&&s.hearts==hearts&&s.focus==focus);
 assert(evidencehintv4::visible("last","last",true,true,s));assert(!evidencehintv4::visible("last","first",true,true,s));assert(!evidencehintv4::visible("last","last",false,true,s));assert(!evidencehintv4::visible("last","last",true,false,s));assert(!evidencehintv4::visible("","",true,true,s));
 for(int hz:{30,60,120}){s.restartRows();int frames=0;while(!s.passes){s.tick(1.f/hz);assert(++frames<hz*30);}assert(s.passes==1);s.restartRows();assert((!evidencehintv4::ready(s)&&s.lanePasses==std::array<int,3>{0,0,0}));}
 s.lines={{"a","one","weak"},{"a","two","plain"},{"b","one","weak"},{"b","two","plain"},{"c","one","weak"},{"c","two","plain"}};s.lanes={{0,1},{2,3},{4,5}};s.restartRows();
 s.advanceLane(0);s.advanceLane(0);assert(!evidencehintv4::ready(s));s.advanceLane(1);s.advanceLane(1);assert(!evidencehintv4::ready(s));s.advanceLane(2);s.advanceLane(2);assert(evidencehintv4::ready(s));s.restartRows();assert(!evidencehintv4::ready(s));
 for(int hz:{30,60,120}){s.restartRows();int frames=0;while(!evidencehintv4::ready(s)){s.tick(1.f/hz);assert(++frames<hz*30);}assert((s.lanePasses==std::array<int,3>{1,1,1}));}
 for(int i=0;i<200;i++){float a=evidencehintv4::opacity(i*.037f);assert(a>=.43999f&&a<=1.00001f);}assert(evidencehintv4::opacity(0)==1);
 J all;std::ifstream("data/v4_story/native_tasks.json")>>all;int contexts=0,applicable=0;
 for(const auto& [id,bundle]:all["tasks"].items()){auto kind=bundle["stage"].value("kind",std::string());if(kind!="nonstop"&&kind!="panic")continue;++contexts;std::set<std::string> actualOwned;for(const auto& e:bundle.value("requiresEvidence",J::array()))actualOwned.insert(e.get<std::string>());
  auto hint=evidencehintv4::primary(bundle,actualOwned);if(hint.empty())continue;++applicable;assert(actualOwned.count(hint));bool actualCandidate=false;for(const auto& option:bundle["stage"].value("options",J::array()))if(option.value("id",std::string())==hint)actualCandidate=true;assert(actualCandidate);
 }
 assert(contexts==89&&applicable>0);
 J contract,skills;std::ifstream("tools/v4_growth_contract.json")>>contract;std::ifstream("data/skills.json")>>skills;growthv4::State growth;growthv4::Init(growth,contract,skills);auto row=growthv4::Skill(growth,"v3_abracadabra");assert(row&&row->at("sourceSaveNo")==12&&row->at("sp")==24&&row->at("fp")==0&&row->at("sourceGroup")==-1&&row->at("sourceDelta")==3);assert(growthv4::Purchase(growth,"v3_abracadabra",true,true).reason=="event-acquisition-only");std::map<std::string,int> bonds;int coins=0;
 for(int e=1;e<=3;e++){auto flag=contract["entries"]["kaede:"+std::to_string(e)]["completionFlags"][0].get<std::string>();growthv4::Observe(growth,{{flag,true}},bonds,coins);assert(bool(growth.owned.count("v3_abracadabra"))==(e==3));}
 assert(!growthv4::Toggle(growth,"v3_abracadabra",23,true).changed);assert(growthv4::Toggle(growth,"v3_abracadabra",24,true).changed);growthv4::State copy;growthv4::Init(copy,contract,skills);assert(growthv4::Restore(copy,growthv4::Save(growth),24)&&copy.equipped.count("v3_abracadabra"));
 std::cout<<J{{"status","PASS"},{"nonstopPanicContexts",contexts},{"ownedNormalPrimaryContexts",applicable},{"lateHintOnly",true},{"allPanicLanesRequired",true},{"fps",{30,60,120}},{"retryReset",true},{"sourceCostAcquisitionSave",true},{"playerLaunch",false}}.dump()<<"\n";
}
