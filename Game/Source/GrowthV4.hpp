#pragma once
// Pure authored growth. Owner supplies story completion flags and inventory.
#include <HBEngine/Game.hpp>
#include <algorithm>
#include <map>
#include <set>
#include <string>
#include <vector>
namespace growthv4 {
using J=hb::Json;
struct State {J contract=J::object(),skills=J::array();std::set<std::string> completed,owned,equipped,giftClaims,fpClaims;J giftReceipts=J::array();int legacyBudget=0,fp=0;};
struct GiftContext {std::string actor,window;bool freeWindow=false,busy=true,present=false,originalIdentity=false;};
struct Result {bool changed=false;std::string reason;int bonds=0,coins=0;std::vector<std::string> encounters,unlocked;};
inline int Level(const State& s,int points){int level=1;for(auto& threshold:s.contract.at("policy").at("bondThresholds"))if(points>=threshold.get<int>())level++;return std::clamp(level-1,1,5);}
inline int LegacyCapacity(const State& s,int chapter){auto p=s.contract.at("policy");return std::min(p.value("maximumCapacity",16),p.value("initialCapacity",6)+p.value("capacityPerChapter",2)*std::max(0,chapter-1));}
inline int Capacity(const State& s,int actual){return std::max(std::clamp(actual,1,99),s.legacyBudget);}
inline const J* Skill(const State& s,const std::string& id){for(const auto& row:s.skills)if(row.value("id",std::string())==id)return &row;return nullptr;}
inline bool Supported(const State& s,const J& skill){auto effect=skill.value("effect",std::string());for(const auto& e:s.contract.at("supportedEffects"))if(e==effect)return true;return false;}
inline int Used(const State& s){int used=0;for(const auto& id:s.equipped)if(auto row=Skill(s,id))used+=row->value("sp",0);return used;}
inline void Init(State& s,const J& contract,const J& skillData){s=State{};s.contract=contract;s.skills=skillData.at("items");}
inline std::vector<std::string> Unlock(State& s,const std::map<std::string,int>& bonds){
 std::vector<std::string> out;for(const auto& row:s.skills){if(row.value("legacyOnly",false))continue;auto who=row.value("who",std::string());bool eligible=false;
  if(row.contains("masteryActor")){auto actor=row.at("masteryActor").get<std::string>();eligible=true;for(int episode=1;episode<=3;episode++)eligible=eligible&&s.completed.count(actor+":"+std::to_string(episode));}
  else if(!row.contains("sourceLabel")){auto at=bonds.find(who);int points=at==bonds.end()?0:at->second;eligible=Level(s,points)>=row.value("level",99);}
  if(eligible&&Supported(s,row)&&s.owned.insert(row.at("id").get<std::string>()).second)out.push_back(row.at("id").get<std::string>());
 }return out;
}
inline Result Purchase(State& s,const std::string& id,bool confirmed,bool editable){
 if(!editable)return {false,"editing-unavailable-in-current-mode"};auto row=Skill(s,id);
 if(!row||!Supported(s,*row)||row->value("legacyOnly",false))return {false,"unsupported-skill"};
 if(s.owned.count(id))return {false,"already-owned"};int cost=row->value("fp",0);
 if(cost<=0)return {false,"event-acquisition-only"};if(s.fp<cost)return {false,"insufficient-fp"};if(!confirmed)return {false,"not-confirmed"};
 s.fp-=cost;s.owned.insert(id);return {true,"purchased"};
}
inline Result Observe(State& s,const J& appliedFlags,std::map<std::string,int>& bonds,int& coins,bool grantRewards=true){
 Result out;if(!appliedFlags.is_object())return out;
 for(const auto& [flag,value]:appliedFlags.items()){
  if(!value.is_boolean()||!value.get<bool>()||!s.contract.at("flagIndex").contains(flag))continue;
  auto key=s.contract["flagIndex"][flag].get<std::string>();if(!s.completed.insert(key).second)continue;
  const auto& e=s.contract.at("entries").at(key);out.changed=true;out.encounters.push_back(key);
  if(grantRewards){int delta=s.contract["policy"].value("eventBond",0),money=s.contract["policy"].value("eventCoins",0);bonds[e.at("actor").get<std::string>()]+=delta;coins+=money;out.bonds+=delta;out.coins+=money;if(s.fpClaims.insert(key).second)s.fp=std::min(999,s.fp+s.contract["policy"].value("eventFP",1));}
 }
 out.unlocked=Unlock(s,bonds);return out;
}
inline Result Toggle(State& s,const std::string& id,int capacity,bool editable){
 if(!editable)return {false,"editing-unavailable-in-current-mode"};
 auto row=Skill(s,id);if(!row||!Supported(s,*row))return {false,"unsupported-skill"};
 if(s.equipped.count(id)){s.equipped.erase(id);s.legacyBudget=std::min(s.legacyBudget,Used(s));if(s.legacyBudget<=capacity)s.legacyBudget=0;return {true,"unequipped"};}
 if(!s.owned.count(id))return {false,"not-owned"};
 if(Used(s)+row->value("sp",0)>Capacity(s,capacity))return {false,"insufficient-capacity"};
 auto groupOf=[&](const J& r){if(r.contains("sourceGroup")){int group=r.at("sourceGroup").get<int>();return group<0?std::string():"source:"+std::to_string(group);}auto effect=r.value("effect",std::string());return effect=="max_heart"?std::string("source:0"):s.contract.at("effectGroups").value(effect,effect);};
 auto group=groupOf(*row);if(!group.empty())for(const auto& other:s.equipped){auto q=Skill(s,other);if(q&&groupOf(*q)==group)return {false,"conflicting-group"};}
 s.equipped.insert(id);return {true,"equipped"};
}
inline std::vector<J> Equipped(const State& s){std::vector<J> out;for(const auto& id:s.equipped)if(s.owned.count(id))if(auto row=Skill(s,id))out.push_back(*row);return out;}
inline bool Effect(const State& s,const std::string& effect){for(const auto& id:s.equipped)if(s.owned.count(id))if(auto row=Skill(s,id))if(row->value("effect",std::string())==effect)return true;return false;}
inline int MaximumHp(const State& s){return Effect(s,"voice_lv2")?20000:Effect(s,"voice_lv1")?14000:Effect(s,"max_heart")?12000:10000;}
inline int MaximumMental(const State& s){return Effect(s,"concentration_lv2")?20000:Effect(s,"concentration_lv1")?14000:10000;}
inline int FocusMaintenance(const State& s){return Effect(s,"right_brain")?35:50;}
inline int MentalRegen(const State& s){return Effect(s,"bed_making")?25:20;}
// Apply after the source-selected/WAK difficulty damage, exactly once.
inline int Damage(const State& s,int amount){return Effect(s,"viability")?int(std::max(0,amount)*.8f):std::max(0,amount);}
inline bool MentalStep(const State& s,int& mental,int& hp,bool held,int ticks,bool* exhausted=nullptr){
 bool focused=held&&mental>0,depleted=held&&mental<=0;
 for(int i=0;i<ticks;i++){if(held&&!depleted){mental=std::max(0,mental-FocusMaintenance(s));if(Effect(s,"delusion"))hp=std::min(MaximumHp(s),hp+2);if(mental==0)depleted=true;}else mental=std::min(MaximumMental(s),mental+MentalRegen(s));}
 if(exhausted)*exhausted=depleted;return focused;
}
inline J Pages(const State& s,const std::string& actor){J out=J::array();for(const auto& key:s.completed){const auto& e=s.contract.at("entries").at(key);if(e.value("actor",std::string())==actor)out.push_back(e);}return out;}
// Owner rechecks this immediately before mutation, not only when opening the picker.
inline bool GiftEligible(const State& s,const std::string& offer,const J& flags,const GiftContext& context){
 if(!context.freeWindow||context.busy||!context.present||!context.originalIdentity||context.window.empty())return false;
 const auto& offers=s.contract.at("giftOffers");if(!offers.contains(offer))return false;const auto& row=offers[offer];
 if(row.value("actor",std::string())!=context.actor)return false;
 if(s.giftClaims.count(offer+":"+context.window))return false;
 for(const auto& id:row.value("requiresAnyCompletionFlags",J::array())){auto key=id.get<std::string>();if(flags.contains(key)&&flags[key].is_boolean()&&flags[key].get<bool>())return true;}
 return false;
}
inline Result CommitGift(State& s,std::map<std::string,int>& inventory,const std::string& offer,const std::string& gift,const J& flags,const GiftContext& context,bool confirmed,bool accepted){
 if(!confirmed||!accepted)return {false,"not-accepted"};
 if(!GiftEligible(s,offer,flags,context))return {false,"authored-context-unavailable"};
 const auto& row=s.contract.at("giftOffers").at(offer);bool allowed=false;for(const auto& id:row.at("allowedGifts"))if(id==gift)allowed=true;
 if(!allowed||row.value("acceptedNode",std::string()).empty())return {false,"unbound-gift-response"};
 auto item=inventory.find(gift);if(item==inventory.end()||item->second<1)return {false,"not-owned"};
 auto claim=offer+":"+context.window;--item->second;s.giftClaims.insert(claim);
 s.giftReceipts.push_back({{"id",claim},{"actor",context.actor},{"giftId",gift},{"offer",offer},{"window",context.window}});
 Result out;out.changed=true;out.reason="consumed-one";out.bonds=row.value("bondDelta",0);return out;
}
inline J Save(const State& s){return {{"schemaVersion",3},{"contentVersion","v4"},{"completed",s.completed},{"owned",s.owned},{"equipped",s.equipped},{"giftClaims",s.giftClaims},{"giftReceipts",s.giftReceipts},{"legacyBudget",s.legacyBudget},{"fp",s.fp},{"fpClaims",s.fpClaims}};}
inline bool Restore(State& s,const J& data,int capacity,int oldChapter=1){
 try{int version=data.value("schemaVersion",0);if((version<1||version>3)||data.value("contentVersion",std::string())!="v4")return false;
 State next=s;next.completed=data.at("completed").get<std::set<std::string>>();next.owned=data.at("owned").get<std::set<std::string>>();auto equipped=data.at("equipped").get<std::set<std::string>>();next.equipped.clear();next.giftClaims=data.value("giftClaims",std::set<std::string>{});next.giftReceipts=data.value("giftReceipts",J::array());
 if(!next.giftReceipts.is_array()||next.giftReceipts.size()!=next.giftClaims.size())return false;
 std::set<std::string> receipts;for(const auto& r:next.giftReceipts){
  if(!r.is_object())return false;for(auto key:{"id","actor","giftId","offer","window"})if(!r.contains(key)||!r[key].is_string())return false;
  auto id=r["id"].get<std::string>(),offer=r["offer"].get<std::string>(),window=r["window"].get<std::string>();
  if(window.empty()||id!=offer+":"+window||!next.giftClaims.count(id)||!receipts.insert(id).second||!next.contract.at("giftOffers").contains(offer))return false;
  const auto& row=next.contract["giftOffers"][offer];if(row.value("actor",std::string())!=r["actor"].get<std::string>())return false;
  bool allowed=false;for(const auto& gift:row.at("allowedGifts"))if(gift==r["giftId"])allowed=true;if(!allowed)return false;
 }
 for(const auto& key:next.completed)if(!s.contract.at("entries").contains(key))return false;
 next.fp=version>=3?data.at("fp").get<int>():0;next.fpClaims=version>=3?data.at("fpClaims").get<std::set<std::string>>():std::set<std::string>{};if(next.fp<0||next.fp>999)return false;for(const auto& key:next.fpClaims)if(!next.completed.count(key))return false;
 for(const auto& id:next.owned){auto row=Skill(next,id);if(!row||!Supported(next,*row))return false;}
 int legacy=version==1?LegacyCapacity(s,oldChapter):data.value("legacyBudget",0);if(legacy<0||legacy>16)return false;next.legacyBudget=legacy;
 for(const auto& id:equipped)if(!Toggle(next,id,capacity,true).changed)return false;
 // Preserve old equipped skills without inventing XP; the compatibility floor can only shrink.
 next.legacyBudget=std::min(legacy,Used(next));if(next.legacyBudget<=capacity)next.legacyBudget=0;
 s=std::move(next);return true;
 }catch(const std::exception&){return false;}
}
} // namespace growthv4
