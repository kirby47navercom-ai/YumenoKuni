#pragma once
#include <HBEngine/Game.hpp>
#include <vector>
#include <string>
#include <cmath>
#include <cstdio>
#include "ShotRecoveryV4.hpp"
#include "DisplayV4.hpp"
namespace kotodamaflightv4 {
// Camera-child closed meshes. Selected evidence letters form one oriented 3D word;
// the evidence HUD plate is never used as the projectile.
struct Flight {
 std::vector<hb::Actor*> actors;
 std::vector<unsigned> letters;
 void clear(){for(auto* a:actors)if(a)hb::Components::SetBool(a,"MeshRenderer","visible",false);actors.clear();letters.clear();}
 void begin(const std::string& label){
  clear();for(size_t p=0;p<label.size()&&letters.size()<48;){unsigned c=(unsigned char)label[p++];if(c>=192){int n=c<224?1:c<240?2:3;c&=(1u<<(6-n))-1;while(n--&&p<label.size())c=(c<<6)|((unsigned char)label[p++]&63);}letters.push_back(c);}
  for(size_t i=0;i<letters.size();++i){auto* a=hb::Scene::FindActorById("KotodamaWord"+std::to_string(i));actors.push_back(a);if(a&&letters[i]>32){char mesh[120];std::snprintf(mesh,sizeof mesh,"Assets/Art/nonstop_solid_type/u_%x_w.glb",letters[i]);hb::Components::SetString(a,"MeshRenderer","mesh",mesh);}}
 }
 void draw(float progress,float x,float y,float originY,bool active){
  float width=1280,height=720;
#ifdef _WIN32
  RECT r{};if(auto window=displayv4::Window();window&&GetClientRect(window,&r)){width=float(r.right);height=float(r.bottom);}
#endif
  for(size_t i=0;i<actors.size();++i)if(auto* a=actors[i]){
   const auto p=shotv4::WordFlight::letter(progress,int(i),int(letters.size()),x,y,originY,width,height);
   const bool on=active&&p.visible&&letters[i]>32;
   hb::Components::SetBool(a,"MeshRenderer","visible",on);
   if(on){hb::Scene::SetPosition(a,{p.x,p.y,p.z});hb::Scene::SetScale(a,{p.scale,p.scale,p.scale});hb::Scene::SetRotation(a,{0,p.yaw,p.roll});}

  }
 }
};
}
