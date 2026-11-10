#include "../Game/Source/TaskGraphV4.hpp"
#include "../Game/Source/SaveV4.hpp"
#include <fstream>
#include <iostream>
#include <cassert>
using J=hb::Json;
static std::map<std::string,std::string> saveStore;
static bool failPartWrite=false,failCleanup=false;
void hb::Save::WriteText(const std::string& slot,const std::string& json){if(failPartWrite&&slot.rfind("yumeno-v4-",0)==0)throw std::runtime_error("injected part failure");saveStore[slot]=json;}
std::string hb::Save::ReadText(const std::string& slot){return saveStore.at(slot);}
void hb::Save::Delete(const std::string& slot){if(failCleanup)throw std::runtime_error("injected cleanup failure");saveStore.erase(slot);}
template<class F> bool rejects(F f){try{f();return false;}catch(const std::exception&){return true;}}
int main(){
 std::ifstream input("data/v4_story/native_tasks.json");J root;input>>root;auto& tasks=root["tasks"];
 auto bundle=tasks["T1-NS-A01"];J evidence=J::object();assert(rejects([&]{taskv4::prepare(bundle,evidence);}));
 evidence["v4:E1-01"]={{"name","owned"},{"text","actually acquired"}};
 auto prepared=taskv4::prepare(bundle,evidence);assert(prepared["options"].size()==1&&prepared["options"][0]["id"]=="v4:E1-01");
 assert(!evidence.contains("v4:E2-01"));
 J local=bundle;local["scopeOnlyEvidence"]=true;auto scoped=taskv4::prepare(local,J::object());assert(scoped["options"].size()==1);assert(evidence.size()==1);
 auto pending=bundle;pending["ready"]=false;assert(rejects([&]{taskv4::prepare(pending,evidence);}));
 auto lie=tasks["T1-LIE-01"];J node={{"success","fallback"}};
 auto a=taskv4::success(node,lie,"refute"),b=taskv4::success(node,lie,"lie");assert(a.target!=b.target&&a.sets.empty()&&b.sets["T1-LIE-B"]==true);
 assert(rejects([&]{taskv4::success(node,lie,"agree");}));
 J polygon=J::array({J::array({.1,.2}),J::array({.7,.2}),J::array({.7,.8}),J::array({.1,.8})});
 assert(taskv4::inside(polygon,.3,.5)&&taskv4::inside(polygon,.1,.2)&&!taskv4::inside(polygon,.9,.5));
 J progress={{"node","stable"},{"read",J::array()},{"log",J::array()}};
 for(int i=0;i<45000;i++)progress["read"].push_back("long-authored-node:"+std::to_string(i));
 for(int i=0;i<2000;i++)progress["log"].push_back({{"text",std::string(600,'x')},{"id",std::to_string(i)}});
 auto package=savev4::pack(progress,"1793272758494-1");assert(package.parts.size()==65);std::map<std::string,J> stored;
 for(auto& part:package.parts){assert(part.data.dump().size()<200000);stored[part.slot]=part.data;}
 auto restored=savev4::unpack(package.head,[&](const std::string& id){return stored.at(id);});assert(restored["read"]==progress["read"]&&restored["log"]==progress["log"]);
 stored.erase(package.parts.front().slot);assert(rejects([&]{savev4::unpack(package.head,[&](const std::string& id){return stored.at(id);});}));
 saveStore["progress"]=J{{"progressFormat",17}}.dump();assert(savev4::write("progress",progress));assert(savev4::read("progress")["read"]==progress["read"]);
 auto committed=saveStore.at("progress");failPartWrite=true;assert(!savev4::write("progress",progress));assert(saveStore.at("progress")==committed);failPartWrite=false;
 failCleanup=true;assert(savev4::write("progress",progress));assert(savev4::read("progress")["log"]==progress["log"]);failCleanup=false;
 auto superseded=J::parse(saveStore.at("progress"))["snapshot"].get<std::string>();assert(savev4::write("progress",progress));
 for(auto& [slot,text]:saveStore)assert(slot.rfind("yumeno-v4-"+superseded+"-",0)!=0);
 std::cout<<"PASS owned/scoped evidence, pending bindings, actual lie outcomes, polygon hits, 45000-read/2000-log split save, corrupt parts rejection\n";
}
