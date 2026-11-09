#pragma once
#include <HBEngine/Game.hpp>
#include <algorithm>
namespace difficultyv4 {
struct State {int logic=1,action=1;};
inline hb::Json save(const State& s){return {{"version",1},{"logic",s.logic},{"action",s.action}};}
inline bool restore(State& out,const hb::Json& j){try{if(j.is_null()||j.empty()){out={};return true;}if(!j.is_object()||j.value("version",0)!=1)return false;State s{j.at("logic").get<int>(),j.at("action").get<int>()};if(s.logic<0||s.logic>2||s.action<0||s.action>2)return false;out=s;return true;}catch(const std::exception&){return false;}}
inline void change(State& s,int row,int direction){if(row<0||row>1)return;int& value=row?s.action:s.logic;value=(value+(direction<0?2:1))%3;}
// WAK damage is scaled once. DAT-selected damage rows must not use this helper.
inline int wakDamage(int raw,int difficulty){return int(std::max(0,raw)*(difficulty==0?.25f:difficulty==1?.5f:1.f));}
inline int anagramDamage(int logic){return logic==0?500:logic==2?2000:1000;}
inline float anagramSpeed(int action){return float((std::clamp(action,0,2)+1)*32);}
inline int mineWidth(int action){return 18+2*std::clamp(action,0,2);}
// Own chapters1..3 use the source early row family,4..6 the advanced family.
inline int mineColors(int chapter,int logic){return chapter>=4&&logic>0?4:3;}
}
