#include "../Game/Source/AimSkillsV4.hpp"
#include "../Game/Source/GrowthV4.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
int main(){
 using namespace aimskillsv4;auto near=[](float a,float b){return std::abs(a-b)<.0001f;};
 assert(swayAmplitude(false,false)==16&&swayAmplitude(true,false)==8&&swayAmplitude(false,true)==0&&swayAmplitude(true,true)==0);
 Sway sway;assert(near(sway.offset(16).x,0)&&near(sway.offset(16).y,0));
 // Distinct extrema distinguish both lobes and both vertical quadrants.
 for(auto expected:std::vector<Point>{{-32,0},{32,0},{0,-32},{0,32}}){sway.phase=180;auto at=sway.offset(16);assert(near(at.x,expected.x)&&near(at.y,expected.y));sway.quadrant++;}
 sway={};sway.phase=90;auto corner=sway.offset(16);assert(near(corner.x,-16)&&near(corner.y,-8));sway.phase=300;corner=sway.offset(16);assert(near(corner.x,-8)&&corner.y>0);
 int checked=0;Sway normal,half,none;
 for(int i=0;i<1440;i++){
  auto n=normal.step(1.f/60,true,16),h=half.step(1.f/60,true,8),z=none.step(1.f/60,true,0);
  assert(near(n.x-640,2*(h.x-640))&&near(n.y-360,2*(h.y-360)));assert(z.x==640&&z.y==360&&none.phase==0&&none.quadrant==0);
  assert(normal.desired.x==640&&normal.desired.y==360&&std::abs(n.x-640)<=32.001f&&std::abs(n.y-360)<=32.001f);checked++;
 }
 assert(normal.phase==0&&normal.quadrant==0&&near(normal.fraction,0));
 debate::State panic;debate::Line row;row.text=row.word="x";row.kind="weak";row.answer="actual";panic.lines.assign(3,row);panic.broken.assign(3,false);panic.lanes={{0},{1},{2}};panic.laneAt={0,0,0};panic.laneTime={1,1,1};auto glyph=panic.panicGlyphs(0).front();Sway hitCursor;hitCursor.desired={glyph.x+32,glyph.y};hitCursor.phase=180;auto visible=hitCursor.step(0,false,16);assert(near(visible.x,glyph.x)&&panic.panicHit(visible.x,visible.y));assert(!panic.panicHit(hitCursor.desired.x,hitCursor.desired.y));
 Sway paused;paused.step(1.f/120,true,16);assert(paused.phase==0&&near(paused.fraction,.5f));
 for(int i=0;i<100;i++)paused.step(10,false,16);assert(paused.phase==0&&near(paused.fraction,.5f));paused.step(1.f/120,true,16);assert(paused.phase==2&&near(paused.fraction,0));
 for(int hz:{30,60,120}){Sway rate;for(int i=0;i<hz*12;i++)rate.step(1.f/hz,true,16);assert(rate.phase==0&&rate.quadrant==0&&near(rate.fraction,0));}
 for(int hz:{30,60,120})for(float gain:{.8f,1.f,1.2f}){
  Point desired{640,360};Pointer input;Result pending;input.sample({640,360},desired,false,pending);
  for(int i=0;i<hz*5;i++){auto mouse=input.sample({640,360},desired,false,pending);desired=digitalAim(desired,mouse,{-1,-1},1.f/hz,gain);input.digital=input.moved=true;}
  assert(desired.x==0&&near(desired.y,-8.f/3));auto stopped=input.sample({640,360},desired,false,pending);assert(stopped.x==0&&near(stopped.y,-8.f/3));
  for(int i=0;i<hz*6;i++)desired=digitalAim(desired,desired,{1,1},1.f/hz,gain);assert(desired.x==1280&&near(desired.y,2168.f/3));
  auto diagonal=digitalAim({0,0},{0,0},{1,1},1.f,gain);assert(near(std::hypot(diagonal.x,diagonal.y),400*gain));
  auto axes=digitalAim({100,100},{200,200},{1,0},.1f,gain);assert(near(axes.x,100+40*gain)&&axes.y==200);
  auto returned=input.sample({650,360},desired,false,pending,true,gain);assert(input.moved&&!input.digital&&near(returned.x,gain==1?650:std::clamp(desired.x+10*gain,0.f,1280.f)));
 }
 // SHIFT applies only to desired delta: idle sway never feeds its displacement back.
 for(float gain:{.8f,1.f,1.2f}){Sway cursor;Pointer pointer;Result pending;cursor.desired=pointer.sample({100,100},cursor.desired,false,pending,true,gain);cursor.desired=pointer.sample({150,125},cursor.desired,false,pending,true,gain);Point base=cursor.desired;
  for(int i=0;i<720;i++){cursor.desired=pointer.sample({150,125},cursor.desired,false,pending,true,gain);cursor.step(1.f/60,true,16);assert(cursor.desired.x==base.x&&cursor.desired.y==base.y);}assert(near(base.x,100+50*gain));
  pending={{500,300},true};cursor.desired=pointer.sample({150,125},cursor.desired,true,pending);assert(cursor.desired.x==500&&!pending.active&&pointer.appliedPending);cursor.resetPhase();assert(cursor.desired.x==500&&cursor.quadrant==0&&cursor.phase==0);auto actual=cursor.step(1.f/60,true,16);auto offset=cursor.offset(16);assert(near(actual.x,500+offset.x));
  cursor.reset();assert(cursor.phase==0&&cursor.quadrant==0&&cursor.fraction==0&&cursor.desired.x==640);
 }
 growthv4::J contract,skills;std::ifstream("tools/v4_growth_contract.json")>>contract;std::ifstream("data/skills.json")>>skills;growthv4::State learned;growthv4::Init(learned,contract,skills);
 learned.fp=8;assert(growthv4::Purchase(learned,"v3_calm_down_lv1",true,true).changed&&learned.fp==0);assert(!growthv4::Toggle(learned,"v3_calm_down_lv1",7,true).changed&&growthv4::Toggle(learned,"v3_calm_down_lv1",8,true).changed);
 assert(growthv4::Purchase(learned,"v3_calm_down_lv2",true,true).reason=="event-acquisition-only");std::map<std::string,int>bonds;int coins=0;
 for(int episode=1;episode<=3;episode++){auto flag=contract["entries"]["haruka:"+std::to_string(episode)]["completionFlags"][0].get<std::string>();growthv4::Observe(learned,{{flag,true}},bonds,coins);}
 assert(learned.owned.count("v3_calm_down_lv2"));assert(growthv4::Toggle(learned,"v3_calm_down_lv2",32,true).reason=="conflicting-group");growthv4::Toggle(learned,"v3_calm_down_lv1",32,true);assert(!growthv4::Toggle(learned,"v3_calm_down_lv2",15,true).changed&&growthv4::Toggle(learned,"v3_calm_down_lv2",16,true).changed);
 growthv4::State restored;growthv4::Init(restored,contract,skills);assert(growthv4::Restore(restored,growthv4::Save(learned),16)&&growthv4::Effect(restored,"calm_down_lv2")&&!growthv4::Effect(restored,"calm_down_lv1"));
 growthv4::J report={{"status","PASS"},{"scope","Own pure CALM trajectory/desired separation/clock/pause/acquisition/group/SP/save; no game player or original execution"},{"trajectoryTicks",checked},{"frameRates",{30,60,120}},{"sourceAmplitude",{24,12,0}},{"ownAmplitudeParameter",{16,8,0}},{"nativeDynamicSuppressionKnown",false},{"nativePhysicalHzMeasured",false}};std::ofstream("Game/Saved/calm-aim-20261031.json")<<report.dump(2)<<"\n";std::cout<<report.dump()<<"\n";
}
