#include "../Game/Source/ShowdownV4.hpp"
#include <cassert>
#include <iostream>
using namespace showdownv4;
int main(){
 int checks=0;auto yes=[&](bool value){++checks;assert(value);};
 yes(intersects({0,0},{10,0},{5,2},2));yes(intersects({0,0},{10,0},{12,0},2));yes(!intersects({0,0},{10,0},{12.01f,0},2));yes(intersects({0,0},{0,0},{1,0},1));
 yes(normalized(-10)==350&&normalized(370)==10);yes(clampArc(355,350,10)==355&&clampArc(180,350,10)==350);yes(std::abs(inputAngle(90,0,0,0,0)-90)<.001f);yes(inputAngle(90,1,0,0,0)==0);
 auto segment=angleSegment({0,0},0,10);yes(segment.first.x==-10&&segment.second.x==10);
 std::vector<Statement> lines{{"a",false,2,100,5,-5},{"b",false,2,100,5,-5},{"real-weak",true,1,100,5,-5},{"plain-tail",false,2,100,5,-5}};
 Group first;first.entries={{false,0},{false,1}};first.threshold=60;
 Group last;last.entries={{false,2},{false,3}};last.threshold=255;
 State s;s.reset(lines,{first,last});std::vector<Glyph> plain{{{0,0},2,0,true,false,false}},weak{{{0,0},2,0,true,true,true}};
 auto stroke=[&](const char* id){yes(s.beginStroke());return s.resolveStroke(id,{-3,0},{3,0},plain);};
 yes(s.beginStroke());yes(!s.beginStroke());yes(s.resolveStroke("a",{-3,0},{3,0},plain)==Event::PartialCut&&s.remainingHits()==1);
 yes(stroke("a")==Event::StatementCut&&s.current()->id=="b");yes(stroke("b")==Event::PartialCut);yes(stroke("b")==Event::StatementCut&&s.phase==Phase::Settling);
 for(int i=0;i<25;i++)s.tick();
 yes(s.phase==Phase::AdvanceFeedback&&s.gauge==60);s.acknowledge();yes(s.group==1&&s.current()->id=="real-weak");
 yes(s.blade("plain-tail","correct","correct",{-3,0},{3,0},weak)==Event::Air);yes(s.phase==Phase::Active);
 yes(stroke("real-weak")==Event::PartialCut&&s.phase==Phase::Active);yes(s.blade("real-weak","wrong","correct",{-3,0},{3,0},weak)==Event::WrongBlade&&s.hp==8000);
 s.acknowledge();yes(s.group==1&&s.entry==0&&s.gauge==50);
 auto invisible=weak;invisible[0].visible=false;yes(s.blade("real-weak","correct","correct",{-3,0},{3,0},invisible)==Event::Air);
 yes(s.blade("real-weak","correct","correct",{-3,0},{3,0},weak)==Event::CorrectBlade&&s.phase==Phase::Complete&&s.lastVPoint);
 // The actual weak row remains the target even when source has a later plain row.
 s.reset(lines,{first,last});s.group=1;s.startGroup(true);s.entry=1;yes(s.blade("plain-tail","correct","correct",{-3,0},{3,0},weak)==Event::Air);
 s.reset(lines,{first,last});s.group=1;s.startGroup(true);s.gauge=0;yes(s.decideGroup()==Event::GroupRetreated);s.acknowledge();yes(s.group==0);
 s.gauge=0;yes(s.decideGroup()==Event::Failed&&s.phase==Phase::Failed);
 s.reset(lines,{first,last});s.gauge=20;yes(s.decideGroup()==Event::GroupRepeated);s.acknowledge();yes(s.gauge==20&&s.entry==0);
 s.gauge=55;yes(s.decideGroup()==Event::TugStarted);float time=s.remaining;s.tugElapsed=179;for(int i=0;i<8;i++)s.tugPress();yes(s.tick(.35f)==Event::TugSucceeded&&s.remaining==time);
 s.reset(lines,{first,last});s.gauge=55;s.decideGroup();s.tugElapsed=179;yes(s.tick()==Event::Failed);
 s.reset(lines,{first,last});s.halfTug=true;s.gauge=55;s.decideGroup();for(int i=0;i<4;i++)s.tugPress();yes(s.tick()==Event::TugSucceeded);
 s.reset(lines,{first,last});s.remaining=.5f;yes(s.tick()==Event::Timeout&&s.phase==Phase::TimedOut);
 Group dialogue;dialogue.entries={{true,-1},{false,0}};s.reset(lines,{dialogue,last});yes(s.phase==Phase::Dialogue&&s.current()==nullptr);s.resumeDialogue();yes(s.current()->id=="a");
 std::cout<<"{\"passed\":true,\"checks\":"<<checks<<",\"pureStateOnly\":true,\"gameExecuted\":false}"<<std::endl;
}
