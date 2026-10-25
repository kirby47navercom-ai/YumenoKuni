// 래피 패드 (V3 모노패드 배치, docs/spec/16 §4·§5-2). Tab 열기/닫기, A/D·마우스 아이콘, Enter 들어가기, Backspace·우클릭 돌아가기.
// 하위 화면 : 지도 · 언령 · 선물 · 통신부 · 교칙 · 설정. 위젯 W_Pad 좌표는 tools/create-project.mjs 와 같다.
namespace padui {
const char* ID="pad";
struct Icon{const char* key;const char* title;const char* desc;Color tint;};
const Icon ICONS[6]{
 {"map","MAP  지도","공원 지도를 확인합니다. 지금 갈 수 있는 구역이 표시됩니다.",{1,.16f,.3f,.13f}},
 {"bullet","KOTODAMA  언령","모은 언령(증거·증언·교칙·마법)을 확인합니다.",{.85f,.85f,.9f,.1f}},
 {"gift","PRESENT  선물","가지고 있는 선물을 확인합니다. 자유행동 때 줄 수 있습니다.",{.2f,.7f,1,.13f}},
 {"card","REPORT CARD  통신부","함께한 시간이 쌓인 학생들의 통신부를 확인합니다.",{1,.16f,.3f,.13f}},
 {"rules","SCHOOL RULES  교칙","래피가 정한 교칙을 확인합니다. 어기면 처벌입니다.",{.2f,.7f,1,.13f}},
 {"option","OPTION  설정","저장하거나 타이틀로 돌아갑니다.",{.7f,.72f,.8f,.1f}}};
constexpr float ICON_X=60,ICON_Y=470,ICON_W=140,ICON_STEP=170,ROW_X=60,ROW_Y=230,ROW_W=560,ROW_H=34,ROW_STEP=36,SIL_X=60,SIL_Y=220,SIL_STEP=70;
const char* const STUDENTS[15]{"rei","sora","ken","nana","riku","akari","yuu","koto","satsuki","taiga","rin","sho","ai","haruka","kaede"};
}
void Yumeno::ptext(const std::string& id,const std::string& v){if(ptexts.count(id)&&ptexts[id]==v)return;ptexts[id]=v;UI::SetText(this,padui::ID,id,v);}
void Yumeno::pvis(const std::string& id,bool v){if(pvisible.count(id)&&pvisible[id]==v)return;pvisible[id]=v;UI::SetVisible(this,padui::ID,id,v);}
void Yumeno::padToggle(){
 if(mode==Mode::Pad){for(auto& [id,v]:pvisible)if(v){UI::SetVisible(this,padui::ID,id,false);v=false;}mode=beforePad;return;}
 beforePad=mode;mode=Mode::Pad;padPageAt=-1;padRow=0;
 for(auto id:{"PdFloor","PdTint","PdHead","PdFace","PdTitle","PdBubble","PdDesc","PdBig","PdSide","PdCoins","PdName","PdSchool","PdHint"})pvis(id,true);
 auto face=std::string("Assets/Art/cutin/mio_1.webp");UI::SetTexture(this,padui::ID,"PdFace",face);
 for(int i=0;i<6;i++){pvis("PdIcon"+std::to_string(i),true);UI::SetTexture(this,padui::ID,"PdIcon"+std::to_string(i),std::string("Assets/Art/ui/pad_")+padui::ICONS[i].key+".svg");}
 padMenu();
}
void Yumeno::padMenu(){
 auto& ic=padui::ICONS[padIcon];
 ptext("PdTitle",ic.title);ptext("PdDesc",ic.desc);UI::SetTexture(this,padui::ID,"PdBig",std::string("Assets/Art/ui/pad_")+ic.key+".svg");
 UI::SetColor(this,padui::ID,"PdTint",ic.tint);
 for(int i=0;i<6;i++){bool on=i==padIcon;auto id="PdIcon"+std::to_string(i);float s=on?1.22f:.92f;UI::SetScale(this,padui::ID,id,{s,s});UI::SetOpacity(this,padui::ID,id,padPageAt<0||on?1.f:.35f);}
 ptext("PdCoins","COINS\n"+std::to_string(coins));
 ptext("PdHint",padPageAt<0?"A/D 고르기   Enter 열기   Tab 닫기":"W/S 고르기   Backspace 돌아가기");
}
void Yumeno::padHidePage(){
 for(int i=0;i<12;i++){pvis("PdRowP"+std::to_string(i),false);pvis("PdRowT"+std::to_string(i),false);}
 for(int i=0;i<15;i++)pvis("PdSil"+std::to_string(i),false);
 for(auto id:{"PdPic","PdPicTitle","PdPicText","PdLevel","PdStand"})pvis(id,false);
 bool menu=padPageAt<0;for(int i=0;i<6;i++)pvis("PdIcon"+std::to_string(i),menu); // 하위 화면은 화면 전체를 쓴다(V3)
 pvis("PdBubble",menu);pvis("PdDesc",menu);
}
// 하위 화면 목록 : 종류별 줄
std::vector<std::pair<std::string,std::string>> Yumeno::padRows()const{
 std::vector<std::pair<std::string,std::string>> r;
 if(padPageAt==1)for(auto& c:cards)r.push_back({c,kotodamaName(c)});
 if(padPageAt==2)for(auto& [id,n]:gifts)r.push_back({id,giftName(id)+"   ×"+std::to_string(n)});
 if(padPageAt==4)for(auto& x:rules["rules"])r.push_back({x.value("no",""),x.value("no","")+"   "+x.value("text","")});
 if(padPageAt==5){r.push_back({"save","저장하기"});r.push_back({"title","타이틀로 돌아가기"});}
 if(padPageAt==0){r.push_back({"here",std::string("지금 : ")+(chapter.value("chapter","P")=="P"?"프롤로그":"제"+chapter.value("chapter","1")+"장")});
  for(auto& rm:rooms)r.push_back({rm.bg,rm.name});}
 return r;
}
void Yumeno::padShowPage(){
 padHidePage();padMenu();
 if(padPageAt==3){ // 통신부 : 위 실루엣 줄, 왼쪽 단계, 오른쪽 입상
  for(int i=0;i<15;i++){auto id="PdSil"+std::to_string(i);auto s=padui::STUDENTS[i];pvis(id,true);
   auto face=artPath("pad",std::string("face_")+s,"pad",".png");UI::SetTexture(this,padui::ID,id,face.empty()?std::string("Assets/Art/sprites/")+s+"/"+s+"_C01.webp":face);
   UI::SetOpacity(this,padui::ID,id,i==padRow?1.f:flowOn&&!inPark(s)?.18f:.45f);UI::SetScale(this,padui::ID,id,{i==padRow?1.15f:1.f,i==padRow?1.15f:1.f});}
  auto s=padui::STUDENTS[std::clamp(padRow,0,14)];int lv=level(s),pts=bonds.count(s)?bonds.at(s):0;
  std::string t=nameOf(s)+"\n\n";for(int k=5;k>=1;k--)t+=std::string(k<=lv?"■ ":"□ ")+"Lv"+std::to_string(k)+(k==lv?"   ← 지금":"")+"\n";
  t+="\n인연 포인트 "+std::to_string(pts)+(flowOn&&!inPark(s)?"\n\n(이제 만날 수 없다)":"");
  ptext("PdLevel",t);pvis("PdLevel",true);
  UI::SetTexture(this,padui::ID,"PdStand",std::string("Assets/Art/figure/")+s+".webp");pvis("PdStand",true);
  ptext("PdHint","A/D 학생 넘기기   Backspace 돌아가기");
  return;
 }
 auto rows=padRows();padRow=std::clamp(padRow,0,std::max(0,int(rows.size())-1));
 int first=std::max(0,padRow-11);
 for(int i=0;i<12;i++){int k=first+i;bool on=k<int(rows.size());auto p="PdRowP"+std::to_string(i),t="PdRowT"+std::to_string(i);pvis(p,on);pvis(t,on);
  if(!on)continue;ptext(t,rows[k].second);UI::SetTexture(this,padui::ID,p,k==padRow?"Assets/Art/ui/pad_row_on.svg":"Assets/Art/ui/pad_row.svg");}
 if(rows.empty()){pvis("PdRowT0",true);ptext("PdRowT0",padPageAt==1?"아직 언령이 없다.":padPageAt==2?"선물이 없다. 자유행동 때 G 로 캡슐 머신을 돌릴 수 있다.":"없음");return;}
 auto& cur=rows[padRow];std::string pic,title=cur.second,body;
 if(padPageAt==1){bool icon=false;for(auto& c:art["kotodama"])if(c.get<std::string>()==cur.first)icon=true;if(icon)pic="Assets/Art/kotodama/"+cur.first+".png";title=kotodamaName(cur.first);body=kotodamaText(cur.first);}
 if(padPageAt==2){pic=artPath("gifts",cur.first,"gift",".png");title=giftName(cur.first);for(auto& g:giftData["items"])if(g.value("id","")==cur.first)body="등급 : "+g.value("tier","");}
 if(padPageAt==4){title=cur.first;body=cur.second.substr(std::min(cur.second.size(),cur.first.size()+3));}
 if(padPageAt==0){pic=artPath("backgrounds",cur.first,"bg",".webp");if(pic.empty()){pic=artPath("pad","map_park","pad",".png");}body=" ";}
 if(padPageAt==5){title=cur.second;body=cur.first=="save"?"지금까지의 진행을 저장합니다.":"저장하지 않은 진행은 사라집니다.";}
 pvis("PdPic",!pic.empty());if(!pic.empty())UI::SetTexture(this,padui::ID,"PdPic",pic);
 ptext("PdPicTitle",title);ptext("PdPicText",body.empty()?std::string(" "):body);pvis("PdPicTitle",true);pvis("PdPicText",true);
}
void Yumeno::updatePad(float delta,bool click){
 (void)delta;Vec2 m{0,0};Input::GetMousePosition(m);
 bool back=pressed("Backspace")||pressed("mouse1");
 if(padPageAt<0){
  int over=-1;if(m.y>padui::ICON_Y&&m.y<padui::ICON_Y+padui::ICON_W&&m.x>padui::ICON_X)over=int((m.x-padui::ICON_X)/padui::ICON_STEP);if(over>5)over=-1;
  int before=padIcon;if(pressed("a"))padIcon=(padIcon+5)%6;if(pressed("d"))padIcon=(padIcon+1)%6;if(over>=0)padIcon=over;
  if(padIcon!=before)padMenu();
  if(enterNow||(click&&over>=0)){padPageAt=padIcon;padRow=0;padShowPage();}
  if(back)padToggle();
  return;
 }
 if(back){padPageAt=-1;padHidePage();padMenu();return;}
 int before=padRow;
 if(padPageAt==3){if(pressed("a")||pressed("q"))padRow=(padRow+14)%15;if(pressed("d")||pressed("e"))padRow=(padRow+1)%15;
  if(click&&m.y>padui::SIL_Y&&m.y<padui::SIL_Y+64){int i=int((m.x-padui::SIL_X)/padui::SIL_STEP);if(i>=0&&i<15)padRow=i;}}
 else{if(pressed("w"))padRow--;if(pressed("s"))padRow++;
  if(m.x>padui::ROW_X&&m.x<padui::ROW_X+padui::ROW_W&&m.y>padui::ROW_Y){int i=int((m.y-padui::ROW_Y)/padui::ROW_STEP);int first=std::max(0,padRow-11);if(i<12&&click)padRow=first+i;}}
 if(padRow!=before)padShowPage();
 if(padPageAt==5&&(enterNow||click)){auto rows=padRows();if(padRow<int(rows.size())){
  if(rows[padRow].first=="save"){saveFlow();toast("저장했다");}
  else{padToggle();saveFlow();hideExplore();toTitle();}}}
}
