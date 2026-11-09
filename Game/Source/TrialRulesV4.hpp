#pragma once
// Pure, rendering-independent rules traced to docs/spec/18_V3_분석/05_미니게임.md.
// No original tables, artwork, script text, RNG implementation or engine dependency.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
namespace trialv4 {
enum class Result {None, Selected, Removed, Correct, Wrong, Collected, Complete, Failed, Rewound, PhaseAdvanced, PhaseBack, Armed};

// Own deterministic quota allocator, shared with the production mine adapter.
inline std::vector<int> mineBoard(int width,int height,int n,int seed){
 if(width<1||height<1||width>22||height>11||n<2||n>4)throw std::invalid_argument("mine board dimensions");
 std::uint32_t random=std::uint32_t(seed)^0x9e3779b9u;
 auto next=[&](){random^=random<<13;random^=random>>17;random^=random<<5;return random;};
 std::vector<int> board(width*height,-1);
 for(int by=0;by<height;by+=n)for(int bx=0;bx<width;bx+=n){int w=std::min(n,width-bx),h=std::min(n,height-by),area=w*h;std::vector<int> remaining(n,area/n);for(int c=0;c<area%n;c++)++remaining[(c+seed)%n];
  auto fill=[&](auto&& self,int at)->bool{if(at==area)return true;int x=at%w,y=at/w,k=(by+y)*width+bx+x;std::array<int,4> order{0,1,2,3};for(int q=n-1;q>0;--q)std::swap(order[q],order[next()%(q+1)]);
   for(int q=0;q<n;q++){int color=order[q];if(!remaining[color])continue;if(x>=2&&board[k-1]==color&&board[k-2]==color)continue;if(y>=2&&board[k-width]==color&&board[k-2*width]==color)continue;board[k]=color;--remaining[color];if(self(self,at+1))return true;++remaining[color];board[k]=-1;}return false;};
  if(!fill(fill,0))throw std::runtime_error("mine board quota allocation");}
 return board;
}

struct MineImage {int id=-1;std::vector<int> cells;bool correct=false,collectible=false,active=true;};
struct Mine {
 int width=0,height=0,colors=3,time=18000,hp=10000,wrongDamage=1000,cooldown=0,feedback=0,last=-1,clicks=0;
 bool safetyFirst=false,undoEnabled=false;Result state=Result::None;
 std::vector<int> cells,imageAt;std::vector<MineImage> images;std::vector<std::vector<int>> history;std::set<int> collected;
 void reset(int w,int h,int n,const std::vector<int>& board,int ticks=18000){
  if(w<=0||h<=0||n<2||int(board.size())!=w*h)throw std::invalid_argument("mine dimensions");
  if(std::any_of(board.begin(),board.end(),[&](int c){return c<0||c>=n;}))throw std::invalid_argument("mine color");
  width=w;height=h;colors=n;cells=board;imageAt.assign(w*h,-1);images.clear();history.clear();collected.clear();last=-1;clicks=0;time=ticks;cooldown=feedback=0;state=Result::None;
 }
 bool playing()const{return state!=Result::Complete&&state!=Result::Failed&&feedback==0;}
 std::vector<int> adjacent(int k)const{std::vector<int> out;if(k%width)out.push_back(k-1);if(k%width+1<width)out.push_back(k+1);if(k>=width)out.push_back(k-width);if(k+width<width*height)out.push_back(k+width);return out;}
 std::vector<int> group(int cell)const {
  if(cell<0||cell>=int(cells.size())||cells[cell]<0)return{};
  int color=cells[cell];std::set<int> seen{cell};std::queue<int> q;q.push(cell);
  while(!q.empty()){int k=q.front();q.pop();for(int n:adjacent(k))if(cells[n]==color&&seen.insert(n).second)q.push(n);}return {seen.begin(),seen.end()};
 }
 Result click(int cell){
  if(!playing())return Result::None;
  if(cell<0||cell>=int(cells.size())||cells[cell]<0){last=-1;clicks=0;return Result::None;}
  auto g=group(cell);
  if(g.size()<2){if(last==cell)++clicks;else{last=cell;clicks=1;}if(clicks<3)return Result::Selected;
   history.push_back(cells);cells[cell]=-1;last=-1;clicks=0;if(!safetyFirst)time=std::max(0,time-600);if(time==0)state=Result::Failed;return Result::Removed;}
  history.push_back(cells);std::set<int> members(g.begin(),g.end()),boundary;
  for(int k:g)for(int n:adjacent(k))if(!members.count(n)&&cells[n]>=0)boundary.insert(n);
  for(int k:g)cells[k]=-1;
  for(int k:boundary)cells[k]=(cells[k]+1)%colors;
  last=-1;clicks=0;return Result::Removed;
 }
 Result undo(){if(!undoEnabled||!playing()||history.empty())return Result::None;cells=history.back();history.pop_back();last=-1;clicks=0;return Result::Rewound;}
 void setImages(const std::vector<MineImage>& value,bool allowOverlap=false){
  images=value;imageAt.assign(cells.size(),-1);std::set<int> ids;
  for(auto& image:images){if(image.id<0||!ids.insert(image.id).second)throw std::invalid_argument("mine image id");for(int cell:image.cells){if(cell<0||cell>=int(cells.size())||(!allowOverlap&&imageAt[cell]>=0))throw std::invalid_argument("mine image footprint");imageAt[cell]=image.id;}}
 }
 bool partialImage(int id)const{
  auto image=std::find_if(images.begin(),images.end(),[&](const auto& p){return p.id==id;});if(image==images.end()||!image->active||image->cells.empty())return false;bool open=false,covered=false;
  for(int cell:image->cells){open=open||cells[cell]<0;covered=covered||cells[cell]>=0;}return open&&covered;
 }
 // alpha is the selected source pixel after inverse image rotation/scale, not a bbox hit.
 Result submitAt(int cell,unsigned alpha){
  if(!playing()||cell<0||cell>=int(cells.size())||cells[cell]>=0||alpha<=127||imageAt[cell]<0)return Result::None;
  return submitImage(imageAt[cell],alpha);
 }
 bool imageExposed(int imageId)const{
  auto found=std::find_if(images.begin(),images.end(),[&](const MineImage& p){return p.id==imageId;});
  return found!=images.end()&&found->active&&std::none_of(found->cells.begin(),found->cells.end(),[&](int k){return cells[k]>=0;});
 }
 Result submitImage(int imageId,unsigned alpha){
  if(!playing()||alpha<=127)return Result::None;
  auto found=std::find_if(images.begin(),images.end(),[&](const MineImage& p){return p.id==imageId;});if(found==images.end()||!found->active)return Result::None;
  if(!imageExposed(imageId))return Result::None;
  if(found->correct){state=Result::Complete;return Result::Complete;}
  if(found->collectible){collected.insert(found->id);found->active=false;feedback=60;return Result::Collected;}
  if(cooldown==0){hp=std::max(0,hp-wrongDamage);cooldown=30;if(hp==0)state=Result::Failed;}return Result::Wrong;
 }
 void tick(int frames=1){
  for(int k=0;k<frames;k++){if(state==Result::Complete||state==Result::Failed)return;if(feedback>0){--feedback;continue;}if(cooldown>0)--cooldown;time=std::max(0,time-1);if(time==0)state=Result::Failed;}
 }
 bool permanentCollectionEligible()const{return state==Result::Complete&&!collected.empty();}
};

struct Scrum {
 static bool keywordVisible(int row,bool confirmed,bool headStart){return confirmed||(headStart&&row==0);}
 int difficulty=1,phase=0,success=0,misses=0,elapsed=0,pattern=0,patternHits=0,patternElapsed=0,patternThreshold=6,patternPeriod=180;
 bool duet=false;Result state=Result::None;std::uint32_t rng=1;
 std::array<int,10> directions{{0,0,2,2,0,0,2,2,0,0}};
 inline static constexpr int required[3][5]={{2,3,4,5,13},{4,5,6,7,15},{5,6,7,8,16}};
 inline static constexpr int missesAllowed[3][5]={{8,8,8,8,11},{6,6,6,6,9},{5,5,5,5,8}};
 inline static constexpr int limits[5]={180,180,180,180,300};
 int direction()const{return directions[pattern%10];}
 void reset(int level=1){difficulty=std::clamp(level,0,2);phase=success=misses=elapsed=pattern=patternHits=patternElapsed=0;patternThreshold=nextThreshold();state=Result::None;}
 int nextThreshold(){rng=rng*1664525u+1013904223u;return 6+int((rng>>16)%5);}
 // At most one logical direction per input snapshot. Caller translates physical keys.
 Result tick(int input=-1){
  if(state==Result::Complete||state==Result::Failed)return Result::None;
  ++elapsed;++patternElapsed;
  if(input>=0&&input<=3){if(input==direction()){int n=duet?2:1;success+=n;patternHits+=n;}else ++misses;}
  // Success wins when success/time or success/miss reach thresholds on the same tick.
  if(success>=required[difficulty][phase]){if(++phase==5){state=Result::Complete;return Result::Complete;}success=misses=elapsed=0;return Result::PhaseAdvanced;}
  if(misses>=missesAllowed[difficulty][phase]||elapsed>=limits[phase]){if(phase==0){state=Result::Failed;return Result::Failed;}--phase;success=misses=elapsed=0;return Result::PhaseBack;}
  if(patternHits>=patternThreshold||patternElapsed>=patternPeriod){pattern=duet?0:(pattern+1)%10;patternHits=patternElapsed=0;patternThreshold=nextThreshold();}
  return Result::None;
 }
};

// Source contracts are per admitted update. The host admits own 60Hz ticks;
// this is not an observation of the original scheduler's wall-clock rate.
struct AnagramLight {
 int mental=10000,mode=5;float radius=0,spotTime=0,waveOffset=-1472;
 int waveMode=2;float waveTime=0,waveFlight=0,wavePeriod=10;bool sourceWave=false;
 int maxMental=10000;float radiusMin=200,radiusMax=600,growth=256,shrink=2048;
 void configure(bool intuition,bool spark=false){radiusMin=200;radiusMax=intuition?700:600;growth=intuition?1280:256;shrink=2048;wavePeriod=spark?5:10;sourceWave=true;}
 bool spotActive()const{return mode==6||mode==8;}
 bool focusActive()const{return mode==7||mode==8;}
 void reset(int value=10000){mental=std::clamp(value,0,maxMental);mode=5;radius=spotTime=waveTime=waveFlight=0;waveOffset=-1472;waveMode=2;}
 void startSpot(){mental=std::max(0,mental-2000);radius=radiusMin;spotTime=0;}
 float tick(bool heldSpot,bool heldFocus,bool fast=false,bool arrival=false){
  if(!arrival)switch(mode){
   case 5:
    if(heldSpot&&mental>=2000){startSpot();mode=6;}
    else if(heldFocus&&mental>2000){mental-=2000;mode=7;}
    else mental=std::min(maxMental,mental+20*(fast?2:1));
    break;
   case 6:
    mental=std::max(0,mental-15);
    if(mental==0||!heldSpot)mode=5;
    else if(heldFocus&&mental>2000){mental-=2000;mode=8;}
    break;
   case 7:
    mental=std::max(0,mental-50);
    if(mental==0||!heldFocus)mode=5;
    else if(heldSpot&&mental>=2000){startSpot();mode=8;}
    break;
   case 8:
    mental=std::max(0,mental-65);
    if(mental==0||(!heldSpot&&!heldFocus))mode=5;
    else if(!heldSpot)mode=7;else if(!heldFocus)mode=6;
    break;
  }
  float seconds=(focusActive()?1.f/120:1.f/60)*(fast?2:1);
  for(int i=0;i<(fast?2:1);i++){
   if(spotActive()){spotTime+=1.f/60;float gap=radiusMax-radiusMin;radius=radiusMax-gap*gap/(gap+growth*spotTime);}
   else radius=std::max(0.f,radius-shrink/60);
   if(sourceWave&&!arrival){float step=focusActive()?1.f/120:1.f/60;waveTime+=step;
    if(waveMode==1){if(waveTime>=wavePeriod){waveTime-=wavePeriod;waveFlight=0;waveOffset=-1472;waveMode=2;}}
    else{waveFlight+=step;waveOffset=-1472+waveFlight*1024;if(waveOffset>=1472)waveMode=1;}}
  }
  if(!sourceWave){waveOffset+=1024*seconds;if(waveOffset>=1472)waveOffset=-1472;}
  return seconds;
 }
};
struct Orb {char16_t glyph=0;float x=0,y=0,vx=0,vy=0,t=0,tx=0,ty=0;std::array<float,4> compartment{};bool active=true,flying=false;};
struct Anagram {
 inline static constexpr int COUNT=20;
 // Own reproducible RNG; the source establishes inset ranges, not this RNG.
 unsigned int positionSeed=0x56334147u;
 float positionUnit(){positionSeed=1664525u*positionSeed+1013904223u;return float(positionSeed>>8)/16777216.f;}
 std::array<Orb,COUNT> orbs;std::u16string answer,candidates;std::size_t at=0;int pending=-1,hp=10000,wrongDamage=1000,spawnSerial=0;bool collected=false;Result state=Result::None;
 void reset(const std::u16string& required,const std::u16string& choices=u"",bool initialA=false){
  if(required.empty())throw std::invalid_argument("anagram answer empty");
  answer=required;candidates=choices.empty()?answer:choices;at=initialA?1:0;pending=-1;collected=false;spawnSerial=0;state=at>=answer.size()?Result::Complete:Result::None;
  for(int i=0;i<COUNT;i++){orbs[i]=Orb{};orbs[i].vx=i%2?-32.f:32.f;respawn(i);}
  layout(-1024,-416,2048,832,0,COUNT);
 }
 void layout(float x,float y,float w,float h,int first,int count){
  if(count==1){auto& o=orbs[first];o.compartment={x,y,w,h};o.x=x+64+std::max(0.f,w-128)*positionUnit();o.y=y+64+std::max(0.f,h-128)*positionUnit();return;}
  int left=count/2,right=count-left;
  if(w>=h){layout(x,y,w/2,h,first,left);layout(x+w/2,y,w/2,h,first+left,right);}
  else{layout(x,y,w,h/2,first,left);layout(x,y+h/2,w,h/2,first+left,right);}
 }
 void respawn(int slot,bool required=false){auto& o=orbs[slot];o.active=true;o.flying=false;o.t=0;
  // Guarantee the current required unit can reappear, including repeated letters.
  int pick=spawnSerial++;o.glyph=(at<answer.size()&&(required||pick%4==0))?answer[at]:candidates[std::size_t(pick)%candidates.size()];}
 Result pick(int slot,float targetX,float targetY){
  if(pending>=0||state==Result::Complete||state==Result::Failed||slot<0||slot>=COUNT||!orbs[slot].active)return Result::None;
  auto& o=orbs[slot];if(o.glyph==0){collected=true;respawn(slot);return Result::Collected;}
  pending=slot;o.flying=true;o.t=0;o.tx=targetX;o.ty=targetY;return Result::Selected;
 }
 std::array<float,3> position(int slot)const{auto& o=orbs[slot];if(!o.flying)return{o.x,o.y,1};float t=o.t,z=1-2*t+2*t*t;
  return{(o.x+o.vx*t+(o.tx-o.x-o.vx)*t*t)/z,(o.y+o.vy*t+(o.ty-o.y-o.vy)*t*t)/z,1/z};}
 // Caller passes the allowed movement delta (ordinary1/60, concentration1/120).
 Result advance(float allowedDelta){
  if(pending<0)return Result::None;
  auto& o=orbs[pending];o.t=std::min(1.f,o.t+2*std::max(0.f,allowedDelta));if(o.t<1)return Result::None;
  int slot=pending;pending=-1;bool correct=at<answer.size()&&o.glyph==answer[at];
  if(correct){++at;if(at==answer.size()){o.active=false;o.flying=false;state=Result::Complete;return Result::Complete;}respawn(slot,true);return Result::Correct;}
  hp=std::max(0,hp-wrongDamage);respawn(slot);if(hp==0)state=Result::Failed;return Result::Wrong;
 }
 bool permanentCollectionEligible()const{return state==Result::Complete&&collected;}
};

enum class Rating {Critical,Hit,Miss,MashSuccess,MashFailure,None};
enum class NoteType {Tap,Hold,Mash};
struct FourPieces {
 std::array<int,4> order{{-1,-1,-1,-1}};int count=0,transition=-15;bool settled=false;
 Result pick(int logical){
  if(logical<0||logical>3||count>=4||std::find(order.begin(),order.end(),logical)!=order.end())return Result::None;
  order[count++]=logical;return Result::Selected;
 }
 // 338280 starts at -15; 338b00 clears readiness at fps*0.5 before the outer judge.
 Result tick(){if(count<4||settled)return Result::None;if(transition++<30)return Result::None;settled=true;return order==std::array<int,4>{{0,1,2,3}}?Result::Complete:Result::Failed;}
 float blend()const{return std::clamp(transition/30.f,0.f,1.f);}
};
struct Note {NoteType type=NoteType::Tap;int button=0,progress=0,held=-1,holdFrames=60,mashPower=1;float targetSeconds=.9f;bool done=false;};
struct Arming {
 int difficulty=1,tension=10,maximumTension=20,hp=10000,maxHp=10000,opponent=100,totalOpponent=100,combo=0;
 bool fever=false,highTension=false,beatHeaven=false,wildAwakening=false;float viability=1.f;Note current{};float holdSeconds=0;
 int timingAssist=0; // Set only by the V4 armament adapter; other callers keep native timing.
 int hitHalfWindow()const{return ((difficulty==0?44:7)+timingAssist)*(beatHeaven?2:1);}
 Rating window(int d)const{if(d<1||d>(difficulty==0?120:45))return Rating::None;if(d>=19&&d<=21)return Rating::Critical;int h=hitHalfWindow();return d>=20-1-h&&d<=20+1+h?Rating::Hit:Rating::Miss;}
 int apply(Rating rating){
  if(rating==Rating::None)return 0;
  static constexpr int gain[3][5]={{6,3,-1,6,-1},{4,2,-2,4,-8},{2,1,-3,2,-10}};
  int index=rating==Rating::Critical?0:rating==Rating::Hit?1:rating==Rating::Miss?2:rating==Rating::MashSuccess?3:4;
  int enemy=index==0?(wildAwakening?20:10):index==3?10:index==1?5:0;opponent=std::max(0,opponent-enemy);
  if(index==2||index==4)combo=0;else ++combo;
  int delta=gain[std::clamp(difficulty,0,2)][index];if(highTension&&delta>=0)delta*=2;tension=std::clamp(tension+delta,0,maximumTension);
  // A normal miss does not directly damage HP. Only an emptied tension bar does.
  if(tension>0)return 0;
  tension=10;int damage=int(1000*(difficulty==0?.25f:difficulty==1?.5f:1.f)*viability);hp=std::max(0,hp-damage);return damage;
 }
 Rating press(Note& n,int button,int d){
  if(n.done||button<0||button>3)return Rating::None;
  auto r=window(d);if(r==Rating::None)return r;
  if(n.type!=NoteType::Mash&&!fever&&button!=n.button){n.done=true;apply(Rating::Miss);return Rating::Miss;}
  if(n.type==NoteType::Mash){n.progress+=n.mashPower*((difficulty==0||fever)?2:1);if(n.progress<10)return Rating::None;n.done=true;apply(Rating::MashSuccess);return Rating::MashSuccess;}
  if(n.type==NoteType::Hold){if(r==Rating::Miss){n.done=true;apply(r);}else n.held=button;return r;}
  n.done=true;apply(r);return r;
 }
 Rating release(Note& n,int button,int durationDelta){
  if(n.done||n.type!=NoteType::Hold||n.held!=button)return Rating::None;
  n.done=true;int h=hitHalfWindow();auto r=std::abs(durationDelta)<=1?Rating::Critical:std::abs(durationDelta)<=1+h?Rating::Hit:Rating::Miss;apply(r);return r;
 }
 void expire(Note& n){if(n.done)return;n.done=true;apply(n.type==NoteType::Mash?Rating::MashFailure:Rating::Miss);}
 bool finalOrder(const std::array<int,4>& selected)const{return selected==std::array<int,4>{{0,1,2,3}};}
 int finalWrong(){tension=0;int damage=int(3000*(difficulty==0?.25f:difficulty==1?.5f:1.f)*viability);hp=std::max(0,hp-damage);opponent=std::max(1,totalOpponent/10);return damage;}
};
} // namespace trialv4
