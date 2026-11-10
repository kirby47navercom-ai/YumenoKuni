#include "../Game/Source/ExploreWorld.hpp"
#include <cassert>
#include <iostream>
int main(){
 using J=hb::Json;exworld::State world;world.id="mirror_maze";world.active=true;
 world.history["hotel_lobby"]={1,1.6f,2,12,-4};world.history[world.id]={5,1.6f,8,0,0};
 world.pose={2.25f,1.7f,-3.5f,37,-11};const auto old=world.history;
 const auto saved=exworld::save(world);
 assert(saved.at(world.id)==J::array({2.25f,1.7f,-3.5f,37.f,-11.f}));
 assert(saved.at("hotel_lobby")==J::array({1.f,1.6f,2.f,12.f,-4.f}));
 assert(world.history.size()==old.size()&&world.history.at(world.id).x==5);
 exworld::State restored;exworld::restore(restored,saved);assert(restored.history.at(world.id).yaw==37);
 world.history.erase(world.id);assert(exworld::save(world).contains(world.id));
 world.active=false;assert(!exworld::save(world).contains(world.id));world.active=true;world.id.clear();assert(!exworld::save(world).contains(""));
 std::cout<<"Current pose replaces stale history; first room persists; other rooms and live state preserved; old save format unchanged.\n";
}
