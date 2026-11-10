#include <HBEngine/Bridge.hpp>
#include "../Game/Source/ExploreWorld.hpp"
#include <iostream>
int main(){using namespace hb;
 bridgeWorldData=Json::array({{{"id","Camera"},{"kind","camera"},{"position",{0,0,0}},{"rotation",{0,0,0}},{"scale",{1,1,1}},{"components",Json::array({{{"id","camera"},{"type","Camera"},{"properties",{{"fieldOfView",court::FIELD_OF_VIEW}}}}})}}});bridgeStateIndices["Camera"]=0;
 exworld::State s;s.active=s.loaded=true;s.space="room";s.data={{"spaces",{{"room",{{"outdoor",false}}}}}};
 for(int i=0;i<120;i++){s.pose.yaw=float(i);exworld::camera(s);}
 if(!bridgeOperations.empty()){std::cerr<<"FAIL: unchanged FOV emitted "<<bridgeOperations.size()<<" commands in120 camera updates\n";return 1;}
 auto* camera=Scene::FindActorById("Camera");Components::SetFloat(camera,"Camera","fieldOfView",70);bridgeOperations.clear();exworld::camera(s);
 if(bridgeOperations.size()!=1||Components::GetFloat(camera,"Camera","fieldOfView")!=court::FIELD_OF_VIEW){std::cerr<<"FAIL: changed FOV was not restored exactly once\n";return 1;}
 bridgeOperations.clear();exworld::camera(s);if(!bridgeOperations.empty()){std::cerr<<"FAIL: restored FOV was sent again\n";return 1;}
 std::cout<<"PASS:120 moving camera updates emit0 unchanged FOV commands; wrong FOV restores once\n";
}
