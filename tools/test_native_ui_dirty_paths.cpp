#include <HBEngine/Bridge.hpp>
#include <cassert>
#include <iostream>
using namespace hb;
int main(){
 const std::string instance="hud~/",element="node~/";
 Json node={{"text","old"},{"visible",true},{"enabled",true},{"value",0.25},{"min",0},{"max",1},{"type","ProgressBar"}};
 Json input=Json::array({{{"id","owner"},{"position",{0,0,0}},{"rotation",{0,0,0}},{"scale",{1,1,1}},{"gameplayDebug",{{"ui",{{instance,{{element,node},{"unrelated",{{"text","preserved"}}}}}}}}}}});
 bridgeWorldData=input;bridgeStateIndices["owner"]=0;auto* actor=bridgeActor("owner");
 UI::SetText(actor,instance,element,"new");UI::SetValue(actor,instance,element,5);UI::SetVisible(actor,instance,element,false);UI::SetEnabled(actor,instance,element,false);
 assert(UI::GetText(actor,instance,element)=="new");assert(UI::GetValue(actor,instance,element)==1);
 // Getter uses the legacy mutable access boundary; it must retain full restoration.
 assert(!bridgeDirtyStates.empty());bridgeRestoreWorld(input);assert(bridgeWorldData==input);
 UI::SetText(actor,instance,element,"another");UI::SetValue(actor,instance,element,-5);UI::SetVisible(actor,instance,element,false);UI::SetEnabled(actor,instance,element,false);
 assert(bridgeDirtyStates.empty()&&bridgeDirtyFields.empty());assert(bridgeDirtyUIPaths.at(0).size()==5);
 assert(!node.contains("checked"));bridgeRestoreWorld(input);assert(bridgeWorldData==input);assert(bridgeDirtyUIPaths.empty());
 // Parent mutation wins over leaf tracking; changing types and deleting a parent restore too.
 UI::SetText(actor,instance,element,"new");auto* state=bridgeState(actor);(*state)["gameplayDebug"].erase("ui");(*state)["custom"]=7;bridgeRestoreWorld(input);assert(bridgeWorldData==input);
 UI::SetText(actor,instance,element,"new");(*bridgeStateFields(actor,{"gameplayDebug"}))["gameplayDebug"]=nullptr;bridgeRestoreWorld(input);assert(bridgeWorldData==input);
 // UI not initialized: original null-to-object insertion/restoration remains intact.
 Json empty=input;empty[0].erase("gameplayDebug");bridgeWorldData=empty;UI::SetText(actor,"absent","absent","x");assert(bridgeWorldData[0].contains("gameplayDebug"));bridgeRestoreWorld(empty);assert(bridgeWorldData==empty);
 // Array-size replacement clears leaf marks as well.
 bridgeWorldData=input;UI::SetText(actor,instance,element,"x");bridgeRestoreWorld(Json::array());assert(bridgeDirtyUIPaths.empty()&&bridgeWorldData.empty());
 std::cout<<"native UI leaf restore: setters/read-after-write, escaped names, missing checked, parent/whole mutation, absent UI and resize PASS\n";
}
