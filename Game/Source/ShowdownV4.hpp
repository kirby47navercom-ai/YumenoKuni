#pragma once
// Pure state/geometry only. Host owns source dialogue, drawing, cues and routes.
// REA contract: docs/spec/18_V3_분석/05_미니게임.md:533-578.
// V4 group/hit/duration values are explicitly own tuning in the schema adapter.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace showdownv4 {
constexpr float PI=3.14159265358979323846f;
struct Point {float x=0,y=0;};
struct Glyph {Point center;float radius=0;int index=0;bool visible=true,weak=false,vpoint=false;};
inline float normalized(float a){a=std::fmod(a,360.f);return a<0?a+360:a;}
inline bool intersects(Point a,Point b,Point p,float radius){
 float dx=b.x-a.x,dy=b.y-a.y,d=dx*dx+dy*dy;
 float t=d>0?std::clamp(((p.x-a.x)*dx+(p.y-a.y)*dy)/d,0.f,1.f):0.f;
 float x=a.x+t*dx-p.x,y=a.y+t*dy-p.y;return x*x+y*y<=radius*radius;
}
inline bool bladeIntersects(Point a,Point b,Point p,float radius,float offset){
 if(intersects(a,b,p,radius))return true;float length=std::hypot(b.x-a.x,b.y-a.y);if(length==0)return false;
 Point shift{-(b.y-a.y)*offset/length,(b.x-a.x)*offset/length};
 return intersects({a.x+shift.x,a.y+shift.y},{b.x+shift.x,b.y+shift.y},p,radius)||intersects({a.x-shift.x,a.y-shift.y},{b.x-shift.x,b.y-shift.y},p,radius);
}
inline float clampArc(float angle,float first,float last){
 angle=normalized(angle);if(last-first>=359.99f)return angle;
 first=normalized(first);last=normalized(last);
 bool inside=first<=last?(angle>=first&&angle<=last):(angle>=first||angle<=last);
 if(inside)return angle;
 auto distance=[](float a,float b){float d=std::abs(a-b);return std::min(d,360-d);};
 return distance(angle,first)<=distance(angle,last)?first:last;
}
inline float inputAngle(float previous,float axisX,float axisY,float mouseDX,float mouseDY,float first=0,float last=360,bool unrestricted=false){
 float n=std::hypot(axisX,axisY);
 if(n<=.125f)axisX=axisY=0;
 else{float m=std::min(1.f,(n-.125f)/.875f);axisX=axisX/n*m;axisY=axisY/n*m;}
 float x=axisX,y=axisY;
 if(std::abs(axisX)<.4f&&std::abs(axisY)<.4f){float a=previous*PI/180;x=75*std::cos(a)+mouseDX;y=75*std::sin(a)+mouseDY;}
 if(x==0&&y==0)return unrestricted?normalized(previous):clampArc(previous,first,last);
 float angle=std::atan2(y,x)*180/PI;return unrestricted?normalized(angle):clampArc(angle,first,last);
}
inline std::pair<Point,Point> angleSegment(Point center,float degrees,float radius=1400){
 float a=degrees*PI/180;Point d{radius*std::cos(a),radius*std::sin(a)};
 return {{center.x-d.x,center.y-d.y},{center.x+d.x,center.y+d.y}};
}

enum class Phase {Active,Dialogue,Settling,AdvanceFeedback,RepeatFeedback,RetreatFeedback,Tug,WrongFeedback,Complete,TimedOut,Failed};
enum class Event {None,Air,PartialCut,StatementCut,Dialogue,GroupAdvanced,GroupRepeated,GroupRetreated,TugStarted,TugSucceeded,WrongBlade,CorrectBlade,Timeout,Failed};
struct Statement {
 std::string id;bool blade=false,decoy=false;int requiredHits=2;float durationFrames=216,gaugeGain=5,gaugeLoss=-5;
};
struct Entry {bool dialogue=false;int statement=-1;};
struct Group {
 std::vector<Entry> entries;float threshold=60,initialGauge=50;int settleFrames=15,dwellFrames=10,tugRequired=8,tugLimit=180;
 bool forceTug=false,losePreviousOnWrong=false;
};
struct State {
 std::vector<Statement> statements;std::vector<Group> groups;std::vector<int> hits;
 Phase phase=Phase::Active;int group=0,entry=0,hp=10000,wrongBladeDamage=2000,groupFailureDamage=1000;
 float remaining=10800,initialTime=10800,gauge=50,gaugeTarget=50,entryTime=0,settling=0;
 int gaugeFrames=0,tugPresses=0,tugElapsed=0;bool strokeActive=false,lastVPoint=false,halfTug=false;float bladeOffset=8.f*(2.f/3);
 std::uint64_t strokeSerial=0,lastHitSerial=0;float angle=0;

 void reset(const std::vector<Statement>& s,const std::vector<Group>& g,int initialHp=10000,float timeFrames=10800){
  if(s.empty()||g.empty()||initialHp<=0||timeFrames<=0)throw std::invalid_argument("showdown empty setup");
  statements=s;groups=g;hits.assign(s.size(),0);hp=initialHp;remaining=initialTime=timeFrames;group=entry=0;lastVPoint=false;strokeActive=false;strokeSerial=lastHitSerial=0;angle=0;halfTug=false;bladeOffset=8.f*(2.f/3);
  for(auto& line:s)if(line.requiredHits<1||line.requiredHits>5||line.durationFrames<=0)throw std::invalid_argument("showdown hit/duration tuning");
  for(auto& current:g){if(current.entries.empty()||current.tugRequired<=0||current.tugLimit<=0)throw std::invalid_argument("showdown group tuning");for(auto& item:current.entries)if(!item.dialogue&&(item.statement<0||item.statement>=int(s.size())))throw std::invalid_argument("showdown missing statement");}
  startGroup(true);
 }
 const Group& currentGroup()const{return groups.at(group);}
 const Statement* current()const{if(group<0||group>=int(groups.size()))return nullptr;if(entry>=int(currentGroup().entries.size()))return nullptr;auto& e=currentGroup().entries[entry];return e.dialogue?nullptr:&statements[e.statement];}
 int currentIndex()const{if(!current())return -1;return currentGroup().entries[entry].statement;}
 int remainingHits()const{int i=currentIndex();return i<0?0:std::max(0,statements[i].requiredHits-hits[i]);}
 void startGroup(bool resetGauge){
  entry=0;entryTime=settling=0;gaugeFrames=0;strokeActive=false;tugElapsed=tugPresses=0;
  if(resetGauge)gauge=gaugeTarget=currentGroup().initialGauge;
  for(auto& e:currentGroup().entries)if(!e.dialogue)hits[e.statement]=0;
  phase=currentGroup().entries[0].dialogue?Phase::Dialogue:Phase::Active;
 }
 void targetGauge(float value){gaugeTarget=std::clamp(value,0.f,100.f);gaugeFrames=std::max(1,currentGroup().settleFrames);}
 void nextEntry(){
  ++entry;entryTime=0;strokeActive=false;
  if(entry>=int(currentGroup().entries.size())){phase=Phase::Settling;settling=0;}
  else phase=currentGroup().entries[entry].dialogue?Phase::Dialogue:Phase::Active;
 }
 void resumeDialogue(){if(phase!=Phase::Dialogue)throw std::logic_error("no pending authored dialogue");nextEntry();}
 // The host reads the just-completed group's afterAdvance source queue before
 // acknowledging. No authored interlude is silently turned into a cut target.
 void acknowledge(){
  if(phase==Phase::AdvanceFeedback){if(group+1>=int(groups.size()))throw std::logic_error("final group requires its actual blade");++group;startGroup(true);}
  else if(phase==Phase::RepeatFeedback)startGroup(false);
  else if(phase==Phase::RetreatFeedback){group=std::max(0,group-1);startGroup(true);}
  else if(phase==Phase::WrongFeedback){if(currentGroup().losePreviousOnWrong&&group>0)--group;startGroup(true);}
  else throw std::logic_error("showdown feedback is not pending");
 }
 bool beginStroke(){if(phase!=Phase::Active||strokeActive)return false;strokeActive=true;++strokeSerial;return true;}
 Event resolveStroke(const std::string& id,Point a,Point b,const std::vector<Glyph>& glyphs){
  if(!strokeActive)return Event::None;
  strokeActive=false;auto* line=current();
  if(!line||line->id!=id||lastHitSerial==strokeSerial)return Event::Air;
  bool hit=false;for(auto& glyph:glyphs)if(glyph.visible&&!glyph.weak&&glyph.radius>0&&intersects(a,b,glyph.center,glyph.radius)){hit=true;break;}
  if(!hit)return Event::Air;
  lastHitSerial=strokeSerial;int i=currentIndex();
  // Ordinary cuts may erase surrounding type, but may not resolve or erase
  // the protected actual weak substring. Only blade() judges that claim.
  if(line->blade){hits[i]=std::min(line->requiredHits-1,hits[i]+1);return Event::PartialCut;}
  if(++hits[i]<line->requiredHits)return Event::PartialCut;
  targetGauge(gaugeTarget+line->gaugeGain);nextEntry();return Event::StatementCut;
 }
 // 한국어판 V3(Uba6XjXj8OU 3099초) : 칼선에 글자가 다 깨져 남은 글자가 없으면 그 발언은 끝난다(Claude 2026-11-05)
 Event completeStatement(){auto* line=current();if(!line||line->blade)return Event::None;int i=currentIndex();hits[i]=line->requiredHits;targetGauge(gaugeTarget+line->gaugeGain);nextEntry();return Event::StatementCut;}
 Event blade(const std::string& id,const std::string& selected,const std::string& answer,Point a,Point b,const std::vector<Glyph>& glyphs){
  if(phase!=Phase::Active)return Event::None;
  auto* line=current();if(!line||!line->blade||line->id!=id)return Event::Air;
  bool hit=false,v=false;for(auto& glyph:glyphs)if(glyph.visible&&glyph.weak&&glyph.radius>0&&bladeIntersects(a,b,glyph.center,glyph.radius,bladeOffset)){hit=true;v=v||glyph.vpoint;}
  if(!hit)return Event::Air;
  if(selected!=answer||line->decoy){hp=std::max(0,hp-wrongBladeDamage); /* 가짜 약점(decoy)은 어떤 칼로 베어도 틀린 칼날 */phase=hp?Phase::WrongFeedback:Phase::Failed;strokeActive=false;return Event::WrongBlade;}
  lastVPoint=v;phase=Phase::Complete;strokeActive=false;return Event::CorrectBlade;
 }
 void tugPress(){if(phase==Phase::Tug)++tugPresses;}
 Event decideGroup(){
  auto& g=currentGroup();
  if(gauge>=g.threshold){phase=Phase::AdvanceFeedback;return Event::GroupAdvanced;}
  if(g.forceTug||gauge>=g.threshold-10){phase=Phase::Tug;tugElapsed=tugPresses=0;return Event::TugStarted;}
  if(gauge>0){phase=Phase::RepeatFeedback;return Event::GroupRepeated;}
  hp=std::max(0,hp-groupFailureDamage);
  if(!hp||group==0){phase=Phase::Failed;return Event::Failed;}
  phase=Phase::RetreatFeedback;return Event::GroupRetreated;
 }
 Event tick(float allowedScale=1){
  if(allowedScale<0)throw std::invalid_argument("negative showdown scale");
  if(phase==Phase::Tug){
   // This loop has its own unscaled counter; normal focus/time drain is not
   // copied into it. Reaching required presses wins on the last allowed tick.
   ++tugElapsed;int required=halfTug?std::max(1,currentGroup().tugRequired/2):currentGroup().tugRequired;
   if(tugPresses>=required){phase=Phase::AdvanceFeedback;return Event::TugSucceeded;}
   if(tugElapsed>=currentGroup().tugLimit){hp=std::max(0,hp-groupFailureDamage);phase=hp&&group>0?Phase::RetreatFeedback:Phase::Failed;return phase==Phase::Failed?Event::Failed:Event::GroupRetreated;}
   return Event::None;
  }
  if(phase!=Phase::Active&&phase!=Phase::Settling)return Event::None;
  remaining=std::max(0.f,remaining-allowedScale);if(remaining<=0){phase=Phase::TimedOut;return Event::Timeout;}
  if(gaugeFrames>0){gauge+=(gaugeTarget-gauge)/gaugeFrames;if(--gaugeFrames==0)gauge=gaugeTarget;}
  if(phase==Phase::Settling){if(gaugeFrames==0&&(settling+=allowedScale)>=currentGroup().dwellFrames)return decideGroup();return Event::None;}
  entryTime+=allowedScale;auto* line=current();if(line&&entryTime>=line->durationFrames){targetGauge(gaugeTarget+line->gaugeLoss);nextEntry();}
  return phase==Phase::Dialogue?Event::Dialogue:Event::None;
 }
};
}
