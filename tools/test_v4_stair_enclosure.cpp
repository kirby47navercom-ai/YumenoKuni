#include "../Game/Source/ExploreWorld.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
std::string hb::Data::GetText(const std::string& path){std::ifstream f("Game/"+path);if(!f)throw std::runtime_error(path);return {std::istreambuf_iterator<char>(f),{}};}
int main(){
 using J=hb::Json;exworld::State s;s.data=hb::Data::Get("Assets/Data/explore_world.json");s.space="lower_stairway";s.active=true;
 const auto& spec=s.spec();assert(spec.at("enclosedStairShell")==true);s.pose={0,1.6f,5.25f,0,0};assert(!exworld::solid(s,0,5.25f));
 float last=0;int samples=0;
 // Use the shipped floor/collision functions for both directions and portal landings.
 for(float z=5.25f;z>=-5.5f;z-=.025f){assert(!exworld::solid(s,0,z));float y=exworld::floorAt(s,0,z);assert(std::abs(y-last)<.201f);s.pose.y=y+1.6f;last=y;++samples;}
 assert(std::abs(last+5.76f)<.001f);
 for(float z=-5.5f;z<=5.25f;z+=.025f){assert(!exworld::solid(s,0,z));float y=exworld::floorAt(s,0,z);assert(std::abs(y-last)<.201f);s.pose.y=y+1.6f;last=y;++samples;}
 assert(std::abs(last)<.001f);
 for(float z:{-3.f,-1.f,1.f,3.f}){s.pose.y=1.6f;s.pose.y=exworld::floorAt(s,0,z)+1.6f;assert(exworld::solid(s,1.2f,z));assert(exworld::solid(s,-1.2f,z));}
 s.pose.y=-2.88f+1.6f;for(float x=-.88f;x>=-1.48f;x-=.02f){assert(!exworld::solid(s,x,0));assert(std::abs(exworld::floorAt(s,x,0)+2.88f)<.001f);}
 int portals=0;for(const auto& e:s.data["connections"]){const char* key=nullptr;float floor=0;if(e["id"]=="maintenance_workshop__lower_stairway"){key="b_p";floor=-2.88f;}if(e["id"]=="lower_stairway__lower_corridor"){key="a_p";floor=-5.76f;}if(!key)continue;auto p=exworld::point(e[key]);assert(std::abs(p.y-1.2f-floor)<.001f);float n=std::hypot(p.x,p.z);float x=p.x-p.x/n*.9f,z=p.z-p.z/n*.9f;s.pose.y=floor+1.6f;assert(!exworld::solid(s,x,z));assert(std::abs(exworld::floorAt(s,x,z)-floor)<.001f);++portals;}
 assert(portals==2);J report={{"ok",true},{"actualCppFloorCollision",true},{"bidirectionalSamples",samples},{"existingPortals",portals},{"newRoutes",0},{"nativePixels",false}};std::ofstream("Game/Saved/stair-enclosure-cpp-20261101.json")<<report.dump(2)<<"\n";std::cout<<report.dump()<<"\n";
}
