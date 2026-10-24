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

enum class Motion{Slide,Fly,Swirl,Slam,Wave,Shake};

struct Line{std::string speaker,text,kind,word,answer;int start=0;bool lie=false;Motion motion=Motion::Slide;float spacing=1;}; // spacing : 글꼴 폭 계수

struct Glyph{std::string text;float x=0,y=0,scale=1,rotation=0,opacity=1,halfW=0,halfH=0;bool front=true,weak=false;};

// 한 증언의 t(0~1) 시점 글자 배치
inline std::vector<Glyph> place(const Line& l,float t,int lane,float base){
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
    float R=620,a=-PI*.85f+PI*1.7f*t+local/R;X=R*std::sin(a);Z=SPEAKER_Z-R*std::cos(a);Y=laneY*.5f-40;roll=std::sin(a)*-8;break;}
   case Motion::Slam:{ // 위에서 쾅 떨어져 박힌 뒤 천천히 흐른다
    float drop=std::min(1.f,t/.12f);float bounce=drop<1?0:std::sin(std::min(1.f,(t-.12f)/.1f)*PI)*-18;
    X=local-90*t;Y=-900+(900+laneY)*(1-std::pow(1-drop,3))+bounce;Z=620;roll=-6;break;}
   case Motion::Wave:  // 소음 : 뒤에서 일렁이며 지나간다
    X=-1150+(2300+total)*t+local;Z=1250;Y=laneY+7*std::sin(t*20+i*.5f);break;
   case Motion::Shake: // 떨리는 목소리
    X=1100-(2200+total)*t+local;Z=820;Y=laneY+std::sin(t*180+i*2.1f)*3;roll=std::sin(t*150+i)*3;break;
  }
  Glyph g;g.text=gs[i];
  float s=FOCAL/std::max(120.f,Z);
  g.x=CX+X*s;g.y=CY+Y*s;g.scale=s;g.rotation=roll;g.opacity=fade;
  g.front=Z<SPEAKER_Z;g.weak=l.kind=="weak"&&int(i)>=l.start&&int(i)<weakEnd;
  g.halfW=em(gs[i])*base*l.spacing*s*.5f;g.halfH=base*s*.62f;
  out.push_back(g);
 }
 return out;
}

inline float duration(const Line& l,float base){
 float w=0;for(auto& g:glyphs(l.text))w+=em(g)*base*l.spacing;
 switch(l.motion){case Motion::Swirl:return 7.5f;case Motion::Slam:return 5.5f+w/500;case Motion::Fly:return 5.f;default:return 5.f+w/320;}
}

inline bool inside(const Glyph& g,float x,float y,float pad){return std::abs(x-g.x)<=g.halfW+pad&&std::abs(y-g.y)<=g.halfH+pad;}

struct State{
 std::vector<Line> lines;
 std::vector<bool> broken,silenced;
 int index=0,hearts=5;
 float time=0,focus=100;

 const Line& line()const{return lines[index];}
 float base()const{return line().kind=="weak"?50.f:40.f;}
 float t()const{return std::clamp(time/duration(line(),base()),0.f,1.f);}
 std::vector<Glyph> current()const{return place(line(),t(),index%3,base());}
 // 소음은 본 증언과 겹쳐서 흐른다 : 가장 가까운 소음 줄
 int noiseIndex()const{for(size_t k=1;k<lines.size();++k){int i=(index+int(k))%int(lines.size());if(lines[i].kind=="noise"&&!silenced[i])return i;}return -1;}
 std::vector<Glyph> noise()const{int i=noiseIndex();if(i<0)return {};float d=duration(lines[i],34);return place(lines[i],std::fmod(time+1.5f,d)/d,(index+1)%3,34);}

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

// 줄 종류·순서로 기본 연출을 고른다(데이터에 motion 이 있으면 그것을 우선)
inline Motion motionOf(const std::string& name,const std::string& kind,int i){
 if(name=="slide")return Motion::Slide;if(name=="fly")return Motion::Fly;if(name=="swirl")return Motion::Swirl;
 if(name=="slam")return Motion::Slam;if(name=="wave")return Motion::Wave;if(name=="shake")return Motion::Shake;
 if(kind=="noise")return Motion::Wave;
 if(kind=="weak"){static const Motion m[]{Motion::Fly,Motion::Slam,Motion::Swirl};return m[i%3];}
 if(kind=="agree")return Motion::Slide;
 return i%2?Motion::Shake:Motion::Slide;
}
}
