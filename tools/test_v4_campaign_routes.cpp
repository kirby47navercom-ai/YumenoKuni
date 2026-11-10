#include "../Game/Source/TaskGraphV4.hpp"
#include "../Game/Source/SaveV4.hpp"
#include "../Game/Source/GrowthV4.hpp"
#include "../Game/Source/PlayerProgressV4.hpp"
#include "../Game/Source/DifficultyV4.hpp"
#include "../Game/Source/TrialResultV4.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
using J=hb::Json;
std::string hb::Data::GetText(const std::string& path){std::ifstream file("Game/"+path);if(!file)throw std::runtime_error("Missing generated data: "+path);return {std::istreambuf_iterator<char>(file),std::istreambuf_iterator<char>()};}
static bool spotEligible(const storyv4::State& s,const J& spot){
 auto flags=spot.value("requiresFlags",J::object());for(const auto& [key,value]:flags.items())if(!s.flags.contains(key)||s.flags[key]!=value)return false;
 for(const auto& id:spot.value("requiresCards",J::array()))if(!s.evidence.contains(id.get<std::string>()))return false;return true;
}
int main(int argc,char** argv){
 std::string traceTag=argc>1?argv[1]:"";assert(traceTag.empty()||std::all_of(traceTag.begin(),traceTag.end(),[](char c){return c>='0'&&c<='9';}));
 std::set<std::string> allTasks,assignedNodes,visitedAssignments;std::map<std::string,int> types;int total=0,roundtrips=0,maxDepth=0,variants=0;J traces=J::array(),runtimeNodes=J::object();
 try{for(int policy=0;policy<4;policy++){
  storyv4::State state;bool resumed=policy==3;std::string ch=resumed?"3":"P";int menus=0,chapterEnds=0;std::map<std::string,int> visits;J trace=J::array();
  auto chapter=[&](const std::string& id){auto flags=state.flags,evidence=state.evidence;auto reads=state.read;auto log=state.log;state={};state.graph=hb::Data::Get("Assets/Data/v4_story/chapters/"+id+".json");assert(storyv4::valid(state.graph));state.flags=flags;state.evidence=evidence;state.read=reads;state.log=log;state.active=true;assert(storyv4::jump(state,state.graph.at("entry").get<std::string>()));};
  chapter(ch);
  if(resumed){
   std::ifstream f("Game/Saved/ui-checkpoints/normal-ch3-latest/savegames.json");J checkpoint;f>>checkpoint;const auto& items=checkpoint.at("items");
   auto load=[&](const std::string& slot){return J::parse(items.at("hbengine.savegame.json."+slot+".project.004a6371-3a84-4fc3-8b54-31a5001740dd").get<std::string>());};
   auto saved=savev4::unpack(load("yumeno-progress-v4"),load);assert(saved["chapter"]=="3"&&saved["node"]=="v4:input:T3-NS-A11");assert(storyv4::restore(state,state.graph,saved));
   playerprogress::State player;assert(playerprogress::restore(player,saved.value("playerProgress",J())));growthv4::State growth;growthv4::Init(growth,hb::Data::Get("Assets/Data/v4_story/growth.json"),hb::Data::Get("Assets/Data/skills.json"));assert(growthv4::Restore(growth,saved.at("growth"),playerprogress::level(player),3));
   difficultyv4::State difficulty;assert(difficultyv4::restore(difficulty,saved.value("difficulty",J())));resultv4::State results;assert(resultv4::restore(results,saved.value("trialResults",J())));
  }
  for(int steps=0;steps<150000;steps++){
   if(++visits[state.node]>100)throw std::runtime_error("Route cycle: "+state.node);
   const auto& node=storyv4::enter(state);auto kind=node.value("type",std::string());++total;++types[kind];maxDepth=std::max(maxDepth,int(state.stack.size()));
   trace.push_back({{"chapter",ch},{"id",state.node},{"kind",kind}});
   auto textKey=ch+":"+state.node;if(!runtimeNodes.contains(textKey)){J view=J::object();for(const auto* field:{"type","source","text","mono","speaker","actor","options","q","publicRecords","showRecord","rows","title","name"})if(node.contains(field))view[field]=node[field];runtimeNodes[textKey]=std::move(view);}
   if(node.contains("set")){visitedAssignments.insert(state.node);for(const auto& [key,value]:node["set"].items())assert(state.flags.at(key)==value);}
   if(node.contains("sceneVariants")){int matches=0;for(const auto& candidate:node["sceneVariants"]){bool ok=true;for(const auto& condition:candidate["when"]){auto key=condition.at("flag").get<std::string>();if(!state.flags.contains(key)||state.flags[key]!=condition["equals"])ok=false;}matches+=ok;}if(matches!=1)throw std::runtime_error("Scene variant has no unique preceding choice: "+state.node);++variants;}
   if(kind=="task"||steps%2000==0){auto saved=storyv4::save(state);storyv4::State copy;assert(storyv4::restore(copy,state.graph,saved));assert(storyv4::save(copy)==saved);const auto& restored=storyv4::enter(copy);(void)restored;assert(copy.flags==state.flags);++roundtrips;}
   if(kind=="branch"||kind=="call"||kind=="return"){assert(storyv4::route(state));continue;}
   if(kind=="menu"){
    std::vector<int> eligible;for(int i=0;i<int(node["options"].size());i++)if(storyv4::eligible(state,node["options"][i]))eligible.push_back(i);
    if(eligible.empty())throw std::runtime_error("Menu has no eligible choice: "+state.node);
    auto pick=policy==0?eligible.front():policy==1?eligible.back():eligible[(menus++)%eligible.size()];trace.back()["choice"]=pick;trace.back()["visibleOptions"]=eligible;assert(storyv4::choose(state,pick));continue;
   }
   if(kind=="investigate"){
    bool complete=true;for(const auto& id:node.value("requiredSpotIds",J::array()))if(!state.flags.value("spot:"+id.get<std::string>()+":complete",false))complete=false;
    for(const auto& id:node.value("requiredCards",J::array()))if(!state.evidence.contains(id.get<std::string>()))complete=false;
    if(complete&&node.contains("next")){assert(storyv4::jump(state,node["next"].get<std::string>()));continue;}
    std::vector<J> spots;for(const auto& spot:node["spots"])if(spotEligible(state,spot)&&!state.flags.value("spot:"+spot.at("id").get<std::string>()+":complete",false))spots.push_back(spot);
    if(spots.empty())throw std::runtime_error("Investigation has no eligible unfinished target: "+state.node);
    auto spot=policy==1?spots.back():spots.front();auto flags=spot.value("onReturnSet",J::object());flags["spot:"+spot.at("id").get<std::string>()+":complete"]=true;if(spot.contains("completionFlag"))flags[spot["completionFlag"].get<std::string>()]=true;
    state.stack.push_back({state.node,flags});assert(storyv4::jump(state,spot.at("entry").get<std::string>()));continue;
   }
   if(kind=="task"){
    auto id=node.at("taskId").get<std::string>();const auto& bundle=storyv4::bucketData("Assets/Data/v4_story/native_tasks/",storyv4::bucket(id,64)).at("tasks").at(id);auto stage=taskv4::prepare(bundle,state.evidence);trace.back()["preparedStage"]=stage;allTasks.insert(id);
    std::string judgment="refute";auto outcomes=node.value("outcomes",bundle.value("outcomes",J::object()));if(!outcomes.empty()){auto it=policy==1?std::prev(outcomes.end()):outcomes.begin();judgment=it.value().at("judgment").get<std::string>();}
    // Explicit structural success injection; no input, score, duration or gameplay claim.
    auto route=taskv4::success(node,bundle,judgment);trace.back()["judgment"]=judgment;trace.back()["taskId"]=id;storyv4::setFlags(state,route.sets);assert(storyv4::jump(state,route.target));continue;
   }
   if(kind=="end"){
    assert(state.stack.empty());++chapterEnds;
    if(node.value("chapterComplete",false)&&node.contains("nextChapter")){ch=node["nextChapter"].get<std::string>();chapter(ch);continue;}
    assert(node.value("campaignNarrativeEnd",false)&&ch=="6"&&chapterEnds==(resumed?4:7));break;
   }
   if(kind=="gate")throw std::runtime_error("Reached unresolved authored gate: "+state.node);
   if(kind=="evidence"){auto id=node.at("evidenceId").get<std::string>();if(node.value("revision",false))assert(state.evidence.contains(id));state.evidence[id]={{"name",node.value("name",id)},{"text",node.value("text",std::string())}};}
   else if(kind=="say"){state.read.insert(state.node);state.log.push_back({{"id",state.node},{"text",node.at("text")}});if(state.log.size()>2000)state.log.erase(state.log.begin());}
   else assert(kind=="stage"||kind=="document");
   assert(storyv4::jump(state,node.at("next").get<std::string>()));
   if(steps==149999)throw std::runtime_error("Campaign step limit");
  }
  assert(chapterEnds==(resumed?4:7));
  traces.push_back({{"policy",policy},{"normalCheckpointResume",resumed},{"trace",trace}});
 }}catch(const std::exception& error){std::cerr<<error.what()<<"\n";return 1;}
 // Every actual assignment is checked independently, including unselected branches.
 for(const auto& ch:{"P","1","2","3","4","5","6"}){std::ifstream f(std::string("data/v4_story/chapters/")+ch+".json");J full;f>>full;
  for(const auto& [id,node]:full["nodes"].items())if(node.contains("set")){
   assignedNodes.insert(id);storyv4::State s;s.graph=hb::Data::Get(std::string("Assets/Data/v4_story/chapters/")+ch+".json");assert(storyv4::jump(s,id));for(const auto& [key,value]:node["set"].items())s.flags[key]=value==true?J(false):J("before");
   storyv4::enter(s);for(const auto& [key,value]:node["set"].items())assert(s.flags[key]==value);auto flags=s.flags;storyv4::enter(s);assert(s.flags==flags);
   storyv4::State restored;assert(storyv4::restore(restored,s.graph,storyv4::save(s)));storyv4::enter(restored);assert(restored.flags==flags);
  }
 }
 std::ofstream("Game/Saved/campaign-route-traces"+(traceTag.empty()?std::string():"-"+traceTag)+".json")<<J{{"status","PASS"},{"nativePlayerLaunched",false},{"taskSuccessInjectedForStructureOnly",true},{"durationCertified",false},{"policies",traces},{"runtimeNodes",runtimeNodes}}.dump()<<"\n";
 std::cout<<J{{"status","PASS"},{"fullStartPolicies",3},{"chaptersPerFullStartPolicy",7},{"normalCheckpointResumeChapters",4},{"normalCheckpointGrowthDifficultyResultsRestored",true},{"visitedNodes",total},{"uniqueTasks",allTasks.size()},{"types",types},{"saveRoundtrips",roundtrips},{"maxCallDepth",maxDepth},{"sceneVariants",variants},{"authoredAssignmentNodes",assignedNodes.size()},{"visitedAssignmentNodes",visitedAssignments.size()},{"nativePlayerLaunched",false},{"taskSuccessInjectedForStructureOnly",true},{"durationCertified",false}}.dump()<<"\n";
}
