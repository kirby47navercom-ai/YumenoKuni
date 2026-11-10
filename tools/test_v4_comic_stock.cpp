#include "../Game/Source/ComicProgressV4.hpp"
#include <cassert>
#include <iostream>
#include <limits>

using comicprogressv4::State;
template<class F>bool rejects(F f){try{f();}catch(const std::invalid_argument&){return true;}return false;}
int main(){
 // Actual cached DAT availability rows for chapter6, three selector columns.
 // These exercise the mechanism only: no original-to-own story/image mapping.
 const std::vector<std::vector<int>> originalGates{{0,0,2,3,0,0,5,4},{0,2,3,4,0,1,6,5},{1,3,4,5,0,2,7,6}};
 int solvedRuns=0;
 for(const auto& thresholds:originalGates)for(int rate:{30,60,120}){
  State s;s.reset(8,{},0,1);s.configureStock(thresholds);
  for(int n=0;n<8;n++){
   int selected=-1;for(int i=7;i>=0;i--)if(!s.stockUsed(i)&&s.stockRemaining(i)==0){selected=i;break;}
   assert(selected>=0);assert(!s.stockCanConfirm(selected,true));
   if(s.stockPendingUnlock(selected)){
    assert(s.stockBeginUnlock(selected)&&!s.stockBeginUnlock(selected));
    for(int i=0;i<8;i++)assert(!s.stockCanConfirm(i));
    float elapsed=0;int opened=-1;while(opened<0){opened=s.stockTickUnlock(1.f/rate,1.f/3);elapsed+=1.f/rate;assert(elapsed<1);}
    assert(opened==selected&&elapsed>=1.f/3-0.00001f&&elapsed<=1.f/3+1.f/rate+0.00001f);
    assert(s.stockTickUnlock(1.f/rate,1.f/3)==-1);
   }
   assert(s.stockCanConfirm(selected)&&s.completed()==n);
   assert(s.place(selected,8)&&s.stockUsed(selected)&&!s.stockCanConfirm(selected));
  }
  assert(s.completed()==8);solvedRuns++;
 }
 // Own reduced boards: shuffled origin mapping must preserve retained slot0
 // eligibility and remain playable with either acquired skill state.
 int adaptedRuns=0;
 for(const std::vector<int> origins:std::vector<std::vector<int>>{{4,1,3,0,5,2},{6,3,1,7,0,5,2,4}})
  for(int column=0;column<3;column++)for(bool prefill:{false,true}){
   const int count=(int)origins.size();std::vector<int> gates;
   for(int i=0;i<count;i++)gates.push_back(origins[i]==0?0:std::max(0,i-2+column));
   State adapted;adapted.reset(count,{0},prefill?20:0,1);adapted.configureStock(gates,origins);
   for(int i=0;i<count;i++)if(origins[i]==0)assert(gates[i]==0&&adapted.stockUsed(i)==prefill);
   while(adapted.completed()<count){
    int chosen=-1;for(int i=count-1;i>=0;i--)if(!adapted.stockUsed(i)&&adapted.stockRemaining(i)==0){chosen=i;break;}
    assert(chosen>=0);
    if(adapted.stockPendingUnlock(chosen)){assert(adapted.stockBeginUnlock(chosen));assert(adapted.stockTickUnlock(.25f,.25f)==chosen);}
    assert(adapted.stockCanConfirm(chosen));assert(adapted.place(origins[chosen],count));assert(adapted.stockUsed(chosen));
   }
   adaptedRuns++;
  }
 State s;s.reset(6,{},0,1);s.configureStock({0,0,2,2,4,4});
 assert(s.stockRemaining(4)==4&&!s.stockCanConfirm(4)&&!s.stockBeginUnlock(4));
 assert(s.completed()==0&&s.place(1,6)&&s.stockRemaining(4)==3); // no hidden advancement
 assert(s.place(0,6)&&s.stockPendingUnlock(2));
 assert(s.stockBeginUnlock(2)&&!s.stockBeginUnlock(3));
 assert(s.stockTickUnlock(.1f,.4f)==-1&&!s.stockCanConfirm(0));
 assert(s.stockTickUnlock(.3f,.4f)==2&&!s.stockBeginUnlock(2));
 assert(s.stockCanConfirm(2)&&s.stockPendingUnlock(3)&&!s.stockCanConfirm(3));
 assert(!s.stockValid(-1)&&!s.stockValid(6)&&s.stockRemaining(-1)==-1&&!s.stockCanConfirm(6));
 assert(rejects([&]{s.configureStock({0,2,2,4,5});}));
 State fresh;fresh.reset(6,{},0,1);
 assert(rejects([&]{fresh.configureStock({1,1,2,3,4,5});}));
 assert(rejects([&]{fresh.configureStock({0,2,2,2,2,2});}));
 assert(rejects([&]{s.configureStock({0,0,0,0,0,6});}));
 assert(rejects([&]{s.configureStock({0,0,0,0,0,0},{0,1,2,3,4,4});}));
 assert(rejects([&]{s.stockTickUnlock(-.1f,.4f);}));
 assert(rejects([&]{s.stockTickUnlock(.1f,std::numeric_limits<float>::quiet_NaN());}));
 s.reset(6,{0},20,1);s.configureStock({0,0,2,2,4,4});assert(s.completed()==1&&s.stockUsed(0)&&s.stockRemaining(2)==1);
 assert(rejects([&]{s.configureStock({1,0,0,0,0,0});}));
 s.reset(6,{},0,1);s.configureStock({0,0,2,2,4,4},{5,3,1,4,0,2});assert(s.place(5,6)&&s.stockUsed(0)&&!s.stockUsed(5));
 s.reset(6,{},0,1);assert(s.stockThresholds.empty()&&s.stockUnlockIndex<0&&s.stockUnlockElapsed==0);
 State story;
 story.reset(15,{},0,1);
 std::vector<int> storyOrigins{0,1,2,3,4,5,-1,6,7,8,9,10,11,-1,12,13,14};
 std::vector<std::vector<int>> prereqs{{},{},{},{},{},{},{},{0,2},{0,2},{1,5},{1,5},{6,7,8},{6,7,8},{9,10,11},{9,10,11},{9,10,11},{12,13}};
 story.configureStoryStock(prereqs,storyOrigins);
 assert(story.stockCanConfirm(6)&&!story.stockUsed(6)&&story.stockRemaining(7)==2);
 assert(story.place(3,15)&&story.place(4,15)&&story.stockRemaining(7)==2);
 assert(story.place(0,15)&&story.stockRemaining(7)==1&&story.place(2,15));
 assert(story.stockBeginUnlock(7)&&story.stockTickUnlock(.5f,.5f)==7&&story.stockCanConfirm(7));
 while(story.completed()<15){
  int selected=-1;
  for(int i=int(storyOrigins.size())-1;i>=0;i--)if(storyOrigins[i]>=0&&!story.stockUsed(i)&&story.stockRemaining(i)==0){selected=i;break;}
  assert(selected>=0);
  if(story.stockPendingUnlock(selected)){assert(story.stockBeginUnlock(selected));assert(story.stockTickUnlock(.5f,.5f)==selected);}
  assert(story.stockCanConfirm(selected)&&story.place(storyOrigins[selected],15));
 }
 assert(story.completed()==15&&story.stockCanConfirm(6)&&!story.stockUsed(13));
 prereqs[0]={6};
 assert(rejects([&]{story.configureStoryStock(prereqs,storyOrigins);}));
 std::cout<<"comic stock PASS: "<<solvedRuns<<" actual-DAT-column/30-60-120 runs; "<<adaptedRuns<<" own 6/8-board difficulty/prefill runs; per-piece gates, remaining count, one selected unlock animation, held-confirm blocking, used origins, prefill, softlock/invalid rejection\n";
}
