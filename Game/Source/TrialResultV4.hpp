#pragma once
#include <HBEngine/Game.hpp>
#include <algorithm>
#include <cmath>
#include <map>
#include <set>
#include <string>
#include <vector>

// REA score-record and result-consumer contracts. Own phase IDs, timed replacement
// budgets and grade thresholds are adaptations for this manuscript's phase plan.
namespace resultv4 {
using hb::Json;
inline int type(const std::string& kind){
 if(kind=="nonstop")return 0;if(kind=="showdown")return 1;if(kind=="reasoning")return 2;
 if(kind=="anagram")return 3;if(kind=="mindmine")return 4;if(kind=="armament")return 5;
 if(kind=="scrum")return 6;if(kind=="climax")return 7;if(kind=="panic")return 8;return -1;
}
inline int raw(int kind,float remaining,bool vpoint=false,int frequency=60){
 if(kind<0||kind>8||!std::isfinite(remaining)||remaining<0||frequency<=0)return 0;
 // Preserve source float operations and its two successive hundred rounding steps.
 int q=0;
 if(kind==0||kind==1||kind==6||kind==8){int n=int((remaining/60.f)*10.f*100.f);if(n%100)n+=100;q=n/100;
  if(vpoint&&kind!=6){n=int(q*300.f/2.f);if(n%100)n+=100;q=n/100;}}
 else if(kind==5)q=(int(remaining)/frequency)*10;
 else if(kind==7)q=int(remaining)*10/60;
 else q=int(std::ceil(remaining*10.f/60.f));return q;
}
inline float coefficient(int difficulty){return difficulty==0?.8f:difficulty==2?1.2f:1.f;}
inline int weighted(int score,int a,int b){return int(float(score)*coefficient(a)*coefficient(b));}
inline int rank(int score,int upper,int middle){return score>=upper?0:score>=middle?1:2;}
struct Record {std::string id;int type=-1,raw=0,initial=0,remaining=0,difficulty0=1,difficulty1=1;bool back=false;};
struct Run {std::string chapter,pending;std::vector<Record> records;int gaffe=0,retry=0,total=0,award=0,upper=0,middle=0;bool financing=false,paid=false,complete=false;};
struct State {Run current;std::map<std::string,Run> best;};
inline Json encode(const Run& r){Json rows=Json::array();for(const auto& x:r.records)rows.push_back({{"id",x.id},{"type",x.type},{"raw",x.raw},{"initial",x.initial},{"remaining",x.remaining},{"d0",x.difficulty0},{"d1",x.difficulty1},{"back",x.back}});
 return {{"chapter",r.chapter},{"pending",r.pending},{"records",rows},{"gaffe",r.gaffe},{"retry",r.retry},{"total",r.total},{"award",r.award},{"upper",r.upper},{"middle",r.middle},{"financing",r.financing},{"paid",r.paid},{"complete",r.complete}};}
inline Json save(const State& s){Json best=Json::object();for(const auto& [ch,r]:s.best)best[ch]=encode(r);return {{"version",1},{"current",encode(s.current)},{"best",best}};}
// Blueprint string replies cap at4096 characters; persistence retains every row.
inline Json summary(const State& s){
 auto brief=[](const Run& r){return Json{{"chapter",r.chapter},{"records",r.records.size()},{"gaffe",r.gaffe},{"retry",r.retry},{"total",r.total},{"award",r.award},{"paid",r.paid},{"complete",r.complete}};};
 Json best=Json::object();for(const auto& [ch,r]:s.best)best[ch]=brief(r);return {{"version",1},{"summary",true},{"current",brief(s.current)},{"best",best}};
}
inline bool decode(const Json& j,Run& out){try{
 if(!j.is_object())return false;Run r;r.chapter=j.value("chapter",std::string());if(!r.chapter.empty()&&(r.chapter.size()!=1||r.chapter[0]<'1'||r.chapter[0]>'6'))return false;
 r.pending=j.value("pending",std::string());auto rows=j.at("records");if(!rows.is_array()||rows.size()>50)return false;std::set<std::string> ids;
 for(const auto& v:rows){Record x;x.id=v.at("id").get<std::string>();x.type=v.at("type").get<int>();x.raw=v.at("raw").get<int>();x.initial=v.at("initial").get<int>();x.remaining=v.at("remaining").get<int>();x.difficulty0=v.at("d0").get<int>();x.difficulty1=v.at("d1").get<int>();x.back=v.at("back").get<bool>();
  if(x.id.empty()||!ids.insert(x.id).second||x.type<0||x.type>8||x.raw<0||x.raw>1000000||x.initial<0||x.initial>3600000||x.remaining<0||x.remaining>x.initial||x.difficulty0<0||x.difficulty0>2||x.difficulty1<0||x.difficulty1>2)return false;r.records.push_back(x);}
 if(!r.pending.empty()&&(r.records.empty()||r.records.back().id!=r.pending))return false;
 r.gaffe=j.value("gaffe",0);r.retry=j.value("retry",0);r.total=j.value("total",0);r.award=j.value("award",0);r.upper=j.value("upper",0);r.middle=j.value("middle",0);r.financing=j.value("financing",false);r.paid=j.value("paid",false);r.complete=j.value("complete",false);
 if(r.gaffe<0||r.gaffe>99999||r.retry<0||r.retry>99999||r.total<0||r.total>50000000||r.award<0||r.award>999||r.middle<0||r.upper<r.middle||r.upper>50000000||(r.paid&&!r.complete)||(r.complete&&!r.pending.empty()))return false;out=std::move(r);return true;
 }catch(const std::exception&){return false;}}
inline bool restore(State& out,const Json& j){try{State s;if(j.is_null()||j.empty()){out=std::move(s);return true;}if(!j.is_object()||j.value("version",0)!=1||!decode(j.at("current"),s.current))return false;const auto& best=j.at("best");if(!best.is_object()||best.size()>6)return false;for(const auto& [ch,v]:best.items()){Run r;if(!decode(v,r)||r.chapter!=ch||!r.complete||!r.paid)return false;s.best[ch]=std::move(r);}out=std::move(s);return true;}catch(const std::exception&){return false;}}
inline void begin(State& s,const std::string& chapter){s.current=Run{};s.current.chapter=chapter;}
inline bool capture(State& s,const Record& r){auto& c=s.current;if(c.complete)return false;for(const auto& x:c.records)if(x.id==r.id)return false;
 if(!c.pending.empty())throw std::runtime_error("Previous score phase has not returned");if(c.records.size()>=50)throw std::runtime_error("Trial score phase capacity exceeded");c.records.push_back(r);c.pending=r.id;return true;}
inline void commit(State& s,const std::string& id,bool back=false){auto& r=s.current;if(r.pending!=id)return;if(back&&!r.records.empty())r.records.back().back=true;r.pending.clear();}
inline int settle(State& s,int& wallet,bool financing){auto& r=s.current;if(r.paid)return 0;if(!r.pending.empty())throw std::runtime_error("Result opened before score continuation");
 r.total=0;r.upper=r.middle=0;r.financing=financing;
 for(const auto& x:r.records){r.total+=weighted(x.raw,x.difficulty0,x.difficulty1);int maximum=raw(x.type,float(x.initial));r.upper+=maximum/2;r.middle+=maximum/4;}
 r.total=std::max(0,r.total-std::min(r.gaffe*100,9999)-std::min(r.retry*1000,9999));
 r.award=std::min(999,(r.total/200)*(financing?2:1));wallet=std::clamp(wallet+r.award,0,999);r.complete=r.paid=true;
 auto i=s.best.find(r.chapter);if(i==s.best.end()||r.total>=i->second.total)s.best[r.chapter]=r;return r.award;
}
inline const char* label(int type){static const char* names[]{"논스톱 논의","반론 쇼다운","추론 연결","섬광 애너그램","발굴 이매지네이션","이론 무장","논의 스크럼","클라이맥스 추리","패닉 논의"};return type>=0&&type<9?names[type]:"";}
}
