#pragma once
#include <HBEngine/Game.hpp>
#include "Debate.hpp"
#include <set>
namespace evidencehintv4 {
// Own IDs map normal primary answers only; alternate/converted answers never replace it.
inline std::string primary(const hb::Json& task,const std::set<std::string>& owned){
 if(!task.is_object())return {};
 auto kind=task.value("stage",hb::Json::object()).value("kind",std::string());if(kind!="nonstop"&&kind!="panic")return {};
 std::string id;for(const auto& row:task.value("debate",hb::Json::object()).value("lines",hb::Json::array())){
  auto weak=row.value("weak",hb::Json::object());if(row.value("kind",std::string())!="weak"||weak.value("lie",false))continue;
  auto candidate=weak.value("answer",std::string());if(!candidate.empty())id=candidate;
 }
 return owned.count(id)?id:std::string();
}
inline bool ready(const debate::State& state){return state.panic()?state.lanePasses[0]>0&&state.lanePasses[1]>0&&state.lanePasses[2]>0:state.passes>0;}
inline bool visible(const std::string& primary,const std::string& selected,bool active,bool equipped,const debate::State& state){return active&&equipped&&ready(state)&&!primary.empty()&&primary==selected;}
// Existing selected-row ink only; this pulse is an own presentation adaptation.
inline float opacity(float seconds){return .72f+.28f*std::cos(std::max(0.f,seconds)*6.f);}
}
