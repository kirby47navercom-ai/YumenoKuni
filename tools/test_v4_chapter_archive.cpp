#include "../Game/Source/ChapterArchiveV4.hpp"
#include "../Game/Source/SaveV4.hpp"
#include <cassert>
#include <iostream>
static std::map<std::string,std::string> storage;
static std::string failSlot;
static int operations=0;
std::string hb::Save::ReadText(const std::string& slot){++operations;return storage.count(slot)?storage.at(slot):"{}";}
void hb::Save::WriteText(const std::string& slot,const std::string& value){++operations;if(slot==failSlot)throw std::runtime_error("injected failure");storage[slot]=value;}
void hb::Save::Delete(const std::string& slot){++operations;storage.erase(slot);}
int main(){
 using namespace chapterarchive;using hb::Json;Index index,restored;
 for(auto ch:{"P","1","2","3","4","5","6"})for(int type=0;type<4;type++)index[key(ch,type)]={ch,"actual-node:"+key(ch,type),slot(ch,type),type};
 assert(restore(restored,save(index))&&restored.size()==28&&save(restored)==save(index));
 auto good=save(restored),bad=good;bad["entries"][0]["slot"]="yumeno-progress-v4";assert(!restore(restored,bad)&&save(restored)==good);
 bad=good;bad["entries"][0]["type"]=4;assert(!restore(restored,bad));bad=good;bad["entries"].push_back(bad["entries"][0]);assert(!restore(restored,bad));
 // Each replay entry owns independent multipart storage. Publishing an index
 // must follow complete readback; failures cannot unlock a phantom section.
 Json progress{{"chapter","3"},{"node","actual-node:3:2"},{"read",Json::array()},{"log",Json::array()}};
 for(int i=0;i<2000;i++)progress["log"].push_back({{"text",std::string(200,'x')}});
 savev4::Writer writer;auto entrySlot=slot("3",2);assert(savev4::begin(writer,entrySlot,progress));int result=0,steps=0;
 while(!result){operations=0;result=savev4::step(writer);assert(operations<=2);assert(++steps<128);}
 assert(result==1&&savev4::read(entrySlot)==savev4::unpack(writer.package.head,[](const std::string& p){return Json::parse(storage.at(p));}));
 Index published;published[key("3",2)]={"3",progress["node"].get<std::string>(),entrySlot,2};hb::Save::Write("index",save(published));auto oldIndex=storage.at("index");
 failSlot=slot("4",3);assert(savev4::begin(writer,failSlot,progress));while(savev4::step(writer)==0){}assert(writer.failed&&storage.at("index")==oldIndex);
 failSlot.clear();assert(savev4::write("yumeno-progress-v4",{{"node","other"}}));assert(savev4::read(entrySlot)["node"]=="actual-node:3:2");
 // Replaying an earlier reached entry must not erase later read/earned progress.
 auto entry=savev4::read(entrySlot);entry["read"]={"entry-only"};entry["flags"]={{"route","old"}};entry["evidence"]={{"old",{{"name","old"},{"text","old"}}}};entry["stack"]={{{"returnTo","old-return"}}};entry["coins"]=3;
 auto later=entry;later["contentVersion"]="v4";later["node"]="later-node";later["flags"]={{"route","future"}};later["read"]=Json::array();later["coins"]=71;later["growth"]={{"completed",{"earned-fte"}}};
 for(int i=0;i<45000;i++)later["read"].push_back("later-read:"+std::to_string(i));
 assert(savev4::write("yumeno-progress-v4",later));auto common=Json::parse(storage.at("yumeno-progress-v4"));
 auto bank=galleryv4::save({});bank["read"]={"bank-only","later-read:0"};assert(savev4::write("yumeno-v4-gallery",bank));auto currentBank=Json::parse(storage.at("yumeno-v4-gallery"));
 Replay replay;assert(beginReplay(replay,common,{currentBank,currentBank},{"live-only"}));auto entryBefore=entry;bool rejected=false;try{mergeReplay(entry,replay);}catch(const std::exception&){rejected=true;}assert(rejected&&entry==entryBefore);
 auto storageBefore=storage;int ticks=0;result=0;while(!result){operations=0;result=replayStep(replay,[](const std::string& key){assert(key.find("-log-")==std::string::npos);return Json::parse(hb::Save::ReadText(key));});assert(operations<=1);assert(++ticks<1000);}
 assert(result==1&&ticks>450&&storage==storageBefore);mergeReplay(entry,replay);
 auto merged=entry["read"].get<std::set<std::string>>();assert(merged.size()==45003&&merged.count("entry-only")&&merged.count("live-only")&&merged.count("bank-only")&&merged.count("later-read:44999"));
 assert(entry["coins"]==71&&entry["growth"]==later["growth"]&&entry["node"]==entryBefore["node"]&&entry["flags"]==entryBefore["flags"]&&entry["evidence"]==entryBefore["evidence"]&&entry["stack"]==entryBefore["stack"]&&entry["log"]==entryBefore["log"]);
 assert(savev4::write("replayed",entry)&&savev4::read("replayed")["read"]==entry["read"]);assert(storage.at("yumeno-progress-v4")==storageBefore.at("yumeno-progress-v4"));
 // A damaged canonical read part blocks replay even if a gallery bank is valid.
 auto damagedKey="yumeno-v4-"+common["snapshot"].get<std::string>()+"-read-0";auto savedPart=storage.at(damagedKey);storage.erase(damagedKey);storageBefore=storage;
 assert(beginReplay(replay,common,{currentBank},{}));result=0;while(!result)result=replayStep(replay,[](const std::string& key){return Json::parse(hb::Save::ReadText(key));});assert(result<0&&storage==storageBefore);storage[damagedKey]=savedPart;
 // Superseded optional banks may fail; a complete current bank preserves history.
 auto stale=currentBank;stale["snapshot"]="123-456";assert(beginReplay(replay,common,{stale,currentBank},{}));result=0;while(!result)result=replayStep(replay,[](const std::string& key){return Json::parse(hb::Save::ReadText(key));});assert(result==1&&replay.banks.errors==1&&replay.reads.count("bank-only"));
 assert(beginReplay(replay,common,{stale},{}));result=0;while(!result)result=replayStep(replay,[](const std::string& key){return Json::parse(hb::Save::ReadText(key));});assert(result<0);
 // Inline saves and no prior gallery remain compatible; reset/new-game is separate.
 assert(beginReplay(replay,Json{{"contentVersion","v4"},{"read",{"inline-read"}}},{},{}));result=0;while(!result)result=replayStep(replay,[](const std::string&){assert(false);return Json();});assert(result==1&&replay.reads.count("inline-read"));
 assert(!beginReplay(replay,Json{{"contentVersion","legacy"}},{},{}));assert(!beginReplay(replay,Json{{"contentVersion","v4"},{"progressFormat","parts-v1"},{"snapshot","bad"},{"readParts",0}},{},{}));
 std::cout<<"chapter archive PASS: 28-entry bound, cooperative writes/failure isolation; replay preserves 45000 global reads + entry/live/gallery union, earned inventory and original story cursor/flags/evidence/stack/log; <=1 read/update, no canonical log reads, no preparation writes, missing canonical/all-bank failures block, stale bank fallback, inline compatibility\n";
}
