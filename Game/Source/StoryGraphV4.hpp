#pragma once
// Executable authored routes only. The manuscript block index is never executable.
#include <HBEngine/Game.hpp>
#include "CampaignRevisionV4.hpp"
#include <map>
#include <set>
#include <string>
#include <vector>
namespace storyv4 {
using J=hb::Json;
inline unsigned bucket(const std::string& id,unsigned count){std::uint32_t h=2166136261u;for(unsigned char c:id){h^=c;h*=16777619u;}return h%count;}
inline const J& bucketData(const std::string& prefix,unsigned index){
 unsigned packs=prefix=="Assets/Data/v4_story/native_tasks/"?32:prefix=="Assets/Data/v4_story/gallery_map/"?4:prefix=="Assets/Data/v4_story/gallery_records/"?5:0;
 static std::map<std::string,J> cache;auto key=prefix+(packs?"pack_"+std::to_string(index%packs):std::to_string(index))+".json";
 auto found=cache.find(key);if(found==cache.end())found=cache.emplace(key,hb::Data::Get(key)).first;
 return packs?found->second.at("buckets").at(std::to_string(index)):found->second;
}
inline const J& lookup(const J& graph,const std::string& id){
 if(graph.value("storage","")!="hash-shards-v1")return graph.at("nodes").at(id);
 const auto& page=bucketData(graph.at("bucketPrefix").get<std::string>(),bucket(id,graph.at("bucketCount").get<unsigned>()));
 const auto& n=page.at("nodes").at(id);auto ch=graph.value("chapter",std::string());int scope=ch=="P"?0:ch.size()==1&&ch[0]>='1'&&ch[0]<='6'?ch[0]-'0':-1;
 if(scope>=0&&!(n.value("scope",0)&(1<<scope)))throw std::runtime_error("V4 node belongs to a different chapter");
 return n;
}
inline bool has(const J& graph,const std::string& id){try{lookup(graph,id);return true;}catch(const std::exception&){return false;}}
struct Frame {std::string next;J onReturn=J::object();};
struct State {
 J graph,flags=J::object(),evidence=J::object();std::set<std::string> read;std::string node,section,blocked;std::vector<Frame> stack;
 std::vector<J> log;bool active=false,restoring=false;int generation=0,shownStages=0;
 const J& current()const{return lookup(graph,node);}
};
inline bool valid(const J& g){
 if(g.is_object()&&g.value("schemaVersion",0)==1&&g.value("contentVersion","")=="v4"&&g.value("storage","")=="hash-shards-v1"){
  const auto prefix=g.value("bucketPrefix","");const int buckets=g.value("bucketCount",0);
  const bool authored=prefix=="Assets/Data/v4_story/nodes/"&&buckets==128;
  const bool preview=g.value("campaignRevision","")=="rewrite-v5"&&prefix=="Assets/Data/v4_story/revision/nodes/"&&buckets==32;
  return (authored||preview)&&has(g,g.value("entry",""));
 }
 if(!g.is_object()||g.value("schemaVersion",0)!=1||g.value("contentVersion","")!="v4"||!g.contains("nodes")||!g["nodes"].is_object())return false;
 if(!g["nodes"].contains(g.value("entry","")))return false;
 const auto& nodes=g["nodes"];
 for(const auto& [id,n]:nodes.items()){
  if(!n.is_object()||n.value("id","")!=id)return false;
  for(auto key:{"next","target","returnTo","default","success","wrong"})if(n.contains(key)&&(!n[key].is_string()||!nodes.contains(n[key].get<std::string>())))return false;
  for(auto key:{"options","cases"})if(n.contains(key)){if(!n[key].is_array())return false;for(auto& o:n[key])if(!o.contains("to")||!o["to"].is_string()||!nodes.contains(o["to"].get<std::string>()))return false;}
 }
 return true;
}
inline bool jump(State& s,const std::string& id){
 if(!has(s.graph,id)){s.blocked="Missing authored route: "+id;return false;}
 s.node=id;s.generation++;s.blocked.clear();return true;
}
inline void setFlags(State& s,const J& values){if(values.is_object())for(auto& [k,v]:values.items())s.flags[k]=v;}
inline const J& enter(State& s){const auto& node=s.current();setFlags(s,node.value("set",J::object()));return node;}
inline bool route(State& s){
 const auto& n=s.current();auto type=n.value("type","");
 if(type=="branch"){
  for(auto& c:n["cases"])if(s.flags.contains(c.value("flag",""))&&s.flags[c.value("flag","")]==c["equals"])return jump(s,c["to"].get<std::string>());
  return jump(s,n.value("default",""));
 }
 if(type=="call"){
  if(s.stack.size()>=32){s.blocked="Authored call stack exceeds 32";return false;}
  s.stack.push_back({n.value("returnTo",""),n.value("onReturnSet",J::object())});return jump(s,n.value("target",""));
 }
 if(type=="return"){
  if(s.stack.empty()){s.blocked="Return without an authored caller";return false;}
  auto f=s.stack.back();s.stack.pop_back();setFlags(s,f.onReturn);return jump(s,f.next);
 }
 return false;
}
inline bool eligible(const State& s,const J& option){
 auto requires=option.value("requires",J::object());if(!requires.is_object())return false;
 for(auto& [key,value]:requires.items())if(s.flags.contains(key)?s.flags[key]!=value:value!=false)return false;return true;
}
inline bool choose(State& s,int index){
 const auto& n=s.current();if(n.value("type","")!="menu"||index<0||index>=int(n["options"].size()))return false;
 auto o=n["options"][index];if(!eligible(s,o))return false;setFlags(s,o.value("set",J::object()));return jump(s,o.value("to",""));
}
inline J save(const State& s){
 auto frames=J::array();for(auto& f:s.stack)frames.push_back({{"returnTo",f.next},{"onReturnSet",f.onReturn}});
 J result{{"schemaVersion",1},{"contentVersion","v4"},{"chapter",s.graph.value("chapter","")},{"node",s.node},{"generation",s.generation},{"flags",s.flags},{"evidence",s.evidence},{"read",s.read},{"stack",frames},{"log",s.log}};
 if(s.graph.contains("campaignRevision"))result["campaignRevision"]=s.graph.at("campaignRevision");
 return result;
}
inline bool restore(State& out,const J& g,const J& data){
 if(!valid(g)||!data.is_object()||data.value("schemaVersion",0)!=1||data.value("contentVersion","")!="v4"||data.value("chapter","")!=g.value("chapter","")||!has(g,data.value("node","")))return false;
 if(data.value("campaignRevision",std::string())!=g.value("campaignRevision",std::string()))return false;
 State s;s.graph=g;s.node=data["node"].get<std::string>();s.flags=data.value("flags",J::object());if(!s.flags.is_object())return false;
 s.generation=data.value("generation",0);if(s.generation<0||s.generation>2000000000)return false;
 s.evidence=data.value("evidence",J::object());if(!s.evidence.is_object())return false;
 for(auto& [id,e]:s.evidence.items())if(!e.is_object()||!e.contains("name")||!e["name"].is_string()||!e.contains("text")||!e["text"].is_string())return false;
 s.read=data.value("read",std::set<std::string>{});
 auto frames=data.value("stack",J::array());if(!frames.is_array()||frames.size()>32)return false;
 for(auto& f:frames){if(!f.is_object()||!has(g,f.value("returnTo",""))||!f.value("onReturnSet",J::object()).is_object())return false;s.stack.push_back({f["returnTo"].get<std::string>(),f.value("onReturnSet",J::object())});}
 auto log=data.value("log",J::array());if(!log.is_array()||log.size()>2000)return false;
 for(auto& r:log){if(!r.is_object()||!r.contains("text")||!r["text"].is_string())return false;s.log.push_back(r);}
 s.active=true;s.restoring=true;out=std::move(s);return true;
}
} // namespace storyv4
