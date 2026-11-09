#pragma once
#include <HBEngine/Game.hpp>
#include "GalleryV4.hpp"
#include <map>
#include <string>
namespace chapterarchive {
using hb::Json;
struct Entry {std::string chapter,node,slot;int type=0;};
using Index=std::map<std::string,Entry>;
inline std::string key(const std::string& chapter,int type){return chapter+":"+std::to_string(type);}
inline std::string slot(const std::string& chapter,int type){return campaignv4::slot("yumeno-v4-entry-"+chapter+"-"+std::to_string(type));}
inline Json save(const Index& entries){Json rows=Json::array();for(const auto& [id,e]:entries)rows.push_back({{"id",id},{"chapter",e.chapter},{"type",e.type},{"node",e.node},{"slot",e.slot}});return {{"version",1},{"entries",rows}};}
inline bool restore(Index& out,const Json& j){try{if(!j.is_object()||j.value("version",0)!=1||!j.contains("entries")||!j["entries"].is_array()||j["entries"].size()>28)return false;Index next;for(const auto& r:j["entries"]){Entry e{r.at("chapter").get<std::string>(),r.at("node").get<std::string>(),r.at("slot").get<std::string>(),r.at("type").get<int>()};auto id=r.at("id").get<std::string>();if((e.chapter!="P"&&(e.chapter.size()!=1||e.chapter[0]<'1'||e.chapter[0]>'6'))||e.type<0||e.type>3||e.node.empty()||e.node.size()>192||id!=key(e.chapter,e.type)||e.slot!=slot(e.chapter,e.type)||!next.emplace(id,e).second)return false;}out=std::move(next);return true;}catch(const std::exception&){return false;}}
inline const char* label(int type){return type==0?"장 시작":type==1?"자유행동":type==2?"수사":type==3?"학급재판":"재판 결과";}
// Read the common history cooperatively before replacing the live story state.
struct Replay {Json common;galleryv4::ReadJob current,banks;std::set<std::string> reads;int phase=0;};
inline bool beginReplay(Replay& out,const Json& common,const std::vector<Json>& banks,const std::set<std::string>& liveRead){
 try{Replay next;next.common=common;next.reads=liveRead;
  if(!common.is_object()||(!common.empty()&&!campaignv4::matches(common)))return false;
  if(common.value("progressFormat",std::string())=="parts-v1"&&(!savev4::validSnapshot(common.value("snapshot",std::string()))||!common.contains("readParts")))return false;
  galleryv4::enqueue(next.current,common);std::set<std::string> seen;
  for(const auto& bank:banks){if(!bank.is_object()||bank.empty())continue;auto id=bank.value("snapshot",std::string());if(!id.empty()&&!seen.insert(id).second)continue;galleryv4::enqueue(next.banks,bank);}
  out=std::move(next);return true;
 }catch(const std::exception&){return false;}
}
// One part read or 100 IDs per update; a damaged current save blocks replay.
inline int replayStep(Replay& job,const std::function<Json(const std::string&)>& load){
 if(job.phase<0)return -1;if(job.phase==2)return 1;
 auto& reader=job.phase==0?job.current:job.banks;
 for(const auto& id:galleryv4::readStep(reader,load))job.reads.insert(id);
 if(!reader.done)return 0;
 if(job.phase==0){if(reader.errors){job.phase=-1;return -1;}job.phase=1;return 0;}
 if(!galleryv4::readable(reader)){job.phase=-1;return -1;}job.phase=2;return 1;
}
inline void mergeReplay(Json& entry,const Replay& job){
 if(job.phase!=2)throw std::runtime_error("Chapter replay history is not ready");
 auto next=entry;for(auto key:{"coins","pulls","bonds","gifts","giftKnown","giftNew","growth","playerProgress","exploreReactions","galleryBank"})if(job.common.contains(key))next[key]=job.common[key];
 auto reads=entry.value("read",std::set<std::string>{});reads.insert(job.reads.begin(),job.reads.end());next["read"]=reads;entry=std::move(next);
}
}
