// 탐색 (docs/spec/16 §1-1·§2·§3) : 지도 → 방(1인칭 배경 + 서 있는 인물 + 조사 대상) → 조사/대화.
// 수사 : 방 = 수사 장면, 조사 대상 = 장면 안 break 구간. 자유행동 : 장소마다 인물이 서 있고, 말을 걸면 「함께 시간을 보낼까?」.
// Flow.hpp 다음에 include. 위젯 W_Explore 좌표는 tools/create-project.mjs 와 같다.
namespace exui {
const char* ID="explore";
constexpr float BG_W=1600,BG_H=900,PAN=160; // 배경은 화면보다 넓게 깔고 좌우로 돌아본다
constexpr float MAP_X=700,MAP_Y=96,MAP_W=520,MAP_H=56,MAP_STEP=62;
constexpr float CF_YES_X=380,CF_NO_X=660,CF_Y=360,CF_W=220,CF_H=50;
const char* const PLACES[]{"중앙 광장","호텔 로비","호텔 라운지","푸드코트","의무실","기념품샵","호텔 식당"}; // 이벤트가 없는 인물이 서 있을 곳
}

// 받침 있으면 b, 없으면 a (예 : 레이와 / 미오와 / 린과)
std::string josa(const std::string& word,const std::string& a,const std::string& b){
 if(word.size()<3)return a;auto s=word.substr(word.size()-3);unsigned c=((unsigned char)s[0]&0x0F)<<12|((unsigned char)s[1]&0x3F)<<6|((unsigned char)s[2]&0x3F);
 return c>=0xAC00&&c<=0xD7A3&&(c-0xAC00)%28?b:a;
}
void Yumeno::etext(const std::string& id,const std::string& v){if(etexts.count(id)&&etexts[id]==v)return;etexts[id]=v;UI::SetText(this,exui::ID,id,v);}
void Yumeno::evis(const std::string& id,bool v){if(evisible.count(id)&&evisible[id]==v)return;evisible[id]=v;UI::SetVisible(this,exui::ID,id,v);}
void Yumeno::hideExplore(){
 for(auto id:{"ExBg","ArL","ArR","AreaBand","AreaIcon","AreaName","Mini","ExHint","LblBand","LblText","Cross","MapBack","MapImg","MapPlace","MapWho","MapHead","MapSub","MapHint","CfShade","CfBox","CfText","CfYesP","CfYes","CfNoP","CfNo"})evis(id,false);
 for(int i=0;i<6;i++)evis("Fig"+std::to_string(i),false);
 for(int i=0;i<10;i++){evis("MiniDot"+std::to_string(i),false);evis("Spark"+std::to_string(i),false);}
 for(int i=0;i<9;i++){evis("MapP"+std::to_string(i),false);evis("MapT"+std::to_string(i),false);for(int k=0;k<4;k++)evis("MapF"+std::to_string(i)+"_"+std::to_string(k),false);}
}

// ── 지도 : 수사 현장 / 자유행동 장소 목록 ─────────────────────────
void Yumeno::showMap(){
 hideFlow();hideExplore();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);mode=Mode::Map;
 auto& b=currentBeat();bool inv=b.value("t","")=="investigate";
 rooms.clear();
 if(inv){
  for(int i=0;i<int(b["spots"].size());i++){auto& s=b["spots"][i];Room r;r.spot=i;r.name=s.value("spot","");r.bg=s.value("bg","");
   for(auto& p:s["people"])if(inPark(p.get<std::string>()))r.people.push_back(p.get<std::string>());
   for(int k=0;k<int(s["objects"].size());k++){auto& o=s["objects"][k];r.objects.push_back({o.value("name",""),o.value("from",0),o.value("to",0),o.value("who",""),k});}
   r.done=roomDone(r);rooms.push_back(r);}
 }else{ // 자유행동 : 이벤트 장소마다 그 인물, 이벤트가 없는 인물은 기본 장소에
  std::map<std::string,int> at;
  auto roomFor=[&](const std::string& place,const std::string& bg)->Room&{if(!at.count(place)){at[place]=int(rooms.size());Room r;r.name=place;r.bg=bg;rooms.push_back(r);}return rooms[at[place]];};
  std::set<std::string> placed;
  for(auto& p:b["pool"]){auto who=p.value("who","");if(!inPark(who)||seen.count(p.value("id",""))||placed.count(who))continue;placed.insert(who);
   roomFor(p.value("place","중앙 광장"),p.value("bg","plaza_day")).people.push_back(who);}
  int k=0;for(auto s:{"rei","sora","ken","nana","riku","akari","yuu","koto","satsuki","taiga","rin","sho","ai","haruka","kaede"}){
   if(!inPark(s)||placed.count(s))continue;auto place=exui::PLACES[(k++*5+chapterAt)%7];
   roomFor(place,"").people.push_back(s);}
  for(auto& r:rooms)if(r.bg.empty()){for(auto& [w,prefixes]:std::vector<std::pair<std::string,std::string>>{{"광장","plaza_day"},{"로비","hotel_lobby"},{"라운지","hotel_lounge_day"},{"푸드코트","foodcourt"},{"의무실","infirmary"},{"기념품","souvenir_shop"},{"식당","hotel_dining"}})if(r.name.find(w)!=std::string::npos)r.bg=prefixes;if(r.bg.empty())r.bg="plaza_day";}
  if(rooms.size()>9)rooms.resize(9);
 }
 evis("MapBack",true);evis("MapHead",true);evis("MapSub",true);evis("MapHint",true);
 mapPreview();
 etext("MapHead",inv?"수사 — 어디를 조사할까?":"자유행동 — 누구와 보낼까?");
 etext("MapSub",inv?"현장 "+std::to_string(rooms.size())+"곳":"남은 시간 "+std::to_string(slots)+"번   ◎ "+std::to_string(coins));
 etext("MapHint",inv?"클릭 : 이동":"클릭 : 이동     G : 캡슐 머신(3코인)");
 for(int i=0;i<9;i++){bool on=i<int(rooms.size());auto n=std::to_string(i);evis("MapP"+n,on);evis("MapT"+n,on);
  for(int k=0;k<4;k++){auto f="MapF"+n+"_"+std::to_string(k);bool face=on&&k<int(rooms[i].people.size());evis(f,face);
   if(face){auto s=rooms[i].people[k];auto img=artPath("pad","face_"+s,"pad",".png");UI::SetTexture(this,exui::ID,f,img.empty()?"Assets/Art/sprites/"+s+"/"+s+"_C01.webp":img);}}
  if(!on)continue;
  etext("MapT"+n,(rooms[i].done?"✓ ":"")+rooms[i].name);
  UI::SetTexture(this,exui::ID,"MapP"+n,i==mapHover?"Assets/Art/ui/map_item_on.svg":"Assets/Art/ui/map_item.svg");}
 hud();fvis("FHud",true);
}
bool Yumeno::roomDone(const Room& r)const{
 auto& s=currentBeat()["spots"][r.spot];
 for(auto& o:r.objects)if(!seen.count(s.value("id","")+"#"+std::to_string(o.index)))return false;
 return true;
}
// 지도 왼쪽 : 가리킨 장소 미리보기 + 그곳에 있는 사람
void Yumeno::mapPreview(){
 if(mapHover>=int(rooms.size()))return;auto& r=rooms[mapHover];
 auto img=artPath("backgrounds",r.bg,"bg",".webp");evis("MapImg",!img.empty());if(!img.empty())UI::SetTexture(this,exui::ID,"MapImg",img);
 std::string who;for(auto& p:r.people)who+=(who.empty()?"":" · ")+nameOf(p);
 etext("MapPlace",r.name);etext("MapWho",who.empty()?std::string(" "):who);evis("MapPlace",true);evis("MapWho",true);
}
int Yumeno::mapAt(float x,float y)const{
 if(x<exui::MAP_X||x>exui::MAP_X+exui::MAP_W||y<exui::MAP_Y)return -1;
 int i=int((y-exui::MAP_Y)/exui::MAP_STEP);
 return i<int(rooms.size())&&y-exui::MAP_Y-i*exui::MAP_STEP<=exui::MAP_H?i:-1;
}

// ── 방 : 배경을 넓게 깔고, 인물은 바닥에 서 있고, 조사 대상은 화면 곳곳 ──────
void Yumeno::enterRoom(int i){
 roomAt=i;auto& r=rooms[i];panX=0;
 hideExplore();hideFlow();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);
 auto bg=artPath("backgrounds",r.bg,"bg",".webp");
 evis("ExBg",true);if(!bg.empty()){UI::SetTexture(this,exui::ID,"ExBg",bg);lastBackground=bg;if(currentBeat().value("t","")=="investigate")sceneBackground=bg;}
 for(auto id:{"ArL","ArR","AreaBand","AreaIcon","AreaName","Mini","ExHint","Cross"})evis(id,true);
 etext("AreaName",r.name);
 etext("ExHint",currentBeat().value("t","")=="investigate"?"클릭 : 조사 · 말 걸기     M : 지도     Tab : 패드":"인물을 클릭해 말 걸기     M : 지도");
 // 조사 대상 자리 : 배경 가로를 고르게 나눠 바닥~벽 높이에 둔다(인물은 사이사이)
 hotspots.clear();
 int n=int(r.objects.size()),m=int(r.people.size());
 for(int k=0;k<n;k++){if(!r.objects[k].who.empty())continue;float u=.14f+.72f*(k+.5f)/std::max(1,n);float v=k%2?.58f:.7f;hotspots.push_back({u,v,false,k,""});}
 for(int k=0;k<m&&k<6;k++){float u=m==1?.5f:.22f+.56f*k/std::max(1,m-1);hotspots.push_back({u,.98f,true,-1,r.people[k]});
  UI::SetTexture(this,exui::ID,"Fig"+std::to_string(k),"Assets/Art/figure/"+r.people[k]+".webp");evis("Fig"+std::to_string(k),true);}
 placeRoom();mode=Mode::Explore;
 // 들어가자마자 나오는 대사(첫 조사 대상 앞) : 한 번만
 if(currentBeat().value("t","")=="investigate"){auto& s=currentBeat()["spots"][r.spot];auto key=s.value("id","")+"#in";
  if(!seen.count(key)&&s.value("intro",0)>0){seen.insert(key);playSegment(r.spot,0,s.value("intro",0));}}
}
void Yumeno::placeRoom(){
 float ox=-exui::PAN+panX,oy=-90; // 배경 왼쪽 위
 UI::SetPosition(this,exui::ID,"ExBg",{ox,oy});
 int fig=0,dot=0;
 for(auto& h:hotspots){float x=ox+h.u*exui::BG_W,y=oy+h.v*exui::BG_H;
  if(h.person){UI::SetPosition(this,exui::ID,"Fig"+std::to_string(fig),{x,std::min(y,740.f)});fig++;}
  else if(dot<10){auto id="Spark"+std::to_string(dot);UI::SetPosition(this,exui::ID,id,{x,y});dot++;}}
 // 미니맵 : 조사 대상 점(끝난 것은 회색)
 auto& r=rooms[roomAt];
 for(int k=0;k<10;k++){bool on=k<int(r.objects.size());auto id="MiniDot"+std::to_string(k);evis(id,on);if(!on)continue;
  float a=k*6.2832f/std::max<size_t>(1,r.objects.size());UI::SetPosition(this,exui::ID,id,{1170+44*std::cos(a),590+44*std::sin(a)});
  bool done=currentBeat().value("t","")=="investigate"&&seen.count(currentBeat()["spots"][r.spot].value("id","")+"#"+std::to_string(r.objects[k].index));
  UI::SetColor(this,exui::ID,id,done?Color{.45f,.45f,.5f,1}:Color{1,.82f,.12f,1});}
}
int Yumeno::hotspotAt(float x,float y)const{
 float ox=-exui::PAN+panX,oy=-90;int best=-1;float bd=1e9f;
 for(int i=0;i<int(hotspots.size());i++){auto& h=hotspots[i];float hx=ox+h.u*exui::BG_W,hy=oy+h.v*exui::BG_H;
  float d=h.person?(std::abs(x-hx)<90&&y>hy-480&&y<hy?std::abs(x-hx):1e9f):std::hypot(x-hx,y-hy);
  if(d<(h.person?90.f:70.f)&&d<bd){bd=d;best=i;}}
 return best;
}
std::string Yumeno::hotspotLabel(int i)const{
 auto& h=hotspots[i];auto& r=rooms[roomAt];
 if(h.person)return "말 걸기 : "+nameOf(h.who);
 return "조사하기 : "+r.objects[h.object].name;
}
// 장면 구간 재생 : 끝나면 탐색으로 돌아온다
void Yumeno::playSegment(int spot,int from,int to){
 ctxSpot=spot;event=from;eventEnd=to;showStory();flowPresent();
}
void Yumeno::interact(int i){
 auto h=hotspots[i];auto& r=rooms[roomAt];bool inv=currentBeat().value("t","")=="investigate";
 if(inv){
  int obj=h.object;
  if(h.person)for(auto& o:r.objects)if(o.who==h.who)obj=o.index;
  if(obj<0){sayOnce(h.who,reaction(h.who,"chat"),"C01",After::Explore);return;}
  auto& o=r.objects[obj];segmentKey=currentBeat()["spots"][r.spot].value("id","")+"#"+std::to_string(o.index);
  playSegment(r.spot,o.from,o.to);return;
 }
 // 자유행동 : 확인 → 이벤트
 if(!h.person)return;
 confirmWho=h.who;showConfirm(nameOf(h.who)+josa(nameOf(h.who),"와","과")+" 함께 시간을 보낼까?");
}
void Yumeno::showConfirm(const std::string& q){
 mode=Mode::Confirm;confirmYes=true;
 for(auto id:{"CfShade","CfBox","CfText","CfYesP","CfYes","CfNoP","CfNo"})evis(id,true);etext("CfText",q);
 UI::SetTexture(this,exui::ID,"CfYesP","Assets/Art/ui/map_item_on.svg");UI::SetTexture(this,exui::ID,"CfNoP","Assets/Art/ui/map_item.svg");
}
void Yumeno::confirmPicked(bool yes){
 for(auto id:{"CfShade","CfBox","CfText","CfYesP","CfYes","CfNoP","CfNo"})evis(id,false);
 if(!yes){mode=Mode::Explore;return;}
 int p=poolOf(confirmWho);
 if(p>=0){band("free");ctxPool=p;event=0;eventEnd=-1;showStory();flowPresent();return;}
 addBond(confirmWho,1);coins+=1;giftTarget=confirmWho;sayOnce(confirmWho,reaction(confirmWho,"chat"),"C02",After::Gift);
}
// 수사 : 방의 조사 대상 하나가 끝났다
void Yumeno::segmentDone(){
 if(!segmentKey.empty()){seen.insert(segmentKey);segmentKey.clear();coins+=1;}
 ctxSpot=-1;eventEnd=-1;
 bool all=true;for(auto& r:rooms)if(!roomDone(r))all=false;
 if(all){ // V3 : 필요한 조사를 다 하면 수사 종료 방송 → 재판으로
  auto ch=chapter.value("chapter","1");int added=0;
  for(auto& [id,v]:kotodama.items())if(id.size()>2&&id[1]==ch[0]&&cards.insert(id).second)++added;
  band("invend");hideExplore();nextBeat();return;
 }
 rooms[roomAt].done=roomDone(rooms[roomAt]);
 enterRoomBack();
}
void Yumeno::enterRoomBack(){ // 대화가 끝난 뒤 같은 방 그대로
 hideFlow();dialogVisible(false);UI::SetVisible(this,UI_ID,"Portrait",false);
 for(auto id:{"ExBg","ArL","ArR","AreaBand","AreaIcon","AreaName","Mini","ExHint","Cross"})evis(id,true);
 for(int k=0;k<int(rooms[roomAt].people.size())&&k<6;k++)evis("Fig"+std::to_string(k),true);
 placeRoom();mode=Mode::Explore;hud();fvis("FHud",true);
}

// 띠 연출 : 자유행동·수사 개시·수사 종료·시체 발견 (1.4초, 입력을 막지 않음)
void Yumeno::band(const std::string& kind){
 UI::SetTexture(this,exui::ID,"Band","Assets/Art/ui/band_"+kind+".svg");evis("Band",true);bandTimer=1.4f;
 if(kind=="body"){evis("Flash",true);flashTimer=.25f;}
}
// 언령 획득 : 빛 + 카드 + 「언령 ○○를 손에 넣었다」. 클릭할 때까지
void Yumeno::kotodamaGet(const std::string& id){
 for(auto x:{"KShade","KGlow","KFrame","KCard","KBand","KTitle","KMsg"})evis(x,true);
 bool icon=false;for(auto& c:art["kotodama"])if(c.get<std::string>()==id)icon=true;
 evis("KCard",icon);if(icon)UI::SetTexture(this,exui::ID,"KCard","Assets/Art/kotodama/"+id+".png");
 std::string frame=id[0]=='T'?"frame_testimony":id[0]=='M'||id[0]=='R'?"frame_rule_magic":id[0]=='N'?"frame_memo":"frame_evidence";
 UI::SetTexture(this,exui::ID,"KFrame","Assets/Art/ui/kotodama/"+frame+".png");
 etext("KTitle","언령 「"+kotodamaName(id)+"」");etext("KMsg",josa(kotodamaName(id),"를","을")+" 손에 넣었다!");
 popupFrom=mode;mode=Mode::Popup;kspin=0;
}
void Yumeno::updateExplore(float delta,bool click){
 if(bandTimer>0&&(bandTimer-=delta)<=0)evis("Band",false);
 if(flashTimer>0&&(flashTimer-=delta)<=0)evis("Flash",false);
 Vec2 m{640,360};Input::GetMousePosition(m);
 if(mode==Mode::Popup){
  kspin+=delta;UI::SetRotation(this,exui::ID,"KGlow",kspin*20);UI::SetScale(this,exui::ID,"KFrame",{std::min(1.f,kspin*4),std::min(1.f,kspin*4)});
  if(click||enterNow){for(auto x:{"KShade","KGlow","KFrame","KCard","KBand","KTitle","KMsg"})evis(x,false);mode=popupFrom;++event;flowPresent();}
  return;
 }
 if(mode==Mode::Map){
  if(pressed("g")&&currentBeat().value("t","")=="freetime"){pullCapsule();etext("MapSub","남은 시간 "+std::to_string(slots)+"번   ◎ "+std::to_string(coins));}
  int over=mapAt(m.x,m.y);if(over>=0&&over!=mapHover){mapHover=over;for(int i=0;i<int(rooms.size());i++)UI::SetTexture(this,exui::ID,"MapP"+std::to_string(i),i==mapHover?"Assets/Art/ui/map_item_on.svg":"Assets/Art/ui/map_item.svg");mapPreview();}
  if(click&&over>=0){hideExplore();enterRoom(over);}
  return;
 }
 if(mode==Mode::Confirm){
  bool overYes=m.y>exui::CF_Y&&m.y<exui::CF_Y+exui::CF_H&&m.x>exui::CF_YES_X&&m.x<exui::CF_YES_X+exui::CF_W;
  bool overNo=m.y>exui::CF_Y&&m.y<exui::CF_Y+exui::CF_H&&m.x>exui::CF_NO_X&&m.x<exui::CF_NO_X+exui::CF_W;
  if(pressed("a")||overYes)confirmYes=true;if(pressed("d")||overNo)confirmYes=false;
  UI::SetTexture(this,exui::ID,"CfYesP",confirmYes?"Assets/Art/ui/map_item_on.svg":"Assets/Art/ui/map_item.svg");UI::SetTexture(this,exui::ID,"CfNoP",confirmYes?"Assets/Art/ui/map_item.svg":"Assets/Art/ui/map_item_on.svg");
  if((click&&(overYes||overNo))||enterNow)confirmPicked(click?overYes:confirmYes);
  return;
 }
 // 방 : 화면 끝으로 마우스를 대거나 A/D 로 돌아본다
 float dir=(m.x<70||Input::IsKeyDown("a")?1.f:0.f)-(m.x>1210||Input::IsKeyDown("d")?1.f:0.f);
 if(dir!=0){panX=std::clamp(panX+dir*delta*420,-exui::PAN,exui::PAN);placeRoom();}
 UI::SetPosition(this,exui::ID,"Cross",{m.x,m.y});
 int over=hotspotAt(m.x,m.y);
 if(over!=crossOver){crossOver=over;UI::SetTexture(this,exui::ID,"Cross",over>=0?"Assets/Art/ui/ex_cross_on.svg":"Assets/Art/ui/ex_cross.svg");
  evis("LblBand",over>=0);evis("LblText",over>=0);if(over>=0)etext("LblText",hotspotLabel(over));}
 if(pressed("m")){showMap();return;}
 if(click&&over>=0){evis("LblBand",false);evis("LblText",false);crossOver=-1;interact(over);}
}
// 자동 진행 검증 : 지도에서 아직 안 끝난 곳 → 방에서 안 본 대상(또는 이벤트가 남은 인물)
Json Yumeno::autoExplore()const{
 using hb::Json;
 if(mode==Mode::Popup)return Json{{"kind","key"},{"key","Enter"}};
 if(mode==Mode::Confirm)return Json{{"kind","key"},{"key","Enter"}};
 bool inv=currentBeat().value("t","")=="investigate";
 if(mode==Mode::Map){
  int want=0;
  for(int i=0;i<int(rooms.size());i++){if(inv?!rooms[i].done:std::any_of(rooms[i].people.begin(),rooms[i].people.end(),[&](const std::string& s){return poolOf(s)>=0;})){want=i;break;}}
  if(!inv&&coins>=3&&gifts.empty())return Json{{"kind","key"},{"key","g"}};
  return Json{{"kind","click"},{"x",exui::MAP_X+60},{"y",exui::MAP_Y+want*exui::MAP_STEP+exui::MAP_H/2}};
 }
 if(mode==Mode::Explore){
  auto& r=rooms[roomAt];float ox=-exui::PAN+panX,oy=-90;
  for(auto& h:hotspots){
   bool todo;
   if(inv){int obj=h.object;if(h.person){obj=-1;for(auto& o:r.objects)if(o.who==h.who)obj=o.index;}
    todo=obj>=0&&!seen.count(currentBeat()["spots"][r.spot].value("id","")+"#"+std::to_string(r.objects[obj].index));}
   else todo=h.person&&poolOf(h.who)>=0;
   if(todo){float x=ox+h.u*exui::BG_W,y=oy+h.v*exui::BG_H;if(h.person)y=std::min(y,740.f)-200;
    if(x<80)return Json{{"kind","key"},{"key","a"}};if(x>1200)return Json{{"kind","key"},{"key","d"}};
    return Json{{"kind","click"},{"x",x},{"y",y}};}
  }
  if(!inv&&!hotspots.empty()){for(auto& h:hotspots)if(h.person){float x=ox+h.u*exui::BG_W;return Json{{"kind","click"},{"x",std::clamp(x,100.f,1180.f)},{"y",500}};}}
  return Json{{"kind","key"},{"key","m"}};
 }
 return Json{{"kind","key"},{"key","Enter"}};
}
