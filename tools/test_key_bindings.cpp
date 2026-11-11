#include <HBEngine/Bridge.hpp>
#include "../Game/Source/GameInputV4.hpp"
#include "../Game/Source/OptionsV4.hpp"
#include <cassert>
#include <iostream>

int main(){
 using Input=gameinputv4::Input;
 const auto defaults=keybindv4::Defaults();assert(keybindv4::Valid(defaults));
 auto keys=defaults;keys["w"]="j";keys["mouse0"]="k";
 assert(keybindv4::Valid(keys));
 optv4::Values value,decoded;value.keys=keys;value.music=4;
 assert(optv4::Decode(optv4::Encode(value),decoded)&&decoded.keys==keys&&decoded.music==4);
 auto saved=optv4::Encode(value);saved.erase("keys");
 assert(optv4::Decode(saved,decoded)&&decoded.keys==defaults&&decoded.music==4);
 saved["version"]=1;assert(optv4::Decode(saved,decoded)&&decoded.keys==defaults);
 auto broken=keybindv4::Encode(keys);broken["w"]="e";
 assert(keybindv4::Decode(broken)==defaults);
 for(const auto& invalid:hb::Json::array({"Escape","Backspace","unknown",42,nullptr})){
  broken=keybindv4::Encode(keys);broken["w"]=invalid;assert(keybindv4::Decode(broken)==defaults);
 }
 keybindv4::active=keys;keybindv4::enabled=true;
 hb::bridgeInput={{"keys",{{"j",1},{"k",1},{"w",0},{"e",1}}}};
 assert(Input::IsKeyDown("w")&&Input::IsKeyDown("mouse0")&&Input::IsKeyDown("e"));
 keybindv4::enabled=false;
 assert(!Input::IsKeyDown("w")&&!Input::IsKeyDown("mouse0")&&Input::IsKeyDown("e"));
 const auto first=Input::PollPhysical();assert(first.held&&!first.pressed.empty());
 assert(Input::PollPhysical().pressed.empty());hb::bridgeInput["keys"]=hb::Json::object();
 assert(!Input::PollPhysical().held);hb::bridgeInput["keys"]["j"]=1;
 assert(Input::PollPhysical().pressed=="j");
 int points=0;
 for(hb::Vec2 size:std::array<hb::Vec2,6>{{{1280,720},{1920,1080},{2560,1440},{3440,1440},{3840,2160},{1600,1200}}}){
  const float fit=std::min(size.x/1280.f,size.y/720.f);
  for(hb::Vec2 expected:std::array<hb::Vec2,4>{{{64,80},{640,360},{1190,470},{950,110}}}){
   hb::Vec2 physical{expected.x*fit+(size.x-1280*fit)*.5f,expected.y*fit+(size.y-720*fit)*.5f};
   auto p=Input::CanvasPosition(physical,size,{1280,720},true);
   assert(std::abs(p.x-expected.x)<.001&&std::abs(p.y-expected.y)<.001);++points;
   p=Input::CanvasPosition({expected.x*fit,expected.y*fit},size,{1280,720},false);
   assert(std::abs(p.x-expected.x)<.001&&std::abs(p.y-expected.y)<.001);++points;
  }
 }
 assert(optv4::ExploreHint(value,true).find("J")!=std::string::npos);
 optv4::RestoreSourceDefaults(value);assert(value.keys==defaults);
 std::cout<<"Bindings roundtrip/legacy/conflict/invalid fallback, physical capture, modal bypass, remapped mouse/hold, defaults and "<<points<<" canvas roundtrips PASS\n";
}
