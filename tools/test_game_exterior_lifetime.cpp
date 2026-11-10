#include <HBEngine/Bridge.hpp>
#include "../Game/Source/ExploreWorld.hpp"
#include <cassert>
#include <iostream>
int main(){using namespace hb;
 for(const auto& id:{"OutdoorSkyDome","ExteriorContext","Exterior_landmark"}){const size_t n=bridgeWorldData.size();bridgeStateIndices[id]=n;bridgeWorldData.push_back({{"id",id},{"kind","empty"},{"position",{0,0,0}},{"rotation",{0,0,0}},{"scale",{1,1,1}},{"components",Json::array({{{"id",std::string(id)+"Mesh"},{"type","MeshRenderer"},{"properties",{{"mesh","old.glb"},{"visible",true}}}}})}});}
 exworld::State s;s.active=s.visible=s.loaded=true;s.id=s.space="room";s.data={{"spaces",{{"room",{{"outdoor",false}}},{"plaza",{{"outdoor",true}}}}},{"instances",{{"room",{{"p",{0,0,0}}}},{"plaza",{{"p",{0,0,0}}}}}},{"worldContext",{{"mesh","world.glb"},{"landmarks",{{"landmark","landmark.glb"}}}}}};
 exworld::environment(s,0);for(const auto& id:{"OutdoorSkyDome","ExteriorContext","Exterior_landmark"})assert(Components::GetString(Scene::FindActorById(id),"MeshRenderer","mesh").empty());
 s.id=s.space="plaza";exworld::environment(s,1);assert(Components::GetString(Scene::FindActorById("OutdoorSkyDome"),"MeshRenderer","mesh")=="Assets/Art/environment/sky_night.glb");assert(Components::GetString(Scene::FindActorById("ExteriorContext"),"MeshRenderer","mesh")=="world.glb");assert(Components::GetString(Scene::FindActorById("Exterior_landmark"),"MeshRenderer","mesh")=="landmark.glb");
 s.id=s.space="room";exworld::environment(s,0);for(const auto& id:{"OutdoorSkyDome","ExteriorContext","Exterior_landmark"})assert(Components::GetString(Scene::FindActorById(id),"MeshRenderer","mesh").empty());
 std::cout<<"PASS: interior starts without exterior meshes, night loads only matching sky/context, returning indoors clears all exterior mesh references\n";
}
