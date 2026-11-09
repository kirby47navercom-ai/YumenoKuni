#pragma once
#include <HBEngine/Game.hpp>
#include <algorithm>
#include <cmath>
#include <string>
#include <set>

namespace playerprogress {
struct State {int xp=0;float walkPhase=0;int displayed=1,popup=0,hold=0,frame=0,child=0;float clock=0;int phase=0,skyPhase=0;std::string context="chapter";std::set<std::string> claims;};
inline const hb::Json& data(){static const auto value=hb::Data::Get("Assets/Data/v4_story/player_progress.json");return value;}
inline int amount(const std::string& kind){for(const auto& row:data().at("gains"))if(row[0].get<std::string>()==kind)return row[1].get<int>();return 0;}
inline int level(const State& s,const hb::Json& rows=data().at("levels")){int result=1;for(const auto& row:rows)if(s.xp>=row[1].get<int>())result=row[0].get<int>();return result;}
inline float fraction(const State& s){int lv=level(s);if(lv>=99)return 1;const auto& rows=data().at("levels");int low=rows[lv-1][1],high=rows[lv][1];return float(s.xp-low)/float(high-low);}
inline bool gain(State& s,int amount){int before=s.xp;s.xp=int(std::clamp(static_cast<long long>(s.xp)+amount,0ll,168500ll));return before!=s.xp;}
inline bool claim(State& s,const std::string& id,int amount){if(id.empty()||id.size()>192||s.claims.size()>=4096||!s.claims.insert(id).second)return false;gain(s,amount);return true;}
// Source controller polls completion separately from root animation records.
inline int tick(State& s,int actual){
 if(s.popup==0){if(s.displayed!=actual){s.displayed=actual;s.popup=1;}return 0;}
 if(s.popup==1){s.popup=2;s.frame=s.child=s.hold=0;return 1;}
 ++s.child;
 if(s.popup==2){if(s.frame<16){++s.frame;return 0;}if(s.hold<60){++s.hold;return 0;}s.popup=3;s.frame=0;return 2;}
 if(s.frame<13){++s.frame;return 0;}s.popup=0;s.frame=s.child=s.hold=0;return 3;
}
inline bool fullGauge(const State& s,int actual){return s.displayed!=actual||s.popup!=0;}
inline int walk(State& s,float distance){
 // Project meter->phase calibration matches this world's existing bob phase.
 // It is independent of whether the player enables visible camera bob.
 if(!std::isfinite(distance)||distance<0)return 0;
 if(distance==0){if(s.walkPhase<=0)return 0;s.walkPhase=0;return 1;}
 s.walkPhase+=distance*8;int steps=int(s.walkPhase/3.14159265f);s.walkPhase-=steps*3.14159265f;return steps;
}
inline hb::Json save(const State& s){return {{"v",2},{"xp",s.xp},{"walkPhase",s.walkPhase},{"claims",s.claims},{"phase",s.phase},{"skyPhase",s.skyPhase},{"context",s.context}};}
inline bool restore(State& s,const hb::Json& value,const hb::Json& levels=data().at("levels")){
 if(value.is_null()){s={};return true;}if(!value.is_object()||(value.value("v",0)!=1&&value.value("v",0)!=2)||!value.contains("xp")||!value["xp"].is_number_integer())return false;
 State next;next.xp=value["xp"];next.walkPhase=value.value("walkPhase",0.f);next.phase=value.value("phase",0);next.skyPhase=value.value("skyPhase",next.phase==1?1:0);next.context=value.value("context",std::string("chapter"));next.claims=value.value("claims",std::set<std::string>{});
 if(next.xp<0||next.xp>168500||!std::isfinite(next.walkPhase)||next.walkPhase<0||next.walkPhase>=3.14159265f||next.phase<0||next.phase>2||next.claims.size()>4096)return false;
 if(next.skyPhase<0||next.skyPhase>2)return false;if(next.context!="chapter"&&next.context!="extra"&&next.context!="epilogue"&&next.context!="trial")return false;
 for(const auto& id:next.claims)if(id.empty()||id.size()>192)return false;
 // UI controller is transient: loading restores earned state without replaying its notification.
 next.displayed=level(next,levels);s=std::move(next);return true;
}
}
