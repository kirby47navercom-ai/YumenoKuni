#include "../Game/Source/DifficultyV4.hpp"
#include "../Game/Source/TrialRulesV4.hpp"
#include "../Game/Source/TrialResultV4.hpp"
#include <cassert>
#include <iostream>
int main(){using namespace difficultyv4;State s;assert(s.logic==1&&s.action==1);change(s,0,1);change(s,0,1);assert(s.logic==0&&s.action==1);change(s,1,-1);change(s,1,-1);assert(s.action==2);State restored;assert(restore(restored,save(s))&&save(restored)==save(s));assert(!restore(restored,{{"version",1},{"logic",3},{"action",0}})&&restored.action==2);assert(restore(restored,hb::Json())&&restored.logic==1&&restored.action==1);
 for(int d=0;d<3;d++){assert(wakDamage(2000,d)==(d==0?500:d==1?1000:2000));assert(anagramDamage(d)==(d==0?500:d==1?1000:2000));trialv4::Arming a;a.difficulty=d;a.hp=10000;a.tension=1;assert(a.apply(trialv4::Rating::Miss)==(d==0?250:d==1?500:1000));trialv4::Scrum scrum;scrum.reset(d);assert(scrum.difficulty==d);assert(anagramSpeed(d)==32*(d+1));}
 resultv4::State scores;resultv4::begin(scores,"1");resultv4::Record row;row.id="actual";row.type=3;row.initial=row.remaining=600;row.raw=resultv4::raw(3,600);row.difficulty0=0;row.difficulty1=2;assert(resultv4::capture(scores,row));resultv4::State copy;assert(resultv4::restore(copy,resultv4::save(scores))&&copy.current.records[0].difficulty0==0&&copy.current.records[0].difficulty1==2);
 std::cout<<"difficulty PASS: independent axes, wrap/cancel RAM state, save/default/corruption, WAK vs DAT damage, action armament/scrum, orb speed, actual result selectors\n";
}
