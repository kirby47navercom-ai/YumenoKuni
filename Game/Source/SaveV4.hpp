#pragma once
// The engine bounds each save JSON independently. Publish parts before the head.
#include <HBEngine/Game.hpp>
#include "CampaignRevisionV4.hpp"
#include <chrono>
#include <functional>
#include <vector>
namespace savev4 {
using J=hb::Json;
struct Part{std::string slot;J data;};
struct Package{J head;std::vector<Part> parts;};
inline std::string partSlot(const std::string& snapshot,const std::string& kind,int index){
 return campaignv4::slot("yumeno-v4-"+snapshot+"-"+kind+"-"+std::to_string(index));
}
inline std::string snapshotId(){static unsigned serial=0;auto stamp=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return std::to_string(stamp)+"-"+std::to_string(++serial);}
inline bool validSnapshot(const std::string& id){return !id.empty()&&id.size()<=40&&std::all_of(id.begin(),id.end(),[](char c){return (c>='0'&&c<='9')||c=='-';});}
inline Package pack(J progress,const std::string& snapshot){
 if(!validSnapshot(snapshot))throw std::runtime_error("Invalid V4 snapshot ID");
 Package p;auto reads=progress.value("read",J::array()),log=progress.value("log",J::array());progress.erase("read");progress.erase("log");
 p.head=std::move(progress);p.head["progressFormat"]="parts-v1";p.head["snapshot"]=snapshot;
 auto split=[&](const char* kind,const J& rows,int size){
  if(!rows.is_array())throw std::runtime_error("Invalid V4 progress collection");int count=0;
  for(std::size_t first=0;first<rows.size();first+=size){J chunk=J::array();for(std::size_t i=first;i<std::min(first+size,rows.size());i++)chunk.push_back(rows[i]);
   auto slot=partSlot(snapshot,kind,count);
   J body{{"version",1},{"snapshot",snapshot},{"kind",kind},{"index",count},{"rows",chunk}};
   if(body.dump().size()>200000)throw std::runtime_error("V4 save part exceeds bounded JSON");p.parts.push_back({slot,std::move(body)});count++;
  }p.head[std::string(kind)+"Parts"]=count;
 };
 split("read",reads,1000);split("log",log,100);
 if(p.head.dump().size()>200000)throw std::runtime_error("V4 progress header exceeds bounded JSON");return p;
}
inline J unpack(const J& head,const std::function<J(const std::string&)>& read){
 if(head.value("progressFormat","")!="parts-v1")return head;
 auto snapshot=head.value("snapshot",std::string());if(!validSnapshot(snapshot))throw std::runtime_error("Invalid saved V4 snapshot");
 J result=head;
 for(auto kind:{"read","log"}){
  int count=head.value(std::string(kind)+"Parts",-1);if(count<0||count>128)throw std::runtime_error("Invalid V4 save part count");J rows=J::array();
  for(int i=0;i<count;i++){
   auto body=read(partSlot(snapshot,kind,i));
   if(!body.is_object()||body.value("version",0)!=1||body.value("snapshot","")!=snapshot||body.value("kind","")!=kind||body.value("index",-1)!=i||!body.contains("rows")||!body["rows"].is_array()||body["rows"].size()>(std::string(kind)=="read"?1000:100))throw std::runtime_error("Damaged V4 save part");
   for(auto& row:body["rows"])rows.push_back(row);
  }result[kind]=std::move(rows);
 }
 return result;
}
inline bool write(const std::string& slot,const J& progress){
 try{
  J previous;try{previous=J::parse(hb::Save::ReadText(slot));}catch(const std::exception&){}
  auto package=pack(progress,snapshotId());
  for(auto& p:package.parts){hb::Save::Write(p.slot,p.data);if(J::parse(hb::Save::ReadText(p.slot))!=p.data)return false;}
  hb::Save::Write(slot,package.head);if(J::parse(hb::Save::ReadText(slot))!=package.head)return false;
  // Only the superseded, explicitly identified parts are eligible after commit.
  try{if(previous.is_object()&&previous.value("progressFormat","")=="parts-v1"){
   auto old=previous.value("snapshot",std::string());if(validSnapshot(old)&&old!=package.head["snapshot"]){
    for(auto kind:{"read","log"}){int count=previous.value(std::string(kind)+"Parts",-1);if(count<0||count>128)continue;
     for(int i=0;i<count;i++)try{hb::Save::Delete(partSlot(old,kind,i));}catch(const std::exception&){}
    }
   }
  }}catch(const std::exception&){}return true;
 }catch(const std::exception&){return false;}
}
inline J read(const std::string& slot){return unpack(J::parse(hb::Save::ReadText(slot)),[](const std::string& part){return J::parse(hb::Save::ReadText(part));});}
// Manual saves yield between bounded part writes. The old head stays valid until commit.
struct Writer {std::string slot;Package package;J previous;std::vector<std::string> obsolete;std::size_t at=0,clean=0;bool committed=false,failed=false;};
inline bool begin(Writer& w,const std::string& slot,const J& progress){
 try{w={};w.slot=slot;try{w.previous=J::parse(hb::Save::ReadText(slot));}catch(const std::exception&){}
 w.package=pack(progress,snapshotId());
 auto old=w.previous.is_object()?w.previous.value("snapshot",std::string()):std::string();if(w.previous.is_object()&&w.previous.value("progressFormat",std::string())=="parts-v1"&&validSnapshot(old)&&old!=w.package.head["snapshot"]){for(auto kind:{"read","log"}){int count=w.previous.value(std::string(kind)+"Parts",-1);if(count<0||count>128)throw std::runtime_error("Invalid previous part count");for(int i=0;i<count;i++)w.obsolete.push_back(partSlot(old,kind,i));}}return true;
 }catch(const std::exception&){w.failed=true;return false;}
}
// 0 pending,1 complete,-1 failure; at most one verified part/head or two obsolete deletes per call.
inline int step(Writer& w){
 if(w.failed||w.slot.empty())return -1;
 try{if(w.at<w.package.parts.size()){const auto& p=w.package.parts[w.at];hb::Save::Write(p.slot,p.data);if(J::parse(hb::Save::ReadText(p.slot))!=p.data)throw std::runtime_error("Part readback differs");++w.at;return 0;}
 if(!w.committed){hb::Save::Write(w.slot,w.package.head);if(J::parse(hb::Save::ReadText(w.slot))!=w.package.head)throw std::runtime_error("Head readback differs");w.committed=true;return 0;}
 for(int i=0;i<2&&w.clean<w.obsolete.size();i++,w.clean++)try{hb::Save::Delete(w.obsolete[w.clean]);}catch(const std::exception&){}
 return w.clean==w.obsolete.size()?1:0;
 }catch(const std::exception&){w.failed=true;return -1;}
}
} // namespace savev4
