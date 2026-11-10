#include "../../Game/Source/GrowthV4.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
int main(){
 using namespace growthv4;J c,skills;std::ifstream("tools/v4_growth_contract.json")>>c;std::ifstream("data/skills.json")>>skills;
 State s;Init(s,c,skills);std::map<std::string,int> bonds;int coins=10;
 auto result=Observe(s,{{"fte:152:complete",true},{"fte:33:complete",true}},bonds,coins);
 assert(result.encounters.size()==1&&bonds["taiga"]==2&&coins==12&&s.fp==1&&s.fpClaims.size()==1&&s.owned.empty()&&s.equipped.empty());
 assert(!Observe(s,{{"fte:33:complete",true}},bonds,coins).changed);
 Observe(s,{{"fte:46:complete",true}},bonds,coins);assert(Level(s,4)==2&&!s.owned.count("taiga1")&&s.fp==2&&s.equipped.empty());
 // A real old entitlement remains usable, but new encounters never mint legacy skills.
 s.owned.insert("taiga1");
 assert(Toggle(s,"taiga1",6,true).changed&&Effect(s,"max_heart"));
 assert(!Toggle(s,"taiga1",6,false).changed&&s.equipped.count("taiga1"));
 auto legacy=Save(s);legacy["schemaVersion"]=1;legacy.erase("legacyBudget");State migrated;Init(migrated,c,skills);assert(Restore(migrated,legacy,1,1)&&Used(migrated)==2&&Capacity(migrated,1)==2&&migrated.legacyBudget==2);assert(Toggle(migrated,"taiga1",1,true).changed&&Capacity(migrated,1)==1);
 auto snapshot=Save(s);State restored;Init(restored,c,skills);assert(Restore(restored,snapshot,6));assert(Save(restored)==snapshot);
 assert(!Observe(restored,{{"fte:152:complete",true}},bonds,coins).changed);
 auto bad=snapshot;bad["equipped"].push_back("unknown");assert(!Restore(restored,bad,6)&&Save(restored)==snapshot);
 bonds["sora"]=18;bonds["nana"]=18;s.owned.insert("sora2");s.owned.insert("nana2");assert(Toggle(s,"sora2",6,true).changed);assert(Toggle(s,"nana2",6,true).reason=="insufficient-capacity");
 assert(Toggle(s,"nana2",16,true).reason=="conflicting-group");assert(Toggle(s,"sora2",6,true).changed);assert(Toggle(s,"nana2",6,true).changed);
 std::map<std::string,int> inventory{{"G11",2}};J giftFlags={{"fte:29:complete",true}};GiftContext context{"nana","window1",true,false,true,true};
 assert(!CommitGift(s,inventory,"not-authored","G11",giftFlags,context,true,true).changed&&inventory["G11"]==2);
 s.contract["giftOffers"]["test"]={{"actor","nana"},{"allowedGifts",J::array({"G11"})},{"acceptedNode","test:accepted"},{"requiresAnyCompletionFlags",J::array({"fte:29:complete"})},{"bondDelta",3}};
 context.present=false;assert(!CommitGift(s,inventory,"test","G11",giftFlags,context,true,true).changed);context.present=true;
 assert(!CommitGift(s,inventory,"test","G11",giftFlags,context,true,false).changed);
 auto given=CommitGift(s,inventory,"test","G11",giftFlags,context,true,true);assert(given.changed&&given.bonds==3&&inventory["G11"]==1);
 assert(!CommitGift(s,inventory,"test","G11",giftFlags,context,true,true).changed&&inventory["G11"]==1);
 State gifted;Init(gifted,s.contract,skills);assert(Restore(gifted,Save(s),16)&&gifted.giftReceipts.size()==1);
 State shop;Init(shop,c,skills);shop.fp=40;
 assert(Purchase(shop,"v3_voice1",false,true).reason=="not-confirmed"&&shop.fp==40&&shop.owned.empty());
 assert(!Purchase(shop,"v3_voice1",true,false).changed&&shop.fp==40);
 assert(Purchase(shop,"v3_voice1",true,true).changed&&shop.fp==36&&shop.equipped.empty());
 assert(!Purchase(shop,"v3_voice1",true,true).changed&&shop.fp==36);
 assert(!Purchase(shop,"v3_voice2",true,true).changed&&shop.fp==36);
 assert(!Toggle(shop,"v3_voice1",3,true).changed&&Toggle(shop,"v3_voice1",4,true).changed&&MaximumHp(shop)==14000);
 shop.owned.insert("v3_voice2");assert(Toggle(shop,"v3_voice2",99,true).reason=="conflicting-group");
 Toggle(shop,"v3_voice1",99,true);assert(Toggle(shop,"v3_voice2",99,true).changed&&MaximumHp(shop)==20000);
 for(auto id:{"v3_focus1","v3_right_brain","v3_delusion"})assert(Purchase(shop,id,true,true).changed);
 assert(shop.fp==0&&!Purchase(shop,"v3_ponder",true,true).changed);
 for(auto id:{"v3_focus1","v3_right_brain","v3_delusion"})assert(Toggle(shop,id,99,true).changed);
 assert(MaximumMental(shop)==14000);int mental=14000,hp=10000;assert(MentalStep(shop,mental,hp,true,60)&&mental==11900&&hp==10120);
 mental=14000;hp=20000;MentalStep(shop,mental,hp,true,1);assert(mental==13965&&hp==20000);
 shop.owned.insert("v3_bed_making");assert(Toggle(shop,"v3_bed_making",99,true).changed);mental=1000;MentalStep(shop,mental,hp,false,60);assert(mental==2500&&hp==20000);
 mental=10;hp=10000;bool exhausted=false;MentalStep(shop,mental,hp,true,60,&exhausted);assert(exhausted&&mental==1475&&hp==10002); // no held-key depletion/reentry oscillation in a caught-up batch
 State learned;Init(learned,c,skills);int wallet=0;std::map<std::string,int> links;
 for(auto flag:{"fte:33:complete","fte:46:complete","fte:51:complete"})Observe(learned,{{flag,true}},links,wallet);
 assert(learned.fp==3&&learned.owned.count("v3_voice2")&&!learned.equipped.count("v3_voice2"));
 learned.fp=999;Observe(learned,{{"fte:20:complete",true}},links,wallet);assert(learned.fp==999&&learned.fpClaims.size()==4);
 auto modern=Save(learned);State copy;Init(copy,c,skills);assert(Restore(copy,modern,99)&&Save(copy)==modern);
 auto corrupt=modern;corrupt["fp"]=1000;assert(!Restore(copy,corrupt,99)&&Save(copy)==modern);corrupt=modern;corrupt["fpClaims"].push_back("rin:3");assert(!Restore(copy,corrupt,99));
 auto old=modern;old["schemaVersion"]=2;old.erase("fp");old.erase("fpClaims");assert(Restore(copy,old,99)&&copy.fp==0&&copy.fpClaims.empty());assert(!Observe(copy,{{"fte:33:complete",true}},links,wallet).changed&&copy.fp==0);
 State mine;Init(mine,c,skills);mine.fp=8;assert(!Purchase(mine,"v3_undo",true,true).changed&&mine.fp==8);
 for(auto flag:{"fte:25:complete","fte:43:complete","fte:52:complete"})Observe(mine,{{flag,true}},links,wallet);
 assert(mine.owned.count("v3_undo")&&mine.fp==11&&Toggle(mine,"v3_undo",4,true).changed&&Effect(mine,"undo_enable"));
 for(auto id:{"v3_safety","v3_tug"}){assert(Purchase(mine,id,true,true).changed);assert(Toggle(mine,id,12,true).changed);}
 assert(mine.fp==3&&Used(mine)==12&&Effect(mine,"safety_first")&&Effect(mine,"showdown_tug_half"));
 std::cout<<"growth fixture PASS\n";
}
