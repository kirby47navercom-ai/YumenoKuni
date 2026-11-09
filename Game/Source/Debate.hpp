#pragma once
// 다이내믹 논스톱 논의 (V3) 규칙·연출 모델.
// 증언 글자 하나하나가 3D 경로 위에 놓이고, 원근 투영으로 화면 위치·크기·회전·앞뒤(화자 앞/뒤)가 정해진다.
#include <algorithm>
#include <array>
#include <cmath>
#include <string>
#include <vector>
#include "GlyphMetricsV4.hpp"
#include "NonstopSolidTypeV4.hpp"
#include "NonstopNoiseDirection.hpp"
namespace debate {

inline int u8len(const std::string& s){int n=0;for(unsigned char c:s)if((c&0xC0)!=0x80)++n;return n;}
// 코드포인트 단위로 자른다
inline std::vector<std::string> glyphs(const std::string& s){
 std::vector<std::string> out;
 for(size_t i=0;i<s.size();){unsigned char c=s[i];int len=c<0x80?1:c<0xE0?2:c<0xF0?3:4;out.push_back(s.substr(i,len));i+=len;}
 return out;
}
// 글자 폭 추정(em) : 한글·전각 0.86, ASCII 0.56, 공백 0.26.
// ponytail: 실제 글꼴 측정이 아닌 추정치. 어긋나면 엔진 텍스트 측정 API로 교체.
// 글꼴별 폭 계수 : 붓·손글씨 계열은 좁다
inline float spacingOf(const std::string& font){
 for(auto n:{"Dokdo","EastSeaDokdo","NanumPen","Gaegu","CuteFont","KirangHaerang"})if(font.find(n)!=std::string::npos)return .7f;
 return 1.f;
}
// 글꼴을 알면 실제 글꼴 폭(tools/glyph_metrics.py), 모르면 예전 추정치.
// 글꼴 실측 폭으로 줄 수 세기(엔진 줄바꿈 높이 추정용, 글자 단위).
inline int lineCount(const std::string& text,const std::string& font,float size,float width);
inline float em(const std::string& g,const std::string& font=""){if(!font.empty())return glyphmetrics::advance(g,font);unsigned char c=g[0];return c==' '?.26f:c<0x80?.56f:.86f;}
inline int lineCount(const std::string& text,const std::string& font,float size,float width){int lines=1;float used=0;for(const auto& g:glyphs(text)){if(g=="\n"){++lines;used=0;continue;}float a=em(g,font)*size;if(used+a>width&&used>0){++lines;used=0;}used+=a;}return lines;}

constexpr float FOCAL=900,CX=640,CY=360,SPEAKER_Z=900; // 화자(입상) 평면 깊이
constexpr float PI=3.14159265f;

// 연출 : 흐름·날아듦·화자 주위 회전·쾅·소음 일렁임·떨림·흩어진 글자 모임·카메라로 돌진·바닥에서 솟음·한 글자씩·통통 튐·나선
enum class Motion{Slide,Fly,Swirl,Slam,Wave,Shake,Assemble,Zoom,Rise,Type,Bounce,Spiral,Burst};

struct Line{std::string speaker,text,kind,word,answer;int start=0;bool lie=false;Motion motion=Motion::Slide;float spacing=1,size=1;std::string actor,pose,font;std::string id,followPose,performance,composition;float followAt=.4f;bool decoy=false;bool readable=false;float yaw=0;int shot=-1;std::string fx;bool directed=false;int vpointIndex=-1;std::string noiseGroup;int noiseRewardSeconds=0;int noiseDurability=1;float noiseAnchorX=640,noiseAnchorY=330;bool noiseAnchored=false;bool noiseLoud=false;int noiseFor=-1;}; /* noiseFor : 이 잡음이 붙은 발언 줄 번호(V3 DAT 잡음 행은 특정 발언 뒤에 붙는다) */ // Physical actor is independent of the displayed identity.

enum class Delivery{Measured,Assertive,Uneasy,Regret,Suspect};
inline Delivery delivery(const Line& line){
 if(line.performance=="regret")return Delivery::Regret;
 if(line.performance=="suspect")return Delivery::Suspect;
 if(line.performance=="assertive")return Delivery::Assertive;
 if(line.performance=="uneasy")return Delivery::Uneasy;
 if(line.performance=="measured")return Delivery::Measured;
 if(line.motion==Motion::Shake)return Delivery::Uneasy;
 if(line.motion==Motion::Slam||line.motion==Motion::Burst||line.motion==Motion::Zoom||line.fx.find("punch")!=std::string::npos)return Delivery::Assertive;
 return Delivery::Measured;
}
inline const char* courtWash(const Line& line){
 switch(delivery(line)){
  case Delivery::Regret:return "Assets/Art/ui/gpu_trial/nonstop_regret.svg";
  case Delivery::Suspect:return "Assets/Art/ui/gpu_trial/nonstop_suspect.svg";
  case Delivery::Assertive:return "Assets/Art/ui/gpu_trial/nonstop_spot.svg";
  case Delivery::Uneasy:return "Assets/Art/ui/gpu_trial/nonstop_uneasy.svg";
  default:return "Assets/Art/ui/gpu_trial/court_dim.svg";
 }
}

struct Glyph{std::string text;float x=0,y=0,scale=1,rotation=0,opacity=1,halfW=0,halfH=0,depth=900,yaw=0,pitch=0;bool front=true,weak=false,solid=false;};

inline float duration(const Line&,float);
inline float smooth(float a){a=std::clamp(a,0.f,1.f);return a*a*(3-2*a);}
// A speech has one track from entrance to exit. Layout fitting is computed from
// its final composition before animation: never clamp/re-fit halfway through it.
inline std::vector<Glyph> speech(const Line& l,float t,int lane,float base0){
 const auto gs=glyphs(l.text);if(gs.empty())return {};
 const auto& cue=l.composition;const auto tone=delivery(l);
 const bool solid=tone==Delivery::Assertive&&(l.font.empty()||l.font.find("blackhansans")!=std::string::npos)&&std::all_of(gs.begin(),gs.end(),[](const auto& c){return c==" "||solidtypev4::has(c);});
 const float base=base0*l.size,seconds=t*duration(l,base0),end=duration(l,base0);
 std::vector<int> row(gs.size()),word(gs.size());std::vector<float> width(gs.size()),off(gs.size()),weight(gs.size(),1.f);
 // Korean reference: main nouns keep their mass; attached particles are small
 // on the same baseline. Never shrink the highlighted target itself.
 {const std::array<const char*,18> tails{"에서는","으로는","에서","으로","부터","까지","처럼","한테","에게","은","는","이","가","을","를","의","도","만"};
  size_t start=0;for(size_t stop=0;stop<=gs.size();++stop){if(stop<gs.size()&&gs[stop]!=" ")continue;size_t endWord=stop;while(endWord>start&&(gs[endWord-1]=="."||gs[endWord-1]==","||gs[endWord-1]=="?"||gs[endWord-1]=="!"||gs[endWord-1]=="…"))--endWord;std::string w;for(size_t j=start;j<endWord;++j)w+=gs[j];const bool wholeWord=w=="타이가"||w=="아이"||w=="사이"||w=="같이"||w=="많이";if(!wholeWord)for(auto tail:tails){std::string s(tail);if(w.size()>s.size()&&w.compare(w.size()-s.size(),s.size(),s)==0){size_t n=glyphs(s).size();for(size_t j=endWord-n;j<endWord;++j)weight[j]=.72f;break;}}start=stop+1;}}
 std::vector<float> totals(1,0);int line=0,wi=0;size_t lastSpace=0;float beforeSpace=0;
 for(size_t i=0;i<gs.size();++i){
  const bool target=int(i)>=l.start&&int(i)<l.start+u8len(l.word)&&(l.kind=="weak"||l.kind=="agree");
  if(target)weight[i]=1.18f;
  width[i]=em(gs[i],l.font)*base*l.spacing*weight[i];
  if(gs[i]==" "){lastSpace=i;beforeSpace=totals[line];++wi;}
  if(totals[line]+width[i]>885.f&&totals[line]>0){
   size_t cut=lastSpace>0&&row[lastSpace]==line?lastSpace+1:i;
   if(cut==i){++line;totals.push_back(0);}
   else{float carry=totals[line]-beforeSpace-width[lastSpace];totals[line]=beforeSpace;++line;totals.push_back(carry);float x=0;for(size_t j=cut;j<i;++j){row[j]=line;off[j]=x;x+=width[j];}}
   lastSpace=0;
  }
  row[i]=line;word[i]=wi;off[i]=totals[line];totals[line]+=width[i];
 }
 const int lines=line+1,words=wi+1;std::vector<Glyph> out;
 for(size_t i=0;i<gs.size();++i){
  const int r=row[i],w=word[i];const float fraction=words>1?float(w)/(words-1):.5f;
  float x=off[i]+width[i]*.5f-totals[r]*.5f,y=(r-(lines-1)*.5f)*base*1.32f,z=805,roll=0;
  float size=weight[i],yaw=l.yaw,pitch=solid?-8.f:0.f;
  if(cue=="reason"){x+=(r-(lines-1)*.5f)*38;y+=x*.035f;z+=x*.08f;roll=2;}
  else if(cue=="infer"){y-=x*.13f;z+=x*.17f;roll=-7;}
  else if(cue=="qualify"){x+=r?58.f:-58.f;y+=r?14.f:-14.f;z+=r?35.f:-20.f;roll=r?2.f:-3.f;}
  else if(cue=="compare"){x+=r?80.f:-80.f;y+=r?12.f:-12.f;z+=r?35.f:-35.f;roll=r?5.f:-5.f;}
  else if(cue=="question"){y+=30.f*(2*fraction-1)*(2*fraction-1)-18;z+=70*(fraction-.5f);roll=-12+24*fraction;}
  else if(cue=="recall"){x-=65;y+=x*.045f;z+=x*.055f;roll=2.5f;}
  else if(cue=="correct"){x+=r?35.f:-35.f;z+=r?-45.f:25.f;roll=r?-4.f:2.f;}
  else if(cue=="deny"){y+=x*.095f;z-=x*.12f;roll=5;}
  else if(cue=="insist"){y-=x*.09f;z+=x*.12f;roll=-5;}
  else if(cue=="drop"){y+=x*.10f;z-=40;roll=6;}
  else if(cue=="hesitate"){y+=w*2.f;x-=35;z+=x*.05f;roll=-2;}
  else if(cue=="regret"){y+=x*.07f;z+=45;roll=4;}
  else if(cue=="suspect"){x+=r?65.f:-65.f;z+=r?40.f:-25.f;roll=r?4.f:-4.f;}
  else if(cue=="tease"){y-=22*std::sin(fraction*PI);z+=x*.13f;roll=-7+12*fraction;}
  else if(cue=="address"){y+=x*.035f;z+=x*std::sin(yaw*PI/180)*.3f;roll=yaw*.15f;}
  y+=base*(1-size)*.45f;
  Glyph g;g.text=gs[i];g.solid=solid;g.yaw=yaw;g.pitch=pitch;
  const float projection=FOCAL/z;
  g.x=CX+x*projection;g.y=CY+y*projection;g.depth=z;g.scale=projection*l.size*size;g.rotation=roll;
  g.halfW=width[i]*projection*.5f;g.halfH=base*size*projection*.58f;
  g.front=true;g.weak=(l.kind=="weak"||l.kind=="agree")&&int(i)>=l.start&&int(i)<l.start+u8len(l.word);
  out.push_back(g);
 }
 float left=1e9f,right=-1e9f,top=1e9f,bottom=-1e9f;
 for(const auto& g:out){float a=g.rotation*PI/180,c=std::abs(std::cos(a)),s=std::abs(std::sin(a)),hw=c*g.halfW+s*g.halfH,hh=s*g.halfW+c*g.halfH;left=std::min(left,g.x-hw);right=std::max(right,g.x+hw);top=std::min(top,g.y-hh);bottom=std::max(bottom,g.y+hh);}
 const float fit=std::min({1.f,980.f/std::max(1.f,right-left),320.f/std::max(1.f,bottom-top)});
 const float cx=(left+right)*.5f,cy=(top+bottom)*.5f;
 float anchorX=640,anchorY=310;
 if(cue=="reason"){anchorX=620;anchorY=300;}
 else if(cue=="qualify"){anchorX=600;anchorY=325;}
 else if(cue=="recall"){anchorX=570;anchorY=350;}
 else if(cue=="correct"){anchorX=655;anchorY=305;}
 else if(cue=="deny"||cue=="insist"){anchorX=650;anchorY=285;}
 else if(cue=="drop"){anchorY=330;}
 else if(cue=="hesitate"){anchorX=590;anchorY=355;}
 else if(cue=="regret"){anchorX=650;anchorY=375;}
 else if(cue=="suspect"){anchorX=620;anchorY=310;}
 else if(cue=="tease"){anchorX=660;anchorY=290;}
 else if(cue=="still"){anchorX=600;anchorY=360;}
 const float centerX=std::clamp(anchorX,120+(right-left)*fit*.5f,1160-(right-left)*fit*.5f);
 const float centerY=std::clamp(anchorY+(lane-1)*12,155+(bottom-top)*fit*.5f,530-(bottom-top)*fit*.5f);
 for(size_t i=0;i<out.size();++i){
  auto& g=out[i];g.x=centerX+(g.x-cx)*fit;g.y=centerY+(g.y-cy)*fit;g.scale*=fit;g.halfW*=fit;g.halfH*=fit;
  const float fraction=words>1?float(word[i])/(words-1):0;
  float onset=.05f+fraction*.34f;
  if(cue=="hesitate")onset=.05f+fraction*.72f;
  else if(cue=="correct"||cue=="compare")onset=.04f+row[i]*.17f;
  else if(cue=="deny"||cue=="insist"||cue=="drop")onset=.04f+row[i]*.10f;
  else if(cue=="still")onset=0;
  const float age=seconds-onset,in=smooth(age/(cue=="recall"?.32f:.24f)),tail=smooth((end-seconds)/.22f);
  g.opacity=in*tail;
  if(cue=="drop"){const float fall=smooth(age/.42f);g.y-=220*(1-fall);}
  else if(cue=="deny"||cue=="insist"){float u=smooth(age/.20f);g.x+=(cue=="deny"?35.f:-35.f)*(1-u);g.scale*=1+.12f*(1-u);}
  else if(cue=="question"){g.x+=(1-in)*(fraction-.5f)*65;g.y-=24*(1-in);g.rotation+=(1-in)*(fraction-.5f)*16;}
  else if(cue=="compare"){g.x+=(row[i]?48.f:-48.f)*(1-in);}
  else if(cue=="tease"){g.rotation-=9*(1-in);g.y+=12*(1-in);}
  else if(cue=="hesitate"){g.y+=8*(1-in);g.rotation+=2*std::sin(std::max(0.f,age)*34)*(1-in);}
  else if(cue=="correct"){g.x+=(row[i]?-24.f:24.f)*(1-in);}
  else if(cue=="reason"||cue=="address"){g.x-=14*(1-in);}
  else if(cue=="regret"){g.y-=10*(1-in);}
  // Continued motion has a specific direction, not a common sinusoidal bob.
  const float progress=std::clamp((seconds-.8f)/std::max(1.f,end-.8f),0.f,1.f);
  if(cue=="infer")g.x+=36*progress;
  if(cue=="recall")g.x-=24*progress;
  if(cue=="tease")g.x+=18*progress;
  if(cue=="regret")g.y+=12*progress;
  if(cue=="reason"){g.x+=(row[i]?16.f:-16.f)*progress;g.y-=6*fraction*progress;}
  if(cue=="qualify"){g.x+=(fraction-.5f)*22*progress;g.yaw+=(fraction-.5f)*6*progress;}
  if(cue=="compare"){g.x+=(row[i]?22.f:-22.f)*progress;g.yaw+=(row[i]?5.f:-5.f)*progress;}
  if(cue=="question"){g.rotation+=(fraction-.5f)*8*progress;g.y-=12*(1-fraction)*progress;}
  if(cue=="correct"||cue=="deny"||cue=="insist"){
   const float approach=(cue=="correct"?24.f:36.f)*progress,k=g.depth/(g.depth-approach);
   g.depth-=approach;g.x=centerX+(g.x-centerX)*k;g.y=centerY+(g.y-centerY)*k;g.scale*=k;g.halfW*=k;g.halfH*=k;
  }
  if(cue=="hesitate")g.x+=fraction*10*progress;
  if(cue=="suspect")g.x=centerX+(g.x-centerX)*(1-.025f*progress);
  if(cue=="tease")g.rotation+=(fraction-.5f)*5*progress;
  if(cue=="address")g.x+=10*progress;
 }
 return out;
}

// 한 증언의 t(0~1) 시점 글자 배치
inline float hash(int i,int k){float v=std::sin(i*12.9898f+k*78.233f)*43758.5453f;return v-std::floor(v);} // 글자별 고정 난수
inline std::vector<Glyph> place(const Line& l,float t,int lane,float base0){
 if(l.readable)return speech(l,t,lane,base0);
 float base=base0*l.size;
 const auto mix=[](float a,float b,float u){return a+(b-a)*u;};
 const float settle=l.readable?std::clamp(std::min((t-.12f)/.18f,(.94f-t)/.13f),0.f,1.f):0.f;
 const auto tone=l.readable?delivery(l):Delivery::Measured;
 auto gs=glyphs(l.text);
 const bool solid=l.readable&&tone==Delivery::Assertive&&std::all_of(gs.begin(),gs.end(),[](const auto& c){return c==" "||solidtypev4::has(c);});
 int weakEnd=l.start+u8len(l.word);
 // V3(영상 A 16:36·16:52) : 발언은 두세 줄로 쌓이고 낱말마다 크기가 다르다. 약점 낱말은 크게.
 // 낱말 크기는 낱말 번호로 정한 고정 난수라 매 프레임 같다(명중 판정도 같은 배치를 쓴다).
 std::vector<int> word(gs.size());{int w=0;for(size_t i=0;i<gs.size();++i){if(gs[i]==" ")++w;word[i]=w;}}
 // 읽히게 : 낱말마다 무작위 크기는 없앴다. 약점·동의 낱말만 크게(V3 영상 A 1:18 등 핵심 낱말 강조)
 // V3(한국어판 논스톱 「환기구에서 나오는 포환을…」) : 체언은 크게, 붙은 조사는 작게, 용언·부사 어절은 조금 작게. 약점·동의 낱말은 가장 크게.
 std::vector<float> part(gs.size(),1.f);{static const char* tails[]{"에서는","으로는","에서","으로","부터","까지","처럼","한테","에게","께서","마저","조차","이나","은","는","이","가","을","를","에","의","도","만","와","과","로"};
  size_t w0=0;for(size_t k=0;k<=gs.size();++k){if(k<gs.size()&&gs[k]!=" ")continue;size_t w1=k;while(w1>w0&&(gs[w1-1]=="."||gs[w1-1]==","||gs[w1-1]=="?"||gs[w1-1]=="!"||gs[w1-1]=="…"))--w1;
   std::string word;for(size_t m=w0;m<w1;++m)word+=gs[m];size_t tail=0;for(auto t:tails){std::string ts(t);if(word.size()>ts.size()&&word.compare(word.size()-ts.size(),ts.size(),ts)==0){tail=glyphs(ts).size();break;}}
   for(size_t m=w0;m<w1;++m)part[m]=tail?(m>=w1-tail?.72f:1.15f):(w1-w0>=2?.88f:1.f);w0=k+1;}}
 auto wordScale=[&](size_t i){if(l.kind=="noise")return 1.f;bool weak=int(i)>=l.start&&int(i)<weakEnd&&(l.kind=="weak"||l.kind=="agree");return weak?1.3f:part[i];};
 size_t cut=gs.size();
 if(gs.size()>16&&l.motion!=Motion::Wave&&(l.readable||l.motion!=Motion::Burst)){size_t best=gs.size();for(size_t i=1;i+1<gs.size();++i)if(gs[i]==" "&&(best==gs.size()||std::abs(int(i)-int(gs.size()/2))<std::abs(int(best)-int(gs.size()/2))))best=i;if(best<gs.size())cut=best+1;}
 std::vector<float> off(gs.size());float lineTotal[2]{0,0};
 for(size_t i=0;i<gs.size();++i){int r=i>=cut;off[i]=lineTotal[r];lineTotal[r]+=em(gs[i],l.font)*base*l.spacing*wordScale(i);}
 float total=std::max(lineTotal[0],lineTotal[1]),lineGap=cut<gs.size()?base*1.25f:0;
 float laneY=(-130.f+lane*120.f)+(cut<gs.size()?(lane==2?-base*.7f:lane==0?base*.45f:0.f):0.f), /* 두 줄 발언 : 맨 아래 자리는 올리고 맨 위 자리는 내려 화면 안에 */ /* 두 줄이면 위로 올려 아랫줄이 화면 밖·HUD 뒤로 가지 않게 */fade=std::clamp(std::min(t/.07f,(1-t)/.07f),0.f,1.f);
 std::vector<Glyph> out;
 const float statementT=t;
 for(size_t i=0;i<gs.size();++i){
  const float onset=l.readable?.025f+.22f*word[i]/std::max(1,word.back()):0.f;
  const float t=l.readable?std::clamp((statementT-onset)/(1.f-onset),0.f,1.f):statementT;
  const float settle=l.readable?std::clamp(std::min((t-.12f)/.18f,(.94f-t)/.13f),0.f,1.f):0.f;
  int r=i>=cut;float ws=wordScale(i);
  float local=off[i]+em(gs[i],l.font)*base*l.spacing*ws*.5f-lineTotal[r]*.5f+(r?base*.9f:0); // 줄 중심 기준 x, 둘째 줄은 조금 오른쪽
  float X=0,Y=laneY,Z=700,roll=0;
  const float lineY=cut<gs.size()?(r-.5f)*lineGap:0.f;
  switch(l.motion){
   case Motion::Slide:{ // 오른쪽에서 빠르게 들어와 화자 옆에 머물며 천천히 밀리다 빠진다. 원근으로 한쪽 끝이 더 멀다
    float a=1-std::pow(1-std::min(1.f,t/.14f),3),e=std::pow(std::clamp((t-.86f)/.14f,0.f,1.f),2);
    X=120+760*(1-a)-220*t-1500*e+local;Z=760+local*.35f;roll=-4;break;}
   case Motion::Fly:{  // 화자 뒤에서 카메라 앞으로 빠르게 날아든 뒤 천천히 지나간다
    float a=1-std::pow(1-std::min(1.f,t/.35f),2);
    Z=2000-1430*a+local*.2f;X=-180+260*t+local;Y=laneY*.6f-90*(1-a);roll=-12+12*a;break;}
   case Motion::Swirl:{ // 화자 주위를 한 바퀴 돈다(뒤로 지나갈 때는 입상 뒤에 그려짐)
    float R=430,a=-PI*.85f+PI*1.7f*t+local/R;X=R*std::sin(a);Z=SPEAKER_Z+150-R*std::cos(a);Y=laneY*.35f;roll=std::sin(a)*-8;break;}
   case Motion::Slam:{ // 위에서 쾅 떨어져 박힌 뒤 천천히 흐른다
    float drop=std::min(1.f,t/.12f);float bounce=drop<1?0:std::sin(std::min(1.f,(t-.12f)/.1f)*PI)*-18;
    X=local-90*t;Y=-900+(900+laneY)*(1-std::pow(1-drop,3))+bounce;Z=620;roll=-6;break;}
   case Motion::Wave:{ // 소음 : 줄마다 방향·기울기·깊이·휘는 쪽이 다르다(글로 정한 고정값이라 매 프레임 같다)
    unsigned v=2166136261u;for(unsigned char c:l.text){v^=c;v*=16777619u;}float dir=v&1?-1.f:1.f,tilt=float(int(v>>1&3)-1.5f)*6,arc=(v>>3&1?-1.f:1.f)*(40+float(v>>4&3)*18);
    const float off=float(int(v>>6&3)%3-1)*62; /* 발언 줄 위·가운데·아래 — 약점 낱말을 지나며 가린다 */
    X=dir*(-1150+(2300+total)*t)+local;Z=600;Y=laneY+off-arc*.25f*std::sin(t*PI)+5*std::sin(t*14+i*.6f);roll=tilt+2.5f*std::sin(t*9+i*.4f);break;}
   case Motion::Shake: // 떨리는 목소리
    X=1100-(2200+total)*t+local;Z=820;Y=laneY+std::sin(t*180+i*2.1f)*3;roll=std::sin(t*150+i)*3;break;
   case Motion::Assemble:{ // 사방에 흩어진 글자가 한 줄로 모인 뒤 천천히 밀려난다
    float a=1-std::pow(1-std::min(1.f,t/.3f),3);
    float sx=(hash(int(i),1)-.5f)*2600,sy=(hash(int(i),2)-.5f)*1400,sz=300+hash(int(i),3)*2600;
    X=sx+(local-60*t-sx)*a;Y=sy+(laneY-sy)*a;Z=sz+(720-sz)*a;roll=(1-a)*(hash(int(i),4)-.5f)*180;break;}
   case Motion::Zoom:{ // 화면 한가운데 먼 곳에서 카메라 쪽으로 돌진해 박힌다
    float a=std::min(1.f,t/.16f);a=1-std::pow(1-a,4);
    X=local*(.6f+.4f*a)+30*std::sin(t*3);Y=laneY*.4f;Z=3600-3080*a+120*t;roll=(1-a)*-20;break;}
   case Motion::Rise:{ // 바닥에서 솟아올라 떠오른다
    float a=1-std::pow(1-std::min(1.f,t/.25f),2);
    X=-200+300*t+local;Y=520+(laneY-520)*a-20*t;Z=840+local*-.25f;roll=4;break;}
   case Motion::Type:{ // 한 글자씩 놓인다(주저하는 말)
    float at=float(i)/std::max<size_t>(1,gs.size())*.45f;
    X=local-40*t;Y=laneY+(t<at?-30:0);Z=780;fade=std::min(fade,std::clamp((t-at)/.04f,0.f,1.f));break;}
   case Motion::Bounce: // 통통 튀며 흐른다(장난)
    X=1150-(2300+total)*t+local;Z=740;Y=laneY-std::abs(std::sin(t*9+word[i]*.9f))*12;roll=std::sin(t*9+word[i]*.9f)*3;break; /* 낱말 단위로 살짝 — 글자마다 튀면 못 읽는다 */
   case Motion::Burst:{ // V3 외침(영상 A 16:44 「N...N...No way!」) : 낱말이 화자 둘레 반원에 흩어져 하나씩 팡 하고 박힌다
    int nw=word.empty()?1:word.back()+1,w=word[i];float wStart=0,wWidth=0;
    for(size_t k=0;k<gs.size();++k){if(word[k]!=w)continue;float e2=em(gs[k],l.font)*base*l.spacing*wordScale(k);if(k<i)wStart+=e2;wWidth+=e2;}
    float a=(-62.f+124.f*(nw>1?float(w)/float(nw-1):.5f))*PI/180,tx=std::cos(a),ty=std::sin(a)*.62f; /* 화자 위 둥근 띠를 따라 왼쪽→오른쪽으로 읽힌다 */
    float along=wStart+em(gs[i],l.font)*base*l.spacing*ws*.5f-wWidth*.5f,u=std::clamp((t-.05f*float(w))/.07f,0.f,1.f);
    X=440*std::sin(a)+tx*along;Y=-250*std::cos(a)+ty*along-20*t;Z=700-160*(1-u);roll=std::atan2(ty,tx)*180/PI*.55f;fade=std::min(fade,u);break;}
   case Motion::Spiral:{ // 화면 깊은 곳에서 나선을 그리며 다가온다(연극조)
    float a=std::min(1.f,t/.5f);float ang=(1-a)*PI*3+i*.04f;float R=(1-a)*900;
    X=local+R*std::cos(ang);Y=laneY*.6f+R*.5f*std::sin(ang);Z=2600-1900*a;roll=(1-a)*360*(hash(int(i),5)>.5f?1:-1)*.1f;break;}
  }
  // V3(영상 A 1:19 「If you can't get to the hallway」) : 한 줄이 원근 있는 판 위에 놓인다 — 가까운 끝은 크고 먼 끝은 작다. 각도는 줄마다 연출표(yaw)
  if(!l.readable&&l.yaw!=0&&l.motion!=Motion::Burst&&l.motion!=Motion::Swirl&&l.motion!=Motion::Assemble){float r=l.yaw*PI/180;X+=local*(std::cos(r)-1);Z+=local*std::sin(r);}
  if(l.motion!=Motion::Burst)Y+=base*(1.f-ws)*.42f; /* 작은 글자는 큰 글자 바닥선에 맞춘다 */
  Y+=lineY;
  // V3(LP Ch1 「Shuichi / also had the receiver…」「when Rantaro / moved the bookcase…」) : 한 발언의 묶음(STX 2~3조각)마다 방향·깊이가 달라 입체로 보인다.
  // 묶음 = 두 줄로 나눈 앞·뒤. 글로 정한 고정값이라 매 프레임·명중 판정이 같다. 세로 묶음은 7자 이하만(화면 밖으로 안 나가게)
  if(!l.readable&&cut<gs.size()&&l.motion!=Motion::Burst&&l.motion!=Motion::Wave&&l.motion!=Motion::Swirl&&l.motion!=Motion::Assemble&&l.motion!=Motion::Spiral){
   unsigned hv=2166136261u;for(unsigned char c:l.text){hv^=c;hv*=16777619u;}int style=int(hv%3u);
   const int len0=int(cut),len1=int(gs.size()-cut);
   if(style==0&&len0>7)style=1;if(style==2&&len1>7)style=1;
   float along=off[i]+em(gs[i],l.font)*base*l.spacing*ws*.5f-lineTotal[r]*.5f;
   if(style==0&&r==0){X+=-local-lineTotal[1]*.5f-base*.55f;Y+=-lineY+.5f*lineGap+along*1.02f-lineTotal[0]*.22f;Z-=60;}        /* 앞 묶음이 세로로 선다 */
   else if(style==2&&r==1){X+=-local-base*.9f+lineTotal[0]*.5f+base*.55f;Y+=-lineY-.5f*lineGap+along*1.02f+lineTotal[1]*.5f;Z+=50;} /* 뒤 묶음이 세로로 떨어진다 */
   else if(style==1){if(r==0){Y+=-local*.12f-base*.45f;roll+=-7;Z-=55;}else{Y+=base*.3f;Z+=45;roll+=2;}}                                      /* 앞 묶음은 비스듬히 앞으로, 뒤 묶음은 뒤로 */
  }
  if(l.readable){
   const float angle=std::clamp(l.yaw,-22.f,22.f)*PI/180.f;
   const float phase=std::clamp((t-.12f-word[i]*.012f)/.22f,0.f,1.f);
   const float strike=tone==Delivery::Assertive?std::sin(phase*PI)*(1-phase):0.f;
   const float sag=(tone==Delivery::Uneasy||tone==Delivery::Regret)?(1-phase)*16.f+10.f*std::sin(t*PI):0.f;
   const float drift=(tone==Delivery::Uneasy?45.f:105.f)*(.5f-t);
   const float rise=10.f*std::sin(t*PI)+22.f*strike-sag;
   const float phrase=word[i]*.84f;
   const float spread=(l.motion==Motion::Swirl||l.motion==Motion::Spiral||l.motion==Motion::Burst)?34.f:14.f;
   const float tilt=std::sin(phrase+float(l.motion)*.63f);
   const float offset=spread*tilt*std::sin(phase*PI*.5f);
   const float slope=(r?-.08f:.08f)*std::sin(float(l.motion)+lane);
   // Retain an authored phrase composition during the readable interval.
   // Group transforms share a local baseline: glyphs never jitter independently.
   float groupX=0,groupY=0,groupZ=0,groupRoll=0;
   if(l.composition=="split"){
    groupX=r?95.f:-95.f;groupY=r?52.f:-58.f;
    groupZ=r?65.f:-45.f;groupRoll=r?5.f:-8.f;
   }else if(l.composition=="steps"){
    groupY=(word[i]%3-1)*31.f+12.f*std::sin(t*PI);
    groupZ=(word[i]%3-1)*46.f;groupRoll=(word[i]%3-1)*5.f;
   }else if(l.composition=="diagonal"){
    groupY=-local*.19f+(r?35.f:-22.f);groupZ=-local*.12f;
    groupRoll=-9.f;
   }else if(l.composition=="ribbon"){
    groupY=std::sin(phrase*.6f)*24.f;groupZ=local*.12f;
    groupRoll=std::cos(phrase*.6f)*4.f;
   }
   X=mix(X,local*std::cos(angle)+drift+(r?1.f:-1.f)*spread*.4f+groupX,settle);
   Y=mix(Y,(-68.f+lane*63.f)+lineY-rise+offset+local*slope+groupY,settle);
   Z=mix(Z,std::clamp(730.f+std::clamp(local*std::sin(angle),-100.f,100.f)-140.f*strike+offset*1.2f+groupZ,500.f,850.f),settle);
   roll=mix(roll,(lane-1)*3.f+3.f*strike-2.f*sag/26.f+tilt*spread*.18f+groupRoll,settle);
   fade=std::max(fade,settle);
  }
  Glyph g;g.text=gs[i];g.solid=solid;g.yaw=solid?l.yaw+8.f*std::sin(t*PI):0.f;g.pitch=solid?-10.f+6.f*std::sin(t*PI):0.f;
  float s=FOCAL/std::max(400.f,Z); // 최대 2.25배 : 너무 가까운 글자는 화면을 덮고 렌더링을 막는다
  g.x=CX+X*s;g.y=CY+Y*s;g.scale=s*l.size*ws;g.depth=std::max(400.f,Z);g.rotation=roll;g.opacity=fade;
  if(l.readable)g.opacity*=std::clamp(t/.07f,0.f,1.f);
  g.front=Z<SPEAKER_Z;g.weak=(l.kind=="weak"||(l.kind=="agree"&&!l.answer.empty()))&&int(i)>=l.start&&int(i)<weakEnd;
  g.halfW=em(gs[i],l.font)*base*l.spacing*ws*s*.5f;g.halfH=base*ws*s*.62f;
  out.push_back(g);
 }
 // 줄 전체가 화면 안(이름표 아래 ~ 언령 판 위)에 들어오게 통째로 민다 — 잡음·외침은 제외
 if(l.kind!="noise"&&l.motion!=Motion::Burst&&!out.empty()&&(!l.readable||statementT>=.48f)){float top=1e9f,bot=-1e9f;for(const auto& g:out){top=std::min(top,g.y-g.halfH);bot=std::max(bot,g.y+g.halfH);}
  float dy=top<96?96-top:bot>620?620-bot:0;dy*=std::clamp((t-.12f)/.2f,0.f,1.f); /* 들어오는 움직임(쾅·솟음)은 그대로 두고 자리 잡을 때만 */if(dy!=0)for(auto& g:out)g.y+=dy;}
 if(l.readable&&!out.empty()&&statementT>=.48f){
  float left=1e9f,right=-1e9f,top=1e9f,bottom=-1e9f;
  for(const auto& g:out){left=std::min(left,g.x-g.halfW);right=std::max(right,g.x+g.halfW);top=std::min(top,g.y-g.halfH);bottom=std::max(bottom,g.y+g.halfH);}
  const float fit=std::min({1.f,1050.f/std::max(1.f,right-left),390.f/std::max(1.f,bottom-top)});
  const float cx=(left+right)*.5f,cy=(top+bottom)*.5f,hw=(right-left)*fit*.5f,hh=(bottom-top)*fit*.5f;
  const float tx=std::clamp(cx,95.f+hw,1185.f-hw),ty=std::clamp(cy,130.f+hh,550.f-hh);
  for(auto& g:out){g.x=mix(g.x,tx+(g.x-cx)*fit,settle);g.y=mix(g.y,ty+(g.y-cy)*fit,settle);const float f=mix(1.f,fit,settle);g.scale*=f;g.halfW*=f;g.halfH*=f;}
 }
 return out;
}

inline float duration(const Line& l,float base){
 float w=0;base*=l.size;for(auto& g:glyphs(l.text))w+=em(g,l.font)*base*l.spacing;
 switch(l.motion){case Motion::Swirl:return 7.5f;case Motion::Slam:case Motion::Zoom:case Motion::Assemble:case Motion::Burst:case Motion::Type:case Motion::Spiral:return 5.5f+w/500;case Motion::Fly:return 5.f;case Motion::Rise:return 6.f;default:return 5.f+w/320;}
}

inline bool inside(const Glyph& g,float x,float y,float pad,float* hitDepth=nullptr){
 if(g.solid||g.yaw!=0||g.pitch!=0){
  // Intersect the camera ray with the rendered front plane, then undo its
  // complete rotation. The target is not the old screen-aligned rectangle.
  const float a=g.rotation*PI/180,b=g.yaw*PI/180,c=g.pitch*PI/180;
  const float ca=std::cos(a),sa=std::sin(a),cb=std::cos(b),sb=std::sin(b),cc=std::cos(c),sc=std::sin(c);
  const std::array<float,3> u{ca*cb,sa*cb,-sb},v{ca*sb*sc-sa*cc,sa*sb*sc+ca*cc,cb*sc},n{ca*sb*cc+sa*sc,sa*sb*cc-ca*sc,cb*cc};
  const std::array<float,3> ray{(x-CX)/FOCAL,(y-CY)/FOCAL,1},center{(g.x-CX)*g.depth/FOCAL,(g.y-CY)*g.depth/FOCAL,g.depth};
  auto dot=[](const auto& p,const auto& q){return p[0]*q[0]+p[1]*q[1]+p[2]*q[2];};
  const float den=dot(n,ray);if(std::abs(den)<.00001f)return false;float z=dot(n,center)/den;if(z<=0)return false;
  std::array<float,3> d{z*ray[0]-center[0],z*ray[1]-center[1],z-center[2]};
  bool hit=std::abs(dot(u,d))<=(g.halfW+pad)*g.depth/FOCAL&&std::abs(dot(v,d))<=(g.halfH+pad)*g.depth/FOCAL;if(hit&&hitDepth)*hitDepth=z;return hit;
 }
const float a=g.rotation*PI/180.f,c=std::cos(a),s=std::sin(a),dx=x-g.x,dy=y-g.y;bool hit=std::abs(c*dx+s*dy)<=g.halfW+pad&&std::abs(c*dy-s*dx)<=g.halfH+pad;if(hit&&hitDepth)*hitDepth=g.depth;return hit;}

struct PanicTypeTransform {float scale,x,y;};
inline constexpr PanicTypeTransform PANIC_TYPE[3]={{.80f,38.f,-74.f},{.88f,0.f,-2.f},{.80f,-24.f,-20.f}};
inline const std::vector<std::vector<std::vector<float>>> PANIC_PANES={
 {{0,0},{.592f,0},{.195f,1},{0,1}},
 {{.598f,0},{1,0},{1,1},{.961f,1},{.452f,.367f}},
 {{.449f,.374f},{.955f,1},{.202f,1}}};
inline std::array<float,2> panicViewport(float width,float height){
 const float fit=std::min(width/1280.f,height/720.f);
 return fit>0?std::array<float,2>{width/fit,height/fit}:std::array<float,2>{1280.f,720.f};
}
inline int panicPaneAt(float x,float y,float width=1280.f,float height=720.f){
 x/=width;y/=height;
 for(int lane=0;lane<3;++lane){
  const auto& pane=PANIC_PANES[lane];bool inside=true;
  for(size_t i=0;i<pane.size();++i){
   const auto& a=pane[i];const auto& b=pane[(i+1)%pane.size()];
   if((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])<0){inside=false;break;}
  }
  if(inside)return lane;
 }
 return -1;
}
struct State{
 std::vector<Line> lines;
 std::vector<bool> broken,silenced;std::vector<int> noiseDamage;
 struct NoiseDebris{std::vector<Glyph> glyphs;float age=0;};std::vector<NoiseDebris> noiseDebris;
 void shatterNoise(int at){if(panic()||!line().readable)return;auto pool=noiseIndices();for(int slot=0;slot<int(pool.size());++slot)if(pool[slot]==at){auto gs=noiseGlyphs(at,slot);if(!gs.empty()){if(noiseDebris.size()==3)noiseDebris.erase(noiseDebris.begin());noiseDebris.push_back({gs,0});}break;}}
 void shatterNoiseTransition(int at,const std::vector<Glyph>& before){
  if(panic()||!line().readable||before.empty())return;auto after=silenced[at]?std::vector<Glyph>{}:noiseGlyphs(at);std::vector<Glyph> removed;
  for(size_t k=0;k<before.size();++k)if(before[k].opacity>.3f&&(k>=after.size()||after[k].opacity<=.3f))removed.push_back(before[k]);
  if(!removed.empty()){if(noiseDebris.size()==3)noiseDebris.erase(noiseDebris.begin());noiseDebris.push_back({removed,0});}
 }
 void tickNoiseDebris(float delta){for(auto& d:noiseDebris)d.age+=delta;noiseDebris.erase(std::remove_if(noiseDebris.begin(),noiseDebris.end(),[](const auto& d){return d.age>=.32f;}),noiseDebris.end());}

 int index=0,hearts=5;
 int passes=0;std::array<int,3> lanePasses{{0,0,0}};
 int panicDisplayLane=0;float panicSelectFrames=0;
 int panicLockedNoise=-1,panicLockedLane=-1;float panicLockTicks=0;
 void advancePanicLock(float delta){
  const int active=panicForcedNoise();
  if(panicLockedNoise>=0){
   panicLockTicks+=std::max(0.f,delta)*60.f;
   const bool removed=silenced[panicLockedNoise];
   if((removed&&panicLockTicks>=40.f)||(!removed&&active!=panicLockedNoise)){
    panicLockedNoise=panicLockedLane=-1;panicLockTicks=0;
   }
  }
  if(panicLockedNoise<0&&active>=0){
   for(int lane=0;lane<3;++lane){
    if(lanePasses[lane]||lines[laneLine(lane)].actor!=lines[active].actor)continue;
    panicLockedNoise=active;panicLockedLane=lane;break;
   }
  }
 }
 void trackPanicCursor(float x,float y,float delta,float width=1280.f,float height=720.f){
  const int forced=panicForcedLane();
  const int proposed=forced>=0?forced:panicPaneAt(x,y,width,height);
  if(proposed<0||proposed==panicDisplayLane){panicSelectFrames=0;return;}
  panicSelectFrames+=delta*60.f;
  if(panicSelectFrames>=20.f){panicDisplayLane=proposed;panicSelectFrames=0;}
 }
 bool panicRoundDone()const{return panic()&&std::all_of(lanePasses.begin(),lanePasses.end(),[](int completed){return completed>0;});}
 float time=0,focus=100;
 bool noisePool=false,authoredPanicBeats=false;int noiseAction=1;
 mutable int noiseSyncIndex=-1;mutable float noiseSyncTime=-1,noiseSyncAlpha=0;
 float statementOpacity()const{
  if(noiseSyncIndex!=index||noiseSyncTime!=time){noiseSyncIndex=index;noiseSyncTime=time;noiseSyncAlpha=0;for(const auto& g:current())if(g.text!=" ")noiseSyncAlpha=std::max(noiseSyncAlpha,g.opacity);}
  return noiseSyncAlpha;
 }
 std::vector<float> loudElapsed;std::vector<bool> loudChecked;
 std::vector<std::vector<int>> lanes;
 std::vector<int> laneAt;
 std::vector<float> laneTime;
 void bindNoiseAnchors(){
  for(auto& n:lines)if(n.kind=="noise"&&n.noiseFor>=0&&n.noiseFor<int(lines.size())){
   const auto& host=lines[n.noiseFor];if(!host.readable)continue;const auto cue=noiseCue(n.id,n.text);
   // Authored scene coordinates are independent of the answer/weakpoint glyphs.
   n.noiseAnchorX=cue.x;n.noiseAnchorY=cue.y;n.noiseAnchored=true;
  }
 }
 bool panic()const{return lanes.size()==3;}
 void restartRows(){noiseSyncIndex=-1;noiseDebris.clear();broken.assign(lines.size(),false);silenced.assign(lines.size(),false);noiseDamage.assign(lines.size(),0);loudElapsed.assign(lines.size(),0);loudChecked.assign(lines.size(),false);index=0;time=0;passes=0;lanePasses={{0,0,0}};panicDisplayLane=0;panicSelectFrames=0;panicLockedNoise=panicLockedLane=-1;panicLockTicks=0;bindNoiseAnchors();if(panic()){laneAt.assign(3,0);laneTime.assign(3,0);selectPanic();}}
 int laneOf(int value)const{for(int n=0;n<int(lanes.size());n++)for(int i:lanes[n])if(i==value)return n;return -1;}
 int laneLine(int lane)const{return lanes[lane][laneAt[lane]];}
 std::vector<Glyph> panicGlyphs(int lane)const{
  int at=laneLine(lane);if(lanePasses[lane]>0||broken[at])return {};const auto& l=lines[at];auto chars=glyphs(l.text);std::vector<Glyph> out;
  // V3(영상 A 26:06) : 발언은 자기 영역 안에서 경계선을 따라 쓴다. 영역은 create-project.mjs 패닉(1장 CDV 네이티브 계산)
  // 왼쪽 = 경계(761,0)→(253,720) 와 나란히 아래→위, 오른쪽 위 = 위쪽 가로, 아래 = 경계(577,266)→(1226,720) 와 나란히
  static const float ang[3]{-55.f,-6.f,35.f},ox[3]{190,700,600},oy[3]{600,215,395};static const int per[3]{12,9,8};
  const float a=ang[lane]*PI/180,dx=std::cos(a),dy=std::sin(a),nx=-dy,ny=dx;
  float run=0; /* 글꼴 실제 폭으로 이어 쓴다(46 = 예전 한글 한 칸) */
  for(int i=0;i<std::min(48,int(chars.size()));i++){Glyph g;g.text=chars[i];int row=i/per[lane],col=i%per[lane];if(col==0)run=0;float step=em(chars[i],l.font)*36*1.3f; /* PanicV4 글자 36px × 1.3 */float along=run+step*.5f-23;run+=step;float wob=std::sin(laneTime[lane]*1.5f+i*.13f)*3,n=(lane==0?-1.f:1.f)*row*58+wob; /* 왼쪽 조각은 다음 줄을 왼쪽으로 */
   g.x=ox[lane]+dx*along+nx*n;g.y=oy[lane]+dy*along+ny*n;g.scale=1.3f;g.rotation=ang[lane];g.opacity=std::min(1.f,laneTime[lane]*4);g.halfW=step*.5f;g.halfH=26;g.front=true;g.weak=(l.kind=="agree"||l.kind=="weak")&&i>=l.start&&i<l.start+u8len(l.word);
   const auto fit=PANIC_TYPE[lane];
   g.x=ox[lane]+fit.x+(g.x-ox[lane])*fit.scale;
   g.y=oy[lane]+fit.y+(g.y-oy[lane])*fit.scale;
   g.scale*=fit.scale;g.halfW*=fit.scale;g.halfH*=fit.scale;
   out.push_back(g);
  }
  return out;
 }
 void selectPanic(){if(!panic())return;index=laneLine(0);for(int n=0;n<3;n++){int at=laneLine(n);if(!broken[at]&&(lines[at].kind=="weak"||lines[at].kind=="agree")){index=at;break;}}time=laneTime[laneOf(index)];}
 bool loudVisible(int at)const{
  const auto pool=noiseIndices();
  const auto slot=std::find(pool.begin(),pool.end(),at);
  if(slot==pool.end())return false;
  for(const auto& g:noiseGlyphs(at,int(slot-pool.begin())))
   if(g.opacity>.3f&&g.text!=" "&&g.x+g.halfW>0&&g.x-g.halfW<1280&&g.y+g.halfH>0&&g.y-g.halfH<720)return true;
  return false;
 }
 int panicForcedNoise()const{
  if(!panic())return -1;
  for(int at:noiseIndices()){
   if(!lines[at].noiseLoud||!loudVisible(at))continue;
   for(int lane=0;lane<3;++lane){
    if(lanePasses[lane]||lines[laneLine(lane)].actor!=lines[at].actor)continue;
    return at;
   }
  }
  return -1;
 }
 int panicForcedLane()const{
  if(panicLockedLane>=0)return panicLockedLane;
  const int at=panicForcedNoise();if(at<0)return -1;
  for(int lane=0;lane<3;++lane)if(!lanePasses[lane]&&lines[laneLine(lane)].actor==lines[at].actor)return lane;
  return -1;
 }
 bool panicHit(float x,float y){
  if(!panic()||panicForcedNoise()>=0)return false;
  const int prior=index,forced=panicForcedLane();
  for(int lane=0;lane<3;++lane){
   if(lanePasses[lane]||(forced>=0&&forced!=lane))continue;
   index=laneLine(lane);
   if(weakHit(x,y))return true;
  }
  index=prior;return false;
 }

 const Line& line()const{return lines[index];}
 float base()const{return line().kind=="weak"&&!line().readable?62.f:54.f;} // 줄마다 size 로 다시 곱한다
 float t()const{return std::clamp(time/duration(line(),base()),0.f,1.f);}
 std::vector<Glyph> current()const{return panic()?panicGlyphs(laneOf(index)):place(line(),t(),index%3,base());}
 // 현재 발언에 배치된 잡음만 생성 시각과 수명으로 표시한다.
 std::vector<int> noiseIndices()const{
  std::vector<int> out;int used=0;for(size_t k=1;k<lines.size();++k){int i=(index+int(k))%int(lines.size());if(lines[i].kind!="noise"||silenced[i])continue;
   const int host=lines[i].noiseFor;
   if(host>=0&&((!panic()&&host!=index)||(panic()&&host!=laneLine(0)&&host!=laneLine(1)&&host!=laneLine(2))))continue;
   if(noisePool&&!(panic()&&lines[i].noiseLoud)){bool foreground=false;auto same=[&](int at){return !lines[i].noiseGroup.empty()&&lines[at].noiseGroup==lines[i].noiseGroup;};if(panic())for(int lane=0;lane<3;lane++)foreground=foreground||same(laneLine(lane));else foreground=same(index);if(foreground&&lines[i].noiseFor<0)continue;int n=u8len(lines[i].text);if(used+n>26)continue;used+=n;}
   if(!panic()&&line().readable){auto gs=noiseGlyphs(i);bool visible=false;for(const auto& g:gs)if(g.opacity>.3f&&g.x+g.halfW>0&&g.x-g.halfW<1280&&g.y+g.halfH>0&&g.y-g.halfH<720){visible=true;break;}if(!visible){used-=u8len(lines[i].text);continue;}}
   out.push_back(i);if(!noisePool||out.size()==3)break;
  }return out;
 }
 int noiseIndex()const{auto pool=noiseIndices();return pool.empty()?-1:pool[0];}
 std::vector<Glyph> noiseGlyphs(int i,int slot=0)const{
  const bool foreground=!panic()&&line().readable;
  const float phase=std::fmod(time+1.5f+slot*1.35f,duration(lines[i],40))/duration(lines[i],40);
  if(foreground){
   const auto& l=lines[i];const auto cue=noiseCue(l.id,l.text);if(noiseAction<cue.minAction)return {};
   const float alpha=statementOpacity();if(alpha<=.001f)return {};
   auto chars=glyphs(l.text);std::vector<Glyph> out;
   // A noise response appears at its scene placement and stays there.
   // It is not a projectile flying between opposite screen edges.
   const float z=700.f,scale=FOCAL/z;
   float width=0;for(const auto& c:chars)width+=em(c,l.font)*54;
   const float angle=cue.angle*PI/180.f,ca=std::cos(angle),sa=std::sin(angle);
   const float fit=std::min(1.f,980.f/std::max(1.f,width*scale));
   const float hw=std::abs(ca)*width*scale*fit*.5f+std::abs(sa)*29*scale*fit;
   const float hh=std::abs(sa)*width*scale*fit*.5f+std::abs(ca)*29*scale*fit;
   const float ax=std::clamp(l.noiseAnchorX,60.f+hw,1220.f-hw),ay=std::clamp(l.noiseAnchorY,120.f+hh,575.f-hh);
   float off=0;
   for(size_t k=0;k<chars.size();++k){
    Glyph g;g.text=chars[k];g.front=true;g.depth=z;
    const float local=(off-width*.5f+em(g.text,l.font)*27)*scale*fit;
    g.x=ax+ca*local;g.y=ay+sa*local;g.scale=scale*fit;
    g.halfW=em(g.text,l.font)*27*g.scale;g.halfH=29*g.scale;
    g.rotation=cue.angle;g.yaw=0;
    g.opacity=alpha;if(g.text==" ")g.opacity=0;
    if(i<int(noiseDamage.size())&&noiseDamage[i]>0){int half=int(chars.size())/2,remain=std::max(1,(std::max(1,l.noiseDurability)-noiseDamage[i])*half/std::max(1,l.noiseDurability));if(int(k)<half-remain||int(k)>half+remain)g.opacity=0;}
    off+=em(g.text,l.font)*54;out.push_back(g);
   }
   return out;
  }
  auto out=place(lines[i],phase,panic()?(index+slot+1)%3:index%3,40);
  if(foreground||lines[i].noiseLoud)for(auto& g:out)g.front=true;
  if(foreground)for(auto& g:out){g.depth=430.f;g.y=std::clamp(g.y,148.f,524.f);}
  return out;
 }
 std::vector<Glyph> noise()const{
  std::vector<Glyph> out;auto pool=noiseIndices();
  // Collision-bearing glyphs own the budget; decorative fragments may use
  // only the free slots. A breakup must never hide another live obstruction.
  for(int slot=0;slot<int(pool.size());++slot)for(const auto& g:noiseGlyphs(pool[slot],slot))if(g.opacity>.001f&&g.text!=" ")out.push_back(g);
  for(const auto& d:noiseDebris){float u=d.age/.32f;for(size_t k=0;k<d.glyphs.size()&&out.size()<26;++k){auto g=d.glyphs[k];if(g.text==" "||g.opacity<=.001f)continue;g.x+=(float(k)-d.glyphs.size()*.5f)*35*u;g.y+=(k%2?1:-1)*95*u+100*u*u;g.rotation+=(k%2?1:-1)*75*u;g.scale*=1+.18f*u;g.opacity*=1-smooth(u);out.push_back(g);}}
  return out;
 }


 // 화자 앞으로 나온(보이는) 약점 글자만 맞힐 수 있다
 bool weakHit(float x,float y)const{if((line().kind!="weak"&&line().kind!="agree")||line().answer.empty()||broken[index])return false;for(auto& g:current())if(g.weak&&g.front&&g.opacity>.3f&&inside(g,x,y,12))return true;return false;}
 // V포인트 : 앞에 나온 약점 글자들 가운데 글자의 중심
 bool vpoint(float& x,float& y)const{
  if((line().kind!="weak"&&line().kind!="agree")||line().answer.empty()||broken[index])return false;
  auto gs=current();std::vector<const Glyph*> w;for(auto& g:gs)if(g.weak&&g.front)w.push_back(&g);
  if(line().vpointIndex>=0){int i=line().vpointIndex;if(i>=int(gs.size())||!gs[i].weak||!gs[i].front||gs[i].opacity<=.3f)return false;x=gs[i].x;y=gs[i].y;return true;}
  if(w.empty())return false;auto* g=w[w.size()/2];x=g->x;y=g->y;return true;
 }
 // A normal bullet is stopped by the nearest rendered noise glyph, not
 // by a whole-line rectangle or by a hidden/behind-target piece of text.
 int blockingNoise(float x,float y)const{
  float mainDepth=1e9f,noiseDepth=1e9f;int selected=-1;
  if(!panic()&&line().readable)for(auto g:current())if(g.weak&&g.front&&g.opacity>.3f&&g.text!=" "){g.halfW*=1.4f;g.halfH*=1.4f;float z;if(inside(g,x,y,0,&z))mainDepth=std::min(mainDepth,z);}
  auto pool=noiseIndices();for(int slot=0;slot<int(pool.size());++slot)for(auto g:noiseGlyphs(pool[slot],slot))if(g.front&&g.opacity>.3f&&g.text!=" "){g.halfW*=1.4f;g.halfH*=1.4f;float z;if(inside(g,x,y,0,&z)&&z<noiseDepth){noiseDepth=z;selected=pool[slot];}}
  return noiseDepth<=mainDepth?selected:-1;
 }
 bool noiseHit(float x,float y)const{return blockingNoise(x,y)>=0;}

 bool cleared()const{for(size_t i=0;i<lines.size();++i)if(lines[i].kind=="weak"&&!lines[i].decoy&&!broken[i])return false;return true;} // 함정 약점은 끝내는 조건에 세지 않는다
 void advanceLane(int lane){
  if(laneAt[lane]+1<int(lanes[lane].size()))++laneAt[lane];else lanePasses[lane]=1;
  laneTime[lane]=0;
 }
 void next(){noiseDebris.clear();if(!panic()&&line().readable)for(size_t i=0;i<lines.size();++i)if(lines[i].kind=="noise"&&lines[i].noiseFor==index){silenced[i]=false;if(i<noiseDamage.size())noiseDamage[i]=0;}if(panic()){advanceLane(laneOf(index));selectPanic();return;}for(size_t k=0;k<lines.size();++k){index=(index+1)%int(lines.size());if(index==0)++passes;if(!broken[index]&&!(lines[index].kind=="noise"))break;}time=0;}
 bool tick(float delta){
  if(panic()){
   const int prior=index;
   if(authoredPanicBeats){
    bool beatDone=true;
    for(int n=0;n<3;++n){
     if(lanePasses[n])continue;
     const int at=laneLine(n);
     laneTime[n]+=delta;
     beatDone=beatDone&&(broken[at]||laneTime[n]>=duration(lines[at],54));
    }
    if(beatDone){
     const auto active=noiseIndices();
     const bool mustSilence=std::any_of(active.begin(),active.end(),[&](int at){return lines[at].noiseLoud&&lines[at].noiseFor>=0;});
     if(!mustSilence)for(int n=0;n<3;++n)if(!lanePasses[n])advanceLane(n);
    }
   }else for(int n=0;n<3;n++){if(lanePasses[n])continue;laneTime[n]+=delta;int at=laneLine(n);if(broken[at]||laneTime[n]>=duration(lines[at],54))advanceLane(n);}
   selectPanic();return prior!=index;
  }
  time+=delta;if(time<duration(line(),base()))return false;next();return true;
 }
};

// 연출 고르기 : 대본의 연출 지정 > 문장의 감정(부호) > 인물 성격 > 종류. 같은 논의에서 바로 앞 줄과 겹치지 않게 한 칸 민다.
inline Motion motionByName(const std::string& n,bool& ok){
 static const std::pair<const char*,Motion> t[]{{"slide",Motion::Slide},{"fly",Motion::Fly},{"swirl",Motion::Swirl},{"slam",Motion::Slam},{"wave",Motion::Wave},{"shake",Motion::Shake},{"assemble",Motion::Assemble},{"zoom",Motion::Zoom},{"rise",Motion::Rise},{"type",Motion::Type},{"bounce",Motion::Bounce},{"spiral",Motion::Spiral},{"burst",Motion::Burst}};
 for(auto& [k,m]:t)if(n==k){ok=true;return m;}
 ok=false;return Motion::Slide;
}
inline Motion motionOf(const std::string& name,const Line& l,int i,Motion previous){
 bool ok;Motion m=motionByName(name,ok);if(ok)return m;
 if(l.kind=="noise")return Motion::Wave;
 const auto& t=l.text;auto has=[&](const char* s){return t.find(s)!=std::string::npos;};
 // 인물 성격
 static const std::pair<const char*,Motion> person[]{{"켄",Motion::Spiral},{"리쿠",Motion::Bounce},{"린",Motion::Bounce},{"하루카",Motion::Bounce},{"타이가",Motion::Slam},{"소라",Motion::Slam},{"레이",Motion::Slide},{"카에데",Motion::Slide},{"나나",Motion::Type},{"아이",Motion::Type},{"코토",Motion::Rise},{"사츠키",Motion::Zoom},{"쇼",Motion::Assemble},{"유우",Motion::Fly},{"아카리",Motion::Assemble},{"래피",Motion::Swirl}};
 Motion byPerson=Motion::Slide;for(auto& [k,v]:person)if(l.speaker==k)byPerson=v;
 if(has("!"))m=l.kind=="weak"?(i%2?Motion::Zoom:Motion::Burst):(i%2?Motion::Burst:Motion::Slam);   // 외침 : V3 는 화자 둘레로 흩어진다
 else if(has("…"))m=Motion::Type;                                                // 머뭇거림
 else if(has("?"))m=l.kind=="weak"?Motion::Swirl:Motion::Fly;                     // 물음
 else if(l.kind=="agree")m=Motion::Rise;
 else if(l.kind=="weak"){static const Motion w[]{Motion::Fly,Motion::Assemble,Motion::Zoom,Motion::Swirl};m=i%2?w[i%4]:byPerson;}
 else m=byPerson;
 if(m==previous){static const Motion alt[]{Motion::Assemble,Motion::Fly,Motion::Rise,Motion::Slide};m=alt[i%4];}
 return m;
}
// 감정 크기 : 외침은 크게, 속삭임·머뭇거림은 작게
inline float sizeOf(const Line& l){
 if(l.kind=="noise")return l.noiseLoud?1.7f:1.4f; // 분홍 잡음이 잘 보이게(V3 영상 A 1:31 「Y-Yeah, I...?」 크기)
 if(l.text.find('!')!=std::string::npos)return 1.25f;
 if(l.text.find("…")!=std::string::npos)return .85f;
 return 1.f;
}
}
