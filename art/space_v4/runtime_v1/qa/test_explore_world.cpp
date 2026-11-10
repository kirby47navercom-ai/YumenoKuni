#include "ExploreWorld.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
int main(){
 using namespace exworld;State s;std::ifstream input("art/space_v4/runtime_v1/world.json");input>>s.data;s.loaded=s.active=true;int checks=0;
 auto yes=[&](bool v){++checks;assert(v);};
 for(auto& [id,d]:s.data["spaces"].items()){
  s.space=s.id=id;s.free=d.value("mode","")=="free_walk";auto p=point(d["spawn"]);s.pose={p.x,p.y,p.z,0,0};yes(!solid(s,p.x,p.z));
  if(!s.free){auto before=s.pose;yes(!move(s,.1f,1,1,true));yes(s.pose.x==before.x&&s.pose.z==before.z);look(s,1000,1000);yes(s.pose.x==before.x&&s.pose.y==before.y&&s.pose.z==before.z);yes(s.pose.pitch<=d["pitch_limits"][1].get<float>());}
  else{for(int i=0;i<100;i++){move(s,.1f,1,0,true);yes(!solid(s,s.pose.x,s.pose.z));}yes(solid(s,d["bounds"][2].get<float>()+1,0));}
 }
 s.space=s.id="hotel_lobby";s.free=true;s.pose={-4,1.55f,.2f,0,0};
 for(int n=0;n<18;n++){float z=.2f-.26f*n;float floor=floorAt(s,-4,z);yes(std::abs(floor-(n+1)*3.2f/18)<.001f);s.pose.z=z;s.pose.y=floor+1.55f;}
 yes(std::abs(s.pose.y-4.75f)<.001f);
 s.space=s.id="plaza";s.pose={0,1.55f,0,0,0};float x,y,depth;yes(project(s,{0,1.55f,-2},x,y,depth)&&std::abs(x-640)<.001f&&std::abs(y-360)<.001f);yes(!project(s,{0,1.55f,2},x,y,depth));
 auto path=route(s,"plaza","guest_16");yes(path.size()>=4&&path.front()=="plaza"&&path.back()=="guest_16");
 std::cout<<"{\"passed\":true,\"assertions\":"<<checks<<",\"scope\":\"local geometry math; no renderer/game/original execution\"}"<<std::endl;
}
