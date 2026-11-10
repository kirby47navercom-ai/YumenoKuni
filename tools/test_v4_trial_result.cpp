#include "../Game/Source/TrialResultV4.hpp"
#include "../Game/Source/SaveV4.hpp"
#include <cassert>
#include <iostream>
int main(){
 using namespace resultv4;using hb::Json;
 assert(raw(0,601)==101&&raw(0,601,true)==152&&raw(1,601,true)==152&&raw(6,601,true)==101);
 assert(raw(5,59)==0&&raw(7,59)==9&&raw(4,59)==10&&raw(5,601)==100&&raw(7,601)==100);
 assert(weighted(1500,0,0)==960&&weighted(1500,1,1)==1500&&weighted(1500,2,2)==2160);
 State s;begin(s,"1");Record x;x.id="NS-1";x.type=0;x.initial=18000;x.remaining=9000;x.raw=1500;
 assert(capture(s,x));assert(!capture(s,x));assert(s.current.records.size()==1&&s.current.pending==x.id);
 State resumed;assert(restore(resumed,save(s))&&resumed.current.pending==x.id);assert(!capture(resumed,x));commit(resumed,x.id,true);commit(resumed,x.id,true);assert(resumed.current.records.size()==1&&resumed.current.records[0].back&&resumed.current.pending.empty());
 for(int i=1;i<10;i++){x.id="NS-"+std::to_string(i+1);assert(capture(resumed,x));commit(resumed,x.id);}
 resumed.current.gaffe=1;resumed.current.retry=1;int wallet=900;assert(settle(resumed,wallet,true)==138);assert(resumed.current.total==13900&&wallet==999&&resumed.best.at("1").total==13900);
 assert(settle(resumed,wallet,true)==0&&wallet==999);auto paid=save(resumed);assert(restore(s,paid)&&s.current.paid);wallet=0;assert(settle(s,wallet,false)==0&&wallet==0);
 // Best record replacement includes ties, but every distinct result pays its current award.
 begin(s,"1");x.id="new";x.raw=13900;x.initial=120000;x.remaining=83400;assert(capture(s,x));commit(s,x.id);assert(settle(s,wallet,false)==69&&s.best.at("1").records[0].id=="new");
 begin(s,"1");x.id="lower";x.raw=1000;assert(capture(s,x));commit(s,x.id);assert(settle(s,wallet,false)==5&&s.best.at("1").records[0].id=="new");
 auto previous=save(s);auto invalid=previous;invalid["current"]["records"][0]["remaining"]=-1;assert(!restore(s,invalid)&&save(s)==previous);invalid=previous;invalid["current"]["pending"]="unknown";assert(!restore(s,invalid));
 assert(restore(s,Json())&&s.best.empty()&&s.current.records.empty());
 for(int ch=1;ch<=6;ch++){begin(s,std::to_string(ch));for(int i=0;i<50;i++){x.id="T"+std::to_string(ch)+":"+std::to_string(i);x.type=i%9;x.raw=1000;x.initial=18000;x.remaining=6000;capture(s,x);commit(s,x.id);}settle(s,wallet,false);}
 auto full=save(s);assert(restore(resumed,full)&&resumed.best.size()==6&&resumed.current.records.size()==50);
 auto compact=summary(s);assert(full.dump().size()>4096&&compact.dump().size()<3000);assert(compact["best"].size()==6&&compact["current"]["records"]==50&&compact["best"]["6"]["paid"]==true);assert(save(s)==full);
 Json snapshot{{"trialResults",full},{"read",Json::array()},{"log",Json::array()}};auto package=savev4::pack(snapshot,"1793330000000-1");assert(package.head.dump().size()<200000);
 // This is a data/calculation test only. No original or own game is executed.
 std::cout<<"PASS: score quantization, pending/return, entry payout, tie best, legacy migration, malformed save and six-chapter/50-phase capacity ("<<package.head.dump().size()<<" header bytes)\n";
}
