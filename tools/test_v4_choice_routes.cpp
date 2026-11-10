#include "../Game/Source/TaskGraphV4.hpp"
#include <deque>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
using J=hb::Json;
std::string hb::Data::GetText(const std::string& path){std::ifstream f("Game/"+path);if(!f)throw std::runtime_error(path);return {std::istreambuf_iterator<char>(f),{}};}
struct Work{std::string chapter,kind,target;int option=-1;J snapshot;};
static bool eligibleSpot(const storyv4::State& s,const J& spot){
 const auto flags=spot.value("requiresFlags",J::object());for(const auto& [k,v]:flags.items())if(!s.flags.contains(k)||s.flags[k]!=v)return false;
 for(const auto& id:spot.value("requiresCards",J::array()))if(!s.evidence.contains(id.get<std::string>()))return false;return true;
}
int main(int argc,char** argv){
 std::string output=argc>1?argv[1]:"Game/Saved";if(output.rfind("Game/Saved",0)!=0||output.find("..")!=std::string::npos||output.find(':')!=std::string::npos)throw std::runtime_error("Owned output folder required");std::filesystem::create_directories(output);std::ofstream menuFixtures,taskFixtures;if(argc>1){menuFixtures.open(output+"/menu-fixtures.jsonl");taskFixtures.open(output+"/task-fixtures.jsonl");}std::set<std::string> exportedTasks;
 std::map<std::string,J> graphs;for(auto ch:{"P","1","2","3","4","5","6"})graphs[ch]=hb::Data::Get(std::string("Assets/Data/v4_story/chapters/")+ch+".json");
 std::deque<Work> queue;queue.push_back({"P","start","",-1,J()});std::set<std::string> queued,covered,visited,branchTargets;J runs=J::array(),errors=J::array();long long stepsTotal=0;
 auto id=[](const std::string& ch,const std::string& node,const std::string& kind,const std::string& to){return ch+"|"+node+"|"+kind+"|"+to;};
 auto enqueue=[&](const storyv4::State& s,const std::string& kind,const std::string& target,int option){auto key=id(s.graph.at("chapter"),s.node,kind,target);if(covered.count(key)||!queued.insert(key).second)return;auto snapshot=storyv4::save(s);queue.push_back({s.graph.at("chapter"),kind,target,option,snapshot});if(menuFixtures&&kind=="menu"){auto next=s;if(!storyv4::choose(next,option))throw std::runtime_error("Fixture option must be eligible");J trail=J::array();for(int i=0;i<100;i++){trail.push_back(next.node);const auto& n=storyv4::enter(next);auto t=n.value("type",std::string());if(t=="branch"||t=="call"||t=="return"){if(!storyv4::route(next))throw std::runtime_error(next.blocked);continue;}if(t=="stage"&&!n.value("showRecord",false)){if(!storyv4::jump(next,n.at("next")))throw std::runtime_error(next.blocked);continue;}break;}J eligible=J::array();const auto& n=s.current();for(int i=0;i<int(n["options"].size());i++)if(storyv4::eligible(s,n["options"][i]))eligible.push_back(i);menuFixtures<<J{{"chapter",s.graph.at("chapter")},{"node",s.node},{"option",option},{"eligible",eligible},{"trail",trail},{"sets",n["options"][option].value("set",J::object())},{"state",snapshot}}.dump()<<"\n";}};
 while(!queue.empty()){
  auto work=std::move(queue.front());queue.pop_front();if(work.kind!="start"&&covered.count(id(work.chapter,work.snapshot.at("node"),work.kind,work.target)))continue;storyv4::State s;std::string ch=work.chapter;bool forced=work.kind!="start",ended=false;int steps=0;std::map<std::string,int> repeats;
  try{
   if(work.kind=="start"){s.graph=graphs[ch];s.active=true;if(!storyv4::jump(s,s.graph.at("entry")))throw std::runtime_error(s.blocked);}
   else if(!storyv4::restore(s,graphs[ch],work.snapshot))throw std::runtime_error("Fork snapshot could not restore");
   for(;steps<150000;steps++){
    if(++repeats[s.node]>100)throw std::runtime_error("Route repeats: "+s.node);++stepsTotal;visited.insert(ch+"|"+s.node);const auto& n=storyv4::enter(s);auto kind=n.value("type",std::string());
    if(kind=="branch"||kind=="call"||kind=="return"){auto before=s.node;if(!storyv4::route(s))throw std::runtime_error(s.blocked);if(kind=="branch")branchTargets.insert(ch+"|"+before+"|"+s.node);continue;}
    if(kind=="menu"){
     std::vector<int> options;for(int i=0;i<int(n["options"].size());i++)if(storyv4::eligible(s,n["options"][i])){options.push_back(i);enqueue(s,"menu",std::to_string(i),i);}if(options.empty())throw std::runtime_error("No eligible menu option: "+s.node);
     int pick=forced?work.option:options.front();if(forced&&work.kind!="menu")throw std::runtime_error("Forced decision kind differs");forced=false;
     covered.insert(id(ch,s.node,"menu",std::to_string(pick)));if(!storyv4::choose(s,pick))throw std::runtime_error("Ineligible selected option");continue;
    }
    if(kind=="investigate"){
     std::vector<int> available;for(int i=0;i<int(n["spots"].size());i++){const auto& spot=n["spots"][i];if(eligibleSpot(s,spot)&&!s.flags.value("spot:"+spot.at("id").get<std::string>()+":complete",false)){available.push_back(i);enqueue(s,"spot",std::to_string(i),i);}}
     bool complete=true;for(const auto& spot:n.value("requiredSpotIds",J::array()))if(!s.flags.value("spot:"+spot.get<std::string>()+":complete",false))complete=false;for(const auto& card:n.value("requiredCards",J::array()))if(!s.evidence.contains(card.get<std::string>()))complete=false;
     if(!forced&&complete&&n.contains("next")){if(!storyv4::jump(s,n["next"]))throw std::runtime_error(s.blocked);continue;}
     if(available.empty())throw std::runtime_error("Unfinished investigation has no target: "+s.node);int pick=forced?work.option:available.front();if(forced&&work.kind!="spot")throw std::runtime_error("Forced spot kind differs");forced=false;
     if(std::find(available.begin(),available.end(),pick)==available.end())throw std::runtime_error("Unavailable investigation fork");covered.insert(id(ch,s.node,"spot",std::to_string(pick)));const auto& spot=n["spots"][pick];auto flags=spot.value("onReturnSet",J::object());flags["spot:"+spot.at("id").get<std::string>()+":complete"]=true;if(spot.contains("completionFlag"))flags[spot["completionFlag"].get<std::string>()]=true;s.stack.push_back({s.node,flags});if(!storyv4::jump(s,spot.at("entry")))throw std::runtime_error(s.blocked);continue;
    }
    if(kind=="task"){
     auto task=n.at("taskId").get<std::string>();if(taskFixtures&&exportedTasks.insert(task).second)taskFixtures<<J{{"taskId",task},{"state",storyv4::save(s)}}.dump()<<"\n";const auto& bundle=storyv4::bucketData("Assets/Data/v4_story/native_tasks/",storyv4::bucket(task,64)).at("tasks").at(task);taskv4::prepare(bundle,s.evidence);auto outcomes=n.value("outcomes",bundle.value("outcomes",J::object()));std::string judgment="refute";
     if(!outcomes.empty()){for(const auto& [key,outcome]:outcomes.items())enqueue(s,"task",outcome.at("judgment"),-1);judgment=outcomes.begin().value().at("judgment");}
     if(forced){if(work.kind!="task")throw std::runtime_error("Forced task kind differs");judgment=work.target;forced=false;}
     covered.insert(id(ch,s.node,"task",judgment));auto route=taskv4::success(n,bundle,judgment);storyv4::setFlags(s,route.sets);if(!storyv4::jump(s,route.target))throw std::runtime_error(s.blocked);continue;
    }
    if(forced)throw std::runtime_error("Forced decision did not start at its saved input");
    if(kind=="end"){
     if(!s.stack.empty())throw std::runtime_error("Ending retains a caller");
     if(n.value("chapterComplete",false)&&n.contains("nextChapter")){ch=n.at("nextChapter");auto flags=s.flags,evidence=s.evidence;s={};s.graph=graphs[ch];s.flags=std::move(flags);s.evidence=std::move(evidence);s.active=true;if(!storyv4::jump(s,s.graph.at("entry")))throw std::runtime_error(s.blocked);continue;}
     if(!n.value("campaignNarrativeEnd",false)||ch!="6")throw std::runtime_error("Not a complete campaign ending");ended=true;break;
    }
    if(kind=="evidence"){auto card=n.at("evidenceId").get<std::string>();if(n.value("revision",false)&&!s.evidence.contains(card))throw std::runtime_error("Unacquired evidence revision");s.evidence[card]={{"name",n.value("name",card)},{"text",n.value("text",std::string())}};}
    else if(kind!="say"&&kind!="stage"&&kind!="document")throw std::runtime_error("Unresolved node kind: "+kind+" at "+s.node);
    if(!storyv4::jump(s,n.at("next")))throw std::runtime_error(s.blocked);
   }
   if(!ended)throw std::runtime_error("Campaign fork exceeded step bound");runs.push_back({{"startChapter",work.chapter},{"startNode",work.snapshot.is_object()?work.snapshot.value("node",std::string()):"chapter-entry"},{"kind",work.kind},{"option",work.target},{"steps",steps},{"end",s.node}});
  }catch(const std::exception& e){errors.push_back({{"chapter",ch},{"node",s.node},{"startKind",work.kind},{"option",work.target},{"error",e.what()}});}
  if((runs.size()+errors.size())%50==0)std::cout<<J{{"runs",runs.size()},{"queued",queue.size()},{"coveredEdges",covered.size()},{"errors",errors.size()}}.dump()<<std::endl;
 }
 J missing=J::array();for(const auto& [ch,g]:graphs){std::ifstream f("data/v4_story/chapters/"+ch+".json");auto full=J::parse(f);for(const auto& [node,n]:full.at("nodes").items())if(n.value("type",std::string())=="menu")for(int i=0;i<int(n["options"].size());i++)if(!covered.count(id(ch,node,"menu",std::to_string(i))))missing.push_back({{"chapter",ch},{"node",node},{"index",i},{"requires",n["options"][i].value("requires",J::object())},{"source",n.value("source",J::object())}});}
 J report{{"status",errors.empty()&&missing.empty()?"PASS":"INCOMPLETE"},{"scope","Reachable saved-state forks of every discovered eligible authored menu, investigation target and successful task judgment, each continued to a real authored ending. Structural C++ runner with injected task success, no native input, human duration or all-history-combination claim."},{"taskSuccessInjectedForStructureOnly",true},{"nativePlayerLaunched",false},{"runs",runs},{"coveredEdges",covered.size()},{"visitedNodes",visited.size()},{"steps",stepsTotal},{"uncoveredMenuOptions",missing},{"errors",errors}};
 std::ofstream(output+"/choice-route-coverage.json")<<report.dump(2)<<"\n";std::cout<<J{{"status",report["status"]},{"runs",runs.size()},{"missingOptions",missing.size()},{"errors",errors.size()}}.dump()<<std::endl;return errors.empty()&&missing.empty()?0:1;
}
