#pragma once
#include "Debate.hpp"
#include <algorithm>
#include <cmath>
#include <optional>
#include <vector>
namespace aimskillsv4 {
struct Point {float x=0,y=0;};
struct Result {Point desired;bool active=false;};
inline float swayAmplitude(bool lv1,bool lv2){return lv2?0.f:lv1?8.f:16.f;}
struct Sway {
 Point desired{640,360};float phase=0,fraction=0;int quadrant=0;
 void reset(){*this={};}
 void resetPhase(){phase=fraction=0;quadrant=0;}
 // Native1830's path, scaled1920->1280; own60Hz, cos-wrapper inferred from joins.
 Point offset(float amplitude)const{
  if(amplitude<=0)return {};
  float radius=phase<90?amplitude*.25f*(1+phase/90):phase<=270?amplitude*.5f:amplitude*.25f*(1+(phase-180)/90);
  auto sin=[](float degree){return std::sin(degree*3.1415927f/180);};auto cos=[](float degree){return std::cos(degree*3.1415927f/180);};
  switch(quadrant){
   case 0:return {sin(90-phase)*amplitude-amplitude,-cos(90-phase)*radius};
   case 1:return {sin(phase-90)*amplitude+amplitude,-cos(phase-90)*radius};
   case 2:return {sin(phase-180)*radius,-amplitude-cos(phase-180)*amplitude};
   default:return {sin(-phase)*radius,amplitude-cos(-phase)*amplitude};
  }
 }
 Point step(float delta,bool admitted,float amplitude){
  if(admitted&&amplitude>0&&std::isfinite(delta)){
   fraction+=std::max(0.f,delta)*60;int ticks=int(fraction+1e-5f);fraction=std::max(0.f,fraction-ticks);
   for(int i=0;i<ticks;i++){phase+=2;if(phase>=360){phase-=360;quadrant=(quadrant+1)%4;}}
  }
  auto displacement=offset(amplitude);return {desired.x+displacement.x,desired.y+displacement.y};
 }
};
inline float directGain(bool down,bool up){return down?.8f:up?1.2f:1.f;}
// Own PC arrow keys stand in for a full-stick input (native10 * design2/3).
inline Point digitalAim(Point before,Point mouse,Point axis,float delta,float gain){
 if(!std::isfinite(delta)||delta<=0)return mouse;float length=std::hypot(axis.x,axis.y);if(length>1){axis.x/=length;axis.y/=length;}
 if(axis.x)mouse.x=std::clamp(before.x+axis.x*400*gain*delta,0.f,1280.f);
 if(axis.y)mouse.y=std::clamp(before.y+axis.y*400*gain*delta,-8.f/3,2168.f/3);return mouse;
}
struct Pointer {
 Point physical{-1,-1};bool moved=false,initialized=false,appliedPending=false,digital=false;
 Point sample(Point raw,Point current,bool enabled,Result& pending,bool allowPending=true,float gain=1){
  appliedPending=false;bool first=!initialized;initialized=true;auto prior=physical;moved=first||raw.x!=physical.x||raw.y!=physical.y;physical=raw;if(moved)digital=false;
  if(!first&&gain!=1){if(moved){current.x=std::clamp(current.x+(raw.x-prior.x)*gain,0.f,1280.f);current.y=std::clamp(current.y+(raw.y-prior.y)*gain,-8.f/3,2168.f/3);}else if(enabled&&pending.active&&allowPending){current=pending.desired;appliedPending=true;}}
  else if(moved||(!enabled&&!digital))current=raw;else if(enabled&&pending.active&&allowPending){current=pending.desired;appliedPending=true;}pending.active=false;return current;
 }
};
inline bool finite(Point p){return std::isfinite(p.x)&&std::isfinite(p.y);}
inline std::optional<Point> paranormalTarget(const std::vector<debate::Glyph>& glyphs){
 std::vector<Point> weak;for(const auto& g:glyphs){if(!weak.empty()&&(g.text=="\n"||g.text==u8"　"))break;if(g.text!="\r"&&g.weak)weak.push_back({g.x,g.y});}
 return weak.empty()||!finite(weak[weak.size()/2])?std::nullopt:std::optional<Point>(weak[weak.size()/2]);
}
// Own raw glyph indices are authored directly; don't substitute the ordinary
// V-point display's middle fallback for a missing native-designated target.
inline std::optional<Point> robotTarget(const debate::Line& line,const std::vector<debate::Glyph>& glyphs){
 int i=line.vpointIndex;if(i<0||i>=int(glyphs.size()))return std::nullopt;const auto& g=glyphs[i];
 if(!g.weak||!g.front||g.opacity<=.3f||!finite({g.x,g.y}))return std::nullopt;return Point{g.x,g.y};
}
inline std::vector<Point> visiblePoints(const debate::State& state){
 std::vector<Point> out;auto add=[&](int at,const std::vector<debate::Glyph>& glyphs){if(at<0||at>=int(state.lines.size())||state.broken[at])return;const auto& line=state.lines[at];if(line.kind!="weak"&&line.kind!="agree")return;if(auto p=robotTarget(line,glyphs))if(p->x>=0&&p->x<=1280&&p->y>=0&&p->y<=720)out.push_back(*p);};
 if(state.panic())for(int lane=0;lane<3;lane++)add(state.laneLine(lane),state.panicGlyphs(lane));else add(state.index,state.current());return out;
}
inline Result step(Point current,bool focused,bool direct,bool panic,bool paranormal,bool robot,const std::vector<Point>& weak,const std::vector<Point>& vpoints){
 Result out{current,false};if(!focused||direct||!finite(current))return out;
 auto toward=[&](Point p){out.desired={current.x+(p.x-current.x)*.2f,current.y+(p.y-current.y)*.2f};out.active=true;};
 if(paranormal&&!panic&&!weak.empty()&&finite(weak[0]))toward(weak[0]);
 if(robot){float best=64.f;std::optional<Point> chosen;for(auto p:vpoints){if(!finite(p))continue;float d=std::hypot(p.x-current.x,p.y-current.y);if(d<best){best=d;chosen=p;}}if(chosen)toward(*chosen);}
 // Source logical1920x1080 cursor bounds, uniformly mapped to own1280x720.
 if(out.active){out.desired.x=std::clamp(out.desired.x,0.f,1280.f);out.desired.y=std::clamp(out.desired.y,-8.f/3,2168.f/3);}
 return out;
}
}
