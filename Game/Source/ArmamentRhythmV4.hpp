#pragma once
#include "TrialRulesV4.hpp"
#include "ArmamentChartsV4.hpp"
#include <limits>

namespace armrhythm {
inline float speedForDifficulty(int){return 1.f;} // Keep the original chart/BGM beat grid.
inline std::vector<int> phaseBudgets(int chapter){
 return armcharts::phaseHp.at(std::clamp(chapter,1,6)-1);
}
struct Live {
 int id=0,slot=0,phrase=0;const armcharts::Note* source=nullptr;trialv4::Note note{};
 float spawn=0,target=0,heldSince=-1;bool done=false;float finished=-1;
 trialv4::Rating rating=trialv4::Rating::None;
};
struct Event {
 int slot;float x,y;trialv4::Rating rating;int type,button,progress,judge;
};
struct ReadView {const Live* primary=nullptr;const Live* held=nullptr;const Live* preview=nullptr;const Live* feedback=nullptr;};
struct State {
 int chapter=1,phase=0,judged=0,nextPhrase=0,deliveredPhrase=0,phasePhraseBase=0;float clock=0,speed=1;
 std::vector<Live> live;
 float moveX=0,moveY=0,scaleX=1,scaleY=1;
 double time=0;int serial=0,noteLoop=0,moveLoop=0;std::size_t noteAt=0,moveAt=0;
 int obscureIndex=-1,obscureNext=0;bool obscureActive=false;float obscureAge=0,obscureX=600,obscureY=600,obscureVX=1,obscureVY=1,obscureFrames=0;
 void obscureTick(float delta,const trialv4::Arming& health){
  if(chapter!=6)return;int damage=health.totalOpponent-health.opponent;
  constexpr int starts[]{520,900},ends[]{650,1100};
  if(!obscureActive){if(obscureNext<2&&damage>=starts[obscureNext]){obscureIndex=obscureNext++;obscureActive=true;obscureAge=0;}}
  else if(damage>=ends[obscureIndex])obscureActive=false;
  obscureAge+=delta*60;obscureFrames+=delta*60;while(obscureFrames>=1){obscureFrames-=1;obscureX+=obscureVX*10;obscureY+=obscureVY*10;if(obscureX-128<=0||1920<=obscureX+128)obscureVX*=-1;if(obscureY-128<=150||950<=obscureY+128)obscureVY*=-1;}
 }
 int motion=-1;std::size_t step=0;float motionTime=0,fromX=0,fromY=0,fromSX=1,fromSY=1;

 void start(int value){chapter=std::clamp(value,1,6);obscureIndex=-1;obscureNext=0;obscureActive=false;obscureX=obscureY=600;obscureVX=obscureVY=1;obscureFrames=0;phase=judged=serial=nextPhrase=deliveredPhrase=phasePhraseBase=0;live.clear();resetPhase();}
 void resetPhase(){for(const auto& n:live)if(n.done||n.target<=clock)deliveredPhrase=std::max(deliveredPhrase,n.phrase+1);nextPhrase=deliveredPhrase;clock=0;time=0;noteLoop=moveLoop=0;noteAt=moveAt=0;live.clear();moveX=moveY=0;scaleX=scaleY=1;motion=-1;step=0;motionTime=0;}
 const armcharts::Chart& chart()const{return armcharts::chapters[chapter-1].at(phase);}
 ReadView readView()const{
  ReadView v;
  for(const auto& n:live){
   if(n.done){if(n.rating!=trialv4::Rating::Miss&&n.rating!=trialv4::Rating::MashFailure&&clock-n.finished<.25f&&(!v.feedback||n.finished>v.feedback->finished))v.feedback=&n;continue;}
   if(n.heldSince>=0){if(!v.held||n.target>v.held->target)v.held=&n;continue;}
   if(!v.primary||n.target<v.primary->target){v.preview=v.primary;v.primary=&n;}
   else if(!v.preview||n.target<v.preview->target)v.preview=&n;
  }
  return v;
 }
 std::array<float,2> pose(const Live& n)const{
  float t=std::clamp((clock-n.spawn)/std::max(.001f,n.target-n.spawn),0.f,1.f);
  return {n.source->startScale+(n.source->endScale-n.source->startScale)*t,n.source->startRotation+(n.source->endRotation-n.source->startRotation)*t};
 }
 float textScale(const Live& n)const{
  float t=std::clamp((clock-n.spawn)/std::max(.001f,n.target-n.spawn),0.f,1.f);
  return (n.source->startTextScale+(n.source->endTextScale-n.source->startTextScale)*t)/std::max(.001f,n.source->endTextScale);
 }
 const Live* front()const {
  const Live* found=nullptr;
  for(const auto& l:live)if(!l.done&&(!found||l.target<found->target||(l.target==found->target&&l.id<found->id)))found=&l;
  return found;
 }
 void beginStep(){fromX=moveX;fromY=moveY;fromSX=scaleX;fromSY=scaleY;motionTime=0;}
 void beginMotion(int id){
  if(id<0||id>=int(armcharts::moves.size()))throw std::out_of_range("armament movement id");
  motion=id;step=0;beginStep();
 }
 void advanceMotion(float delta){
  while(motion>=0){const auto& m=armcharts::moves[motion];if(step>=m.steps.size()){motion=-1;break;}
   const auto& s=m.steps[step];float duration=std::max(0.f,s.frames/60.f),take=std::min(delta,std::max(0.f,duration-motionTime));motionTime+=take;delta-=take;
   float t=duration>0?std::clamp(motionTime/duration,0.f,1.f):1.f;
   float tx=m.kind==1?s.x-448.f:m.kind==0?0.f:fromX,ty=m.kind==1?s.y-32.f:m.kind==0?0.f:fromY;
   float sx=m.kind==2?s.x:m.kind==0?1.f:fromSX,sy=m.kind==2?s.y:m.kind==0?1.f:fromSY;
   moveX=fromX+(tx-fromX)*t;moveY=fromY+(ty-fromY)*t;scaleX=fromSX+(sx-fromSX)*t;scaleY=fromSY+(sy-fromSY)*t;
   if(motionTime+1e-6f<duration)break;
   ++step;beginStep();if(delta<=0)break;
  }
 }
 void spawn(const armcharts::Note& source,int loop){
  std::array<bool,30> used{};for(const auto& l:live)used.at(l.slot)=true;
  int slot=0;while(slot<30&&used[slot])++slot;
  if(slot==30){auto done=std::find_if(live.begin(),live.end(),[](const Live& l){return l.done;});if(done==live.end())throw std::runtime_error("armament live slot overflow");slot=done->slot;}
  live.erase(std::remove_if(live.begin(),live.end(),[&](const Live& l){return l.done&&l.slot==slot;}),live.end());
  Live l;l.id=serial++;l.slot=slot;l.phrase=nextPhrase++;l.source=&source;l.spawn=source.spawn+loop*chart().cycle;l.target=source.target+loop*chart().cycle;
  l.note.type=static_cast<trialv4::NoteType>(source.type);l.note.holdFrames=source.holdFrames;l.note.mashPower=source.mashPower;
  std::uint32_t seed=std::uint32_t(chapter)*0x9e3779b9u^std::uint32_t(source.row+1)*0x85ebca6bu^std::uint32_t(loop+1)*0xc2b2ae35u;
  seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;l.note.button=source.button==4?int(seed%4):source.button;l.note.targetSeconds=l.target;
  live.push_back(l);
 }
 void schedule(double until){
  const auto& c=chart();if(c.cycle<=0)throw std::runtime_error("armament empty cycle");
  for(;;){double n=c.notes.empty()?std::numeric_limits<double>::infinity():double(c.notes[noteAt].spawn)+noteLoop*double(c.cycle);
   double m=c.moves.empty()?std::numeric_limits<double>::infinity():double(c.moves[moveAt].first)+moveLoop*double(c.cycle);
   double next=std::min(n,m);if(next>until+1e-6)break;
   advanceMotion(float(std::max(0.0,next-time)));time=std::max(time,next);
   if(m<=n){beginMotion(c.moves[moveAt].second);if(++moveAt==c.moves.size()){moveAt=0;++moveLoop;}}
   else{spawn(c.notes[noteAt],noteLoop);if(++noteAt==c.notes.size()){noteAt=0;++noteLoop;}}
  }
  advanceMotion(float(std::max(0.0,until-time)));time=until;clock=float(time);
 }
 std::vector<Event> tick(float delta,trialv4::Arming& health,std::array<bool,4> edges,std::array<bool,4> held){
  std::vector<Event> events;
  if(!std::isfinite(delta))delta=0;
  delta=std::clamp(delta,0.f,.25f)*speed;
  int nextPhase=0,threshold=0,damage=health.totalOpponent-health.opponent;
  const auto thresholds=phaseBudgets(chapter);
  for(std::size_t i=0;i+1<thresholds.size();++i){threshold+=thresholds[i];if(damage>=threshold)nextPhase=int(i)+1;else break;}
  if(nextPhase!=phase){phase=nextPhase;resetPhase();phasePhraseBase=nextPhrase;}
  schedule(time+delta);
  for(const auto& l:live)if(l.target<=clock)deliveredPhrase=std::max(deliveredPhrase,l.phrase+1);
  auto emit=[&](Live& l,trialv4::Rating r){
   l.rating=r;l.done=l.note.done;if(l.done){l.finished=clock;++judged;}
   events.push_back({l.slot,l.source->x,l.source->y,r,l.source->type,l.note.button,l.note.progress,l.done?1:0});
  };
  for(auto& l:live)if(!l.done&&l.heldSince>=0&&!held[l.note.held]){
   int durationDelta=int(std::lround((clock-l.heldSince)*60-l.note.holdFrames));
   auto r=health.release(l.note,l.note.held,durationDelta);if(r!=trialv4::Rating::None)emit(l,r);
  }
  // A release and another note's press can both be accepted in one input snapshot.
  bool mashPressed=false; // Native anyDown is one boolean, regardless of chord size.
  for(int key=0;key<4;++key)if(edges[key]){
   Live* selected=nullptr;Live* fallback=nullptr;
   for(auto& l:live)if(!l.done&&l.heldSince<0&&!(mashPressed&&l.note.type==trialv4::NoteType::Mash)){int d=int(20+(l.target-clock)*60);if(health.window(d)==trialv4::Rating::None)continue;
    if(!fallback||std::abs(l.target-clock)<std::abs(fallback->target-clock))fallback=&l;
    if((health.fever||l.note.type==trialv4::NoteType::Mash||l.note.button==key)&&(!selected||l.target<selected->target))selected=&l;
   }
   if(!selected)selected=fallback;
   if(!selected)continue;
   auto& l=*selected;
   if(l.note.type==trialv4::NoteType::Mash)mashPressed=true;
   // Difficulty relief changes the progress per mash edge, never the source pattern.
   const int power=l.note.mashPower;if(l.note.type==trialv4::NoteType::Mash&&health.difficulty!=0&&!health.fever)l.note.mashPower*=2;
   int oldProgress=l.note.progress;auto r=health.press(l.note,key,int(20+(l.target-clock)*60));l.note.mashPower=power;
   if(l.note.held>=0&&l.heldSince<0)l.heldSince=clock;
   if(r!=trialv4::Rating::None||l.note.progress!=oldProgress)emit(l,r);
  }
  for(auto& l:live)if(!l.done){
   float late=(1+health.hitHalfWindow())/60.f;
   float limit=l.note.type==trialv4::NoteType::Mash?l.target+.4f:l.target+std::min(19.f/60,late);
   if(l.heldSince>=0)limit=l.heldSince+l.note.holdFrames/60.f+late;
   if(clock>limit){health.expire(l.note);emit(l,l.note.type==trialv4::NoteType::Mash?trialv4::Rating::MashFailure:trialv4::Rating::Miss);}
  }
  live.erase(std::remove_if(live.begin(),live.end(),[&](const Live& l){return l.done&&clock-l.finished>=.45f;}),live.end());
  return events;
 }
};
} // namespace armrhythm
