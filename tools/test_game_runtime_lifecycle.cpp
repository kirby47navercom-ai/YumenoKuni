#include <HBEngine/Bridge.hpp>
#include "../Game/Source/WidgetOwnersV4.hpp"
#include "../Game/Source/RuntimeScenesV4.hpp"
#include <cassert>
#include <iostream>
int main(){
 using W=widgetownersv4::UI;using namespace hb;
 Json host={{"id","UI_modal"},{"kind","empty"},{"position",{0,0,0}},{"rotation",{0,0,0}},{"scale",{1,1,1}}};bridgeWorldData=Json::array({host});bridgeStateIndices["UI_modal"]=0;
 W::SetVisible(nullptr,"pad","leaf",false);assert(bridgeOperations.empty());
 W::Show(nullptr,"Assets/UI/Pad.hbwidget.json","pad");auto first=bridgeId(W::Owner(nullptr,"pad"));assert(W::Mounted("pad"));
 auto n=bridgeOperations.size();W::SetText(nullptr,"pad","leaf","same");W::SetText(nullptr,"pad","leaf","same");assert(bridgeOperations.size()==n+1);
 W::SetPosition(nullptr,"pad","leaf",{3,7});n=bridgeOperations.size();W::SetPosition(nullptr,"pad","leaf",{3,7});assert(bridgeOperations.size()==n);
 W::Remove(nullptr,"pad");assert(!W::Mounted("pad")&&!W::applied.count("pad"));n=bridgeOperations.size();W::SetText(nullptr,"pad","leaf","hidden");assert(bridgeOperations.size()==n);
 W::Show(nullptr,"Assets/UI/Pad.hbwidget.json","pad");assert(bridgeId(W::Owner(nullptr,"pad"))==first);n=bridgeOperations.size();W::SetText(nullptr,"pad","leaf","same");assert(bridgeOperations.size()==n+1);
 scenesv4::court.loaded=scenesv4::court.requested=true;scenesv4::court.instance="court";assert(!scenesv4::exploreReady());assert(!scenesv4::court.loaded&&scenesv4::waiting());assert(!scenesv4::court.loaded);
 scenesv4::title();assert(scenesv4::waiting());assert(!scenesv4::poll());assert(bridgeOperations.back()["key"]=="openScene");
 host["id"]="TitleScene";bridgeWorldData.push_back(host);bridgeStateIndices["TitleScene"]=1;assert(scenesv4::poll());assert(!scenesv4::waiting());
 scenesv4::court.loaded=true;scenesv4::loadingShown=true;scenesv4::reset();assert(!scenesv4::waiting()&&!scenesv4::court.loaded&&!scenesv4::explore.loaded&&!scenesv4::loadingShown);
 std::cout<<"PASS: scene-owned host, absent writes, unchanged setters, remove/remount cache reset, court-explore-title ownership\n";
}

