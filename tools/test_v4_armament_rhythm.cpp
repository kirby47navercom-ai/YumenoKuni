#include "../Game/Source/ArmamentRhythmV4.hpp"
#include <cassert>
#include <iostream>
#include <map>
#include <set>

using namespace trialv4;
static Arming healthFor(int chapter){Arming h;h.totalOpponent=0;for(int n:armrhythm::phaseBudgets(chapter))h.totalOpponent+=n;h.opponent=h.totalOpponent;h.hp=1000000;return h;}
static armrhythm::Live fixture(const armcharts::Note& source,int slot){
 armrhythm::Live l;l.source=&source;l.slot=slot;l.id=slot;l.phrase=slot;l.spawn=source.spawn;l.target=source.target;
 l.note.type=NoteType(source.type);l.note.button=source.button;l.note.holdFrames=source.holdFrames;l.note.mashPower=source.mashPower;return l;
}
static void inputCases(){
 const armcharts::Note hold{0,0,1,30,1,-1,0,1,500,200},tap{1,1,0,0,1,-1,0,1.5f,900,600};
 armrhythm::State s;s.start(1);s.noteLoop=s.moveLoop=100;s.live={fixture(hold,0),fixture(tap,1)};
 auto h=healthFor(1);std::array<bool,4> none{},down{};down[0]=true;
 s.tick(.25f,h,none,none);s.tick(.25f,h,none,none);s.tick(.25f,h,none,none);
 auto e=s.tick(.25f,h,down,down);assert(e.size()==1&&e[0].judge==0&&s.live[0].heldSince==1&&h.opponent==h.totalOpponent);
 s.tick(.25f,h,none,down);down={false,true,false,false};e=s.tick(.25f,h,down,down);
 assert(e.size()==2&&e[0].rating==Rating::Critical&&e[1].rating==Rating::Critical&&h.opponent==h.totalOpponent-20&&s.judged==2);
 e=s.tick(0,h,down,none);assert(e.empty()&&h.opponent==h.totalOpponent-20);

 s.start(1);s.noteLoop=s.moveLoop=100;s.live={fixture(tap,0)};h=healthFor(1);
 e=s.tick(.1f,h,{true,false,false,false},none);assert(e.empty()&&!s.live[0].done);
 for(int i=0;i<5;i++)s.tick(.25f,h,none,none);
 e=s.tick(.15f,h,{true,false,false,false},none);assert(e.size()==1&&e[0].rating==Rating::Miss&&s.judged==1);
 s.tick(.25f,h,none,none);s.tick(.25f,h,none,none);assert(s.live.empty());

 const armcharts::Note mash{2,3,2,0,2,-1,0,1,400,400};s.start(1);s.noteLoop=s.moveLoop=100;s.live={fixture(mash,0)};h=healthFor(1);
 for(int i=0;i<3;i++)s.tick(.25f,h,none,none);
 for(int i=0;i<5;i++){std::array<bool,4> edge{};edge[i%4]=true;e=s.tick(.05f,h,edge,edge);}
 assert(s.live[0].done&&s.live[0].note.progress==10&&s.judged==1&&h.opponent==h.totalOpponent-10);

 s.start(1);s.noteLoop=s.moveLoop=100;s.live={fixture(mash,0)};h=healthFor(1);
 for(int i=0;i<4;i++)s.tick(.25f,h,none,none);
 e=s.tick(0,h,{true,true,true,true},{true,true,true,true});
 assert(e.size()==1&&s.live[0].note.progress==2&&!s.live[0].done&&s.judged==0);
 // Chord deduplication is specific to Mash; another matching Tap still receives its edge.
 auto simultaneous=tap;simultaneous.target=1;s.live.push_back(fixture(simultaneous,1));
 e=s.tick(0,h,{true,true,true,true},{true,true,true,true});
 assert(e.size()==2&&s.live[0].note.progress==4&&s.live[1].done&&s.live[1].rating==Rating::Critical);

 // Unreleased holds and untouched notes expire once instead of blocking the chart.
 s.start(1);s.noteLoop=s.moveLoop=100;s.live={fixture(hold,0)};h=healthFor(1);
 for(int i=0;i<4;i++)s.tick(.25f,h,none,none);
 s.tick(0,h,{true,false,false,false},{true,false,false,false});
 for(int i=0;i<6;i++)s.tick(.25f,h,none,{true,false,false,false});
 assert(s.judged==1&&s.live[0].done&&s.live[0].rating==Rating::Miss);
 s.tick(-1,h,none,none);float old=s.clock;s.tick(std::numeric_limits<float>::quiet_NaN(),h,none,none);assert(s.clock==old);
}
static int play(int chapter,int fps,float speed=1){
 armrhythm::State s;s.start(chapter);s.speed=speed;auto h=healthFor(chapter);int peak=0,lastPhase=0,misses=0;std::map<int,std::set<int>> seen;
 std::array<bool,4> held{};float dt=1.f/fps;
 for(int frame=0;frame<fps*600&&h.opponent>0;frame++){
  std::array<bool,4> edges{};float next=s.clock+dt*speed;
  for(const auto& l:s.live)if(!l.done){
   if(l.heldSince>=0){held[l.note.held]=next-l.heldSince<l.note.holdFrames/60.f-1e-5f;continue;}
   if(l.note.type==NoteType::Mash){if(next>=l.target-.34f&&next<=l.target+.1f)edges[frame%4]=true;}
   else if(next>=l.target-1e-5f&&s.clock<l.target+dt*speed){edges[l.note.button]=true;held[l.note.button]=true;}
  }
  for(const auto& event:s.tick(dt,h,edges,held)){if(event.rating==Rating::Miss||event.rating==Rating::MashFailure)++misses;}
  peak=std::max(peak,int(std::count_if(s.live.begin(),s.live.end(),[](const auto& l){return !l.done;})));
  lastPhase=std::max(lastPhase,s.phase);
  for(const auto& l:s.live){seen[s.phase].insert(l.source->row);if(l.source->button==4)assert(l.note.button>=0&&l.note.button<4);}
 }
 for(int p=0;p<int(armencounters::chapters[chapter-1].size());p++){assert(seen[p].size()==armencounters::chapters[chapter-1][p].notes.size());}
 assert(misses==0);assert(h.opponent==0);assert(lastPhase==int(armencounters::chapters[chapter-1].size())-1);assert(peak>1&&peak<=30);return s.judged;
}
static void scheduling(){
 armrhythm::State a,b;a.start(6);b.start(6);auto ah=healthFor(6),bh=ah;
 std::array<bool,4> none{};
 for(int i=0;i<162;i++)a.tick(1.f/30,ah,none,none);
 for(int i=0;i<648;i++)b.tick(1.f/120,bh,none,none);
 assert(a.serial==b.serial&&std::abs(a.clock-b.clock)<.001f);
 assert(std::abs(a.moveX-b.moveX)<.01f&&std::abs(a.moveY-b.moveY)<.01f&&std::abs(a.scaleX-b.scaleX)<.001f);
 for(const auto& l:a.live)assert(l.source->x==armencounters::chapters[5][0].notes[l.id].x);
 armrhythm::State c;c.start(6);auto ch=healthFor(6);ch.opponent=ch.totalOpponent;for(int i=0;i<3;i++)ch.opponent-=armrhythm::phaseBudgets(6)[i];c.tick(0,ch,none,none);assert(c.phase==3&&c.clock==0&&c.live.size()==1&&c.live[0].source==&armencounters::chapters[5][3].notes[0]);
 c.start(1);c.noteLoop=c.moveLoop=100;const auto& n=armencounters::chapters[0][0].notes[0];for(int i=0;i<30;i++)c.live.push_back(fixture(n,i));
 bool overflow=false;try{c.spawn(n,0);}catch(const std::runtime_error&){overflow=true;}assert(overflow);
}
static void paceAndDamage(){
 armrhythm::State slow,fast;slow.start(2);fast.start(2);fast.speed=1.3f;auto a=healthFor(2),b=a;std::array<bool,4> none{};
 for(int i=0;i<120;i++){slow.tick(1.f/120,a,none,none);fast.tick(1.f/120,b,none,none);}
 assert(std::abs(slow.clock-1)<.001f&&std::abs(fast.clock-1.3f)<.001f);
 Arming oldHealth,newHealth;oldHealth.hp=newHealth.hp=20000;newHealth.maxHp=20000;newHealth.viability=2;oldHealth.tension=newHealth.tension=2;
 oldHealth.apply(Rating::Miss);newHealth.apply(Rating::Miss);assert(oldHealth.hp==19500&&newHealth.hp==19000);
 assert(newHealth.finalWrong()==3000&&newHealth.hp==16000);
 Arming defense;defense.hp=20000;defense.tension=2;defense.viability=.8f*2;defense.apply(Rating::Miss);assert(defense.hp==19200);
 for(int chapter=1;chapter<=6;chapter++)for(float speed:{1.3f,1.5f}){assert(play(chapter,30,speed)>0);assert(play(chapter,120,speed)>0);}
}
static void holdDeadlinesAndPhrases(){
 const armcharts::Note hold{0,0,1,30,1,-1,0,1,500,200};std::array<bool,4> none{},down{true,false,false,false};
 armrhythm::State s;s.start(1);s.noteLoop=s.moveLoop=100;s.live={fixture(hold,0)};auto h=healthFor(1);
 for(int i=0;i<4;i++){s.tick(.25f,h,none,none);}
 s.tick(.12f,h,none,none);assert(!s.live[0].done);auto e=s.tick(.02f,h,none,none);assert(e.size()==1&&e[0].rating==Rating::Miss&&s.live[0].done&&s.live[0].heldSince<0);assert(s.tick(.1f,h,none,none).empty());
 s.start(1);s.noteLoop=s.moveLoop=100;s.live={fixture(hold,0)};h=healthFor(1);for(int i=0;i<4;i++)s.tick(.25f,h,none,none);s.tick(0,h,down,down);s.tick(.25f,h,none,down);s.tick(.25f,h,none,down);s.tick(.12f,h,none,down);assert(!s.live[0].done);e=s.tick(.02f,h,none,down);assert(e.size()==1&&s.live[0].rating==Rating::Miss);
 // Only unseen previews rewind at an armor transition, never the argument's beginning.
 s.start(1);s.live={fixture(hold,0),fixture(hold,1)};s.live[0].done=true;s.live[0].phrase=7;s.live[1].phrase=8;s.nextPhrase=9;s.resetPhase();assert(s.deliveredPhrase==8&&s.nextPhrase==8);
 const auto& n=armcharts::chapters[0][0].notes[0];auto l=fixture(n,0);s.clock=l.spawn;auto p=s.pose(l);assert(std::abs(p[0]-.1f)<.001f&&p[1]==-10);s.clock=l.target;p=s.pose(l);assert(p[0]==1&&p[1]==10);
}
static void visiblePool(){
 int peak=0;
 for(int chapter=1;chapter<=6;chapter++)for(int phase=0;phase<int(armencounters::chapters[chapter-1].size());phase++)for(int difficulty=0;difficulty<3;difficulty++)for(bool holdForever:{false,true}){
  armrhythm::State s;s.start(chapter);s.phase=phase;auto h=healthFor(chapter);h.hp=1000000000;h.difficulty=difficulty;for(int i=0;i<phase;i++)h.opponent-=armrhythm::phaseBudgets(chapter)[i];
  for(int frame=0;frame<int(s.chart().cycle*3*120);frame++){
   std::array<bool,4> edges{},held{};
   if(holdForever)for(const auto& n:s.live)if(!n.done&&n.note.type==NoteType::Hold){held[n.note.button]=true;if(n.heldSince<0&&std::abs(n.target-s.clock)<.02f)edges[n.note.button]=true;}
   s.tick(1.f/120,h,edges,held);peak=std::max(peak,int(s.live.size()));assert(s.live.size()<=12);
  }
 }
 std::cout<<"all19 authored charts visible pool peak="<<peak<<"/12\n";
}

static void readableFocus(){
 for(int chapter=1;chapter<=6;chapter++)for(const auto& chart:armencounters::chapters[chapter-1]){
  for(std::size_t i=0;i<chart.notes.size();++i){const auto& n=chart.notes[i];const auto& next=chart.notes[(i+1)%chart.notes.size()];
   float gap=next.target-n.target+(i+1==chart.notes.size()?chart.cycle:0);
   assert(gap/armrhythm::speedForDifficulty(2)>=.45f-1e-5f);assert(n.target-n.spawn>=2.19f);assert(n.x==1040&&n.y==660);
   if(n.type==2)assert(n.mashPower>=4);
   if(n.type==1)for(const auto& other:chart.notes)if(&n!=&other&&other.type==1)for(int loop:{-1,0,1}){
    float at=other.target+loop*chart.cycle;assert(!(at>n.target+.001f&&at<n.target+n.holdFrames/60.f-.001f));
   }
  }
 }
 armrhythm::State s;s.start(1);s.schedule(10);const auto v=s.readView();assert(v.primary&&v.preview&&v.primary!=v.preview);assert(v.primary->target<=v.preview->target);
 assert(armrhythm::speedForDifficulty(0)==.85f&&armrhythm::speedForDifficulty(1)==1.f&&armrhythm::speedForDifficulty(2)==1.12f);
}
static void humanPaced(){
 for(int fps:{30,120})for(int difficulty:{0,1,2})for(int chapter=1;chapter<=6;chapter++){
  armrhythm::State s;s.start(chapter);s.speed=armrhythm::speedForDifficulty(difficulty);auto h=healthFor(chapter);h.difficulty=difficulty;int misses=0;
  for(int frame=0;frame<fps*900&&h.opponent>0;frame++){
   const float next=s.clock+s.speed/fps;std::array<bool,4> edges{},held{};
   for(const auto& n:s.live)if(!n.done){
    if(n.heldSince>=0){held[n.note.held]=next-n.heldSince<n.note.holdFrames/60.f;continue;}
    if(n.note.type==NoteType::Mash){const float press=n.target+(-.15f+.15f*std::min(2,n.note.progress/4))*s.speed;if(s.clock<press&&next>=press)edges[(n.note.progress/4)%4]=true;}
    else{const float press=n.target+.07f*s.speed;if(s.clock<press&&next>=press){edges[n.note.button]=true;held[n.note.button]=true;}}
   }
   for(const auto& event:s.tick(1.f/fps,h,edges,held))if(event.rating==Rating::Miss||event.rating==Rating::MashFailure)++misses;
   const auto v=s.readView();assert(!v.primary||v.primary->heldSince<0);assert(!v.held||v.held->heldSince>=0);
  }
  assert(h.opponent==0&&misses==0);
 }
 std::cout<<"human-paced70ms late presses /150ms mash spacing / all6 /30+120 / all difficulties PASS\n";
}

int main(){readableFocus();humanPaced();visiblePool();inputCases();scheduling();holdDeadlinesAndPhrases();paceAndDamage();for(int chapter=1;chapter<=6;chapter++){int a=play(chapter,30),b=play(chapter,120);assert(a>0&&b>0);std::cout<<"chapter "<<chapter<<" judged30="<<a<<" judged120="<<b<<"\n";}std::cout<<"armament rhythm PASS\n";}
