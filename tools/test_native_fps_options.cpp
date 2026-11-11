#include <HBEngine/Bridge.hpp>
#include "../Game/Source/OptionsV4.hpp"
#include <cassert>
#include <iostream>
int main(){
 optv4::Values v;assert(v.frameRate==120);auto j=optv4::Encode(v);optv4::Values d;assert(optv4::Decode(j,d)&&d.frameRate==120);
 for(int fps:{30,60,120}){v.frameRate=fps;assert(optv4::Decode(optv4::Encode(v),d)&&d.frameRate==fps);}
 j.erase("frameRate");assert(optv4::Decode(j,d)&&d.frameRate==120);j["version"]=1;assert(optv4::Decode(j,d)&&d.frameRate==120);
 for(int bad:{0,-1,59,61,144,10000}){j["frameRate"]=bad;assert(optv4::Decode(j,d)&&d.frameRate==120);}
 hb::Game::SetStateText("{\"unrelated\":{\"progress\":7}}");optv4::State s;s.values.frameRate=120;assert(optv4::Adjust(s,10,1)&&s.values.frameRate==30);assert(optv4::Adjust(s,10,1)&&s.values.frameRate==60);assert(optv4::Adjust(s,10,1)&&s.values.frameRate==120);assert(optv4::Adjust(s,10,-1)&&s.values.frameRate==60);
 const auto state=hb::Json::parse(hb::Game::GetStateText());assert(state["runtimeSettings"]["frameRate"]==60&&state["unrelated"]["progress"]==7);

 for(int mode:{0,1,2}){v.windowMode=mode;v.width=1600;v.height=900;assert(optv4::Decode(optv4::Encode(v),d)&&d.windowMode==mode&&d.width==1600&&d.height==900);}
 j=optv4::Encode(v);j.erase("windowMode");j.erase("width");j.erase("height");assert(optv4::Decode(j,d)&&d.windowMode==0&&d.width==1280&&d.height==720);
 j["windowMode"]=99;j["width"]=-1;j["height"]=99999;assert(optv4::Decode(j,d)&&d.windowMode==2&&d.width==1280&&d.height==720);
 assert(optv4::Adjust(s,14,1)&&s.values.frameRate==120);assert(optv4::Rows==15);std::cout<<"30/60/120 FPS encode/decode, legacy migration, invalid fallback, cycling, session apply, state preservation and defaults PASS\n";
}
