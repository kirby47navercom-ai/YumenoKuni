#pragma once
// 재판 줄마다 연출표(Claude 2026-11-04, 사양서 25). 원본 : data/v4_story/trial_direction.json → Assets/Data/v4_story/trial_direction.json
// debate[<line id>] : pose(C01~C14·T01~T04·U1~U6·X…), motion(Debate.hpp 이름), yaw(원근 판 각도), size, font(Assets/Fonts 아래 경로),
//                    shot(Courtroom SHOTS 번호), fx("shake"·"swirl"·"punch"·"flash" 를 | 로), se(큐 이름)
// queue[<eventId>]  : pose, fx, se  — 재판 중 대화 줄
#include <string>
namespace trialdirection {
inline const hb::Json& all(){
 static const hb::Json value=[](){try{return hb::Data::Get("Assets/Data/v4_story/trial_direction.json");}catch(...){return hb::Json::object();}}();
 return value;
}
inline const hb::Json* find(const char* table,const std::string& id){
 const auto& d=all();if(id.empty()||!d.contains(table))return nullptr;const auto& t=d[table];auto it=t.find(id);return it==t.end()?nullptr:&*it;
}
inline bool has(const std::string& fx,const char* name){return ("|"+fx+"|").find(std::string("|")+name+"|")!=std::string::npos;}
// "C05" 처럼 접미사만 쓰면 인물 이름을 붙인다
inline std::string pose(const std::string& actor,const std::string& p){if(p.empty())return {};return p.find('_')!=std::string::npos?p:actor+"_"+p;}
}
