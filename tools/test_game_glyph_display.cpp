#include "../Game/Source/GlyphDisplayV4.hpp"
#include <cassert>
#include <cmath>
#include <iostream>
using namespace glyphdisplayv4;
int main(){
 Batch batch;std::map<std::string,Values> expected,actual;std::size_t before=0,after=0,checks=0;
 auto flush=[&]{batch.flush([&](const std::string& id,const Values& v,unsigned mask){auto& a=actual[id];if(mask&Visible){a.visible=v.visible;++after;}if(mask&Text){a.text=v.text;++after;}if(mask&Position){a.position=v.position;++after;}if(mask&Scale){a.scale=v.scale;++after;}if(mask&Rotation){a.rotation=v.rotation;++after;}if(mask&Opacity){a.opacity=v.opacity;++after;}});};
 for(int frame=0;frame<1200;frame++){
  for(int i=0;i<74;i++){
   const auto id=std::to_string(i);auto& old=expected[id];Values v;
   v.visible=(frame+i)%101<80;v.opacity=(frame+i*3)%90<60?0.f:float((frame+i)%7)/6;
   v.text="glyph"+std::to_string((frame/20+i)%50);v.position={float(frame+i)*.75f,float(frame-i)*.25f};v.scale={1+(frame%20)*.01f,1+(i%4)*.01f};v.rotation=float((frame+i)%360);
   if(old.visible!=v.visible){batch.visible(id,v.visible);++before;}if(old.text!=v.text){batch.text(id,v.text);++before;}if(!(old.position==v.position)){batch.position(id,v.position);++before;}if(!(old.scale==v.scale)){batch.scale(id,v.scale);++before;}if(old.rotation!=v.rotation){batch.rotation(id,v.rotation);++before;}if(old.opacity!=v.opacity){batch.opacity(id,v.opacity);++before;}old=v;
  }
  flush();for(const auto& [id,e]:expected){auto& a=actual[id];assert(a.visible==(e.visible&&e.opacity!=0));if(e.visible&&e.opacity!=0){assert(a.opacity==e.opacity);assert(a.text==e.text);assert(a.position==e.position);assert(a.scale==e.scale);assert(a.rotation==e.rotation);}++checks;}
 }
 const auto sent=after;flush();assert(after==sent);assert(after<before*.5);
 // A hidden state may receive its final pose before its visibility changes.
 batch.visible("late",false);batch.position("late",{12,34});batch.scale("late",{2,3});batch.text("late","final");batch.opacity("late",.5f);flush();assert(!actual["late"].visible);batch.visible("late",true);flush();assert(actual["late"].position==Point({12,34}));assert(actual["late"].scale==Point({2,3}));assert(actual["late"].text=="final"&&actual["late"].opacity==.5f);
 // A blank cell moves logically without producing pixels; a later glyph must
 // restore its latest pose before it becomes visible, even on the same layer.
 batch.text("late"," \t\r\n");flush();assert(!actual["late"].visible);
 const auto blankWrites=after;
 for(int i=0;i<60;i++){batch.position("late",{float(i),float(-i)});batch.scale("late",{2,3});batch.rotation("late",float(i));batch.opacity("late",.75f);flush();}
 assert(after==blankWrites);batch.text("late","한");flush();assert(actual["late"].visible);assert(actual["late"].position==Point({59,-59}));assert(actual["late"].rotation==59&&actual["late"].opacity==.75f);
 assert(!hasInk("")&&!hasInk(" ")&&hasInk("한")&&hasInk(" A "));
 std::cout<<"{\"ok\":true,\"visibleStateChecks\":"<<checks<<",\"baselineWrites\":"<<before<<",\"batchedWrites\":"<<after<<",\"reductionPercent\":"<<100.*(1.-double(after)/before)<<",\"gameplayLogicChanged\":false}\n";
}
