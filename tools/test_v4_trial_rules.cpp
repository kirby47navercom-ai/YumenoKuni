#include "../Game/Source/TrialRulesV4.hpp"
#include <cassert>
#include <iostream>
#include <numeric>
using namespace trialv4;
int main(){
 int checks=0;auto yes=[&](bool v){++checks;assert(v);};
 Mine m;m.reset(3,3,3,{0,0,1,0,0,1,2,2,1});m.undoEnabled=true;auto original=m.cells;
 yes(m.group(0).size()==4);yes(m.click(0)==Result::Removed);yes(m.cells[0]<0&&m.cells[1]<0&&m.cells[3]<0&&m.cells[4]<0);
 yes(m.cells[2]==2&&m.cells[5]==2);yes(m.cells[6]==0&&m.cells[7]==0&&m.cells[8]==1);
 yes(m.undo()==Result::Rewound&&m.cells==original);yes(m.time==18000);
 m.reset(2,2,2,{0,1,1,0});yes(m.group(0).size()==1);yes(m.click(0)==Result::Selected&&m.clicks==1);m.click(3);yes(m.click(0)==Result::Selected&&m.clicks==1);
 m.click(0);int hp=m.hp;yes(m.click(0)==Result::Removed&&m.cells[0]==-1&&m.time==17400&&m.hp==hp);
 yes(m.undo()==Result::Rewound&&m.cells[0]==0&&m.time==17400&&m.hp==hp);
 m.click(0);m.click(-1);yes(m.click(0)==Result::Selected&&m.clicks==1);
 m.reset(1,1,2,{0},100);m.safetyFirst=true;m.click(0);m.click(0);m.click(0);yes(m.time==100);m.safetyFirst=false;
 m.reset(2,1,2,{0,1});m.setImages({{7,{0,1},true,false,true}});m.cells[0]=-1;
 yes(m.submitAt(0,255)==Result::None);m.cells[1]=-1;yes(m.submitAt(0,127)==Result::None);yes(m.submitAt(0,128)==Result::Complete);
 m.tick(18000);yes(m.state==Result::Complete);
 m.reset(2,1,2,{0,1});m.hp=3000;m.setImages({{9,{0},false,false,true},{10,{1},false,true,true}});m.cells={-1,-1};
 yes(m.submitAt(0,255)==Result::Wrong&&m.hp==2000);m.submitAt(0,255);yes(m.hp==2000);m.tick(30);m.submitAt(0,255);yes(m.hp==1000);
 int before=m.time;yes(m.submitAt(1,255)==Result::Collected);m.tick(60);yes(m.time==before&&m.feedback==0);yes(!m.permanentCollectionEligible());
 m.tick(30);m.submitAt(0,255);yes(m.state==Result::Failed&&!m.permanentCollectionEligible());
 Scrum s;s.reset(1);yes(Scrum::required[1][0]==4&&Scrum::required[1][4]==15);yes(Scrum::missesAllowed[1][0]==6&&Scrum::missesAllowed[1][4]==9);
 for(int phase=0;phase<5;phase++){int count=Scrum::required[1][phase];for(int k=0;k<count;k++){auto result=s.tick(s.direction());if(k+1==count)yes(result==(phase==4?Result::Complete:Result::PhaseAdvanced));}yes(s.phase==phase+1);}
 yes(s.state==Result::Complete);s.reset();for(int k=0;k<4;k++)s.tick(s.direction());yes(s.phase==1);for(int k=0;k<6;k++)s.tick((s.direction()+1)%4);yes(s.phase==0&&s.elapsed==0&&s.success==0);
 for(int k=0;k<180;k++)s.tick();
 yes(s.state==Result::Failed);
 s.reset();s.elapsed=179;s.success=3;yes(s.tick(s.direction())==Result::PhaseAdvanced); // final permitted tick success wins
 s.reset();s.duet=true;yes(s.tick(s.direction())==Result::None&&s.success==2);yes(s.tick(s.direction())==Result::PhaseAdvanced);
 AnagramLight light;light.reset(2000);light.tick(false,true);yes(light.mode==5&&light.mental==2020); // focus requires strictly more than 2000
 light.reset(2000);light.tick(true,false);yes(light.mode==6&&light.mental==0&&light.radius>200&&light.radius<600); // spot admits equality
 light.tick(true,false);yes(light.mode==5&&light.radius>0); // exhausted spot fades rather than vanishing
 light.reset();light.tick(true,true);yes(light.mode==6&&light.mental==8000);light.tick(true,true);yes(light.mode==8&&light.mental==5985); // spot first, then upkeep + focus start
 float motion=light.tick(true,true,true);yes(light.mode==8&&light.mental==5920&&std::abs(motion-1.f/60)<.00001f); // outer upkeep once, two internal steps
 light.tick(false,true);yes(light.mode==7&&light.mental==5855&&light.radius>0);light.tick(false,false);yes(light.mode==5&&light.mental==5805);light.tick(false,false,true);yes(light.mental==5845);
 light.reset();light.tick(false,true);yes(light.mode==7&&light.mental==8000);light.tick(true,true);yes(light.mode==8&&light.mental==5950);
 light.reset();light.tick(true,false);float initialRadius=light.radius;for(int i=0;i<59;i++)light.tick(true,false);float expected=600-160000.f/(400+256);yes(std::abs(light.radius-expected)<.001f&&light.radius>initialRadius&&light.radius<600);light.tick(false,false);yes(!light.spotActive()&&light.radius>0);for(int i=0;i<20;i++)light.tick(false,false);yes(light.radius==0);
 light.reset(9990);light.tick(false,false,true);yes(light.mental==10000);yes(std::abs(light.waveOffset-(-1472+1024.f/30))<.001f);
 Anagram a;a.reset(u"가가");yes(a.orbs.size()==20&&a.at==0);yes(a.orbs[0].compartment==std::array<float,4>{{-1024,-416,256,416}});a.orbs[0].glyph=u'가';a.orbs[0].x=100;a.orbs[0].y=20;a.orbs[0].vx=5;a.orbs[0].vy=0;
 for(int i=1;i<Anagram::COUNT;i++){auto& o=a.orbs[i];auto c=o.compartment;yes(o.x>=c[0]+64&&o.x<c[0]+c[2]-64&&o.y>=c[1]+64&&o.y<c[1]+c[3]-64);}
 yes(a.orbs[1].y!=a.orbs[5].y); // samples the source range rather than fixed synthetic midpoints
 yes(a.pick(0,400,-50)==Result::Selected&&a.at==0);yes(a.advance(.25f)==Result::None&&a.at==0);auto mid=a.position(0);yes(std::abs(mid[2]-2)<.001f);
 yes(a.pick(1,400,-50)==Result::None);yes(a.advance(.25f)==Result::Correct&&a.at==1&&a.orbs[0].active&&a.orbs[0].glyph==u'가');
 yes(a.pick(0,450,-50)==Result::Selected);yes(a.advance(.5f)==Result::Complete&&a.at==2);
 a.reset(u"가나",u"가");a.orbs[0].glyph=u'가';a.pick(0,0,0);a.advance(.5f);yes(a.orbs[0].glyph==u'나'); // required unit cannot disappear
 a.reset(u"가");a.hp=2000;a.orbs[0].glyph=u'나';a.pick(0,0,0);yes(a.advance(.5f)==Result::Wrong&&a.at==0&&a.hp==1000);
 a.orbs[0].glyph=0;yes(a.pick(0,0,0)==Result::Collected&&a.at==0&&a.hp==1000&&!a.permanentCollectionEligible());
 a.orbs[0].glyph=u'가';a.pick(0,0,0);a.advance(.5f);yes(a.permanentCollectionEligible());
 Arming r;yes(r.window(19)==Rating::Critical&&r.window(21)==Rating::Critical);yes(r.window(12)==Rating::Hit&&r.window(28)==Rating::Hit);yes(r.window(11)==Rating::Miss&&r.window(29)==Rating::Miss&&r.window(0)==Rating::None);
 yes(r.apply(Rating::Miss)==0&&r.hp==10000&&r.tension==8);r.apply(Rating::Miss);r.apply(Rating::Miss);r.apply(Rating::Miss);yes(r.apply(Rating::Miss)==500&&r.hp==9500&&r.tension==10);
 r.tension=10;yes(r.apply(Rating::MashFailure)==0&&r.tension==2);yes(r.apply(Rating::MashFailure)==500&&r.tension==10);
 r.opponent=100;r.tension=10;r.apply(Rating::Critical);yes(r.opponent==90&&r.tension==14);r.apply(Rating::Hit);yes(r.opponent==85&&r.tension==16);
 Note tap{NoteType::Tap,2};yes(r.press(tap,1,20)==Rating::Miss&&tap.done);Note hold{NoteType::Hold,3};yes(r.press(hold,3,20)==Rating::Critical&&!hold.done&&hold.held==3);yes(r.release(hold,2,0)==Rating::None);yes(r.release(hold,3,0)==Rating::Critical&&hold.done);
 Note mash{NoteType::Mash,0};for(int i=0;i<9;i++)r.press(mash,0,20);yes(!mash.done&&mash.progress==9);yes(r.press(mash,0,20)==Rating::MashSuccess&&mash.done);
 yes(r.finalOrder({{0,1,2,3}})&&!r.finalOrder({{1,0,2,3}}));r.totalOpponent=570;int old=r.hp;yes(r.finalWrong()==1500&&r.hp==old-1500&&r.opponent==57&&r.tension==0);
 std::array<int,4> permutation{{0,1,2,3}};int accepted=0;
 do{FourPieces p;yes(p.pick(-1)==Result::None&&p.count==0);for(int i=0;i<3;i++){yes(p.pick(permutation[i])==Result::Selected&&p.count==i+1);yes(p.pick(permutation[i])==Result::None&&p.count==i+1);yes(p.tick()==Result::None);}yes(p.pick(permutation[3])==Result::Selected&&p.count==4);for(int i=0;i<45;i++)yes(p.tick()==Result::None&&!p.settled);auto result=p.tick();yes(p.settled&&(result==Result::Complete||result==Result::Failed));accepted+=result==Result::Complete;yes(p.pick(permutation[0])==Result::None&&p.count==4);yes(p.tick()==Result::None);}while(std::next_permutation(permutation.begin(),permutation.end()));yes(accepted==1);
 std::cout<<"{\"passed\":true,\"assertions\":"<<checks<<",\"scope\":\"pure local rules; no game/original runtime\"}"<<std::endl;
}
