#pragma once
// 논스톱 논의 규칙 : 증언 한 줄씩 화면을 가로질러 흐르고, 약점 단어에 맞는 언령을 쏘면 논파.
#include <algorithm>
#include <string>
#include <vector>
namespace debate {

inline int u8len(const std::string& s){int n=0;for(unsigned char c:s)if((c&0xC0)!=0x80)++n;return n;}
// 코드포인트 기준 [from, from+count)
inline std::string u8sub(const std::string& s,int from,int count){
 size_t a=s.size(),b=s.size();int n=0;
 for(size_t i=0;i<=s.size();++i){
  bool lead=i==s.size()||(static_cast<unsigned char>(s[i])&0xC0)!=0x80;
  if(!lead)continue;
  if(n==from)a=std::min(a,i);
  if(n==from+count){b=i;break;}
  ++n;
 }
 return a>=s.size()?std::string():s.substr(a,b-a);
}
// 글자 폭 추정 : 한글·전각 0.86em, ASCII 0.56em, 공백 0.26em.
// ponytail: 실제 글꼴 측정이 아닌 추정치. 판정이 어긋나면 엔진 텍스트 측정 API로 교체.
inline float width(const std::string& s,float size){
 float w=0;
 for(size_t i=0;i<s.size();){
  unsigned char c=s[i];int len=c<0x80?1:c<0xE0?2:c<0xF0?3:4;
  w+=c==' '?.26f:c<0x80?.56f:.86f;i+=len; // Pretendard 실측 근사 (한글 0.86em)
 }
 return w*size;
}

struct Line{std::string speaker,text,kind,word,answer;int start=0;};
struct Layout{float x=0,y=0,size=40,pre=0,weak=0,post=0;};

struct State{
 std::vector<Line> lines;
 std::vector<bool> broken;
 int index=0,hearts=5;
 float time=0;

 const Line& line()const{return lines[index];}
 float size()const{return line().kind=="weak"?44.f:36.f;}
 float total()const{return width(line().text,size());}
 float duration()const{return 5.f+total()/300.f;}
 Layout layout()const{
  auto& l=line();Layout o;o.size=size();
  if(l.kind=="weak"){
   o.pre=width(u8sub(l.text,0,l.start),o.size);
   o.weak=width(l.word,o.size);
   o.post=width(u8sub(l.text,l.start+u8len(l.word),1<<20),o.size);
  }else o.pre=total();
  float w=o.pre+o.weak+o.post,t=time/duration();
  o.x=1280-(1280+w)*t;
  o.y=150+float(index%3)*130;
  return o;
 }
 bool weakHit(float mx,float my)const{
  if(line().kind!="weak"||broken[index])return false;
  auto o=layout();const float pad=14;
  return mx>=o.x+o.pre-pad&&mx<=o.x+o.pre+o.weak+pad&&my>=o.y-pad&&my<=o.y+o.size*1.4f+pad;
 }
 bool cleared()const{for(size_t i=0;i<lines.size();++i)if(lines[i].kind=="weak"&&!broken[i])return false;return true;}
 // 다음 줄 (논파된 줄은 건너뜀)
 void next(){
  for(size_t k=0;k<lines.size();++k){index=(index+1)%int(lines.size());if(!broken[index])break;}
  time=0;
 }
 // true = 줄이 바뀌었음
 bool tick(float delta){time+=delta;if(time<duration())return false;next();return true;}
};
}
