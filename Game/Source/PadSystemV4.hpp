#include "PadWrapV4.hpp"
// V3's six system columns and distinct storage/backlog/theme/modal carriers.
// Geometry comes from the retained SFL contracts. Thirty independent manual
// saves, PC keys, slot labels and availability of supplied themes are own policy.
#include <ctime>
namespace padsystem {
inline bool hit(Vec2 p,const hb::Json& r){return p.x>=r[0].get<float>()&&p.x<r[0].get<float>()+r[2].get<float>()&&p.y>=r[1].get<float>()&&p.y<r[1].get<float>()+r[3].get<float>();}
inline void rect(hb::Actor* owner,const std::string& widget,const std::string& id,const hb::Json& r,float dx=0,float dy=0){widgetownersv4::UI::SetPosition(owner,widget,id,{r[0].get<float>()+dx,r[1].get<float>()+dy});widgetownersv4::UI::SetSize(owner,widget,id,{r[2].get<float>(),r[3].get<float>()});}
inline std::string time(){std::time_t t=std::time(nullptr);std::tm tm{};localtime_s(&tm,&t);char out[40];std::strftime(out,sizeof(out),"%Y/%m/%d  %H:%M:%S",&tm);return out;}
// Conservative word wrapping for variable already-read dialogue. The native
// ScrollBox needs an inner width below its scrollbar; don't add blank bottom.
inline std::pair<std::string,int> wrap(const std::string& text,float width,const std::string& font,float size){
 std::string out,word;float used=0;int lines=1;
 auto advance=[&](const std::string& g){return debate::em(g,font)*size;}; /* 글꼴 실측 폭(GlyphMetricsV4) */
 auto emit=[&](){if(word.empty())return;float length=0;for(const auto& g:debate::glyphs(word))length+=advance(g);if(used>0&&used+length>width){out+='\n';used=0;++lines;}for(const auto& g:debate::glyphs(word)){float w=advance(g);if(used+w>width){out+='\n';used=0;++lines;}out+=g;used+=w;}word.clear();};
 for(const auto& g:debate::glyphs(text)){if(g=="\n"){emit();out+='\n';used=0;++lines;}else if(g==" "){emit();{float sp=advance(" ");if(used>0&&used+sp<width){out+=' ';used+=sp;}}}else word+=g;}emit();return {out,lines};
}
}
void Yumeno::padSystemInit(){
 try{auto j=Json::parse(Save::ReadText(campaignv4::slot("yumeno-manual-index-v1")));if(j.is_object()&&j.value("version",0)==1&&j.contains("slots")&&j["slots"].is_object())padManualSlots=j["slots"];}catch(const std::exception&){}
 try{auto j=Json::parse(Save::ReadText("yumeno-pad-theme-v1"));padThemeSaveNo=std::clamp(j.value("saveNo",0),0,65535);}catch(const std::exception&){}
}
std::string Yumeno::padManualSlot()const{return campaignv4::slot("yumeno-manual-v1-"+std::to_string(std::clamp(padStorageRow,0,29)+1));}
void Yumeno::padThemeApply(){
 const auto pages=Data::Get("Assets/Data/v4_story/system_pages_layout.json");const auto themes=pages["theme"]["entries"];std::string image;
 for(const auto& theme:themes)if(theme.value("saveNo",-1)==padThemeSaveNo)image=theme.value("image",std::string());
 if(image.empty()&&!themes.empty()){padThemeSaveNo=themes[0].value("saveNo",0);image=themes[0].value("image",std::string());}
 if(!image.empty())UI::SetTexture(this,padui::ID,"PdFloor",image);
 pvis("PdThemeHome",padPageAt<0);if(padPageAt<0)UI::SetTexture(this,padui::ID,"PdThemeHome",std::string("Assets/Art/ui/v3/pad_home/")+padui::ICONS[padIcon].key+"_overlay.svg");
}
void Yumeno::padSystemClear(){
 for(auto id:{"padsystem","padstorage","padload","padtheme","padconfirm"})UI::Remove(this,id);
 if(padSystemLog){padSystemLog=false;v4Log(false);}padSystemVisible=false;padStorageBusy=false;padStorageDelay=0;padSavePhase=0;padSaveSnapshot=Json();padSaveWriter={};
}
int Yumeno::padManualSaveStep(){
 if(!v4.active)return padManualSave()?1:-1;
 if(!campaignv4::canSave(v4.graph))return -1;
 try{
  if(padSavePhase==0){if(!v4.blocked.empty())return -1;padSaveSnapshot=v4Snapshot();if(!savev4::begin(padSaveWriter,campaignv4::slot("yumeno-progress-v4"),padSaveSnapshot))return -1;padSavePhase=1;return 0;}
  int result=savev4::step(padSaveWriter);if(result<=0)return result;
  if(padSavePhase==1){if(!savev4::begin(padSaveWriter,padManualSlot(),padSaveSnapshot))return -1;padSavePhase=2;return 0;}
  auto next=padManualSlots;std::string place;if(world.data.contains("instances")&&world.data["instances"].contains(world.id))place=world.data["instances"][world.id].value("label",std::string());
  next[std::to_string(padStorageRow)]={{"kind","v4"},{"chapter",chapterAt==0?std::string("프롤로그"):"제"+std::to_string(chapterAt)+"장"},{"date",padsystem::time()},{"place",place}};
  Json index{{"version",1},{"slots",next}};Save::Write(campaignv4::slot("yumeno-manual-index-v1"),index);if(Json::parse(Save::ReadText(campaignv4::slot("yumeno-manual-index-v1")))!=index)return -1;padManualSlots=std::move(next);padSavePhase=0;padSaveSnapshot=Json();padSaveWriter={};return 1;
 }catch(const std::exception&){return -1;}
}
bool Yumeno::padManualSave(){
 try{
  if(!saveFlow())return false;auto slot=padManualSlot();bool ok=false;
  // Never alias the canonical parts-v1 head: its next write deletes its old
  // parts. Each manual slot owns an independently packed snapshot instead.
  if(v4.active)ok=savev4::write(slot,savev4::read(campaignv4::slot("yumeno-progress-v4")));
  else{auto j=Json::parse(Save::ReadText(SAVE_SLOT));Save::Write(slot,j);ok=Json::parse(Save::ReadText(slot))==j;}
  if(!ok)return false;
  std::string ch=chapterAt==0?"프롤로그":"제"+std::to_string(chapterAt)+"장",place;
  if(world.data.contains("instances")&&world.data["instances"].contains(world.id))place=world.data["instances"][world.id].value("label",std::string());
  padManualSlots[std::to_string(padStorageRow)]={{"kind",v4.active?"v4":"legacy"},{"chapter",ch},{"date",padsystem::time()},{"place",place}};
  Json index{{"version",1},{"slots",padManualSlots}};Save::Write(campaignv4::slot("yumeno-manual-index-v1"),index);return Json::parse(Save::ReadText(campaignv4::slot("yumeno-manual-index-v1")))==index;
 }catch(const std::exception&){return false;}
}
bool Yumeno::padManualLoad(){
 auto key=std::to_string(padStorageRow);if(!padManualSlots.contains(key))return false;
 bool ok=padManualSlots[key].value("kind",std::string())=="v4"?v4Load(padManualSlot()):loadFlow(padManualSlot());
 if(!ok)return false;padSystemClear();for(auto& [id,on]:pvisible)if(on){UI::SetVisible(this,padui::ID,id,false);on=false;}padPageAt=-1;titleMenu(false);UI::SetVisible(this,UI_ID,"Title",false);return true;
}
void Yumeno::padSystemDraw(){
 for(auto id:{"padsystem","padstorage","padload","padtheme","padconfirm"})UI::Remove(this,id);
 padSystemVisible=true;
 for(auto id:{"PdTitle","PdTint","PdSide","PdCoins","PdName","PdSchool","PdHint"})pvis(id,false);
 static const auto layout=Data::Get("Assets/Data/v4_story/system_layout.json"),pages=Data::Get("Assets/Data/v4_story/system_pages_layout.json");
 if(padSystemView==0){
  UI::Show(this,"Assets/UI/PadSystemV4.hbwidget.json","padsystem");padRow=padSystemColumn;
  for(int i=0;i<6;i++){auto n=std::to_string(i);auto row=layout["entries"][i];float dy=i==padSystemColumn?-layout["lift"].get<float>():0;
   for(const auto& pair:std::vector<std::pair<std::string,std::string>>{{"SyBase","base"},{"SyIcon","icon"},{"SyLabel","title"}}){padsystem::rect(this,"padsystem",pair.first+n,row[pair.second],0,dy);UI::SetOpacity(this,"padsystem",pair.first+n,pair.first=="SyLabel"?(i==padSystemColumn?1.f:.6015625f):1.f);}
  }
  for(int i=0;i<6;i++){auto n=std::to_string(i);const auto& r=layout["entries"][i];const bool on=i==padSystemColumn;UI::SetTexture(this,"padsystem","SyBase"+n,r[on?"baseOn":"baseOff"].get<std::string>());UI::SetTexture(this,"padsystem","SyIcon"+n,r[on?"iconOn":"iconOff"].get<std::string>());}
  float dx=layout["entries"][padSystemColumn]["base"][0].get<float>()-layout["entries"][0]["base"][0].get<float>();
  for(int i=0;i<4;i++)padsystem::rect(this,"padsystem","SyActive"+std::to_string(i),layout["active"][i],dx);
  const char* notices[]{"지금까지 읽은 대화를 확인해요.","현재 진행을 저장해요.","저장한 진행을 불러와요.","표시·소리·조작을 조절해요.","패드의 테마를 바꿔요.","메인 메뉴로 돌아가요. 저장하지 않은 진행은 사라져요."};
  UI::SetText(this,"padsystem","SyNotice",notices[padSystemColumn]);return;
 }
 if(padSystemView==1||padSystemView==2){
  UI::Show(this,"Assets/UI/SaveSlotsV4.hbwidget.json","padstorage");int first=(padStorageRow/6)*6;padRow=padStorageRow;
  UI::SetText(this,"padstorage","SvTitle",padStorageBusy?"저장 중…":padSystemView==1?"저장":"불러오기");UI::SetText(this,"padstorage","SvPage",std::to_string(first/6+1)+" / 5");
  for(int i=0;i<6;i++){auto n=std::to_string(i),key=std::to_string(first+i);bool occupied=padManualSlots.contains(key);auto row=occupied?padManualSlots[key]:Json::object();
   UI::SetText(this,"padstorage","SvNumber"+n,std::to_string(first+i+1));UI::SetText(this,"padstorage","SvChapter"+n,occupied?row.value("chapter",std::string()):"저장 데이터 없음");UI::SetText(this,"padstorage","SvDate"+n,occupied?row.value("date",std::string()):std::string());
   for(auto p:{"SvNumber","SvChapter","SvDate"})UI::SetOpacity(this,"padstorage",std::string(p)+n,first+i==padStorageRow?1.f:.6015625f);
  }
  auto dy=pages["storage"]["rows"][padStorageRow%6]["parts"][0][1].get<float>()-pages["storage"]["rows"][0]["parts"][0][1].get<float>();padsystem::rect(this,"padstorage","SvActive",pages["storage"]["active"],0,dy);return;
 }
 if(padSystemView==3){
  padRow=padConfirmChoice;
  UI::Show(this,"Assets/UI/LoadDetailV4.hbwidget.json","padload");auto row=padManualSlots.value(std::to_string(padStorageRow),Json::object());
  UI::SetText(this,"padload","LdNumber",std::to_string(padStorageRow+1));UI::SetText(this,"padload","LdGame",row.value("chapter",std::string()));UI::SetText(this,"padload","LdDate",row.value("date",std::string()));UI::SetText(this,"padload","LdDetail",row.value("place",std::string()));
  for(int i=0;i<2;i++){UI::SetTexture(this,"padload","LdChoice"+std::to_string(i),std::string("Assets/Art/ui/pad_load_choice_")+(i==padConfirmChoice?"on":"off")+".svg");UI::SetOpacity(this,"padload",i==0?"LdYes":"LdNo",i==padConfirmChoice?1.f:.6f);}return;
 }
 if(padSystemView==4){
  UI::Show(this,"Assets/UI/PadThemeV4.hbwidget.json","padtheme");const auto entries=pages["theme"]["entries"];padThemeRow=std::clamp(padThemeRow,0,int(entries.size())-1);
  if(padThemeRow<padThemeFirst)padThemeFirst=padThemeRow;if(padThemeRow>=padThemeFirst+7)padThemeFirst=padThemeRow-6;padThemeFirst=std::clamp(padThemeFirst,0,std::max(0,int(entries.size())-7));padRow=padThemeRow;
  for(int i=0;i<7;i++){int index=padThemeFirst+i;bool on=index<int(entries.size());auto n=std::to_string(i);UI::SetVisible(this,"padtheme","ThRow"+n,on);if(!on)continue;
   auto row=entries[index];UI::SetText(this,"padtheme","ThRow"+n,row.value("name",std::string())+(row.value("saveNo",-1)==padThemeSaveNo?"  ◀":""));UI::SetOpacity(this,"padtheme","ThRow"+n,index==padThemeRow?1.f:.6015625f);Color ink=index==padThemeRow?Color{0,0,0,1}:Color{1,1,1,1};UI::SetColor(this,"padtheme","ThRow"+n,ink);
   for(int d=0;d<2;d++){auto id="ThNumber"+n+"_"+std::to_string(d);UI::SetText(this,"padtheme",id,std::to_string(((index+1)/(d==0?10:1))%10));UI::SetColor(this,"padtheme",id,ink);UI::SetVisible(this,"padtheme",id,d==1||index+1>=10);}
  }
  padsystem::rect(this,"padtheme","ThActive",pages["theme"]["active"],0,pages["theme"]["rows"][padThemeRow-padThemeFirst][1].get<float>()-pages["theme"]["rows"][0][1].get<float>());
  UI::SetTexture(this,"padtheme","ThPreview",entries[padThemeRow].value("image",std::string()));
  UI::SetText(this,"padtheme","ThBody",entries[padThemeRow].value("name",std::string())+"\nEnter로 적용해요.");return;
 }
 UI::Show(this,"Assets/UI/CommonConfirmV4.hbwidget.json","padconfirm");
 padRow=padConfirmChoice;
 UI::SetText(this,"padconfirm","CwBody",padSystemView==5?"메인 메뉴로 돌아갈까요?\n저장하지 않은 진행은 사라져요.":"이 데이터를 덮어써서 저장할까요?");
 for(int i=0;i<2;i++){UI::SetTexture(this,"padconfirm","CwChoice"+std::to_string(i),std::string("Assets/Art/ui/pad_choice_")+(i==padConfirmChoice?"on":"off")+".svg");UI::SetOpacity(this,"padconfirm",i==0?"CwYes":"CwNo",i==padConfirmChoice?1.f:.6f);}
}
void Yumeno::padSystemUpdate(float delta,bool click){
 if(padSystemLog){v4LogUpdate(click);return;}
 if(padStorageBusy){if((padStorageDelay-=delta)>0)return;int result=padManualSaveStep();if(result==0)return;padStorageBusy=false;padSavePhase=0;padSaveSnapshot=Json();padSaveWriter={};padSystemDraw();toast(result>0?"저장했어요":"저장하지 못했어요. 다시 시도해 주세요");return;}
 Vec2 m;Input::GetMousePositionForCanvas({1280,720},m);bool back=pressed("Backspace")||pressed("mouse1")||pressed("Escape");
 if(back){if(padSystemView==0){padPageAt=-1;padHidePage();padMenu();}else{padSystemView=padSystemView==3?2:padSystemView==6?1:0;padSystemDraw();}sfx("ui_cancel");return;}
 static const auto layout=Data::Get("Assets/Data/v4_story/system_layout.json"),pages=Data::Get("Assets/Data/v4_story/system_pages_layout.json");
 bool select=enterNow;
 if(padSystemView==0){
  int old=padSystemColumn;if(pressed("a")||pressed("ArrowLeft"))padSystemColumn=(padSystemColumn+5)%6;if(pressed("d")||pressed("ArrowRight"))padSystemColumn=(padSystemColumn+1)%6;
  if(click)for(int i=0;i<6;i++)if(padsystem::hit(m,layout["entries"][i]["base"])){padSystemColumn=i;select=true;}
  if(old!=padSystemColumn){padSystemDraw();sfx("ui_select");}
  if(!select)return;if(machineActive&&machineFromGallery&&(padSystemColumn==0||padSystemColumn==1||padSystemColumn==2||padSystemColumn==5)){toast("갤러리 머신에서는 정보·설정만 확인할 수 있어요");sfx("ui_cancel");return;}sfx("ui_confirm");
  if(padSystemColumn==0){padSystemLog=true;UI::SetVisible(this,"padsystem","root",false);v4Log(true);return;}
  if(padSystemColumn==3){UI::SetVisible(this,"padsystem","root",false);optv4::Open(optionsV4);return;}
  padSystemView=padSystemColumn==1?1:padSystemColumn==2?2:padSystemColumn==4?4:5;padConfirmChoice=1;
  if(padSystemView==4){const auto entries=pages["theme"]["entries"];for(int i=0;i<int(entries.size());i++)if(entries[i].value("saveNo",-1)==padThemeSaveNo)padThemeRow=i;}
  padSystemDraw();return;
 }
 if(padSystemView==1||padSystemView==2){
  int old=padStorageRow;if(pressed("w")||pressed("ArrowUp"))padStorageRow=(padStorageRow+29)%30;if(pressed("s")||pressed("ArrowDown"))padStorageRow=(padStorageRow+1)%30;if(pressed("q"))padStorageRow=std::max(0,padStorageRow-6);if(pressed("e"))padStorageRow=std::min(29,padStorageRow+6);
  if(click)for(int i=0;i<6;i++){auto r=pages["storage"]["rows"][i]["parts"][1];if(padsystem::hit(m,r)){padStorageRow=(padStorageRow/6)*6+i;select=true;}}
  if(old!=padStorageRow){padSystemDraw();sfx("ui_select");}if(!select)return;
  if(padSystemView==2&&!padManualSlots.contains(std::to_string(padStorageRow))){
   sfx("v3se_000");
   return;
  }
  sfx("ui_confirm");
  if(padSystemView==2){padSystemView=3;padConfirmChoice=1;padSystemDraw();}
  else if(padManualSlots.contains(std::to_string(padStorageRow))){padSystemView=6;padConfirmChoice=1;padSystemDraw();}
  else{padStorageBusy=true;padStorageDelay=.15f;padSystemDraw();}return;
 }
 if(padSystemView==4){
  int old=padThemeRow,count=int(pages["theme"]["entries"].size());if(pressed("w")||pressed("ArrowUp"))padThemeRow=(padThemeRow+count-1)%count;if(pressed("s")||pressed("ArrowDown"))padThemeRow=(padThemeRow+1)%count;if(pressed("q"))padThemeRow=std::max(0,padThemeRow-7);if(pressed("e"))padThemeRow=std::min(count-1,padThemeRow+7);
  if(click)for(int i=0;i<7;i++)if(padsystem::hit(m,pages["theme"]["rows"][i])&&padThemeFirst+i<count){padThemeRow=padThemeFirst+i;select=true;}
  if(old!=padThemeRow){padSystemDraw();sfx("ui_select");}if(!select)return;
  auto theme=pages["theme"]["entries"][padThemeRow];int selected=theme.value("saveNo",0);try{Save::Write("yumeno-pad-theme-v1",Json{{"version",1},{"saveNo",selected}});if(Json::parse(Save::ReadText("yumeno-pad-theme-v1")).value("saveNo",-1)!=selected)throw std::runtime_error("theme persistence");padThemeSaveNo=selected;padThemeApply();padSystemView=0;padSystemDraw();sfx("ui_confirm");}catch(const std::exception&){toast("테마를 저장하지 못했어요. 다시 시도해 주세요");}return;
 }
 int old=padConfirmChoice;if(pressed("a")||pressed("ArrowLeft"))padConfirmChoice=0;if(pressed("d")||pressed("ArrowRight"))padConfirmChoice=1;
 for(int i=0;i<2;i++)if(click&&padsystem::hit(m,pages[padSystemView==3?"detail":"confirm"][padSystemView==3?(i==0?"LdYes":"LdNo"):(i==0?"yes":"no")])){padConfirmChoice=i;select=true;}
 if(old!=padConfirmChoice){padSystemDraw();sfx("ui_select");}if(!select)return;
 sfx("ui_confirm");
 if(padConfirmChoice==1){padSystemView=padSystemView==3?2:padSystemView==6?1:0;padSystemDraw();return;}
 if(padSystemView==5){padToggle();toTitle();return;}
 if(padSystemView==6){padSystemView=1;padStorageBusy=true;padStorageDelay=.15f;padSystemDraw();return;}
 if(padSystemView==3&&!padManualLoad()){toast("저장 데이터를 불러오지 못했어요");padSystemView=2;padSystemDraw();}
}
