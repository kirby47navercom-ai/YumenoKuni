#pragma once
#include <HBEngine/Game.hpp>
#include <algorithm>
#include <cmath>
#include <functional>
#include <map>
#include <set>
#include <string>
#include <vector>
namespace machinev4 {
enum class Phase {Select,Pay,Reveal,Prize,Extra,Closing};
struct State {Phase phase=Phase::Select;int selected=0,cost=0,draws=0;float extra=0;bool fresh=false;std::string prize;};
inline float repeatPercent(int total,int known,int coins){
 if(total<=0)return 0;if(known>=total)return 100;float rate=100.f*known/total;
 if(coins<=1)return rate;if(coins==100)return 0;return std::max(0.f,rate-100.f*coins/total);
}
inline float extraChance(int coins){return coins==100?1.f:std::clamp(.1f+.009f*coins,0.f,1.f);}
inline bool success(float chance,std::uint32_t random){return chance*32768.f>=float(random&32767);}
inline void change(State& s,int delta,int balance){if(s.phase==Phase::Select)s.selected=std::clamp(s.selected+delta,0,std::min(100,std::max(0,balance)));}
inline bool confirm(State& s,int balance){if(s.phase!=Phase::Select||s.selected<=0||s.selected>std::min(100,balance))return false;s.cost=s.selected;s.extra=extraChance(s.selected);s.draws=0;s.phase=Phase::Pay;return true;}
inline std::string choose(const std::vector<std::string>& pool,const std::set<std::string>& known,int coins,const std::function<std::uint32_t()>& random){
 if(pool.empty())throw std::runtime_error("Empty machine catalog");std::vector<std::string> old,fresh;for(const auto& id:pool)(known.count(id)?old:fresh).push_back(id);
 float chance=repeatPercent(int(pool.size()),int(old.size()),coins)/100.f;if(old.empty())chance=0;if(fresh.empty())chance=1;
 bool duplicate=success(chance,random());auto* chosen=duplicate?&old:&fresh;
 // Own safety adaptation for the retained inclusive-zero empty-pool boundary.
 if(chosen->empty())chosen=duplicate?&fresh:&old;return (*chosen)[random()%chosen->size()];
}
inline bool payAndAward(State& s,int& wallet,std::map<std::string,int>& inventory,std::set<std::string>& known,std::set<std::string>& newItems,const std::vector<std::string>& pool,const std::function<std::uint32_t()>& random){
 if(s.phase!=Phase::Pay||s.cost>wallet||pool.empty())return false;
 auto id=choose(pool,known,s.cost,random);wallet-=s.cost;s.fresh=known.insert(id).second;if(s.fresh)newItems.insert(id);inventory[id]=std::min(999,std::min(999,inventory[id])+1);s.prize=id;s.cost=s.selected=0;++s.draws;s.phase=Phase::Reveal;return true;
}
inline bool next(State& s,std::uint32_t random){if(s.phase!=Phase::Prize)return false;if(success(s.extra,random)){s.extra*=.5f;s.phase=Phase::Extra;return true;}s.phase=Phase::Select;return false;}
inline hb::Json save(const State& s){return {{"version",1},{"phase",int(s.phase)},{"selected",s.selected},{"cost",s.cost},{"draws",s.draws},{"extra",s.extra},{"fresh",s.fresh},{"prize",s.prize}};}
inline bool restore(State& out,const hb::Json& j,int wallet,const std::vector<std::string>& pool){try{if(!j.is_object()||j.value("version",0)!=1)return false;State s;s.phase=Phase(j.at("phase").get<int>());s.selected=j.at("selected").get<int>();s.cost=j.at("cost").get<int>();s.draws=j.at("draws").get<int>();s.extra=j.at("extra").get<float>();s.fresh=j.at("fresh").get<bool>();s.prize=j.at("prize").get<std::string>();if(int(s.phase)<0||int(s.phase)>4||s.selected<0||s.selected>std::min(100,wallet)||s.cost<0||s.cost>100||((s.phase==Phase::Reveal||s.phase==Phase::Prize||s.phase==Phase::Extra)&&(s.prize.empty()||s.draws==0||s.cost!=0||s.selected!=0))||(s.phase==Phase::Pay&&s.cost>wallet)||s.draws<0||!std::isfinite(s.extra)||s.extra<0||s.extra>1||(!s.prize.empty()&&std::find(pool.begin(),pool.end(),s.prize)==pool.end()))return false;out=std::move(s);return true;}catch(const std::exception&){return false;}}
}
