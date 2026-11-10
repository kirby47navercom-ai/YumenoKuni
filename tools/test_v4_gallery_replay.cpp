#include "../Game/Source/GalleryV4.hpp"
#include "../Game/Source/DialoguePortraitV4.hpp"
#include <cassert>
int main(){
 using J=hb::Json;using galleryv4::replayMusic;
 J n={{"source",{{"file","one.md"},{"location","day"}}}};
 J h={{"presentation",{{"sectionBeds",{{"one.md:day",{{"music","bgm_daily"}}},{"one.md:night",{{"music","@silence"}}}}}}}};
 auto m=replayMusic(n,h);assert(m.first&&m.second=="bgm_daily");
 n["source"]["location"]="night";m=replayMusic(n,h);assert(m.first&&m.second=="@silence");
 n["source"]["location"]="unknown";assert(!replayMusic(n,h).first);
 n["music"]="";m=replayMusic(n,h);assert(m.first&&m.second.empty());
 n["music"]="bgm_explicit";assert(replayMusic(n,h).second=="bgm_explicit");
 n={{"type","say"},{"actor","mio"},{"mono",false},{"dialoguePortrait","rin"}};
 assert(dialogueportraitv4::interlocutor(n)=="rin");n["mono"]=true;assert(dialogueportraitv4::interlocutor(n).empty());
 n={{"scene",{{"space","hotel_rest_lounge"}}},{"sceneVariants",J::array({
  J{{"space","kitchen"},{"when",J::array({J{{"flag","F-AI02-B"},{"equals","B1"}}})}},
  J{{"space","hotel_corridor"},{"when",J::array({J{{"flag","F-AI02-B"},{"equals","B2"}}})}},
  J{{"space","hotel_rest_lounge"},{"when",J::array({J{{"flag","F-AI02-B"},{"equals","B3"}}})}}
 })}};
 const auto original=n;
 for(auto pair:{std::pair{"B1","kitchen"},std::pair{"B2","hotel_corridor"},std::pair{"B3","hotel_rest_lounge"}}){J flags={{"F-AI02-B",pair.first}};const auto before=flags;assert(galleryv4::replayScene(n,flags)["space"]==pair.second);assert(flags==before);}
 assert(galleryv4::replayScene(n,J::object())==n["scene"]);assert(n==original);
 n["sceneVariants"].push_back(n["sceneVariants"][1]);assert(galleryv4::replayScene(n,J{{"F-AI02-B","B2"}})==n["scene"]);
}
