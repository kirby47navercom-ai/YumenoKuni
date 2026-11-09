#pragma once
#include "TrialRulesV4.hpp"
namespace mineopeningv4 {
struct Rect {int x,y,w,h;};
inline std::vector<int> choose(int w,int h,int percent,unsigned seed){
 if(w<1||h<1||1LL*w*h>4096)throw std::invalid_argument("mine opening dimensions");
 int count=std::clamp((w*h*std::clamp(percent,0,100)+99)/100,1,w*h);std::vector<Rect> regions{{0,0,w,h}};
 while(int(regions.size())<count){int best=0;for(int i=1;i<int(regions.size());i++){auto a=regions[i],b=regions[best];if(a.w*a.h>b.w*b.h||(a.w*a.h==b.w*b.h&&std::max(a.w,a.h)>std::max(b.w,b.h)))best=i;}
  auto a=regions[best],b=a;if(a.w>a.h){a.w/=2;b.x+=a.w;b.w-=a.w;}else{a.h/=2;b.y+=a.h;b.h-=a.h;}regions[best]=a;regions.push_back(b);
 }
 // Own reproducible RNG; native regions/count/order are preserved.
 auto next=[&](){seed=seed*1664525u+1013904223u;return seed;};std::vector<int> out;
 for(auto a:regions){int x=a.x+next()%a.w,y=a.y+next()%a.h;out.push_back(y*w+x);}return out;
}
struct State {
 std::vector<int> pending;int interval=0,settle=0;
 bool active()const{return !pending.empty()||settle>0;}
 void reset(){pending.clear();interval=settle=0;}
 void start(int w,int h,int percent,unsigned seed){reset();pending=choose(w,h,percent,seed);}
 int tick(trialv4::Mine& mine){
  if(pending.empty()){if(settle>0)--settle;return -1;}
  if(++interval<3)return -1;interval=0;int cell=pending.back();pending.pop_back();mine.cells.at(cell)=-1;if(pending.empty())settle=60;return cell;
 }
};
}
