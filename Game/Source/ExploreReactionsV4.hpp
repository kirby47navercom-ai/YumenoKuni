#pragma once
#include <HBEngine/Game.hpp>
#include <map>
#include <string>
namespace reactionv4 {
struct Object {int remaining=3,stock=2;};
using State=std::map<std::string,Object>;
struct Hit {int medals=0;bool accepted=false,completed=false;};
inline Hit hit(Object& x){Hit h;if(x.remaining<=0)return h;h.accepted=true;if(x.stock>0){--x.stock;h.medals=1;}h.completed=--x.remaining==0;return h;}
inline hb::Json save(const State& s){hb::Json out=hb::Json::object();for(const auto& [id,x]:s)out[id]={x.remaining,x.stock};return out;}
inline bool restore(State& out,const hb::Json& j){try{State s;if(j.is_null()){out={};return true;}if(!j.is_object()||j.size()>128)return false;for(const auto& [id,v]:j.items()){if(id.empty()||id.size()>192||!v.is_array()||v.size()!=2||!v[0].is_number_integer()||!v[1].is_number_integer())return false;Object x{v[0].get<int>(),v[1].get<int>()};if(x.remaining<0||x.remaining>3||x.stock!=std::max(0,x.remaining-1))return false;s[id]=x;}out=std::move(s);return true;}catch(const std::exception&){return false;}}
}
