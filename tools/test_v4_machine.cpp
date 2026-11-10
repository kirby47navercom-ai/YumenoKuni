#include "../Game/Source/MachineV4.hpp"
#include <cassert>
#include <iostream>
int main(){
 using namespace machinev4;State s;int coins=200;std::map<std::string,int> items;std::set<std::string> known,newItems;std::vector<std::string> pool{"a","b","c"};
 change(s,200,coins);assert(s.selected==100&&coins==200);change(s,-100,coins);assert(!confirm(s,coins)&&coins==200);change(s,100,coins);assert(confirm(s,coins)&&coins==200);
 auto zero=[](){return 0u;};assert(payAndAward(s,coins,items,known,newItems,pool,zero)&&coins==100&&s.draws==1&&items["a"]==1&&known.count("a")&&newItems.count("a"));
 assert(!payAndAward(s,coins,items,known,newItems,pool,zero)&&coins==100);s.phase=Phase::Prize;
 for(int i=0;i<6;i++){assert(next(s,0)&&s.phase==Phase::Extra);s.phase=Phase::Pay;assert(payAndAward(s,coins,items,known,newItems,pool,zero)&&coins==100);s.phase=Phase::Prize;}
 assert(s.draws==7&&items["a"]==7);assert(!next(s,32767)&&s.phase==Phase::Select&&coins==100);
 // Possession zero still counts as previously discovered. 100 coins is not
 // absolute novelty: inclusive low15=0 selects the nonempty duplicate pool.
 items["a"]=0;assert(choose(pool,known,100,zero)=="a");assert(repeatPercent(3,1,100)==0&&repeatPercent(3,3,100)==100);
 items["a"]=999;s.phase=Phase::Pay;s.cost=0;assert(payAndAward(s,coins,items,known,newItems,pool,zero)&&items["a"]==999);
 std::uint32_t randoms[]{32767,1};int cursor=0;assert(choose(pool,known,100,[&](){return randoms[cursor++];})=="c");
 State restored;assert(restore(restored,save(s),coins,pool));auto before=save(restored),bad=before;bad["cost"]=101;assert(!restore(restored,bad,coins,pool)&&save(restored)==before);bad=before;bad["extra"]=-1;assert(!restore(restored,bad,coins,pool));
 s={};change(s,10,5);assert(s.selected==5);assert(!confirm(s,0));assert(success(0,0)&&!success(0,1)&&success(.5f,16384)&&!success(.5f,16385));
 std::cout<<"machine PASS: deferred debit, discovery vs quantity, source float/low15 boundaries,100-coin duplicate, free extras beyond4, one payout per state, safe empty pool, restore rejection\n";
}
