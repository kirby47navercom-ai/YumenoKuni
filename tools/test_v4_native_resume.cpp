#include <HBEngine/Session.hpp>
#include "../Game/Source/Yumeno.cpp"
#include <fstream>
#include <iostream>
#include <cassert>
using J=hb::Json;
static J read(const std::string& file){std::ifstream f(file);if(!f)throw std::runtime_error(file);return J::parse(f);}
int main(int argc,char** argv){
 bool resultTest=argc>2&&std::string(argv[2])=="--result-widget",rhythmTest=argc>2&&std::string(argv[2])=="--rhythm",endingTest=argc>2&&std::string(argv[2])=="--ending-save",readSkipTest=argc>2&&std::string(argv[2])=="--read-skip";auto destination=resultTest?"Game/Saved/native-result-operations.json":rhythmTest?"Game/Saved/native-rhythm-restore-operations.json":endingTest?"Game/Saved/native-ending-restore-operations.json":readSkipTest?"Game/Saved/read-skip-restore-operations.json":"Game/Saved/native-resume-operations.json";
 auto raw=read(argc>1?argv[1]:"Game/Saved/ui-checkpoints/normal-ch3-latest/savegames.json");
 auto storage=raw.at("items");
 std::string expectedNode,canonicalKey,projectSuffix;for(const auto& [key,value]:storage.items())if(key.find("yumeno-progress-v4.project.")!=std::string::npos){expectedNode=J::parse(value.get<std::string>()).at("node").get<std::string>();canonicalKey=key;projectSuffix=key.substr(key.find(".project."));}
 int saveQueries=0;bool failWrite=false;
 std::map<std::string,int> dataQueries;
 hb::bridgeQuery=[&](const J& p)->J{
  auto key=p.at("key").get<std::string>();const auto& a=p.at("args");J value;
  if(key=="dataJsonRead"){++dataQueries[a.at("path").get<std::string>()];value=read("Game/"+a.at("path").get<std::string>()).dump();}
  else if(key=="saveJsonRead"){++saveQueries;std::string prefix="hbengine.savegame.json."+a.at("slot").get<std::string>()+".project.";value="";for(const auto& [k,v]:storage.items())if(k.rfind(prefix,0)==0)value=v;}
  else if(key=="saveJsonWrite"){++saveQueries;if(failWrite)throw std::runtime_error("simulated write failure");storage["hbengine.savegame.json."+a.at("slot").get<std::string>()+projectSuffix]=a.at("json");value=true;}
  else if(key=="saveJsonDelete"){++saveQueries;storage.erase("hbengine.savegame.json."+a.at("slot").get<std::string>()+projectSuffix);value=true;}
  else throw std::runtime_error("Unexpected query: "+key);
  return {{"ok",true},{"value",value}};
 };
 auto objects=read("Game/Assets/Scenes/Main.hbscene.json").at("objects");
 hb::bridgeSync(objects);hb::bridgeActors["Driver"]=std::make_unique<Yumeno>();
 auto* game=static_cast<Yumeno*>(hb::bridgeActors.at("Driver").get());hb::bridgeActorIds[game]="Driver";
 J frames=J::array();bool passed=false;std::set<std::string> mounted;
 auto widgetOrder=[&](){for(const auto& op:hb::bridgeOperations){auto key=op.at("key").get<std::string>();const auto& a=op.at("args");if(!a.contains("instance"))continue;auto id=a.value("target",std::string())+":"+a.at("instance").get<std::string>();if(key=="uiShow")mounted.insert(id);else if(key=="uiRemove")mounted.erase(id);else if(key.rfind("uiSet",0)==0&&!mounted.count(id))throw std::runtime_error("Widget used before Show: "+id);}};
 for(int i=0;i<10;i++){
  hb::bridgeOperations=J::array();hb::bridgeOperationStart=0;
  hb::bridgeInput={{"keys",i==1?J{{"c",1}}:J::object()}};
  std::string error;try{game->Update(1.f/60);widgetOrder();}catch(const std::exception& e){error=e.what();}
  J counts=J::object();for(const auto& op:hb::bridgeOperations){auto k=op.at("key").get<std::string>();counts[k]=counts.value(k,0)+1;}
  frames.push_back({{"frame",i},{"operations",hb::bridgeOperations.size()},{"counts",counts},{"error",error},{"stats",J::parse(game->Stats())}});
  std::ofstream(destination)<<frames.dump(2)<<"\n";
  if(error.empty())error=J::parse(game->Stats()).value("error",std::string());
  if(!error.empty()){std::cerr<<error<<" frame="<<i<<" operations="<<hb::bridgeOperations.size()<<"\n";return 1;}
  auto stats=J::parse(game->Stats());if(stats.value("node",std::string())==expectedNode&&stats.value("mode",std::string())==(endingTest?"credits":"trial")){passed=true;}
 }
 if(readSkipTest){
  hb::bridgeOperations=J::array();game->DebugV4DialogueFixture(0);widgetOrder();const auto id=game->v4.node;game->optionsV4.values.textSpeed=0;game->optionsV4.values.readOnlySkip=false;game->shown=0;game->skipTimer=0;
  for(int i=0;i<100&&game->v4.node==id;i++){hb::bridgeOperations=J::array();hb::bridgeInput={{"keys",{{"control",1}}}};game->Update(.1f);widgetOrder();}bool recorded=game->v4.read.count(id)>0;bool advanced=game->v4.node!=id;
  std::ofstream("Game/Saved/read-skip-regression.json")<<J{{"ok",recorded&&advanced},{"node",id},{"advanced",advanced},{"recorded",recorded},{"scope","Actual C++ Update and original authored one-page dialogue fixture; Control must publish read status before leaving its final page. No historical read reconstruction or native renderer claim."}}.dump(2)<<"\n";
  std::cout<<J{{"ok",recorded&&advanced},{"recorded",recorded},{"advanced",advanced}}.dump()<<"\n";return recorded&&advanced?0:1;
 }
 if(endingTest){
  assert(passed&&game->v4.current().value("campaignNarrativeEnd",false));const auto coins=game->coins;hb::bridgeOperations=J::array();game->v4EndingBegin();widgetOrder();assert(game->v4EndingSavePending&&game->mode!=Yumeno::Mode::Credits);
  int steps=0,maximumQueries=0;for(;game->v4EndingSavePending&&steps<300;steps++){saveQueries=0;hb::bridgeOperations=J::array();hb::bridgeInput={{"keys",{{"enter",1},{"tab",1}}}};game->Update(1.f/60);widgetOrder();maximumQueries=std::max(maximumQueries,saveQueries);if(game->v4EndingSavePending)assert(game->mode!=Yumeno::Mode::Credits);assert(game->lastError.empty());}
  assert(!game->v4EndingSavePending&&game->mode==Yumeno::Mode::Credits&&maximumQueries<=4&&game->coins==coins);auto saved=savev4::read("yumeno-progress-v4");assert(saved.at("node")==expectedNode&&saved["trialResults"]["best"]["6"]["paid"]==true);
  auto committed=storage.at(canonicalKey);hb::bridgeOperations=J::array();game->v4EndingBegin();widgetOrder();failWrite=true;hb::bridgeOperations=J::array();game->Update(1.f/60);widgetOrder();assert(!game->v4EndingSavePending&&game->mode!=Yumeno::Mode::Credits&&!game->lastError.empty()&&storage.at(canonicalKey)==committed);
  std::ofstream("Game/Saved/ending-save-cooperative.json")<<J{{"ok",true},{"steps",steps},{"maximumSaveQueriesPerUpdate",maximumQueries},{"completePartsBeforeCredits",true},{"inputCannotExitWhileSaving",true},{"failurePreservesPublishedHead",true},{"failureDoesNotShowCredits",true},{"scope","Actual C++ and read-only engine bridge, actual ending snapshot, in-memory save service and injected write failure; native replay is separate"}}.dump(2)<<"\n";std::cout<<J{{"ok",true},{"steps",steps},{"maximumQueries",maximumQueries}}.dump()<<"\n";return 0;
 }
 // Exercise the same native Save tab that the traversal opens before input.
 hb::bridgeOperations=J::array();game->padToggle();game->padPageAt=5;
 for(int view:{0,1,2,4,5,6}){game->padSystemView=view;game->padSystemDraw();widgetOrder();hb::bridgeOperations=J::array();}
 game->padToggle();widgetOrder();
 if(argc>2&&std::string(argv[2])=="--panic-hud"){
  assert(game->stageKind=="panic");hb::bridgeOperations=J::array();game->debateHud(true);widgetOrder();
  for(const auto* element:{"NamePanel","TrialSpeaker"}){bool hidden=false;for(const auto& op:hb::bridgeOperations){const auto& a=op.at("args");if(op.at("key")=="uiSetVisible"&&a.value("element",std::string())==element){assert(a.at("target")=="UI_main");hidden=!a.at("visible").get<bool>();}}assert(hidden);}
  std::ofstream("Game/Saved/panic-hud-ownership.json")<<J{{"ok",true},{"scope","Actual C++/normal saved panic and widget ownership; overlapping single-speaker plate is hidden. Native pixels still pending."}}.dump(2)<<"\n";
 }
 if(argc>2&&std::string(argv[2])=="--pad-cache"){
  game->padToggle();game->padPageAt=0;game->padMapDraw();widgetOrder();hb::bridgeOperations=J::array();game->padRows();game->padMapUpdate(1.f/60,false);widgetOrder();
  auto mapReads=dataQueries["Assets/Data/v4_story/map_layout.json"];
  for(int i=0;i<120;i++){hb::bridgeOperations=J::array();game->padRows();game->padMapUpdate(1.f/60,false);widgetOrder();}
  assert(dataQueries["Assets/Data/v4_story/map_layout.json"]==mapReads);
  game->padMapClear();game->padPageAt=4;game->padRow=0;game->padRulesDraw();widgetOrder();assert(!game->padRuleIds().empty());
  hb::bridgeOperations=J::array();game->keyEdges.clear();game->keyEdges["s"]=true;game->padRulesUpdate(1.f/60,false);widgetOrder();game->keyEdges.clear();
  for(int i=0;i<20;i++){hb::bridgeOperations=J::array();game->padRulesUpdate(1.f/60,false);widgetOrder();}
  assert(game->padRow==1&&game->padRuleTimer==0);auto ruleReads=dataQueries["Assets/Data/v4_story/rules_layout.json"];
  for(int i=0;i<120;i++){hb::bridgeOperations=J::array();game->padRuleIds();game->padRulesUpdate(1.f/60,false);widgetOrder();}
  assert(dataQueries["Assets/Data/v4_story/rules_layout.json"]==ruleReads);
  hb::bridgeOperations=J::array();game->padToggle();widgetOrder();
  std::ofstream("Game/Saved/pad-layout-cache.json")<<J{{"ok",true},{"mapFrames",120},{"ruleFrames",120},{"repeatedLayoutQueries",0},{"ruleTurnCompleted",true},{"scope","Actual C++/read-only engine bridge and normal saved world/public documents; no renderer/player in this test"}}.dump(2)<<"\n";
 }
 if(rhythmTest){
  game->DebugFastRead();J records=J::array();int lastRecorded=-1,ticks=0;auto wanted=expectedNode.substr(std::string("v4:input:").size());
  for(;ticks<12000;ticks++){
   const auto a=game->v4Auto();auto kind=a.value("kind",std::string());J keys{{"control",1}};
   if(kind=="hold-key"||(kind=="release-after"&&a.value("remaining",0.f)>0))keys[hb::bridgeInputKey(a.at("key").get<std::string>())]=1;
   else if((kind=="key"||kind=="rapid-key")&&ticks%2==0)keys[hb::bridgeInputKey(a.at("key").get<std::string>())]=1;
   hb::bridgeInput={{"keys",keys}};hb::bridgeOperations=J::array();game->Update(1.f/60);widgetOrder();
   auto diagnostic=game->RhythmStats();assert(diagnostic.size()<4096);
   for(const auto& r:game->rhythmRecent)if(r.at("note").get<int>()>lastRecorded){records.push_back(r);lastRecorded=r.at("note").get<int>();}
   assert(game->lastError.empty()&&game->v4.blocked.empty());
   if(game->v4LastOutcome.value("taskId",std::string())==wanted)break;
  }
  assert(dataQueries["Assets/Data/presentation/v3_armament_layout.json"]==1);
  auto result=J{{"ok",ticks<12000},{"ticks",ticks},{"task",wanted},{"retries",game->retries},{"hp",game->armingV4.hp},{"opponent",game->armingV4.opponent},{"records",records},{"rhythmLayoutQueries",dataQueries["Assets/Data/presentation/v3_armament_layout.json"]},{"diagnosticBytes",game->RhythmStats().size()},{"scope","Actual C++ at60Hz with sampled key states and actual saved inventory; no renderer/player or task success injection"}};
  std::ofstream("Game/Saved/rhythm-cpp-input-replay.json")<<result.dump(2)<<"\n";std::cout<<J{{"ok",ticks<12000},{"ticks",ticks},{"retries",game->retries},{"hp",game->armingV4.hp},{"opponent",game->armingV4.opponent},{"records",records.size()}}.dump()<<"\n";assert(ticks<12000);
 }
 if(resultTest){
  // Pure ownership fixture: real captured vote UI, not a played result claim.
  hb::bridgeOperations=J::array();game->trialResultStart();
  try{widgetOrder();}catch(const std::exception& e){std::ofstream("Game/Saved/result-widget-lifecycle-before.json")<<J{{"error",e.what()},{"operations",hb::bridgeOperations}}.dump(2);std::cerr<<e.what()<<"\n";return 1;}
  assert(game->trialResultOn);auto coins=game->coins;hb::bridgeOperations=J::array();game->padToggle();game->toast("저장했어요");game->padToggle();widgetOrder();assert(game->trialResultOn);assert(game->toastTimer==0&&!game->fvisible["FToast"]);
  hb::bridgeOperations=J::array();game->trialResultClear();game->trialResultStart();widgetOrder();assert(game->coins==coins);
  std::ofstream("Game/Saved/result-widget-lifecycle.json")<<J{{"ok",true},{"checks",{"first mount before UI access","Pad close clears modal toast","reopen after Remove","result reward not paid twice"}},{"scope","Actual C++ and engine bridge operation ownership fixture; native route is separate"}}.dump(2)<<"\n";
 }
 assert(passed);std::cout<<J{{"ok",true},{"frames",frames.size()},{"scope","Actual game C++ and read-only engine bridge, protected save, per-update1000 operation cap. No renderer/player in this test."}}.dump()<<"\n";
}
