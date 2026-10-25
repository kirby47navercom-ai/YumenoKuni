#pragma once
// 다이내믹 논스톱 논의 (V3) 규칙·연출 모델.
// 증언 글자 하나하나가 3D 경로 위에 놓이고, 원근 투영으로 화면 위치·크기·회전·앞뒤(화자 앞/뒤)가 정해진다.
#include <algorithm>
#include <cmath>
#include <string>
#include <vector>
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
inline float em(const std::string& g){unsigned char c=g[0];return c==' '?.26f:c<0x80?.56f:.86f;}

constexpr float FOCAL=900,CX=640,CY=360,SPEAKER_Z=900; // 화자(입상) 평면 깊이
constexpr float PI=3.14159265f;

// 연출 : 흐름·날아듦·화자 주위 회전·쾅·소음 일렁임·떨림·흩어진 글자 모임·카메라로 돌진·바닥에서 솟음·한 글자씩·통통 튐·나선
enum class Motion{Slide,Fly,Swirl,Slam,Wave,Shake,Assemble,Zoom,Rise,Type,Bounce,Spiral};

struct Line{std::string speaker,text,kind,word,answer;int start=0;bool lie=false;Motion motion=Motion::Slide;float spacing=1,size=1;}; // spacing : 글꼴 폭 계수, size : 감정 크기

struct Glyph{std::string text;float x=0,y=0,scale=1,rotation=0,opacity=1,halfW=0,halfH=0;bool front=true,weak=false;};

// 한 증언의 t(0~1) 시점 글자 배치
inline float hash(int i,int k){float v=std::sin(i*12.9898f+k*78.233f)*43758.5453f;return v-std::floor(v);} // 글자별 고정 난수
inline std::vector<Glyph> place(const Line& l,float t,int lane,float base0){
 float base=base0*l.size;
 auto gs=glyphs(l.text);
 std::vector<float> off(gs.size());float total=0;
 for(size_t i=0;i<gs.size();++i){off[i]=total;total+=em(gs[i])*base*l.spacing;}
 int weakEnd=l.start+u8len(l.word);
 float laneY=-170.f+lane*150.f,fade=std::clamp(std::min(t/.07f,(1-t)/.07f),0.f,1.f);
 std::vector<Glyph> out;
 for(size_t i=0;i<gs.size();++i){
  float local=off[i]+em(gs[i])*base*l.spacing*.5f-total*.5f; // 문장 중심 기준 x
  float X=0,Y=laneY,Z=700,roll=0;
  switch(l.motion){
   case Motion::Slide: // 옆으로 흐르며 살짝 비틀린 원근(한쪽 끝이 더 멀다)
    X=1150-(2300+total)*t+local;Z=760+local*.35f;roll=-4;break;
   case Motion::Fly:{  // 화자 뒤에서 카메라 앞으로 빠르게 날아든 뒤 천천히 지나간다
    float a=1-std::pow(1-std::min(1.f,t/.35f),2);
    Z=2000-1430*a+local*.2f;X=-180+260*t+local;Y=laneY*.6f-90*(1-a);roll=-12+12*a;break;}
   case Motion::Swirl:{ // 화자 주위를 한 바퀴 돈다(뒤로 지나갈 때는 입상 뒤에 그려짐)
    float R=430,a=-PI*.85f+PI*1.7f*t+local/R;X=R*std::sin(a);Z=SPEAKER_Z+150-R*std::cos(a);Y=laneY*.35f;roll=std::sin(a)*-8;break;}
   case Motion::Slam:{ // 위에서 쾅 떨어져 박힌 뒤 천천히 흐른다
    float drop=std::min(1.f,t/.12f);float bounce=drop<1?0:std::sin(std::min(1.f,(t-.12f)/.1f)*PI)*-18;
    X=local-90*t;Y=-900+(900+laneY)*(1-std::pow(1-drop,3))+bounce;Z=620;roll=-6;break;}
   case Motion::Wave:  // 소음 : 뒤에서 일렁이며 지나간다
    X=-1150+(2300+total)*t+local;Z=1250;Y=laneY+7*std::sin(t*20+i*.5f);break;
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
    X=1150-(2300+total)*t+local;Z=740;Y=laneY-std::abs(std::sin(t*14+i*.6f))*38;roll=std::sin(t*14+i*.6f)*8;break;
   case Motion::Spiral:{ // 화면 깊은 곳에서 나선을 그리며 다가온다(연극조)
    float a=std::min(1.f,t/.5f);float ang=(1-a)*PI*3+i*.04f;float R=(1-a)*900;
    X=local+R*std::cos(ang);Y=laneY*.6f+R*.5f*std::sin(ang);Z=2600-1900*a;roll=(1-a)*360*(hash(int(i),5)>.5f?1:-1)*.1f;break;}
  }
  Glyph g;g.text=gs[i];
  float s=FOCAL/std::max(400.f,Z); // 최대 2.25배 : 너무 가까운 글자는 화면을 덮고 렌더링을 막는다
  g.x=CX+X*s;g.y=CY+Y*s;g.scale=s;g.rotation=roll;g.opacity=fade;
  g.front=Z<SPEAKER_Z;g.weak=l.kind=="weak"&&int(i)>=l.start&&int(i)<weakEnd;
  g.halfW=em(gs[i])*base*l.spacing*s*.5f;g.halfH=base*s*.62f;
  out.push_back(g);
 }
 return out;
}

inline float duration(const Line& l,float base){
 float w=0;base*=l.size;for(auto& g:glyphs(l.text))w+=em(g)*base*l.spacing;
 switch(l.motion){case Motion::Swirl:return 7.5f;case Motion::Slam:case Motion::Zoom:case Motion::Assemble:case Motion::Type:case Motion::Spiral:return 5.5f+w/500;case Motion::Fly:return 5.f;case Motion::Rise:return 6.f;default:return 5.f+w/320;}
}

inline bool inside(const Glyph& g,float x,float y,float pad){return std::abs(x-g.x)<=g.halfW+pad&&std::abs(y-g.y)<=g.halfH+pad;}

struct State{
 std::vector<Line> lines;
 std::vector<bool> broken,silenced;
 int index=0,hearts=5;
 float time=0,focus=100;

 const Line& line()const{return lines[index];}
 float base()const{return line().kind=="weak"?62.f:54.f;} // 줄마다 size 로 다시 곱한다
 float t()const{return std::clamp(time/duration(line(),base()),0.f,1.f);}
 std::vector<Glyph> current()const{return place(line(),t(),index%3,base());}
 // 소음은 본 증언과 겹쳐서 흐른다 : 가장 가까운 소음 줄
 int noiseIndex()const{for(size_t k=1;k<lines.size();++k){int i=(index+int(k))%int(lines.size());if(lines[i].kind=="noise"&&!silenced[i])return i;}return -1;}
 std::vector<Glyph> noise()const{int i=noiseIndex();if(i<0)return {};float d=duration(lines[i],40);return place(lines[i],std::fmod(time+1.5f,d)/d,(index+1)%3,40);}

 // 화자 앞으로 나온(보이는) 약점 글자만 맞힐 수 있다
 bool weakHit(float x,float y)const{if(line().kind!="weak"||broken[index])return false;for(auto& g:current())if(g.weak&&g.front&&g.opacity>.3f&&inside(g,x,y,12))return true;return false;}
 // V포인트 : 앞에 나온 약점 글자들 가운데 글자의 중심
 bool vpoint(float& x,float& y)const{
  if(line().kind!="weak"||broken[index])return false;
  auto gs=current();std::vector<const Glyph*> w;for(auto& g:gs)if(g.weak&&g.front)w.push_back(&g);
  if(w.empty())return false;auto* g=w[w.size()/2];x=g->x;y=g->y;return true;
 }
 bool noiseHit(float x,float y)const{for(auto& g:noise())if(g.opacity>.3f&&inside(g,x,y,8))return true;return false;}
 bool cleared()const{for(size_t i=0;i<lines.size();++i)if(lines[i].kind=="weak"&&!broken[i])return false;return true;}
 void next(){for(size_t k=0;k<lines.size();++k){index=(index+1)%int(lines.size());if(!broken[index]&&!(lines[index].kind=="noise"))break;}time=0;}
 bool tick(float delta){time+=delta;if(time<duration(line(),base()))return false;next();return true;}
};

// 연출 고르기 : 대본의 연출 지정 > 문장의 감정(부호) > 인물 성격 > 종류. 같은 논의에서 바로 앞 줄과 겹치지 않게 한 칸 민다.
inline Motion motionByName(const std::string& n,bool& ok){
 static const std::pair<const char*,Motion> t[]{{"slide",Motion::Slide},{"fly",Motion::Fly},{"swirl",Motion::Swirl},{"slam",Motion::Slam},{"wave",Motion::Wave},{"shake",Motion::Shake},{"assemble",Motion::Assemble},{"zoom",Motion::Zoom},{"rise",Motion::Rise},{"type",Motion::Type},{"bounce",Motion::Bounce},{"spiral",Motion::Spiral}};
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
 if(has("!"))m=l.kind=="weak"?(i%2?Motion::Zoom:Motion::Slam):Motion::Slam;   // 외침
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
 if(l.kind=="noise")return .9f;
 if(l.text.find('!')!=std::string::npos)return 1.25f;
 if(l.text.find("…")!=std::string::npos)return .85f;
 return 1.f;
}
}
