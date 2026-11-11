#include <HBEngine/Bridge.hpp>
#include "../Game/Source/InvestigationV4.hpp"
#include <cassert>
#include <iostream>
int main(){
 using namespace investigationv4;
 const J hub={{"requiredSpotIds",{"a","b"}},{"requiredCards",{"record","prior"}},
 {"spots",J::array({J{{"id","a"},{"providesCards",{"record"}}},J{{"id","b"}},
 J{{"id","review"},{"providesCards",{"prior"}},{"missingCards",{"prior"}}}})}};
 J flags={{"spot:a:complete",true},{"spot:b:complete",true}};
 auto p=Check(hub,flags,{"record"});assert(!p.complete&&p.spots==2&&p.cards==1);
 assert(Eligible(hub["spots"][2],flags,{"record"}));
 assert(!Eligible(hub["spots"][2],flags,{"record","prior"}));
 p=Check(hub,flags,{"record","prior"});assert(p.complete);
 flags["spot:b:complete"]=false;p=Check(hub,flags,{"record","prior"});assert(!p.complete);
 flags["spot:b:complete"]="not a boolean";assert(!Done(flags,"b"));
 p=Check(hub,J::object(),{});assert(!p.complete&&p.missing.size()==2);
 J evidenceOnly=hub;evidenceOnly["finishOnRequiredCards"]=true;assert(Check(evidenceOnly,J::object(),{"record","prior"}).complete);
 J locked={{"requiresCards",{"record"}},{"requiresFlags",{{"unlocked",true}}}};
 assert(!Eligible(locked,J::object(),{"record"}));assert(Eligible(locked,J{{"unlocked",true}},{"record"}));
 J gather={{"requiredSpotIds",{"board"}},{"spots",J::array({J{{"id","board"}}})}};
 assert(!Check(gather,J::object(),{}).complete);assert(Check(gather,J{{"spot:board:complete",true}},{}).complete);
 std::cout<<"Investigation evidence/inspection gates, missing prior record, completed revisit, eligibility, malformed completion and boarding gate PASS\n";
}
