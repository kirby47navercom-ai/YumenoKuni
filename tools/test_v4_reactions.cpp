#include "../Game/Source/ExploreReactionsV4.hpp"
#include <cassert>
#include <iostream>
int main(){
 reactionv4::State s;auto& object=s["plaza:plaza_detail_planter"];
 auto first=reactionv4::hit(object);assert(first.accepted&&first.medals==1&&!first.completed&&object.remaining==2&&object.stock==1);
 reactionv4::State loaded;assert(reactionv4::restore(loaded,reactionv4::save(s)));auto& resumed=loaded.begin()->second;
 auto second=reactionv4::hit(resumed);assert(second.accepted&&second.medals==1&&!second.completed);
 auto last=reactionv4::hit(resumed);assert(last.accepted&&last.medals==0&&last.completed);
 for(int i=0;i<100;i++){auto hit=reactionv4::hit(resumed);assert(!hit.accepted&&!hit.completed&&!hit.medals);}
 auto good=reactionv4::save(loaded),bad=good;bad.begin().value()[1]=1;assert(!reactionv4::restore(loaded,bad)&&reactionv4::save(loaded)==good);
 assert(reactionv4::restore(s,good)&&s.begin()->second.remaining==0);assert(reactionv4::restore(s,hb::Json())&&s.empty());
 std::cout<<"PASS: impact stock distinct from completion XP, mid-reaction restore, exhausted re-hit blocked and invalid stock rejected\n";
}
