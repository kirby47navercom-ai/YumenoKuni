#include "Yumeno.h"
using namespace hb;

namespace {constexpr const char* DocumentWidget="v4story";}

bool Yumeno::v4DocumentOpen()const{
 if(!v4.active)return false;const auto& node=v4.current();auto kind=node.value("type",std::string());return kind=="document"||kind=="evidence"||(kind=="stage"&&node.value("showRecord",false));
}
void Yumeno::v4DocumentVisible(bool visible){for(auto id:{"DocumentShade","DocumentPaper","DocumentTitle","DocumentBody","DocumentHint"})UI::SetVisible(this,DocumentWidget,id,visible);}
void Yumeno::v4DocumentDraw(){
 bool picture=documentV4.imagePage();
 UI::SetPosition(this,DocumentWidget,"DocumentTitle",{245,105});UI::SetSize(this,DocumentWidget,"DocumentTitle",{790,66});UI::SetColor(this,DocumentWidget,"DocumentTitle",Color{1,1,1,1});UI::SetPosition(this,DocumentWidget,"DocumentHint",{245,655});UI::SetSize(this,DocumentWidget,"DocumentHint",{790,32});UI::SetColor(this,DocumentWidget,"DocumentHint",Color{1,1,1,1});
 // pad_bubble has transparent margins; its readable white area begins below
 // the widget origin. Keep all eight paginated lines inside that area.
 UI::SetPosition(this,DocumentWidget,"DocumentBody",{245,230});UI::SetSize(this,DocumentWidget,"DocumentBody",{790,260});
 UI::SetPosition(this,DocumentWidget,"DocumentPaper",picture?Vec2{70,60}:Vec2{190,75});UI::SetSize(this,DocumentWidget,"DocumentPaper",picture?Vec2{1140,570}:Vec2{900,560});UI::SetTexture(this,DocumentWidget,"DocumentPaper",picture?documentV4.image:std::string("Assets/Art/ui/v3/pad_bubble.webp"));
 UI::SetText(this,DocumentWidget,"DocumentTitle",picture?"":documentV4.title);UI::SetText(this,DocumentWidget,"DocumentBody",documentV4.text());
 UI::SetText(this,DocumentWidget,"DocumentHint",std::to_string(documentV4.page+1)+"/"+std::to_string(documentV4.count())+" · 방향키 넘기기 · Enter/클릭 "+(documentV4.final()?"닫기":"다음"));
 v4DocumentVisible(true);
}
std::string Yumeno::DocumentStats()const{return Json{{"page",documentV4.page},{"pages",documentV4.count()},{"final",documentV4.final()},{"imagePage",documentV4.imagePage()},{"text",documentV4.text()}}.dump();}
