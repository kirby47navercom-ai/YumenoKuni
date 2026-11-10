#include "../Game/Source/GalleryV4.hpp"
#include "../Game/Source/MachineV4.hpp"
#include <cassert>
#include <iostream>
static std::map<std::string,std::string> storage;
static std::string failSlot;static int operations=0;
std::string hb::Save::ReadText(const std::string& slot){++operations;return storage.count(slot)?storage.at(slot):"{}";}
void hb::Save::WriteText(const std::string& slot,const std::string& value){++operations;if(slot==failSlot)throw std::runtime_error("injected gallery write failure");storage[slot]=value;}
void hb::Save::Delete(const std::string& slot){++operations;storage.erase(slot);}
int main(){using namespace galleryv4;State s;int wallet=10;assert(!buy(s,"cg:a",5,wallet,true)&&wallet==10);assert(grant(s,"cg:a")&&!grant(s,"cg:a")&&fresh(s,"cg:a"));assert(!buy(s,"cg:a",5,wallet,false)&&wallet==10);assert(!buy(s,"cg:a",11,wallet,true));assert(buy(s,"cg:a",5,wallet,true)&&wallet==5&&status(s,"cg:a")==2&&fresh(s,"cg:a"));assert(!buy(s,"cg:a",5,wallet,true)&&wallet==5);assert(view(s,"cg:a")&&!fresh(s,"cg:a")&&!view(s,"cg:a"));State copy;assert(restore(copy,save(s))&&save(copy)==save(s));auto before=save(copy),bad=before;bad["purchased"].push_back("unearned");assert(!restore(copy,bad)&&save(copy)==before);State old;grant(old,"cg:a");merge(old,s);assert(status(old,"cg:a")==2&&!fresh(old,"cg:a"));
 Json story{{"node","actual-story"},{"coins",10},{"read",Json::array({"story-read"})},{"log",Json::array({{{"text","actual-dialogue"}}})}};assert(savev4::write("yumeno-progress-v4",story));Json common=Json::parse(storage.at("yumeno-progress-v4"));auto oldCommon=storage.at("yumeno-progress-v4");State unbought;grant(unbought,"cg:a");hb::Save::Write("yumeno-v4-gallery",save(unbought));auto oldProfile=storage.at("yumeno-v4-gallery");
 common["coins"]=wallet;machinev4::State machine;machine.selected=10;common["machine"]=machinev4::save(machine);std::set<std::string> reads;for(int i=0;i<5000;i++)reads.insert("real-read:"+std::to_string(i));SaveJob job;assert(beginSave(job,s,reads,common)&&job.canonical["machine"]["selected"]==5);failSlot="yumeno-progress-v4";int result=0;
 while(!result){operations=0;result=saveStep(job);assert(operations<=2);}assert(result<0&&storage.at("yumeno-progress-v4")==oldCommon&&storage.at("yumeno-v4-gallery")==oldProfile);
 failSlot="yumeno-v4-gallery";assert(beginSave(job,s,reads,common));result=0;while(!result){operations=0;result=saveStep(job);assert(operations<=2);}assert(result<0&&storage.at("yumeno-v4-gallery")==oldProfile);
 auto paid=Json::parse(storage.at("yumeno-progress-v4"));assert(paid["coins"]==5&&paid["node"]=="actual-story"&&machinev4::restore(machine,paid["machine"],paid["coins"],{"G01"})&&machine.selected==5);auto recover=savev4::unpack(paid["galleryBank"],[](const std::string& key){return Json::parse(storage.at(key));});assert(recover["read"].size()==5000&&restore(copy,recover)&&status(copy,"cg:a")==2);assert(savev4::read("yumeno-progress-v4")["read"]==story["read"]);
 failSlot.clear();assert(beginSave(job,s,reads,paid));result=0;while(!result){operations=0;result=saveStep(job);assert(operations<=2);}assert(result==1&&savev4::read("yumeno-v4-gallery")["read"].size()==5000&&Json::parse(storage.at("yumeno-progress-v4"))["coins"]==5);
 // Manual save still points to a retired bank. A complete current profile wins.
 auto stale=Json::parse(storage.at("yumeno-v4-gallery"));assert(beginSave(job,s,reads,Json::parse(storage.at("yumeno-progress-v4"))));result=0;while(!result)result=saveStep(job);assert(result==1);
 ReadJob reader;enqueue(reader,stale);enqueue(reader,Json::parse(storage.at("yumeno-v4-gallery")));std::set<std::string> recovered;
 int ticks=0;while(!reader.done){operations=0;for(const auto& id:readStep(reader,[](const std::string& slot){return Json::parse(hb::Save::ReadText(slot));}))recovered.insert(id);assert(operations<=1);assert(++ticks<2000);}assert(reader.errors==1&&readable(reader)&&recovered==reads);
 ReadJob broken;enqueue(broken,stale);while(!broken.done)readStep(broken,[](const std::string& slot){return Json::parse(hb::Save::ReadText(slot));});assert(broken.errors==1&&!readable(broken));
 std::cout<<"gallery PASS: ownership/NEW/purchase, cancelled/insufficient/duplicate, corruption rejection; 5000-read bounded archive, canonical debit + entitlement commit, failure before/after head, recoverable profile, unchanged story cursor/read/log, wallet-machine reconciliation, stale manual bank skips to complete current archive, all-bank failure blocks commit\n";
}
