#pragma once
#include <HBEngine/Game.hpp>
#include "SaveV4.hpp"
#include <set>
#include <string>
#include <deque>
namespace galleryv4 {
using hb::Json;
// Replays use the source section's authored bed, not a nonexistent node.music.
// A missing binding inherits the preceding replay bed; explicit silence is retained.
inline std::pair<bool,std::string> replayMusic(const Json& node,const Json& chapter){
 if(node.contains("music"))return {true,node.at("music").get<std::string>()};
 auto source=node.value("source",Json::object());auto section=source.value("file",std::string())+":"+source.value("location",std::string());
 auto beds=chapter.value("presentation",Json::object()).value("sectionBeds",Json::object());
 if(beds.contains(section))return {true,beds.at(section).value("music",std::string())};
 return {false,{}};
}
// Use the actual saved current-episode choice. Missing/ambiguous history keeps
// the existing catalogue fallback; it is not proof of the original past room.
inline Json replayScene(const Json& node,const Json& flags){
 auto scene=node.value("scene",Json::object());int matches=0;Json selected;
 for(const auto& candidate:node.value("sceneVariants",Json::array())){
  bool eligible=true;for(const auto& condition:candidate.at("when")){
   auto key=condition.at("flag").get<std::string>();if(!flags.contains(key)||flags.at(key)!=condition.at("equals")){eligible=false;break;}
  }
  if(eligible){selected=candidate;++matches;}
 }
 return matches==1?selected:scene;
}
struct State {std::set<std::string> available,purchased,viewed;bool machine=false;};
inline bool grant(State& s,const std::string& id){return !id.empty()&&s.available.insert(id).second;}
inline int status(const State& s,const std::string& id){return s.purchased.count(id)?2:s.available.count(id)?1:0;}
inline bool fresh(const State& s,const std::string& id){return s.available.count(id)&&!s.viewed.count(id);}
inline bool buy(State& s,const std::string& id,int price,int& wallet,bool confirm){if(!confirm||price<0||wallet<price||status(s,id)!=1)return false;wallet-=price;s.purchased.insert(id);return true;}
inline bool view(State& s,const std::string& id){return status(s,id)==2&&s.viewed.insert(id).second;}
inline Json save(const State& s){return {{"version",1},{"available",s.available},{"purchased",s.purchased},{"viewed",s.viewed},{"machine",s.machine}};}
inline bool restore(State& out,const Json& j){try{if(j.is_null()||j.empty()){out={};return true;}if(!j.is_object()||j.value("version",0)!=1)return false;State s;s.available=j.at("available").get<std::set<std::string>>();s.purchased=j.at("purchased").get<std::set<std::string>>();s.viewed=j.at("viewed").get<std::set<std::string>>();s.machine=j.at("machine").get<bool>();if(s.available.size()>2000)return false;for(const auto& id:s.available)if(id.empty()||id.size()>160)return false;for(const auto& id:s.purchased)if(!s.available.count(id))return false;for(const auto& id:s.viewed)if(!s.purchased.count(id))return false;out=std::move(s);return true;}catch(const std::exception&){return false;}}
inline void merge(State& into,const State& from){into.available.insert(from.available.begin(),from.available.end());into.purchased.insert(from.purchased.begin(),from.purchased.end());into.viewed.insert(from.viewed.begin(),from.viewed.end());into.machine=into.machine||from.machine;}
// Old manual saves can retain a superseded bank pointer. Skip that candidate,
// but never publish a replacement archive unless a global bank was fully read.
struct ReadJob {std::deque<Json> heads;Json rows=Json::array();std::size_t at=0;int part=0,parts=0,errors=0;std::string snapshot;bool active=false,global=false,expected=false,completeGlobal=false,done=false;};
inline bool readable(const ReadJob& job){return job.done&&(!job.expected||job.completeGlobal);}
inline void enqueue(ReadJob& job,const Json& head){if(!head.is_object()||head.empty())return;job.heads.push_back(head);if(head.contains("available"))job.expected=true;}
inline std::vector<std::string> readStep(ReadJob& job,const std::function<Json(const std::string&)>& load){
 std::vector<std::string> added;if(job.done)return added;
 try{
  if(job.at<job.rows.size()){for(int n=0;n<100&&job.at<job.rows.size();n++,job.at++){auto id=job.rows[job.at].get<std::string>();if(id.empty()||id.size()>256)throw std::runtime_error("Invalid gallery read ID");added.push_back(std::move(id));}return added;}
  if(job.active&&job.part<job.parts){auto p=load(savev4::partSlot(job.snapshot,"read",job.part));if(!p.is_object()||p.value("version",0)!=1||p.value("snapshot",std::string())!=job.snapshot||p.value("kind",std::string())!="read"||p.value("index",-1)!=job.part||!p.contains("rows")||!p["rows"].is_array()||p["rows"].size()>1000)throw std::runtime_error("Invalid gallery read part");job.rows=p["rows"];job.at=0;++job.part;return added;}
  if(job.active&&job.global)job.completeGlobal=true;job.active=false;
  if(job.heads.empty()){job.done=true;return added;}
  auto head=job.heads.front();job.heads.pop_front();job.global=head.contains("available");job.rows=head.value("read",Json::array());job.at=0;job.part=0;job.parts=head.value("readParts",0);job.snapshot=head.value("snapshot",std::string());
  if(!job.rows.is_array()||job.rows.size()>4096||job.parts<0||job.parts>128||(job.parts&&!savev4::validSnapshot(job.snapshot)))throw std::runtime_error("Invalid gallery read head");job.active=true;
 }catch(const std::exception&){++job.errors;job.active=false;job.rows=Json::array();job.at=0;job.part=job.parts=0;}
 return added;
}
struct SaveJob {savev4::Writer writer;Json canonical;int phase=0;};
inline bool beginSave(SaveJob& job,const State& state,const std::set<std::string>& reads,Json canonical){try{job={};if(canonical.contains("machine")&&canonical["machine"].value("phase",-1)==0){auto& machine=canonical["machine"];machine["selected"]=std::clamp(machine.value("selected",0),0,std::min(100,std::max(0,canonical.value("coins",0))));}job.canonical=std::move(canonical);auto bank=save(state);bank["read"]=reads;bank["log"]=Json::array();if(!savev4::begin(job.writer,campaignv4::slot("yumeno-v4-gallery"),bank))return false;job.phase=1;return true;}catch(const std::exception&){return false;}}
inline int saveStep(SaveJob& job){
 try{if(job.phase==1){if(job.writer.at<job.writer.package.parts.size())return savev4::step(job.writer)<0?-1:0;
   if(!job.canonical.empty()){auto next=job.canonical;next["gallery"]=job.writer.package.head;next["galleryBank"]=job.writer.package.head;hb::Save::Write(campaignv4::slot("yumeno-progress-v4"),next);if(Json::parse(hb::Save::ReadText(campaignv4::slot("yumeno-progress-v4")))!=next)return -1;job.canonical=std::move(next);}job.phase=2;return 0;}
  if(job.phase==2){auto bank=job.writer.package.head;hb::Save::Write(campaignv4::slot("yumeno-v4-gallery"),bank);if(Json::parse(hb::Save::ReadText(campaignv4::slot("yumeno-v4-gallery")))!=bank)return -1;job.writer.committed=true;job.phase=3;return 0;}
  if(job.phase==3)return savev4::step(job.writer);return -1;
 }catch(const std::exception&){return -1;}
}
}
