#include <HBEngine/Session.hpp>
#include "../Game/Source/Yumeno.cpp"
#include <fstream>
#include <iostream>
#include <cassert>
using J=hb::Json;
static J read(const std::string& path){std::ifstream f(path);if(!f)throw std::runtime_error(path);return J::parse(f);}
int main(){
 hb::bridgeQuery=[](const J& p)->J{auto key=p.at("key").get<std::string>();J value="";
  if(key=="dataJsonRead")value=read("Game/"+p.at("args").at("path").get<std::string>()).dump();
  else if(key=="saveJsonWrite"||key=="saveJsonDelete")value=true;
  else if(key!="saveJsonRead")throw std::runtime_error("Unexpected query: "+key);
  return {{"ok",true},{"value",value}};
 };
 hb::bridgeSync(read("Game/Assets/Scenes/Main.hbscene.json").at("objects"));
 hb::bridgeActors["Driver"]=std::make_unique<Yumeno>();auto* game=static_cast<Yumeno*>(hb::bridgeActors.at("Driver").get());hb::bridgeActorIds[game]="Driver";
 auto clear=[](){hb::bridgeOperations=J::array();hb::bridgeOperationStart=0;hb::bridgeInput={{"keys",J::object()}};};
 clear();game->Update(1.f/60);J cases=J::array();int failures=0;
 const auto tasks=read("data/v4_story/native_tasks.json").at("tasks");
 for(const auto& [id,bundle]:tasks.items()){
  const auto kind=bundle.at("stage").value("kind",std::string());if(kind!="reasoning"&&kind!="climax"&&kind!="choice"&&kind!="bullet"&&kind!="person"&&kind!="spot"&&kind!="vote")continue;
  // Split fixture construction just as production restore yields before entry.
  clear();game->v4Start(id.substr(1,1));assert(game->lastError.empty());clear();
  const auto catalog=game->v4.graph.value("evidenceCatalog",J::object());for(const auto& [card,e]:catalog.items())game->v4.evidence[card]={{"name",e.value("name",card)},{"text",e.value("text",std::string())}};
  for(const auto& card:bundle.value("requiresEvidence",J::array()))if(!game->v4.evidence.contains(card.get<std::string>()))game->v4.evidence[card.get<std::string>()]={{"name",card},{"text","isolated input fixture"}};
  assert(storyv4::jump(game->v4,game->v4.graph.at("taskNodes").at(id).get<std::string>()));game->v4Enter();assert(game->lastError.empty());
  while(game->v4QueueActive){clear();game->v4TaskQueueNext();}
  int positions=kind=="reasoning"?int(game->stage["questions"].size()):kind=="climax"?int(game->stage["slots"].size()):1;
  for(int position=0;position<positions;position++){
   clear();game->v4TaskLinks=position;if(kind=="reasoning")game->v4Reasoning();else if(kind=="climax")game->v4ComicShow();
   const int choices=int(game->opts.size()),answer=game->optAnswer;
   for(int wrong=kind=="spot"?-1:0;wrong<choices;wrong++){
    if(wrong==answer||(kind=="spot"&&wrong>=0&&game->stage["regions"][wrong].value("correct",false)))continue;
    while(game->v4QueueActive){clear();game->v4TaskQueueNext();}
    clear();game->v4ResetHearts(game->maxHearts);game->v4TaskLinks=position;if(kind=="reasoning")game->v4Reasoning();else if(kind=="climax")game->v4ComicShow();
    const auto node=game->v4.node;const int hp=game->v4TaskHp(),count=game->correctCount,gaffe=game->trialResults.current.gaffe;
    clear();game->optionPicked(wrong);if(kind=="climax"){clear();game->v4ComicUpdate(20.f/60,false);}
    auto expectedRows=game->v4Task["queues"].value("wrong",J::array());
    if(kind=="reasoning"){const auto& q=game->stage["questions"][position];for(const auto& variant:q.value("wrongVariants",J::array()))if(variant.value("optionId",std::string())==q["optionIds"][wrong].get<std::string>()&&!variant.value("script",J::array()).empty())expectedRows=variant["script"];}
    if(kind=="climax")expectedRows=game->stage["slots"][position]["options"][wrong].value("response",J::array());
    if(kind=="spot"&&wrong>=0){auto cause=game->stage["regions"][wrong].value("wrongVariant",std::string());for(const auto& variant:game->v4Task["queues"].value("wrongVariants",J::array()))if(!cause.empty()&&variant.value("cause",std::string())==cause)expectedRows=variant.value("script",variant.value("events",J::array()));}
    bool expectedResponse=!expectedRows.empty();int delta=kind=="climax"&&!expectedResponse?0:1;const bool response=game->v4QueueActive,charged=game->trialResults.current.gaffe==gaffe+delta,exactResponse=!expectedResponse||game->v4Queue==expectedRows;
    if(response){std::set<std::string> hidden;for(const auto& op:hb::bridgeOperations)if(op.at("key")=="uiSetVisible"&&!op.at("args").at("visible").get<bool>())hidden.insert(op.at("args").value("element",std::string()));assert(hidden.count("StatusPanel")&&hidden.count("StatusLabel"));for(int i=0;i<10;i++)assert(hidden.count("Star"+std::to_string(i)));}
    const bool ok=response==expectedResponse&&exactResponse&&charged&&game->v4.node==node&&game->correctCount==count&&game->v4TaskHp()<hp&&game->v4TaskLinks==position;
    cases.push_back({{"task",id},{"kind",kind},{"position",position},{"wrong",wrong},{"response",response},{"exactAuthoredResponse",exactResponse},{"expectedResponse",expectedResponse},{"oneGaffe",charged},{"hpBefore",hp},{"hpAfter",game->v4TaskHp()},{"ok",ok}});if(!ok)++failures;
    for(int i=0;i<5;i++){clear();game->v4TaskQueueUpdate(1.f/60);}assert(game->trialResults.current.gaffe==gaffe+delta);
    if(ok){resultv4::State restored;assert(resultv4::restore(restored,resultv4::save(game->trialResults)));assert(restored.current.gaffe==gaffe+delta);}
   }
  }
  while(game->v4QueueActive){clear();game->v4TaskQueueNext();}
  int gaffe=game->trialResults.current.gaffe;clear();game->optionPicked(game->optAnswer);if(kind=="climax"){clear();game->v4ComicUpdate(20.f/60,false);}assert(game->trialResults.current.gaffe==gaffe);
 }
 J report{{"ok",failures==0},{"cases",cases},{"failures",failures},{"scope","Actual C++ isolated fixtures of every candidate wrong option at all reasoning links and comic slots, ordinary answer/evidence/person/vote/spot tasks, plus outside-image spot misses. Explicit per-position fixture state and direct wrong callbacks; not native gameplay, full-history combinations or a playtime certificate. Exact authored response, HP, retained problem, one mistake event, repeat-display and save roundtrip checks."}};
 std::ofstream("Game/Saved/wrong-choice-full-regression.json")<<report.dump(2)<<"\n";std::cout<<J{{"ok",failures==0},{"cases",cases.size()},{"failures",failures}}.dump()<<"\n";return failures?1:0;
}
