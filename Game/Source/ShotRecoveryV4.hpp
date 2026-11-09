#pragma once
#include <algorithm>
#include <cmath>
namespace shotv4 {
enum class Phase {Ready,Flight,Recovery,Release};
struct State {
 Phase phase=Phase::Ready;int frames=0,recovery=0;float fraction=0;bool laser=false;
 void reset(){*this={};}
 bool ready()const{return phase==Phase::Ready;}
 float duration()const{return (laser?7.f:14.f)/60;}
 void fire(bool beam,bool trigger){laser=beam;frames=beam?7:14;recovery=trigger?0:60;fraction=0;phase=Phase::Flight;}
 // Invalid weak-point answers use the separate fixed failure wait.
 void wrong(){phase=Phase::Recovery;frames=recovery=60;fraction=0;}
 void tick(bool down){
  if(phase==Phase::Flight){if(--frames<=0){phase=Phase::Recovery;frames=recovery;}return;}
  if(phase==Phase::Recovery){if(frames>0)--frames;if(frames<=0)phase=down?Phase::Release:Phase::Ready;return;}
  if(phase==Phase::Release&&!down)phase=Phase::Ready;
 }
 void advance(float delta,bool down){fraction+=std::max(0.f,delta)*60;int ticks=int(fraction+1e-5f);fraction=std::max(0.f,fraction-ticks);for(int i=0;i<ticks;i++)tick(down);}
};
// REA3e21f0/3e2510: frozen aim/selected ID; separate preparation and glyph passage.
struct WordFlight {
 float originX=1280,originY=360,targetX=640,targetY=360,prepare=14.f/60,duration=.5f;
 struct LetterPose {float x,y,z,scale;bool visible;float yaw,roll;};
 static WordFlight make(float x,float y,bool laser,unsigned seed){
  WordFlight f;f.targetX=x;f.targetY=y;f.originY=(350.f+float(seed%381))*2.f/3;
  f.prepare=(laser?7.f:14.f)/60;
  const float dx=(1280-x)*1.5f,dy=(f.originY-y)*1.5f;
  const float distance=std::max(std::hypot(dx,dy-330),std::hypot(dx,dy+330));
  f.duration=std::max(1.f/60,distance/((laser?40.f:20.f)*2*60));return f;
 }
 static LetterPose letter(float progress,int i,int count,float x,float y,float originY,float w=1280,float h=720){
  const float focal=h/(2*std::tan(43.6f*3.14159265f/360)),fit=std::min(w/1280.f,h/720.f),depth=.4f;
  const float span=(depth-.04f)/.028f,unit=depth/focal,tx=(x*fit-w/2)*unit,ty=(h/2-y*fit)*unit;
  const float dx=(w/2*.04f/focal-tx)/span,dy=((h/2-originY*fit)*.04f/focal-ty)/span;
  const float pitch=1.f;
  const float d=i*pitch+span-progress*((count-1)*pitch+span+pitch),z=depth-.028f*d;
  // One readable word baseline: every face shares the projected travel angle.
  const float roll=std::atan2((y-originY)*fit,std::max(1.f,w-x*fit))*180/3.14159265f;
  const float yaw=-38.f;
  return{tx+dx*d,ty+dy*d,-z,40*fit*unit/.1f,d>=0&&z>.025f,yaw,roll};
 }

};

}
