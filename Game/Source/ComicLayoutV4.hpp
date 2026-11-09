#pragma once
#include <HBEngine/Game.hpp>
#include <array>
#include <algorithm>
#include <cmath>
#include "Courtroom.hpp"
namespace comicv4ui {
using Rect=std::array<float,4>;
inline constexpr int stockPageSize=8;
inline int page(const hb::Json& stage,int slot){const auto& pages=stage.at("comicPresentation").at("pages");for(int p=0;p<int(pages.size());p++)for(const auto& i:pages[p].at("slots"))if(i.get<int>()==slot)return p;throw std::runtime_error("Comic slot has no authored page");}
inline int count(const hb::Json& stage){return int(stage.at("comicPresentation").at("pages").size());}
inline std::vector<int> slots(const hb::Json& stage,int page){return stage.at("comicPresentation").at("pages").at(page).at("slots").get<std::vector<int>>();}
// Display and picking share the same projected four corners. The bounding
// rectangle alone includes empty pixels outside a perspective panel.
inline constexpr float angle=0.f;
inline const hb::Json& quad(const hb::Json& stage,int index){return stage.at("comicPresentation").at("pages").at(page(stage,index)).at("screenQuads").at(std::to_string(index));}
inline Rect rect(const hb::Json& stage,int index){const auto& q=quad(stage,index);float l=1280,t=720,r=0,b=0;for(const auto& p:q){l=std::min(l,p[0].get<float>());t=std::min(t,p[1].get<float>());r=std::max(r,p[0].get<float>());b=std::max(b,p[1].get<float>());}return {l,t,r-l,b-t};}
inline bool hitRect(Rect r,float rotation,float x,float y){float a=-rotation*court::PI/180,dx=x-r[0]-r[2]/2,dy=y-r[1]-r[3]/2;return std::abs(dx*std::cos(a)-dy*std::sin(a))<=r[2]/2&&std::abs(dx*std::sin(a)+dy*std::cos(a))<=r[3]/2;}
inline bool hit(const hb::Json& stage,int index,float x,float y){const auto& q=quad(stage,index);float sign=0;for(int i=0;i<4;i++){const auto& a=q[i];const auto& b=q[(i+1)%4];float cross=(b[0].get<float>()-a[0].get<float>())*(y-a[1].get<float>())-(b[1].get<float>()-a[1].get<float>())*(x-a[0].get<float>());if(std::abs(cross)<.001f)continue;if(sign&&cross*sign<0)return false;sign=cross;}return true;}
inline Rect pageThumb(int p,int current=0){return {552.f+(p-current)*142.f,102.f-(p-current)*15.f,144,80};}
inline Rect expanded(int i){return {247.f+(i%4)*244.f,177.f+(i/4)*211.f,226,174};}
}

