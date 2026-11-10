// Pure source timing/pagination model; no native player, target-time padding or reading-speed claim.
#include "../Game/Source/DialogueTextV4.hpp"
#include "../Game/Source/OptionsV4.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
using J=hb::Json;
static J read(const std::string& path){std::ifstream f(path);assert(f);J j;f>>j;return j;}
int main(int argc,char** argv){
 assert(argc==2);std::string tag=argv[1];assert(!tag.empty()&&tag.find_first_not_of("0123456789")==std::string::npos);
 auto rows=read("Game/Saved/selected-dialogue-"+tag+".json");
 auto layout=read("Game/Assets/Data/v4_story/dialogue_layout.json"),choice=read("Game/Assets/Data/v4_story/choice_layout.json");
 std::map<std::string,float> advances;for(const auto& bucket:choice["advances"])for(const auto& [key,v]:bucket.items())advances[key]=v.get<float>();
 optv4::State options;assert(options.values.textSpeed==8&&!options.values.autoRead);
 assert(optv4::CharactersPerSecond(options)==40.f&&options.values.autoWait==1.5f);
 // Check the actual AutoAdvance reset/full-page/blocked behavior at fixed 60Hz.
 options.values.autoRead=true;assert(!optv4::AutoAdvance(options,1,false));
 assert(!optv4::AutoAdvance(options,1,true));for(int i=0;i<89;++i)assert(!optv4::AutoAdvance(options,1.f/60,true));
 int waitTicks=89;while(!optv4::AutoAdvance(options,1.f/60,true)){assert(waitTicks<100);++waitTicks;}++waitTicks;
 assert(!optv4::AutoAdvance(options,2,true,true));assert(!optv4::AutoAdvance(options,2,true));
 J phases=J::object();
 for(const auto& row:rows){
  const bool trial=row["phase"]=="trial";
  float size=trial?layout["trial"]["font"].get<float>():layout["font"].get<float>();
  float width=trial?layout["trial"]["body"][2].get<float>()-8:layout["ownWrap"]["width"].get<float>();
  const auto text=row["text"].get<std::string>();
  auto pages=dialoguetext::pages(text,width,trial?2:3,[&](const std::string& glyph){auto it=advances.find(glyph);return (it==advances.end()?26.66667f:it->second)*size/26.6666667f;},true);
  std::string joined;int count=0;double reveal=0;int revealTicks=0;
  for(const auto& page:pages){
   joined+=page.raw;const auto chars=dialoguetext::glyphs(page.text).size();count+=int(chars);reveal+=chars/40.0;
   float shown=0;int ticks=0;while(int(shown)<int(chars)){shown=std::min(float(chars),shown+(1.f/60)*optv4::CharactersPerSecond(options));++ticks;}
   revealTicks+=ticks;
  }
  assert(joined==text);
  const std::string key=std::to_string(row["policy"].get<int>())+":"+row["chapter"].get<std::string>()+":"+row["phase"].get<std::string>();
  if(!phases.contains(key))phases[key]={{"rows",0},{"pages",0},{"displayGlyphs",0},{"revealSeconds",0.0},{"autoDialogueTicks60Hz",0}};
  auto& total=phases[key];total["rows"]=total["rows"].get<int>()+1;total["pages"]=total["pages"].get<int>()+int(pages.size());
  total["displayGlyphs"]=total["displayGlyphs"].get<int>()+count;total["revealSeconds"]=total["revealSeconds"].get<double>()+reveal;
  // FullSeen's first call is on the reveal-complete frame, then waitTicks subsequent frames.
  total["autoDialogueTicks60Hz"]=total["autoDialogueTicks60Hz"].get<int>()+revealTicks+int(pages.size())*waitTicks;
 }
 J report={{"ok",true},{"nativePlayerLaunched",false},{"taskThinkingReadingOrAnimationAssigned",false},
  {"defaultAutoEnabled",false},{"autoScenario",{{"textSpeed",8},{"charactersPerSecond",40},{"waitSecondsPerPage",1.5},{"waitTicks60Hz",waitTicks}}},
  {"source",J::array({"Game/Source/DialogueTextV4.hpp","Game/Source/OptionsV4.hpp","Game/Source/V4Story.hpp","Game/Source/V4Tasks.hpp"})},
  {"scope","Exact own source pagination and option timing over selected route dialogue only. Auto must be enabled; manual reveal/advance remains player controlled. No human reading rate, task time or five-hour claim."},{"phases",phases}};
 std::ofstream out("Game/Saved/dialogue-pacing-"+tag+".json");out<<report.dump(2)<<'\n';
 std::cout<<J{{"ok",true},{"phases",phases.size()},{"waitTicks60Hz",waitTicks},{"nativePlayerLaunched",false}}.dump()<<'\n';
}
