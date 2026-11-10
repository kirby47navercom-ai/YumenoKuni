#include "../Game/Source/Debate.hpp"
#include <cassert>
#include <iostream>
int main(){
 debate::State s;
 for(int i=0;i<6;i++){debate::Line l;l.text=i%2?"긴 발언이 독립된 열에서 계속 이어지는 중이다":"짧은 발언";l.kind=i==2?"weak":"plain";l.word=i==2?"짧은":"";l.answer=i==2?"owned":"";s.lines.push_back(l);}
 s.lines[2].start=0;s.broken.assign(6,false);s.silenced.assign(6,false);s.lanes={{0,1},{2,3},{4,5}};s.laneAt={0,0,0};s.laneTime={0,0,0};s.selectPanic();
 assert(s.index==2);s.tick(.4f);for(int n=0;n<3;n++)assert(!s.panicGlyphs(n).empty());
 auto g=s.panicGlyphs(1)[0];assert(s.weakHit(g.x,g.y));s.index=0;assert(s.panicHit(g.x,g.y));assert(s.index==2);
 s.laneTime[0]=100;s.tick(.1f);assert(s.laneAt[0]==1&&s.laneAt[1]==0&&s.laneAt[2]==0);assert(!s.cleared());
 s.broken[2]=true;assert(s.cleared());s.next();assert(s.laneAt[1]==1);for(int n=0;n<3;n++)assert(s.laneLine(n)>=0);
 debate::Line loud;loud.kind="noise";loud.text="shout";loud.motion=debate::Motion::Wave;loud.noiseLoud=true;
 s.lines.push_back(loud);s.noisePool=true;s.restartRows();s.time=2;
 s.advancePanicLock(0);
 assert(s.panicLockedNoise==6&&s.panicForcedLane()==0);
 s.silenced[6]=true;
 s.advancePanicLock(39.f/60.f);
 assert(s.panicForcedNoise()==-1&&s.panicForcedLane()==0);
 s.advancePanicLock(2.f/60.f);
 assert(s.panicForcedLane()==-1);
 std::cout<<"independent panic lanes, simultaneous glyphs, hit selection and exact completion PASS\n";
}
