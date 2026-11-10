#include "../Game/Source/PlayerProgressV4.hpp"
#include "../Game/Source/SaveV4.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
#include <map>
static std::map<std::string,std::string> storage;
static int operations=0;
static std::string failSlot;
std::string hb::Data::GetText(const std::string& file){std::ifstream in("Game/"+file);if(!in)throw std::runtime_error(file);return {std::istreambuf_iterator<char>(in),{}};}
std::string hb::Save::ReadText(const std::string& slot){++operations;return storage.count(slot)?storage.at(slot):"{}";}
void hb::Save::WriteText(const std::string& slot,const std::string& text){++operations;if(slot==failSlot)throw std::runtime_error("injected write failure");storage[slot]=text;}
void hb::Save::Delete(const std::string& slot){++operations;storage.erase(slot);}
int main(){
 using hb::Json;playerprogress::State s;assert(playerprogress::level(s)==1);
 playerprogress::gain(s,499);s.displayed=1;assert(playerprogress::claim(s,"out:1",1));assert(!playerprogress::claim(s,"out:1",1));assert(s.xp==500&&playerprogress::fullGauge(s,2));
 assert(playerprogress::tick(s,2)==0&&s.displayed==2&&s.popup==1);assert(playerprogress::tick(s,2)==1&&s.popup==2&&s.frame==0);
 for(int i=0;i<16;i++)playerprogress::tick(s,2);assert(s.frame==16&&s.hold==0);
 for(int i=0;i<60;i++)playerprogress::tick(s,3);assert(s.hold==60&&s.popup==2&&s.displayed==2);
 assert(playerprogress::tick(s,3)==2&&s.popup==3);for(int i=0;i<13;i++)playerprogress::tick(s,3);assert(s.frame==13&&s.popup==3);assert(playerprogress::tick(s,3)==3&&s.popup==0);assert(playerprogress::tick(s,3)==0&&s.displayed==3&&s.popup==1);
 playerprogress::State restored;assert(playerprogress::restore(restored,playerprogress::save(s)));assert(restored.xp==500&&restored.displayed==2&&restored.popup==0&&restored.claims.count("out:1"));
 auto before=playerprogress::save(restored);assert(!playerprogress::restore(restored,{{"v",2},{"xp",168501}})&&playerprogress::save(restored)==before);assert(playerprogress::restore(restored,{{"v",1},{"xp",1250},{"walkPhase",.25}})&&restored.displayed==3&&restored.claims.empty());
 restored.skyPhase=2;restored.phase=0;playerprogress::State evening;assert(playerprogress::restore(evening,playerprogress::save(restored))&&evening.skyPhase==2&&evening.phase==0);assert(!playerprogress::restore(evening,{{"v",2},{"xp",0},{"skyPhase",3}}));assert(playerprogress::restore(evening,{{"v",1},{"xp",0},{"phase",1}})&&evening.skyPhase==1);
 Json small{{"node","old"},{"read",Json::array({"a"})},{"log",Json::array({{{"text","old"}}})}},large=small;large["node"]="new";large["read"]=Json::array();large["log"]=Json::array();
 for(int i=0;i<600;i++)large["read"].push_back("read:"+std::to_string(i));for(int i=0;i<2000;i++)large["log"].push_back({{"id",std::to_string(i)},{"text",std::string(400,'x')}});
 assert(savev4::write("head",small));auto old=storage.at("head");savev4::Writer w;assert(savev4::begin(w,"head",large));int result=0,steps=0;
 while(!result){operations=0;bool wasCommitted=w.committed;result=savev4::step(w);assert(operations<=2);if(!wasCommitted&&!w.committed)assert(storage.at("head")==old);assert(++steps<200);}
 assert(result==1&&savev4::read("head")["log"]==large["log"]);assert(savev4::begin(w,"manual",large));while(savev4::step(w)==0){}assert(savev4::read("manual")["node"]=="new");
 assert(savev4::write("head",small));assert(savev4::read("manual")["log"]==large["log"]);
 old=storage.at("head");assert(savev4::begin(w,"head",large));for(int i=0;i<3;i++)assert(savev4::step(w)==0);assert(storage.at("head")==old&&savev4::read("head")["node"]=="old");
 failSlot="head";while(savev4::step(w)==0){}assert(w.failed&&storage.at("head")==old&&savev4::read("head")["node"]=="old");
 std::cout<<"player growth + bounded multipart save PASS; 2000-log/600-read snapshot, atomic head, independent manual slot, interrupted/failed write preserves prior save\n";
}
