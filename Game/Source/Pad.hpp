// 래피 패드 (V3 모노패드 배치, docs/spec/16 §4·§5-2). Tab 열기/닫기, A/D·마우스 아이콘, Enter 들어가기, Backspace·우클릭 돌아가기.
// 하위 화면 : 지도 · 코토다마 · 선물 · 통신부 · 교칙 · 설정. 위젯 W_Pad 좌표는 tools/create-project.mjs 와 같다.
namespace padui {
const char* ID="pad";
struct Icon{const char* key;const char* title;const char* desc;Color tint;};
const Icon ICONS[6]{
 {"map","MAP  지도","공원 지도를 확인합니다. 지금 갈 수 있는 구역이 표시됩니다.",{1,.16f,.3f,.13f}},
 {"bullet","KOTODAMA  코토다마","모은 코토다마를 확인합니다. 증거·증언·교칙·마법이 기록돼 있어요.",{.85f,.85f,.9f,.1f}},
 {"gift","PRESENT  선물","가지고 있는 선물을 확인합니다. 자유행동 때 줄 수 있습니다.",{.2f,.7f,1,.13f}},
 {"card","REPORT CARD  통신부","함께한 시간이 쌓인 학생들의 통신부를 확인합니다.",{1,.16f,.3f,.13f}},
 {"rules","SCHOOL RULES  교칙","래피가 정한 교칙을 확인합니다. 어기면 처벌입니다.",{.2f,.7f,1,.13f}},
 {"option","OPTION  설정","표시·소리·조작을 조절하고 진행을 저장해요.",{.7f,.72f,.8f,.1f}}};
constexpr float ICON_X=60,ICON_Y=470,ICON_W=140,ICON_STEP=170,ROW_X=60,ROW_Y=230,ROW_W=560,ROW_H=34,ROW_STEP=36,SIL_X=60,SIL_Y=220,SIL_STEP=70;
constexpr float BUTTON_X[6]{87.3333f,266.f,444.6667f,622.6667f,802.6667f,980.6667f};
const char* const STUDENTS[15]{"rei","sora","ken","nana","riku","akari","yuu","koto","satsuki","taiga","rin","sho","ai","haruka","kaede"};
const char* const REPORTERS[16]{"mio","rei","sora","ken","nana","riku","akari","yuu","koto","satsuki","taiga","rin","sho","ai","haruka","kaede"};
}
void Yumeno::ptext(const std::string& id,const std::string& v){if(ptexts.count(id)&&ptexts[id]==v)return;ptexts[id]=v;UI::SetText(this,padui::ID,id,v);if(id=="PdHint")ptext("PdHintShadow",v);}
void Yumeno::pvis(const std::string& id,bool v){if(pvisible.count(id)&&pvisible[id]==v)return;pvisible[id]=v;UI::SetVisible(this,padui::ID,id,v);if(id=="PdHint")pvis("PdHintShadow",v);}
void Yumeno::padToggle(bool playCloseSound){
 if(mode==Mode::Pad&&padStorageBusy)return;
 if(mode==Mode::Pad){padSkillPurchase.clear();UI::Remove(this,"skillconfirm");}
 if(mode==Mode::Pad)padSystemClear();
 if(mode==Mode::Pad)padMapClear();
 if(mode==Mode::Pad&&padPageAt==4&&padRuleTimer>0)return;
 if(mode==Mode::Pad&&padRulesVisible){UI::Remove(this,"padrules");padRulesVisible=false;padRuleTimer=0;}
 if(mode==Mode::Pad&&padReportVisible){UI::Remove(this,"padreport");padReportVisible=false;}
 if(mode==Mode::Pad&&padSkillVisible){UI::Remove(this,"padskill");padSkillVisible=false;}
 if(mode==Mode::Pad&&padGiftVisible){padGiftLeave();UI::Remove(this,"padgift");padGiftVisible=false;}
 if(mode==Mode::Pad&&padEvidenceVisible){UI::Remove(this,"padevidence");padEvidenceVisible=false;}
 if(mode==Mode::Pad&&beforePad==Mode::Trial&&!v4TaskActive){v4TaskRoot(true);if(playingDebate)debateHud(true);}
 if(mode==Mode::Trial&&!v4TaskActive)v4TaskRoot(false);
 // Modal feedback was already shown in the Pad; do not cover resumed trial HUDs.
 if(mode==Mode::Pad){toastTimer=0;fvis("FToast",false);for(auto& [id,v]:pvisible)if(v){UI::SetVisible(this,padui::ID,id,false);v=false;}UI::Remove(this,"pad");mode=beforePad;if(trialEntryTime==0)UI::SetVisible(this,"trialentryv4","root",true);if(mode==Mode::Story&&v4DocumentOpen())v4DocumentDraw();if(mode==Mode::Machine){machineArmed=false;UI::SetVisible(this,"machinev4","root",true);machineDraw();}world.mouseX=world.mouseY=-1;if(mode==Mode::Trial&&v4TaskActive){v4CancelInput();v4TaskRoot(!v4QueueActive);if(playingDebate&&!v4QueueActive)debateHud(true);if(v4QueueAfter=="success"&&!v4ComicPage.empty())v4ComicComplete(true);}else if(v4.active&&v4.current().contains("comicPage"))v4ComicComplete(true);if(playCloseSound)sfx("ui_pad_close");return;}
 if(v4DocumentOpen())v4DocumentVisible(false);
 ptexts.clear();pvisible.clear();UI::Show(this,"Assets/UI/Pad.hbwidget.json","pad");
 beforePad=mode;UI::SetVisible(this,"trialvitalsv4","root",false);if(beforePad==Mode::Trial&&v4TaskActive){v4CancelInput();v4TaskRoot(false);}mode=Mode::Pad;padPageAt=-1;padRow=0;padSystemView=0;
 if(comicShown)UI::SetVisible(this,"comicv4","root",false);
 for(int layer=0;layer<4;layer++)pv4::HideSequence(presentationV4,layer);
 Vec2 mouse;Input::GetCenteredMousePositionForCanvas({1280,720},mouse);padMouseX=mouse.x;padMouseY=mouse.y;sfx("ui_pad");
 for(auto id:{"PdFloor","PdTint","PdHead","PdFace","PdTitle","PdBubble","PdDesc","PdBig","PdSide","PdCoins","PdName","PdSchool","PdHint"})pvis(id,true);
 UI::SetTexture(this,padui::ID,"PdFace","Assets/Art/pad/face_lappy.webp");
 for(int i=0;i<6;i++){pvis("PdIcon"+std::to_string(i),true);UI::SetTexture(this,padui::ID,"PdIcon"+std::to_string(i),std::string("Assets/Art/ui/v3/pad_home/icon_")+padui::ICONS[i].key+".svg");}
 padMenu();
}
void Yumeno::padMenu(){
 auto& ic=padui::ICONS[padIcon];
 ptext("PdTitle",ic.title);ptext("PdDesc",ic.desc);UI::SetTexture(this,padui::ID,"PdBig",std::string("Assets/Art/ui/v3/pad_")+ic.key+".webp");
 bool home=padPageAt<0;
 pvis("PdHint",padPageAt!=3&&padPageAt!=4);
 for(auto id:{"PdCoins","PdName","PdSchool"})pvis(id,padPageAt<0);pvis("PdSide",false);
 UI::SetPosition(this,padui::ID,"PdHint",(padPageAt==1||padPageAt==2||padPageAt==3)?Vec2{40,676}:Vec2{760,676});UI::SetSize(this,padui::ID,"PdHint",(padPageAt==1||padPageAt==2||padPageAt==3)?Vec2{1200,30}:Vec2{370,30});
 UI::SetPosition(this,padui::ID,"PdHintShadow",(padPageAt==1||padPageAt==2||padPageAt==3)?Vec2{41.5f,677.5f}:Vec2{761.5f,677.5f});UI::SetSize(this,padui::ID,"PdHintShadow",(padPageAt==1||padPageAt==2||padPageAt==3)?Vec2{1200,30}:Vec2{370,30});
 if(home){padListFirst=0;padEvidenceImage=padEvidenceImages=0;}
 padThemeApply();
 pvis("PdFloor",padPageAt!=0); /* V3 pad map : translucent plan over the live 3D view (prologue video frames) */
 pvis("PdHead",false);pvis("PdBig",false);pvis("PdTitle",!home);pvis("PdFace",home);pvis("PdTint",!home);pvis("PdBubble",home);pvis("PdDesc",home);
 if(home){
  // Supplied Korean menu SFL: title[154,126], description[628,230],
  // host[218.15,275.55]*0.9, native design1920x1080 ->1280x720.
  UI::SetPosition(this,padui::ID,"PdFace",{145.43f,183.7f});UI::SetSize(this,padui::ID,"PdFace",{211.2f,153.6f});
  // Shape13 has local x bounds[-58,645], not[0,587] from the PNG size.
  UI::SetPosition(this,padui::ID,"PdBubble",{380.f,153.33f});UI::SetSize(this,padui::ID,"PdBubble",{468.67f,170.67f});
  UI::SetPosition(this,padui::ID,"PdDesc",{414.f,184.67f});UI::SetSize(this,padui::ID,"PdDesc",{406.67f,107.f});UI::SetFontSize(this,padui::ID,"PdDesc",30.f);
 }else UI::SetColor(this,padui::ID,"PdTint",ic.tint);
 for(int i=0;i<6;i++){bool on=i==padIcon;auto id="PdIcon"+std::to_string(i);/* V3 top : selected icon is drawn larger and raised (theme showcase frames) */UI::SetPosition(this,padui::ID,id,{padui::BUTTON_X[i]-(on?14.f:0.f),on?366.f:436.6667f});UI::SetSize(this,padui::ID,id,on?Vec2{160,165}:Vec2{132,136});UI::SetScale(this,padui::ID,id,{1,1});UI::SetOpacity(this,padui::ID,id,padPageAt<0||on?1.f:.35f);}
 ptext("PdCoins","COINS\n"+std::to_string(coins));
 ptext("PdHint",padPageAt<0?"A/D 고르기   Z·Enter 결정   Esc 돌아가기":"W/S 고르기   Esc 돌아가기");
}
void Yumeno::padHidePage(){
 padHintRow=-1;padHintTime=0;
 padSystemClear();
 padMapClear();
 if(padRulesVisible){UI::Remove(this,"padrules");padRulesVisible=false;}padRuleTimer=0;
 if(padReportVisible){UI::Remove(this,"padreport");padReportVisible=false;}
 if(padSkillVisible){UI::Remove(this,"padskill");padSkillVisible=false;}
 if(padGiftVisible){UI::Remove(this,"padgift");padGiftVisible=false;}
 if(padEvidenceVisible){UI::Remove(this,"padevidence");padEvidenceVisible=false;}
 for(int i=0;i<12;i++){UI::SetPosition(this,padui::ID,"PdRowP"+std::to_string(i),{60,230.f+i*36});UI::SetSize(this,padui::ID,"PdRowP"+std::to_string(i),{560,34});UI::SetPosition(this,padui::ID,"PdRowT"+std::to_string(i),{84,234.f+i*36});UI::SetSize(this,padui::ID,"PdRowT"+std::to_string(i),{520,28});UI::SetFontSize(this,padui::ID,"PdRowT"+std::to_string(i),20);}
 for(int i=0;i<12;i++){UI::SetOpacity(this,padui::ID,"PdRowP"+std::to_string(i),1);pvis("PdRowP"+std::to_string(i),false);pvis("PdRowT"+std::to_string(i),false);}
 for(int i=0;i<15;i++)pvis("PdSil"+std::to_string(i),false);
 for(auto id:{"PdPic","PdPicTitle","PdPicText","PdLevel","PdStand"})pvis(id,false);
 UI::SetPosition(this,padui::ID,"PdPic",{660,220});UI::SetSize(this,padui::ID,"PdPic",{440,260});
 UI::SetPosition(this,padui::ID,"PdPicTitle",{660,488});UI::SetSize(this,padui::ID,"PdPicTitle",{460,36});
 UI::SetPosition(this,padui::ID,"PdPicText",{660,528});UI::SetSize(this,padui::ID,"PdPicText",{460,140});
 UI::SetColor(this,padui::ID,"PdPicText",Color{.9f,.95f,1,1});UI::SetFontSize(this,padui::ID,"PdPicText",19);
 bool menu=padPageAt<0;for(int i=0;i<6;i++)pvis("PdIcon"+std::to_string(i),menu); // 하위 화면은 화면 전체를 쓴다(V3)
 pvis("PdBubble",menu);pvis("PdDesc",menu);
}
// 하위 화면 목록 : 종류별 줄
std::vector<std::pair<std::string,std::string>> Yumeno::padRows()const{
 std::vector<std::pair<std::string,std::string>> r;
 if(padPageAt==1)for(auto& c:cards)r.push_back({c,kotodamaName(c)});
 if(padPageAt==2)for(const auto& item:giftData["items"]){auto id=item.value("id",std::string());r.push_back({id,giftName(id)});}
 if(padPageAt==4){r.push_back({"cover","표지"});for(const auto& id:padRuleIds())r.push_back({id,v4.active?v4Documents[id].value("title",std::string()):id});}
 if(padPageAt==5){
  if(padSystemView==0)r={{"log","대화 기록"},{"save","저장"},{"load","불러오기"},{"options","환경설정"},{"theme","테마"},{"title","메인 메뉴"}};
  else if(padSystemView==5||padSystemView==6)r={{"title_yes","예"},{"cancel","아니오"}};
  else if(padSystemView==3)r={{"load_yes","불러오기"},{"cancel","돌아가기"}};
  else if(padSystemView==1||padSystemView==2)for(int i=0;i<30;i++)r.push_back({"slot"+std::to_string(i+1),std::to_string(i+1)});
  else if(padSystemView==4){static const auto pages=Data::Get("Assets/Data/v4_story/system_pages_layout.json");for(const auto& theme:pages["theme"]["entries"])r.push_back({std::to_string(theme.value("saveNo",0)),theme.value("name",std::string())});}
 }
 if(padPageAt==0){static const auto layout=Data::Get("Assets/Data/v4_story/map_layout.json");for(const auto& id:padMapCandidates())if(layout["instances"][id].value("group",-1)==padMapGroup)r.push_back({id,layout["instances"][id].value("label",id)});}
 return r;
}
void Yumeno::padEvidenceImageDraw(){
 padEvidenceImages=0;if(!v4.active||padPageAt!=1)return;auto rows=padRows();if(padRow<0||padRow>=int(rows.size()))return;
 auto map=Data::Get("Assets/Data/v4_story/evidence_art.json");auto images=map.value("items",Json::object()).value(rows[padRow].first,Json::array());padEvidenceImages=int(images.size());
 if(images.empty())return;padEvidenceImage=(padEvidenceImage+padEvidenceImages)%padEvidenceImages;
 UI::SetVisible(this,"padevidence","PeImage",true);UI::SetTexture(this,"padevidence","PeImage",images[padEvidenceImage].value("image",std::string()));
 UI::SetVisible(this,"padevidence","PePagePlate",padEvidenceImages>1);UI::SetVisible(this,"padevidence","PePage",padEvidenceImages>1);UI::SetText(this,"padevidence","PePage",std::to_string(padEvidenceImage+1)+" / "+std::to_string(padEvidenceImages));
}
void Yumeno::padGiftLeave(){
 if(padPageAt!=2)return;auto rows=padRows();if(padRow>=0&&padRow<int(rows.size()))giftNew.erase(rows[padRow].first);
}
void Yumeno::padGiftDraw(){
 static const auto numericSource=Data::Get("Assets/Data/v4_story/gift_source_ui.json")["states"];
 auto rows=padRows();int count=int(rows.size());if(!count)return;
 for(const auto& [id,qty]:gifts)if(qty>0)giftKnown.insert(id);
 padRow=std::clamp(padRow,0,count-1);int selectedRow=padRow/9;
 if(selectedRow<padListFirst/9)padListFirst=selectedRow*9;
 if(selectedRow>=padListFirst/9+3)padListFirst=(selectedRow-2)*9;
 padListFirst=std::clamp(padListFirst,0,std::max(0,(count+8)/9-3)*9);
 if(!padGiftVisible){UI::Show(this,"Assets/UI/PadGiftV4.hbwidget.json","padgift");padGiftVisible=true;}
 pvis("PdTitle",false);pvis("PdTint",false);
 if(v4.active&&v4GiftCatalog.empty())v4GiftCatalog=Data::Get("Assets/Data/v4_story/gifts.json");
 for(int i=0;i<27;i++){
  int index=padListFirst+i;bool exists=index<count,on=index==padRow;std::string id=exists?rows[index].first:std::string();bool known=exists&&giftKnown.count(id);int qty=known&&gifts.count(id)?gifts.at(id):0;auto n=std::to_string(i);
  for(auto key:{"PgBase","PgImage"})UI::SetVisible(this,"padgift",std::string(key)+n,exists);
  UI::SetVisible(this,"padgift","PgFrame"+n,exists&&on);UI::SetVisible(this,"padgift","PgNew"+n,known&&giftNew.count(id));
  UI::SetVisible(this,"padgift","PgTimes"+n,known);
  for(int d=0;d<3;d++){auto digit="PgDigit"+n+"_"+std::to_string(d);int divisor=d==0?1:d==1?10:100;UI::SetVisible(this,"padgift",digit,known&&(d==0||qty>=divisor));UI::SetTexture(this,"padgift",digit,numericSource["techou_present_icon_US_digit_"+std::to_string((std::min(qty,999)/divisor)%10)]["asset"].get<std::string>());UI::SetOpacity(this,"padgift",digit,on?1.f:.5f);}
  if(!exists)continue;auto image=known?artPath("gifts",id,"gift",".webp"):std::string("Assets/Art/ui/pad_gift_unknown.svg");
  if(known&&v4.active&&v4GiftCatalog["items"].contains(id))image=v4GiftCatalog["items"][id].value("image",std::string());
  UI::SetTexture(this,"padgift","PgImage"+n,image);UI::SetOpacity(this,"padgift","PgImage"+n,on?1.f:.30078125f);UI::SetOpacity(this,"padgift","PgBase"+n,on?1.f:.30078125f);UI::SetOpacity(this,"padgift","PgNew"+n,on?1.f:.5f);UI::SetOpacity(this,"padgift","PgTimes"+n,on?1.f:.5f);
 }
 auto id=rows[padRow].first;bool known=giftKnown.count(id);std::string body;
 if(known)for(const auto& item:giftData["items"])if(item.value("id",std::string())==id)body="등급 : "+item.value("tier",std::string());
 UI::SetText(this,"padgift","PgTitle",known?giftName(id):"？？？");UI::SetText(this,"padgift","PgBody",body);
 int discovered=0;for(const auto& row:rows)if(giftKnown.count(row.first))++discovered;
 UI::SetVisible(this,"padgift","PgQuantity",known);

 for(const auto& value:std::vector<std::pair<std::string,int>>{{"Number",padRow+1},{"Quantity",known?(gifts.count(id)?gifts.at(id):0):0},{"Complete",discovered*100/count}})for(int d=0,divisor=1;d<3;d++,divisor*=10){auto digit="Pg"+value.first+"Digit"+std::to_string(d);int amount=std::clamp(value.second,0,999);UI::SetVisible(this,"padgift",digit,(value.first!="Quantity"||known)&&(d==0||amount>=divisor));UI::SetTexture(this,"padgift",digit,numericSource["techou_present_icon_US_digit_"+std::to_string(amount/divisor%10)+(value.first=="Complete"?"":"_black")]["asset"].get<std::string>());}
 ptext("PdHint","W/S/A/D 고르기 · Q/E 목록 쪽 · Esc 돌아가기");
}
void Yumeno::padShowPage(){
 padHidePage();padMenu();
 if(padPageAt==0){padMapDraw();return;}
 if(padPageAt==2){padGiftDraw();return;}
 if(padPageAt==3){padReportDraw();return;}
 if(padPageAt==4){padRulesDraw();return;}
 if(padPageAt==5){padSystemDraw();return;}

 auto rows=padRows();padRow=std::clamp(padRow,0,std::max(0,int(rows.size())-1));
 bool evidencePage=padPageAt==1;int visibleRows=evidencePage?11:12;
 if(evidencePage){if(padRow<padListFirst)padListFirst=padRow;if(padRow>=padListFirst+11)padListFirst=padRow-10;padListFirst=std::clamp(padListFirst,0,std::max(0,int(rows.size())-11));pvis("PdTitle",false);}
 int first=evidencePage?padListFirst:std::max(0,padRow-11);
 if(evidencePage){std::set<std::string> owned;for(const auto& row:rows)owned.insert(row.first);auto hint=evidencehintv4::primary(v4Task,owned);bool active=v4.active&&v4TaskActive&&playingDebate&&!v4QueueActive&&beforePad==Mode::Trial;
  if(padRow<int(rows.size())&&evidencehintv4::visible(hint,rows[padRow].first,active,skillOn("abracadabra"),debate))padHintRow=padRow-first;
 }
 for(int i=0;i<12;i++){int k=first+i;bool on=i<visibleRows&&k<int(rows.size());auto p="PdRowP"+std::to_string(i),t="PdRowT"+std::to_string(i);pvis(p,on);pvis(t,on);
  if(!on)continue;ptext(t,rows[k].second);UI::SetColor(this,padui::ID,t,evidencePage&&k==padRow?Color{0,0,0,1}:Color{1,1,1,1});UI::SetTexture(this,padui::ID,p,evidencePage?(k==padRow?"Assets/Art/ui/pad_evidence_row_on.svg":"Assets/Art/ui/pad_evidence_row.svg"):(k==padRow?"Assets/Art/ui/pad_row_on.svg":"Assets/Art/ui/pad_row.svg"));
  if(evidencePage){constexpr float textY[11]{141,217,296,373,451,529,606,685,763,840,918};UI::SetPosition(this,padui::ID,p,{.6667f,81.3333f+52*i});UI::SetSize(this,padui::ID,p,{566.6667f,54});UI::SetPosition(this,padui::ID,t,{52,textY[i]*(2.f/3)});UI::SetSize(this,padui::ID,t,{514,51.3333f});UI::SetFontSize(this,padui::ID,t,std::min(30.f,500.f/std::max(1,u8len(rows[k].second))));}
 }
 if(rows.empty()){pvis("PdRowT0",true);ptext("PdRowT0",padPageAt==1?"아직 코토다마가 없다.":padPageAt==2?(v4.active?"선물이 없다. 자유행동 때 C 로 캡슐 머신을 돌릴 수 있다.":"선물이 없다. 자유행동 때 G 로 캡슐 머신을 돌릴 수 있다."):"없음");return;}
 auto& cur=rows[padRow];std::string pic,title=cur.second,body;
 if(padPageAt==1){bool icon=false;for(auto& c:art["kotodama"])if(c.get<std::string>()==cur.first)icon=true;if(icon)pic="Assets/Art/kotodama/"+cur.first+".webp";title=kotodamaName(cur.first);body=kotodamaText(cur.first);}
 if(padPageAt==2){pic=artPath("gifts",cur.first,"gift",".webp");if(v4.active){if(v4GiftCatalog.empty())v4GiftCatalog=Data::Get("Assets/Data/v4_story/gifts.json");if(v4GiftCatalog["items"].contains(cur.first))pic=v4GiftCatalog["items"][cur.first].value("image",std::string());}title=giftName(cur.first);for(auto& g:giftData["items"])if(g.value("id","")==cur.first)body="등급 : "+g.value("tier","");}
 if(padPageAt==4){if(v4.active){auto& doc=v4Documents[cur.first];title=doc.value("title",std::string());for(auto& row:doc["rows"]){if(!body.empty())body+="\n\n";body+=row.get<std::string>();}pic=doc.value("image",std::string());}else{title=cur.first;body=cur.second.substr(std::min(cur.second.size(),cur.first.size()+3));}}
 if(padPageAt==0){auto ch=chapter.value("chapter","P");pic=cur.first=="here"?artPath("pad","map_A"+std::string(ch=="P"||ch=="1"?"0":ch),"pad",".webp"):artPath("backgrounds",cur.first,"bg",".webp");if(pic.empty())pic=artPath("pad","map_park","pad",".webp");body=cur.first=="here"?"지금 갈 수 있는 구역":" ";}
 if(evidencePage){
  // Recreate this eight-node detail to reset the engine ScrollBox on row changes.
  // Glyph wrapping uses the host's line-height, not the unsigned SFL gap field.
  UI::Show(this,"Assets/UI/PadEvidenceV4.hbwidget.json","padevidence");padEvidenceVisible=true;
  UI::SetVisible(this,"padevidence","PeImage",!pic.empty());if(!pic.empty())UI::SetTexture(this,"padevidence","PeImage",pic);
  UI::SetText(this,"padevidence","PeText",body);int lines=debate::lineCount(body,"Assets/Fonts/pretendard/Pretendard-Medium.otf",31.25f,533); /* 글꼴 실측 폭 */
  UI::SetSize(this,"padevidence","PeText",{533.336f,std::max(209.32f,(lines+1)*40.625f)});
  padEvidenceImageDraw();ptext("PdHint","W/S 고르기 · Q/E 목록 쪽 · A/D 그림 · 휠 설명 · Esc 돌아가기");return;
 }
 pvis("PdPic",!pic.empty());if(!pic.empty())UI::SetTexture(this,padui::ID,"PdPic",pic);
 ptext("PdPicTitle",title);ptext("PdPicText",body.empty()?std::string(" "):body);pvis("PdPicTitle",true);pvis("PdPicText",true);
}
void Yumeno::updatePad(float delta,bool click){
 if(padPageAt==1&&padHintRow>=0){padHintTime+=std::max(0.f,delta);UI::SetOpacity(this,padui::ID,"PdRowP"+std::to_string(padHintRow),evidencehintv4::opacity(padHintTime));}
 Vec2 m{0,0};Input::GetCenteredMousePositionForCanvas({1280,720},m);
 if(padPageAt==0){padMapUpdate(delta,click);return;}
 if(padPageAt==5){padSystemUpdate(delta,click);return;}
 if(padPageAt==4&&padRuleTimer>0){padRulesUpdate(delta,click);return;}
 if(padSkillConfirmUpdate(click))return;
 bool back=pressed("Backspace")||pressed("mouse1")||pressed("Escape")||pressed("x")||pressed("r"); /* V3 PC Escape/R/X = pad_circle (13_입력) */
 if(padPageAt<0){
  int over=-1;for(int i=0;i<6;i++){float y=i==padIcon?383.3333f:436.6667f;if(m.x>=padui::BUTTON_X[i]&&m.x<padui::BUTTON_X[i]+132&&m.y>=y&&m.y<y+136)over=i;}
  int before=padIcon;if(pressed("a"))padIcon=(padIcon+5)%6;if(pressed("d"))padIcon=(padIcon+1)%6;bool moved=m.x!=padMouseX||m.y!=padMouseY;padMouseX=m.x;padMouseY=m.y;if(over>=0&&moved)padIcon=over;
  if(padIcon!=before){padMenu();sfx("ui_select");}
  if(enterNow||pressed("z")||(click&&over>=0)){sfx("ui_confirm");padPageAt=padIcon;padRow=0;padListFirst=0;padReportPage=0;padSkillRow=0;padShowPage();}
  if(back)padToggle();
  return;
 }
 if(back&&trialEntryTime==0){padToggle();return;}
 if(back&&padSkillVisible){UI::Remove(this,"padskill");padSkillVisible=false;padReportDraw();sfx("ui_cancel");return;}
 if(back){padGiftLeave();sfx("ui_cancel");padPageAt=-1;padHidePage();padMenu();return;}
 int before=padRow;bool rowClicked=false;
 if(padPageAt==4){padRulesUpdate(delta,click);return;}
 if(padPageAt==2){
  auto rows=padRows();int count=int(rows.size());if(!count)return;int next=padRow;
  // Own PC mapping onto the source nine-column cursor; the original physical
  // keys are not inferred from SFL clip names.
  if(pressed("a"))next=(next+count-1)%count;if(pressed("d"))next=(next+1)%count;
  if(pressed("w")||pressed("s")){int column=next%9,totalRows=(count+8)/9,row=next/9;row=(row+totalRows+(pressed("s")?1:-1))%totalRows;next=std::min(row*9+column,count-1);}
  if(pressed("q"))next=std::max(0,next-27);if(pressed("e"))next=std::min(count-1,next+27);
  if(click)for(int i=0;i<27;i++){float x=86.f+(i%9)*126.666667f,y=90.666667f+(i/9)*128.666667f;if(m.x>=x&&m.x<x+85.333333f&&m.y>=y&&m.y<y+85.333333f&&padListFirst+i<count)next=padListFirst+i;}
  if(next!=padRow){padGiftLeave();padRow=next;padGiftDraw();sfx("ui_select");}return;
 }
 if(padPageAt==3){
  if(padSkillVisible){
   auto skills=padSkills();int total=int(skills.size());if(!total)return;int beforeSkill=padSkillRow;
   if(pressed("w"))padSkillRow=(padSkillRow+total-1)%total;if(pressed("s"))padSkillRow=(padSkillRow+1)%total;
   if(pressed("q"))padSkillRow=std::max(0,padSkillRow-7);if(pressed("e"))padSkillRow=std::min(total-1,padSkillRow+7);
   int first=std::max(0,padSkillRow-6);if(click){const auto& layout=Data::Get("Assets/Data/v4_story/skill_layout.json");for(int i=0;i<7;i++){auto r=layout["catalog"][i];if(m.x>=r[0].get<float>()&&m.x<r[0].get<float>()+r[2].get<float>()&&m.y>=r[1].get<float>()&&m.y<r[1].get<float>()+r[3].get<float>()&&first+i<total)padSkillRow=first+i;}}
   if(enterNow){auto id=skills[padSkillRow].value("id",std::string());if(!growthV4.owned.count(id)){auto available=growthv4::Purchase(growthV4,id,false,v4.active&&(!v4Court||trialEntryTime==0)&&!(machineActive&&machineFromGallery)&&v4.current().value("type",std::string())!="investigate");if(available.reason=="not-confirmed"){padSkillPurchase=id;padSkillConfirm=1;padSkillConfirmArmed=false;padSkillConfirmDraw();}else{toast(available.reason=="insufficient-fp"?"FP가 부족해요":"자유행동 기록을 마치면 익힐 수 있어요");sfx("ui_cancel");}return;}auto changed=growthv4::Toggle(growthV4,id,playerprogress::level(playerProgress),v4.active&&(!v4Court||trialEntryTime==0)&&!(machineActive&&machineFromGallery)&&v4.current().value("type",std::string())!="investigate");if(changed.changed)sfx("ui_confirm");else{toast(changed.reason=="insufficient-capacity"?"장착 SP가 부족해요":changed.reason=="conflicting-group"?"같은 계열 스킬이 이미 장착돼 있어요":"아직 익히지 않은 스킬이에요");sfx("ui_cancel");}}
   if(padSkillRow!=beforeSkill||enterNow)padSkillDraw();return;
  }
  int next=padRow,direction=pressed("a")||pressed("q")?-1:pressed("d")||pressed("e")?1:0;
  if(direction)for(int step=0;step<16;step++){next=(next+16+direction)%16;if(padReportAllowed(next))break;}
  if(click){const auto& layout=Data::Get("Assets/Data/v4_story/report_layout.json");for(int i=0;i<16;i++){auto r=layout["strip"][i];if(m.x>=r[0].get<float>()&&m.x<r[0].get<float>()+r[2].get<float>()&&m.y>=r[1].get<float>()&&m.y<r[1].get<float>()+r[3].get<float>()&&padReportAllowed(i))next=i;}}
  if(next!=padRow){padRow=next;padReportPage=0;padShowPage();sfx("ui_select");return;}
  int oldPage=padReportPage,count=padReportPages();if(pressed("w"))padReportPage=(padReportPage+count-1)%count;if(pressed("s"))padReportPage=(padReportPage+1)%count;
  if(padReportPage!=oldPage){padShowPage();sfx("ui_select");}
  if(enterNow&&padRow==0&&padReportPage==1){if(v4.active&&!v4Court&&!(machineActive&&machineFromGallery)&&v4.current().value("type",std::string())!="investigate"){UI::Remove(this,"padreport");padReportVisible=false;padSkillRow=0;padSkillDraw();sfx("ui_confirm");}else{sfx("ui_cancel");toast("현재는 스킬 장착을 바꿀 수 없어요");}}return;
 }
 else if(padPageAt==1){int count=int(padRows().size());if(count>0){
  if(pressed("w"))padRow=(padRow+count-1)%count;if(pressed("s"))padRow=(padRow+1)%count;
  int cursor=padRow-padListFirst,lastFirst=std::max(0,count-11);
  if(pressed("q")){if(padListFirst>0){padListFirst=std::max(0,padListFirst-11);padRow=std::clamp(padListFirst+cursor,0,count-1);}else padRow=0;}
  if(pressed("e")){if(padListFirst<lastFirst){padListFirst=std::min(lastFirst,padListFirst+11);padRow=std::clamp(padListFirst+cursor,0,count-1);}else padRow=count-1;}
  if(click&&m.x>=.6667f&&m.x<567.3334f&&m.y>=81.3333f){int i=int((m.y-81.3333f)/52);if(i>=0&&i<11&&padListFirst+i<count){padRow=padListFirst+i;rowClicked=true;}}
  if(padRow==before&&padEvidenceImages>1&&(pressed("a")||pressed("d"))){padEvidenceImage+=pressed("d")?1:-1;padEvidenceImageDraw();sfx("ui_select");}
  if(padRow==before&&(pressed("q")||pressed("e"))){padEvidenceImage=0;padEvidenceImageDraw();}
  if(padRow!=before)sfx("ui_select");
 }}
 else{if(pressed("w"))padRow--;if(pressed("s"))padRow++;
  if(m.x>padui::ROW_X&&m.x<padui::ROW_X+padui::ROW_W&&m.y>padui::ROW_Y){int i=int((m.y-padui::ROW_Y)/padui::ROW_STEP);int first=std::max(0,padRow-11);if(i>=0&&i<12&&click&&m.y-padui::ROW_Y-i*padui::ROW_STEP<padui::ROW_H&&first+i<int(padRows().size())){padRow=first+i;rowClicked=true;}}}

 if(padRow!=before){padEvidenceImage=0;padShowPage();}
}

#include "PadReportV4.hpp"
#include "PadRulesV4.hpp"
#include "PadSystemV4.hpp"
#include "PadMapV4.hpp"
