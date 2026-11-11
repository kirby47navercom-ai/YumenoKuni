#pragma once
#include <HBEngine/Game.hpp>
#include <set>
#include <string>
#include <vector>

namespace investigationv4 {
using J=hb::Json;
inline bool Done(const J& flags,const std::string& id){auto it=flags.find("spot:"+id+":complete");return it!=flags.end()&&it->is_boolean()&&it->get<bool>();}
inline bool Eligible(const J& spot,const J& flags,const std::set<std::string>& cards){
 if(spot.contains("requiresFlags"))for(const auto& [key,value]:spot["requiresFlags"].items())if(!flags.contains(key)||flags[key]!=value)return false;
 for(const auto& id:spot.value("requiresCards",J::array()))if(!cards.count(id.get<std::string>()))return false;
 if(spot.contains("missingCards")){bool missing=false;for(const auto& id:spot["missingCards"])if(!cards.count(id.get<std::string>()))missing=true;if(!missing)return false;}
 return true;
}
struct Progress {int spots=0,totalSpots=0,cards=0,totalCards=0;bool complete=false;std::vector<std::string> missing;};
inline Progress Check(const J& hub,const J& flags,const std::set<std::string>& cards){
 Progress p;
 for(const auto& id:hub.value("requiredSpotIds",J::array())){++p.totalSpots;if(Done(flags,id.get<std::string>()))++p.spots;}
 for(const auto& id:hub.value("requiredCards",J::array())){++p.totalCards;if(cards.count(id.get<std::string>()))++p.cards;else p.missing.push_back(id.get<std::string>());}
 p.complete=p.cards==p.totalCards&&(hub.value("finishOnRequiredCards",false)||p.spots==p.totalSpots);
 return p;
}
}
